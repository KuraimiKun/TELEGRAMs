"""Membership schema preservation, isolation and row-lock behavior on disposable PostgreSQL."""

import asyncio
import os
import uuid

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import MetaData, Table, delete, func, insert, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from bots.channelmanager import ingress, member_delivery, member_interactions, members, outbox
from bots.channelmanager.member_specs import MemberSpec
from bots.channelmanager.models import (
    AutoAction,
    AutoSnapshot,
    AutoSource,
    Channel,
    Event,
    Inbox,
    JoinRequest,
    MemberAction,
    MemberGateReceipt,
    MemberHead,
    Operation,
)
from core.db.base import Base, create_engine, create_sessionmaker, upsert, utcnow
from core.db.migrate import alembic_config, upgrade
from core.db.models import Bot as BotRecord
from core.db.models import BotSetting
from core.runtime.dispatcher import build_dispatcher
from core.sdk.registry import discover
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR, insert_legacy
from tests.bots.channelmanager.test_members import (
    PERSON,
    ingest,
    join_event,
    latest,
    person,
    plan,
    setup_members,
)
from tests.bots.channelmanager.test_publishing import drain
from tests.conftest import BOT_ID, RecordingSession, build_test_ctx

URL = os.environ.get("TEST_CHM_MEMBERS_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_CHM_MEMBERS_DATABASE_URL not set")


def checked_url():
    assert URL
    parsed = make_url(URL)
    assert parsed.drivername == "postgresql+asyncpg" and parsed.host in {"127.0.0.1", "localhost"}
    assert (parsed.database or "").startswith("channelmanager_phase5_test")
    return URL


def test_membership_migration_preserves_automation_and_matches_models():
    url = checked_url()
    upgrade(url)
    cfg = alembic_config(url)
    command.downgrade(cfg, "0018_gg_fed_enforcement")
    command.upgrade(cfg, "0022_chm_automation")
    async def seed():
        engine = create_engine(url)
        try:
            async with engine.begin() as connection:
                await connection.execute(pg_insert(BotRecord).values(id=BOT_ID, slug="channelmanager", title="Test", active=True).on_conflict_do_nothing())
                await insert_legacy(connection, Channel, bot_id=BOT_ID, channel_id=CHANNEL_ID, title="Preserved")
                await connection.execute(insert(AutoSource).values(bot_id=BOT_ID, id="a" * 16, channel_id=CHANNEL_ID, source_key="message:501", status="planned"))
                await connection.execute(insert(AutoSnapshot).values(bot_id=BOT_ID, source_id="a" * 16, number=1, original=[], transformed=[]))
                await connection.execute(insert(AutoAction).values(bot_id=BOT_ID, id="b" * 32, channel_id=CHANNEL_ID, source_id="a" * 16,
                    version=1, action_key="route", kind="copy", actor_id=OPERATOR, destination_id=CHANNEL_ID - 1, control_generation=1,
                    payload={}, status="succeeded", remote_ids=[999]))
                def old_operation(sync):
                    table = Table("chm_operations", MetaData(), autoload_with=sync)
                    sync.execute(table.insert().values(bot_id=BOT_ID, id="c" * 32, channel_id=CHANNEL_ID, generation=1, kind="auto_copy",
                        dedupe_key="preserved", automation_id="b" * 32, payload={"action_id": "b" * 32}, status="succeeded", attempts=1,
                        max_attempts=5, run_at=utcnow(), dispatched=True, created_at=utcnow(), updated_at=utcnow()))
                await connection.run_sync(old_operation)
        finally:
            await engine.dispose()
    asyncio.run(seed())
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "0022_chm_automation")
    command.upgrade(cfg, "head")
    async def check():
        engine = create_engine(url)
        try:
            async with engine.connect() as connection:
                assert (await connection.execute(select(AutoAction.remote_ids))).scalar_one() == [999]
                assert (await connection.execute(select(Operation.automation_id, Operation.member_action_id))).one() == ("b" * 32, None)
                return await connection.run_sync(lambda c: compare_metadata(MigrationContext.configure(c, opts={"compare_type": True}), Base.metadata))
        finally:
            await engine.dispose()
    assert asyncio.run(check()) == []


@pytest.fixture
async def pg_members(redis, tmp_path, monkeypatch):
    url = checked_url()
    await asyncio.to_thread(upgrade, url)
    engine = create_engine(url)
    sm = create_sessionmaker(engine)
    api = RecordingSession()
    try:
        async with sm() as session:
            await session.execute(text("TRUNCATE chm_channels, chm_presets CASCADE"))
            await session.execute(delete(Inbox).where(Inbox.bot_id == BOT_ID))
            await session.execute(delete(BotSetting).where(BotSetting.bot_id == BOT_ID))
            for bot_id, slug in [(BOT_ID, "channelmanager"), (222222, "chm_members_other")]:
                await session.execute(upsert(session, BotRecord).values(id=bot_id, slug=slug, title=slug, active=True).on_conflict_do_nothing())
            await session.commit()
        ctx = await build_test_ctx(discover(["channelmanager"])[0], sm, redis, api, tmp_path)
        async def immediate(*args):
            return 0
        monkeypatch.setattr(outbox, "reserve_budget", immediate)
        await setup_members(ctx, api, MemberSpec(enabled=True, captcha=True))
        yield ctx, api
    finally:
        await api.close()
        await engine.dispose()


