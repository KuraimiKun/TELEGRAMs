"""Immutable channel quotes, payment-linked periods and non-destructive entitlement projection."""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import uuid
from datetime import timedelta
from fractions import Fraction
from typing import Any

from sqlalchemy import func, select, update

from bots.channelmanager.content import ContentError
from bots.channelmanager.growth_specs import ChannelLimits, ChannelPlanSpec
from bots.channelmanager.models import (
    AutoRule,
    BillingIncident,
    Channel,
    ChannelBilling,
    ChannelGrant,
    ChannelInvoice,
    ChannelPlanVersion,
    Delivery,
    Entitlement,
    Event,
    ForwardRoute,
    Inbox,
    LockedContent,
    Operation,
    PostSchedule,
    SenderBinding,
    VirtualGrant,
)
from bots.channelmanager.permissions import AccessDenied, bot_post_rights, operator_rights
from core.db.base import upsert, utcnow
from core.db.models import BotSetting, Payment


def is_catalog_admin(ctx, user_id):
    return not ctx.is_child and (ctx.platform.is_super_admin(user_id) or user_id in ctx.env.admin_ids)


async def control_scope(ctx, channel_id, session):
    if not ctx.is_child:
        return ctx.bot_id, channel_id
    binding = await session.scalar(select(SenderBinding).where(SenderBinding.sender_bot_id == ctx.bot_id,
        SenderBinding.channel_id == channel_id, SenderBinding.active.is_(True)))
    return (binding.bot_id, channel_id) if binding else (ctx.bot_id, channel_id)


async def paid_grants(session, bot_id, channel_id):
    return list((await session.scalars(select(ChannelGrant).join(Payment, Payment.id == ChannelGrant.payment_id).where(
        ChannelGrant.bot_id == bot_id, ChannelGrant.channel_id == channel_id, Payment.bot_id == bot_id,
        Payment.status == "paid", ChannelGrant.status == "paid").order_by(ChannelGrant.created_at, ChannelGrant.id))).all())


def current_grant(grants, now):
    valid = {}
    for grant in grants:
        if grant.parent_id and grant.parent_id not in valid:
            continue
        if grant.starts_at <= now < grant.ends_at:
            valid[grant.id] = grant
    return max(valid.values(), key=lambda g: (g.spec["rank"], g.created_at, g.id), default=None)


def fingerprint(grants):
    return hashlib.sha256(json.dumps([(g.id, g.status, g.starts_at.isoformat(), g.ends_at.isoformat()) for g in grants], separators=(",", ":")).encode()).hexdigest()


async def limits_for(ctx, channel_id, *, session=None):
    if session is None:
        async with ctx.sm() as owned:
            return await limits_for(ctx, channel_id, session=owned)
    bot_id, source = await control_scope(ctx, channel_id, session)
    grants = await paid_grants(session, bot_id, source)
    current = current_grant(grants, utcnow())
    if current:
        return ChannelPlanSpec.model_validate(current.spec).limits
    settings = dict((await session.execute(select(BotSetting.key, BotSetting.value).where(BotSetting.bot_id == bot_id))).all())
    default = ctx.module.settings_model()
    configured = default.model_dump() | settings
    state = await session.get(ChannelBilling, (bot_id, source))
    entitlement = await session.get(Entitlement, (ctx.bot_id, channel_id))
    return ChannelLimits(schedules=entitlement.max_schedules if entitlement and state is None else configured["free_max_schedules"],
        rules=configured["max_auto_rules_per_channel"], routes=configured["max_routes_per_channel"])


async def resource_allowed(ctx, channel_id, kind, resource_id, *, session):
    limits = await limits_for(ctx, channel_id, session=session)
    model: Any
    model, cap = {"rule": (AutoRule, limits.rules), "route": (ForwardRoute, limits.routes),
        "lock": (LockedContent, limits.locks), "delegate": (VirtualGrant, limits.delegates)}[kind]
    if cap == 0:
        return False
    order = [model.priority, model.id] if kind == "rule" else [model.created_at, model.user_id] if kind == "delegate" else [model.id]
    key = model.user_id if kind == "delegate" else model.id
    ids = (await session.scalars(select(key).where(model.bot_id == ctx.bot_id, model.channel_id == channel_id,
        model.active.is_(True)).order_by(*order).limit(cap))).all()
    return resource_id in ids


