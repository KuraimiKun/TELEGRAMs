"""Per-user daily quotas stored in Redis (atomic, auto-expiring, exactly-once refunds).

Used by bots for anything rationed per day: downloads, AI analyses, anonymous messages, document jobs.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis

from core.redis import KeySpace

KEY_TTL = 2 * 86400

# Atomically add ARGV[3] units if the result stays within the limit. Returns the new count, or -1.
_CONSUME_LUA = """
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
local units = tonumber(ARGV[3])
if current + units > tonumber(ARGV[1]) then
  return -1
end
current = redis.call('INCRBY', KEYS[1], units)
redis.call('EXPIRE', KEYS[1], ARGV[2])
return current
"""

# Refund once per job: KEYS[1] quota key, KEYS[2] refund marker. ARGV[1] units, ARGV[2] ttl. Returns 1/0.
_REFUND_LUA = """
if redis.call('SET', KEYS[2], '1', 'NX', 'EX', ARGV[2]) == false then
  return 0
end
local v = redis.call('DECRBY', KEYS[1], ARGV[1])
if v < 0 then redis.call('SET', KEYS[1], 0, 'EX', ARGV[2]) end
return 1
"""


def seconds_until_reset(now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(1, int((tomorrow - now).total_seconds()))


def today(now: datetime | None = None) -> str:
    return f"{(now or datetime.now(UTC)):%Y%m%d}"


class DailyQuota:
    """A named daily counter per user: ``DailyQuota(ctx.redis, ctx.keys, "cv")``."""

    def __init__(self, redis: Redis, keys: KeySpace, name: str = "quota") -> None:
        self.redis = redis
        self.keys = keys
        self.name = name

    def _key(self, user_id: int, day: str | None = None) -> str:
        return self.keys(self.name, user_id, day or today())

    async def used(self, user_id: int) -> int:
        value = await self.redis.get(self._key(user_id))
        return int(value or 0)

    async def consume(self, user_id: int, limit: int, units: int = 1) -> str | None:
        """Charge ``units`` against today's limit. Returns the charged day (for refunds) or None if over."""
        day = today()
        result = await self.redis.eval(_CONSUME_LUA, 1, self._key(user_id, day), limit, KEY_TTL, max(1, units))
        return day if int(result) != -1 else None

    async def refund(self, user_id: int, units: int = 1, day: str | None = None, token: str | None = None) -> bool:
        """Give units back to the day they were charged. With ``token`` (e.g. a job id) it happens at most once."""
        marker = self.keys(f"{self.name}_refunded" if self.name != "quota" else "refunded", token or f"anon:{user_id}:{datetime.now(UTC).timestamp()}")
        res = await self.redis.eval(_REFUND_LUA, 2, self._key(user_id, day), marker, max(1, units), KEY_TTL)
        return int(res) == 1

    async def reset(self, user_id: int) -> None:
        await self.redis.delete(self._key(user_id))

    async def remaining(self, user_id: int, limit: int) -> int:
        return max(0, limit - await self.used(user_id))
