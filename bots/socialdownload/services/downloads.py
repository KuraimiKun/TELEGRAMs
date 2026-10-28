"""Download recording and analytics service for SocialDownload."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bots.socialdownload.models import Download
from core.db.base import utcnow


class DownloadStatsService:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sm = sessionmaker

    async def record_download(
        self,
        user_id: int,
        platform: str,
        url: str,
        quality: str,
        status: str,
        size_bytes: int | None = None,
        duration_ms: int | None = None,
        error_code: str | None = None,
        from_cache: bool = False,
        is_vip: bool = False,
    ) -> None:
        async with self.sm() as session:
            record = Download(
                user_id=user_id,
                platform=platform,
                url=url[:1024],
                quality=quality,
                status=status,
                size_bytes=size_bytes,
                duration_ms=duration_ms,
                error_code=error_code,
                from_cache=from_cache,
                is_vip=is_vip,
                created_at=utcnow(),
            )
            session.add(record)
            await session.commit()

    async def get_metrics(self) -> dict[str, Any]:
        """One aggregate query for the headline numbers + one for the platform breakdown."""
        now = utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        recent = Download.created_at >= day_ago
        async with self.sm() as session:
            row = (
                await session.execute(
                    select(
                        func.count(Download.id),
                        func.count(Download.id).filter(recent),
                        func.count(Download.id).filter(recent, Download.status == "failed"),
                        func.count(Download.id).filter(Download.from_cache.is_(True)),
                        func.coalesce(func.sum(Download.size_bytes).filter(Download.status == "ok"), 0),
                    )
                )
            ).one()
            top = (
                await session.execute(
                    select(Download.platform, func.count(Download.id).label("cnt"))
                    .where(Download.created_at >= week_ago)
                    .group_by(Download.platform)
                    .order_by(desc("cnt"))
                    .limit(5)
                )
            ).all()

        total, last_24h, failed_24h, cached, total_bytes = (int(v or 0) for v in row)
        return {
            "total_downloads": total,
            "dl_24h": last_24h,
            "success_rate_24h": 100.0 if last_24h == 0 else round((last_24h - failed_24h) * 100 / last_24h, 1),
            "cache_hit_ratio": 0.0 if total == 0 else round(cached * 100 / total, 1),
            "cached": cached,
            "total_bytes": total_bytes,
            "top_platforms": [(p, c) for p, c in top],
        }
