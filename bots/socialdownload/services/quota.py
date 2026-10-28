"""Daily download quota (the generic core ``DailyQuota`` under the bot's ``quota`` keys)."""

from __future__ import annotations

from redis.asyncio import Redis

from core.redis import KeySpace
from core.sdk.quota import KEY_TTL, DailyQuota, seconds_until_reset, today

__all__ = ["KEY_TTL", "QuotaService", "seconds_until_reset", "today"]


class QuotaService(DailyQuota):
    def __init__(self, redis: Redis, keys: KeySpace | None = None) -> None:
        super().__init__(redis, keys or KeySpace("socialdownload"), "quota")
