"""Broadcasts, membership tracking, force-subscribe replay, refunds, localized commands."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import CopyMessage
from aiogram.types import (
    Chat,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberUpdated,
    MessageId,
    RefundedPayment,
    Update,
    User,
)
from sqlalchemy import select

from core.callback_data import CoreForceSubCb
from core.db.models import BotUser, Group
from core.runtime.dispatcher import build_dispatcher
from core.runtime.gateway import register_bot_commands
from core.services.broadcast import BroadcastRunner


@pytest.fixture
def dp(ctx):
    return build_dispatcher(ctx)


# ------------------------------------------------------------------ broadcasts
async def _members(ctx, ids):
    for uid in ids:
        await ctx.users.get_or_create(uid, language_code="en")


async def test_broadcast_runs_marks_blocked_and_reports(ctx, api):
    await _members(ctx, [1, 2, 3, 4])

    def copy(m: CopyMessage):
        if m.chat_id == 3:
            return TelegramForbiddenError(method=m, message="Forbidden: bot was blocked by the user")
        return MessageId(message_id=1)

    api.responses["CopyMessage"] = copy
    b = await ctx.broadcast.create(admin_id=1, target="all", from_chat_id=1, message_id=10)
    assert b.total == 4
    stop = asyncio.Event()
    done = asyncio.Event()

    async def finished(result):
        done.set()

    runner = asyncio.create_task(BroadcastRunner(ctx.broadcast, ctx.bot, poll=0.05).run(stop, on_finished=finished))
    await asyncio.wait_for(done.wait(), 10)
    stop.set()
    await runner

    b = await ctx.broadcast.get(b.id)
    assert (b.status, b.sent, b.blocked, b.failed) == ("done", 3, 1, 0)
    assert (await ctx.users.get(3)).blocked_bot


async def test_broadcast_resumes_from_cursor_without_resending(ctx, api):
    await _members(ctx, [1, 2, 3, 4, 5])
    api.responses["CopyMessage"] = MessageId(message_id=1)
    b = await ctx.broadcast.create(admin_id=1, target="all", from_chat_id=1, message_id=10)

    # Simulate a crash after user 3: cursor persisted, status still running.
    await ctx.broadcast._save(b, status="running", cursor=3, sent=3)
    b = await ctx.broadcast.get(b.id)
    stop = asyncio.Event()
    await ctx.broadcast.run(ctx.bot, b, stop)
    sent_to = [m.chat_id for m in api.calls("CopyMessage")]
    assert sent_to == [4, 5]
    assert (await ctx.broadcast.get(b.id)).sent == 5


async def test_broadcast_cancel_stops_runner(ctx, api, monkeypatch):
    monkeypatch.setattr("core.services.broadcast.RATE_PER_SEC", 10_000)
    await _members(ctx, list(range(1, 400)))
    b = await ctx.broadcast.create(admin_id=1, target="all", from_chat_id=1, message_id=10)

    def copy(m):
        if len(api.calls("CopyMessage")) == 10:  # admin presses "stop" mid-way
            asyncio.get_running_loop().create_task(ctx.broadcast.cancel(b.id))
        return MessageId(message_id=1)

    api.responses["CopyMessage"] = copy
    result = await ctx.broadcast.run(ctx.bot, await ctx.broadcast.get(b.id), asyncio.Event())
    assert result.status == "cancelled"
    assert len(api.calls("CopyMessage")) <= 60  # stops at the next checkpoint, not after the whole audience

    # A cancelled broadcast is never (re)started.
    api.requests.clear()
    await ctx.broadcast.run(ctx.bot, await ctx.broadcast.get(b.id), asyncio.Event())
    assert api.calls("CopyMessage") == []


# ------------------------------------------------------------------ membership
def member_update(chat: Chat, old, new, user_id: int = 42) -> Update:
    actor = User(id=user_id, is_bot=False, first_name="A", language_code="en")
    bot = User(id=123456, is_bot=True, first_name="B")
    cmu = ChatMemberUpdated(
        chat=chat,
        from_user=actor,
        date=datetime.now(UTC),
        old_chat_member=old(user=bot),
        new_chat_member=new(user=bot),
    )
    return Update(update_id=9000, my_chat_member=cmu)


async def test_user_blocking_the_bot_is_tracked(ctx, dp, api):
    await ctx.users.get_or_create(42, language_code="en")
    await dp.feed_update(ctx.bot, member_update(Chat(id=42, type="private"), ChatMemberMember, ChatMemberLeft))
    assert (await ctx.users.get(42)).blocked_bot
    await dp.feed_update(ctx.bot, member_update(Chat(id=42, type="private"), ChatMemberLeft, ChatMemberMember))
    assert not (await ctx.users.get(42)).blocked_bot


async def test_group_add_and_remove(ctx, dp, api):
    chat = Chat(id=-500, type="supergroup", title="Fans")
    await dp.feed_update(ctx.bot, member_update(chat, ChatMemberLeft, ChatMemberMember))
    assert api.calls("SendMessage")[-1].chat_id == -500  # welcome
    async with ctx.sm() as s:
        g = (await s.execute(select(Group).where(Group.chat_id == -500))).scalar_one()
    assert g.active and g.title == "Fans"
    await dp.feed_update(ctx.bot, member_update(chat, ChatMemberMember, ChatMemberLeft))
    async with ctx.sm() as s:
        assert not (await s.execute(select(Group).where(Group.chat_id == -500))).scalar_one().active


async def test_group_chatter_does_not_register_users(ctx, dp, builders):
    await dp.feed_update(ctx.bot, builders["message"]("hello everyone", user_id=77, chat_type="supergroup", chat_id=-9))
    async with ctx.sm() as s:
        assert (await s.execute(select(BotUser).where(BotUser.user_id == 77))).scalar_one_or_none() is None


# ------------------------------------------------------------------ force-subscribe
async def _unthrottle(ctx) -> None:
    keys = await ctx.redis.keys(ctx.keys("throttle*"))
    if keys:
        await ctx.redis.delete(*keys)

async def test_force_sub_blocks_then_replays_the_link(ctx, dp, api, builders, monkeypatch):
    async def ok(url):
        return None

    monkeypatch.setattr("bots.socialdownload.handlers.link.assert_public_url", ok)
    await ctx.groups.add_channel(-100777, "News", "https://t.me/news")
    joined = {"value": False}

    def member(m):
        cls = ChatMemberMember if joined["value"] else ChatMemberLeft
        return cls(user=User(id=m.user_id, is_bot=False, first_name="x"))

    api.responses["GetChatMember"] = member
    await dp.feed_update(ctx.bot, builders["message"]("https://x.com/a/status/1", user_id=8))
    prompt = api.calls("SendMessage")[-1]
    assert prompt.text == ctx.translator.get("en", "fsub-required")
    token_cb = prompt.reply_markup.inline_keyboard[-1][0].callback_data
    assert (await ctx.extras["queue"].depth())["normal"] == 0

    await dp.feed_update(ctx.bot, builders["callback"](token_cb, user_id=8))  # still not joined
    assert api.calls("AnswerCallbackQuery")[-1].text == ctx.translator.get("en", "fsub-not-yet")

    joined["value"] = True
    await _unthrottle(ctx)
    await dp.feed_update(ctx.bot, builders["callback"](token_cb, user_id=8))
    assert (await ctx.extras["queue"].depth())["normal"] == 1  # the original link was processed

    # The token is single-use and bound to its user.
    await _unthrottle(ctx)
    await dp.feed_update(ctx.bot, builders["callback"](CoreForceSubCb(token="deadbeef00").pack(), user_id=8))
    assert (await ctx.extras["queue"].depth())["normal"] == 1


# ------------------------------------------------------------------ refunds & commands
async def test_telegram_initiated_refund_update(ctx, dp, api):
    from aiogram.types import Message

    await ctx.users.get_or_create(42, language_code="en")
    await ctx.payments.record_payment(42, None, 100, 30, "charge-r")
    msg = Message(
        message_id=5,
        date=datetime.now(UTC),
        chat=Chat(id=42, type="private"),
        from_user=User(id=42, is_bot=False, first_name="A"),
        refunded_payment=RefundedPayment(
            currency="XTR", total_amount=100, invoice_payload="x", telegram_payment_charge_id="charge-r"
        ),
    )
    await dp.feed_update(ctx.bot, Update(update_id=777, message=msg))
    assert not (await ctx.users.get(42)).is_vip()
    assert api.calls("SendMessage")[-1].text == ctx.translator.get("en", "vip-refunded")


async def test_commands_are_registered_per_language(ctx, api):
    await register_bot_commands(ctx)
    calls = api.calls("SetMyCommands")
    langs = {c.language_code for c in calls}
    assert {None, "en", "ar", "es", "ru"} <= langs
    ar = next(c for c in calls if c.language_code == "ar")
    descriptions = {c.command: c.description for c in ar.commands}
    assert descriptions["lang"] == ctx.translator.get("ar", "cmd-lang")
    assert "admin" not in descriptions
    assert len(descriptions) == len(ar.commands)  # no duplicates
