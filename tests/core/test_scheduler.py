from __future__ import annotations

import asyncio
from datetime import timedelta

from sqlalchemy import update

from core.db.base import utcnow
from core.db.models import BotUser
from core.runtime.scheduler import CentralScheduler, _Job, every, vip_notices


async def _member(ctx, user_id: int, vip_in: timedelta | None) -> None:
    await ctx.users.get_or_create(user_id, language_code="en")
    if vip_in is not None:
        async with ctx.sm() as s:
            await s.execute(
                update(BotUser)
                .where(BotUser.bot_id == ctx.bot_id, BotUser.user_id == user_id)
                .values(vip_until=utcnow() + vip_in)
            )
            await s.commit()


async def test_vip_notices_are_sent_exactly_once(ctx, api):
    await _member(ctx, 1, timedelta(days=2))  # expiring soon
    await _member(ctx, 2, timedelta(hours=-3))  # just expired
    await _member(ctx, 3, timedelta(days=30))  # not due
    await _member(ctx, 4, None)  # never VIP

    await vip_notices(ctx)
    first = [(m.chat_id, m.text) for m in api.calls("SendMessage")]
    assert sorted(c for c, _ in first) == [1, 2]

    api.requests.clear()
    await vip_notices(ctx)  # second run: nothing new
    assert api.calls("SendMessage") == []


async def test_vip_notice_resent_after_renewal_cycle(ctx, api):
    await _member(ctx, 5, timedelta(days=1))
    await vip_notices(ctx)
    assert len(api.calls("SendMessage")) == 1

    # User renews, then the new period nears its end again -> a fresh notice is due.
    await ctx.subs.grant_vip(5, 1)
    api.requests.clear()
    await vip_notices(ctx)
    assert len(api.calls("SendMessage")) == 1


async def test_job_runs_once_per_interval_across_replicas(ctx):
    runs = 0

    async def handler(_ctx) -> None:
        nonlocal runs
        runs += 1

    job = _Job("t", handler, every(timedelta(hours=1)), timeout=5)
    stop = asyncio.Event()
    a, b = CentralScheduler([ctx], stop), CentralScheduler([ctx], stop)
    tasks = [asyncio.create_task(s._job_loop(s._ctx_target(ctx, job), job)) for s in (a, b)]
    await asyncio.sleep(0.3)
    stop.set()
    await asyncio.gather(*tasks)
    assert runs == 1

    # A restarted scheduler respects the stored next-run time.
    stop2 = asyncio.Event()
    t = asyncio.create_task(CentralScheduler([ctx], stop2)._job_loop(CentralScheduler._ctx_target(ctx, job), job))
    await asyncio.sleep(0.2)
    stop2.set()
    await t
    assert runs == 1


async def test_failing_job_backs_off_and_releases_lock(ctx):
    async def boom(_ctx) -> None:
        raise RuntimeError("x")

    job = _Job("bad", boom, every(timedelta(seconds=1)), timeout=5)
    stop = asyncio.Event()
    t = asyncio.create_task(CentralScheduler([ctx], stop)._job_loop(CentralScheduler._ctx_target(ctx, job), job))
    await asyncio.sleep(0.2)
    stop.set()
    await t
    assert await ctx.redis.get(ctx.keys("sched", "lock", "bad")) is None
