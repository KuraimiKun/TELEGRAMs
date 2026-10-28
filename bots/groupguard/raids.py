"""Persisted scoped raid generations and owning deadlines with source-specific bans."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta

from aiogram.types import ChatJoinRequest, ChatMemberUpdated
from redis.exceptions import RedisError
from sqlalchemy import select, update

from bots.groupguard import actions, authz, durable, joins, perms
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.contracts import ActionResult, StepResult, result_of
from bots.groupguard.models import GuardEventReceipt, GuardJob, GuardRaid
from core.db.base import affected, upsert, utcnow
from core.sdk.context import BotContext

COUNT = r"""
local now = tonumber(ARGV[1])
redis.call('ZREMRANGEBYSCORE',KEYS[1],'-inf',now-60)
redis.call('ZADD',KEYS[1],now,ARGV[2])
redis.call('EXPIRE',KEYS[1],65)
return redis.call('ZCARD',KEYS[1])
"""


def active(raid: GuardRaid | None) -> bool:
    return raid is not None and raid.status == "active" and raid.deadline > utcnow()


async def state(ctx: BotContext, chat_id: int) -> GuardRaid | None:
    async with ctx.sm() as session:
        return await session.get(GuardRaid, (ctx.bot_id, chat_id))


async def change(
    ctx: BotContext,
    chat_id: int,
    seconds: int | None,
    *,
    automatic: bool = False,
    expected_auto: int | None = None,
    expected_generation: str | None = None,
    check_generation: bool = False,
) -> GuardRaid | None:
    svc = ctx.extras["guard"]
    async with svc.member_session(chat_id, 0) as (session, _member):
        cfg = await svc.config(chat_id, fresh=True)
        old = (
            await session.execute(
                select(GuardRaid).where(GuardRaid.bot_id == ctx.bot_id, GuardRaid.chat_id == chat_id)
            )
        ).scalar_one_or_none()
        if check_generation and (old.generation if old is not None else None) != expected_generation:
            return None
        if automatic and (
            not cfg.auto_raid_count
            or active(old)
            or cfg.auto_raid_count != expected_auto
            or (old.generation if old else None) != expected_generation
        ):
            return old
        generation = uuid.uuid4().hex
        deadline = utcnow() + timedelta(seconds=seconds or 0)
        # Activation and its owning deadline job commit atomically in this transaction.
        await session.execute(
            update(GuardJob)
            .where(
                GuardJob.bot_id == ctx.bot_id,
                GuardJob.chat_id == chat_id,
                GuardJob.kind == "raid_expire",
                GuardJob.status.in_({"pending", "running"}),
                GuardJob.dispatched.is_(False),
            )
            .values(status="cancelled", updated_at=utcnow())
        )
        values = dict(
            generation=generation,
            deadline=deadline,
            ban_seconds=cfg.raid_ban_seconds,
            status="active" if seconds is not None else "inactive",
            updated_at=utcnow(),
        )
        await session.execute(
            upsert(session, GuardRaid)
            .values(bot_id=ctx.bot_id, chat_id=chat_id, **values)
            .on_conflict_do_update(index_elements=["bot_id", "chat_id"], set_=values)
        )
        if seconds is not None:
            await durable.enqueue(
                ctx,
                "raid_expire",
                chat_id,
                dedupe_key=f"raid:{chat_id}:{generation}",
                generation=generation,
                payload={},
                run_at=deadline,
                session=session,
            )
    return await state(ctx, chat_id)


async def expire_job(ctx: BotContext, job: GuardJob) -> ActionResult:
    svc = ctx.extras["guard"]
    async with svc.member_session(job.chat_id, 0) as (session, _member):
        await session.execute(
            update(GuardRaid)
            .where(
                GuardRaid.bot_id == ctx.bot_id,
                GuardRaid.chat_id == job.chat_id,
                GuardRaid.generation == job.generation,
                GuardRaid.deadline <= utcnow(),
            )
            .values(status="expired", updated_at=utcnow())
        )
    return result_of(StepResult("raid_expire", "applied"))


async def protected(ctx: BotContext, chat_id: int, user_id: int) -> bool:
    actual = await perms.fresh_rights(ctx, chat_id, user_id)
    return (
        actual is None or actual.is_admin or await ctx.extras["guard"].approval(chat_id, user_id) is not None
    )


async def decline(
    ctx: BotContext, chat_id: int, user_id: int, contact_id: int, issued: datetime
) -> ActionResult:
    raid = await state(ctx, chat_id)
    if not active(raid) or raid is None:
        return result_of(StepResult("raid_decline", "skipped", "inactive"))
    fingerprint = hashlib.sha256(
        json.dumps([chat_id, user_id, contact_id, int(issued.timestamp()), raid.generation]).encode()
    ).hexdigest()
    scope = dict(bot_id=ctx.bot_id, kind="raid_request", chat_id=chat_id, fingerprint=fingerprint)
    async with ctx.sm() as session:
        inserted = await session.execute(
            upsert(session, GuardEventReceipt)
            .values(**scope, user_id=user_id, status="processing", created_at=utcnow(), updated_at=utcnow())
            .on_conflict_do_nothing()
        )
        await session.commit()
        if affected(inserted) != 1:
            prior = (await session.execute(select(GuardEventReceipt).filter_by(**scope))).scalar_one()
            return (
                result_of(StepResult("raid_decline_prior", "acknowledged"))
                if prior.status == "completed"
                else actions.failure("raid_decline_prior", prior.error_code or "uncertain")
            )
    outcome = "uncertain"
    error: str | None = "interrupted_processing"
    try:
        cap = await authz.internal_authorize(ctx, chat_id, frozenset({"invite_users"}))
        current = await state(ctx, chat_id)
        if not cap.allowed:
            result = actions.failure("raid_decline", cap.code)
        elif (
            not active(current)
            or current is None
            or current.generation != raid.generation
            or await protected(ctx, chat_id, user_id)
        ):
            result = actions.failure("raid_decline", "policy_changed")
        else:
            result = result_of(
                await actions.perform(
                    "raid_decline", lambda: ctx.bot.decline_chat_join_request(chat_id, user_id)
                )
            )
        error = next((s.error_code for s in result.steps if s.status == "failed"), None)
        outcome = (
            "completed"
            if result.primary_completed
            else "uncertain"
            if error in {"TelegramNetworkError", "TelegramServerError"}
            else "failed"
        )
        return result
    finally:
        async with ctx.sm() as session:
            await session.execute(
                update(GuardEventReceipt)
                .filter_by(**scope)
                .values(status=outcome, error_code=error, updated_at=utcnow())
            )
            await session.commit()


async def joining(ctx: BotContext, event: ChatMemberUpdated) -> bool:
    user, chat = event.new_chat_member.user, event.chat
    cfg: ChatConfig = await ctx.extras["guard"].config(chat.id, fresh=True)
    if user.is_bot or await protected(ctx, chat.id, user.id):
        return False
    raid = await state(ctx, chat.id)
    if cfg.auto_raid_count and not active(raid):
        # Delayed historical deliveries do not create a new minute of joins.
        now = time.time()
        if abs(now - event.date.timestamp()) < 60:
            try:
                count = await ctx.redis.eval(
                    COUNT,
                    1,
                    ctx.keys(
                        "raid_joins", chat.id, raid.generation if raid else "initial", cfg.auto_raid_count
                    ),
                    str(now),
                    joins.fingerprint(event),
                )  # type: ignore[misc]
                if int(count) > cfg.auto_raid_count:
                    raid = await change(
                        ctx,
                        chat.id,
                        cfg.raid_seconds,
                        automatic=True,
                        expected_auto=cfg.auto_raid_count,
                        expected_generation=raid.generation if raid else None,
                    )
            except (RedisError, ValueError, TypeError):
                await actions.announce(
                    ctx, cfg, chat.id, chat.title, actions.failure("raid", "counter_unavailable"), ""
                )
    if not active(raid) or raid is None:
        return False

    async def current() -> bool:
        latest = await state(ctx, chat.id)
        return (
            active(latest)
            and latest is not None
            and latest.generation == raid.generation
            and not await protected(ctx, chat.id, user.id)
        )

    result = await actions.punish(
        ctx,
        chat.id,
        user.id,
        "ban",
        timedelta(seconds=raid.ban_seconds),
        source="raid",
        generation=raid.generation,
        dispatch_guard=current,
    )
    await actions.announce(
        ctx,
        cfg,
        chat.id,
        chat.title,
        result,
        actions.group_t(ctx, cfg)("gg-raid-banned", user=actions.mention(user.id, user.first_name)),
    )
    return True


async def request(ctx: BotContext, event: ChatJoinRequest) -> bool:
    cfg = await ctx.extras["guard"].config(event.chat.id, fresh=True)
    raid = await state(ctx, event.chat.id)
    if not active(raid) or event.from_user.is_bot or await protected(ctx, event.chat.id, event.from_user.id):
        return False
    result = await decline(ctx, event.chat.id, event.from_user.id, event.user_chat_id, event.date)
    if any(step.operation == "raid_decline_prior" for step in result.steps):
        return True
    await actions.announce(
        ctx,
        cfg,
        event.chat.id,
        event.chat.title,
        result,
        actions.group_t(ctx, cfg)(
            "gg-raid-declined", user=actions.mention(event.from_user.id, event.from_user.first_name)
        ),
    )
    return True
