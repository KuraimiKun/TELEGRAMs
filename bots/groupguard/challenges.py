"""Issued SQL CAPTCHA generations: scoped callbacks, answer/timeout claims, and owned release."""
from __future__ import annotations

import secrets
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from aiogram.types import CallbackQuery, Message
from sqlalchemy import delete, or_, select, update

from bots.groupguard import actions, authz, durable, perms
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.contracts import ActionResult, Right, StepResult, result_of
from bots.groupguard.models import GuardChallenge, GuardJob, GuardRestriction
from bots.groupguard.service import GuardService
from core.db.base import affected, upsert, utcnow
from core.sdk.context import BotContext


@dataclass(frozen=True, slots=True)
class AnswerClaim:
    status: str
    generation: str = ""
    left: int = 0
    result: ActionResult | None = None


async def begin(ctx: BotContext, chat_id: int, user_id: int, cfg: ChatConfig, *, mode: str,
                answer: str, deadline: datetime, contact_id: int | None = None,
                contact_deadline: datetime | None = None, prompt: dict | None = None,
                event_identity: str | None = None) -> str:
    generation = secrets.token_hex(8)
    svc: GuardService = ctx.extras["guard"]
    async with svc.member_session(chat_id, user_id) as (session, member):
        previous = await session.get(GuardChallenge, (ctx.bot_id, chat_id, user_id))
        if (event_identity is not None and previous is not None and previous.status in {"issuing", "pending"}
                and previous.prompt.get("event_identity") == event_identity):
            return ""
        if previous is not None:
            await session.execute(update(GuardJob).where(GuardJob.bot_id == ctx.bot_id,
                GuardJob.kind == "captcha_expire", GuardJob.generation == previous.generation,
                GuardJob.dispatched.is_(False)).values(status="cancelled", updated_at=utcnow()))
        values = dict(generation=generation, status="issuing", message_id=0,
            message_chat_id=contact_id or chat_id, thread_id=None, mode=mode, answer=answer, attempts=0,
            deadline=deadline, policy=cfg.model_dump(), request_contact_id=contact_id,
            contact_deadline=contact_deadline, created_at=utcnow(), prompt={**(prompt or {}), "event_identity": event_identity},
            progress="", question_solved=False, rules_accepted=False)
        await session.execute(upsert(session, GuardChallenge).values(bot_id=ctx.bot_id, chat_id=chat_id,
            user_id=user_id, **values).on_conflict_do_update(index_elements=["bot_id", "chat_id", "user_id"], set_=values))
        member.verified = False
    return generation


async def attach(ctx: BotContext, chat_id: int, user_id: int, generation: str, sent: Message) -> bool:
    svc: GuardService = ctx.extras["guard"]
    async with svc.member_session(chat_id, user_id) as (session, _member):
        state = await session.get(GuardChallenge, (ctx.bot_id, chat_id, user_id))
        if state is None or state.generation != generation or state.status != "issuing" or sent.chat.id != state.message_chat_id:
            return False
        state.message_id, state.thread_id, state.status = sent.message_id, sent.message_thread_id, "pending"
        await durable.enqueue(ctx, "captcha_expire", chat_id, user_id=user_id, generation=generation,
            dedupe_key=f"captcha:{chat_id}:{user_id}:{generation}", payload={}, run_at=state.deadline, session=session)
        return True


async def move_private(ctx: BotContext, chat_id: int, user_id: int, generation: str, sent: Message) -> bool:
    """Bind an actual PM receipt to this pending generation, invalidating the older card."""
    svc: GuardService = ctx.extras["guard"]
    async with svc.member_session(chat_id, user_id) as (session, _member):
        state = await session.get(GuardChallenge, (ctx.bot_id, chat_id, user_id))
        if (state is None or state.status != "pending" or state.generation != generation or state.deadline <= utcnow()
                or (state.contact_deadline is not None and state.contact_deadline <= utcnow())
                or sent.from_user is None or sent.from_user.id != ctx.bot_id
                or sent.chat.id != (state.request_contact_id or user_id)):
            return False
        state.message_chat_id, state.message_id, state.thread_id = sent.chat.id, sent.message_id, sent.message_thread_id
        return True


