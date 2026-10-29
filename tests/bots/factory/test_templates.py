from __future__ import annotations

from datetime import UTC, datetime

from aiogram.types import Chat, Message, Update, User
from sqlalchemy import select

from bots.feedback.models import FeedbackThread
from core.runtime.dispatcher import build_dispatcher
from core.sdk.context import ChildInfo
from core.sdk.registry import discover
from tests.conftest import BOT_ID, build_test_ctx, callback_update, message_update, tg_user

OWNER, VISITOR = 1, 20202


async def child_ctx(slug, template, sm, redis, api, tmp_path):
    module = discover([slug], include_templates=True)[0]
    child = ChildInfo(owner_id=OWNER, template=template, factory_username="factory_bot")
    return await build_test_ctx(module, sm, redis, api, tmp_path, child=child)


def reply_update(text: str, user_id: int, reply_to_id: int) -> Update:
    bot_user = User(id=BOT_ID, is_bot=True, first_name="Bot")
    original = Message(message_id=reply_to_id, date=datetime.now(UTC), chat=Chat(id=user_id, type="private"),
                       from_user=bot_user, text="x")
    msg = Message(message_id=reply_to_id + 1000, date=datetime.now(UTC), chat=Chat(id=user_id, type="private"),
                  from_user=tg_user(user_id), text=text, reply_to_message=original)
    return Update(update_id=reply_to_id + 5000, message=msg)


async def test_templates_are_factory_only():
    assert {m.slug for m in discover()} >= {"anonymous", "groupguard", "factory"}
    assert not {"feedback", "custombot"} & {m.slug for m in discover()}
    names = {m.factory_template for m in discover(include_templates=True) if m.factory_template}
    assert names == {"anonymous", "feedback", "groupguard", "custom", "channelmanager"}


async def test_feedback_round_trip(sm, redis, api, tmp_path):
    ctx = await child_ctx("feedback", "feedback", sm, redis, api, tmp_path)
    dp = build_dispatcher(ctx)
    await dp.feed_update(ctx.bot, message_update("/start", user_id=VISITOR))
    assert "@factory_bot" in api.calls("SendMessage")[-1].text  # credit line

    await dp.feed_update(ctx.bot, message_update("Is the shop open <today>?", user_id=VISITOR))
    inbox = [m for m in api.calls("SendMessage") if m.chat_id == OWNER][-1]
    assert f"<code>{VISITOR}</code>" in inbox.text and "&lt;today&gt;" in inbox.text
    async with sm() as s:
        thread = (await s.execute(select(FeedbackThread))).scalar_one()
    assert thread.user_id == VISITOR and thread.inbox_chat_id == OWNER

    await dp.feed_update(ctx.bot, reply_update("Yes, until 9pm!", OWNER, thread.inbox_msg_id))
    [copy] = api.calls("CopyMessage")
    assert copy.chat_id == VISITOR and copy.from_chat_id == OWNER

    await dp.feed_update(ctx.bot, reply_update("/ban", OWNER, thread.inbox_msg_id))
    assert (await ctx.users.get(VISITOR)).is_banned


async def test_custom_bot_builder_and_visitor(sm, redis, api, tmp_path):
    ctx = await child_ctx("custombot", "custom", sm, redis, api, tmp_path)
    dp = build_dispatcher(ctx)
    pages = ctx.extras["pages"]
    root = await pages.root()

    await dp.feed_update(ctx.bot, message_update("/build", user_id=VISITOR))
    assert not any("Builder" in (m.text or "") for m in api.calls("SendMessage"))  # visitors can't edit

    await dp.feed_update(ctx.bot, message_update("/build", user_id=OWNER))
    assert "Builder" in api.calls("SendMessage")[-1].text
    await dp.feed_update(ctx.bot, callback_update(f"cbb:add:{root.id}", user_id=OWNER))
    await dp.feed_update(ctx.bot, message_update("💰 Prices", user_id=OWNER))
    [prices] = await pages.children(root.id)
    await dp.feed_update(ctx.bot, callback_update(f"cbb:content:{prices.id}", user_id=OWNER))
    await dp.feed_update(ctx.bot, message_update("Coffee 2$, Tea 1$", user_id=OWNER))
    await dp.feed_update(ctx.bot, callback_update(f"cbb:command:{prices.id}", user_id=OWNER))
    await dp.feed_update(ctx.bot, message_update("/prices", user_id=OWNER))
    assert (await pages.get(prices.id)).command == "prices"

    await dp.feed_update(ctx.bot, message_update("/start", user_id=VISITOR))
    home = api.calls("SendMessage")[-1]
    assert home.reply_markup.inline_keyboard[0][0].text == "💰 Prices"
    await dp.feed_update(ctx.bot, message_update("/prices", user_id=VISITOR))
    assert "Coffee 2$" in api.calls("SendMessage")[-1].text

    exported = await pages.export()
    assert exported["root"]["children"][0]["command"] == "prices"
    assert await pages.import_(exported) == 2
    [again] = await pages.children((await pages.root()).id)
    assert again.text == "Coffee 2$, Tea 1$"
