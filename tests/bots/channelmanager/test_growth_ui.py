import pytest
from sqlalchemy import func, select

from bots.channelmanager.growth import lock_token
from bots.channelmanager.growth_ui import GrowthCb
from bots.channelmanager.models import (
    Campaign,
    ChannelPlanVersion,
    GrowthAction,
    LockedContent,
    SubscriberMenu,
    VirtualGrant,
)
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR
from tests.bots.channelmanager.test_channel_billing import catalog
from tests.bots.channelmanager.test_growth import body, lead, setup_growth
from tests.bots.channelmanager.test_publishing_ui import feed
from tests.conftest import BOT_ID, callback_update, message_update


@pytest.fixture(autouse=True)
def no_throttle(monkeypatch):
    from bots.channelmanager import outbox
    from core.middlewares.throttling import ThrottlingMiddleware
    async def passthrough(self, handler, event, data):
        return await handler(event, data)
    monkeypatch.setattr(ThrottlingMiddleware, "__call__", passthrough)
    async def immediate(*args):
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", immediate)


async def click(chm, dp, action, resource=CHANNEL_ID, generation=None, *, actor=OPERATOR, bound=OPERATOR):
    if generation is None:
        channel = await chm.extras["channelmanager"].get(CHANNEL_ID)
        generation = channel.generation if channel else 0
    await feed(chm, dp, callback_update(GrowthCb(a=action, x=str(resource), g=generation, u=bound).pack(), user_id=actor))


async def test_team_permission_change_requires_review_and_its_owner(chm, dp, api):
    await setup_growth(chm, api)
    await feed(chm, dp, message_update("/team"))
    await click(chm, dp, "teamedit")
    await feed(chm, dp, message_update("77 create,edit_own,delete_own"))
    async with chm.sm() as session:
        assert await session.get(VirtualGrant, (BOT_ID, CHANNEL_ID, 77)) is None
    await click(chm, dp, "teamsave", actor=88)
    async with chm.sm() as session:
        assert await session.get(VirtualGrant, (BOT_ID, CHANNEL_ID, 77)) is None
    await click(chm, dp, "teamsave")
    async with chm.sm() as session:
        assert (await session.get(VirtualGrant, (BOT_ID, CHANNEL_ID, 77))).active


async def test_lock_wizard_does_not_publish_and_signed_start_routes_privately(chm, dp, api):
    await setup_growth(chm, api)
    await click(chm, dp, "newlock")
    for text in ["Public teaser", "Private secret", "-"]:
        await feed(chm, dp, message_update(text))
    async with chm.sm() as session:
        row = await session.scalar(select(LockedContent))
        assert row is not None
        assert await session.scalar(select(func.count()).select_from(GrowthAction)) == 0
    assert not [m for m in api.calls("SendMessage") if m.chat_id == CHANNEL_ID]
    await feed(chm, dp, message_update(f"/start {lock_token(chm, row)}", user_id=77))
    async with chm.sm() as session:
        action = await session.scalar(select(GrowthAction))
        assert action.kind == "reveal" and action.user_id == 77


async def test_campaign_preview_and_confirm_are_separate(chm, dp, api):
    await setup_growth(chm, api)
    await lead(chm)
    await click(chm, dp, "newcamp")
    await feed(chm, dp, message_update("Campaign content"))
    async with chm.sm() as session:
        row = await session.scalar(select(Campaign))
        assert row.total == 1 and row.status == "draft"
        assert await session.scalar(select(func.count()).select_from(GrowthAction)) == 0
    await click(chm, dp, "csend", row.id, row.generation, actor=88)
    async with chm.sm() as session:
        assert (await session.get(Campaign, (BOT_ID, row.id))).status == "draft"
    await click(chm, dp, "csend", row.id, row.generation)
    async with chm.sm() as session:
        assert (await session.get(Campaign, (BOT_ID, row.id))).status == "queued"


async def test_catalog_wizard_keeps_prices_unpublished_until_review(chm, dp, api):
    await click(chm, dp, "plannew", "0", 0, actor=999, bound=999)
    await feed(chm, dp, message_update("Business\nbusiness 2 30 250\n50 40 40 5 20 2000 10 yes", user_id=999))
    async with chm.sm() as session:
        row = await session.scalar(select(ChannelPlanVersion))
        assert not row.published and row.spec["stars"] == 250
    await click(chm, dp, "planpub", row.id, 0, actor=999, bound=999)
    assert (await chm.extras["billing"].plans())[0].id == row.id


