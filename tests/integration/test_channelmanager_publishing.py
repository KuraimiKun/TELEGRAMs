"""Publishing checks against an explicitly named disposable PostgreSQL database."""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import timedelta

import pytest
from aiogram.types import Chat
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import exists, insert, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from bots.channelmanager import delivery, outbox
from bots.channelmanager.content import PostSpec, TextBody
from bots.channelmanager.models import Channel, Delivery, Entitlement, Operation, Post, PostSchedule
from core.db.base import Base, create_engine, create_sessionmaker, upsert, utcnow
from core.db.migrate import alembic_config, upgrade
from core.db.models import Bot as BotRecord
from core.sdk.registry import discover
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR, admin_member, insert_legacy
from tests.bots.channelmanager.test_publishing import channel_sends, drain
from tests.conftest import BOT_ID, RecordingSession, build_test_ctx

URL = os.environ.get("TEST_CHM_PUBLISH_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_CHM_PUBLISH_DATABASE_URL not set")


def checked_url() -> str:
    assert URL
    parsed = make_url(URL)
    assert parsed.drivername == "postgresql+asyncpg"
    assert parsed.host in {"127.0.0.1", "localhost"}
    assert (parsed.database or "").startswith("channelmanager_phase2_test")
    return URL


def test_publishing_migration_preserves_foundation_records_and_matches_models():
    url = checked_url()
    upgrade(url)
    cfg = alembic_config(url)
    command.downgrade(cfg, "0018_gg_fed_enforcement")
    command.upgrade(cfg, "0019_chm_foundations")

    async def seed():
        engine = create_engine(url)
        try:
            async with engine.begin() as connection:
                await connection.execute(pg_insert(BotRecord).values(id=BOT_ID, slug="channelmanager", title="Test", active=True)
                    .on_conflict_do_nothing())
                await insert_legacy(connection, Channel, bot_id=BOT_ID, channel_id=CHANNEL_ID, title="Preserved")
                await connection.execute(insert(Operation).values(bot_id=BOT_ID, id="a" * 32, channel_id=CHANNEL_ID,
                    generation=1, kind="notice", dedupe_key="pre-publishing", payload={"recipient_id": OPERATOR, "text": "Preserved"}))
        finally:
            await engine.dispose()

    asyncio.run(seed())
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "0019_chm_foundations")
    command.upgrade(cfg, "head")

    async def check():
        engine = create_engine(url)
        try:
            async with engine.connect() as connection:
                assert await connection.scalar(select(Channel.title).where(Channel.bot_id == BOT_ID)) == "Preserved"
                assert await connection.scalar(select(Operation.dedupe_key).where(Operation.bot_id == BOT_ID)) == "pre-publishing"
                assert await connection.scalar(select(Operation.delivery_id).where(Operation.bot_id == BOT_ID)) is None
                return await connection.run_sync(lambda c: compare_metadata(
                    MigrationContext.configure(c, opts={"compare_type": True}), Base.metadata))
        finally:
            await engine.dispose()

    assert asyncio.run(check()) == []


@pytest.fixture
async def pg_chm(redis, tmp_path, monkeypatch):
    url = checked_url()
    await asyncio.to_thread(upgrade, url)
    engine = create_engine(url)
    sm = create_sessionmaker(engine)
    api = RecordingSession()
    try:
        async with sm() as session:
            # Only the validated disposable database above can reach this cleanup.
            await session.execute(text("TRUNCATE chm_channels CASCADE"))
            for bot_id, slug in [(BOT_ID, "channelmanager"), (222222, "chm_pg_other")]:
                await session.execute(upsert(session, BotRecord).values(id=bot_id, slug=slug, title=slug, active=True)
                    .on_conflict_do_nothing())
            await session.commit()
        ctx = await build_test_ctx(discover(["channelmanager"])[0], sm, redis, api, tmp_path)
        api.responses["GetChat"] = lambda method: Chat(id=int(method.chat_id), type="channel", title="PG test")
        api.responses["GetChatMember"] = lambda method: admin_member(method.user_id)

        async def immediate(*args):
            return 0
        monkeypatch.setattr(outbox, "reserve_budget", immediate)
        await ctx.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
        yield ctx, api
    finally:
        await api.close()
        await engine.dispose()


