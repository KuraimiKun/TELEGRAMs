"""Phase 3 migrations and locking against an explicitly disposable loopback database."""

from __future__ import annotations

import asyncio
import os
from datetime import timedelta

import pytest
from aiogram.types import Chat
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import MetaData, Table, delete, func, insert, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import make_url

from bots.channelmanager import interactions, outbox
from bots.channelmanager.content import ContentError, PostSpec, TextBody
from bots.channelmanager.models import (
    CalendarReservation,
    Channel,
    Delivery,
    Occurrence,
    Post,
    PostVersion,
    Vote,
    VoteBoard,
)
from bots.channelmanager.timing import Rule
from core.db.base import Base, create_engine, create_sessionmaker, upsert, utcnow
from core.db.migrate import alembic_config, upgrade
from core.db.models import Bot as BotRecord
from core.db.models import BotSetting
from core.sdk.registry import discover
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR, admin_member, insert_legacy
from tests.bots.channelmanager.test_advanced import make_batch
from tests.bots.channelmanager.test_publishing import drain
from tests.conftest import BOT_ID, RecordingSession, build_test_ctx

URL = os.environ.get("TEST_CHM_ADVANCED_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_CHM_ADVANCED_DATABASE_URL not set")


def checked_url():
    assert URL
    parsed = make_url(URL)
    assert parsed.drivername == "postgresql+asyncpg" and parsed.host in {"127.0.0.1", "localhost"}
    assert (parsed.database or "").startswith("channelmanager_phase3_test")
    return URL


def test_advanced_migration_preserves_sent_delivery_and_matches_models():
    url = checked_url()
    upgrade(url)
    cfg = alembic_config(url)
    command.downgrade(cfg, "0018_gg_fed_enforcement")
    command.upgrade(cfg, "0020_chm_publishing")

    async def seed():
        engine = create_engine(url)
        try:
            async with engine.begin() as connection:
                await connection.execute(pg_insert(BotRecord).values(id=BOT_ID, slug="channelmanager", title="Test", active=True).on_conflict_do_nothing())
                await insert_legacy(connection, Channel, bot_id=BOT_ID, channel_id=CHANNEL_ID, title="Preserved")
                await connection.execute(insert(Post).values(bot_id=BOT_ID, id="a" * 16, channel_id=CHANNEL_ID, creator_id=OPERATOR, target_ids=[CHANNEL_ID]))
                await connection.execute(insert(PostVersion).values(bot_id=BOT_ID, post_id="a" * 16, number=1,
                    spec=PostSpec(body=TextBody(text="Preserved")).model_dump(mode="json")))
                def old_delivery(sync):
                    table = Table("chm_deliveries", MetaData(), autoload_with=sync)
                    sync.execute(table.insert().values(bot_id=BOT_ID, id="b" * 32, post_id="a" * 16, channel_id=CHANNEL_ID,
                        version=1, generation=1, actor_id=OPERATOR, state="sent", message_id=789, sent_at=utcnow(),
                        edit_status="none", pin_status="none", delete_status="pending", created_at=utcnow()))
                await connection.run_sync(old_delivery)
        finally:
            await engine.dispose()

    asyncio.run(seed())
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "0020_chm_publishing")
    command.upgrade(cfg, "head")

    async def check():
        engine = create_engine(url)
        try:
            async with engine.connect() as connection:
                target = (await connection.execute(select(Delivery.message_id, Delivery.delete_status, Delivery.markup_status))).one()
                assert tuple(target) == (789, "pending", "none")
                return await connection.run_sync(lambda c: compare_metadata(MigrationContext.configure(c, opts={"compare_type": True}), Base.metadata))
        finally:
            await engine.dispose()
    assert asyncio.run(check()) == []


@pytest.fixture
async def pg_advanced(redis, tmp_path, monkeypatch):
    url = checked_url()
    await asyncio.to_thread(upgrade, url)
    engine = create_engine(url)
    sm = create_sessionmaker(engine)
    api = RecordingSession()
    try:
        async with sm() as session:
            await session.execute(text("TRUNCATE chm_channels, chm_presets CASCADE"))
            await session.execute(delete(BotSetting).where(BotSetting.bot_id == BOT_ID))
            await session.execute(upsert(session, BotRecord).values(id=BOT_ID, slug="channelmanager", title="Test", active=True).on_conflict_do_nothing())
            await session.commit()
        ctx = await build_test_ctx(discover(["channelmanager"])[0], sm, redis, api, tmp_path)
        api.responses["GetChat"] = lambda method: Chat(id=int(method.chat_id), type="channel", title="PG phase 3")
        api.responses["GetChatMember"] = lambda method: admin_member(method.user_id)
        async def immediate(*args):
            return 0
        monkeypatch.setattr(outbox, "reserve_budget", immediate)
        await ctx.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
        yield ctx, api
    finally:
        await api.close()
        await engine.dispose()


