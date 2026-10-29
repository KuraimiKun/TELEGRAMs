"""Explicitly isolated PostgreSQL/Redis verification for Phase 6."""

import asyncio
import itertools
import os
from dataclasses import replace
from datetime import timedelta

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from redis.asyncio import from_url
from sqlalchemy import delete, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from bots.channelmanager import invitations, members, outbox
from bots.channelmanager.growth_specs import DelegateSpec
from bots.channelmanager.models import (
    Channel,
    ChannelGrant,
    ChannelInvoice,
    GrowthAction,
    InviteCredit,
    JoinRequest,
    MemberBan,
    Operation,
    Post,
    PostVersion,
    SenderBinding,
)
from bots.channelmanager.senders import SenderService, token_epoch
from core.db.base import Base, create_engine, create_sessionmaker, upsert, utcnow
from core.db.migrate import alembic_config, upgrade
from core.db.models import Bot as BotRecord
from core.db.models import ChildBot
from core.sdk.context import ChildInfo
from core.sdk.registry import discover
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR
from tests.bots.channelmanager.test_channel_billing import buy, catalog, checkout, payment
from tests.bots.channelmanager.test_growth import body, grant, setup_growth
from tests.bots.channelmanager.test_members import join_event, person, setup_members
from tests.conftest import BOT_ID, RecordingSession, build_test_ctx

URL = os.environ.get("TEST_CHM_GROWTH_DATABASE_URL")
REDIS_URL = os.environ.get("TEST_CHM_REDIS_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_CHM_GROWTH_DATABASE_URL not set")
REAL_RESERVE = outbox.reserve_budget


def checked_url():
    assert URL
    parsed = make_url(URL)
    assert parsed.drivername == "postgresql+asyncpg" and parsed.host in {"127.0.0.1", "localhost"}
    assert (parsed.database or "").startswith("channelmanager_phase6_test")
    return URL


@pytest.fixture
async def pg_growth(redis, tmp_path, monkeypatch):
    url = checked_url()
    await asyncio.to_thread(upgrade, url)
    engine = create_engine(url)
    sm = create_sessionmaker(engine)
    api = RecordingSession()
    try:
        async with sm() as session:
            await session.execute(text("TRUNCATE bots CASCADE"))
            await session.execute(upsert(session, BotRecord).values(id=BOT_ID, slug="channelmanager", title="Test", active=True).on_conflict_do_nothing())
            await session.commit()
        ctx = await build_test_ctx(discover(["channelmanager"])[0], sm, redis, api, tmp_path)
        # Same deterministic API fixture as unit tests; all SQL here uses PostgreSQL.
        from aiogram.types import Chat

        from tests.bots.channelmanager.conftest import admin_member
        api.responses["GetChat"] = Chat(id=CHANNEL_ID, type="channel", title="Postgres")
        api.responses["GetChatMember"] = lambda m: admin_member(m.user_id)
        await setup_growth(ctx, api)
        async def immediate(*args):
            return 0
        monkeypatch.setattr(outbox, "reserve_budget", immediate)
        yield ctx, api
    finally:
        await api.close()
        await engine.dispose()


async def test_growth_migration_roundtrip_preserves_admission_cleanup_and_matches_models(pg_growth):
    ctx, api = pg_growth
    await setup_members(ctx, api)
    async with ctx.sm() as session:
        await members.observe_request(session, ctx, join_event().chat_join_request, 12001, utcnow())
        channel = await session.get(Channel, (BOT_ID, CHANNEL_ID))
        config = await ctx.extras["members"].config(CHANNEL_ID, OPERATOR)
        action = await members.action(session, ctx, channel, config, kind="ban", key="preserved-ban", user_id=77,
            payload={"destination": CHANNEL_ID, "until_date": (utcnow() + timedelta(days=1)).isoformat()})
        session.add(MemberBan(bot_id=BOT_ID, id="b" * 32, channel_id=CHANNEL_ID, chat_id=CHANNEL_ID, user_id=77,
            action_id=action.id, status="active", until_date=utcnow() + timedelta(days=1)))
        await session.commit()
    cfg = alembic_config(checked_url())
    await asyncio.to_thread(command.downgrade, cfg, "0023_chm_members")
    await asyncio.to_thread(command.upgrade, cfg, "head")
    async with ctx.sm() as session:
        assert await session.scalar(select(func.count()).select_from(JoinRequest)) == 1
        assert (await session.scalar(select(MemberBan))).status == "active"
        assert (await session.scalar(select(Operation).where(Operation.kind == "member_ban"))).member_action_id == action.id
        assert (await session.scalar(select(JoinRequest))).invite_count == 0
    async with ctx.sm.kw["bind"].connect() as connection:
        diff = await connection.run_sync(lambda c: compare_metadata(MigrationContext.configure(c, opts={"compare_type": True}), Base.metadata))
    assert diff == []