async def test_plan_choice_produces_reviewable_quote_before_invoice_delivery(chm, dp, api):
    plan = await catalog(chm, api)
    await click(chm, dp, "plans")
    await click(chm, dp, "q", plan.id + ".r")
    async with chm.sm() as session:
        from bots.channelmanager.models import ChannelInvoice
        invoice = await session.scalar(select(ChannelInvoice))
        assert invoice.status == "quoted" and invoice.amount == 100
        assert await session.scalar(select(func.count()).select_from(GrowthAction)) == 0
    await click(chm, dp, "pay", invoice.id, 0)
    async with chm.sm() as session:
        assert (await session.scalar(select(GrowthAction))).kind == "invoice"


async def test_subscriber_menu_feedback_and_explicit_subscription(chm, dp, api):
    await setup_growth(chm, api)
    await lead(chm, campaign_opt_in=False)
    await click(chm, dp, "menuedit")
    await feed(chm, dp, message_update("Subscriber menu"))
    await feed(chm, dp, message_update("Site - https://example.com"))
    async with chm.sm() as session:
        menu = await session.get(SubscriberMenu, (BOT_ID, CHANNEL_ID))
        assert menu.feedback and menu.content["buttons"][0][0]["url"] == "https://example.com"
    await click(chm, dp, "subscriber", actor=77, bound=77)
    assert any(m.text == "Subscriber menu" and m.chat_id == 77 for m in api.calls("SendMessage"))
    await click(chm, dp, "subscribe", actor=77, bound=77)
    await click(chm, dp, "fbnew", actor=77, bound=77)
    await feed(chm, dp, message_update("A question", user_id=77))
    async with chm.sm() as session:
        from bots.channelmanager.models import MemberLead
        assert (await session.get(MemberLead, (BOT_ID, CHANNEL_ID, 77))).campaign_opt_in
        assert (await session.scalar(select(GrowthAction))).kind == "feedback"


async def test_input_cancel_prevents_later_text_from_becoming_campaign(chm, dp, api):
    await setup_growth(chm, api)
    await click(chm, dp, "newcamp")
    await feed(chm, dp, message_update("/cancel"))
    await feed(chm, dp, message_update("Unrelated text"))
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(Campaign)) == 0


def test_growth_callbacks_fit_large_telegram_user_ids():
    for action, resource, generation in [("rfask", "a" * 32, 0), ("pay", "a" * 32, 0), ("cresume", "a" * 16, 99999999),
        ("bindask", "999999999999999999", 99999999)]:
        assert len(GrowthCb(a=action, x=resource, g=generation, u=999999999999999999).pack().encode()) <= 64


async def test_unlock_explains_ordered_required_chats_without_sending_secret(chm, dp, api):
    from aiogram.types import ChatMemberLeft

    from tests.bots.channelmanager.test_members import person
    await setup_growth(chm, api)
    required = [{"chat_id": CHANNEL_ID - 1, "url": "https://t.me/required_one"},
        {"chat_id": CHANNEL_ID - 2, "url": "https://t.me/required_two"}]
    row = await chm.extras["growth"].create_lock(CHANNEL_ID, OPERATOR, body("Teaser"), body("Secret"), required)
    previous = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: ChatMemberLeft(user=person(77)) if m.user_id == 77 and m.chat_id == CHANNEL_ID - 1 else previous(m)
    await feed(chm, dp, message_update(f"/start {lock_token(chm, row)}", user_id=77))
    message = api.calls("SendMessage")[-1]
    urls = [b.url for r in message.reply_markup.inline_keyboard for b in r]
    assert urls[:2] == ["https://t.me/required_one", "https://t.me/required_two"]
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(GrowthAction)) == 0


async def test_native_invoice_and_feedback_use_payer_operator_language(chm, api):
    from tests.bots.channelmanager.test_publishing import drain
    await chm.users.get_or_create(OPERATOR, None, "Owner", "ar")
    plan = await catalog(chm, api)
    invoice = await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id)
    await chm.extras["billing"].send_invoice(invoice.id, OPERATOR)
    await lead(chm)
    await chm.extras["growth"].menu(CHANNEL_ID, OPERATOR, body("Menu"), feedback=True)
    await chm.extras["growth"].feedback(CHANNEL_ID, 77, "سؤال", "arabic")
    await drain(chm)
    assert "القناة" in api.calls("SendInvoice")[0].description
    assert any("الملاحظة" in (m.text or "") and "سؤال" in m.text for m in api.calls("SendMessage"))


async def test_non_stars_payment_review_does_not_offer_native_stars_refund(chm, dp, api):
    from tests.bots.channelmanager.test_channel_billing import payment
    from tests.bots.channelmanager.test_members import person
    plan = await catalog(chm, api)
    invoice = await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id)
    assert await chm.extras["billing"].fulfill(person(OPERATOR), payment(invoice, currency="USD")) == "review"
    await click(chm, dp, "invoices")
    message = api.calls("EditMessageText")[-1]
    assert "USD" in message.text and "support" in message.text
    assert all(":irask:" not in b.callback_data for row in message.reply_markup.inline_keyboard for b in row)