async def verified(ctx: BotContext, chat_id: int, user_id: int) -> bool:
    svc: GuardService = ctx.extras["guard"]
    async with svc.sm() as session:
        from bots.groupguard.models import GuardMember
        member = await session.get(GuardMember, (ctx.bot_id, chat_id, user_id))
        return member is not None and member.verified


async def reset(ctx: BotContext, chat_id: int, user_id: int, *, forget: bool) -> None:
    svc: GuardService = ctx.extras["guard"]
    async with svc.member_session(chat_id, user_id) as (session, member):
        if forget:
            member.verified = False
        state = await session.get(GuardChallenge, (ctx.bot_id, chat_id, user_id))
        if state is not None and state.status in {"issuing", "pending"}:
            state.status = "cancelled"
            await session.execute(update(GuardJob).where(GuardJob.bot_id == ctx.bot_id,
                GuardJob.kind == "captcha_expire", GuardJob.generation == state.generation,
                GuardJob.dispatched.is_(False)).values(status="cancelled"))


def _scoped(ctx: BotContext, query: CallbackQuery, state: GuardChallenge, generation: str) -> bool:
    msg = query.message
    return (not query.from_user.is_bot and query.from_user.id == state.user_id and isinstance(msg, Message)
        and msg.from_user is not None and msg.from_user.id == ctx.bot_id and generation == state.generation
        and msg.message_id == state.message_id and msg.chat.id == state.message_chat_id
        and msg.message_thread_id == state.thread_id)


async def persist_claim(ctx: BotContext, state: GuardChallenge, status: str, attempts: int) -> bool:
    # This commit precedes the external effect. A crash cannot turn an answered generation back into pending.
    async with ctx.sm() as session:
        changed = await session.execute(update(GuardChallenge).where(GuardChallenge.bot_id == ctx.bot_id,
            GuardChallenge.chat_id == state.chat_id, GuardChallenge.user_id == state.user_id,
            GuardChallenge.generation == state.generation, GuardChallenge.status == "pending").values(
                status=status, attempts=attempts, claim_at=utcnow()))
        await session.commit()
        return affected(changed) == 1


