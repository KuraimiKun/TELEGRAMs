"""Actual CAPTCHA issuance, private image cards, progressive choices and frozen rules."""
from __future__ import annotations

import json
import math
import secrets
from datetime import timedelta

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User,
)
from redis.exceptions import RedisError

from bots.groupguard import actions, authz, captcha_modes, challenges, delivery, durable
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.contracts import ActionResult, StepResult, result_of
from bots.groupguard.keyboards import GgCb
from bots.groupguard.models import GuardChallenge, GuardJob, GuardRestriction
from core.db.base import utcnow
from core.sdk.context import BotContext


def markup(ctx: BotContext, state: GuardChallenge) -> InlineKeyboardMarkup:
    frozen = ChatConfig.model_validate(state.policy)
    t = actions.group_t(ctx, frozen)
    if state.question_solved and frozen.captcha_rules and frozen.rules and not state.rules_accepted:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t("gg-btn-accept-rules"),
            callback_data=GgCb(action="cap", chat=state.chat_id, user=state.user_id, arg=state.generation + ".r.ok").pack())]])
    question = captcha_modes.Question.from_dict(state.prompt)
    sequence = len(state.progress) if state.mode == "text2" else 0
    buttons = [InlineKeyboardButton(text=(frozen.captcha_text or t("gg-btn-human")) if state.mode == "button" else value,
        callback_data=GgCb(action="cap", chat=state.chat_id, user=state.user_id,
            arg=f"{state.generation}.{sequence}.{index}").pack()) for index, value in enumerate(question.choices)]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i:i+4] for i in range(0, len(buttons), 4)])


async def state_of(ctx: BotContext, chat_id: int, user_id: int) -> GuardChallenge | None:
    async with ctx.sm() as session:
        return await session.get(GuardChallenge, (ctx.bot_id, chat_id, user_id))


async def send_card(ctx: BotContext, state: GuardChallenge, destination: int, user: User) -> Message | None:
    if state.status not in {"issuing", "pending"} or state.deadline <= utcnow() or not await authz.active_namespace(ctx):
        return None
    if state.contact_deadline is not None and state.contact_deadline <= utcnow():
        return None
    frozen = ChatConfig.model_validate(state.policy)
    t = actions.group_t(ctx, frozen)
    kb = markup(ctx, state)
    sent = None
    if state.question_solved and frozen.captcha_rules and frozen.rules and not state.rules_accepted:
        f = await delivery.fillings(ctx, state.chat_id, user, raw=frozen.rules)
        body = await delivery.send(ctx, destination, delivery.Content(frozen.rules, frozen.rules_format), f,
            kind="rules", extra_keyboard=kb, owner_id=user.id)
        # Real returned message carrying the acceptance button, rather than a guessed message ID.
        return body.messages[-1] if body.result.primary_completed and body.messages else None
    text = (t("gg-captcha", user=actions.mention(user.id, user.first_name),
        minutes=str(max(1, math.ceil((state.deadline-utcnow()).total_seconds() / 60)))) + "\n" + t("gg-captcha-button")) if state.mode == "button" else t(f"gg-captcha-question-{state.mode}", position=str(len(state.progress)+1))
    async def call():
        nonlocal sent
        if state.mode == "button":
            sent = await ctx.bot.send_message(destination, text, reply_markup=kb)
        else:
            question = captcha_modes.Question.from_dict(state.prompt)
            sent = await ctx.bot.send_photo(destination, BufferedInputFile(question.png(), filename="verification.png"),
                caption=text, reply_markup=kb)
        return sent if isinstance(sent, Message) else False
    step = await actions.perform("captcha_card", call)
    return sent if step.completed and isinstance(sent, Message) else None


async def personal_link(ctx: BotContext, state: GuardChallenge, label: str) -> InlineKeyboardMarkup | None:
    token = secrets.token_urlsafe(16)
    value = dict(bot_id=ctx.bot_id, chat_id=state.chat_id, user_id=state.user_id, generation=state.generation)
    try:
        ttl = max(1, int((state.deadline-utcnow()).total_seconds()))
        stored = await ctx.redis.set(ctx.keys("captcha_open", token), json.dumps(value), ex=min(ttl, 86400))
    except RedisError:
        return None
    if not stored:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=label,
        url=f"https://t.me/{ctx.username}?start=ggv_{token}")]])


