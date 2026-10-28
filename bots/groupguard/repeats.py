"""SQL note cadence, fenced by content generation and current author authority."""
from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bots.groupguard import actions, authz, delivery, durable, perms
from bots.groupguard.contracts import ActionResult, Actor, StepResult, result_of
from bots.groupguard.models import GuardItem, GuardJob, GuardNight, GuardRepeat
from core.db.base import utcnow
from core.sdk.context import BotContext


async def replace(ctx: BotContext, session: AsyncSession, item: GuardItem, *, author_id: int | None,
                  seconds: int | None, thread_id: int | None) -> None:
    old = await session.get(GuardRepeat, (ctx.bot_id, item.chat_id, item.id))
    if old is not None:
        await session.execute(update(GuardJob).where(GuardJob.bot_id == ctx.bot_id,
            GuardJob.kind == "repeat_note", GuardJob.generation == old.generation,
            GuardJob.dispatched.is_(False), GuardJob.status.in_({"pending", "running"})).values(status="cancelled"))
        await session.delete(old)
        await session.flush()
    if seconds is not None:
        if author_id is None or not 60 <= seconds <= 30 * 86400:
            raise ValueError("repeat_author_or_duration_invalid")
        session.add(GuardRepeat(bot_id=ctx.bot_id, chat_id=item.chat_id, item_id=item.id,
            generation=uuid.uuid4().hex, author_id=author_id, interval_seconds=seconds,
            next_run=utcnow() + timedelta(seconds=seconds), status="active", thread_id=thread_id))


async def tick(ctx: BotContext, limit: int = 100) -> None:
    if not await authz.active_namespace(ctx):
        return
    await durable.recover(ctx, limit)
    async with ctx.sm() as session:
        due = list((await session.execute(select(GuardRepeat).where(GuardRepeat.bot_id == ctx.bot_id,
            GuardRepeat.status == "active", GuardRepeat.next_run <= utcnow())
            .order_by(GuardRepeat.next_run, GuardRepeat.chat_id, GuardRepeat.item_id).limit(limit))).scalars())
    for row in due:
        async with ctx.extras["guard"].member_session(row.chat_id, 0) as (session, _member):
            state = await session.get(GuardRepeat, (ctx.bot_id, row.chat_id, row.item_id), populate_existing=True)
            if state is None or state.generation != row.generation or state.status != "active" or state.next_run > utcnow():
                continue
            dedupe = f"repeat:{state.chat_id}:{state.item_id}:{state.generation}:{int(state.next_run.timestamp())}"
            job_id = await durable.enqueue(ctx, "repeat_note", state.chat_id, generation=state.generation,
                dedupe_key=dedupe, payload=dict(item_id=state.item_id), session=session)
            job = await session.get(GuardJob, job_id, populate_existing=True)
            if job is not None and job.status == "uncertain":
                state.status = "uncertain"
            elif job is not None and job.status in {"failed", "cancelled", "succeeded"}:
                # A cancelled pre-dispatch job (including pause) gets a new due identity.
                state.next_run = utcnow() + timedelta(seconds=state.interval_seconds)


async def run(ctx: BotContext, job: GuardJob) -> ActionResult:
    svc = ctx.extras["guard"]
    async with svc.member_session(job.chat_id, 0) as (session, _member):
        state = await session.get(GuardRepeat, (ctx.bot_id, job.chat_id, int(job.payload["item_id"])))
        item = (await session.execute(select(GuardItem).where(GuardItem.bot_id == ctx.bot_id,
            GuardItem.chat_id == job.chat_id, GuardItem.id == int(job.payload["item_id"])))) .scalar_one_or_none()
        if state is None or item is None or state.generation != job.generation or state.status != "active":
            return result_of(StepResult("repeat_note", "skipped", "generation_changed"))
        author = Actor(ctx.bot_id, job.chat_id, "human", state.author_id)
        allowed = await authz.authorize(ctx, author, target_chat_id=job.chat_id,
            caller_rights=frozenset({"change_info"}), bot_rights=frozenset())
        cfg = await svc.config(job.chat_id, fresh=True)
        if not allowed.allowed or (cfg.private_notes and not item.options.get("noprivate")) or item.options.get("admin") or item.options.get("private"):
            state.status = "cancelled"
            result = result_of(StepResult("repeat_note", "skipped", "authority_or_access_changed"))
        else:
            night = await session.get(GuardNight, (ctx.bot_id, job.chat_id))
            if night is not None and night.status in {"prepared", "dispatched", "closed", "uncertain"}:
                state.next_run = utcnow() + timedelta(seconds=60)
                result = result_of(StepResult("repeat_note", "skipped", "night_closed"))
            else:
                member = await perms.fresh_member(ctx, job.chat_id, state.author_id)
                f = await delivery.fillings(ctx, job.chat_id, member.user if member else None, raw=item.text or "")
                await durable.dispatched(ctx, job)
                sent = await delivery.send(ctx, job.chat_id,
                    delivery.Content.from_dict(dict(raw=item.text or "", format=item.content_format,
                        media_kind=item.media_kind, file_id=item.file_id)), f, thread_id=state.thread_id)
                result = sent.result
                if any(step.error_code in {"TelegramNetworkError", "TelegramServerError"} for step in result.steps):
                    state.status = "uncertain"
                elif not any(step.retry_after is not None for step in result.steps) or job.attempts >= 5:
                    # At most one catch-up delivery, never a backlog burst after downtime.
                    state.next_run = utcnow() + timedelta(seconds=state.interval_seconds)
        await durable.finish(ctx, job, result, session=session)
        return result


async def schedule_delete(ctx: BotContext, chat_id: int, ids: list[int], *, session: AsyncSession,
                          seconds: int = 300) -> None:
    for mid in dict.fromkeys(ids):
        await durable.enqueue(ctx, "content_delete", chat_id, dedupe_key=f"content_delete:{chat_id}:{mid}",
            payload=dict(message_id=mid), run_at=utcnow() + timedelta(seconds=seconds), session=session)


async def delete_message(ctx: BotContext, job: GuardJob) -> ActionResult:
    allowed = await authz.internal_authorize(ctx, job.chat_id, frozenset({"delete_messages"}))
    if not allowed.allowed:
        return actions.failure("content_delete", allowed.code)
    await durable.dispatched(ctx, job)
    return await actions.delete(ctx, job.chat_id, int(job.payload["message_id"]))
