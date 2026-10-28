"""Periodic cleanup of abandoned download work dirs and expired direct-link files."""

from __future__ import annotations

import asyncio
import shutil
import time
from pathlib import Path

from bots.socialdownload.config import SocialDownloadEnv
from bots.socialdownload.engine.queue import JobQueue
from core.log import get_logger
from core.sdk.context import BotContext

log = get_logger(__name__)

STALE_WORKDIR_SECONDS = 2 * 3600


def _newest_mtime(path: Path) -> float:
    """Most recent modification anywhere inside ``path`` (a long download keeps touching its .part file)."""
    newest = path.stat().st_mtime
    for p in path.rglob("*"):
        try:
            newest = max(newest, p.stat().st_mtime)
        except FileNotFoundError:
            continue
    return newest


def _sweep(downloads: Path, public: Path, active_ids: set[str], public_ttl: int, now: float) -> tuple[int, int]:
    removed_dirs = removed_files = 0
    if downloads.exists():
        for item in downloads.iterdir():
            try:
                if not item.is_dir() or item.name in active_ids:
                    continue
                if now - _newest_mtime(item) > STALE_WORKDIR_SECONDS:
                    shutil.rmtree(item, ignore_errors=True)
                    removed_dirs += 1
            except Exception as e:
                log.warning("cleanup_download_failed", path=str(item), error=str(e))
    if public.exists():
        for file in public.iterdir():
            try:
                # Published files get mtime = publication time (see uploader._publish_file).
                if file.is_file() and now - file.stat().st_mtime > public_ttl:
                    file.unlink(missing_ok=True)
                    removed_files += 1
            except Exception as e:
                log.warning("cleanup_public_failed", path=str(file), error=str(e))
    return removed_dirs, removed_files


async def run_cleanup(ctx: BotContext) -> None:
    env: SocialDownloadEnv = ctx.env  # type: ignore[assignment]
    queue: JobQueue = ctx.extras["queue"]
    active = {i.decode() if isinstance(i, bytes) else str(i) for i in await ctx.redis.zrange(queue.inflight, 0, -1)}
    dirs, files = await asyncio.to_thread(
        _sweep, env.downloads_dir, env.public_dir, active, env.direct_link_ttl_seconds, time.time()
    )
    if dirs or files:
        log.info("cleanup_done", workdirs=dirs, public_files=files)
