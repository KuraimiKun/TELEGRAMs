from __future__ import annotations

import asyncio
import json

import pytest
from aiogram.types import User
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from core.config import PlatformConfig
from core.db.models import ChildBot
from core.factory.crypto import webhook_secret
from core.factory.runtime import ChildRegistry
from core.factory.serving import SECRET_HEADER, ChildWebhook
from core.runtime.dispatcher import build_dispatcher
from core.sdk.registry import SharedInfra, discover, factory_templates
from tests.conftest import build_test_ctx, callback_update, message_update

CHILD_ID = 777000
CHILD_TOKEN = "777000:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
OWNER = 50


def child_user() -> User:
    return User(id=CHILD_ID, is_bot=True, first_name="Shop Help", username="shop_help_bot")


@pytest.fixture
async def fctx(sm, redis, api, tmp_path):
    api.responses["GetMe"] = lambda m: child_user()
    return await build_test_ctx(discover(["factory"])[0], sm, redis, api, tmp_path)


async def create_via_chat(dp, ctx, api, template="feedback", token=CHILD_TOKEN):
    await dp.feed_update(ctx.bot, message_update("/newbot", user_id=OWNER))
    await dp.feed_update(ctx.bot, callback_update(f"fac:tpl:0:1:{template}", user_id=OWNER))
    await dp.feed_update(ctx.bot, message_update(token, user_id=OWNER))


async def test_create_manage_and_limits(fctx, api):
    dp = build_dispatcher(fctx)
    children = fctx.extras["children"]
    await create_via_chat(dp, fctx, api)
    child = await children.get(CHILD_ID)
    assert child is not None and child.owner_id == OWNER and child.template == "feedback"
    assert CHILD_TOKEN not in child.token_enc  # encrypted at rest
    assert api.calls("DeleteMessage"), "the token message must be deleted"
    assert "is live" in api.calls("EditMessageText")[-1].text

    # Free plan: one bot. A second token is refused.
    api.responses["GetMe"] = lambda m: User(id=CHILD_ID + 1, is_bot=True, first_name="B", username="b_bot")
    await create_via_chat(dp, fctx, api, token="777001:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB")
    assert await children.get(CHILD_ID + 1) is None

    await dp.feed_update(fctx.bot, callback_update(f"fac:pause:{CHILD_ID}:1:", user_id=OWNER))
    assert (await children.get(CHILD_ID)).status == "paused"
    await dp.feed_update(fctx.bot, callback_update(f"fac:pause:{CHILD_ID}:1:", user_id=OWNER + 1))  # not owner
    await dp.feed_update(fctx.bot, callback_update(f"fac:resume:{CHILD_ID}:1:", user_id=OWNER))
    assert (await children.get(CHILD_ID)).status == "active"

    await dp.feed_update(fctx.bot, callback_update(f"fac:brand:{CHILD_ID}:1:", user_id=OWNER))
    assert (await children.get(CHILD_ID)).branding is True  # needs VIP

    await dp.feed_update(fctx.bot, callback_update(f"fac:del_ok:{CHILD_ID}:1:", user_id=OWNER))
    assert await children.get(CHILD_ID) is None


async def test_bad_tokens(fctx, api):
    from aiogram.exceptions import TelegramUnauthorizedError
    from aiogram.methods import GetMe

    dp = build_dispatcher(fctx)
    await create_via_chat(dp, fctx, api, token="not a token")
    assert "doesn't look like a bot token" in api.calls("EditMessageText")[-1].text
    api.responses["GetMe"] = lambda m: TelegramUnauthorizedError(method=GetMe(), message="Unauthorized")
    await dp.feed_update(fctx.bot, message_update(CHILD_TOKEN, user_id=OWNER))  # still waiting for a token
    assert "invalid" in api.calls("EditMessageText")[-1].text
    assert await fctx.extras["children"].get(CHILD_ID) is None


