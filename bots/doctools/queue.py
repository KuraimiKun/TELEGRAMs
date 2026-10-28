"""Redis list queue with atomic leases, fencing and bounded crash recovery."""

from __future__ import annotations

import json
import secrets
import time
from collections.abc import Awaitable
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, field_validator
from redis.asyncio import Redis

from core.redis import KeySpace

JOB_TTL = 6 * 3600
LEASE_SECONDS = 90
MAX_ATTEMPTS = 3
DEAD_KEEP = 100


class DocAsset(BaseModel):
    message_id: int = Field(default=0, ge=0)
    file_id: str = ""
    file_name: str = "document.pdf"
    kind: Literal["pdf", "image", "docx", "text"] = "pdf"
    size_bytes: int = Field(default=0, ge=0)
    text: str | None = None


class Basket(BaseModel):
    user_id: int
    chat_id: int
    assets: list[DocAsset] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    callback_stamp: int = Field(default_factory=lambda: secrets.randbits(31))

    @field_validator("assets")
    @classmethod
    def _message_order(cls, assets: list[DocAsset]) -> list[DocAsset]:
        # Concurrent webhook handlers can append in completion order. Telegram IDs retain send order.
        return sorted(assets, key=lambda asset: asset.message_id) if all(asset.message_id for asset in assets) else assets


class Job(BaseModel):
    id: str = Field(default_factory=lambda: secrets.token_hex(8))
    user_id: int
    chat_id: int
    operation: str
    assets: list[DocAsset]
    options: dict[str, Any] = Field(default_factory=dict)
    lang: str = "en"
    is_vip: bool = False
    max_bytes: int = 20 * 1024 * 1024
    max_pages: int = 50
    reply_to: int | None = None
    quota_day: str | None = None
    created_at: float = Field(default_factory=time.time)
    attempts: int = 0
    lease_token: str = ""
    # Telegram polls can be resumed after worker failure without repeating acknowledged questions.
    delivered_items: int = 0
    ai_used: bool = False

    @field_validator("options", mode="before")
    @classmethod
    def _empty_options(cls, value: Any) -> Any:
        # Redis Lua cjson on some engines serializes an empty object as an empty array.
        return {} if value == [] else value


# Job existence is checked inside Lua, so enqueue races cannot exceed concurrency.
_ENQUEUE = """
local active = 0
for _, id in ipairs(redis.call('SMEMBERS', KEYS[2])) do
  if redis.call('EXISTS', ARGV[5] .. id) == 1 then active = active + 1
  else redis.call('SREM', KEYS[2], id) end
end
if active >= tonumber(ARGV[3]) then return -1 end
if redis.call('EXISTS', KEYS[1]) == 1 then return -1 end
redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[4])
redis.call('SADD', KEYS[2], ARGV[2])
redis.call('EXPIRE', KEYS[2], ARGV[4])
redis.call('RPUSH', KEYS[3], ARGV[2])
return redis.call('LLEN', KEYS[3])
"""

_POP = """
for i = 1, 2 do
  local id = redis.call('LPOP', KEYS[i])
  while id do
    local raw = redis.call('GET', ARGV[1] .. id)
    if raw then
      local job = cjson.decode(raw)
      job.lease_token = ARGV[3]
      raw = cjson.encode(job)
      redis.call('SET', ARGV[1] .. id, raw, 'EX', ARGV[5])
      redis.call('SET', ARGV[2] .. id, ARGV[3], 'EX', ARGV[5])
      redis.call('ZADD', KEYS[3], ARGV[4], id)
      return raw
    end
    id = redis.call('LPOP', KEYS[i])
  end
end
return false
"""

_HEARTBEAT = """
if redis.call('GET', KEYS[1]) ~= ARGV[1] then return 0 end
if not redis.call('ZSCORE', KEYS[2], ARGV[2]) then return 0 end
redis.call('ZADD', KEYS[2], ARGV[3], ARGV[2])
redis.call('EXPIRE', KEYS[3], ARGV[4])
redis.call('EXPIRE', KEYS[1], ARGV[4])
return 1
"""

_SAVE = """
if redis.call('GET', KEYS[2]) ~= ARGV[1] then return 0 end
redis.call('SET', KEYS[1], ARGV[2], 'EX', ARGV[3])
return 1
"""

_FINISH = """
local token = redis.call('GET', KEYS[2])
if token and token ~= ARGV[1] then return 0 end
if not token and ARGV[1] ~= '' then return 0 end
redis.call('ZREM', KEYS[3], ARGV[2])
redis.call('SREM', KEYS[4], ARGV[2])
redis.call('DEL', KEYS[1], KEYS[2])
return 1
"""

_REQUEUE = """
if redis.call('GET', KEYS[2]) ~= ARGV[1] then return 0 end
redis.call('SET', KEYS[1], ARGV[2], 'EX', ARGV[4])
redis.call('DEL', KEYS[2])
redis.call('ZREM', KEYS[3], ARGV[3])
redis.call('LPUSH', KEYS[4], ARGV[3])
return 1
"""

