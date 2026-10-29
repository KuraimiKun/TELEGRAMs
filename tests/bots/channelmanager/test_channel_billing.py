"""Channel Stars purchases remain atomic, scoped and independent of personal VIP."""

import uuid
from datetime import timedelta

import pytest
from aiogram.types import Chat, Message, PreCheckoutQuery, SuccessfulPayment, Update
from sqlalchemy import func, select

from bots.channelmanager import ingress, outbox, worker
from bots.channelmanager.billing import limits_for
from bots.channelmanager.content import ContentError, PostSpec, TextBody
from bots.channelmanager.growth_specs import ChannelLimits, ChannelPlanSpec
from bots.channelmanager.models import (
    BillingIncident,
    ChannelGrant,
    ChannelInvoice,
    Delivery,
    Event,
    Inbox,
    Operation,
)
from bots.channelmanager.permissions import AccessDenied
from core.db.base import utcnow
from core.db.models import Payment
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR
from tests.bots.channelmanager.test_growth import setup_growth
from tests.bots.channelmanager.test_members import person
from tests.bots.channelmanager.test_publishing import drain
from tests.conftest import BOT_ID


@pytest.fixture(autouse=True)
def immediate(monkeypatch):
    async def reserve(*args):
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", reserve)


async def catalog(chm, api, *, stars=100, days=30, rank=1, limits=None):
    await setup_growth(chm, api)
    spec = ChannelPlanSpec(name="Plan", tier=f"tier{rank}", rank=rank, stars=stars, days=days,
        limits=limits or ChannelLimits(schedules=40, rules=40, routes=40, delegates=5))
    plan = await chm.extras["billing"].create_plan(999, spec)
    await chm.extras["billing"].publish_plan(999, plan.id)
    return plan


def checkout(invoice, *, payer=OPERATOR, amount=None, currency="XTR", query_id=None):
    return PreCheckoutQuery(id=query_id or uuid.uuid4().hex, from_user=person(payer), currency=currency,
        total_amount=invoice.amount if amount is None else amount, invoice_payload=f"chp_{invoice.id}")


def payment(invoice, *, amount=None, currency="XTR", charge=None, payload=None):
    return SuccessfulPayment(currency=currency, total_amount=invoice.amount if amount is None else amount,
        invoice_payload=payload or f"chp_{invoice.id}", telegram_payment_charge_id=charge or uuid.uuid4().hex,
        provider_payment_charge_id="")


async def buy(chm, plan, *, kind="renew", charge=None):
    invoice = await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id, kind=kind)
    assert await chm.extras["billing"].checkout(checkout(invoice))
    paid = payment(invoice, charge=charge)
    assert await chm.extras["billing"].fulfill(person(OPERATOR), paid) == "paid"
    return invoice, paid


async def test_catalog_unpublished_by_default_and_restricted_to_main_platform_admin(chm, api):
    await setup_growth(chm, api)
    spec = ChannelPlanSpec(name="Unpublished", tier="unpublished", rank=1, days=30, stars=123)
    with pytest.raises(AccessDenied):
        await chm.extras["billing"].create_plan(OPERATOR, spec)
    row = await chm.extras["billing"].create_plan(999, spec)
    assert not row.published and await chm.extras["billing"].plans() == []
    with pytest.raises(ContentError):
        await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, row.id)


@pytest.mark.parametrize("variation", ["payer", "amount", "currency", "retired", "expired", "unauthorized"])
async def test_checkout_rejects_changed_quote_or_resource(chm, api, variation):
    plan = await catalog(chm, api)
    invoice = await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id)
    query = checkout(invoice, payer=77 if variation == "payer" else OPERATOR,
        amount=101 if variation == "amount" else None, currency="USD" if variation == "currency" else "XTR")
    if variation == "retired":
        await chm.extras["billing"].publish_plan(999, plan.id, active=False)
    if variation == "expired":
        async with chm.sm() as session:
            row = await session.get(ChannelInvoice, (BOT_ID, invoice.id))
            row.expires_at = utcnow() - timedelta(seconds=1)
            await session.commit()
    if variation == "unauthorized":
        from aiogram.types import ChatMemberLeft
        original = api.responses["GetChatMember"]
        api.responses["GetChatMember"] = lambda m: ChatMemberLeft(user=person(OPERATOR)) if m.user_id == OPERATOR else original(m)
    assert not await chm.extras["billing"].checkout(query)


