"""One code path for turning a user request into a delivered file or a queued job.

Used by the link handler, format/playlist pickers, search results, inline mode and force-sub replay so
every entry point applies the same limits, quota accounting, caching and concurrency rules.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, Field

from bots.socialdownload.engine.cache import MediaCache, request_key
from bots.socialdownload.engine.limits import TierPolicy, policy_for
from bots.socialdownload.engine.queue import Job, JobQueue
from bots.socialdownload.services.downloads import DownloadStatsService
from bots.socialdownload.services.quota import QuotaService, seconds_until_reset
from bots.socialdownload.settings import SocialDownloadSettings
from bots.socialdownload.uploader import TelegramUploader
from core.db.models import BotUser
from core.log import get_logger
from core.sdk.actions import record_user_action
from core.sdk.context import BotContext

log = get_logger(__name__)

PENDING_TTL = 30 * 60


class PendingRequest(BaseModel):
    """A link waiting for the user to pick a format / playlist option. Bound to its owner."""

    user_id: int
    chat_id: int
    chat_type: str = "private"
    reply_to: int | None = None
    url: str
    platform: str
    title: str = ""
    audio_format: str = "mp3"
    entries: int = 0
    created_at: float = Field(default_factory=time.time)


class Outcome(StrEnum):
    QUEUED = "queued"
    DELIVERED = "delivered"  # served from cache instantly
    LIMIT = "limit"  # daily quota exhausted
    BUSY = "busy"  # too many active jobs
    LOCKED = "locked"  # quality not allowed on this plan


@dataclass(slots=True)
class SubmitResult:
    outcome: Outcome
    position: int = 0
    job: Job | None = None
    policy: TierPolicy | None = None
    active: int = 0

    def limit_reset(self) -> tuple[int, int]:
        secs = seconds_until_reset()
        return secs // 3600, (secs % 3600) // 60


class DownloadService:
    def __init__(self, ctx: BotContext) -> None:
        self.ctx = ctx
        self.queue: JobQueue = ctx.extras["queue"]
        self.quota: QuotaService = ctx.extras["quota"]
        self.cache: MediaCache = ctx.extras["cache"]
        self.uploader: TelegramUploader = ctx.extras["uploader"]
        self.stats: DownloadStatsService = ctx.extras["download_stats"]

    async def settings(self) -> SocialDownloadSettings:
        return await self.ctx.settings.get()

    # ------------------------------------------------------------------ pending menus
    async def save_pending(self, req: PendingRequest) -> str:
        token = secrets.token_hex(6)
        await self.ctx.redis.set(self.ctx.keys("pending", token), req.model_dump_json(), ex=PENDING_TTL)
        return token

    async def load_pending(self, token: str) -> PendingRequest | None:
        raw = await self.ctx.redis.get(self.ctx.keys("pending", token))
        return PendingRequest.model_validate_json(raw) if raw else None

    async def drop_pending(self, token: str) -> None:
        await self.ctx.redis.delete(self.ctx.keys("pending", token))

    # ------------------------------------------------------------------ submit
    async def submit(
        self,
        *,
        user: BotUser,
        chat_id: int,
        chat_type: str,
        url: str,
        platform: str,
        kind: str,
        height: int | None = None,
        audio_format: str = "mp3",
        playlist_count: int | None = None,
        reply_to: int | None = None,
        status_msg_id: int | None = None,
        inline_message_id: str | None = None,
        lang: str = "en",
    ) -> SubmitResult:
        stg = await self.settings()
        policy = policy_for(user.is_vip(), stg)

        if kind == "video" and height and height > policy.max_height:
            return SubmitResult(Outcome.LOCKED, policy=policy)
        h = 0 if kind == "audio" else min(height or policy.max_height, policy.max_height)

        items: str | None = None
        units = 1
        if playlist_count:
            n = max(1, min(playlist_count, policy.playlist_max))
            items = f"1-{n}"
            units = n if stg.playlist_charge_per_item else 1
        ckey = request_key(url, kind, h, audio_format, items)

        active = await self.queue.active_count(user.user_id)
        if active >= policy.concurrent:
            return SubmitResult(Outcome.BUSY, policy=policy, active=active)

        units = min(units, policy.daily_limit)
        day = await self.quota.consume(user.user_id, policy.daily_limit, units)
        if day is None:
            return SubmitResult(Outcome.LIMIT, policy=policy)

        job = Job(
            user_id=user.user_id,
            chat_id=chat_id,
            chat_type=chat_type,
            reply_to=reply_to,
            status_msg_id=status_msg_id,
            inline_message_id=inline_message_id,
            url=url,
            platform=platform,
            kind=kind,
            max_height=h or policy.max_height,
            max_bytes=self.uploader.effective_max_bytes(policy.max_bytes, policy.direct_links),
            max_duration_s=policy.max_duration_s,
            max_items=policy.playlist_max,
            playlist_items=items,
            priority=policy.priority,
            is_vip=policy.is_vip,
            direct_links=policy.direct_links,
            lang=lang,
            caption=user.pref("caption", True),
            sponsor=stg.sponsor_text if policy.show_sponsor else None,
            audio_format=audio_format,
            cache_key=ckey,
            quality_label="audio" if kind == "audio" else ("playlist" if items else f"{h}p"),
            quota_units=units,
            quota_day=day,
        )

        # Instant delivery from the file_id cache (no queue slot needed).
        if inline_message_id is None:
            cached = await self.cache.get(ckey)
            if cached:
                ok = await self.uploader.deliver_cached(
                    chat_id, cached, job, self.ctx.username or "bot", reply_to=reply_to, cache_key=ckey
                )
                if ok:
                    await self.record_success(job, from_cache=True)
                    return SubmitResult(Outcome.DELIVERED, job=job, policy=policy)

        position = await self.queue.enqueue(job, max_active=policy.concurrent)
        if position < 0:
            await self.quota.refund(user.user_id, units, day, token=job.id)
            return SubmitResult(Outcome.BUSY, policy=policy, active=policy.concurrent)
        job.shown_position = position
        await self.queue.save(job)
        return SubmitResult(Outcome.QUEUED, position=position, job=job, policy=policy)

    # ------------------------------------------------------------------ bookkeeping
    async def refund(self, job: Job) -> None:
        """Give the job's quota back — at most once per job, to the day it was charged."""
        await self.quota.refund(job.user_id, job.quota_units, job.quota_day, token=job.id)

    async def record_success(
        self,
        job: Job,
        *,
        from_cache: bool,
        size_bytes: int | None = None,
        duration_ms: int | None = None,
    ) -> None:
        """Stats + referral bookkeeping after a delivery. Never raises: the user already has the file."""
        try:
            await self.stats.record_download(
                user_id=job.user_id,
                platform=job.platform,
                url=job.url,
                quality=job.quality_label,
                status="ok",
                from_cache=from_cache,
                size_bytes=size_bytes,
                duration_ms=duration_ms,
                is_vip=job.is_vip,
            )
        except Exception as e:
            log.exception("record_download_failed", job_id=job.id, error=str(e))
        await record_user_action(self.ctx, job.user_id)

    async def record_failure(self, job: Job, code: str) -> None:
        try:
            await self.stats.record_download(
                user_id=job.user_id,
                platform=job.platform,
                url=job.url,
                quality=job.quality_label,
                status="failed",
                error_code=code,
                is_vip=job.is_vip,
            )
        except Exception as e:
            log.exception("record_download_failed", job_id=job.id, error=str(e))
