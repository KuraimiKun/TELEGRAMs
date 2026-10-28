"""Central scheduler running core background tasks and bot-defined scheduled jobs.

Every job is:
* **wall-clock scheduled** — the next run time is stored in Redis, so restarts neither skip nor repeat runs;
* **single-flight** across replicas — guarded by a Redis lock holding an owner token (only the owner releases it);
* **bounded** — runs under a timeout and backs off exponentially after failures.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import secrets
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from redis.asyncio import Redis
from sqlalchemy import and_, or_, select, update

from core.config import PlatformConfig
from core.db.base import utcnow
from core.db.models import BotUser, Broadcast, ChildBot
from core.factory.runtime import ChildRegistry
from core.log import get_logger
from core.observability import SCHEDULED_RUNS, capture
from core.redis import KeySpace
from core.runtime.app import child_registry, run_role
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.services.broadcast import BroadcastRunner
from core.ui.emoji import E
from core.ui.text import esc, kv, title

log = get_logger("scheduler")

# Compare-and-delete: release a lock only if we still own it.
_RELEASE_LUA = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"

MIN_LOCK_TTL = 30
MAX_BACKOFF = 3600
NOTIFY_RATE_PER_SEC = 20


@dataclass(slots=True)
class _Job:
    name: str
    handler: Callable[[BotContext], Awaitable[None]]
    next_after: Callable[[datetime], datetime]  # given "now", when should the following run happen
    timeout: float


@dataclass(slots=True)
class _Target:
    """Where a job loop keeps its schedule/lock state and how it calls the job."""

    redis: Redis
    keys: KeySpace
    label: str  # bot slug (logs) / metric name
    metric: str
    call: Callable[[], Awaitable[None]]


def every(interval: timedelta) -> Callable[[datetime], datetime]:
    return lambda now: now + interval


def daily_at(hour: int, minute: int = 0) -> Callable[[datetime], datetime]:
    def nxt(now: datetime) -> datetime:
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return candidate if candidate > now else candidate + timedelta(days=1)

    return nxt


class CentralScheduler:
    def __init__(
        self, contexts: list[BotContext], stop: asyncio.Event | None = None, children: ChildRegistry | None = None
    ) -> None:
        self.contexts = contexts
        self._stop_event = stop or asyncio.Event()
        self.children = children

    def jobs_for(self, ctx: BotContext) -> list[_Job]:
        jobs: list[_Job] = []
        features = ctx.features
        if Feature.VIP in features:
            jobs.append(_Job("core:vip_notices", vip_notices, every(timedelta(minutes=15)), timeout=600))
        if Feature.DAILY_STATS in features:
            jobs.append(
                _Job("core:daily_report", daily_report, daily_at(ctx.platform.daily_report_hour_utc), timeout=300)
            )
        for job in ctx.module.scheduled_jobs():
            timeout = (job.timeout or job.interval).total_seconds()
            jobs.append(_Job(job.name, job.handler, every(job.interval), timeout=max(timeout, 1.0)))
        return jobs

    async def run(self) -> None:
        log.info("central_scheduler_started", bots=[c.slug for c in self.contexts])
        tasks = [
            asyncio.create_task(self._job_loop(self._ctx_target(ctx, job), job), name=f"{ctx.slug}:{job.name}")
            for ctx in self.contexts
            for job in self.jobs_for(ctx)
        ]
        if self.children is not None and self.children.enabled:
            tasks.append(asyncio.create_task(self.children.listen(), name="factory:listen"))
            tasks.append(asyncio.create_task(self._child_broadcasts(self.children), name="factory:broadcasts"))
            for template, module in self.children.templates.items():
                for fjob in module.factory_jobs():
                    job = _Job(fjob.name, _noop, every(fjob.interval),
                               timeout=max((fjob.timeout or fjob.interval).total_seconds(), 1.0))
                    target = _Target(
                        redis=self.children.infra.redis,
                        keys=KeySpace(f"factory_{template}"),
                        label=f"factory_{template}",
                        metric=f"factory_{template}",
                        call=functools.partial(fjob.handler, self.children),
                    )
                    tasks.append(asyncio.create_task(self._job_loop(target, job), name=f"factory:{template}:{fjob.name}"))
        # Broadcasts are long-running and resumable, so they get a dedicated runner instead of a timed job.
        tasks += [
            asyncio.create_task(
                BroadcastRunner(ctx.broadcast, ctx.bot).run(self._stop_event, on_finished=_broadcast_report(ctx)),
                name=f"{ctx.slug}:broadcasts",
            )
            for ctx in self.contexts
            if Feature.BROADCAST in ctx.features
        ]
        await self._stop_event.wait()
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        log.info("central_scheduler_stopped")

    def stop(self) -> None:
        self._stop_event.set()

    async def _sleep(self, seconds: float) -> None:
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(self._stop_event.wait(), timeout=max(0.0, seconds))

    @staticmethod
    def _ctx_target(ctx: BotContext, job: _Job) -> _Target:
        return _Target(ctx.redis, ctx.keys, ctx.slug, ctx.metric_name, functools.partial(job.handler, ctx))

    async def _child_broadcasts(self, children: ChildRegistry, poll: float = 10.0) -> None:
        """User-created bots get a broadcast runner only while they have a broadcast to send."""
        running: dict[int, asyncio.Task] = {}
        while not self._stop_event.is_set():
            try:
                async with children.infra.sm() as session:
                    stmt = (
                        select(Broadcast.bot_id)
                        .join(ChildBot, ChildBot.bot_id == Broadcast.bot_id)
                        .where(Broadcast.status.in_(("pending", "running")), ChildBot.status == "active")
                        .distinct()
                    )
                    bot_ids = [int(x) for x in (await session.execute(stmt)).scalars()]
                for bot_id in bot_ids:
                    if bot_id in running and not running[bot_id].done():
                        continue
                    runtime = await children.get(bot_id)
                    if runtime is None:
                        continue
                    ctx = runtime.ctx
                    runner = BroadcastRunner(ctx.broadcast, ctx.bot)
                    running[bot_id] = asyncio.create_task(
                        runner.run(self._stop_event, on_finished=_broadcast_report(ctx), until_idle=True),
                        name=f"{ctx.slug}:broadcasts",
                    )
                for bot_id in [b for b, t in running.items() if t.done()]:
                    running.pop(bot_id)
            except Exception as e:
                log.exception("child_broadcasts_failed", error=str(e))
            await self._sleep(poll)
        for t in running.values():
            t.cancel()
        await asyncio.gather(*running.values(), return_exceptions=True)

    async def _job_loop(self, target: _Target, job: _Job) -> None:
        redis = target.redis
        next_key = target.keys("sched", "next", job.name)
        lock_key = target.keys("sched", "lock", job.name)
        failures = 0

        while not self._stop_event.is_set():
            raw = await redis.get(next_key)
            due_at = float(raw) if raw else 0.0
            wait = due_at - time.time()
            if wait > 0:
                await self._sleep(min(wait, 60))
                continue

            token = secrets.token_hex(8)
            lock_ttl = max(int(job.timeout) + 30, MIN_LOCK_TTL)
            if not await redis.set(lock_key, token, nx=True, ex=lock_ttl):
                await self._sleep(15)  # another replica is running it
                continue

            delay: float = 0
            try:
                # Re-check under the lock: another replica may have just finished this run.
                raw = await redis.get(next_key)
                if raw and float(raw) > time.time():
                    continue
                started = time.monotonic()
                await asyncio.wait_for(target.call(), timeout=job.timeout)
                failures = 0
                nxt = job.next_after(utcnow())
                await redis.set(next_key, str(nxt.timestamp()))
                log.info("scheduled_job_done", bot=target.label, job=job.name, ms=int((time.monotonic() - started) * 1000))
                SCHEDULED_RUNS.labels(target.metric, job.name, "ok").inc()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                failures += 1
                delay = min(30 * 2 ** (failures - 1), MAX_BACKOFF)
                log.exception("scheduled_job_failed", bot=target.label, job=job.name, error=str(e), retry_in=delay)
                SCHEDULED_RUNS.labels(target.metric, job.name, "error").inc()
                capture(e, bot=target.label, job=job.name)
            finally:
                with contextlib.suppress(Exception):
                    await redis.eval(_RELEASE_LUA, 1, lock_key, token)
            if delay:
                await self._sleep(delay)


# --- Core jobs ---------------------------------------------------------------------------------------


async def _notify(ctx: BotContext, user: BotUser, key: str, **kwargs: object) -> bool:
    lang = ctx.translator.resolve(user.lang)
    text = ctx.translator.get(lang, key, **kwargs)
    try:
        await ctx.bot.send_message(chat_id=user.user_id, text=text)
        return True
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        return await _notify(ctx, user, key, **kwargs)
    except TelegramForbiddenError:
        await ctx.users.mark_blocked(user.user_id)
    except Exception as e:
        log.warning("vip_notice_send_failed", bot=ctx.slug, user_id=user.user_id, error=str(e))
    return False


async def vip_notices(ctx: BotContext) -> None:
    """Send each "expiring in 3 days" / "expired" notice exactly once per vip_until value."""
    now = utcnow()
    base = and_(
        BotUser.bot_id == ctx.bot_id,
        BotUser.blocked_bot.is_(False),
        BotUser.is_banned.is_(False),
        BotUser.vip_until.is_not(None),
    )

    def not_sent(stage: str):
        return or_(
            BotUser.vip_notice.is_(None),
            BotUser.vip_notice != stage,
            BotUser.vip_notice_for.is_(None),
            BotUser.vip_notice_for != BotUser.vip_until,
        )

    stages = [
        ("3d", and_(BotUser.vip_until > now, BotUser.vip_until <= now + timedelta(days=3)), "vip-expiring"),
        ("expired", and_(BotUser.vip_until <= now, BotUser.vip_until > now - timedelta(days=7)), "vip-expired"),
    ]
    for stage, window, key in stages:
        async with ctx.sm() as session:
            users = list((await session.execute(select(BotUser).where(base, window, not_sent(stage)))).scalars())
        for u in users:
            days = max(1, round((u.vip_until - now).total_seconds() / 86400)) if u.vip_until else 0
            await _notify(ctx, u, key, days=days)
            async with ctx.sm() as session:
                await session.execute(
                    update(BotUser)
                    .where(BotUser.bot_id == ctx.bot_id, BotUser.user_id == u.user_id)
                    .values(vip_notice=stage, vip_notice_for=u.vip_until)
                )
                await session.commit()
            await asyncio.sleep(1 / NOTIFY_RATE_PER_SEC)
        if users:
            log.info("vip_notices_sent", bot=ctx.slug, stage=stage, count=len(users))


async def daily_report(ctx: BotContext) -> None:
    if not ctx.env.log_channel_id:
        return
    data = await ctx.stats.get_overview()
    lines = [
        title(E.STATS, f"Daily System Snapshot — {esc(ctx.module.title)}"),
        "",
        kv("Total Users", f"{data['total_users']:,}"),
        kv("Active 24h", f"{data['active_24h']:,}"),
        kv("VIP Members", f"{data['vip_users']:,}"),
        kv("Total Actions", f"{data['total_actions']:,}"),
        kv("30d Revenue", f"{data['revenue_30d']:,} ⭐"),
    ]
    for cs in await ctx.module.stats(ctx):
        lines.append(kv(esc(cs.label), esc(cs.value)))
    await ctx.bot.send_message(chat_id=ctx.env.log_channel_id, text="\n".join(lines))


def _broadcast_report(ctx: BotContext):
    async def report(b: Broadcast) -> None:
        admin = await ctx.users.get(b.created_by)
        lang = ctx.translator.resolve(admin.lang if admin else None)
        key = "adm-bc-done" if b.status == "done" else "adm-bc-cancelled"
        text = ctx.translator.get(
            lang, key, id=b.id, sent=b.sent, blocked=b.blocked, failed=b.failed, total=b.total
        )
        await ctx.bot.send_message(chat_id=b.created_by, text=text)

    return report


async def _noop(_ctx: BotContext) -> None:
    return None


async def serve_scheduler(contexts: list[BotContext], stop: asyncio.Event) -> None:
    children = child_registry(contexts, stop)
    try:
        await CentralScheduler(contexts, stop, children=children).run()
    finally:
        if children is not None:
            await children.close()


async def run_scheduler(slugs: list[str] | None = None, platform: PlatformConfig | None = None) -> None:
    await run_role(serve_scheduler, slugs, platform, role_name="scheduler")
