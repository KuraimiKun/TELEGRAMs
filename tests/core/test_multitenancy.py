from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.db.base import Base
from core.db.models import Bot, BotUser, User
from core.redis import KeySpace
from core.sdk.registry import discover
from core.services.users import UserService


def test_keyspace_isolation():
    ks_social = KeySpace("socialdownload")
    ks_other = KeySpace("my_other_bot")

    assert ks_social("q", "high") == "socialdownload:q:high"
    assert ks_other("q", "high") == "my_other_bot:q:high"
    assert ks_social("fid", "abc12345") != ks_other("fid", "abc12345")


def test_bot_discovery():
    modules = discover(["socialdownload"])
    assert len(modules) == 1
    mod = modules[0]
    assert mod.slug == "socialdownload"
    assert mod.table_prefix == "sd_"
    assert "worker" in mod.processes()
    assert any(j.name == "cleanup" for j in mod.scheduled_jobs())


@pytest.mark.asyncio
async def test_user_membership_multitenancy():
    """Verify that a single Telegram user has completely separate memberships in different bots."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sm = async_sessionmaker(engine, expire_on_commit=False)

    # 1. Create two bots
    async with sm() as session:
        bot1 = Bot(id=1, slug="bot_one", title="Bot One", active=True)
        bot2 = Bot(id=2, slug="bot_two", title="Bot Two", active=True)
        session.add_all([bot1, bot2])
        await session.commit()

    user_svc_1 = UserService(sm, bot_id=1)
    user_svc_2 = UserService(sm, bot_id=2)

    user_id = 987654321

    # User registers in bot 1
    u1, is_new1 = await user_svc_1.get_or_create(
        user_id=user_id,
        username="alice",
        first_name="Alice",
        language_code="en",
    )
    assert is_new1 is True
    assert u1.bot_id == 1
    assert u1.user_id == user_id

    # User registers in bot 2
    u2, is_new2 = await user_svc_2.get_or_create(
        user_id=user_id,
        username="alice_updated",
        first_name="Alice B",
        language_code="ar",
    )
    assert is_new2 is True
    assert u2.bot_id == 2
    assert u2.user_id == user_id

    # Global user profile was created once and updated
    async with sm() as session:
        global_u = await session.get(User, user_id)
        assert global_u is not None
        assert global_u.username == "alice_updated"

    # Set VIP in bot 1 only
    async with sm() as session:
        bu1 = await session.get(BotUser, (1, user_id))
        bu1.vip_until = datetime(2099, 1, 1, tzinfo=UTC)
        await session.commit()

    bu1_check = await user_svc_1.get(user_id)
    bu2_check = await user_svc_2.get(user_id)
    assert bu1_check.is_vip() is True
    assert bu2_check.is_vip() is False

    # Preferences are isolated
    await user_svc_1.update_pref(user_id, "quality", "1080")
    await user_svc_2.update_pref(user_id, "quality", "audio")

    bu1_reloaded = await user_svc_1.get(user_id)
    bu2_reloaded = await user_svc_2.get(user_id)
    assert bu1_reloaded.pref("quality") == "1080"
    assert bu2_reloaded.pref("quality") == "audio"

    await engine.dispose()
