"""Crash-safe Redis job queue.

Layout (all keys namespaced per bot)::

    q:high / q:normal      LIST  job ids waiting to run (VIP / free)
    inflight               ZSET  job id -> lease deadline (unix seconds); renewed by heartbeats
    job:<id>               STR   Job JSON (TTL = JOB_TTL)
    ujobs:<user>           SET   a user's queued + running job ids (concurrency limit)
    cancel:<id>            STR   cancellation flag
    waiters:<cache_key>    LIST  jobs parked until an identical download finishes
    dead                   LIST  last DEAD_KEEP dead-lettered jobs (for the admin queue view)

A job is never lost: popping moves it atomically into ``inflight``; if its worker dies the lease expires
and :meth:`JobQueue.reap` re-queues it (up to ``MAX_ATTEMPTS``) or dead-letters it.
"""

from __future__ import annotations

import json
import re
import secrets
import time
from dataclasses import dataclass

from pydantic import BaseModel, Field
from redis.asyncio import Redis

from core.redis import KeySpace

JOB_TTL = 6 * 3600
LEASE_SECONDS = 90  # a worker must heartbeat within this window
PARK_SECONDS = 20 * 60  # max time a parked job waits for its leader before being re-queued
MAX_ATTEMPTS = 3
DEAD_KEEP = 500
JOB_ID_RE = re.compile(r"^[0-9a-f]{12,32}$")


def new_job_id() -> str:
    return secrets.token_hex(8)


class Job(BaseModel):
    id: str = Field(default_factory=new_job_id)
    user_id: int
    chat_id: int | None = None
    chat_type: str = "private"
    reply_to: int | None = None
    status_msg_id: int | None = None
    inline_message_id: str | None = None
    url: str
    platform: str
    kind: str = "video"  # video | audio
    max_height: int = 720
    max_bytes: int
    max_duration_s: int = 3600
    max_items: int = 10  # cap for multi-item posts (carousels / threads)
    playlist_items: str | None = None
    priority: str = "normal"
    is_vip: bool = False
    direct_links: bool = False
    lang: str = "en"
    caption: bool = True
    sponsor: str | None = None
    audio_format: str = "mp3"
    cache_key: str
    quality_label: str = "best"
    created_at: float = Field(default_factory=time.time)
    attempts: int = 0
    parked: bool = False  # waited behind an identical download (exempt from queue-age expiry)
    shown_position: int = 0  # last queue position shown to the user
    # Quota bookkeeping so refunds hit the day that was charged, exactly once.
    quota_units: int = 1
    quota_day: str | None = None


@dataclass(slots=True)
class CancelResult:
    found: bool
    removed_from_queue: bool = False


# KEYS: job, ujobs, queue   ARGV: job_json, job_id, limit, ttl, job_key_prefix
_ENQUEUE = """
local ids = redis.call('SMEMBERS', KEYS[2])
local active = 0
for _, id in ipairs(ids) do
  if redis.call('EXISTS', ARGV[5] .. id) == 1 then active = active + 1 else redis.call('SREM', KEYS[2], id) end
end
if tonumber(ARGV[3]) > 0 and active >= tonumber(ARGV[3]) then return -1 end
redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[4])
redis.call('SADD', KEYS[2], ARGV[2])
redis.call('EXPIRE', KEYS[2], ARGV[4])
redis.call('RPUSH', KEYS[3], ARGV[2])
return redis.call('LLEN', KEYS[3])
"""

# KEYS: first_queue, second_queue, inflight   ARGV: lease_deadline
_POP = """
for i = 1, 2 do
  local id = redis.call('LPOP', KEYS[i])
  if id then
    redis.call('ZADD', KEYS[3], ARGV[1], id)
    return id
  end
end
return false
"""

# KEYS: waiters   -> returns and clears the list atomically
_DRAIN = """
local ids = redis.call('LRANGE', KEYS[1], 0, -1)
redis.call('DEL', KEYS[1])
return ids
"""


def _s(v: bytes | str) -> str:
    return v.decode() if isinstance(v, bytes) else v


