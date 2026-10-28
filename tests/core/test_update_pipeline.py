"""End-to-end tests feeding real ``Update`` objects through a fully built dispatcher."""

from __future__ import annotations

from sqlalchemy import select

from core.db.models import BotUser, Payment
from core.routers.vip import InvoicePayload
from core.runtime.dispatcher import build_dispatcher


async def _feed(ctx, update):
    dp = build_dispatcher(ctx)
    return await dp.feed_update(ctx.bot, update)


async def test_referral_is_captured_from_start_payload(ctx, builders):
    dp = build_dispatcher(ctx)
    await dp.feed_update(ctx.bot, builders["message"]("/start", user_id=1))  # referrer joins first
    await dp.feed_update(ctx.bot, builders["message"]("/start ref_1", user_id=2))

    user = await ctx.users.get(2)
    assert user is not None and user.referred_by == 1


async def test_referral_ignored_when_referrer_not_member(ctx, builders):
    await _feed(ctx, builders["message"]("/start ref_777", user_id=3))
    user = await ctx.users.get(3)
    assert user is not None and user.referred_by is None


async def test_banned_user_gets_reply_in_private(ctx, api, builders):
    dp = build_dispatcher(ctx)
    await dp.feed_update(ctx.bot, builders["message"]("/start", user_id=5))
    await ctx.users.set_banned(5, True, "spam")
    api.requests.clear()

    await dp.feed_update(ctx.bot, builders["message"]("/profile", user_id=5))
    sent = api.calls("SendMessage")
    assert len(sent) == 1
    assert sent[0].text == ctx.translator.get("en", "banned")


async def test_banned_user_silent_in_groups(ctx, api, builders):
    dp = build_dispatcher(ctx)
    await dp.feed_update(ctx.bot, builders["message"]("/start", user_id=6))
    await ctx.users.set_banned(6, True)
    api.requests.clear()

    await dp.feed_update(ctx.bot, builders["message"]("hello", user_id=6, chat_type="supergroup", chat_id=-100))
    assert api.calls("SendMessage") == []


async def test_maintenance_blocks_users_but_not_admins(ctx, api, builders):
    dp = build_dispatcher(ctx)
    await ctx.settings.set("maintenance", True)
    await dp.feed_update(ctx.bot, builders["message"]("/profile", user_id=7))
    assert api.calls("SendMessage")[-1].text == ctx.translator.get("en", "maintenance")

    api.requests.clear()
    await dp.feed_update(ctx.bot, builders["message"]("/admin", user_id=999))  # super admin
    assert all(m.text != ctx.translator.get("en", "maintenance") for m in api.calls("SendMessage"))


async def test_throttle_drops_burst_and_warns_once(ctx, api, builders):
    dp = build_dispatcher(ctx)
    for _ in range(4):
        await dp.feed_update(ctx.bot, builders["message"]("/terms", user_id=8))
    texts = [m.text for m in api.calls("SendMessage")]
    assert texts.count(ctx.translator.get("en", "terms-text")) == 1
    assert texts.count(ctx.translator.get("en", "throttled")) == 1


async def _make_plan(ctx):
    return await ctx.subs.add_or_update_plan(None, "Month", days=30, stars=150)


async def test_payment_flow_grants_vip_even_right_after_pre_checkout(ctx, api, builders):
    plan = await _make_plan(ctx)
    dp = build_dispatcher(ctx)
    await dp.feed_update(ctx.bot, builders["message"]("/start", user_id=10))
    payload = InvoicePayload("socialdownload", plan.id, 10, 30, 150).encode()

    await dp.feed_update(ctx.bot, builders["pre_checkout"](payload, 150, user_id=10))
    answer = api.calls("AnswerPreCheckoutQuery")[-1]
    assert answer.ok is True

    # Arrives within the throttle window: must still be processed.
    await dp.feed_update(ctx.bot, builders["payment"](payload, 150, "charge-1", user_id=10))
    user = await ctx.users.get(10)
    assert user is not None and user.is_vip()

    # Redelivery does not double-grant.
    first_until = user.vip_until
    await dp.feed_update(ctx.bot, builders["payment"](payload, 150, "charge-1", user_id=10))
    user = await ctx.users.get(10)
    assert user.vip_until == first_until
    async with ctx.sm() as s:
        assert len((await s.execute(select(Payment))).scalars().all()) == 1


async def test_pre_checkout_rejects_tampered_invoices(ctx, api, builders):
    plan = await _make_plan(ctx)
    dp = build_dispatcher(ctx)
    good = InvoicePayload("socialdownload", plan.id, 11, 30, 150)

    cases = [
        (good.encode(), 1, 11),  # wrong amount
        (good.encode(), 150, 12),  # paid by another user
        (InvoicePayload("otherbot", plan.id, 11, 30, 150).encode(), 150, 11),  # other bot
        (InvoicePayload("socialdownload", plan.id, 11, 300, 150).encode(), 150, 11),  # days tampered
        ("garbage", 150, 11),
    ]
    for payload, amount, uid in cases:
        await dp.feed_update(ctx.bot, builders["pre_checkout"](payload, amount, user_id=uid))
        assert api.calls("AnswerPreCheckoutQuery")[-1].ok is False, payload


async def test_lang_callback_rejects_unknown_locale(ctx, builders):
    dp = build_dispatcher(ctx)
    await dp.feed_update(ctx.bot, builders["message"]("/start", user_id=20))
    await dp.feed_update(ctx.bot, builders["callback"]("c_lng:xx-evil-very-long", user_id=20))
    async with ctx.sm() as s:
        bu = (await s.execute(select(BotUser).where(BotUser.user_id == 20))).scalar_one()
    assert bu.lang == "en"


async def test_unhandled_errors_are_reported_to_the_user(ctx, api, builders):
    from aiogram import Router
    from aiogram.filters import Command

    boom = Router()

    @boom.message(Command("boom"))
    async def explode(_message) -> None:
        raise RuntimeError("kaboom")

    dp = build_dispatcher(ctx)
    dp.include_router(boom)
    await dp.feed_update(ctx.bot, builders["message"]("/boom", user_id=30))
    assert api.calls("SendMessage")[-1].text == ctx.translator.get("en", "error-unknown")


async def test_backlog_after_downtime_is_not_throttled(ctx, api, builders):
    from datetime import UTC, datetime, timedelta

    dp = build_dispatcher(ctx)
    old = datetime.now(UTC) - timedelta(minutes=5)
    for text in ("/terms", "/support", "/terms"):
        upd = builders["message"](text, user_id=31)
        await dp.feed_update(ctx.bot, upd.model_copy(update={"message": upd.message.model_copy(update={"date": old})}))
    assert ctx.translator.get("en", "throttled") not in [m.text for m in api.calls("SendMessage")]
    assert len(api.calls("SendMessage")) == 3
