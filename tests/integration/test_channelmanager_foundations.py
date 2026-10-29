"""Run only against an explicitly named disposable Channel Manager database."""

from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import replace

import pytest
from aiogram import Bot
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from redis.asyncio import from_url
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from bots.channelmanager import ingress, outbox
from bots.channelmanager.models import ChannelRole, Event, Inbox, Operation
from core.db.base import Base, create_engine, create_sessionmaker, upsert
from core.db.migrate import alembic_config, upgrade
from core.db.models import Bot as BotRecord
from core.redis import KeySpace
from core.runtime.dispatcher import build_dispatcher
from core.sdk.registry import discover
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR, admin_member, membership_update
from tests.conftest import BOT_ID, RecordingSession, build_test_ctx

URL = os.environ.get("TEST_CHM_DATABASE_URL")


def checked_url() -> str:
    assert URL
    parsed = make_url(URL)
    assert parsed.host in {"127.0.0.1", "localhost"}
    assert (parsed.database or "").startswith("channelmanager_phase1_test")
    return URL


@pytest.mark.skipif(not URL, reason="TEST_CHM_DATABASE_URL not set")
def test_channelmanager_migration_round_trip():
    url = checked_url()
    upgrade(url)
    cfg = alembic_config(url)
    command.downgrade(cfg, "0018_gg_fed_enforcement")
    command.upgrade(cfg, "head")

    async def diff():
        engine = create_engine(url)
        try:
            async with engine.connect() as connection:
                return await connection.run_sync(lambda c: compare_metadata(
                    MigrationContext.configure(c, opts={"compare_type": True}), Base.metadata))
        finally:
            await engine.dispose()

    assert asyncio.run(diff()) == []


@pytest.mark.skipif(not URL, reason="TEST_CHM_DATABASE_URL not set")
async def test_concurrent_claims_ingress_and_namespace_constraints(redis, tmp_path):
    url = checked_url()
    engine = create_engine(url)
    sm = create_sessionmaker(engine)
    try:
        async with sm() as session:
            for bot_id, slug in [(BOT_ID, "channelmanager"), (222222, "chm_other")]:
                await session.execute(upsert(session, BotRecord).values(id=bot_id, slug=slug, title=slug, active=True)
                    .on_conflict_do_nothing())
            await session.commit()
        api = RecordingSession()
        ctx = await build_test_ctx(discover(["channelmanager"])[0], sm, redis, api, tmp_path)
        api.responses["GetChatMember"] = lambda method: admin_member(method.user_id)
        dp = build_dispatcher(ctx)
        event = membership_update(100001)
        await asyncio.gather(*(dp.feed_update(ctx.bot, event) for _ in range(12)))
        assert sum(await asyncio.gather(*(ingress.process_one(ctx) for _ in range(8)))) == 1
        async with sm() as session:
            assert len((await session.scalars(select(Inbox))).all()) == 1
            assert len((await session.scalars(select(Event))).all()) == 1

        # A role in bot B cannot refer to a channel owned only by bot A.
        with pytest.raises(IntegrityError):
            async with sm() as session:
                session.add(ChannelRole(bot_id=222222, channel_id=CHANNEL_ID, user_id=OPERATOR))
                await session.commit()

        channel = await ctx.extras["channelmanager"].get(CHANNEL_ID)
        async with sm() as session:
            for n in range(12):
                await outbox.enqueue(session, ctx, channel, kind="notice", dedupe_key=f"pg:{n}",
                                     payload={"recipient_id": OPERATOR, "text": "test"})
            await session.commit()
        claims = await asyncio.gather(*(outbox.claim(ctx) for _ in range(12)))
        assert all(claims) and len({op.id for op in claims}) == 12
        assert await outbox.claim(ctx) is None

        other = replace(ctx, bot_id=222222, bot=Bot(token="222222:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", session=api))
        assert await outbox.claim(other) is None
        async with sm() as session:
            with pytest.raises(ValueError, match="namespace"):
                await outbox.enqueue(session, other, channel, kind="notice", dedupe_key="cross-bot",
                                     payload={"recipient_id": OPERATOR, "text": "wrong bot"})
            assert len((await session.scalars(select(Operation))).all()) == 12
    finally:
        await engine.dispose()


@pytest.mark.skipif(not os.environ.get("TEST_CHM_REDIS_URL"), reason="TEST_CHM_REDIS_URL not set")
async def test_real_redis_atomic_sender_budget(sm, api, tmp_path):
    redis = from_url(os.environ["TEST_CHM_REDIS_URL"])
    ctx = await build_test_ctx(discover(["channelmanager"])[0], sm, redis, api, tmp_path)
    ctx.keys = KeySpace("chmtest_" + uuid.uuid4().hex[:12])
    try:
        waits = await asyncio.gather(*(outbox.reserve_budget(ctx, n) for n in range(1, 51)))
        assert waits.count(0) == 25 and all(wait >= 0 for wait in waits)
    finally:
        keys = [key async for key in redis.scan_iter(match=ctx.keys() + "*")]
        if keys:
            await redis.delete(*keys)
        await redis.aclose()