async def test_child_runtime_and_webhook(fctx, api, sm, redis):
    from sqlalchemy import update

    from core.db.models import Bot as BotRecord

    async with sm() as s:  # the factory's own row carries its @username (synced from getMe at startup)
        await s.execute(update(BotRecord).where(BotRecord.id == fctx.bot_id).values(username="test_bot"))
        await s.commit()
    await fctx.extras["children"].create(OWNER, CHILD_TOKEN, "feedback", limit=5)
    platform = fctx.platform
    infra = SharedInfra(engine=None, sm=sm, redis=redis, cache_redis=redis, session=api)  # type: ignore[arg-type]
    stop = asyncio.Event()
    registry = ChildRegistry(platform, infra, stop, templates=factory_templates())
    runtime = await registry.get(CHILD_ID)
    assert runtime is not None
    ctx = runtime.ctx
    assert ctx.slug == f"c{CHILD_ID}" and ctx.child.owner_id == OWNER and ctx.child.factory_username == "test_bot"
    assert ctx.is_admin(OWNER) and ctx.features == ctx.module.child_features
    assert await registry.get(CHILD_ID) is runtime  # cached

    app = web.Application()
    hook = ChildWebhook(registry, platform)
    hook.register(app)
    async with TestClient(TestServer(app)) as client:
        update = message_update("hello shop", user_id=4242).model_dump(mode="json", exclude_none=True)
        bad = await client.post(f"/webhook/c/{CHILD_ID}", json=update, headers={SECRET_HEADER: "nope"})
        assert bad.status == 401
        ok = await client.post(f"/webhook/c/{CHILD_ID}", data=json.dumps(update),
                               headers={SECRET_HEADER: webhook_secret(platform, CHILD_ID),
                                        "Content-Type": "application/json"})
        assert ok.status == 200
        await hook.drain()
    inbox = [m for m in api.calls("SendMessage") if m.chat_id == OWNER]
    assert inbox and "hello shop" in inbox[-1].text

    # Pausing (published by the factory) evicts the runtime; paused bots are not served.
    child = await fctx.extras["children"].get(CHILD_ID)
    await fctx.extras["children"].pause(child)
    await registry.evict(CHILD_ID)
    assert await registry.get(CHILD_ID) is None


async def test_revoked_bot_token_is_erased(fctx):
    children = fctx.extras["children"]
    await children.create(OWNER, CHILD_TOKEN, "anonymous", limit=5)
    child = await children.get(CHILD_ID)
    await children.revoke(child, "abuse")
    revoked = await children.get(CHILD_ID)
    assert isinstance(revoked, ChildBot) and revoked.status == "revoked" and revoked.token_enc == ""
    from core.factory.children import ChildError

    with pytest.raises(ChildError) as e:
        await children.create(OWNER, CHILD_TOKEN, "anonymous", limit=5)
    assert e.value.code == "revoked"


def test_platform_requires_secret_for_factory():
    assert PlatformConfig().factory_secret_key is None


async def test_channelmanager_foreign_webhook_requires_explicit_migration(fctx, api):
    from aiogram.types import WebhookInfo
    api.responses["GetWebhookInfo"] = WebhookInfo(url="https://old-host.example/webhook", has_custom_certificate=False, pending_update_count=0)
    dp = build_dispatcher(fctx)
    await create_via_chat(dp, fctx, api, template="channelmanager")
    assert await fctx.extras["children"].get(CHILD_ID) is None
    assert not api.calls("DeleteWebhook") and not api.calls("SetWebhook")
    assert "Migrating" in api.calls("EditMessageText")[-1].text
    await dp.feed_update(fctx.bot, callback_update("fac:migrate:0:1:", user_id=OWNER + 1))
    assert await fctx.extras["children"].get(CHILD_ID) is None
    await dp.feed_update(fctx.bot, callback_update("fac:migrate:0:1:", user_id=OWNER))
    child = await fctx.extras["children"].get(CHILD_ID)
    assert child and child.template == "channelmanager"
    assert api.calls("DeleteWebhook")
    await fctx.extras["children"]._set(CHILD_ID, status="paused")
    count = len(api.calls("DeleteWebhook"))
    await dp.feed_update(fctx.bot, callback_update(f"fac:resume:{CHILD_ID}:1:", user_id=OWNER))
    assert (await fctx.extras["children"].get(CHILD_ID)).status == "paused"
    assert len(api.calls("DeleteWebhook")) == count
    await dp.feed_update(fctx.bot, callback_update("fac:migrate:0:1:", user_id=OWNER))
    assert (await fctx.extras["children"].get(CHILD_ID)).status == "active"
    assert len(api.calls("DeleteWebhook")) == count + 1


async def test_channelmanager_pause_without_usable_token_still_fences_bindings(fctx, api):
    from aiogram.types import WebhookInfo
    from sqlalchemy import select

    from bots.channelmanager.models import Channel, Event, SenderBinding
    from tests.conftest import BOT_ID
    api.responses["GetWebhookInfo"] = WebhookInfo(url="", has_custom_certificate=False, pending_update_count=0)
    children = fctx.extras["children"]
    child = await children.create(OWNER, CHILD_TOKEN, "channelmanager", limit=1)
    async with fctx.sm() as session:
        session.add(Channel(bot_id=BOT_ID, channel_id=-1001234567890, title="Control", status="active", sender_paused=True))
        await session.flush()
        session.add(SenderBinding(bot_id=BOT_ID, channel_id=-1001234567890, sender_bot_id=CHILD_ID,
            owner_id=OWNER, token_epoch="opaque", control_username="control"))
        await session.commit()
    await children._set(CHILD_ID, token_enc="unreadable")
    child = await children.get(CHILD_ID)
    await children.pause(child)
    async with fctx.sm() as session:
        assert not (await session.scalar(select(SenderBinding))).active
        assert (await session.scalar(select(Channel))).sender_paused
        assert (await session.scalar(select(Event))).action == "sender.stopped"
