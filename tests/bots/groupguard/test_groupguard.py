from __future__ import annotations

import itertools
import time
from datetime import UTC, datetime

import pytest
from aiogram.types import (
    AcceptedGiftTypes,
    Chat,
    ChatFullInfo,
    ChatMemberAdministrator,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberUpdated,
    ChatPermissions,
    Message,
    MessageEntity,
    Update,
)

from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.jobs import in_night
from core.runtime.dispatcher import build_dispatcher
from core.sdk.registry import discover
from tests.conftest import build_test_ctx, tg_user

GROUP = -1001234567890
ADMIN, MEMBER, NEWBIE = 10, 20, 30
_ids = itertools.count(5000)


def gg_module():
    return discover(["groupguard"])[0]


@pytest.fixture
async def gctx(sm, redis, api, tmp_path):
    ctx = await build_test_ctx(gg_module(), sm, redis, api, tmp_path)
    api.responses["GetChatAdministrators"] = [ChatMemberOwner(user=tg_user(ADMIN), is_anonymous=False)]
    def membership(method):
        if method.user_id == ctx.bot_id:
            return ChatMemberAdministrator(user=tg_user(ctx.bot_id).model_copy(update={"is_bot": True}),
                is_anonymous=False, can_be_edited=False, can_manage_chat=True, can_delete_messages=True,
                can_manage_video_chats=False, can_restrict_members=True, can_promote_members=True,
                can_change_info=True, can_invite_users=True, can_post_stories=False, can_edit_stories=False,
                can_delete_stories=False, can_send_welcome_messages=False, can_pin_messages=True, can_manage_topics=True)
        if method.user_id == ADMIN:
            return ChatMemberOwner(user=tg_user(ADMIN), is_anonymous=False)
        return ChatMemberMember(user=tg_user(method.user_id))
    api.responses["GetChatMember"] = membership
    api.responses["GetChat"] = lambda m: ChatFullInfo(id=m.chat_id, type="supergroup", title="Club", accent_color_id=0,
        max_reaction_count=0, accepted_gift_types=AcceptedGiftTypes(unlimited_gifts=False, limited_gifts=False,
        unique_gifts=False, premium_subscription=False, gifts_from_channels=False),
        permissions=ChatPermissions(can_send_messages=True, can_send_polls=False))
    return ctx


def group_msg(text: str, user_id: int, reply_to: Message | None = None, **extra) -> Update:
    msg = Message(
        message_id=next(_ids), date=datetime.now(UTC), chat=Chat(id=GROUP, type="supergroup", title="Club"),
        from_user=tg_user(user_id), text=text, reply_to_message=reply_to, **extra,
    )
    return Update(update_id=next(_ids), message=msg)


def plain(user_id: int, text: str = "hi") -> Message:
    return Message(message_id=next(_ids), date=datetime.now(UTC), chat=Chat(id=GROUP, type="supergroup"),
                   from_user=tg_user(user_id), text=text)


def join_update(user_id: int) -> Update:
    user = tg_user(user_id)
    event = ChatMemberUpdated(
        chat=Chat(id=GROUP, type="supergroup", title="Club"), from_user=user, date=datetime.now(UTC),
        old_chat_member=ChatMemberLeft(user=user), new_chat_member=ChatMemberMember(user=user),
    )
    return Update(update_id=next(_ids), chat_member=event)


def texts(api, chat_id=GROUP):
    return [m.text for m in api.calls("SendMessage") if m.chat_id == chat_id]


def test_contract_and_night_window():
    m = gg_module()
    assert m.factory_template == "groupguard" and {j.name for j in m.factory_jobs()} == {"captchas", "night"}
    cfg = ChatConfig(night=True, night_start=23, night_end=7, tz_offset=3)
    assert in_night(cfg, 20) and in_night(cfg, 2) and not in_night(cfg, 5)  # 23:00, 05:00 local; 08:00 local
    assert not in_night(ChatConfig(night_start=9, night_end=9), 9)


async def test_ban_mute_require_rights(gctx, api):
    dp = build_dispatcher(gctx)
    await dp.feed_update(gctx.bot, group_msg("/ban", MEMBER, reply_to=plain(NEWBIE)))
    assert not api.calls("BanChatMember") and "right" in texts(api)[-1]

    await dp.feed_update(gctx.bot, group_msg("/ban 2h spamming", ADMIN, reply_to=plain(NEWBIE)))
    [ban] = api.calls("BanChatMember")
    assert ban.user_id == NEWBIE and ban.until_date is not None
    assert "2h" in texts(api)[-1] and "spamming" in texts(api)[-1]

    await dp.feed_update(gctx.bot, group_msg("/mute", ADMIN, reply_to=plain(ADMIN)))
    assert not api.calls("RestrictChatMember") and "admin" in texts(api)[-1]  # admins are protected

    await dp.feed_update(gctx.bot, group_msg("/mute 10m", ADMIN, reply_to=plain(MEMBER)))
    [mute] = api.calls("RestrictChatMember")
    assert mute.user_id == MEMBER and mute.permissions.can_send_messages is False


async def test_warn_limit_bans(gctx, api):
    dp = build_dispatcher(gctx)
    await gctx.extras["guard"].update_config(GROUP, warn_limit=2, warn_action="ban")
    await dp.feed_update(gctx.bot, group_msg("/warn rude", ADMIN, reply_to=plain(MEMBER)))
    assert "(1/2)" in texts(api)[-1] and not api.calls("BanChatMember")
    await dp.feed_update(gctx.bot, group_msg("/warn again", ADMIN, reply_to=plain(MEMBER)))
    assert api.calls("BanChatMember")[-1].user_id == MEMBER
    assert await gctx.extras["guard"].count_warns(GROUP, MEMBER) == 0


