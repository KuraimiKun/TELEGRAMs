"""Telegram file_id cache + dedupe download locks.

Once any user downloads (url, quality), the resulting Telegram file_ids are cached so the same
request is answered instantly without re-downloading.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import asdict, dataclass, field

from redis.asyncio import Redis

from core.redis import KeySpace


@dataclass(slots=True)
class CachedItem:
    kind: str  # video | audio | photo | document | animation
    file_id: str


@dataclass(slots=True)
class CachedMedia:
    items: list[CachedItem]
    title: str = ""
    url: str = ""
    extra: dict = field(default_factory=dict)

    def dumps(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def loads(cls, raw: str | bytes) -> CachedMedia:
        data = json.loads(raw)
        items = [CachedItem(**i) for i in data.pop("items", [])]
        return cls(items=items, **data)


def media_key(url_norm: str, kind: str, height: int | str, items: str | None = None) -> str:
    """Cache key for a normalized URL + requested format."""
    raw = f"{url_norm}|{kind}|{height}|{items or ''}"
    return hashlib.sha1(raw.encode()).hexdigest()


def request_key(url_norm: str, kind: str, height: int, audio_format: str, items: str | None = None) -> str:
    """Cache key for a download request: audio is keyed by codec (mp3 != m4a), video by height."""
    return media_key(url_norm, kind, f"a:{audio_format}" if kind == "audio" else height, items)


class MediaCache:
    """Telegram file_id cache. Lives on the evictable cache Redis (losing an entry only costs a re-download)."""

    def __init__(self, redis: Redis, keys: KeySpace | None = None, ttl_days: int = 30) -> None:
        self.redis = redis
        self.keys = keys or KeySpace("socialdownload")
        self.ttl = ttl_days * 86400

    async def get(self, key: str) -> CachedMedia | None:
        raw = await self.redis.get(self.keys("fid", key))
        if not raw:
            return None
        try:
            return CachedMedia.loads(raw)
        except (ValueError, TypeError):
            await self.redis.delete(self.keys("fid", key))
            return None

    async def set(self, key: str, media: CachedMedia) -> None:
        if media.items:
            await self.redis.set(self.keys("fid", key), media.dumps(), ex=self.ttl)

    async def delete(self, key: str) -> None:
        await self.redis.delete(self.keys("fid", key))


_EXTEND = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('expire', KEYS[1], ARGV[2]) else return 0 end"
_RELEASE = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"


class DownloadLock:
    """Short-lease owner-token lock (on the durable Redis) so identical concurrent requests download once.

    The holder renews the lease while it works; if it dies the lease expires within ``LEASE`` seconds.
    """

    LEASE = 120

    def __init__(self, redis: Redis, keys: KeySpace | None = None) -> None:
        self.redis = redis
        self.keys = keys or KeySpace("socialdownload")

    def _key(self, cache_key: str) -> str:
        return self.keys("lock", "dl", cache_key)

    async def acquire(self, cache_key: str) -> str | None:
        token = secrets.token_hex(8)
        ok = await self.redis.set(self._key(cache_key), token, nx=True, ex=self.LEASE)
        return token if ok else None

    async def extend(self, cache_key: str, token: str) -> bool:
        return bool(await self.redis.eval(_EXTEND, 1, self._key(cache_key), token, self.LEASE))

    async def release(self, cache_key: str, token: str) -> bool:
        return bool(await self.redis.eval(_RELEASE, 1, self._key(cache_key), token))

    async def held(self, cache_key: str) -> bool:
        return bool(await self.redis.exists(self._key(cache_key)))
