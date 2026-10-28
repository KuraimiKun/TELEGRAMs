"""VIP subscription and Telegram Stars billing router."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from core.callback_data import CoreVipCb
from core.db.models import BotUser
from core.i18n import Translate
from core.log import get_logger
from core.sdk.context import BotContext
from core.ui.kb import vip_plans_kb
from core.ui.respond import show
from core.ui.text import esc

log = get_logger(__name__)

STARS_CURRENCY = "XTR"


@dataclass(frozen=True, slots=True)
class InvoicePayload:
    """Everything needed to grant exactly what was invoiced. Format: ``c_vip:<slug>:<plan>:<user>:<days>:<stars>``."""

    slug: str
    plan_id: int
    user_id: int
    days: int
    stars: int

    def encode(self) -> str:
        return f"c_vip:{self.slug}:{self.plan_id}:{self.user_id}:{self.days}:{self.stars}"

    @classmethod
    def decode(cls, raw: str) -> InvoicePayload | None:
        parts = raw.split(":")
        if len(parts) != 6 or parts[0] != "c_vip":
            return None
        try:
            plan_id, user_id, days, stars = (int(p) for p in parts[2:])
        except ValueError:
            return None
        if days <= 0 or stars <= 0:
            return None
        return cls(slug=parts[1], plan_id=plan_id, user_id=user_id, days=days, stars=stars)


def build_router(ctx: BotContext) -> Router:
    router = Router(name=f"core_vip_{ctx.slug}")
    # Modules register their payment prefixes at setup. Unknown payloads are still rejected here,
    # while explicitly registered one-off purchases reach their own validation and entitlement handlers.
    other_payloads = tuple(ctx.extras.get("payment_payload_prefixes", ()))

    @router.message(Command("vip"))
    @router.callback_query(CoreVipCb.filter(F.action == "info"))
    async def show_vip_info(
        event: Message | CallbackQuery,
        user: BotUser,
        t: Translate,
    ) -> None:
        plans = await ctx.subs.list_active_plans()

        info = await ctx.module.vip_info(ctx)
        if user.is_vip() and user.vip_until:
            status_text = t("vip-status-active", until=user.vip_until.strftime("%Y-%m-%d"))
        else:
            status_text = t("vip-status-none", **info)

        text = t("vip-text", perks=t("vip-perks", **info), status=status_text)
        kb = vip_plans_kb(plans, t)

        await show(event, text, kb)

    @router.callback_query(CoreVipCb.filter(F.action == "buy"))
    async def buy_vip_plan(
        query: CallbackQuery,
        callback_data: CoreVipCb,
        t: Translate,
    ) -> None:
        plan = await ctx.subs.get_plan(callback_data.plan_id)
        if not plan or not plan.active:
            await query.answer(t("vip-no-plans"), show_alert=True)
            return

        title = t("vip-invoice-title", name=plan.name)
        desc = t("vip-invoice-desc", days=plan.days)
        payload = InvoicePayload(
            slug=ctx.slug, plan_id=plan.id, user_id=query.from_user.id, days=plan.days, stars=plan.stars
        ).encode()
        prices = [LabeledPrice(label=f"{plan.name} ({plan.days}d)", amount=plan.stars)]

        try:
            if query.message:
                await ctx.bot.send_invoice(
                    chat_id=query.message.chat.id,
                    title=title,
                    description=desc,
                    payload=payload,
                    currency=STARS_CURRENCY,
                    prices=prices,
                    start_parameter=f"vip-{plan.id}",
                )
            await query.answer()
        except Exception as e:
            log.error("send_invoice_error", error=str(e), bot=ctx.slug)
            await query.answer(t("error-unknown"), show_alert=True)

    @router.pre_checkout_query(~F.invoice_payload.startswith(other_payloads))
    async def process_pre_checkout(pre_checkout: PreCheckoutQuery) -> None:
        inv = InvoicePayload.decode(pre_checkout.invoice_payload or "")
        error = None
        if inv is None or inv.slug != ctx.slug:
            error = "Invalid invoice payload"
        elif inv.user_id != pre_checkout.from_user.id:
            error = "This invoice was issued to another user"
        elif pre_checkout.currency != STARS_CURRENCY or pre_checkout.total_amount != inv.stars:
            error = "Invoice amount mismatch"
        else:
            plan = await ctx.subs.get_plan(inv.plan_id)
            if not plan or not plan.active:
                error = "Plan is no longer available"
            elif plan.stars != inv.stars or plan.days != inv.days:
                error = "Plan has changed, please open /vip again"

        if error:
            log.warning("pre_checkout_rejected", bot=ctx.slug, user=pre_checkout.from_user.id, reason=error)
            await pre_checkout.answer(ok=False, error_message=error)
            return
        await pre_checkout.answer(ok=True)

    @router.message(F.successful_payment, ~F.successful_payment.invoice_payload.startswith(other_payloads))
    async def process_successful_payment(
        message: Message,
        t: Translate,
    ) -> None:
        sp = message.successful_payment
        if not sp or not message.from_user:
            return
        inv = InvoicePayload.decode(sp.invoice_payload or "")
        if inv is None or inv.slug != ctx.slug:
            log.error("successful_payment_unknown_payload", bot=ctx.slug, payload=sp.invoice_payload)
            return
        if sp.currency != STARS_CURRENCY or sp.total_amount != inv.stars:
            # Pre-checkout validated this; anything else needs a human look, never a silent grant.
            log.error(
                "successful_payment_amount_mismatch",
                bot=ctx.slug,
                charge_id=sp.telegram_payment_charge_id,
                amount=sp.total_amount,
                expected=inv.stars,
            )
            return

        user_id = message.from_user.id
        if inv.user_id != user_id:
            log.error("successful_payment_wrong_user", bot=ctx.slug, charge_id=sp.telegram_payment_charge_id)
            return
        # Group payments can precede any private interaction/UserMiddleware registration.
        # Register only after this bot's invoice, amount and actual payer were validated.
        await ctx.users.get_or_create(user_id,message.from_user.username,message.from_user.first_name,
                                      message.from_user.language_code)
        plan = await ctx.subs.get_plan(inv.plan_id)

        new_until, created = await ctx.payments.record_payment(
            user_id=user_id,
            plan_id=plan.id if plan else None,
            stars=sp.total_amount,
            days=inv.days,  # what was invoiced, not what the plan says now
            charge_id=sp.telegram_payment_charge_id,
        )
        if not created:
            return

        until_str = new_until.strftime("%Y-%m-%d %H:%M UTC")
        await message.reply(t("vip-activated", until=until_str))

        if ctx.env.log_channel_id:
            log_text = (
                f"⭐ <b>VIP Purchase</b> [{esc(ctx.slug)}]\n"
                f"👤 User: <code>{user_id}</code> (@{esc(message.from_user.username)})\n"
                f"📦 Plan: {esc(plan.name) if plan else 'Unknown'} ({inv.days} days)\n"
                f"💰 Amount: {sp.total_amount} Stars\n"
                f"🧾 Charge: <code>{esc(sp.telegram_payment_charge_id)}</code>\n"
                f"📅 Active until: {until_str}"
            )
            with contextlib.suppress(Exception):
                await ctx.bot.send_message(chat_id=ctx.env.log_channel_id, text=log_text)

    @router.message(F.refunded_payment, ~F.refunded_payment.invoice_payload.startswith(other_payloads))
    async def process_refunded_payment(message: Message, t: Translate) -> None:
        """Telegram-initiated refund (e.g. a dispute): take back exactly the refunded days."""
        rp = message.refunded_payment
        if not rp:
            return
        result = await ctx.payments.process_refund(rp.telegram_payment_charge_id)
        if result:
            await message.answer(t("vip-refunded"))

    return router