async def test_checkout_duplicate_reservation_and_payment_duplicate_grant_once(chm, api):
    plan = await catalog(chm, api)
    invoice = await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id)
    query = checkout(invoice)
    assert await chm.extras["billing"].checkout(query)
    assert await chm.extras["billing"].checkout(query)
    assert not await chm.extras["billing"].checkout(checkout(invoice))
    paid = payment(invoice)
    assert await chm.extras["billing"].fulfill(person(OPERATOR), paid) == "paid"
    assert await chm.extras["billing"].fulfill(person(OPERATOR), paid) == "duplicate"
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(ChannelGrant)) == 1
        record = await session.scalar(select(Payment))
        assert record.days == 0 and record.stars == 100
    assert (await chm.users.get(OPERATOR)).vip_until is None
    assert (await limits_for(chm, CHANNEL_ID)).schedules == 40


@pytest.mark.parametrize("variation", ["payer", "amount", "currency", "payload", "checkout_missing"])
async def test_invalid_successful_payment_creates_review_without_channel_grant(chm, api, variation):
    plan = await catalog(chm, api)
    invoice = await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id)
    if variation != "checkout_missing":
        assert await chm.extras["billing"].checkout(checkout(invoice))
    paid = payment(invoice, amount=101 if variation == "amount" else None,
        currency="USD" if variation == "currency" else "XTR", payload="chp_missing" if variation == "payload" else None)
    assert await chm.extras["billing"].fulfill(person(77 if variation == "payer" else OPERATOR), paid) == "review"
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(ChannelGrant)) == 0
        assert await session.scalar(select(func.count()).select_from(BillingIncident)) == 1


async def test_late_success_after_accepted_checkout_uses_immutable_quote(chm, api):
    plan = await catalog(chm, api)
    invoice = await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id)
    assert await chm.extras["billing"].checkout(checkout(invoice))
    async with chm.sm() as session:
        row = await session.get(ChannelInvoice, (BOT_ID, invoice.id))
        row.expires_at = utcnow() - timedelta(seconds=1)
        await session.commit()
    await chm.extras["billing"].publish_plan(999, plan.id, active=False)
    assert await chm.extras["billing"].fulfill(person(OPERATOR), payment(invoice)) == "paid"


async def test_renewal_downgrade_and_prorated_upgrade_periods(chm, api):
    first = await catalog(chm, api)
    higher = await catalog(chm, api, stars=200, rank=2, limits=ChannelLimits(schedules=80, rules=80, routes=80, delegates=10))
    _invoice, paid = await buy(chm, first)
    upgrade = await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, higher.id, kind="upgrade")
    assert upgrade.amount == 100 and 29 * 86400 < upgrade.seconds <= 30 * 86400
    assert await chm.extras["billing"].checkout(checkout(upgrade))
    assert await chm.extras["billing"].fulfill(person(OPERATOR), payment(upgrade)) == "paid"
    assert (await limits_for(chm, CHANNEL_ID)).schedules == 80
    downgrade, _ = await buy(chm, first, kind="downgrade")
    async with chm.sm() as session:
        grants = (await session.scalars(select(ChannelGrant).order_by(ChannelGrant.created_at))).all()
        assert grants[1].parent_id == grants[0].id
        assert grants[1].ends_at == grants[0].ends_at
        assert grants[2].starts_at == grants[0].ends_at
        assert grants[2].invoice_id == downgrade.id
    await chm.extras["billing"].apply_refund(paid.telegram_payment_charge_id)
    async with chm.sm() as session:
        grants = (await session.scalars(select(ChannelGrant).order_by(ChannelGrant.created_at))).all()
        assert [g.status for g in grants] == ["refunded", "review", "paid"]
        assert grants[2].starts_at <= utcnow() < grants[2].ends_at
    assert (await limits_for(chm, CHANNEL_ID)).schedules == 40


