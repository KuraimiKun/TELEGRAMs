"""Explicit Telegram step results shared by commands, protection and jobs."""
from __future__ import annotations

import math
import time
import uuid
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.types import ChatPermissions, Message
from sqlalchemy import or_, select

from bots.groupguard import authz, perms
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.contracts import ActionResult, StepResult, result_of
from bots.groupguard.models import GuardNight, GuardRestriction
from core.db.base import upsert, utcnow
from core.i18n import Translate
from core.log import get_logger
from core.sdk.context import BotContext
from core.ui.text import esc

log = get_logger(__name__)
Origin = Literal["manual", "internal"]
MUTED = ChatPermissions(
    can_send_messages=False, can_send_audios=False, can_send_documents=False, can_send_photos=False,
    can_send_videos=False, can_send_video_notes=False, can_send_voice_notes=False, can_send_polls=False,
    can_send_other_messages=False, can_add_web_page_previews=False, can_react_to_messages=False,
)


def mention(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{esc(name or str(user_id))}</a>'


def group_t(ctx: BotContext, cfg: ChatConfig) -> Translate:
    return ctx.translator.bind(cfg.lang)


async def perform(operation: str, call: Callable[[], Awaitable[Any]], *, acknowledged: bool = False) -> StepResult:
    """Expected API failures are sanitized; cancellation and programming errors propagate."""
    try:
        response = await call()
    except TelegramRetryAfter as e:
        step = StepResult(operation, "failed", "retry_after", e.retry_after)
    except TelegramAPIError as e:
        step = StepResult(operation, "failed", type(e).__name__)
    else:
        step = StepResult(operation, "failed", "api_false") if response is False or response is None else StepResult(
            operation, "acknowledged" if acknowledged else "applied")
    if step.status == "failed":
        log.info("gg_step_failed", operation=operation, code=step.error_code, retry_after=step.retry_after)
    return step


def failure(operation: str, code: str) -> ActionResult:
    log.info("gg_action_denied", operation=operation, code=code)
    return result_of(StepResult(operation, "failed", code))


@dataclass(frozen=True, slots=True)
class PermissionResult:
    permissions: ChatPermissions | None
    step: StepResult


async def default_permissions(ctx: BotContext, chat_id: int) -> PermissionResult:
    try:
        chat = await ctx.bot.get_chat(chat_id)
    except TelegramAPIError as e:
        return PermissionResult(None, StepResult("permissions", "failed", type(e).__name__))
    if chat is None or chat.permissions is None or not any(
            isinstance(value, bool) for value in chat.permissions.model_dump().values()):
        return PermissionResult(None, StepResult("permissions", "failed", "defaults_unknown"))
    return PermissionResult(chat.permissions, StepResult("permissions", "applied"))


def sanction_deadline(duration: timedelta | None, *, absolute: datetime | int | None = None) -> int | None:
    """Integer deadline computed at dispatch. Absolute deadlines need a >30-second safety margin."""
    now = time.time()
    if absolute is not None:
        until = math.ceil(absolute.timestamp()) if isinstance(absolute, datetime) else absolute
        if isinstance(until, bool) or not isinstance(until, int) or not 45 <= until - now <= 365 * 86400 + 1:
            raise ValueError("unsafe_deadline")
        return until
    if duration is None:
        return None
    if not perms.MIN_UNTIL <= duration <= perms.MAX_UNTIL:
        raise ValueError("duration_invalid")
    # Ceiling preserves 1m despite integer conversion; arbitrary network delay remains unprovable.
    return math.ceil(now + duration.total_seconds())


async def punish(ctx: BotContext, chat_id: int, user_id: int, action: str, duration: timedelta | None,
                 *, origin: Origin = "internal", absolute: datetime | int | None = None,
                 source: str | None = None, generation: str | None = None,
                 dispatch_guard: Callable[[], Awaitable[bool]] | None = None) -> ActionResult:
    if action not in {"ban", "mute", "kick"}:
        return failure("sanction", "unknown_action")
    svc = ctx.extras["guard"]
    async with svc.member_session(chat_id, user_id) as (session, _member):
        existing = list((await session.execute(select(GuardRestriction).where(
            GuardRestriction.bot_id == ctx.bot_id, GuardRestriction.chat_id == chat_id,
            GuardRestriction.user_id == user_id,
            or_(GuardRestriction.until.is_(None), GuardRestriction.until > utcnow())))).scalars())
        owner = source or ("manual" if origin == "manual" else "automatic")
        if action == "kick" and any(r.mode == "ban" and r.source != owner for r in existing):
            return failure("kick", "owned_ban_present")
        if action == "mute" and any(r.mode == "ban" for r in existing):
            return failure("mute", "owned_ban_present")
        others = [r for r in existing if r.source != owner and r.mode == action]
        floor = max((r.until for r in others if r.until is not None), default=None)
        permanent = any(r.until is None for r in others)
        dispatch_info: dict[str, int | None] = {}
        generation = generation or uuid.uuid4().hex
        previous = next((r for r in existing if r.source == owner), None)
        previous_values = dict(mode=previous.mode, state=previous.state, generation=previous.generation,
            until=previous.until, updated_at=previous.updated_at) if previous is not None else None
        intent_written = False

        async def persist_intent(requested: int | None) -> None:
            nonlocal intent_written
            # This independent commit precedes the RPC. Cancellation/SQL failure after a real mute
            # must not make verification believe there was no other restriction owner.
            async with ctx.sm() as evidence:
                values = dict(mode="ban" if action == "kick" else action, state="pending", generation=generation,
                    until=datetime.fromtimestamp(requested, UTC) if requested is not None else None, updated_at=utcnow())
                await evidence.execute(upsert(evidence, GuardRestriction).values(bot_id=ctx.bot_id,
                    chat_id=chat_id, user_id=user_id, source=owner, **values).on_conflict_do_update(
                        index_elements=["bot_id", "chat_id", "user_id", "source"], set_=values))
                await evidence.commit()
            intent_written = True

        result = await _punish_api(ctx, chat_id, user_id, action, duration, origin=origin, absolute=absolute,
            floor=floor, permanent_floor=permanent, dispatch_info=dispatch_info, dispatch_hook=persist_intent,
            dispatch_guard=dispatch_guard)
        # A partial kick can leave a real ban; retain that evidence and never release another source.
        applied_mode = action if action != "kick" else "ban" if result.status == "partial" else None
        if (result.primary_completed or result.status == "partial") and applied_mode in {"ban", "mute"}:
            own_until = dispatch_info.get("requested_until")
            until = datetime.fromtimestamp(own_until, UTC) if own_until is not None else None
            await session.execute(upsert(session, GuardRestriction).values(bot_id=ctx.bot_id, chat_id=chat_id,
                user_id=user_id, source=owner, mode=applied_mode, state="applied", generation=generation, until=until,
                updated_at=utcnow()).on_conflict_do_update(index_elements=["bot_id", "chat_id", "user_id", "source"],
                    set_=dict(mode=applied_mode, state="applied", generation=generation, until=until, updated_at=utcnow())))
            if until is not None:
                from bots.groupguard import durable
                identity = f"{chat_id}:{user_id}:{owner}:{generation}"
                import hashlib
                await durable.enqueue(ctx, "restriction_expire", chat_id, user_id=user_id, generation=generation,
                    dedupe_key="restriction:" + hashlib.sha256(identity.encode()).hexdigest(),
                    payload={"source": owner, "mode": applied_mode}, run_at=until, session=session)
        elif intent_written:
            from sqlalchemy import delete, update
            scope = [GuardRestriction.bot_id == ctx.bot_id, GuardRestriction.chat_id == chat_id,
                GuardRestriction.user_id == user_id, GuardRestriction.source == owner,
                GuardRestriction.generation == generation]
            uncertain = any(step.error_code in {"TelegramNetworkError", "TelegramServerError"} for step in result.steps)
            if uncertain:
                await session.execute(update(GuardRestriction).where(*scope).values(state="uncertain"))
            elif previous_values is not None:
                await session.execute(update(GuardRestriction).where(*scope).values(**previous_values))
            else:
                await session.execute(delete(GuardRestriction).where(*scope))
        return result


async def _release(ctx: BotContext, chat_id: int, user_id: int, *, mode: str, origin: Origin,
                   source: str | None, generation: str | None, expiration: bool = False) -> ActionResult:
    svc = ctx.extras["guard"]
    async with svc.member_session(chat_id, user_id) as (session, _member):
        where = [GuardRestriction.bot_id == ctx.bot_id, GuardRestriction.chat_id == chat_id,
                 GuardRestriction.user_id == user_id]
        all_rows = list((await session.execute(select(GuardRestriction).where(*where))).scalars())
        owned = [r for r in all_rows if r.mode == mode and ((source is not None and r.source == source and
            (generation is None or r.generation == generation)) or
            (source is None and r.source in {"manual", "automatic", "warning", "flood", "ai", "cas"}))]
        remaining = [r for r in all_rows if r not in owned and (r.until is None or r.until > utcnow())]
        if expiration and (not owned or any(r.until is None or r.until > utcnow() for r in owned)):
            return result_of(StepResult("restriction_expire", "skipped", "stale_generation"))
        if source is not None and generation is not None and not owned:
            return failure("release", "stale_restriction_generation")
        maintenance = (source == "captcha" or (source or "").startswith("night:")) and ctx.extras.get("owned_maintenance") is True
        if maintenance:
            bot = await perms.fresh_rights(ctx, chat_id, ctx.bot_id)
            capability = authz.Authorization(bot is not None and bot.allows("restrict_members"), "owned_restore_denied")
        else:
            capability = await authz.internal_authorize(ctx, chat_id, frozenset({"restrict_members"}))
        if not capability.allowed:
            return failure("release", capability.code)
        blocking = [row for row in remaining if row.mode == "ban" or mode == "mute"]
        if blocking:
            if source == "captcha" or (source or "").startswith("night:") or expiration:
                for row in owned:
                    await session.delete(row)
                return result_of(StepResult("verification_release", "applied")).with_steps(
                    StepResult("restoration", "skipped", "other_restriction_active"))
            return failure("unmute" if mode == "mute" else "unban", "other_restriction_active")
        if mode == "mute" and not (source or "").startswith("night:"):
            night = await session.get(GuardNight, (ctx.bot_id, chat_id))
            if night is not None and night.status in {"prepared", "dispatched", "closed", "uncertain"}:
                # Completing verification during closure must neither grant send rights now nor leave
                # a permanent individual mute when the group opens. Transfer the owned restoration.
                hold = "night:" + night.generation
                await session.execute(upsert(session, GuardRestriction).values(bot_id=ctx.bot_id,
                    chat_id=chat_id, user_id=user_id, source=hold, mode="mute", generation=night.generation,
                    until=None, updated_at=utcnow()).on_conflict_do_nothing(
                        index_elements=["bot_id", "chat_id", "user_id", "source"]))
                for row in owned:
                    await session.delete(row)
                return result_of(StepResult("verification_release", "applied")).with_steps(
                    StepResult("restoration", "skipped", "night_active"))
        if maintenance and mode == "mute":
            defaults = await default_permissions(ctx, chat_id)
            permissions = defaults.permissions
            if permissions is None:
                result = result_of(defaults.step)
            else:
                result = result_of(await perform("owned_verification_release", lambda: ctx.bot.restrict_chat_member(
                    chat_id, user_id, permissions=permissions))).with_steps(defaults.step)
        else:
            result = await (_unmute_api if mode == "mute" else _unban_api)(ctx, chat_id, user_id, origin=origin)
        if result.primary_completed:
            for row in owned:
                await session.delete(row)
        return result


async def unmute(ctx: BotContext, chat_id: int, user_id: int, *, origin: Origin = "internal",
                 source: str | None = None, generation: str | None = None, expiration: bool = False) -> ActionResult:
    return await _release(ctx, chat_id, user_id, mode="mute", origin=origin, source=source, generation=generation, expiration=expiration)


async def unban(ctx: BotContext, chat_id: int, user_id: int, *, origin: Origin = "internal",
                source: str | None = None, generation: str | None = None, expiration: bool = False) -> ActionResult:
    return await _release(ctx, chat_id, user_id, mode="ban", origin=origin, source=source, generation=generation, expiration=expiration)


async def _punish_api(ctx: BotContext, chat_id: int, user_id: int, action: str, duration: timedelta | None,
                 *, origin: Origin = "internal", absolute: datetime | int | None = None,
                 floor: datetime | None = None, permanent_floor: bool = False,
                 dispatch_info: dict[str, int | None] | None = None,
                 dispatch_hook: Callable[[int | None], Awaitable[None]] | None = None,
                 dispatch_guard: Callable[[], Awaitable[bool]] | None = None) -> ActionResult:
    if action not in {"ban", "mute", "kick"}:
        return failure("sanction", "unknown_action")
    capability = await authz.internal_authorize(ctx, chat_id, frozenset({"restrict_members"}))
    if not capability.allowed:
        return failure(action, capability.code)
    try:
        until = sanction_deadline(duration, absolute=absolute) if action != "kick" else None
        if dispatch_info is not None:
            dispatch_info["requested_until"] = until
        if permanent_floor:
            until = None
        elif until is not None and floor is not None and floor.timestamp() > until:
            until = sanction_deadline(None, absolute=floor)
    except ValueError as e:
        return failure(action, str(e))
    if dispatch_hook is not None:
        await dispatch_hook(dispatch_info.get("requested_until") if dispatch_info is not None else until)
    if dispatch_guard is not None and not await dispatch_guard():
        return failure(action, "policy_changed")
    if action == "mute":
        step = await perform("mute", lambda: ctx.bot.restrict_chat_member(
            chat_id, user_id, permissions=MUTED, until_date=until))
        return replace(result_of(step), until_date=until)
    step = await perform("ban", lambda: ctx.bot.ban_chat_member(chat_id, user_id, until_date=until))
    if action == "ban" or not step.completed:
        return replace(result_of(step), until_date=until)
    restored = await _unban_api(ctx, chat_id, user_id, origin=origin)
    return result_of(step, *restored.steps)


async def _unmute_api(ctx: BotContext, chat_id: int, user_id: int, *, origin: Origin = "internal") -> ActionResult:
    cap = await authz.internal_authorize(ctx, chat_id, frozenset({"restrict_members"}))
    if not cap.allowed:
        return failure("unmute", cap.code)
    defaults = await default_permissions(ctx, chat_id)
    if defaults.permissions is None:
        return result_of(defaults.step)
    permissions = defaults.permissions
    step = await perform("unmute", lambda: ctx.bot.restrict_chat_member(chat_id, user_id,
                                                                       permissions=permissions))
    return result_of(step).with_steps(defaults.step)


async def _unban_api(ctx: BotContext, chat_id: int, user_id: int, *, origin: Origin = "internal") -> ActionResult:
    cap = await authz.internal_authorize(ctx, chat_id, frozenset({"restrict_members"}))
    if not cap.allowed:
        return failure("unban", cap.code)
    return result_of(await perform("unban", lambda: ctx.bot.unban_chat_member(chat_id, user_id, only_if_banned=True)))


async def delete(ctx: BotContext, chat_id: int, message_id: int, *, origin: Origin = "internal") -> ActionResult:
    return await delete_many(ctx, chat_id, [message_id], origin=origin, single=True)


async def delete_many(ctx: BotContext, chat_id: int, message_ids: Sequence[int], *, origin: Origin = "manual",
                      single: bool = False) -> ActionResult:
    ids = tuple(message_ids)
    cap = await authz.internal_authorize(ctx, chat_id, frozenset({"delete_messages"}))
    if not cap.allowed:
        denied = failure("delete", cap.code)
        return ActionResult(denied.status, denied.steps, False, ids)
    steps: list[StepResult] = []
    ack: list[int] = []
    batch_size = 1 if single else 100
    for start in range(0, len(ids), batch_size):
        batch = ids[start:start + batch_size]

        async def call(batch: tuple[int, ...] = batch) -> bool:
            if single:
                return await ctx.bot.delete_message(chat_id, batch[0])
            return await ctx.bot.delete_messages(chat_id, list(batch))

        step = await perform("delete", call, acknowledged=True)
        steps.append(step)
        if step.completed:
            ack.extend(batch)
    result = result_of(*steps)
    return ActionResult(result.status, result.steps, result.primary_completed, ids, tuple(ack), None)


async def notify(ctx: BotContext, chat_id: int, text: str, **kwargs: Any) -> StepResult:
    return await perform("notification", lambda: ctx.bot.send_message(chat_id, text, **kwargs))


async def log_event(ctx: BotContext, cfg: ChatConfig, chat_title: str | None, text: str, *, category: str = "automated") -> StepResult:
    if cfg.log_chat_id is None or category not in cfg.log_categories:
        return StepResult("log", "skipped")
    destination = cfg.log_chat_id
    return await perform("log", lambda: ctx.bot.send_message(destination, f"🛡 <b>{esc(chat_title or '')}</b>\n{text}"))


def outcome_text(t: Translate, result: ActionResult, success: str) -> str:
    if result.primary_completed:
        return success if result.status != "partial" else success + "\n" + t("gg-outcome-ancillary")
    return t("gg-outcome-partial") if result.status == "partial" else t("gg-outcome-failed")


async def announce(ctx: BotContext, cfg: ChatConfig, chat_id: int, title: str | None,
                   result: ActionResult, success: str, *, silent: bool = False, category: str = "automated", **kwargs: Any) -> ActionResult:
    t = group_t(ctx, cfg)
    text = outcome_text(t, result, success)
    sent = None
    if cfg.action_topic is not None and chat_id < 0:
        kwargs["message_thread_id"] = None if cfg.action_topic == 1 else cfg.action_topic
    async def send():
        nonlocal sent
        sent = await ctx.bot.send_message(chat_id,text,**kwargs)
        return sent
    notice = StepResult("notification", "skipped") if silent else await perform("notification",send)
    audit = await log_event(ctx, cfg, title, text, category=category)
    final = result.with_steps(notice, audit)
    if isinstance(sent,Message):
        from bots.groupguard import cleanup
        final = final.with_steps(await cleanup.schedule(ctx,chat_id,sent,"action"))
    elif notice.completed and "action" in cfg.bot_clean_types and chat_id < 0:
        final = final.with_steps(StepResult("bot_clean_schedule","failed","missing_owned_receipt"))
    if result.primary_completed and (notice.status == "failed" or audit.status == "failed") and not silent:
        # A successful sanction stays successful, but ancillary failure is explicitly visible.
        final = final.with_steps(await notify(ctx, chat_id, t("gg-outcome-ancillary")))
    return final
