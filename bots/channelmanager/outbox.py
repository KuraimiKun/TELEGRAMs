"""Fenced, bounded delivery intents. An expired dispatched lease is never blindly replayed."""

from __future__ import annotations

import asyncio
import math
import uuid
from collections.abc import Awaitable
from datetime import datetime, timedelta
from typing import Any, cast

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import case, exists, literal, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bots.channelmanager.models import Channel, Delivery, Operation, Post, VirtualGrant
from core.db.base import affected, upsert, utcnow
from core.db.models import Bot as BotRecord
from core.sdk.context import BotContext

LEASE_SECONDS = 90


class Notice(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    recipient_id: int = Field(gt=0)
    text: str = Field(min_length=1, max_length=4096)


class PostJob(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    delivery_id: str = Field(min_length=32, max_length=32)
    version: int = Field(gt=0)
    actor_id: int = Field(gt=0)
    automatic: bool = False
    grant_generation: int | None = None
    scheduled: bool = False


class AutoJob(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action_id: str = Field(min_length=32, max_length=32)


POST_KINDS = frozenset({"publish", "edit", "pin", "delete", "delete_reminder", "markup"})


class DispatchBusy(Exception):
    pass


async def enqueue(session: AsyncSession, ctx: BotContext, channel: Channel, *, kind: str,
                  dedupe_key: str, payload: dict[str, Any], run_at: datetime | None = None,
                  automation_id: str | None = None, delivery_id: str | None = None, member_action_id: str | None = None,
                  growth_action_id: str | None = None) -> str:
    if channel.bot_id != ctx.bot_id:
        raise ValueError("channel_namespace_mismatch")
    from bots.channelmanager.automation import AUTO_KINDS
    from bots.channelmanager.growth_specs import GROWTH_KINDS
    from bots.channelmanager.member_specs import MEMBER_KINDS
    if kind not in {"notice", *POST_KINDS, *AUTO_KINDS, *MEMBER_KINDS, *GROWTH_KINDS}:
        raise ValueError("unsupported_operation")
    if kind in GROWTH_KINDS:
        if AutoJob.model_validate(payload).action_id != growth_action_id or automation_id or delivery_id or member_action_id:
            raise ValueError("growth_action_mismatch")
    elif growth_action_id:
        raise ValueError("growth_action_scope")
    elif kind in MEMBER_KINDS:
        if AutoJob.model_validate(payload).action_id != member_action_id or automation_id or delivery_id:
            raise ValueError("member_action_mismatch")
    elif member_action_id:
        raise ValueError("member_action_scope")
    elif kind in AUTO_KINDS:
        job_auto = AutoJob.model_validate(payload)
        if job_auto.action_id != automation_id:
            raise ValueError("automation_mismatch")
    elif kind == "notice":
        if delivery_id or automation_id:
            raise ValueError("invalid_notice_scope")
        Notice.model_validate(payload)
    else:
        if automation_id:
            raise ValueError("invalid_post_scope")
        job = PostJob.model_validate(payload)
        if job.automatic and kind not in {"delete", "delete_reminder", "markup"}:
            raise ValueError("invalid_automatic_operation")
        delivery_id = job.delivery_id
        if not job.automatic:
            grant = await session.get(VirtualGrant, (ctx.bot_id, channel.channel_id, job.actor_id))
            job.grant_generation = grant.generation if grant and grant.active else None
            job.scheduled = bool(kind == "publish" and run_at and run_at > utcnow())
            payload = job.model_dump()
    if not 1 <= len(dedupe_key) <= 160:
        raise ValueError("invalid_dedupe_key")
    await session.execute(upsert(session, Operation).values(bot_id=ctx.bot_id, id=uuid.uuid4().hex,
        channel_id=channel.channel_id, generation=channel.generation, kind=kind, dedupe_key=dedupe_key, delivery_id=delivery_id, automation_id=automation_id,
        member_action_id=member_action_id,
        growth_action_id=growth_action_id,
        payload=payload, run_at=run_at or utcnow()).on_conflict_do_nothing(index_elements=["bot_id", "dedupe_key"]))
    return str((await session.execute(select(Operation.id).where(
        Operation.bot_id == ctx.bot_id, Operation.dedupe_key == dedupe_key))).scalar_one())


async def claim(ctx: BotContext, *, cleanup_only: bool = False) -> Operation | None:
    now = utcnow()
    # Reserve an oldest-first share while prioritizing short contact windows.
    priority = literal(0) if int(now.timestamp()) % 3 == 2 else case(
        (Operation.kind == "member_contact", 0),
        (Operation.kind.in_({"member_approve", "member_decline"}), 1), else_=2)
    async with ctx.sm() as session:
        from bots.channelmanager.release import CLEANUP
        row = (await session.execute(select(Operation).where(Operation.bot_id == ctx.bot_id,
            Operation.status == "pending", Operation.run_at <= now, Operation.attempts < Operation.max_attempts,
            Operation.kind.in_(CLEANUP) if cleanup_only else literal(True))
            .order_by(priority, Operation.run_at, Operation.id).limit(1).with_for_update(skip_locked=True))).scalar_one_or_none()
        if row is None:
            return None
        owner = uuid.uuid4().hex
        changed = await session.execute(update(Operation).where(Operation.bot_id == ctx.bot_id,
            Operation.id == row.id, Operation.status == "pending", Operation.attempts == row.attempts).values(
                status="running", lease_owner=owner, lease_until=now + timedelta(seconds=LEASE_SECONDS),
                dispatched=False, attempts=Operation.attempts + 1, updated_at=now))
        if affected(changed) != 1:
            await session.rollback()
            return None
        await session.commit()
        await session.refresh(row)
        return row


def fence(ctx: BotContext, op: Operation):
    return (Operation.bot_id == ctx.bot_id, Operation.id == op.id, Operation.status == "running",
            Operation.lease_owner == op.lease_owner, Operation.lease_until > utcnow())


async def finish(ctx: BotContext, op: Operation, status: str, *, code: str | None = None,
                 delay: int = 0, message_id: int | None = None, refund_attempt: bool = False,
                 session: AsyncSession | None = None) -> bool:
    if session is None:
        async with ctx.sm() as owned:
            completed = await finish(ctx, op, status, code=code, delay=delay, message_id=message_id,
                                  refund_attempt=refund_attempt, session=owned)
            await owned.commit()
            return completed
    result = await session.execute(update(Operation).where(*fence(ctx, op)).values(
            status=status, error_code=code, remote_message_id=message_id, lease_owner=None, lease_until=None,
            run_at=utcnow() + timedelta(seconds=delay), updated_at=utcnow(),
            attempts=max(0, op.attempts - 1) if refund_attempt else op.attempts,
            dispatched=False if status == "pending" else op.dispatched))
    return affected(result) == 1


async def mark_dispatched(ctx: BotContext, op: Operation, *, require_generation: bool = True, conditions=()) -> bool:
    async with ctx.sm() as session:
        if op.delivery_id:
            target = await session.get(Delivery, (ctx.bot_id, op.delivery_id))
            if target is None:
                return False
            # Serialize the final dispatch decision with edits/cancellation. An EXISTS
            # check alone can see the old generation while an operator holds the post.
            await session.get(Post, (ctx.bot_id, target.post_id), with_for_update=True)
            await session.get(Delivery, (ctx.bot_id, target.id), with_for_update=True)
            busy = await session.scalar(select(Operation.id).where(Operation.bot_id == ctx.bot_id,
                Operation.delivery_id == target.id, Operation.id != op.id, Operation.status == "running",
                Operation.dispatched.is_(True), Operation.lease_until > utcnow()).limit(1))
            if busy:
                raise DispatchBusy
        await session.get(Channel, (ctx.bot_id, op.channel_id), with_for_update=True)
        from bots.channelmanager.release import operation_allowed
        if not await operation_allowed(ctx, op.kind, session=session, channel_id=op.channel_id):
            return False
        from bots.channelmanager.senders import allowed
        if op.kind in {"publish", "edit", "pin"} and not await allowed(ctx, op.channel_id, session=session):
            return False
        checks = [Channel.bot_id == ctx.bot_id, Channel.channel_id == op.channel_id]
        if require_generation:
            checks.append(Channel.generation == op.generation)
            if op.kind in POST_KINDS:
                checks.append(Channel.status == "active")
        else:
            checks.append(Channel.status != "disconnected")
        valid = exists().where(*checks)
        active = exists().where(BotRecord.id == ctx.bot_id, BotRecord.active.is_(True))
        result = await session.execute(update(Operation).where(*fence(ctx, op), valid, active, *conditions).values(dispatched=True))
        await session.commit()
        return affected(result) == 1


# One atomic budget across worker replicas. Reserve neither budget when either is exhausted.
_RATE = """
local botn = tonumber(redis.call('get', KEYS[1]) or '0')
local chatttl = redis.call('pttl', KEYS[2])
if botn >= 25 then return math.max(redis.call('pttl', KEYS[1]), 1) end
if chatttl > 0 then return chatttl end
if redis.call('incr', KEYS[1]) == 1 then redis.call('pexpire', KEYS[1], 1000) end
redis.call('set', KEYS[2], '1', 'PX', 1000)
return 0
"""


async def reserve_budget(ctx: BotContext, recipient_id: int) -> int:
    result = await cast(Awaitable[Any], ctx.redis.eval(_RATE, 2, ctx.keys("send-rate", "bot"),
                                                    ctx.keys("send-rate", "chat", recipient_id)))
    return math.ceil(int(result) / 1000)


async def wait_budget(ctx: BotContext, recipient_id: int) -> None:
    """Optional core-broadcast hook sharing this bot's worker budgets."""
    while not ctx.shutdown.is_set():
        from bots.channelmanager.release import require
        await require(ctx, "publishing")
        delay = await reserve_budget(ctx, recipient_id)
        if not delay:
            return
        try:
            await asyncio.wait_for(ctx.shutdown.wait(), timeout=delay)
        except TimeoutError:
            continue
    raise asyncio.CancelledError


async def execute(ctx: BotContext, op: Operation) -> None:
    from bots.channelmanager.release import operation_allowed
    if not await operation_allowed(ctx, op.kind, channel_id=op.channel_id):
        await finish(ctx, op, "cancelled", code="release_stage")
        return
    if op.growth_action_id is not None:
        from bots.channelmanager.growth_delivery import execute as execute_growth
        await execute_growth(ctx, op)
        return
    if op.member_action_id is not None:
        from bots.channelmanager.member_delivery import execute as execute_member
        await execute_member(ctx, op)
        return
    if op.automation_id is not None:
        from bots.channelmanager.automation_delivery import execute as execute_automation
        await execute_automation(ctx, op)
        return
    if op.kind in POST_KINDS:
        from bots.channelmanager.delivery import execute as execute_post
        await execute_post(ctx, op)
        return
    try:
        if op.kind != "notice":
            raise ValueError("unsupported_operation")
        notice = Notice.model_validate(op.payload)
    except ValueError:
        await finish(ctx, op, "failed", code="invalid_operation")
        return
    try:
        delay = await reserve_budget(ctx, notice.recipient_id)
    except Exception:
        await finish(ctx, op, "pending", code="rate_store_unavailable", delay=5, refund_attempt=True)
        return
    if delay:
        await finish(ctx, op, "pending", code="local_rate", delay=delay, refund_attempt=True)
        return
    if not await mark_dispatched(ctx, op):
        await finish(ctx, op, "cancelled", code="stale_generation")
        return
    op.dispatched = True
    try:
        message = await ctx.bot.send_message(notice.recipient_id, notice.text, parse_mode="HTML", request_timeout=30)
    except TelegramRetryAfter as exc:
        pending = op.attempts < op.max_attempts
        await finish(ctx, op, "pending" if pending else "failed", code="TelegramRetryAfter",
                     delay=max(1, exc.retry_after))
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        await finish(ctx, op, "failed", code=type(exc).__name__)
    except (TelegramNetworkError, TelegramServerError, TimeoutError):
        await finish(ctx, op, "uncertain", code="delivery_unknown")
    except asyncio.CancelledError:
        # Leave the dispatch marker for recovery, even if shutdown interrupts the HTTP call.
        raise
    except Exception:
        await finish(ctx, op, "uncertain", code="delivery_unknown")
    else:
        await finish(ctx, op, "succeeded", message_id=message.message_id)


async def recover(ctx: BotContext, limit: int = 100) -> int:
    async with ctx.sm() as session:
        rows = list((await session.execute(select(Operation).where(Operation.bot_id == ctx.bot_id,
            Operation.status == "running", Operation.lease_until <= utcnow())
            .order_by(Operation.lease_until).limit(limit).with_for_update(skip_locked=True))).scalars())
        for op in rows:
            status = "uncertain" if op.dispatched else "failed" if op.attempts >= op.max_attempts else "pending"
            await session.execute(update(Operation).where(Operation.bot_id == ctx.bot_id, Operation.id == op.id,
                Operation.status == "running", Operation.lease_owner == op.lease_owner,
                Operation.lease_until <= utcnow()).values(status=status, lease_owner=None, lease_until=None,
                    error_code="interrupted_after_dispatch" if op.dispatched else "interrupted_before_dispatch",
                    run_at=utcnow(), updated_at=utcnow()))
        await session.commit()
        return len(rows)