async def test_duplicate_payment_and_parallel_renewals_allocate_once_without_overlap(pg_growth):
    ctx, api = pg_growth
    plan = await catalog(ctx, api)
    invoice = await ctx.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id)
    assert await ctx.extras["billing"].checkout(checkout(invoice))
    paid = payment(invoice)
    results = await asyncio.gather(*(ctx.extras["billing"].fulfill(person(OPERATOR), paid) for _ in range(2)))
    assert sorted(results) == ["duplicate", "paid"]
    a = await ctx.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id)
    b = await ctx.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id)
    for row in [a, b]:
        assert await ctx.extras["billing"].checkout(checkout(row))
    assert await asyncio.gather(*(ctx.extras["billing"].fulfill(person(OPERATOR), payment(row)) for row in [a, b])) == ["paid", "paid"]
    async with ctx.sm() as session:
        grants = (await session.scalars(select(ChannelGrant).order_by(ChannelGrant.starts_at))).all()
        assert len(grants) == 3
        assert all(a.ends_at == b.starts_at for a, b in itertools.pairwise(grants))


async def test_revocation_between_native_authorization_and_sql_dispatch_fence(pg_growth, monkeypatch):
    ctx, api = pg_growth
    await grant(ctx)
    post = await ctx.extras["posts"].create(CHANNEL_ID, 77, body("Must not send"))
    await ctx.extras["posts"].publish(post.id, 77, post.generation)
    while (op := await outbox.claim(ctx)) is not None and op.kind != "publish":
        await outbox.execute(ctx, op)
    assert op and op.kind == "publish"
    authorized, release = asyncio.Event(), asyncio.Event()
    async def blocked_budget(*args):
        authorized.set()
        await release.wait()
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", blocked_budget)
    task = asyncio.create_task(outbox.execute(ctx, op))
    await asyncio.wait_for(authorized.wait(), 10)
    await ctx.extras["team"].save(CHANNEL_ID, OPERATOR, 77, DelegateSpec(), generation=1, active=False)
    release.set()
    await asyncio.wait_for(task, 10)
    assert not [m for m in api.calls("SendMessage") if m.text == "Must not send"]
    async with ctx.sm() as session:
        assert (await session.get(Operation, (BOT_ID, op.id))).status == "cancelled"


async def test_invitee_credit_is_unique_under_concurrent_delivery(pg_growth):
    ctx, api = pg_growth
    await setup_members(ctx, api)
    async with ctx.sm() as session:
        await members.observe_request(session, ctx, join_event().chat_join_request, 12001, utcnow())
        request = await session.scalar(select(JoinRequest))
        channel = await session.get(Channel, (BOT_ID, CHANNEL_ID))
        invite = await invitations.ensure(session, ctx, channel, request)
        invite.status, invite.link_hash = "active", invitations.link_hash("https://t.me/+own")
        await session.commit()
    async def credit():
        async with ctx.sm() as session:
            result = await invitations._credit(session, ctx, CHANNEL_ID, 88, invite.link_hash)
            await session.commit()
            return result
    assert sorted(await asyncio.gather(credit(), credit())) == [False, True]
    async with ctx.sm() as session:
        assert (await session.get(JoinRequest, (BOT_ID, request.id))).invite_count == 1
        assert await session.scalar(select(func.count()).select_from(InviteCredit)) == 1


