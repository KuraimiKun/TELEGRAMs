"""Bounded inbox processing and outgoing delivery using the platform process lifecycle."""

from __future__ import annotations

import asyncio
import contextlib
import time

from prometheus_client import Gauge, Histogram

from bots.channelmanager import ingress, outbox
from core.log import get_logger
from core.sdk.context import BotContext

log = get_logger(__name__)
QUEUE = Gauge("channelmanager_work", "Channel Manager operations by state", ["bot", "state"])
LAG = Gauge("channelmanager_queue_lag_seconds", "Oldest due operation or pending inbox receipt", ["bot", "queue"])
DURATION = Histogram("channelmanager_operation_seconds", "One bounded delivery attempt", ["bot"])
OP_TIMEOUT_SECONDS = 60


def progress(ctx):
    if callback := ctx.extras.get("chm_progress"):
        callback()


async def sweep(ctx: BotContext) -> None:
    await outbox.recover(ctx)
    from bots.channelmanager.delivery import reconcile
    await reconcile(ctx)
    from bots.channelmanager.recurring import settle_replacements
    await settle_replacements(ctx)
    from bots.channelmanager.automation_delivery import reconcile as reconcile_automation
    await reconcile_automation(ctx)
    from bots.channelmanager.member_delivery import reconcile as reconcile_members
    await reconcile_members(ctx)
    from bots.channelmanager.growth_delivery import reconcile as reconcile_growth
    await reconcile_growth(ctx)
    await ctx.extras["billing"].sweep()
    if not ctx.is_child:
        await emit_metrics(ctx.sm, ctx.metric_name, [ctx.bot_id])


async def emit_metrics(sm, metric_name, bot_ids):
    from bots.channelmanager.service import totals_for
    for state, count in (await totals_for(sm, bot_ids)).items():
        QUEUE.labels(metric_name, state).set(count)
    from bots.channelmanager.diagnostics import snapshot_for
    for key, value in (await snapshot_for(sm, bot_ids)).items():
        if key.endswith("_lag_seconds"):
            LAG.labels(metric_name, key.removesuffix("_lag_seconds")).set(value)
        else:
            QUEUE.labels(metric_name, key).set(value)


async def tick(ctx: BotContext) -> int:
    settings = await ctx.settings.get()
    count = 0
    for _ in range(settings.worker_batch_size):
        if ctx.shutdown.is_set() or not await ingress.process_payment(ctx):
            break
        count += 1
        progress(ctx)
    for _ in range(settings.worker_batch_size):
        if ctx.shutdown.is_set() or not await ingress.process_one(ctx):
            break
        count += 1
        progress(ctx)
    if settings.maintenance:
        for _ in range(settings.worker_batch_size):
            if ctx.shutdown.is_set() or (op := await outbox.claim(ctx, cleanup_only=True)) is None:
                break
            await execute_bounded(ctx, op)
            count += 1
            progress(ctx)
        progress(ctx)
        return count
    from bots.channelmanager.invitations import cleanup_one
    for _ in range(settings.worker_batch_size):
        if ctx.shutdown.is_set() or not await cleanup_one(ctx):
            break
        count += 1
    from bots.channelmanager.members import plan_one as plan_member
    for _ in range(settings.worker_batch_size):
        if ctx.shutdown.is_set() or not await plan_member(ctx):
            break
        count += 1
    count += await ctx.extras["recurring"].sweep(limit=settings.worker_batch_size)
    from bots.channelmanager.automation import plan_one
    for _ in range(settings.worker_batch_size):
        if ctx.shutdown.is_set() or not await plan_one(ctx):
            break
        count += 1
    for _ in range(settings.worker_batch_size):
        if ctx.shutdown.is_set():
            break
        op = await outbox.claim(ctx)
        if op is None:
            break
        await execute_bounded(ctx, op)
        count += 1
        progress(ctx)
    progress(ctx)
    return count


async def execute_bounded(ctx, op):
    started = time.perf_counter()
    try:
        async with asyncio.timeout(OP_TIMEOUT_SECONDS):
            await outbox.execute(ctx, op)
    except TimeoutError:
        # Recovery reads the durable dispatch marker, including a cancellation during SQL commit.
        log.warning("channelmanager_operation_timeout", bot=ctx.slug, operation=op.id)
    finally:
        DURATION.labels(ctx.metric_name).observe(time.perf_counter() - started)


async def run(ctx: BotContext) -> None:
    from bots.channelmanager.health import PROGRESS_FILE, pulse
    ctx.extras["chm_progress"] = pulse
    try:
        while not ctx.shutdown.is_set():
            try:
                await sweep(ctx)
                await tick(ctx)
            except Exception as exc:
                log.warning("channelmanager_worker_iteration_failed", bot=ctx.slug, code=type(exc).__name__)
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(ctx.shutdown.wait(), timeout=1)
    finally:
        ctx.extras.pop("chm_progress", None)
        PROGRESS_FILE.unlink(missing_ok=True)
