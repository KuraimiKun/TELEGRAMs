"""Operational jobs: warn admins when yt-dlp is outdated (the #1 cause of broken downloads)."""

from __future__ import annotations

import contextlib

import aiohttp
from yt_dlp.version import __version__ as YTDLP_VERSION

from bots.socialdownload.config import SocialDownloadEnv
from core.log import get_logger
from core.sdk.context import BotContext

log = get_logger(__name__)

PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"


def _parse(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in version.split(".") if p.isdigit())


async def latest_ytdlp_version() -> str | None:
    try:
        async with (
            aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session,
            session.get(PYPI_URL) as resp,
        ):
            resp.raise_for_status()
            return (await resp.json())["info"]["version"]
    except Exception as e:
        log.info("ytdlp_version_check_failed", error=str(e))
        return None


async def check_ytdlp_update(ctx: BotContext) -> None:
    env: SocialDownloadEnv = ctx.env  # type: ignore[assignment]
    if not env.ytdlp_update_alerts:
        return
    latest = await latest_ytdlp_version()
    if not latest or _parse(latest) <= _parse(YTDLP_VERSION):
        return
    marker = ctx.keys("ytdlp_alerted", latest)
    if not await ctx.redis.set(marker, "1", nx=True, ex=30 * 86400):
        return  # already announced this version
    log.warning("ytdlp_outdated", current=YTDLP_VERSION, latest=latest)
    recipients = [env.log_channel_id] if env.log_channel_id else list(env.admin_ids)
    text = ctx.translator.get(ctx.translator.default, "sd-ytdlp-update", latest=latest, current=YTDLP_VERSION)
    for chat_id in recipients:
        with contextlib.suppress(Exception):
            await ctx.bot.send_message(chat_id=chat_id, text=text)