async def test_locks_and_blocklist_delete_but_spare_admins(gctx, api):
    dp = build_dispatcher(gctx)
    await dp.feed_update(gctx.bot, group_msg("/lock links", ADMIN))
    await dp.feed_update(gctx.bot, group_msg("/addblock casino", ADMIN))
    link = group_msg("join https://spam.example now", MEMBER,
                     entities=[MessageEntity(type="url", offset=5, length=20)])
    await dp.feed_update(gctx.bot, link)
    assert api.calls("DeleteMessage")[-1].message_id == link.message.message_id
    await dp.feed_update(gctx.bot, group_msg("best Casino in town", MEMBER))
    assert len(api.calls("DeleteMessage")) == 2
    await dp.feed_update(gctx.bot, group_msg("our site https://ok.example", ADMIN))
    assert len(api.calls("DeleteMessage")) == 2  # admins are exempt


async def test_flood_mutes(gctx, api):
    dp = build_dispatcher(gctx)
    await gctx.extras["guard"].update_config(GROUP, flood_count=3, flood_seconds=10)
    for i in range(4):
        await dp.feed_update(gctx.bot, group_msg(f"msg {i}", MEMBER))
    [mute] = api.calls("RestrictChatMember")
    assert mute.user_id == MEMBER
    assert "flooding" in texts(api)[-1]


async def test_captcha_flow_and_expiry(gctx, api, monkeypatch):
    from bots.groupguard import protect
    from bots.groupguard.handlers import welcome

    async def not_banned(*_a, **_k):
        return False

    monkeypatch.setattr(welcome, "cas_banned", not_banned)
    dp = build_dispatcher(gctx)
    await dp.feed_update(gctx.bot, join_update(NEWBIE))
    assert api.calls("RestrictChatMember")[-1].permissions.can_send_messages is False
    prompt = api.calls("SendMessage")[-1]
    data = prompt.reply_markup.inline_keyboard[0][0].callback_data
    assert data.startswith("gg:cap") and "human" in prompt.text

    await dp.feed_update(gctx.bot, bound_callback(data, api.messages[-1], MEMBER))  # someone else
    assert api.calls("RestrictChatMember")[-1].permissions.can_send_messages is False
    await dp.feed_update(gctx.bot, bound_callback(data, api.messages[-1], NEWBIE))
    assert api.calls("RestrictChatMember")[-1].permissions.can_send_messages is True
    assert api.calls("EditMessageText")

    # A second newcomer never answers: the sweeper removes them.
    await dp.feed_update(gctx.bot, join_update(NEWBIE + 1))
    await gctx.redis.zadd(welcome.due_key(gctx), {f"{GROUP}:{NEWBIE + 1}": time.time() - 1})
    from sqlalchemy import update

    from bots.groupguard.models import GuardChallenge, GuardJob
    async with gctx.sm() as session:
        await session.execute(update(GuardChallenge).where(GuardChallenge.bot_id == gctx.bot_id,
            GuardChallenge.chat_id == GROUP, GuardChallenge.user_id == NEWBIE + 1).values(deadline=datetime.now(UTC)))
        await session.execute(update(GuardJob).where(GuardJob.bot_id == gctx.bot_id,
            GuardJob.kind == "captcha_expire", GuardJob.user_id == NEWBIE + 1).values(run_at=datetime.now(UTC)))
        await session.commit()
    assert await welcome.sweep_captchas(gctx) == 1
    assert api.calls("BanChatMember")[-1].user_id == NEWBIE + 1
    assert api.calls("UnbanChatMember")[-1].user_id == NEWBIE + 1
    assert await gctx.redis.exists(protect.newbie_key(gctx, GROUP, NEWBIE))  # newcomers: no links for a while


async def test_notes_and_filters(gctx, api):
    dp = build_dispatcher(gctx)
    await dp.feed_update(gctx.bot, group_msg("/save faq Read the <b>pinned</b> post", ADMIN))
    await dp.feed_update(gctx.bot, group_msg("/filter price It's free!", ADMIN))
    await dp.feed_update(gctx.bot, group_msg("#faq", MEMBER))
    assert "pinned" in texts(api)[-1]
    await dp.feed_update(gctx.bot, group_msg("what's the PRICE?", MEMBER))
    assert texts(api)[-1] == "It's free!"
    await dp.feed_update(gctx.bot, group_msg("/save x y", MEMBER))  # members can't save
    assert await gctx.extras["guard"].get_item(GROUP, "note", "x") is None


async def test_settings_panel_in_private(gctx, api):
    dp = build_dispatcher(gctx)
    await dp.feed_update(gctx.bot, group_msg("/settings", ADMIN))
    panel = [m for m in api.calls("SendMessage") if m.chat_id == ADMIN][-1]
    [cap] = [b.callback_data for row in panel.reply_markup.inline_keyboard for b in row if ":cap" in b.callback_data]
    sent = next(m for m in reversed(api.messages) if m.chat.id == ADMIN)
    await dp.feed_update(gctx.bot, bound_callback(cap, sent, ADMIN))
    assert (await gctx.extras["guard"].config(GROUP)).captcha == "math"
    await dp.feed_update(gctx.bot, bound_callback(cap, sent, MEMBER))  # not an admin of the group
    assert (await gctx.extras["guard"].config(GROUP)).captcha == "math"


def bound_callback(data, message, user_id):
    from aiogram.types import CallbackQuery
    return Update(update_id=next(_ids), callback_query=CallbackQuery(id=str(next(_ids)), from_user=tg_user(user_id),
        chat_instance="test", data=data, message=message))