async def answer(ctx: BotContext, query: CallbackQuery, chat_id: int, user_id: int, arg: str) -> AnswerClaim:
    generation, separator, value = arg.partition(".")
    if not separator:
        return AnswerClaim("stale")
    svc: GuardService = ctx.extras["guard"]
    async with ctx.sm() as initial:
        snapshot = await initial.get(GuardChallenge, (ctx.bot_id, chat_id, user_id))
    if snapshot is None or snapshot.status != "pending" or not _scoped(ctx, query, snapshot, generation):
        return AnswerClaim("stale")
    delete_prompt: int | None = None
    async with svc.member_session(chat_id, user_id) as (session, member):
        state = await session.get(GuardChallenge, (ctx.bot_id, chat_id, user_id))
        if state is None or state.status != "pending" or not _scoped(ctx, query, state, generation):
            return AnswerClaim("stale")
        if state.deadline <= utcnow() or (state.contact_deadline is not None and state.contact_deadline <= utcnow()):
            return AnswerClaim("expired")
        preflight: frozenset[Right] = frozenset({"invite_users"}) if state.request_contact_id is not None else frozenset({"restrict_members"})
        initial_cap = await authz.internal_authorize(ctx, chat_id, preflight)
        if not initial_cap.allowed:
            return AnswerClaim("failed", result=actions.failure("captcha", initial_cap.code))
        current = await perms.fresh_member(ctx, chat_id, user_id) if state.request_contact_id is None else None
        if state.request_contact_id is None and (current is None or current.status in {"left", "kicked"} or (
                current.status == "restricted" and not getattr(current, "is_member", False))):
            return AnswerClaim("failed", generation, result=actions.failure("captcha", "target_not_member"))
        if state.request_contact_id is not None:
            owned_ban = (await session.execute(select(GuardRestriction).where(GuardRestriction.bot_id == ctx.bot_id,
                GuardRestriction.chat_id == chat_id, GuardRestriction.user_id == user_id, GuardRestriction.mode == "ban",
                or_(GuardRestriction.until.is_(None), GuardRestriction.until > utcnow())).limit(1))).scalar_one_or_none()
            if owned_ban is not None:
                return AnswerClaim("failed", generation, result=actions.failure("join_request", "other_restriction_active"))
        frozen = ChatConfig.model_validate(state.policy)
        if state.prompt.get("mode") in {"button", "text", "text2", "math"}:
            if value == "r.ok":
                if not state.question_solved or not frozen.captcha_rules or not frozen.rules:
                    return AnswerClaim("stale")
                state.rules_accepted = True
                correct = True
            elif state.question_solved:
                if frozen.captcha_rules and frozen.rules and not state.rules_accepted:
                    return AnswerClaim("rules", generation)
                correct = True  # Prior successful question proof survives a known failed release.
            else:
                sequence, dot, choice = value.partition(".")
                expected_sequence = len(state.progress) if state.mode == "text2" else 0
                if (not dot or sequence != str(expected_sequence) or len(choice) != 1 or not choice.isdigit()
                        or int(choice) >= len(state.prompt.get("choices", []))):
                    return AnswerClaim("stale")
                expected = state.answer[expected_sequence] if state.mode == "text2" else state.answer
                correct = secrets.compare_digest(choice, expected)
                if correct and state.mode == "text2":
                    state.progress += choice
                    if len(state.progress) < len(state.answer):
                        return AnswerClaim("progress", generation)
                if correct:
                    state.question_solved = True
                    if frozen.captcha_rules and frozen.rules and not state.rules_accepted:
                        return AnswerClaim("rules", generation)
        else:
            # Already issued legacy button/math generations retain their original answer contract.
            correct = secrets.compare_digest(value, state.answer)
        if not correct and current is not None and perms.member_rights(current).is_admin:
            await session.execute(delete(GuardRestriction).where(GuardRestriction.bot_id == ctx.bot_id,
                GuardRestriction.chat_id == chat_id, GuardRestriction.user_id == user_id,
                GuardRestriction.source == "captcha", GuardRestriction.mode == "mute", GuardRestriction.generation == generation))
            state.status = "cancelled"
            return AnswerClaim("exempt", generation, result=result_of(StepResult("verification_release", "applied")))
        required: frozenset[Right] = frozenset({"invite_users"}) if state.request_contact_id is not None else frozenset({"restrict_members"})
        if not correct and state.attempts + 1 >= 3 and state.request_contact_id is None and state.message_chat_id == chat_id:
            required = frozenset({"restrict_members", "delete_messages"})
        cap = await authz.internal_authorize(ctx, chat_id, required)
        if not cap.allowed:
            return AnswerClaim("failed", result=actions.failure("captcha", cap.code))
        attempts = state.attempts + (0 if correct else 1)
        if not correct and attempts < 3:
            state.attempts = attempts
            return AnswerClaim("wrong", generation, 3 - attempts)
        if not await persist_claim(ctx, state, "answering" if correct else "expiring", attempts):
            return AnswerClaim("stale")
        await session.refresh(state)
        if state.deadline <= utcnow() or (state.contact_deadline is not None and state.contact_deadline <= utcnow()):
            state.status = "pending"  # The owning expiry job, rather than this late answer, decides the timeout action.
            return AnswerClaim("expired", generation)
        from bots.groupguard import fed_enforcement
        if correct and await fed_enforcement.is_banned(ctx, chat_id, user_id, session):
            state.status = "cancelled"
            result = actions.failure("join_verification", "federation_active")
            if state.request_contact_id is not None:
                result = result.with_steps(await actions.perform("fed_request_decline",
                    lambda: ctx.bot.decline_chat_join_request(chat_id, user_id)))
            return AnswerClaim("failed", generation, result=result)
        if state.request_contact_id is not None:
            if not correct:
                state.status = "failed"
                return AnswerClaim("failed", generation, result=actions.failure("join_verification", "attempt_limit"))
            from bots.groupguard import raids
            if raids.active(await raids.state(ctx, chat_id)) and not await raids.protected(ctx, chat_id, user_id):
                result = await raids.decline(ctx, chat_id, user_id, state.request_contact_id,
                                            (state.contact_deadline or state.created_at) - timedelta(minutes=5))
                state.status = "cancelled"
                return AnswerClaim("failed", generation, result=result.with_steps(StepResult("join_verification", "failed", "raid_active")))
            result = result_of(await actions.perform("join_request", lambda: ctx.bot.approve_chat_join_request(chat_id, user_id)))
        elif correct:
            if current is not None and perms.member_rights(current).is_admin:
                await session.execute(delete(GuardRestriction).where(GuardRestriction.bot_id == ctx.bot_id,
                    GuardRestriction.chat_id == chat_id, GuardRestriction.user_id == user_id,
                    GuardRestriction.source == "captcha", GuardRestriction.generation == generation))
                result = result_of(StepResult("verification_release", "applied"))
            else:
                result = await actions.unmute(ctx, chat_id, user_id, source="captcha", generation=generation)
        else:
            # Three failed answers are an actual temporary owned ban (one-hour local policy).
            result = await actions.punish(ctx, chat_id, user_id, "ban", timedelta(hours=1), source="captcha", generation=generation)
            if state.message_chat_id == chat_id:
                delete_prompt = state.message_id
        mutations = {"ban", "unban", "mute", "unmute", "join_request", "join_decline"}
        uncertain = any(s.operation in mutations and s.error_code in {"TelegramNetworkError", "TelegramServerError"} for s in result.steps)
        retryable = correct and not result.primary_completed and not uncertain and not any(
            s.operation in mutations and s.completed for s in result.steps)
        state.status = "solved" if correct and result.primary_completed else "uncertain" if uncertain else "pending" if retryable else "failed"
        if correct and result.primary_completed:
            member.verified = True
        if state.status != "pending":
            await session.execute(update(GuardJob).where(GuardJob.bot_id == ctx.bot_id,
                GuardJob.kind.in_({"captcha_expire", "verification_release"}), GuardJob.generation == generation,
                GuardJob.dispatched.is_(False)).values(status="cancelled"))
        claim = AnswerClaim("accepted" if correct and result.primary_completed else "failed", generation, result=result)
    if delete_prompt is not None:
        deleted = await actions.delete(ctx, chat_id, delete_prompt)
        claim = replace(claim, result=result.with_steps(*deleted.steps))
    return claim