class JobQueue:
    def __init__(self, redis: Redis, keys: KeySpace | None = None) -> None:
        self.redis = redis
        self.keys = keys or KeySpace("socialdownload")
        self.q_high = self.keys("q", "high")
        self.q_normal = self.keys("q", "normal")
        self.queues = {"high": self.q_high, "normal": self.q_normal}
        self.inflight = self.keys("inflight")
        self.dead = self.keys("dead")
        self._pops = 0

    # ------------------------------------------------------------------ keys
    def _job_key(self, job_id: str) -> str:
        return self.keys("job", job_id)

    def _queue_of(self, job: Job) -> str:
        return self.queues.get(job.priority, self.q_normal)

    async def get(self, job_id: str) -> Job | None:
        raw = await self.redis.get(self._job_key(job_id))
        return Job.model_validate_json(raw) if raw else None

    async def save(self, job: Job) -> None:
        await self.redis.set(self._job_key(job.id), job.model_dump_json(), ex=JOB_TTL)

    # ------------------------------------------------------------------ produce
    async def enqueue(self, job: Job, max_active: int = 0) -> int:
        """Atomically enforce the user's concurrency limit and enqueue.

        Returns the 1-based queue position, or ``-1`` if the user already has ``max_active`` jobs.
        """
        res = await self.redis.eval(
            _ENQUEUE,
            3,
            self._job_key(job.id),
            self.keys("ujobs", job.user_id),
            self._queue_of(job),
            job.model_dump_json(),
            job.id,
            max_active,
            JOB_TTL,
            self.keys("job", ""),
        )
        if int(res) < 0:
            return -1
        return await self.position(job)

    async def position(self, job: Job) -> int:
        pos = await self.redis.lpos(self._queue_of(job), job.id)
        if pos is None:
            return 0
        ahead = 0 if job.priority == "high" else int(await self.redis.llen(self.q_high))
        return int(pos) + 1 + ahead

    # ------------------------------------------------------------------ consume
    async def pop(self) -> Job | None:
        """Lease the next job. Weighted fairness: every 4th pop prefers the free queue, so free users
        are never starved by a constant stream of VIP jobs."""
        self._pops += 1
        order = (self.q_normal, self.q_high) if self._pops % 4 == 0 else (self.q_high, self.q_normal)
        job_id = await self.redis.eval(_POP, 3, order[0], order[1], self.inflight, time.time() + LEASE_SECONDS)
        if not job_id:
            return None
        job = await self.get(_s(job_id))
        if job is None:  # expired or cancelled while queued
            await self.redis.zrem(self.inflight, job_id)
            return None
        return job

    async def heartbeat(self, job_id: str) -> None:
        await self.redis.zadd(self.inflight, {job_id: time.time() + LEASE_SECONDS}, xx=True)

    async def requeue(self, job: Job, *, count_attempt: bool) -> None:
        """Put a leased job back at the FRONT of its queue (shutdown / crash recovery)."""
        if count_attempt:
            job.attempts += 1
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.set(self._job_key(job.id), job.model_dump_json(), ex=JOB_TTL)
            pipe.zrem(self.inflight, job.id)
            pipe.lpush(self._queue_of(job), job.id)
            await pipe.execute()

    async def finish(self, job: Job) -> None:
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.zrem(self.inflight, job.id)
            pipe.srem(self.keys("ujobs", job.user_id), job.id)
            pipe.delete(self._job_key(job.id), self.keys("cancel", job.id))
            await pipe.execute()

    async def dead_letter(self, job: Job, reason: str) -> None:
        payload = json.dumps({"reason": reason, "at": int(time.time()), "job": job.model_dump(exclude={"sponsor"})})
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.lpush(self.dead, payload)
            pipe.ltrim(self.dead, 0, DEAD_KEEP - 1)
            await pipe.execute()
        await self.finish(job)

    # ------------------------------------------------------------------ dedupe followers
    async def park(self, job: Job, cache_key: str) -> None:
        """Wait (without holding a worker) until the job downloading the same media finishes."""
        job.parked = True
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.set(self._job_key(job.id), job.model_dump_json(), ex=JOB_TTL)
            pipe.zadd(self.inflight, {job.id: time.time() + PARK_SECONDS})
            pipe.rpush(self.keys("waiters", cache_key), job.id)
            pipe.expire(self.keys("waiters", cache_key), PARK_SECONDS)
            await pipe.execute()

    async def wake(self, cache_key: str) -> int:
        """Re-queue (at the front) every job parked on ``cache_key``. They will hit the cache."""
        ids = await self.redis.eval(_DRAIN, 1, self.keys("waiters", cache_key))
        woken = 0
        for raw in ids or []:
            job = await self.get(_s(raw))
            if job is None:
                await self.redis.zrem(self.inflight, raw)
                continue
            await self.requeue(job, count_attempt=False)
            woken += 1
        return woken

    # ------------------------------------------------------------------ recovery
    async def reap(self, now: float | None = None) -> tuple[list[Job], list[Job]]:
        """Recover jobs whose lease expired. Returns (requeued, exhausted). Exhausted jobs are left for the
        caller to refund/notify and then :meth:`dead_letter`."""
        expired = await self.redis.zrangebyscore(self.inflight, "-inf", now or time.time())
        requeued: list[Job] = []
        exhausted: list[Job] = []
        for raw in expired:
            # ZREM is the ownership test: only one reaper (across replicas) handles each job.
            if not await self.redis.zrem(self.inflight, raw):
                continue
            job = await self.get(_s(raw))
            if job is None:
                continue
            if job.attempts + 1 >= MAX_ATTEMPTS:
                exhausted.append(job)
                continue
            await self.requeue(job, count_attempt=True)
            requeued.append(job)
        return requeued, exhausted

    # ------------------------------------------------------------------ user-facing
    async def active_count(self, user_id: int) -> int:
        """Number of queued + running jobs for a user (stale ids are pruned)."""
        ids = await self.redis.smembers(self.keys("ujobs", user_id))
        if not ids:
            return 0
        ids_str = [_s(i) for i in ids]
        exists = await self.redis.mget([self._job_key(i) for i in ids_str])
        stale = [i for i, e in zip(ids_str, exists, strict=True) if e is None]
        if stale:
            await self.redis.srem(self.keys("ujobs", user_id), *stale)
        return len(ids_str) - len(stale)

    async def cancel(self, job_id: str, user_id: int) -> tuple[CancelResult, Job | None]:
        """Flag a job as cancelled. If it was still waiting in a queue it is removed right away
        (``removed_from_queue``) and the caller owns the refund; otherwise the worker handles it."""
        if not JOB_ID_RE.match(job_id):
            return CancelResult(found=False), None
        job = await self.get(job_id)
        if job is None or job.user_id != user_id:
            return CancelResult(found=False), None
        await self.redis.set(self.keys("cancel", job_id), 1, ex=JOB_TTL)
        removed = await self.redis.lrem(self._queue_of(job), 0, job_id)
        if removed:
            await self.finish(job)
        return CancelResult(found=True, removed_from_queue=bool(removed)), job

    async def is_cancelled(self, job_id: str) -> bool:
        return bool(await self.redis.exists(self.keys("cancel", job_id)))

    async def depth(self) -> dict[str, int]:
        async with self.redis.pipeline(transaction=False) as pipe:
            pipe.llen(self.q_high)
            pipe.llen(self.q_normal)
            pipe.zcard(self.inflight)
            pipe.llen(self.dead)
            high, normal, inflight, dead = await pipe.execute()
        return {"high": int(high), "normal": int(normal), "inflight": int(inflight), "dead": int(dead)}

    async def queued_jobs(self, limit: int = 50) -> list[Job]:
        """Head of both queues in service order (for live position updates)."""
        ids = [_s(i) for i in await self.redis.lrange(self.q_high, 0, limit - 1)]
        ids += [_s(i) for i in await self.redis.lrange(self.q_normal, 0, limit - 1)]
        jobs = []
        for i in ids:
            job = await self.get(i)
            if job:
                jobs.append(job)
        return jobs

    async def dead_jobs(self, limit: int = 20) -> list[str]:
        return [_s(r) for r in await self.redis.lrange(self.dead, 0, limit - 1)]

    async def purge_dead(self) -> int:
        n = int(await self.redis.llen(self.dead))
        await self.redis.delete(self.dead)
        return n