# Recovering under a fresh fencing token and lease closes the reaper crash window.
_CLAIM_EXPIRED = """
local score = redis.call('ZSCORE', KEYS[1], ARGV[1])
if not score or tonumber(score) > tonumber(ARGV[2]) then return false end
local raw = redis.call('GET', KEYS[2])
if not raw then redis.call('ZREM', KEYS[1], ARGV[1]); redis.call('DEL', KEYS[3]); return false end
local job = cjson.decode(raw)
job.lease_token = ARGV[3]
job.attempts = job.attempts + 1
raw = cjson.encode(job)
redis.call('SET', KEYS[2], raw, 'EX', ARGV[5])
redis.call('SET', KEYS[3], ARGV[3], 'EX', ARGV[5])
redis.call('ZADD', KEYS[1], ARGV[4], ARGV[1])
return raw
"""


class JobQueue:
    def __init__(self, redis: Redis, keys: KeySpace | None = None) -> None:
        self.redis = redis
        self.keys = keys or KeySpace("doctools")
        self.q_high = self.keys("dt", "q", "high")
        self.q_normal = self.keys("dt", "q", "normal")
        self.inflight = self.keys("dt", "inflight")
        self.dead = self.keys("dt", "dead")
        self._pops = 0

    def _job(self, id: str) -> str:
        return self.keys("dt", "job", id)

    def _lease(self, id: str) -> str:
        return self.keys("dt", "lease", id)

    def _queue(self, job: Job) -> str:
        return self.q_high if job.is_vip else self.q_normal

    async def _eval(self, script: str, numkeys: int, *args: Any) -> Any:
        # redis-py shares synchronous Lua stubs with its async client.
        return await cast(Awaitable[Any], self.redis.eval(script, numkeys, *args))

    async def get(self, job_id: str) -> Job | None:
        raw = await self.redis.get(self._job(job_id))
        return Job.model_validate_json(raw) if raw else None

    async def enqueue(self, job: Job, max_active: int = 2) -> int:
        return int(await self._eval(
            _ENQUEUE, 3, self._job(job.id), self.keys("dt", "user", job.user_id), self._queue(job),
            job.model_dump_json(), job.id, max_active, JOB_TTL, self.keys("dt", "job", ""),
        ))

    async def pop(self) -> Job | None:
        self._pops += 1
        order = (self.q_normal, self.q_high) if self._pops % 4 == 0 else (self.q_high, self.q_normal)
        raw = await self._eval(
            _POP, 3, *order, self.inflight, self.keys("dt", "job", ""), self.keys("dt", "lease", ""),
            secrets.token_hex(16), time.time() + LEASE_SECONDS, JOB_TTL,
        )
        return Job.model_validate_json(raw) if raw else None

    async def heartbeat(self, job: Job) -> bool:
        return bool(await self._eval(
            _HEARTBEAT, 3, self._lease(job.id), self.inflight, self._job(job.id),
            job.lease_token, job.id, time.time() + LEASE_SECONDS, JOB_TTL,
        ))

    async def save(self, job: Job) -> bool:
        return bool(await self._eval(
            _SAVE, 2, self._job(job.id), self._lease(job.id), job.lease_token, job.model_dump_json(), JOB_TTL,
        ))

    async def finish(self, job: Job) -> bool:
        return bool(await self._eval(
            _FINISH, 4, self._job(job.id), self._lease(job.id), self.inflight,
            self.keys("dt", "user", job.user_id), job.lease_token, job.id,
        ))

    async def requeue(self, job: Job, *, count_attempt: bool = False) -> bool:
        next_job = job.model_copy(update={"lease_token": "", "attempts": job.attempts + int(count_attempt)})
        return bool(await self._eval(
            _REQUEUE, 4, self._job(job.id), self._lease(job.id), self.inflight, self._queue(job),
            job.lease_token, next_job.model_dump_json(), job.id, JOB_TTL,
        ))

    async def reap(self, now: float | None = None) -> tuple[list[Job], list[Job]]:
        now = time.time() if now is None else now
        expired = await self.redis.zrangebyscore(self.inflight, "-inf", now)
        requeued: list[Job] = []
        exhausted: list[Job] = []
        for item in expired:
            job_id = item.decode() if isinstance(item, bytes) else item
            raw = await self._eval(
                _CLAIM_EXPIRED, 3, self.inflight, self._job(job_id), self._lease(job_id),
                job_id, now, secrets.token_hex(16), now + LEASE_SECONDS, JOB_TTL,
            )
            if not raw:
                continue
            job = Job.model_validate_json(raw)
            if job.attempts >= MAX_ATTEMPTS:
                exhausted.append(job)
            elif await self.requeue(job):
                requeued.append(job)
        return requeued, exhausted

    async def dead_letter(self, job: Job, reason: str) -> None:
        # Never retain file references, passwords, text, prompts or model responses.
        if await self.finish(job):
            payload = json.dumps({"id": job.id, "user_id": job.user_id, "operation": job.operation, "reason": reason})
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.lpush(self.dead, payload)
                pipe.ltrim(self.dead, 0, DEAD_KEEP - 1)
                pipe.expire(self.dead, JOB_TTL)
                await pipe.execute()

    async def depth(self) -> dict[str, int]:
        async with self.redis.pipeline(transaction=False) as pipe:
            pipe.llen(self.q_high)
            pipe.llen(self.q_normal)
            pipe.zcard(self.inflight)
            pipe.llen(self.dead)
            values = await pipe.execute()
        return dict(zip(("high", "normal", "inflight", "dead"), map(int, values), strict=True))

    reserve = pop
    complete = finish
