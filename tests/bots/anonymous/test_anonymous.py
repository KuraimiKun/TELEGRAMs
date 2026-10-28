from __future__ import annotations

import pytest

from core.runtime.dispatcher import build_dispatcher
from core.sdk.context import ChildInfo
from core.sdk.registry import discover
from tests.conftest import build_test_ctx

OWNER, VISITOR = 1, 20202


def anon_module():
    return discover(["anonymous"])[0]


@pytest.fixture
async def actx(sm, redis, api, tmp_path):
    return await build_test_ctx(anon_module(), sm, redis, api, tmp_path)


async def _unthrottle(ctx):
    keys = await ctx.redis.keys(ctx.keys("throttle*"))
    if keys:
        await ctx.redis.delete(*keys)


async def feed(dp, ctx, update):
    await _unthrottle(ctx)
    await dp.feed_update(ctx.bot, update)


def last_to(api, chat_id):
    sent = [m for m in api.calls("SendMessage") if m.chat_id == chat_id]
    return sent[-1] if sent else None


def buttons(markup):
    return [b.callback_data for row in markup.inline_keyboard for b in row if b.callback_data]


def test_module_contract():
    m = anon_module()
    assert m.factory_template == "anonymous" and m.standalone and m.table_prefix == "anon_"


async def test_full_anonymous_round_trip(actx, api, builders):
    dp = build_dispatcher(actx)
    svc = actx.extras["anon"]
    await feed(dp, actx, builders["message"]("/start", user_id=OWNER))
    link = await svc.link_for(OWNER)
    assert link.code in last_to(api, OWNER).text

    # Visitor opens the link and writes; the owner receives it without any trace of the sender.
    await feed(dp, actx, builders["message"](f"/start {link.code}", user_id=VISITOR))
    assert "anonymous message" in last_to(api, VISITOR).text
    await feed(dp, actx, builders["message"]("I <3 your style", user_id=VISITOR))
    delivered = last_to(api, OWNER)
    assert "New anonymous message" in delivered.text and "I &lt;3 your style" in delivered.text
    assert str(VISITOR) not in delivered.text and "alice" not in delivered.text.lower()
    [msg_id] = {int(c.split(":")[-1]) for c in buttons(delivered.reply_markup) if c.startswith("an:reply")}
    assert "Sent anonymously" in last_to(api, VISITOR).text

    # The owner replies (their name shows); the visitor answers back and stays anonymous.
    await feed(dp, actx, builders["callback"](f"an:reply:{msg_id}", user_id=OWNER))
    await feed(dp, actx, builders["message"]("who is this?", user_id=OWNER))
    reply = last_to(api, VISITOR)
    assert "replied to your anonymous message" in reply.text and "I &lt;3 your style" in reply.text
    [reply_id] = {int(c.split(":")[-1]) for c in buttons(reply.reply_markup) if c.startswith("an:reply")}
    assert not any(c.startswith("an:block") for c in buttons(reply.reply_markup))  # visitors can't unmask/block

    await feed(dp, actx, builders["callback"](f"an:reply:{reply_id}", user_id=VISITOR))
    await feed(dp, actx, builders["message"]("not telling 😉", user_id=VISITOR))
    back = last_to(api, OWNER)
    assert "Anonymous reply" in back.text and "not telling" in back.text

    stats = await svc.stats(OWNER)
    assert stats.received == 2 and stats.replied == 1
    assert (await svc.stats(VISITOR)).sent == 2


async def test_only_recipient_can_act_and_blocking_works(actx, api, builders):
    dp = build_dispatcher(actx)
    svc = actx.extras["anon"]
    await feed(dp, actx, builders["message"]("/start", user_id=OWNER))
    code = (await svc.link_for(OWNER)).code
    await feed(dp, actx, builders["message"](f"/start {code}", user_id=VISITOR))
    await feed(dp, actx, builders["message"]("hey", user_id=VISITOR))
    msg_id = int(buttons(last_to(api, OWNER).reply_markup)[0].split(":")[-1])

    await feed(dp, actx, builders["callback"](f"an:block:{msg_id}", user_id=3))  # a stranger
    assert not await svc.is_blocked(OWNER, VISITOR)
    await feed(dp, actx, builders["callback"](f"an:block:{msg_id}", user_id=OWNER))
    assert await svc.is_blocked(OWNER, VISITOR)

    await feed(dp, actx, builders["message"](f"/start {code}", user_id=VISITOR))
    assert "can't send" in last_to(api, VISITOR).text