async def issue_group(ctx: BotContext, cfg: ChatConfig, chat_id: int, user: User, *, event_identity: str,
                      before_card=None) -> bool:
    mode = cfg.effective_captcha()
    if mode == "off":
        return False
    question = captcha_modes.question(mode)
    seconds = cfg.verification_seconds() if cfg.captcha_kick else 86400
    generation = await challenges.begin(ctx, chat_id, user.id, cfg, mode=mode, answer=question.answer,
        deadline=utcnow()+timedelta(seconds=seconds), prompt=question.to_dict(), event_identity=event_identity)
    if not generation:
        return True  # Duplicate observed join cannot renew or extend an active issuance.
    muted = await actions.punish(ctx, chat_id, user.id, "mute", None, source="captcha", generation=generation)
    if not muted.primary_completed:
        await challenges.reset(ctx, chat_id, user.id, forget=True)
        return True
    state = await state_of(ctx, chat_id, user.id)
    assert state is not None
    if state.generation != generation:
        return True
    if before_card is not None:
        await before_card()
    t = actions.group_t(ctx, cfg)
    if mode != "button" or (cfg.captcha_rules and cfg.rules):
        kb = await personal_link(ctx, state, t("gg-btn-open-verification"))
        sent = None
        async def banner():
            nonlocal sent
            sent = await ctx.bot.send_message(chat_id, t("gg-captcha-private", user=actions.mention(user.id, user.first_name)), reply_markup=kb)
            return sent if isinstance(sent, Message) and kb is not None else False
        step = await actions.perform("captcha_open", banner) if kb else StepResult("captcha_open", "failed", "state_failed")
        sent = sent if step.completed else None
    else:
        sent = await send_card(ctx, state, chat_id, user)
    if sent is None or not await challenges.attach(ctx, chat_id, user.id, generation, sent):
        await actions.unmute(ctx, chat_id, user.id, source="captcha", generation=generation)
        await challenges.reset(ctx, chat_id, user.id, forget=True)
        return True
    if cfg.captcha_mute_seconds is not None:
        await durable.enqueue(ctx, "verification_release", chat_id, user_id=user.id, generation=generation,
            dedupe_key=f"cap_release:{chat_id}:{user.id}:{generation}", payload={},
            run_at=utcnow()+timedelta(seconds=cfg.captcha_mute_seconds))
    return True


async def issue_request(ctx: BotContext, request, cfg: ChatConfig, contact_deadline) -> None:
    mode = cfg.effective_captcha()
    if mode == "off" or contact_deadline <= utcnow():
        return
    question = captcha_modes.question(mode)
    generation = await challenges.begin(ctx, request.chat.id, request.from_user.id, cfg, mode=mode,
        answer=question.answer, deadline=contact_deadline, contact_id=request.user_chat_id,
        contact_deadline=contact_deadline, prompt=question.to_dict(),
        event_identity=f"request:{request.date.isoformat()}:{request.user_chat_id}")
    if not generation:
        return
    allowed = await authz.internal_authorize(ctx, request.chat.id, frozenset({"invite_users"}))
    if not allowed.allowed:
        await challenges.reset(ctx, request.chat.id, request.from_user.id, forget=True)
        return
    state = await state_of(ctx, request.chat.id, request.from_user.id)
    assert state is not None
    sent = await send_card(ctx, state, request.user_chat_id, request.from_user)
    if sent is None:
        await challenges.reset(ctx, request.chat.id, request.from_user.id, forget=True)
        return
    await challenges.attach(ctx, request.chat.id, request.from_user.id, generation, sent)


async def release_job(ctx: BotContext, job: GuardJob) -> ActionResult:
    svc = ctx.extras["guard"]
    async with svc.member_session(job.chat_id, job.user_id or 0) as (session, _member):
        state = await session.get(GuardChallenge, (ctx.bot_id, job.chat_id, job.user_id))
        if state is None or state.status != "pending" or state.generation != job.generation or state.request_contact_id is not None:
            return result_of(StepResult("verification_release", "skipped", "stale_generation"))
        frozen = ChatConfig.model_validate(state.policy)
        if frozen.captcha_mute_seconds is None or state.created_at + timedelta(seconds=frozen.captcha_mute_seconds) > utcnow():
            return result_of(StepResult("verification_release", "skipped", "deadline_not_reached"))
        allowed = await authz.internal_authorize(ctx, job.chat_id, frozenset({"restrict_members"}))
        if not allowed.allowed:
            return actions.failure("verification_release", allowed.code)
        if not await challenges.persist_claim(ctx, state, "answering", state.attempts):
            return result_of(StepResult("verification_release", "skipped", "already_claimed"))
        await session.refresh(state)
        await durable.dispatched(ctx, job)
        result = await actions.unmute(ctx, job.chat_id, job.user_id or 0, source="captcha", generation=job.generation)
        state.status = "released" if result.primary_completed else "uncertain" if any(
            s.error_code in {"TelegramNetworkError", "TelegramServerError"} for s in result.steps) else "failed"
        # A timer release is not a proof of human verification; do not set member.verified.
        return result


async def complete_unban_job(ctx: BotContext, job: GuardJob) -> ActionResult:
    """Complete only the accepted ban of a known partially failed CAPTCHA kick."""
    svc = ctx.extras["guard"]
    async with svc.member_session(job.chat_id, job.user_id or 0) as (session, _member):
        row = await session.get(GuardRestriction, (ctx.bot_id, job.chat_id, job.user_id, "captcha"))
        state = await session.get(GuardChallenge, (ctx.bot_id, job.chat_id, job.user_id))
        if (row is None or row.generation != job.generation or row.mode != "ban" or row.until is not None or row.state != "applied"
                or state is None or state.generation != job.generation or state.status != "failed"):
            return result_of(StepResult("verification_unban", "skipped", "generation_or_outcome_changed"))
        await durable.dispatched(ctx, job)
        result = await actions.unban(ctx, job.chat_id, job.user_id or 0, source="captcha", generation=job.generation)
        if result.primary_completed:
            state.status = "expired"
        elif any(s.error_code in {"TelegramNetworkError", "TelegramServerError"} for s in result.steps):
            state.status = "uncertain"
            row.state = "uncertain"
        return result


