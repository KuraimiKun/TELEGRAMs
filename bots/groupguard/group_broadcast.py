"""Operator-owned group campaigns with isolated bounded fan-out and durable destination results."""

from __future__ import annotations

import time
from datetime import timedelta

from aiogram.types import User
from redis.exceptions import RedisError
from sqlalchemy import func, select, update

from bots.groupguard import actions, authz, delivery, durable
from bots.groupguard.contracts import ActionResult, StepResult, result_of
from bots.groupguard.models import GuardBroadcast, GuardChat, GuardJob
from core.db.base import utcnow
from core.db.models import ChildBot
from core.sdk.context import BotContext

QUOTA = """
local n=redis.call('INCR',KEYS[1])
if n==1 then redis.call('EXPIRE',KEYS[1],2) end
return n
"""


async def owner(ctx: BotContext, user_id: int) -> bool:
    if not await authz.active_namespace(ctx):
        return False
    if ctx.child is None:
        return user_id in ctx.env.admin_ids or ctx.platform.is_super_admin(user_id)
    async with ctx.sm() as session:
        child = await session.get(ChildBot, ctx.bot_id)
    return (
        child is not None
        and child.owner_id == user_id
        and child.status == "active"
        and child.template == "groupguard"
    )


async def create(ctx: BotContext, user: User, content: delivery.Content) -> GuardBroadcast | None:
    if user.is_bot or not await owner(ctx, user.id):
        return None
    # Shared member0 protects a per-bot campaign limit; no group permissions are granted here.
    svc = ctx.extras["guard"]
    async with svc.member_session(0, 0) as (session, _member):
        existing = (
            (
                await session.execute(
                    select(GuardBroadcast)
                    .where(GuardBroadcast.bot_id == ctx.bot_id, GuardBroadcast.status == "active")
                    .with_for_update()
                )
            )
            .scalars()
            .first()
        )
        if existing is not None:
            return None
        recent = (
            await session.execute(
                select(GuardBroadcast.id)
                .where(
                    GuardBroadcast.bot_id == ctx.bot_id,
                    GuardBroadcast.author_id == user.id,
                    GuardBroadcast.created_at > utcnow() - timedelta(minutes=5),
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if recent is not None:
            return None
        row = GuardBroadcast(
            bot_id=ctx.bot_id,
            author_id=user.id,
            content=content.to_dict(),
            subject=user.model_dump(include={"id", "is_bot", "first_name", "last_name", "username"}),
            status="active",
            cursor=-(2**63),
            expanded=False,
        )
        session.add(row)
        await session.flush()
        return row


async def tick(ctx: BotContext) -> None:
    async with ctx.sm() as session:
        ids = list(
            (
                await session.execute(
                    select(GuardBroadcast.id)
                    .where(GuardBroadcast.bot_id == ctx.bot_id, GuardBroadcast.status == "active")
                    .order_by(GuardBroadcast.id)
                    .limit(10)
                )
            ).scalars()
        )
    for bid in ids:
        async with ctx.sm() as session:
            author = (
                await session.execute(
                    select(GuardBroadcast.author_id).where(
                        GuardBroadcast.bot_id == ctx.bot_id, GuardBroadcast.id == bid
                    )
                )
            ).scalar_one_or_none()
        if author is None:
            continue
        if not await owner(ctx, author):
            async with ctx.sm() as session:
                await session.execute(
                    update(GuardBroadcast)
                    .where(GuardBroadcast.bot_id == ctx.bot_id, GuardBroadcast.id == bid)
                    .values(status="cancelled", updated_at=utcnow())
                )
                await session.commit()
            continue
        async with ctx.sm() as session:
            campaign = (
                await session.execute(
                    select(GuardBroadcast)
                    .where(
                        GuardBroadcast.bot_id == ctx.bot_id,
                        GuardBroadcast.id == bid,
                        GuardBroadcast.status == "active",
                    )
                    .with_for_update()
                )
            ).scalar_one_or_none()
            if campaign is None:
                continue
            prefix = f"groupcast:{bid}:"
            pending = (
                await session.execute(
                    select(func.count())
                    .select_from(GuardJob)
                    .where(
                        GuardJob.bot_id == ctx.bot_id,
                        GuardJob.dedupe_key.startswith(prefix),
                        GuardJob.status.in_({"pending", "running"}),
                    )
                )
            ).scalar_one()
            if pending >= 100:
                continue
            chats = list(
                (
                    await session.execute(
                        select(GuardChat.chat_id)
                        .where(
                            GuardChat.bot_id == ctx.bot_id,
                            GuardChat.active.is_(True),
                            GuardChat.chat_id > campaign.cursor,
                        )
                        .order_by(GuardChat.chat_id)
                        .limit(100)
                    )
                ).scalars()
            )
            for chat in chats:
                await durable.enqueue(
                    ctx,
                    "group_broadcast",
                    chat,
                    dedupe_key=prefix + str(chat),
                    payload={"campaign_id": bid},
                    user_id=author,
                    session=session,
                )
            if chats:
                campaign.cursor = chats[-1]
            else:
                campaign.expanded = True
                if pending == 0:
                    campaign.status = "completed"
            campaign.updated_at = utcnow()
            await session.commit()


async def latest_status(ctx: BotContext, user_id: int) -> tuple[GuardBroadcast, dict[str, int]] | None:
    if not await owner(ctx, user_id):
        return None
    async with ctx.sm() as session:
        campaign = (await session.execute(select(GuardBroadcast).where(
            GuardBroadcast.bot_id == ctx.bot_id, GuardBroadcast.author_id == user_id
        ).order_by(GuardBroadcast.id.desc()).limit(1))).scalar_one_or_none()
        if campaign is None:
            return None
        counts = dict((await session.execute(select(GuardJob.status, func.count()).where(
            GuardJob.bot_id == ctx.bot_id, GuardJob.dedupe_key.startswith(f"groupcast:{campaign.id}:")
        ).group_by(GuardJob.status))).all())
        return campaign, counts


async def run(ctx: BotContext, job: GuardJob) -> ActionResult:
    async with ctx.sm() as session:
        campaign = (
            await session.execute(
                select(GuardBroadcast).where(
                    GuardBroadcast.bot_id == ctx.bot_id, GuardBroadcast.id == job.payload.get("campaign_id")
                )
            )
        ).scalar_one_or_none()
        chat = await session.get(GuardChat, (ctx.bot_id, job.chat_id))
    if campaign is None or campaign.status not in {"active", "completed"} or chat is None or not chat.active:
        return result_of(StepResult("group_broadcast", "skipped", "destination_changed"))
    if not await owner(ctx, campaign.author_id):
        return result_of(StepResult("group_broadcast", "skipped", "owner_changed"))
    try:
        count = await ctx.redis.eval(QUOTA, 1, ctx.keys("guard_outbound_rate", int(time.time())))  # type: ignore[misc]
    except RedisError:
        await durable.defer(ctx, job, 5, "rate_state_unavailable")
        return actions.failure("group_broadcast", "rate_state_unavailable")
    if int(count) > 20:
        await durable.defer(ctx, job, 1)
        return actions.failure("group_broadcast", "local_rate")
    content = delivery.Content.from_dict(campaign.content)
    user = User.model_validate(campaign.subject)
    f = await delivery.fillings(ctx, job.chat_id, user, raw=content.raw)
    cfg = await ctx.extras["guard"].config(job.chat_id, fresh=True)
    # Rendering performs awaited lookups: recheck current authority and destination after them.
    if not await owner(ctx, campaign.author_id):
        return result_of(StepResult("group_broadcast", "skipped", "owner_changed"))
    async with ctx.sm() as session:
        current = await session.get(GuardBroadcast, campaign.id)
        destination = await session.get(GuardChat, (ctx.bot_id, job.chat_id))
        if (current is None or current.bot_id != ctx.bot_id or current.status not in {"active", "completed"}
                or destination is None or not destination.active):
            return result_of(StepResult("group_broadcast", "skipped", "destination_changed"))
    await durable.dispatched(ctx, job)
    sent = await delivery.send(
        ctx,
        job.chat_id,
        content,
        f,
        kind="broadcast",
        thread_id=None if cfg.action_topic == 1 else cfg.action_topic,
    )
    if any(step.completed for step in sent.result.steps) and any(step.retry_after is not None for step in sent.result.steps):
        from dataclasses import replace
        # Do not duplicate a posted attachment after a known companion failure.
        return replace(sent.result,steps=tuple(replace(step,retry_after=None) for step in sent.result.steps))
    return sent.result