async def schedule_allowed(ctx, channel_id, delivery_id, *, session):
    cap = (await limits_for(ctx, channel_id, session=session)).schedules
    ids = (await session.scalars(select(Delivery.id).join(PostSchedule, (PostSchedule.bot_id == Delivery.bot_id) &
        (PostSchedule.post_id == Delivery.post_id)).where(Delivery.bot_id == ctx.bot_id, Delivery.channel_id == channel_id,
            Delivery.state.in_({"pending", "held"}), PostSchedule.status.in_({"pending", "held"}))
        .order_by(PostSchedule.run_at, Delivery.id).limit(cap))).all() if cap else []
    return delivery_id in ids


async def project(session, ctx, channel_id, *, reflow=False):
    now = utcnow()
    rows = list((await session.scalars(select(ChannelGrant).where(ChannelGrant.bot_id == ctx.bot_id,
        ChannelGrant.channel_id == channel_id).order_by(ChannelGrant.created_at, ChannelGrant.id).with_for_update())).all())
    for grant in rows:
        payment = await session.get(Payment, grant.payment_id)
        if payment is None or payment.bot_id != ctx.bot_id or payment.status == "refunded":
            grant.status = "refunded"
    if reflow:
        cursor = now
        for grant in [g for g in rows if not g.parent_id and g.status == "paid" and g.ends_at > now]:
            remaining = grant.ends_at - now if grant.starts_at <= now else timedelta(seconds=grant.seconds)
            grant.starts_at, grant.ends_at = cursor, cursor + remaining
            cursor = grant.ends_at
        by_id = {g.id: g for g in rows}
        for grant in [g for g in rows if g.parent_id and g.status == "paid"]:
            parent = by_id.get(grant.parent_id)
            if parent is None or parent.status != "paid":
                grant.status = "review"
                invoice = await session.get(ChannelInvoice, (ctx.bot_id, grant.invoice_id))
                payment = await session.get(Payment, grant.payment_id)
                if invoice and payment:
                    if invoice.status == "paid":
                        invoice.status = "review"
                    incident_id = hashlib.sha256(f"{payment.charge_id}:upgrade_parent_refunded".encode()).hexdigest()
                    await session.execute(upsert(session, BillingIncident).values(bot_id=ctx.bot_id, id=incident_id,
                        payer_id=invoice.payer_id, invoice_id=invoice.id, charge_id=payment.charge_id, amount=payment.stars,
                        currency="XTR", code="upgrade_parent_refunded").on_conflict_do_nothing())
            else:
                grant.ends_at = parent.ends_at
                grant.starts_at = max(grant.starts_at, parent.starts_at)
    await session.flush()
    current = current_grant([g for g in rows if g.status == "paid"], now)
    until = max((g.ends_at for g in rows if g.status == "paid" and not g.parent_id), default=None)
    state = await session.get(ChannelBilling, (ctx.bot_id, channel_id), with_for_update=True)
    value = current.spec if current else {}
    if state is None:
        state = ChannelBilling(bot_id=ctx.bot_id, channel_id=channel_id, current_plan=value, paid_until=until)
        session.add(state)
    elif state.current_plan != value or state.paid_until != until:
        state.current_plan, state.paid_until, state.generation = value, until, state.generation + 1
    await session.flush()
    limit = await limits_for(ctx, channel_id, session=session)
    entitlement = await session.get(Entitlement, (ctx.bot_id, channel_id), with_for_update=True)
    if entitlement:
        entitlement.max_schedules, entitlement.tier, entitlement.expires_at = limit.schedules, value.get("tier", "free"), until
    # Keep all data; hold excess future obligations for operator review.
    future = (await session.scalars(select(Delivery).join(PostSchedule, (PostSchedule.bot_id == Delivery.bot_id) &
        (PostSchedule.post_id == Delivery.post_id)).where(Delivery.bot_id == ctx.bot_id, Delivery.channel_id == channel_id,
            Delivery.state == "pending", PostSchedule.run_at > now).order_by(PostSchedule.run_at, Delivery.id))).all()
    for target in future[limit.schedules:]:
        target.state, target.error_code = "held", "plan_limit"
        if target.publish_op:
            ids = (await session.scalars(select(Operation.id).where(Operation.bot_id == ctx.bot_id,
                Operation.id == target.publish_op, Operation.dispatched.is_(False)).with_for_update(skip_locked=True))).all()
            await session.execute(update(Operation).where(Operation.bot_id == ctx.bot_id, Operation.id.in_(ids)).values(status="cancelled", error_code="plan_limit"))
    return state


