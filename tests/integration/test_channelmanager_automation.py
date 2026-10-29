"""Source automation migration, namespace and concurrency checks on disposable PostgreSQL."""

from __future__ import annotations

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

from bots.channelmanager import automation, automation_delivery, ingress, outbox
from bots.channelmanager.auto_content import RouteSpec, RuleSpec
from bots.channelmanager.content import TextBody
from bots.channelmanager.models import (
    AutoAction,
    AutoPart,
    AutoSnapshot,
    AutoSource,
    Channel,
    Delivery,
    Inbox,
    Operation,
    Post,
    PostVersion,
)
from core.db.base import Base, create_engine, create_sessionmaker, upsert, utcnow
from core.db.migrate import alembic_config, upgrade
from core.db.models import Bot as BotRecord
from core.db.models import BotSetting
from core.runtime.dispatcher import build_dispatcher
from core.sdk.registry import discover
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR, insert_legacy
from tests.bots.channelmanager.test_automation import (
    DESTINATION,
    ingest_all,
    plan_all,
    setup_automation,
    source_update,
)
from tests.bots.channelmanager.test_publishing import drain
from tests.conftest import BOT_ID, RecordingSession, build_test_ctx

URL = os.environ.get("TEST_CHM_AUTOMATION_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_CHM_AUTOMATION_DATABASE_URL not set")


def checked_url():
    assert URL
    parsed = make_url(URL)
    assert parsed.drivername == "postgresql+asyncpg" and parsed.host in {"127.0.0.1", "localhost"}
    assert (parsed.database or "").startswith("channelmanager_phase4_test")
    return URL


def test_automation_migration_preserves_prior_deliveries_and_operations():
    url = checked_url()
    upgrade(url)
    cfg = alembic_config(url)
    command.downgrade(cfg, "0018_gg_fed_enforcement")
    command.upgrade(cfg, "0021_chm_advanced")

    async def seed():
        engine = create_engine(url)
        try:
            async with engine.begin() as connection:
                await connection.execute(pg_insert(BotRecord).values(id=BOT_ID, slug="channelmanager", title="Test", active=True).on_conflict_do_nothing())
                await insert_legacy(connection, Channel, bot_id=BOT_ID, channel_id=CHANNEL_ID, title="Preserved")
                await connection.execute(insert(Post).values(bot_id=BOT_ID, id="a" * 16, channel_id=CHANNEL_ID, creator_id=OPERATOR, target_ids=[CHANNEL_ID]))
                await connection.execute(insert(PostVersion).values(bot_id=BOT_ID, post_id="a" * 16, number=1, spec={"body": {"text": "Preserved"}}))
                await connection.execute(insert(Delivery).values(bot_id=BOT_ID, id="b" * 32, post_id="a" * 16, channel_id=CHANNEL_ID,
                    version=1, generation=1, actor_id=OPERATOR, state="sent", message_id=789, replace_pending=True))
                def old_operation(sync):
                    table = Table("chm_operations", MetaData(), autoload_with=sync)
                    sync.execute(table.insert().values(bot_id=BOT_ID, id="c" * 32, channel_id=CHANNEL_ID, generation=1, kind="notice",
                        dedupe_key="preserved", payload={"recipient_id": OPERATOR, "text": "Preserved"}, status="pending", attempts=0,
                        max_attempts=5, run_at=utcnow(), dispatched=False, created_at=utcnow(), updated_at=utcnow()))
                await connection.run_sync(old_operation)
        finally:
            await engine.dispose()
    asyncio.run(seed())
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "0021_chm_advanced")
    command.upgrade(cfg, "head")

    async def check():
        engine = create_engine(url)
        try:
            async with engine.connect() as connection:
                assert (await connection.execute(select(Delivery.message_id, Delivery.replace_pending))).one() == (789, True)
                assert (await connection.execute(select(Operation.dedupe_key, Operation.automation_id))).one() == ("preserved", None)
                return await connection.run_sync(lambda c: compare_metadata(MigrationContext.configure(c, opts={"compare_type": True}), Base.metadata))
        finally:
            await engine.dispose()
    assert asyncio.run(check()) == []


@pytest.fixture
async def pg_automation(redis, tmp_path, monkeypatch):
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
            for bot_id, slug in [(BOT_ID, "channelmanager"), (222222, "chm_auto_other")]:
                await session.execute(upsert(session, BotRecord).values(id=bot_id, slug=slug, title=slug, active=True).on_conflict_do_nothing())
            await session.commit()
        ctx = await build_test_ctx(discover(["channelmanager"])[0], sm, redis, api, tmp_path)
        async def immediate(*args):
            return 0
        monkeypatch.setattr(outbox, "reserve_budget", immediate)
        await setup_automation(ctx, api, rule=RuleSpec(header=TextBody(text="Header")))
        yield ctx, api
    finally:
        await api.close()
        await engine.dispose()