async def expire(ctx: BotContext, chat_id: int, user_id: int, generation: str, *, job: GuardJob | None = None,
                 force: bool = False) -> ActionResult:
    svc: GuardService = ctx.extras["guard"]
    delete_prompt: int | None = None
    async with svc.member_session(chat_id, user_id) as (session, _member):
        state = await session.get(GuardChallenge, (ctx.bot_id, chat_id, user_id))
        if state is None or state.generation != generation or state.status != "pending" or (not force and state.deadline > utcnow()):
            return result_of(StepResult("captcha_expire", "skipped", "stale_generation"))
        if state.request_contact_id is not None:
            # Expired contact/request is never approved. Decline is idempotent and scoped.
            cap = await authz.internal_authorize(ctx, chat_id, frozenset({"invite_users"}))
        else:
            required: set[Right] = {"restrict_members"}
            if state.message_chat_id == chat_id:
                required.add("delete_messages")
            cap = await authz.internal_authorize(ctx, chat_id, frozenset(required))
        if not cap.allowed:
            return actions.failure("captcha_expire", cap.code)
        current = await perms.fresh_member(ctx, chat_id, user_id)
        if current is None:
            return actions.failure("captcha_expire", "target_lookup_failed")
        if perms.member_rights(current).is_admin:
            await session.execute(delete(GuardRestriction).where(GuardRestriction.bot_id == ctx.bot_id,
                GuardRestriction.chat_id == chat_id, GuardRestriction.user_id == user_id,
                GuardRestriction.source == "captcha", GuardRestriction.mode == "mute", GuardRestriction.generation == generation))
            state.status = "cancelled"
            return result_of(StepResult("captcha_expire", "skipped", "target_now_admin"))
        if job is not None:
            try:
                await durable.dispatched(ctx, job)
            except durable.LeaseLost:
                return actions.failure("captcha_expire", "lease_lost")
        if not await persist_claim(ctx, state, "expiring", state.attempts):
            return result_of(StepResult("captcha_expire", "skipped", "already_claimed"))
        await session.refresh(state)
        if state.request_contact_id is not None:
            result = result_of(await actions.perform("join_decline", lambda: ctx.bot.decline_chat_join_request(chat_id, user_id)))
        else:
            frozen = ChatConfig.model_validate(state.policy)
            if frozen.captcha_kick:
                result = await actions.punish(ctx, chat_id, user_id, "kick", None, source="captcha", generation=generation)
            else:
                result = result_of(StepResult("captcha_expire", "applied"))  # Own mute intentionally remains.
            if state.message_chat_id == chat_id:
                delete_prompt = state.message_id
        state.status = "expired" if result.primary_completed else "uncertain" if any(
            s.error_code in {"TelegramNetworkError", "TelegramServerError"} for s in result.steps) else "failed"
        ban_done = any(s.operation == "ban" and s.completed for s in result.steps)
        unban_failed = any(s.operation == "unban" and s.status == "failed" for s in result.steps)
        if state.status == "failed" and ban_done and unban_failed:
            retry = next((s.retry_after for s in result.steps if s.retry_after is not None), 60)
            await durable.enqueue(ctx, "verification_unban", chat_id, user_id=user_id, generation=generation,
                dedupe_key=f"cap_unban:{chat_id}:{user_id}:{generation}", payload={},
                run_at=utcnow()+timedelta(seconds=min(max(retry, 1), 3600)), session=session)
        elif state.status == "failed" and job is not None and job.attempts < 5 and not ban_done and any(
                s.retry_after is not None for s in result.steps):
            state.status = "pending"  # Known rejected request, no punitive mutation was accepted.
    if delete_prompt is not None:
        deleted = await actions.delete(ctx, chat_id, delete_prompt)
        result = result.with_steps(*deleted.steps)
    return result