async def test_upgrade_quote_invalidated_by_another_paid_period(chm, api):
    first = await catalog(chm, api)
    higher = await catalog(chm, api, stars=200, rank=2)
    await buy(chm, first)
    upgrade = await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, higher.id, kind="upgrade")
    assert await chm.extras["billing"].checkout(checkout(upgrade))
    await buy(chm, first)
    assert await chm.extras["billing"].fulfill(person(OPERATOR), payment(upgrade)) == "review"
    async with chm.sm() as session:
        row = await session.get(ChannelInvoice, (BOT_ID, upgrade.id))
        assert row.status == "review" and row.charge_id and row.payment_id
    await chm.extras["billing"].request_refund(upgrade.id, OPERATOR)
    await drain(chm)
    assert api.calls("RefundStarPayment")


async def test_refund_idempotent_preserves_unrelated_paid_time_and_personal_vip(chm, api):
    plan = await catalog(chm, api)
    await chm.users.get_or_create(OPERATOR, None, "Owner", "en")
    vip = await chm.subs.grant_vip(OPERATOR, 90, source="admin")
    _first, paid = await buy(chm, plan)
    second, _ = await buy(chm, plan)
    await chm.extras["billing"].apply_refund(paid.telegram_payment_charge_id)
    async with chm.sm() as session:
        grant = await session.scalar(select(ChannelGrant).where(ChannelGrant.invoice_id == second.id))
        end = grant.ends_at
    await chm.extras["billing"].apply_refund(paid.telegram_payment_charge_id)
    async with chm.sm() as session:
        assert (await session.scalar(select(ChannelGrant).where(ChannelGrant.invoice_id == second.id))).ends_at == end
        assert await session.scalar(select(func.count()).select_from(Event).where(Event.action == "billing.refunded")) == 1
    assert (await chm.users.get(OPERATOR)).vip_until == vip


async def test_expiry_holds_excess_schedule_without_deleting_posts_or_cleanup(chm, api):
    plan = await catalog(chm, api, limits=ChannelLimits(schedules=40))
    _, paid = await buy(chm, plan)
    await chm.settings.set("free_max_schedules", 1)
    for n in range(2):
        post = await chm.extras["posts"].create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text=str(n))))
        await chm.extras["posts"].publish(post.id, OPERATOR, post.generation, run_at=utcnow() + timedelta(hours=n + 1))
    await chm.extras["billing"].apply_refund(paid.telegram_payment_charge_id)
    async with chm.sm() as session:
        targets = (await session.scalars(select(Delivery).order_by(Delivery.id))).all()
        assert sorted(t.state for t in targets) == ["held", "pending"]
        assert await session.scalar(select(func.count()).select_from(ChannelGrant)) == 1


async def test_financial_receipt_durable_before_ack_and_processed_during_maintenance(chm, dp, api):
    plan = await catalog(chm, api)
    invoice = await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id)
    assert await chm.extras["billing"].checkout(checkout(invoice))
    paid = payment(invoice)
    event = Update(update_id=55001, message=Message(message_id=1, date=utcnow(), from_user=person(OPERATOR),
        chat=Chat(id=OPERATOR, type="private"), successful_payment=paid))
    await dp.feed_update(chm.bot, event)
    await dp.feed_update(chm.bot, event)
    async with chm.sm() as session:
        receipt = await session.get(Inbox, (BOT_ID, event.update_id))
        assert receipt.event_type == "billing_paid" and receipt.status == "pending"
        assert await session.scalar(select(func.count()).select_from(Payment)) == 0
    assert not await ingress.process_one(chm)
    await chm.settings.set("maintenance", True)
    await worker.tick(chm)
    async with chm.sm() as session:
        receipt = await session.get(Inbox, (BOT_ID, event.update_id))
        assert receipt.status == "completed" and receipt.payload == {}
        assert await session.scalar(select(func.count()).select_from(ChannelGrant)) == 1