async def test_concurrent_schedule_limits_and_duplicate_confirmations(pg_chm):
    ctx, _ = pg_chm
    svc = ctx.extras["posts"]
    first = await svc.create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text="First")))
    second = await svc.create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text="Second")))
    async with ctx.sm() as session:
        await session.execute(update(Entitlement).values(max_schedules=1))
        await session.commit()
    when = utcnow() + timedelta(hours=1)
    results = await asyncio.gather(*(svc.publish(p.id, OPERATOR, p.generation, run_at=when) for p in (first, second)), return_exceptions=True)
    assert sum(not isinstance(r, Exception) for r in results) == 1
    assert [str(r) for r in results if isinstance(r, Exception)] == ["limit"]
    winner = next(r for r in results if not isinstance(r, Exception))
    results = await asyncio.gather(*(svc.publish(winner.id, OPERATOR, winner.generation) for _ in range(2)), return_exceptions=True)
    assert sum(not isinstance(r, Exception) for r in results) == 1
    assert [str(r) for r in results if isinstance(r, Exception)] == ["stale"]
    await drain(ctx)
    async with ctx.sm() as session:
        assert len((await session.scalars(select(Delivery))).all()) == 1


async def test_dispatch_waits_for_committed_post_mutation(pg_chm):
    ctx, api = pg_chm
    svc = ctx.extras["posts"]
    post = await svc.create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text="Never obsolete")))
    post = await svc.publish(post.id, OPERATOR, post.generation)
    op = await outbox.claim(ctx)
    while op.kind != "publish":
        await outbox.execute(ctx, op)
        op = await outbox.claim(ctx)
    started = asyncio.Event()

    async def attempt():
        started.set()
        return await outbox.mark_dispatched(ctx, op, conditions=[exists().where(
            Post.bot_id == BOT_ID, Post.id == post.id, Post.generation == post.generation)])

    async with ctx.sm() as session:
        await svc.locked(session, post.id, post.generation)
        task = asyncio.create_task(attempt())
        await started.wait()
        await asyncio.sleep(0.05)
        assert not task.done(), "dispatch must wait for the operator's post lock"
        await svc.cancel_ops(session, post)
        await session.commit()
    assert not await task
    await delivery.reconcile(ctx)
    assert not channel_sends(api)
    assert (await svc.view(post.id, OPERATOR)).state == "cancelled"


async def test_delivery_namespace_and_target_constraints(pg_chm):
    ctx, _ = pg_chm
    svc = ctx.extras["posts"]
    post = await svc.create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text="Scoped")))
    await svc.publish(post.id, OPERATOR, post.generation, run_at=utcnow() + timedelta(hours=1))
    async with ctx.sm() as session:
        target = await session.scalar(select(Delivery))
    second = CHANNEL_ID - 1
    await ctx.extras["channelmanager"].connect(second, OPERATOR)
    async with ctx.sm() as session:
        session.add(Channel(bot_id=222222, channel_id=CHANNEL_ID, title="Other bot"))
        await session.commit()
    for bot_id, channel_id in [(BOT_ID, second), (222222, CHANNEL_ID)]:
        with pytest.raises(IntegrityError):
            async with ctx.sm() as session:
                session.add(Operation(bot_id=bot_id, id=uuid.uuid4().hex, channel_id=channel_id, delivery_id=target.id,
                    generation=1, kind="publish", dedupe_key=uuid.uuid4().hex, payload={}))
                await session.commit()
    with pytest.raises(IntegrityError):
        async with ctx.sm() as session:
            session.add(Delivery(bot_id=BOT_ID, id=uuid.uuid4().hex, post_id=post.id, channel_id=CHANNEL_ID,
                version=1, generation=1, actor_id=OPERATOR))
            await session.commit()


async def test_persisted_schedule_runs_after_rebuilding_service_context(pg_chm, redis, tmp_path):
    ctx, api = pg_chm
    svc = ctx.extras["posts"]
    post = await svc.create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text="Original")))
    post = await svc.publish(post.id, OPERATOR, post.generation, run_at=utcnow() + timedelta(hours=1))
    await svc.edit(post.id, OPERATOR, post.generation, PostSpec(body=TextBody(text="After restart")))
    async with ctx.sm() as session:
        await session.execute(update(Operation).where(Operation.kind == "publish", Operation.status == "pending").values(run_at=utcnow()))
        await session.execute(update(PostSchedule).values(run_at=utcnow()))
        await session.commit()
    restarted = await build_test_ctx(discover(["channelmanager"])[0], ctx.sm, redis, api, tmp_path)
    await drain(restarted)
    assert [m.text for m in channel_sends(api)] == ["After restart"]
    assert (await restarted.extras["posts"].view(post.id, OPERATOR)).state == "sent"
