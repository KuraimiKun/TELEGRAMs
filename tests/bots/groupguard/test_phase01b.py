from datetime import UTC, datetime

from aiogram.types import Chat, MessageEntity, Update

from core.factory.webhooks import CHILD_UPDATE_TYPES
from core.middlewares.throttling import ThrottlingMiddleware
from core.runtime.dispatcher import allowed_update_types
from tests.bots.groupguard.test_groupguard import ADMIN, GROUP, MEMBER, gctx, group_msg
from tests.bots.groupguard.test_phase01a import build_dispatcher_once, env, send
from tests.conftest import message_update, tg_user

__all__ = ["env", "gctx"]
REAL_THROTTLE = ThrottlingMiddleware.__call__


async def test_blocked_core_commands_before_real_throttle_and_guards(env, api, monkeypatch):
    monkeypatch.setattr(ThrottlingMiddleware, "__call__", REAL_THROTTLE)
    svc = env.extras["guard"]
    await svc.update_config(GROUP, blocklist=["casino"])
    await send(env, group_msg("hello", MEMBER))
    before = len(api.calls("SendMessage"))
    for command in ("/terms casino", "/admin casino", "/support casino"):
        update = group_msg(command, MEMBER)
        await send(env, update)
        assert api.calls("DeleteMessage")[-1].message_id == update.message.message_id
    assert len(api.calls("SendMessage")) == before
    # Private platform terms remains functional and outside group protection.
    await send(env, message_update("/terms", user_id=51))
    assert api.calls("SendMessage")[-1].chat_id == 51


async def test_edits_captions_entities_checked_without_flood_recount(env, api):
    svc = env.extras["guard"]
    await svc.update_config(GROUP, blocklist=["casino"], locks=["links"], flood_count=5)
    original = group_msg("safe", MEMBER)
    await send(env, original)
    key = env.keys("flood_window", "{" + str(GROUP) + "}", MEMBER, 5, 8)
    assert await env.redis.zcard(key) == 1
    edited = original.message.model_copy(update={"text": None, "caption": "casino",
        "edit_date": int(datetime.now(UTC).timestamp())})
    await send(env, Update(update_id=99001, edited_message=edited))
    assert api.calls("DeleteMessage")[-1].message_id == edited.message_id
    assert await env.redis.zcard(key) == 1
    edited = edited.model_copy(update={"caption": "visit here", "caption_entities": [
        MessageEntity(type="text_link", offset=6, length=4, url="https://bad.example")]})
    await send(env, Update(update_id=99002, edited_message=edited))
    assert len(api.calls("DeleteMessage")) == 2 and await env.redis.zcard(key) == 1


async def test_sender_chat_and_ordinary_bot_no_blanket_lock_exemption(env, api):
    await env.extras["guard"].update_config(GROUP, locks=["links"])
    update = group_msg("https://bad.example", MEMBER, sender_chat=Chat(id=-100999, type="channel"))
    await send(env, update)
    bot = group_msg("https://bad.example", MEMBER)
    bot = bot.model_copy(update={"message": bot.message.model_copy(update={"from_user": tg_user(MEMBER).model_copy(update={"is_bot": True})})})
    await send(env, bot)
    assert len(api.calls("DeleteMessage")) == 2
    assert not api.calls("BanChatMember") and not api.calls("RestrictChatMember")


async def test_settings_deep_link_and_all_delivery_subscriptions(env, api):
    await send(env, message_update(f"/start gs_{GROUP}", user_id=ADMIN))
    assert "Settings —" in (api.calls("SendMessage")[-1].text or "")
    expected = {"message", "edited_message", "message_reaction", "message_reaction_count", "chat_member", "chat_join_request"}
    assert expected <= set(allowed_update_types(env, build_dispatcher_once(env)))
    assert expected <= set(CHILD_UPDATE_TYPES)
    await send(env, message_update(f"/start gs_{GROUP}", user_id=MEMBER))
    assert "verified" in api.calls("SendMessage")[-1].text
