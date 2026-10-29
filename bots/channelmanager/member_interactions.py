"""Owned captcha/requirements callbacks and expiring signed private continuation links."""

from __future__ import annotations

import hmac

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select, update

from bots.channelmanager.content import ContentError
from bots.channelmanager.member_delivery import contact_method, required_state
from bots.channelmanager.member_specs import MemberSpec
from bots.channelmanager.members import head_for, lead_for, start_token, welcome
from bots.channelmanager.models import (
    Channel,
    JoinRequest,
    MemberAction,
    MemberConfig,
    MemberGateReceipt,
    Operation,
)
from bots.channelmanager.permissions import AccessDenied
from core.db.base import utcnow
from core.i18n import Translate
from core.ui.respond import show


class GateCb(CallbackData, prefix="chj"):
    r: str
    g: int
    a: int
    u: int


async def interact(ctx, request_id, user, *, answer=None, generation=None, token=None, receipt_id=None):
    async with ctx.sm() as session:
        initial = await session.get(JoinRequest, (ctx.bot_id, request_id))
    if initial is None or initial.user_id != user.id or (token and not hmac.compare_digest(start_token(ctx, initial), token)):
        raise ContentError("stale")
    if generation is not None and initial.generation != generation:
        raise ContentError("stale")
    if utcnow() >= initial.expires_at:
        raise ContentError("member_expired")
    spec = MemberSpec.model_validate(initial.spec)
    index = None
    # A requirements API failure never records success or consumes a captcha attempt.
    if initial.captcha_solved or (answer is not None and answer == initial.challenge.get("answer")):
        index = await required_state(ctx, spec, user.id)
    async with ctx.sm() as session:
        channel = await session.get(Channel, (ctx.bot_id, initial.channel_id), with_for_update=True)
        head = await head_for(session, ctx, initial.channel_id, user.id)
        row = await session.get(JoinRequest, (ctx.bot_id, request_id), with_for_update=True, populate_existing=True)
        config = await session.get(MemberConfig, (ctx.bot_id, initial.channel_id))
        from bots.channelmanager.senders import allowed
        if not await allowed(ctx, initial.channel_id, session=session):
            raise ContentError("sender_changed")
        if (channel is None or channel.status != "active" or row is None or head.request_id != request_id or
                row.status not in {"pending", "approved"} or config is None or config.generation != row.config_generation or utcnow() >= row.expires_at):
            raise ContentError("stale")
        if receipt_id:
            if len(receipt_id) > 128:
                raise ContentError("stale")
            if await session.get(MemberGateReceipt, (ctx.bot_id, receipt_id)):
                return row
            session.add(MemberGateReceipt(bot_id=ctx.bot_id, callback_id=receipt_id, request_id=row.id))
        lead = await lead_for(session, ctx, initial.channel_id, user.id)
        lead.private_interacted_at = utcnow()
        # A callback proves interaction, but only a user-started conversation
        # establishes continued contact beyond Telegram's temporary window.
        lead.reachable = lead.reachable or bool(token)
        if row.status == "pending" and spec.captcha and not row.captcha_solved and answer is not None and answer >= 0:
            if row.captcha_attempts >= spec.captcha_attempts or not 0 <= answer < 4:
                raise ContentError("captcha_attempts")
            row.captcha_attempts += 1
            row.captcha_solved = answer == row.challenge["answer"]
        if index is not None and row.captcha_solved:
            row.required_index = index
            if index == len(spec.required):
                from bots.channelmanager.invitations import credit_request
                await credit_request(session, ctx, row)
        row.next_check = utcnow()
        if row.status == "approved":
            await welcome(session, ctx, channel, config, row, interactive=True)
        else:
            ids = select(MemberAction.operation_id).where(MemberAction.bot_id == ctx.bot_id, MemberAction.request_id == row.id,
                MemberAction.kind == "approve")
            await session.execute(update(Operation).where(Operation.bot_id == ctx.bot_id, Operation.id.in_(ids), Operation.status == "pending").values(run_at=utcnow()))
        await session.commit()
        return row


def build_router(ctx):
    router = Router(name=f"chm_member_gates_{ctx.slug}")
    router.message.filter(F.chat.type == "private")
    router.callback_query.filter(F.message.chat.type == "private")

    async def render(event, row, t):
        if row.status == "approved":
            await show(event, t("chm5-approved"))
            return
        spec = MemberSpec.model_validate(row.spec)
        if row.captcha_attempts >= spec.captcha_attempts and not row.captcha_solved:
            await show(event, t("chm5-attempts-used"))
            return
        method = await contact_method(ctx, row, spec)
        method.chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
        await ctx.bot(method)

    @router.message(CommandStart(deep_link=True), F.text.regexp(r"^/start(?:@\w+)? chj_[a-f0-9]{16}_[0-9]{10}_[a-f0-9]{20}$"))
    async def start(message: Message, t: Translate):
        token = (message.text or "").split(maxsplit=1)[1]
        try:
            row = await interact(ctx, token.split("_")[1], message.from_user, token=token)
            await render(message, row, t)
        except (ValueError, TelegramAPIError, AccessDenied) as exc:
            await show(message, t("chm5-gate-unavailable" if isinstance(exc, (TelegramAPIError, AccessDenied)) else "chm5-gate-stale"))

    @router.callback_query(GateCb.filter())
    async def callback(query: CallbackQuery, callback_data: GateCb, t: Translate):
        cb = callback_data
        if cb.u != query.from_user.id:
            await query.answer(t("chm-denied"), show_alert=True)
            return
        try:
            row = await interact(ctx, cb.r, query.from_user, answer=cb.a, generation=cb.g, receipt_id=query.id)
            await query.answer(t("chm5-progress"))
            await render(query, row, t)
        except (ValueError, TelegramAPIError, AccessDenied) as exc:
            await query.answer(t("chm5-gate-unavailable" if isinstance(exc, (TelegramAPIError, AccessDenied)) else "chm5-gate-stale"), show_alert=True)

    @router.callback_query(F.data.startswith("chj:"))
    async def malformed(query: CallbackQuery, t: Translate):
        await query.answer(t("chm5-gate-stale"), show_alert=True)

    return router