async def test_daily_limit_and_report_notifies_moderators(actx, api, builders):
    dp = build_dispatcher(actx)
    svc = actx.extras["anon"]
    await actx.settings.set("free_daily_messages", 1)
    await feed(dp, actx, builders["message"]("/start", user_id=OWNER))
    code = (await svc.link_for(OWNER)).code
    for text in ("one", "two"):
        await feed(dp, actx, builders["message"](f"/start {code}", user_id=VISITOR))
        await feed(dp, actx, builders["message"](text, user_id=VISITOR))
    assert "messages today" in last_to(api, VISITOR).text

    msg_id = int(buttons(last_to(api, OWNER).reply_markup)[0].split(":")[-1])
    await feed(dp, actx, builders["callback"](f"an:report:{msg_id}", user_id=OWNER))
    report = last_to(api, 999)  # super admin
    assert report is not None and f"<code>{VISITOR}</code>" in report.text
    await feed(dp, actx, builders["callback"](f"an:ban:{msg_id}", user_id=999))
    assert (await actx.users.get(VISITOR)).is_banned


async def test_hint_is_vip_only(actx, api, builders):
    dp = build_dispatcher(actx)
    svc = actx.extras["anon"]
    await feed(dp, actx, builders["message"]("/start", user_id=OWNER))
    code = (await svc.link_for(OWNER)).code
    await feed(dp, actx, builders["message"](f"/start {code}", user_id=VISITOR))
    await feed(dp, actx, builders["message"]("guess who 😎🔥", user_id=VISITOR))
    msg_id = int(buttons(last_to(api, OWNER).reply_markup)[0].split(":")[-1])

    await feed(dp, actx, builders["callback"](f"an:hint:{msg_id}", user_id=OWNER))
    assert "VIP" in last_to(api, OWNER).text

    await actx.subs.grant_vip(OWNER, 7)
    await feed(dp, actx, builders["callback"](f"an:hint:{msg_id}", user_id=OWNER))
    hint = last_to(api, OWNER).text
    assert "Hint" in hint and "Emojis used: 2" in hint
    assert str(VISITOR) not in hint

    # The visitor can never ask for a hint about the owner.
    await feed(dp, actx, builders["callback"](f"an:hint:{msg_id}", user_id=VISITOR))
    assert "Hint" not in (last_to(api, VISITOR).text or "")


async def test_child_bot_is_a_single_branded_inbox(sm, redis, api, tmp_path, builders):
    child = ChildInfo(owner_id=OWNER, template="anonymous", factory_username="factory_bot")
    ctx = await build_test_ctx(anon_module(), sm, redis, api, tmp_path, child=child)
    dp = build_dispatcher(ctx)
    await feed(dp, ctx, builders["message"]("/start", user_id=OWNER))
    assert "https://t.me/test_bot" in last_to(api, OWNER).text

    await feed(dp, ctx, builders["message"]("/start", user_id=VISITOR))
    prompt = last_to(api, VISITOR).text
    assert "anonymous message" in prompt and "@factory_bot" in prompt
    await feed(dp, ctx, builders["message"]("hello owner", user_id=VISITOR))
    assert "hello owner" in last_to(api, OWNER).text
    sent = last_to(api, VISITOR)
    urls = [b.url for row in sent.reply_markup.inline_keyboard for b in row if b.url]
    assert any("factory_bot?start=from_c" in u for u in urls)
    assert ctx.is_admin(OWNER) and not ctx.is_admin(VISITOR)


async def test_media_is_copied_not_forwarded(actx, api, builders):
    from datetime import UTC, datetime

    from aiogram.types import Chat, Message, PhotoSize, Update

    from tests.conftest import tg_user

    dp = build_dispatcher(actx)
    svc = actx.extras["anon"]
    await feed(dp, actx, builders["message"]("/start", user_id=OWNER))
    code = (await svc.link_for(OWNER)).code
    await feed(dp, actx, builders["message"](f"/start {code}", user_id=VISITOR))
    photo = Message(
        message_id=777, date=datetime.now(UTC), chat=Chat(id=VISITOR, type="private"), from_user=tg_user(VISITOR),
        photo=[PhotoSize(file_id="p1", file_unique_id="u1", width=10, height=10)], caption="look <b>",
    )
    await feed(dp, actx, Update(update_id=99001, message=photo))
    [copy] = api.calls("CopyMessage")
    assert copy.chat_id == OWNER and copy.from_chat_id == VISITOR and copy.message_id == 777
    assert "New anonymous message" in copy.caption and "look &lt;b&gt;" in copy.caption
    assert not api.calls("ForwardMessage")


async def test_story_card_and_daily_prompt(actx, api, builders):
    from bots.anonymous.jobs import daily_prompt
    from core.db.base import utcnow

    dp = build_dispatcher(actx)
    svc = actx.extras["anon"]
    await feed(dp, actx, builders["message"]("/link", user_id=OWNER))
    [card] = api.calls("SendPhoto")
    assert (await svc.link_for(OWNER)).code in card.caption

    await svc.set_flag(OWNER, daily_prompt=True)
    await actx.settings.set("daily_prompt_hour_utc", utcnow().hour)
    await daily_prompt(actx)
    await daily_prompt(actx)  # only once per day
    prompts = [m for m in api.calls("SendMessage") if "Today's question" in (m.text or "")]
    assert len(prompts) == 1 and prompts[0].chat_id == OWNER
