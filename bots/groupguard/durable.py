"""Scoped durable intents, serialized warning generations, and bounded recovery.

A dispatched expired lease is uncertain, never blindly repeated. Telegram delivery is not exactly once.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bots.groupguard import actions, authz, perms
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.contracts import ActionResult, Actor, StepResult, result_of
from bots.groupguard.models import GuardChat, GuardJob, GuardRestriction, GuardWarn
from bots.groupguard.service import GuardService
from core.db.base import affected, upsert, utcnow
from core.sdk.context import BotContext

MAX_PAYLOAD = 131072
LEASE_SECONDS = 180


class LeaseLost(RuntimeError):
    pass


async def enqueue(ctx: BotContext, kind: str, chat_id: int, *, dedupe_key: str, payload: dict[str, Any],
                  run_at: datetime | None = None, user_id: int | None = None, generation: str | None = None,
                  session: AsyncSession | None = None) -> str:
    if len(json.dumps(payload).encode()) > MAX_PAYLOAD or len(dedupe_key) > 160:
        raise ValueError("job_payload_too_large")
    if session is None:
        async with ctx.sm() as owned:
            jid = await enqueue(ctx, kind, chat_id, dedupe_key=dedupe_key, payload=payload, run_at=run_at,
                                user_id=user_id, generation=generation, session=owned)
            await owned.commit()
            return jid
    jid = uuid.uuid4().hex
    await session.execute(upsert(session, GuardJob).values(id=jid, bot_id=ctx.bot_id, kind=kind,
        chat_id=chat_id, user_id=user_id, dedupe_key=dedupe_key, generation=generation, payload=payload,
        status="pending", run_at=run_at or utcnow(), dispatched=False, attempts=0,
        created_at=utcnow(), updated_at=utcnow()).on_conflict_do_nothing(index_elements=["bot_id", "dedupe_key"]))
    return str((await session.execute(select(GuardJob.id).where(
        GuardJob.bot_id == ctx.bot_id, GuardJob.dedupe_key == dedupe_key))).scalar_one())


async def claim(ctx: BotContext, job_id: str) -> GuardJob | None:
    async with ctx.sm() as session:
        job = (await session.execute(select(GuardJob).where(GuardJob.id == job_id,
            GuardJob.bot_id == ctx.bot_id, GuardJob.status == "pending", GuardJob.run_at <= utcnow())
            .with_for_update(skip_locked=True))).scalar_one_or_none()
        if job is None:
            return None
        # Conditional UPDATE also fences SQLite tests where FOR UPDATE is unavailable.
        owner = uuid.uuid4().hex
        changed = await session.execute(update(GuardJob).where(GuardJob.id == job.id,
            GuardJob.bot_id == ctx.bot_id, GuardJob.status == "pending").values(status="running",
            lease_owner=owner, lease_until=utcnow() + timedelta(seconds=LEASE_SECONDS), dispatched=False,
            attempts=GuardJob.attempts + 1, updated_at=utcnow()))
        if affected(changed) != 1:
            await session.rollback()
            return None
        await session.commit()
        await session.refresh(job)
        return job


async def dispatched(ctx: BotContext, job: GuardJob) -> None:
    if not await authz.active_namespace(ctx):
        raise LeaseLost("namespace_inactive")
    async with ctx.sm() as session:
        changed = await session.execute(update(GuardJob).where(GuardJob.id == job.id,
            GuardJob.bot_id == ctx.bot_id, GuardJob.status == "running", GuardJob.lease_owner == job.lease_owner,
            GuardJob.lease_until > utcnow()).values(dispatched=True, updated_at=utcnow()))
        if affected(changed) != 1:
            raise LeaseLost("job_lease_lost")
        await session.commit()


async def finish(ctx: BotContext, job: GuardJob, result: ActionResult, *, session: AsyncSession | None = None) -> bool:
    if session is None:
        async with ctx.sm() as owned:
            done = await finish(ctx, job, result, session=owned)
            await owned.commit()
            return done
    failures = [s for s in result.steps if s.status == "failed"]
    code = failures[0].error_code if failures else None
    uncertain = code in {"TelegramNetworkError", "TelegramServerError"}
    retry = next((s.retry_after for s in failures if s.retry_after is not None), None)
    status = "succeeded" if result.primary_completed else "cancelled" if result.status == "noop" else "uncertain" if uncertain else "failed"
    if retry is not None and job.attempts < 5:
        status = "pending"
    values: dict[str, Any] = dict(status=status, error_code=code, lease_until=None, updated_at=utcnow())
    if status == "pending":
        values.update(run_at=utcnow() + timedelta(seconds=min(max(retry or 1, 1), 3600)), dispatched=False)
    changed = await session.execute(update(GuardJob).where(GuardJob.id == job.id,
        GuardJob.bot_id == ctx.bot_id, GuardJob.lease_owner == job.lease_owner,
        GuardJob.status.in_({"running", "uncertain"})).values(**values))
    return affected(changed) == 1


async def defer(ctx: BotContext,job: GuardJob,seconds: int,code: str="local_rate") -> None:
    """No RPC was attempted; keep local quota waits outside the API retry budget."""
    async with ctx.sm() as session:
        await session.execute(update(GuardJob).where(GuardJob.bot_id==ctx.bot_id,GuardJob.id==job.id,
            GuardJob.status=="running",GuardJob.lease_owner==job.lease_owner,GuardJob.dispatched.is_(False)).values(
                status="pending",attempts=max(job.attempts-1,0),run_at=utcnow()+timedelta(seconds=min(max(seconds,1),3600)),
                lease_until=None,error_code=code,updated_at=utcnow()))
        await session.commit()


async def recover(ctx: BotContext, limit: int = 100) -> int:
    async with ctx.sm() as session:
        interrupted = list((await session.execute(select(GuardRestriction).where(
            GuardRestriction.bot_id == ctx.bot_id, GuardRestriction.state == "pending",
            GuardRestriction.updated_at < utcnow() - timedelta(seconds=240)).order_by(GuardRestriction.updated_at)
            .limit(limit).with_for_update(skip_locked=True))).scalars())
        for row in interrupted:
            row.state = "uncertain"
        jobs = list((await session.execute(select(GuardJob).where(GuardJob.bot_id == ctx.bot_id,
            GuardJob.status == "running", GuardJob.lease_until < utcnow()).order_by(GuardJob.lease_until)
            .limit(limit).with_for_update(skip_locked=True))).scalars())
        for job in jobs:
            job.status = "uncertain" if job.dispatched else "pending"
            job.error_code = "interrupted_external_call" if job.dispatched else "interrupted_before_dispatch"
            job.run_at = utcnow()
            job.lease_until = None
        await session.commit()
        return len(jobs)


async def cancel(ctx: BotContext, *, chat_id: int | None = None, kind: str | None = None,
                 generation: str | None = None) -> int:
    where = [GuardJob.bot_id == ctx.bot_id, GuardJob.status.in_({"pending", "running"}), GuardJob.dispatched.is_(False)]
    if chat_id is not None:
        where.append(GuardJob.chat_id == chat_id)
    if kind is not None:
        where.append(GuardJob.kind == kind)
    if generation is not None:
        where.append(GuardJob.generation == generation)
    async with ctx.sm() as session:
        result = await session.execute(update(GuardJob).where(*where).values(status="cancelled", updated_at=utcnow()))
        await session.commit()
        return affected(result)


@dataclass(frozen=True, slots=True)
class WarningDecision:
    warning_id: int
    count: int
    job_id: str | None


def live_warns(ctx: BotContext, chat_id: int, user_id: int):
    return (GuardWarn.bot_id == ctx.bot_id, GuardWarn.chat_id == chat_id, GuardWarn.user_id == user_id,
            or_(GuardWarn.expires_at.is_(None), GuardWarn.expires_at > utcnow()))


async def record_warning(ctx: BotContext, chat_id: int, user_id: int, reason: str | None, by_id: int | None,
                         *, limit: int, action: str, duration_seconds: int | None, name: str,
                         expires_at: datetime | None = None, silent: bool = False, assumed_anonymous: bool = False,
                         current_expiry_policy: bool = False) -> WarningDecision:
    svc: GuardService = ctx.extras["guard"]
    if current_expiry_policy:
        await svc.ensure_chat(chat_id)
    async with svc.member_session(chat_id, user_id) as (session, member):
        if current_expiry_policy:
            # Serialize policy capture with the configuration CAS transaction (including expiry-off).
            payload = (await session.execute(select(GuardChat.config).where(GuardChat.bot_id == ctx.bot_id,
                GuardChat.chat_id == chat_id).with_for_update())).scalar_one_or_none()
            cfg = ChatConfig.model_validate(payload or {})
            expires_at = utcnow() + timedelta(seconds=cfg.warn_time_seconds) if cfg.warn_time_seconds else None
            limit, action, duration_seconds = cfg.warn_limit, cfg.warn_action, cfg.effective_warning_duration()
        warn = GuardWarn(bot_id=ctx.bot_id, chat_id=chat_id, user_id=user_id, reason=reason,
                         by_id=by_id, expires_at=expires_at, created_at=utcnow())
        session.add(warn)
        await session.flush()
        count = int((await session.execute(select(func.count()).select_from(GuardWarn).where(
            *live_warns(ctx, chat_id, user_id)))).scalar_one())
        job = None
        if count >= limit and member.warning_job is None:
            member.warning_generation += 1
            job = await enqueue(ctx, "warning_sanction", chat_id, user_id=user_id,
                generation=str(member.warning_generation), dedupe_key=f"warn:{chat_id}:{user_id}:{member.warning_generation}",
                payload=dict(cutoff=warn.id, limit=limit, action=action, duration_seconds=duration_seconds,
                             name=name, by_id=by_id, silent=silent, assumed_anonymous=assumed_anonymous), session=session)
            member.warning_job = job
        if expires_at is not None:
            await enqueue(ctx, "warning_expire", chat_id, user_id=user_id, dedupe_key=f"warn_expire:{warn.id}",
                          payload=dict(warning_id=warn.id), run_at=expires_at, session=session)
        return WarningDecision(warn.id, count, job)


async def execute_warning(ctx: BotContext, job_id: str) -> ActionResult | None:
    job = await claim(ctx, job_id)
    if job is None:
        return None
    return await _warning(ctx, job)


async def _warning(ctx: BotContext, job: GuardJob) -> ActionResult:
    svc: GuardService = ctx.extras["guard"]
    cfg = await svc.config(job.chat_id, fresh=True)
    user_id = job.user_id or 0
    by_id = job.payload.get("by_id")
    async with svc.member_session(job.chat_id, user_id) as (session, member):
        count = int((await session.execute(select(func.count()).select_from(GuardWarn).where(
            *live_warns(ctx, job.chat_id, user_id), GuardWarn.id <= int(job.payload["cutoff"])))).scalar_one())
        if job.payload.get("assumed_anonymous") and not cfg.anonadmin:
            result = actions.failure("warning_sanction", "assumption_revoked")
        elif member.warning_job != job.id or count < int(job.payload["limit"]):
            result = actions.failure("warning_sanction", "threshold_cancelled")
        elif (target_error := await perms.target_error(ctx, job.chat_id, user_id)) is not None:
            result = actions.failure("warning_sanction", target_error)
        else:
            authorized = (await authz.authorize(ctx, Actor(ctx.bot_id, job.chat_id, "human", int(by_id)),
                target_chat_id=job.chat_id, caller_rights=frozenset({"restrict_members"}),
                bot_rights=frozenset({"restrict_members"}))) if by_id is not None else await authz.internal_authorize(
                ctx, job.chat_id, frozenset({"restrict_members"}))
            if not authorized.allowed:
                result = actions.failure("warning_sanction", authorized.code)
            else:
                try:
                    await dispatched(ctx, job)
                except LeaseLost:
                    result = actions.failure("warning_sanction", "lease_lost")
                else:
                    duration = job.payload.get("duration_seconds")
                    result = await actions.punish(ctx, job.chat_id, user_id, str(job.payload["action"]),
                        timedelta(seconds=duration) if duration is not None else None,
                        origin="manual" if by_id is not None else "internal", source="warning", generation=job.generation)
        if await finish(ctx, job, result, session=session):
            if result.primary_completed:
                await session.execute(delete(GuardWarn).where(*svc._warns(job.chat_id, user_id),
                                                               GuardWarn.id <= int(job.payload["cutoff"])))
            # Pending retry/uncertain intents retain ownership; known failures may be attempted by a new warning.
            failures = [s for s in result.steps if s.status == "failed"]
            retained = any(s.retry_after is not None or s.error_code in {"TelegramNetworkError", "TelegramServerError"}
                           for s in failures)
            if not retained and member.warning_job == job.id:
                member.warning_job = None
        else:
            result = result.with_steps(StepResult("warning_state", "failed", "lease_lost"))
    t = actions.group_t(ctx, cfg)
    text = t(f"gg-warn-limit-{job.payload['action']}", user=actions.mention(user_id, str(job.payload["name"])),
             limit=str(job.payload["limit"]))
    return await actions.announce(ctx, cfg, job.chat_id, await svc.title(job.chat_id), result, text,
                                  silent=bool(job.payload.get("silent")), category="admin" if by_id is not None else "automated")


async def warning_expire(ctx: BotContext, job: GuardJob) -> ActionResult:
    svc: GuardService = ctx.extras["guard"]
    async with svc.member_session(job.chat_id, job.user_id or 0) as (session, _member):
        await session.execute(delete(GuardWarn).where(GuardWarn.bot_id == ctx.bot_id,
            GuardWarn.chat_id == job.chat_id, GuardWarn.user_id == job.user_id,
            GuardWarn.id == int(job.payload["warning_id"]), GuardWarn.expires_at <= utcnow()))
        result = result_of(StepResult("warning_expire", "applied"))
        await finish(ctx, job, result, session=session)
        return result


async def sweep(ctx: BotContext, limit: int = 100) -> int:
    await recover(ctx, limit)
    async with ctx.sm() as session:
        ids = list((await session.execute(select(GuardJob.id).where(GuardJob.bot_id == ctx.bot_id,
            GuardJob.status == "pending", GuardJob.run_at <= utcnow()).order_by(GuardJob.run_at).limit(limit))).scalars())
    completed = 0
    for jid in ids:
        job = await claim(ctx, jid)
        if job is None:
            continue
        if job.kind == "warning_sanction":
            result = await _warning(ctx, job)
        elif job.kind == "warning_expire":
            result = await warning_expire(ctx, job)
        elif job.kind == "restriction_expire":
            release = actions.unmute if job.payload["mode"] == "mute" else actions.unban
            await dispatched(ctx, job)
            result = await release(ctx, job.chat_id, job.user_id or 0, source=job.payload["source"],
                                   generation=job.generation, expiration=True)
            await finish(ctx, job, result)
        elif job.kind == "captcha_expire":
            from bots.groupguard.challenges import expire
            result = await expire(ctx, job.chat_id, job.user_id or 0, job.generation or "", job=job)
            await finish(ctx, job, result)
        else:
            handler = ctx.extras.get("guard_job_handlers", {}).get(job.kind)
            if handler is None:
                result = actions.failure("job", "unknown_job_kind")
            else:
                result = await handler(ctx, job)
            await finish(ctx, job, result)
        completed += int(result.primary_completed)
    return completed