async def test_child_delete_cascades_only_its_namespace_and_keeps_control_ledger(pg_growth):
    ctx, api = pg_growth
    plan = await catalog(ctx, api)
    invoice, _ = await buy(ctx, plan)
    async with ctx.sm() as session:
        for child_id in [222222, 333333]:
            session.add(BotRecord(id=child_id, slug=f"c{child_id}", title="Child", active=True))
            await session.flush()
            child = ChildBot(bot_id=child_id, owner_id=OPERATOR, factory_bot_id=BOT_ID, template="channelmanager", token_enc="encrypted", username="child", title="Child", status="active")
            session.add(child)
            session.add(Channel(bot_id=child_id, channel_id=CHANNEL_ID, title="Child channel", status="active"))
            await session.flush()
            session.add(Post(bot_id=child_id, id="p" * 16, channel_id=CHANNEL_ID, creator_id=OPERATOR, target_ids=[CHANNEL_ID]))
            await session.flush()
            session.add(PostVersion(bot_id=child_id, post_id="p" * 16, number=1, spec=body().model_dump()))
        await session.flush()
        child = await session.get(ChildBot, 222222)
        session.add(SenderBinding(bot_id=BOT_ID, channel_id=CHANNEL_ID, sender_bot_id=222222, owner_id=OPERATOR,
            token_epoch=token_epoch(child), control_username="control"))
        (await session.get(Channel, (BOT_ID, CHANNEL_ID))).sender_paused = True
        await session.commit()
    child_ctx = replace(ctx, bot_id=222222, child=ChildInfo(owner_id=OPERATOR, template="channelmanager", factory_username="factory"))
    await SenderService(child_ctx).stopping("delete")
    async with ctx.sm() as session:
        await session.execute(delete(ChildBot).where(ChildBot.bot_id == 222222))
        await session.execute(delete(BotRecord).where(BotRecord.id == 222222))
        await session.commit()
    async with ctx.sm() as session:
        assert await session.get(Post, (222222, "p" * 16)) is None
        assert await session.get(Post, (333333, "p" * 16)) is not None
        assert (await session.get(Channel, (BOT_ID, CHANNEL_ID))).sender_paused
        assert (await session.get(ChannelInvoice, (BOT_ID, invoice.id))).status == "paid"
        assert await session.scalar(select(func.count()).select_from(ChannelGrant)) == 1


async def test_growth_operation_foreign_keys_reject_cross_channel_action(pg_growth):
    ctx, _ = pg_growth
    async with ctx.sm() as session:
        session.add(Channel(bot_id=BOT_ID, channel_id=CHANNEL_ID - 1, title="Other"))
        session.add(GrowthAction(bot_id=BOT_ID, id="a" * 32, channel_id=CHANNEL_ID, actor_id=OPERATOR, kind="reveal",
            dedupe_key="action", payload={}))
        await session.commit()
    with pytest.raises(IntegrityError):
        async with ctx.sm() as session:
            session.add(Operation(bot_id=BOT_ID, id="o" * 32, channel_id=CHANNEL_ID - 1, generation=1,
                kind="growth_reveal", growth_action_id="a" * 32, dedupe_key="bad", payload={"action_id": "a" * 32}))
            await session.commit()


@pytest.mark.skipif(not REDIS_URL, reason="TEST_CHM_REDIS_URL not set")
async def test_growth_shares_real_redis_sender_budget(pg_growth):
    ctx, _ = pg_growth
    parsed = make_url(REDIS_URL.replace("redis://", "postgresql://", 1))
    assert parsed.host in {"127.0.0.1", "localhost"} and parsed.port == 56388
    redis = from_url(REDIS_URL)
    try:
        scoped = replace(ctx, redis=redis)
        await redis.delete(ctx.keys("send-rate", "bot"), ctx.keys("send-rate", "chat", 77))
        assert await REAL_RESERVE(scoped, 77) == 0
        assert await REAL_RESERVE(scoped, 77) == 1
    finally:
        await redis.aclose()