async def recover_claims(ctx: BotContext, limit: int = 100) -> int:
    async with ctx.sm() as session:
        rows = list((await session.execute(select(GuardChallenge).where(GuardChallenge.bot_id == ctx.bot_id,
            GuardChallenge.status.in_({"answering", "expiring"}),
            GuardChallenge.claim_at < utcnow() - timedelta(seconds=240)).order_by(GuardChallenge.claim_at)
            .limit(limit).with_for_update(skip_locked=True))).scalars())
        for row in rows:
            row.status = "uncertain"
        abandoned = list((await session.execute(select(GuardChallenge).where(GuardChallenge.bot_id == ctx.bot_id,
            GuardChallenge.status == "issuing", GuardChallenge.created_at < utcnow()-timedelta(seconds=240))
            .order_by(GuardChallenge.created_at).limit(limit).with_for_update(skip_locked=True))).scalars())
        for row in abandoned:
            row.status = "refunding" if row.request_contact_id is None else "cancelled"
            if row.request_contact_id is None:
                await durable.enqueue(ctx, "verification_refund", row.chat_id, user_id=row.user_id, generation=row.generation,
                    dedupe_key=f"cap_refund:{row.chat_id}:{row.user_id}:{row.generation}", payload={}, session=session)
        await session.commit()
        return len(rows)+len(abandoned)
