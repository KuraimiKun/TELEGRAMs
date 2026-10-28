"""Admin panel flows driven through the dispatcher (super-admin id 999 comes from the ctx fixture)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from aiogram.types import ChatFullInfo, ChatMemberAdministrator, ChatMemberMember, User
from sqlalchemy import select

from core.callback_data import AdminNavCb, AdminPlanCb, AdminSettingCb, AdminUserCb, AdminUsersCb
from core.db.models import AdminAuditLog, BotUser, Payment
from core.runtime.dispatcher import build_dispatcher

ADMIN = 999


@pytest.fixture
def dp(ctx):
    return build_dispatcher(ctx)


async def feed(dp, ctx, update):
    await dp.feed_update(ctx.bot, update)


def texts(api, method="EditMessageText"):
    return [m.text for m in api.calls(method)]


async def audit_actions(ctx) -> list[str]:
    async with ctx.sm() as s:
        return [a.action for a in (await s.execute(select(AdminAuditLog).order_by(AdminAuditLog.id))).scalars()]


async def test_non_admins_cannot_open_the_panel(ctx, dp, api, builders):
    await feed(dp, ctx, builders["message"]("/admin", user_id=5))
    assert not any("Admin panel" in (m.text or "") for m in api.calls("SendMessage"))
    await feed(dp, ctx, builders["callback"](AdminNavCb(tab="users").pack(), user_id=5))
    assert api.calls("EditMessageText") == []


async def test_panel_only_shows_enabled_features(ctx, dp, api, builders):
    await feed(dp, ctx, builders["message"]("/admin", user_id=ADMIN))
    kb = api.calls("SendMessage")[-1].reply_markup.inline_keyboard
    labels = [b.text for row in kb for b in row]
    assert ctx.translator.get("en", "btn-adm-plans") in labels  # socialdownload has VIP
    assert ctx.translator.get("en", "sd-btn-admin-tab") in labels  # localized module tab


async def test_user_search_card_ban_with_reason_and_vip_grant(ctx, dp, api, builders):
    await ctx.users.get_or_create(42, "alice", "Alice", "en")
    await feed(dp, ctx, builders["callback"](AdminUserCb(user_id=0, action="search").pack(), user_id=ADMIN))
    await feed(dp, ctx, builders["message"]("42", user_id=ADMIN))
    card = api.calls("SendMessage")[-1].text
    assert "<code>42</code>" in card and "Alice" in card

    await feed(dp, ctx, builders["callback"](AdminUserCb(user_id=42, action="ban").pack(), user_id=ADMIN))
    await feed(dp, ctx, builders["message"]("spam <b>bot</b>", user_id=ADMIN))
    u = await ctx.users.get(42)
    assert u.is_banned and u.ban_reason == "spam <b>bot</b>"
    assert "spam &lt;b&gt;bot&lt;/b&gt;" in api.calls("SendMessage")[-1].text  # escaped in the card

    await feed(dp, ctx, builders["callback"](AdminUserCb(user_id=42, action="grant", arg=30).pack(), user_id=ADMIN))
    assert (await ctx.users.get(42)).is_vip()
    notified = [m for m in api.calls("SendMessage") if m.chat_id == 42]
    assert notified and "30" in notified[-1].text
    assert await audit_actions(ctx) == ["user.ban", "vip.grant"]


async def test_navigation_abandons_pending_input(ctx, dp, api, builders):
    await ctx.users.get_or_create(42, "alice", "Alice", "en")
    await feed(dp, ctx, builders["callback"](AdminUserCb(user_id=0, action="search").pack(), user_id=ADMIN))
    await feed(dp, ctx, builders["callback"](AdminNavCb(tab="home").pack(), user_id=ADMIN))
    sent_before = len(api.calls("SendMessage"))
    await feed(dp, ctx, builders["message"]("alice", user_id=ADMIN))  # no longer a search query
    later = api.calls("SendMessage")[sent_before:]
    assert not any("<code>42</code>" in (m.text or "") for m in later)


async def test_user_lists_paginate(ctx, dp, api, builders):
    for uid in range(100, 125):
        await ctx.users.get_or_create(uid, f"u{uid}", "U", "en")
    await feed(dp, ctx, builders["callback"](AdminUsersCb(kind="new", page=1).pack(), user_id=ADMIN))
    first = api.calls("EditMessageText")[-1]
    assert "1/3" in first.text
    user_rows = [r for r in first.reply_markup.inline_keyboard if r[0].callback_data.startswith("c_ausr:")]
    assert len(user_rows) == 10


async def test_refund_flow_calls_telegram_and_removes_paid_days(ctx, dp, api, builders):
    await ctx.users.get_or_create(42, "alice", "Alice", "en")
    await ctx.subs.grant_vip(42, 10, source="admin")
    await ctx.payments.record_payment(42, None, 150, 30, "charge-x")
    async with ctx.sm() as s:
        pay = (await s.execute(select(Payment))).scalar_one()

    await feed(dp, ctx, builders["callback"](AdminUserCb(user_id=42, action="refund_ok", arg=pay.id).pack(), user_id=ADMIN))
    refund = api.calls("RefundStarPayment")
    assert refund and refund[0].telegram_payment_charge_id == "charge-x" and refund[0].user_id == 42
    async with ctx.sm() as s:
        assert (await s.get(Payment, pay.id)).status == "refunded"
        bu = (await s.execute(select(BotUser).where(BotUser.user_id == 42))).scalar_one()
    remaining = (bu.vip_until - datetime.now(UTC)).days
    assert 8 <= remaining <= 10  # the 10 admin days survive; only the 30 paid days were removed


async def test_plans_crud_with_validation(ctx, dp, api, builders):
    await feed(dp, ctx, builders["callback"](AdminPlanCb(action="add").pack(), user_id=ADMIN))
    await feed(dp, ctx, builders["message"]("Bad | 0 | 10", user_id=ADMIN))
    assert "days must be" in api.calls("SendMessage")[-1].text
    await feed(dp, ctx, builders["message"]("Week | 7 | 50", user_id=ADMIN))  # state kept: retry works
    plans = [p for p in await ctx.subs.list_plans() if p.name == "Week"]
    assert plans and plans[0].days == 7 and plans[0].stars == 50

    pid = plans[0].id
    await feed(dp, ctx, builders["callback"](AdminPlanCb(action="toggle", plan_id=pid).pack(), user_id=ADMIN))
    assert not (await ctx.subs.get_plan(pid)).active
    await feed(dp, ctx, builders["callback"](AdminPlanCb(action="delete", plan_id=pid).pack(), user_id=ADMIN))
    assert await ctx.subs.get_plan(pid) is None


async def test_settings_edit_is_typed_and_validated(ctx, dp, api, builders):
    groups = list(ctx.module.settings_model.setting_groups())
    group = "free"
    idx = ctx.module.settings_model.setting_groups()[group].index("free_daily_limit")
    assert group in groups
    await feed(dp, ctx, builders["callback"](AdminSettingCb(group=group, idx=idx, action="edit").pack(), user_id=ADMIN))
    await feed(dp, ctx, builders["message"]("lots", user_id=ADMIN))
    assert "Invalid value" in api.calls("SendMessage")[-1].text
    await feed(dp, ctx, builders["message"]("25", user_id=ADMIN))
    assert (await ctx.settings.get()).free_daily_limit == 25

    # Forged callback with an out-of-range index is rejected.
    await feed(dp, ctx, builders["callback"](AdminSettingCb(group=group, idx=99, action="toggle").pack(), user_id=ADMIN))
    assert api.calls("AnswerCallbackQuery")[-1].text == ctx.translator.get("en", "adm-not-found")


async def test_channel_add_requires_bot_admin(ctx, dp, api, builders):
    from core.callback_data import AdminChannelCb

    chat = ChatFullInfo.model_construct(id=-1001, type="channel", title="News", username="news", invite_link=None)
    api.responses["GetChat"] = chat
    bot_user = User(id=ctx.bot_id, is_bot=True, first_name="B")
    api.responses["GetChatMember"] = ChatMemberMember(user=bot_user)
    await feed(dp, ctx, builders["callback"](AdminChannelCb(action="add").pack(), user_id=ADMIN))
    await feed(dp, ctx, builders["message"]("@news", user_id=ADMIN))
    assert ctx.translator.get("en", "adm-channel-not-admin") in texts(api, "SendMessage")
    assert await ctx.groups.list_channels() == []

    api.responses["GetChatMember"] = ChatMemberAdministrator.model_construct(user=bot_user, status="administrator")
    await feed(dp, ctx, builders["message"]("@news", user_id=ADMIN))
    channels = await ctx.groups.list_channels()
    assert [(c.chat_id, c.invite_link) for c in channels] == [(-1001, "https://t.me/news")]


async def test_search_by_name_lists_multiple_matches(ctx, dp, api, builders):
    await ctx.users.get_or_create(51, "bob_1", "Bob", "en")
    await ctx.users.get_or_create(52, "bobby", "Robert", "en")
    await ctx.users.get_or_create(53, "carol", "Carol", "en")
    await feed(dp, ctx, builders["callback"](AdminUserCb(user_id=0, action="search").pack(), user_id=ADMIN))
    await feed(dp, ctx, builders["message"]("bob", user_id=ADMIN))
    kb = api.calls("SendMessage")[-1].reply_markup.inline_keyboard
    ids = sorted(int(r[0].callback_data.split(":")[1]) for r in kb if r[0].callback_data.startswith("c_ausr:"))
    assert ids == [51, 52]

    # LIKE wildcards are escaped: "%" matches nothing instead of everyone.
    await feed(dp, ctx, builders["callback"](AdminUserCb(user_id=0, action="search").pack(), user_id=ADMIN))
    await feed(dp, ctx, builders["message"]("%", user_id=ADMIN))
    assert "No user matches" in api.calls("SendMessage")[-1].text