async def test_concurrent_calendar_plans_have_no_overlapping_reservations(pg_advanced):
    ctx, api = pg_advanced
    first, second = await make_batch(ctx, api), await make_batch(ctx, api)
    svc = ctx.extras["batches"]
    calendar = await svc.save_calendar(CHANNEL_ID, OPERATOR, "Weekly", "UTC", [{"weekday": d, "at": "09:00"} for d in range(7)])
    start = utcnow() + timedelta(hours=1)
    expected = await svc.preview(first.id, OPERATOR, start=start, calendar_id=calendar.id)
    results = await asyncio.gather(*(svc.schedule(batch.id, OPERATOR, batch.generation, start=start,
        calendar_id=calendar.id, expected=expected) for batch in (first, second)), return_exceptions=True)
    assert sum(not isinstance(r, Exception) for r in results) == 1
    assert [str(r) for r in results if isinstance(r, Exception)] == ["stale_plan"]
    loser = first if isinstance(results[0], Exception) else second
    later = await svc.preview(loser.id, OPERATOR, start=start, calendar_id=calendar.id)
    await svc.schedule(loser.id, OPERATOR, loser.generation, start=start, calendar_id=calendar.id, expected=later)
    async with ctx.sm() as session:
        reserved = (await session.scalars(select(CalendarReservation.run_at))).all()
        assert len(reserved) == len(set(reserved)) == 4


async def test_concurrent_vote_callbacks_are_idempotent_and_closed_board_stays_closed(pg_advanced):
    ctx, _ = pg_advanced
    post = await ctx.extras["posts"].create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text="PG votes"), reactions=["A", "B"]))
    post = await ctx.extras["posts"].publish(post.id, OPERATOR, post.generation)
    await drain(ctx)
    target = (await ctx.extras["posts"].view(post.id, OPERATOR)).deliveries[0]
    results = await asyncio.gather(*(interactions.cast(ctx, target.id, 1, 77, 40) for _ in range(20)))
    assert results.count(True) == 1
    await asyncio.gather(*(interactions.cast(ctx, target.id, 1, n, 41) for n in range(100, 110)))
    await interactions.close(ctx, post.id, OPERATOR, post.generation)
    with pytest.raises(ContentError, match="closed"):
        await interactions.cast(ctx, target.id, 1, 77, 41)
    async with ctx.sm() as session:
        assert await session.scalar(select(func.count()).select_from(Vote)) == 11
        board = await session.get(VoteBoard, (BOT_ID, target.id, 1))
        assert board.closed and board.revision == 12
    await ctx.extras["posts"].edit(post.id, OPERATOR, post.generation,
        PostSpec(body=TextBody(text="Body edit keeps votes"), reactions=["A", "B"]))
    await drain(ctx)
    async with ctx.sm() as session:
        assert (await session.get(VoteBoard, (BOT_ID, target.id, 2))).closed
        assert await session.scalar(select(func.count()).select_from(Vote).where(Vote.version == 2)) == 11


async def test_duplicate_recurrence_sweeps_and_config_quota_are_serialized(pg_advanced, monkeypatch):
    from bots.channelmanager import delivery, posts, recurring

    ctx, _ = pg_advanced
    svc = ctx.extras["posts"]
    roots = [await svc.create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text=str(n)))) for n in range(2)]
    await ctx.settings.set("max_recurrences_per_operator", 1)
    point = utcnow().replace(second=0, microsecond=0) + timedelta(minutes=1)
    rule = Rule(anchor=point, every_minutes=60)
    results = await asyncio.gather(*(ctx.extras["recurring"].configure(p.id, OPERATOR, p.generation, rule) for p in roots), return_exceptions=True)
    assert sum(not isinstance(r, Exception) for r in results) == 1
    assert [str(r) for r in results if isinstance(r, Exception)] == ["limit"]
    for module in (recurring, delivery, posts, outbox):
        monkeypatch.setattr(module, "utcnow", lambda: point)
    made = await asyncio.gather(*(ctx.extras["recurring"].sweep() for _ in range(6)))
    assert sum(made) == 1
    await drain(ctx)
    async with ctx.sm() as session:
        assert await session.scalar(select(func.count()).select_from(Occurrence)) == 1
        assert await session.scalar(select(func.count()).select_from(Delivery)) == 1


async def test_replacement_commit_does_not_wait_on_another_occurrence_lock(pg_advanced, monkeypatch):
    from bots.channelmanager import recurring
    from tests.bots.channelmanager.test_advanced import make_series

    ctx, api = pg_advanced
    _root, _series, clock = await make_series(ctx, api, monkeypatch, replace=True)
    await ctx.extras["recurring"].sweep()
    await drain(ctx)
    async with ctx.sm() as session:
        previous = await session.scalar(select(Delivery))
    clock[0] += timedelta(hours=1)
    await ctx.extras["recurring"].sweep()
    async with ctx.sm() as held:
        await held.get(Post, (BOT_ID, previous.post_id), with_for_update=True)
        job = await outbox.claim(ctx)
        assert job.kind == "publish"
        await asyncio.wait_for(outbox.execute(ctx, job), timeout=5)
        async with ctx.sm() as session:
            current = await session.scalar(select(Delivery).where(Delivery.id != previous.id))
            assert current.state == "sent" and current.replace_pending
        await held.rollback()
    await recurring.settle_replacements(ctx)
    await drain(ctx)
    assert len(api.calls("DeleteMessage")) == 1


async def test_post_lock_refreshes_previously_read_generation(pg_advanced):
    ctx, _ = pg_advanced
    svc = ctx.extras["posts"]
    post = await svc.create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text="Refresh fencing")))
    async with ctx.sm() as session:
        cached = await session.get(Post, (BOT_ID, post.id))
        async with ctx.sm() as other:
            await other.execute(update(Post).where(Post.bot_id == BOT_ID, Post.id == post.id).values(generation=2))
            await other.commit()
        with pytest.raises(ContentError, match="stale"):
            await svc.locked(session, cached.id, 1)