async def test_duplicate_receipts_and_concurrent_planners_create_one_version(pg_automation):
    ctx, api = pg_automation
    dp = build_dispatcher(ctx)
    event = source_update()
    await asyncio.gather(*(dp.feed_update(ctx.bot, event) for _ in range(12)))
    assert sum(await asyncio.gather(*(ingress.process_one(ctx) for _ in range(6)))) == 1
    assert sum(await asyncio.gather(*(automation.plan_one(ctx) for _ in range(6)))) == 1
    await drain(ctx)
    async with ctx.sm() as session:
        assert await session.scalar(select(func.count()).select_from(AutoSource)) == 1
        assert await session.scalar(select(func.count()).select_from(AutoPart)) == 1
        assert await session.scalar(select(func.count()).select_from(AutoSnapshot)) == 1
        assert await session.scalar(select(func.count()).select_from(AutoAction).where(AutoAction.kind == "copy")) == 1
    assert len([m for m in api.calls("EditMessageText") if m.chat_id == CHANNEL_ID]) == 1


async def test_concurrent_route_activation_cannot_create_cycle(pg_automation):
    ctx, _ = pg_automation
    svc = ctx.extras["automation"]
    existing = (await svc.routes(CHANNEL_ID, OPERATOR))[0]
    await svc.stop("route", existing.id, OPERATOR, existing.generation)
    results = await asyncio.gather(svc.save_route(CHANNEL_ID, OPERATOR, "A to B", DESTINATION, RouteSpec(), active=True),
        svc.save_route(DESTINATION, OPERATOR, "B to A", CHANNEL_ID, RouteSpec(), active=True), return_exceptions=True)
    assert sum(not isinstance(r, Exception) for r in results) == 1
    assert [str(r) for r in results if isinstance(r, Exception)] == ["route_cycle"]


async def test_operation_automation_scope_rejects_cross_bot_and_source_channel(pg_automation):
    ctx, _ = pg_automation
    dp = build_dispatcher(ctx)
    await ingest_all(ctx, dp, source_update())
    await plan_all(ctx)
    async with ctx.sm() as session:
        action = await session.scalar(select(AutoAction))
        session.add(Channel(bot_id=222222, channel_id=CHANNEL_ID, title="Other bot"))
        await session.commit()
    for bot_id, channel_id in [(222222, CHANNEL_ID), (BOT_ID, DESTINATION)]:
        with pytest.raises(IntegrityError):
            async with ctx.sm() as session:
                session.add(Operation(bot_id=bot_id, id=uuid.uuid4().hex, channel_id=channel_id, generation=1,
                    kind="auto_copy", dedupe_key=uuid.uuid4().hex, automation_id=action.id, payload={"action_id": action.id}))
                await session.commit()


async def next_auto(ctx):
    while True:
        op = await outbox.claim(ctx)
        assert op is not None
        if op.automation_id:
            return op
        await outbox.execute(ctx, op)


async def test_dispatch_waits_for_source_version_change_and_cancels_stale_work(pg_automation):
    ctx, api = pg_automation
    await ingest_all(ctx, build_dispatcher(ctx), source_update())
    await plan_all(ctx)
    op = await next_auto(ctx)
    async with ctx.sm() as session:
        action = await session.get(AutoAction, (BOT_ID, op.automation_id))
    async with ctx.sm() as held:
        source = await held.get(AutoSource, (BOT_ID, action.source_id), with_for_update=True)
        task = asyncio.create_task(outbox.execute(ctx, op))
        await asyncio.sleep(0.05)
        assert not task.done()
        source.generation += 1
        await held.commit()
    await asyncio.wait_for(task, timeout=5)
    async with ctx.sm() as session:
        assert (await session.get(AutoAction, (BOT_ID, action.id))).status == "cancelled"
    assert not [m for m in api.calls("SendMessage") if m.chat_id == DESTINATION]


async def test_configuration_change_and_inflight_completion_do_not_deadlock(pg_automation):
    ctx, _ = pg_automation
    await ingest_all(ctx, build_dispatcher(ctx), source_update())
    await plan_all(ctx)
    op = await next_auto(ctx)
    async with ctx.sm() as session:
        action = await session.get(AutoAction, (BOT_ID, op.automation_id))
    assert await automation_delivery.mark(ctx, op, action)
    op.dispatched = True
    rule = (await ctx.extras["automation"].rules(CHANNEL_ID, OPERATOR))[0]
    await asyncio.wait_for(asyncio.gather(
        ctx.extras["automation"].save_rule(CHANNEL_ID, OPERATOR, rule.name, RuleSpec(header=TextBody(text="New")),
            active=True, resource_id=rule.id, generation=rule.generation),
        automation_delivery.finish(ctx, op, action, "succeeded", ids=[501] if action.kind == "edit" else [901])), timeout=5)
    async with ctx.sm() as session:
        assert (await session.get(AutoAction, (BOT_ID, action.id))).status == "succeeded"