async def refund_job(ctx: BotContext, job: GuardJob) -> ActionResult:
    """Refund only this generation's transient mute when no challenge receipt was attached."""
    svc = ctx.extras["guard"]
    async with svc.member_session(job.chat_id, job.user_id or 0) as (session, _member):
        state = await session.get(GuardChallenge, (ctx.bot_id, job.chat_id, job.user_id))
        if state is None or state.status != "refunding" or state.generation != job.generation:
            return result_of(StepResult("verification_refund", "skipped", "generation_changed"))
        row = await session.get(GuardRestriction, (ctx.bot_id, job.chat_id, job.user_id, "captcha"))
        if row is None or row.generation != job.generation or row.mode != "mute":
            state.status = "cancelled"
            return result_of(StepResult("verification_refund", "skipped", "no_owned_transient_mute"))
        await durable.dispatched(ctx, job)
        result = await actions.unmute(ctx, job.chat_id, job.user_id or 0, source="captcha", generation=job.generation)
        if result.primary_completed:
            state.status = "refunded"
        elif any(s.operation == "unmute" and s.error_code in {"TelegramNetworkError", "TelegramServerError"} for s in result.steps):
            state.status = "uncertain"
            row.state = "uncertain"
        return result


async def answer(ctx: BotContext, query: CallbackQuery, data: GgCb, t) -> None:
    claim = await challenges.answer(ctx, query, data.chat, data.user, data.arg)
    if claim.status == "exempt":
        await query.answer(t("gg-captcha-admin-exempt"), show_alert=True)
        return
    if claim.status in {"progress", "rules"}:
        state = await state_of(ctx, data.chat, data.user)
        if state is None or not isinstance(query.message, Message):
            await query.answer(t("gg-content-unavailable"), show_alert=True)
            return
        if claim.status == "progress":
            msg = query.message
            step = await actions.perform("captcha_progress", lambda: msg.edit_reply_markup(reply_markup=markup(ctx, state)))
            await query.answer("" if step.completed else t("gg-outcome-ancillary"))
        else:
            card = await send_card(ctx, state, state.message_chat_id, query.from_user)
            bound = card is not None and await challenges.move_private(ctx, data.chat, data.user, state.generation, card)
            await query.answer("" if bound else t("gg-outcome-ancillary"))
        return
    if claim.status == "wrong":
        await query.answer(t("gg-captcha-wrong", left=str(claim.left)), show_alert=True)
        return
    if claim.status != "accepted" or claim.result is None:
        if claim.status == "failed" and claim.result is not None and claim.result.primary_completed:
            await query.answer(t("gg-captcha-attempts-exhausted"), show_alert=True)
            return
        await query.answer(t("gg-captcha-not-you") if query.from_user.id != data.user else
            actions.outcome_text(t, claim.result, "") if claim.result is not None else t("gg-review-expired"), show_alert=True)
        return
    if isinstance(query.message, Message):
        msg = query.message
        text = t("gg-join-approved") if state_request(claim.result) else t("gg-captcha-passed", user=actions.mention(data.user, "✅"))
        call = (lambda: msg.edit_text(text)) if msg.text is not None else (lambda: msg.edit_caption(caption=text))
        notice = await actions.perform("captcha_notice", call)
        if not notice.completed:
            await query.answer(t("gg-outcome-ancillary"), show_alert=True)
            return
    await query.answer(t("gg-captcha-ok"))


def state_request(result: ActionResult) -> bool:
    return any(step.operation == "join_request" for step in result.steps)


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_verification_pm")

    @router.message(F.chat.type == "private", CommandStart(deep_link=True), F.text.regexp(r"^/start(?:@\w+)? ggv_[A-Za-z0-9_-]{20,32}$"))
    async def open_verification(message: Message, command: CommandObject, t):
        user = message.from_user
        if user is None or user.is_bot or message.chat.id != user.id:
            return
        try:
            raw = await ctx.redis.get(ctx.keys("captcha_open", (command.args or "")[4:]))
            value = json.loads(raw) if raw else {}
            valid = value.get("bot_id") == ctx.bot_id and value.get("user_id") == user.id and isinstance(value.get("chat_id"), int)
        except (RedisError, ValueError, TypeError):
            valid = False
        state = await state_of(ctx, value["chat_id"], user.id) if valid else None
        allowed = state is not None and state.generation == value.get("generation") and await delivery.current_member(ctx, state.chat_id, user.id)
        sent = await send_card(ctx, state, user.id, user) if allowed and state is not None else None
        if sent is None or state is None or not await challenges.move_private(ctx, state.chat_id, user.id, state.generation, sent):
            await message.answer(t("gg-content-unavailable"))

    return router