async def test_duplicate_receipts_and_planners_persist_one_request_and_contact(pg_members):
    ctx, _ = pg_members
    dp = build_dispatcher(ctx)
    event = join_event()
    await asyncio.gather(*(dp.feed_update(ctx.bot, event) for _ in range(12)))
    assert sum(await asyncio.gather(*(ingress.process_one(ctx) for _ in range(6)))) == 1
    await asyncio.gather(*(members.plan_one(ctx) for _ in range(6)))
    await drain(ctx)
    async with ctx.sm() as session:
        assert await session.scalar(select(func.count()).select_from(JoinRequest)) == 1
        assert await session.scalar(select(func.count()).select_from(MemberAction).where(MemberAction.kind == "contact")) == 1


async def test_duplicate_captcha_callbacks_serialize_and_consume_one_attempt(pg_members):
    ctx, _ = pg_members
    await ingest(ctx, build_dispatcher(ctx), join_event())
    row = await latest(ctx)
    wrong = (row.challenge["answer"] + 1) % 4
    await asyncio.gather(*(member_interactions.interact(ctx, row.id, person(), answer=wrong, generation=row.generation, receipt_id="same") for _ in range(6)))
    assert (await latest(ctx)).captcha_attempts == 1
    async with ctx.sm() as session:
        assert await session.scalar(select(func.count()).select_from(MemberGateReceipt)) == 1


async def next_member(ctx):
    while True:
        op = await outbox.claim(ctx)
        assert op is not None
        if op.member_action_id:
            return op
        await outbox.execute(ctx, op)


async def test_member_dispatch_waits_for_and_respects_new_head_generation(pg_members):
    ctx, api = pg_members
    await ingest(ctx, build_dispatcher(ctx), join_event())
    await plan(ctx)
    op = await next_member(ctx)
    async with ctx.sm() as held:
        await held.get(Channel, (BOT_ID, CHANNEL_ID), with_for_update=True)
        head = await held.get(MemberHead, (BOT_ID, CHANNEL_ID, PERSON), with_for_update=True)
        task = asyncio.create_task(outbox.execute(ctx, op))
        await asyncio.sleep(0.05)
        assert not task.done()
        head.generation += 1
        head.request_id = None
        await held.commit()
    await asyncio.wait_for(task, timeout=5)
    async with ctx.sm() as session:
        assert (await session.get(MemberAction, (BOT_ID, op.member_action_id))).status == "cancelled"
    assert not [m for m in api.calls("SendMessage") if m.chat_id == PERSON + 1000000]


async def test_configuration_save_and_dispatched_completion_do_not_deadlock(pg_members):
    ctx, _ = pg_members
    await ingest(ctx, build_dispatcher(ctx), join_event())
    await plan(ctx)
    op = await next_member(ctx)
    async with ctx.sm() as session:
        action = await session.get(MemberAction, (BOT_ID, op.member_action_id))
    assert await member_delivery.mark(ctx, op, action)
    op.dispatched = True
    config = await ctx.extras["members"].config(CHANNEL_ID, OPERATOR)
    await asyncio.wait_for(asyncio.gather(ctx.extras["members"].save(CHANNEL_ID, OPERATOR, MemberSpec(enabled=True), config.generation),
        member_delivery.finish(ctx, op, action, "succeeded")), timeout=5)
    async with ctx.sm() as session:
        assert (await session.get(MemberAction, (BOT_ID, action.id))).status == "succeeded"
    assert (await latest(ctx)).status == "held"


async def test_member_operation_foreign_key_rejects_cross_bot_and_channel(pg_members):
    ctx, _ = pg_members
    await ingest(ctx, build_dispatcher(ctx), join_event())
    await plan(ctx)
    async with ctx.sm() as session:
        action = await session.scalar(select(MemberAction))
        session.add(Channel(bot_id=222222, channel_id=CHANNEL_ID, title="Other bot"))
        session.add(Channel(bot_id=BOT_ID, channel_id=CHANNEL_ID - 1, title="Other source"))
        await session.commit()
    for bot_id, channel_id in [(222222, CHANNEL_ID), (BOT_ID, CHANNEL_ID - 1)]:
        with pytest.raises(IntegrityError):
            async with ctx.sm() as session:
                session.add(Operation(bot_id=bot_id, id=uuid.uuid4().hex, channel_id=channel_id, generation=1,
                    kind="member_contact", dedupe_key=uuid.uuid4().hex, member_action_id=action.id, payload={"action_id": action.id}))
                await session.commit()


async def test_concurrent_bulk_confirmation_releases_snapshot_once(pg_members):
    ctx, _ = pg_members
    await ingest(ctx, build_dispatcher(ctx), join_event())
    batch = await ctx.extras["members"].prepare_bulk(CHANNEL_ID, OPERATOR)
    results = await asyncio.gather(*(ctx.extras["members"].confirm_bulk(batch.id, OPERATOR) for _ in range(6)))
    assert all(r.result == {"selected": 1, "released": 1, "skipped": 0} for r in results)
    async with ctx.sm() as session:
        assert await session.scalar(select(func.count()).select_from(Event).where(Event.action == "members.bulk_release")) == 1