class BillingService:
    def __init__(self, ctx):
        self.ctx = ctx

    async def plans(self):
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(ChannelPlanVersion).where(ChannelPlanVersion.bot_id == self.ctx.bot_id,
                ChannelPlanVersion.published.is_(True)).order_by(ChannelPlanVersion.created_at))).all())

    async def create_plan(self, actor_id, spec: ChannelPlanSpec):
        if not is_catalog_admin(self.ctx, actor_id):
            raise AccessDenied("catalog_admin")
        async with self.ctx.sm() as session:
            row = ChannelPlanVersion(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], spec=spec.model_dump(), created_by=actor_id)
            session.add(row)
            await session.commit()
            return row

    async def publish_plan(self, actor_id, plan_id, *, active=True):
        if not is_catalog_admin(self.ctx, actor_id):
            raise AccessDenied("catalog_admin")
        async with self.ctx.sm() as session:
            row = await session.get(ChannelPlanVersion, (self.ctx.bot_id, plan_id), with_for_update=True)
            if row is None:
                raise ContentError("stale")
            row.published = active
            await session.commit()
            return row

    async def quote(self, channel_id, payer_id, plan_id, *, kind="renew"):
        from bots.channelmanager.release import require
        await require(self.ctx, "billing")
        if self.ctx.is_child:
            raise ContentError("control_billing_only")
        await operator_rights(self.ctx, channel_id, payer_id)
        await bot_post_rights(self.ctx, channel_id, "publish")
        if kind not in {"renew", "upgrade", "downgrade"}:
            raise ContentError("invoice_kind")
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            plan = await session.get(ChannelPlanVersion, (self.ctx.bot_id, plan_id))
            if channel is None or channel.status != "active" or plan is None or not plan.published:
                raise ContentError("stale")
            spec = ChannelPlanSpec.model_validate(plan.spec)
            grants = await paid_grants(session, self.ctx.bot_id, channel_id)
            current = current_grant(grants, utcnow())
            amount, seconds, base_id, basis, end = spec.stars, spec.days * 86400, None, None, None
            if kind == "upgrade":
                if current is None or spec.rank <= current.spec["rank"]:
                    raise ContentError("upgrade")
                old = ChannelPlanSpec.model_validate(current.spec)
                if any(int(v) < int(old.limits.model_dump()[k]) for k, v in spec.limits.model_dump().items()):
                    raise ContentError("upgrade")
                seconds = math.ceil((current.ends_at - utcnow()).total_seconds())
                rate = Fraction(spec.stars, spec.days * 86400) - Fraction(old.stars, old.days * 86400)
                if rate <= 0 or seconds <= 0:
                    raise ContentError("upgrade")
                amount = max(1, math.ceil(rate * seconds))
                base_id, basis, end = current.id, fingerprint(grants), current.ends_at
            if kind == "downgrade" and (current is None or spec.rank >= current.spec["rank"]):
                raise ContentError("downgrade")
            row = ChannelInvoice(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=channel_id, payer_id=payer_id,
                plan_id=plan.id, spec=plan.spec, amount=amount, seconds=seconds, kind=kind, base_grant_id=base_id,
                basis_hash=basis, coverage_end=end, expires_at=utcnow() + timedelta(minutes=15))
            session.add(row)
            await session.commit()
            return row

    async def checkout(self, query):
        from bots.channelmanager.release import allowed
        if not await allowed(self.ctx, "billing"):
            return False
        if self.ctx.is_child or query.currency != "XTR" or not query.invoice_payload.startswith("chp_"):
            return False
        invoice_id = query.invoice_payload[4:]
        async with self.ctx.sm() as session:
            initial = await session.get(ChannelInvoice, (self.ctx.bot_id, invoice_id))
        if initial is None or initial.payer_id != query.from_user.id or initial.amount != query.total_amount:
            return False
        try:
            await asyncio.wait_for(asyncio.gather(operator_rights(self.ctx, initial.channel_id, query.from_user.id),
                bot_post_rights(self.ctx, initial.channel_id, "publish")), timeout=5)
        except (AccessDenied, TimeoutError):
            return False
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, initial.channel_id), with_for_update=True)
            row = await session.get(ChannelInvoice, (self.ctx.bot_id, invoice_id), with_for_update=True)
            plan = await session.get(ChannelPlanVersion, (self.ctx.bot_id, row.plan_id))
            if channel is None or channel.status != "active" or row.expires_at <= utcnow() or row.status not in {"quoted", "prechecked"} or plan is None or not plan.published:
                return False
            if row.checkout_id and row.checkout_id != query.id:
                return False
            if row.kind == "upgrade" and row.basis_hash != fingerprint(await paid_grants(session, self.ctx.bot_id, row.channel_id)):
                return False
            row.checkout_id, row.checkout_at, row.status = query.id, utcnow(), "prechecked"
            await session.commit()
            return True

    async def incident(self, session, payer_id, payment, code, invoice_id=None):
        key = hashlib.sha256(f"{payment.telegram_payment_charge_id}:{code}".encode()).hexdigest()
        await session.execute(upsert(session, BillingIncident).values(bot_id=self.ctx.bot_id, id=key, payer_id=payer_id,
            invoice_id=invoice_id, charge_id=payment.telegram_payment_charge_id, amount=payment.total_amount,
            currency=payment.currency[:8], code=code).on_conflict_do_nothing())

    async def fulfill(self, user, payment, *, receipt=None):
        invoice_id = payment.invoice_payload[4:] if payment.invoice_payload.startswith("chp_") else ""
        await self.ctx.users.get_or_create(user.id, user.username, user.first_name, user.language_code)
        async with self.ctx.sm() as session:
            initial = await session.get(ChannelInvoice, (self.ctx.bot_id, invoice_id))
        if self.ctx.is_child or payment.currency != "XTR" or initial is None:
            async with self.ctx.sm() as session:
                await self.incident(session, user.id, payment, "control_billing_only" if self.ctx.is_child else "unknown_invoice" if initial is None else "wrong_currency", invoice_id or None)
                await session.commit()
            return "review"
        try:
            await operator_rights(self.ctx, initial.channel_id, user.id)
            await bot_post_rights(self.ctx, initial.channel_id, "publish")
            authorized = True
        except AccessDenied:
            authorized = False
        outcome = "review"
        async def grant(session, payment_id):
            nonlocal outcome
            if receipt:
                item = await session.get(Inbox, (self.ctx.bot_id, receipt[0]), with_for_update=True)
                if item is None or item.lease_owner != receipt[1] or item.lease_until <= utcnow():
                    raise ContentError("receipt_lease")
            channel = await session.get(Channel, (self.ctx.bot_id, initial.channel_id), with_for_update=True)
            row = await session.get(ChannelInvoice, (self.ctx.bot_id, invoice_id), with_for_update=True)
            problem = None
            if row.payer_id != user.id or row.amount != payment.total_amount:
                problem = "invoice_mismatch"
            elif row.payment_id is not None:
                problem = "invoice_already_paid"
            elif not authorized or channel.status != "active":
                problem = "authorization_changed"
            elif row.checkout_at is None:
                problem = "checkout_missing"
            grants = await paid_grants(session, self.ctx.bot_id, row.channel_id)
            if row.kind == "upgrade" and (row.basis_hash != fingerprint(grants) or row.coverage_end <= utcnow()):
                problem = "upgrade_changed"
            if problem:
                await self.incident(session, user.id, payment, problem, invoice_id)
                if row.payment_id is None and row.payer_id == user.id:
                    row.status, row.payment_id, row.charge_id = "review", payment_id, payment.telegram_payment_charge_id
                return
            now = utcnow()
            start = now if row.kind == "upgrade" else max([now, *(g.ends_at for g in grants if not g.parent_id)])
            end = row.coverage_end if row.kind == "upgrade" else start + timedelta(seconds=row.seconds)
            session.add(ChannelGrant(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=row.channel_id,
                invoice_id=row.id, payment_id=payment_id, parent_id=row.base_grant_id, spec=row.spec, seconds=row.seconds, starts_at=start, ends_at=end))
            row.status, row.payment_id, row.charge_id = "paid", payment_id, payment.telegram_payment_charge_id
            session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=row.channel_id, actor_id=user.id,
                action="billing.paid", details={"invoice_id": row.id, "payment_id": payment_id}))
            await session.flush()
            await project(session, self.ctx, row.channel_id)
            outcome = "paid"
        created = await self.ctx.payments.record_one_off_payment(user.id, payment.total_amount, payment.telegram_payment_charge_id, grant)
        if not created:
            async with self.ctx.sm() as session:
                matching = await session.scalar(select(Payment).where(Payment.charge_id == payment.telegram_payment_charge_id,
                    Payment.bot_id == self.ctx.bot_id, Payment.user_id == user.id, Payment.stars == payment.total_amount))
                linked = await session.get(ChannelInvoice, (self.ctx.bot_id, invoice_id))
                if matching and linked and linked.payment_id == matching.id:
                    return "duplicate"
                await self.incident(session, user.id, payment, "charge_scope", invoice_id)
                await session.commit()
            return "review"
        return outcome

    async def apply_refund(self, charge_id):
        async with self.ctx.sm() as session:
            payment = await session.scalar(select(Payment).where(Payment.bot_id == self.ctx.bot_id, Payment.charge_id == charge_id))
        if payment is None:
            raise ContentError("payment_missing")
        await self.ctx.payments.process_refund(charge_id)
        async with self.ctx.sm() as session:
            initial = await session.scalar(select(ChannelInvoice).where(ChannelInvoice.bot_id == self.ctx.bot_id, ChannelInvoice.payment_id == payment.id))
            if initial:
                await session.get(Channel, (self.ctx.bot_id, initial.channel_id), with_for_update=True)
                invoice = await session.get(ChannelInvoice, (self.ctx.bot_id, initial.id), with_for_update=True)
                if invoice.status == "refunded":
                    return
                invoice.status = "refunded"
                await project(session, self.ctx, initial.channel_id, reflow=True)
                session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=initial.channel_id, actor_id=None,
                    action="billing.refunded", details={"invoice_id": initial.id}))
            await session.execute(update(BillingIncident).where(BillingIncident.bot_id == self.ctx.bot_id,
                BillingIncident.charge_id == charge_id).values(status="refunded"))
            await session.commit()

    async def invoice(self, invoice_id, actor_id):
        async with self.ctx.sm() as session:
            row = await session.get(ChannelInvoice, (self.ctx.bot_id, invoice_id))
        if row is None or (row.payer_id != actor_id and not is_catalog_admin(self.ctx, actor_id)):
            raise AccessDenied("invoice_payer")
        return row

    async def send_invoice(self, invoice_id, actor_id):
        from bots.channelmanager.release import require
        await require(self.ctx, "billing")
        initial = await self.invoice(invoice_id, actor_id)
        if self.ctx.is_child or actor_id != initial.payer_id:
            raise AccessDenied("invoice_payer")
        await operator_rights(self.ctx, initial.channel_id, actor_id)
        from bots.channelmanager.growth import enqueue
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, initial.channel_id), with_for_update=True)
            row = await session.get(ChannelInvoice, (self.ctx.bot_id, invoice_id), with_for_update=True)
            if channel.status != "active" or row.status != "quoted" or row.expires_at <= utcnow():
                raise ContentError("stale")
            action = await enqueue(session, self.ctx, channel, kind="invoice", actor_id=actor_id, user_id=actor_id,
                key=f"invoice:{invoice_id}", resource_id=invoice_id)
            await session.commit()
            return action

    async def request_refund(self, invoice_id, actor_id):
        initial = await self.invoice(invoice_id, actor_id)
        if self.ctx.is_child:
            raise ContentError("control_billing_only")
        from bots.channelmanager.growth import enqueue
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, initial.channel_id), with_for_update=True)
            row = await session.get(ChannelInvoice, (self.ctx.bot_id, invoice_id), with_for_update=True)
            if row.status not in {"paid", "review"} or not row.charge_id:
                raise ContentError("stale")
            row.status = "refunding"
            await session.execute(update(BillingIncident).where(BillingIncident.bot_id == self.ctx.bot_id,
                BillingIncident.charge_id == row.charge_id, BillingIncident.status == "review").values(status="refunding"))
            action = await enqueue(session, self.ctx, channel, kind="refund", actor_id=actor_id, user_id=row.payer_id,
                key=f"refund:{invoice_id}", resource_id=invoice_id, payload={"charge_id": row.charge_id})
            await session.commit()
            return action

    async def refund_incident(self, incident_id, actor_id):
        """Explicit recovery for an unapplied charge; never replay an ambiguous refund RPC."""
        from aiogram.methods import RefundStarPayment
        async with self.ctx.sm() as session:
            initial = await session.get(BillingIncident, (self.ctx.bot_id, incident_id))
            invoice = await session.scalar(select(ChannelInvoice).where(ChannelInvoice.bot_id == self.ctx.bot_id,
                ChannelInvoice.charge_id == initial.charge_id)) if initial else None
        if initial is None or (initial.payer_id != actor_id and not is_catalog_admin(self.ctx, actor_id)):
            raise AccessDenied("invoice_payer")
        if invoice:
            await self.request_refund(invoice.id, actor_id)
            return "pending"
        async with self.ctx.sm() as session:
            row = await session.get(BillingIncident, (self.ctx.bot_id, incident_id), with_for_update=True)
            if self.ctx.is_child or row is None or (row.payer_id != actor_id and not is_catalog_admin(self.ctx, actor_id)):
                raise AccessDenied("invoice_payer")
            if row.status != "review" or row.currency != "XTR":
                raise ContentError("stale")
            siblings = (await session.scalars(select(BillingIncident).where(BillingIncident.bot_id == self.ctx.bot_id,
                BillingIncident.charge_id == row.charge_id).with_for_update())).all()
            if any(v.status != "review" for v in siblings):
                raise ContentError("stale")
            for item in siblings:
                item.status = "refunding"
            charge, payer = row.charge_id, row.payer_id
            await session.commit()
        status = "refund_uncertain"
        try:
            if await self.ctx.bot(RefundStarPayment(user_id=payer, telegram_payment_charge_id=charge)) is True:
                status = "refunded"
                async with self.ctx.sm() as session:
                    known = await session.scalar(select(Payment.id).where(Payment.bot_id == self.ctx.bot_id, Payment.charge_id == charge))
                if known:
                    await self.apply_refund(charge)
        finally:
            async with self.ctx.sm() as session:
                await session.execute(update(BillingIncident).where(BillingIncident.bot_id == self.ctx.bot_id,
                    BillingIncident.charge_id == charge).values(status=status))
                await session.commit()
        return status

    async def impact(self, channel_id, actor_id, limits: ChannelLimits | None = None):
        await operator_rights(self.ctx, channel_id, actor_id)
        target = limits or ChannelLimits()
        async with self.ctx.sm() as session:
            return await self._impact(session, channel_id, target)

    async def _impact(self, session, channel_id, target):
        def count(model):
            return select(func.count()).select_from(model).where(model.bot_id == self.ctx.bot_id, model.channel_id == channel_id)
        schedules = await session.scalar(select(func.count()).select_from(Delivery).join(PostSchedule,
            (PostSchedule.bot_id == Delivery.bot_id) & (PostSchedule.post_id == Delivery.post_id)).where(
                Delivery.bot_id == self.ctx.bot_id, Delivery.channel_id == channel_id, Delivery.state.in_({"pending", "held"}),
                PostSchedule.status.in_({"pending", "held"}), PostSchedule.run_at > utcnow()))
        return {"rules_held": max(0, int(await session.scalar(count(AutoRule).where(AutoRule.active.is_(True))) or 0) - target.rules),
            "routes_held": max(0, int(await session.scalar(count(ForwardRoute).where(ForwardRoute.active.is_(True))) or 0) - target.routes),
            "delegates_held": max(0, int(await session.scalar(count(VirtualGrant).where(VirtualGrant.active.is_(True))) or 0) - target.delegates),
            "locks_held": max(0, int(await session.scalar(count(LockedContent).where(LockedContent.active.is_(True))) or 0) - target.locks),
            "schedules_held": max(0, int(schedules or 0) - target.schedules)}

    async def refund_preview(self, invoice_id, actor_id):
        invoice = await self.invoice(invoice_id, actor_id)
        settings = await self.ctx.settings.get()
        async with self.ctx.sm() as session:
            payment = await session.get(Payment, invoice.payment_id) if invoice.payment_id else None
            grants = [g for g in await paid_grants(session, self.ctx.bot_id, invoice.channel_id) if g.invoice_id != invoice.id]
            current = current_grant(grants, utcnow())
            next_base = next((g for g in grants if not g.parent_id and g.ends_at > utcnow()), None)
            chosen = current or next_base
            target = ChannelPlanSpec.model_validate(chosen.spec).limits if chosen else ChannelLimits(
                schedules=settings.free_max_schedules, rules=settings.max_auto_rules_per_channel, routes=settings.max_routes_per_channel)
            return payment.stars if payment else invoice.amount, await self._impact(session, invoice.channel_id, target)

    async def sweep(self, limit=25):
        async with self.ctx.sm() as session:
            ids = list((await session.scalars(select(ChannelBilling.channel_id).where(ChannelBilling.bot_id == self.ctx.bot_id)
                .order_by(ChannelBilling.channel_id))).all())
        cursor = self.ctx.extras.get("chm_billing_cursor", 0) % max(1, len(ids))
        selected = (ids[cursor:] + ids[:cursor])[:limit]
        self.ctx.extras["chm_billing_cursor"] = (cursor + len(selected)) % max(1, len(ids))
        for channel_id in selected:
            async with self.ctx.sm() as session:
                await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
                # A core refund sweep may have run before this projection.
                changed = await session.scalar(select(ChannelGrant.id).join(Payment, Payment.id == ChannelGrant.payment_id).where(
                    ChannelGrant.bot_id == self.ctx.bot_id, ChannelGrant.channel_id == channel_id,
                    ChannelGrant.status == "paid", Payment.status == "refunded").limit(1))
                refunded_ids = select(Payment.id).where(Payment.bot_id == self.ctx.bot_id, Payment.status == "refunded")
                await session.execute(update(ChannelInvoice).where(ChannelInvoice.bot_id == self.ctx.bot_id,
                    ChannelInvoice.channel_id == channel_id, ChannelInvoice.payment_id.in_(refunded_ids)).values(status="refunded"))
                await project(session, self.ctx, channel_id, reflow=bool(changed))
                await session.commit()