async def test_shared_refund_sweep_reconciles_channel_periods(chm, api):
    plan = await catalog(chm, api)
    _, paid = await buy(chm, plan)
    second, _ = await buy(chm, plan)
    await chm.payments.process_refund(paid.telegram_payment_charge_id)
    await chm.extras["billing"].sweep()
    async with chm.sm() as session:
        next_grant = await session.scalar(select(ChannelGrant).where(ChannelGrant.invoice_id == second.id))
        assert next_grant.starts_at <= utcnow() < next_grant.ends_at


async def test_only_payer_can_request_channel_refund(chm, api):
    plan = await catalog(chm, api)
    invoice, _ = await buy(chm, plan)
    with pytest.raises(AccessDenied):
        await chm.extras["billing"].request_refund(invoice.id, 77)
    await chm.extras["billing"].request_refund(invoice.id, OPERATOR)
    await drain(chm)
    async with chm.sm() as session:
        assert (await session.get(ChannelInvoice, (BOT_ID, invoice.id))).status == "refunded"
        assert (await session.scalar(select(Payment))).status == "refunded"
        assert await session.scalar(select(func.count()).select_from(Operation).where(Operation.kind == "growth_refund")) == 1


async def test_unknown_refund_result_waits_for_native_receipt_without_replay(chm, api):
    from aiogram.exceptions import TelegramNetworkError
    plan = await catalog(chm, api)
    invoice, paid = await buy(chm, plan)
    await chm.extras["billing"].request_refund(invoice.id, OPERATOR)
    api.responses["RefundStarPayment"] = lambda m: TelegramNetworkError(method=m, message="lost result")
    await drain(chm)
    async with chm.sm() as session:
        assert (await session.get(ChannelInvoice, (BOT_ID, invoice.id))).status == "refund_uncertain"
        assert (await session.scalar(select(Payment))).status == "paid"
    await drain(chm)
    assert len(api.calls("RefundStarPayment")) == 1
    await chm.extras["billing"].apply_refund(paid.telegram_payment_charge_id)
    assert (await limits_for(chm, CHANNEL_ID)).schedules == (await chm.settings.get()).free_max_schedules


async def test_charge_cannot_fulfill_a_different_invoice(chm, api):
    plan = await catalog(chm, api)
    _, paid = await buy(chm, plan)
    second = await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id)
    assert await chm.extras["billing"].checkout(checkout(second))
    changed = paid.model_copy(update={"invoice_payload": f"chp_{second.id}"})
    assert await chm.extras["billing"].fulfill(person(OPERATOR), changed) == "review"
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(ChannelGrant)) == 1
        assert (await session.scalar(select(BillingIncident))).code == "charge_scope"


async def test_refund_preview_uses_actual_review_charge_amount(chm, api):
    plan = await catalog(chm, api)
    invoice = await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id)
    assert await chm.extras["billing"].checkout(checkout(invoice))
    assert await chm.extras["billing"].fulfill(person(OPERATOR), payment(invoice, amount=101)) == "review"
    amount, impact = await chm.extras["billing"].refund_preview(invoice.id, OPERATOR)
    assert amount == 101 and "schedules_held" in impact


async def test_expired_receipt_owner_cannot_grant_payment(chm, api):
    plan = await catalog(chm, api)
    invoice = await chm.extras["billing"].quote(CHANNEL_ID, OPERATOR, plan.id)
    assert await chm.extras["billing"].checkout(checkout(invoice))
    async with chm.sm() as session:
        session.add(Inbox(bot_id=BOT_ID, update_id=55002, event_type="billing_paid", payload={},
            lease_owner="new_owner", lease_until=utcnow() + timedelta(seconds=90)))
        await session.commit()
    with pytest.raises(ContentError, match="receipt_lease"):
        await chm.extras["billing"].fulfill(person(OPERATOR), payment(invoice), receipt=(55002, "old_owner"))
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(Payment)) == 0
        assert await session.scalar(select(func.count()).select_from(ChannelGrant)) == 0
