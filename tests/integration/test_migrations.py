"""Postgres-only checks. Run with TEST_DATABASE_URL=postgresql+asyncpg://user:pass@host/db (a disposable DB)."""

from __future__ import annotations

import asyncio
import os

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text

from core.db.base import Base, create_engine
from core.db.migrate import alembic_config, upgrade

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL not set")


async def _reset() -> None:
    engine = create_engine(URL)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await engine.dispose()


async def _diff() -> list:
    engine = create_engine(URL)
    async with engine.connect() as conn:
        diff = await conn.run_sync(
            lambda c: compare_metadata(MigrationContext.configure(c, opts={"compare_type": True}), Base.metadata)
        )
    await engine.dispose()
    return diff


def test_migrations_build_the_model_schema_and_round_trip():
    asyncio.run(_reset())
    upgrade(URL)
    assert asyncio.run(_diff()) == [], "models and migrations are out of sync: run `python -m core makemigrations`"

    cfg = alembic_config(URL)
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    assert asyncio.run(_diff()) == []


async def _concurrency_checks() -> None:
    from core.db.base import create_sessionmaker
    from core.db.models import Bot
    from core.services.payments import PaymentService
    from core.services.subscriptions import SubscriptionService
    from core.services.users import UserService

    engine = create_engine(URL)
    sm = create_sessionmaker(engine)
    async with sm() as s:
        s.add(Bot(id=1, slug="pgtest", title="t"))
        await s.commit()

    users = UserService(sm, bot_id=1)
    # A burst of updates from a brand-new user must not raise IntegrityError.
    results = await asyncio.gather(*(users.get_or_create(77, "u", "U", "en") for _ in range(10)))
    assert sum(1 for _u, new in results if new) == 1

    subs = SubscriptionService(sm, bot_id=1)
    payments = PaymentService(sm, bot_id=1, subs=subs)
    outcomes = await asyncio.gather(*(payments.record_payment(77, None, 100, 30, "dup-charge") for _ in range(5)))
    assert sum(1 for _until, created in outcomes if created) == 1

    # Concurrent grants must not lose updates (row lock).
    before = (await users.get(77)).vip_until
    await asyncio.gather(*(subs.grant_vip(77, 1) for _ in range(5)))
    after = (await users.get(77)).vip_until
    assert round((after - before).total_seconds() / 86400) == 5
    await engine.dispose()


def test_postgres_concurrency_paths():
    asyncio.run(_reset())
    upgrade(URL)
    asyncio.run(_concurrency_checks())


def test_groupguard_legacy_data_survives_foundation_upgrade():
    asyncio.run(_reset())
    cfg = alembic_config(URL)
    command.upgrade(cfg, "0009_doctools")

    async def seed():
        engine = create_engine(URL)
        async with engine.begin() as conn:
            await conn.execute(text("INSERT INTO bots (id,slug,title,active,created_at) VALUES (717,'legacyguard','Legacy',true,now())"))
            await conn.execute(text("""INSERT INTO gg_chats (bot_id,chat_id,config,created_at,updated_at)
                VALUES (717,-100717,CAST(:cfg AS jsonb),now(),now())"""),
                {"cfg": '{"welcome_text":"<b>Legacy</b>","external":{"opaque":7},"warn_limit":4}'})
            await conn.execute(text("""INSERT INTO gg_warns (bot_id,chat_id,user_id,reason,created_at)
                VALUES (717,-100717,27,'historical reason',now())"""))
            await conn.execute(text("""INSERT INTO gg_items (bot_id,chat_id,kind,key,text,media_kind,file_id,created_at)
                VALUES (717,-100717,'note','old phrase','<b>عربي</b>','photo','opaque-file',now())"""))
        await engine.dispose()

    async def verify():
        engine = create_engine(URL)
        async with engine.connect() as conn:
            chat = (await conn.execute(text("SELECT config,revision FROM gg_chats WHERE bot_id=717"))).one()
            assert chat.config["external"] == {"opaque": 7} and chat.revision == 0
            warn = (await conn.execute(text("SELECT reason,expires_at FROM gg_warns WHERE bot_id=717"))).one()
            assert warn.reason == "historical reason" and warn.expires_at is None
            item = (await conn.execute(text("SELECT key,text,file_id,format,options FROM gg_items WHERE bot_id=717"))).one()
            assert item.key == "old phrase" and item.text == "<b>عربي</b>" and item.file_id == "opaque-file"
            assert item.format == "html" and item.options == {}
        await engine.dispose()

    asyncio.run(seed())
    command.upgrade(cfg, "head")
    asyncio.run(verify())
    assert asyncio.run(_diff()) == []
