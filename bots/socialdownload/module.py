"""SocialDownload bot module definition."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

from aiogram import Router

from bots.socialdownload.admin import downloads as admin_downloads
from bots.socialdownload.cleanup import run_cleanup
from bots.socialdownload.config import SocialDownloadEnv
from bots.socialdownload.engine.cache import DownloadLock, MediaCache
from bots.socialdownload.engine.network import CookieJar, ProxyPool
from bots.socialdownload.engine.queue import JobQueue
from bots.socialdownload.engine.ytdl import DownloadEngine
from bots.socialdownload.handlers import (
    callbacks,
    inline,
    link,
    profile,
    search,
    settings,
    start,
)
from bots.socialdownload.maintenance import check_ytdlp_update
from bots.socialdownload.services.downloads import DownloadStatsService
from bots.socialdownload.services.quota import QuotaService
from bots.socialdownload.services.requests import DownloadService
from bots.socialdownload.settings import SocialDownloadSettings
from bots.socialdownload.uploader import TelegramUploader
from bots.socialdownload.worker import run_worker
from core.config import MB
from core.db.models import BotUser
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.sdk.module import (
    AdminSection,
    BotModule,
    CommandSpec,
    PlanSpec,
    ScheduledJob,
    StatLine,
)
from core.ui.text import human_size


class SocialDownloadBot(BotModule):
    slug = "socialdownload"
    title = "Social Download Bot"
    table_prefix = "sd_"
    features = {
        Feature.ADMIN,
        Feature.VIP,
        Feature.LANG,
        Feature.BROADCAST,
        Feature.FORCE_SUB,
        Feature.REFERRAL,
        Feature.GROUPS,
        Feature.DAILY_STATS,
    }
    env_model = SocialDownloadEnv
    settings_model = SocialDownloadSettings
    locales_dir = Path(__file__).resolve().parent / "locales"

    default_plans = [
        PlanSpec(name="1 Month VIP", days=30, stars=150, sort=1),
        PlanSpec(name="3 Months VIP", days=90, stars=350, sort=2),
        PlanSpec(name="1 Year VIP", days=365, stars=1000, sort=3),
    ]

    async def setup(self, ctx: BotContext) -> None:
        env: SocialDownloadEnv = ctx.env  # type: ignore

        cache = MediaCache(ctx.cache_redis or ctx.redis, keys=ctx.keys, ttl_days=env.cache_ttl_days)
        queue = JobQueue(ctx.redis, keys=ctx.keys)
        quota = QuotaService(ctx.redis, keys=ctx.keys)
        download_stats = DownloadStatsService(ctx.sessionmaker)
        cookie_jar = CookieJar(env.cookies_dir, redis=ctx.redis, keys=ctx.keys)
        proxy_pool = ProxyPool(ctx.redis, env.proxies, file=env.proxies_file, keys=ctx.keys)

        engine = DownloadEngine(
            cookies=cookie_jar,
            proxies=proxy_pool,
            pot_provider_url=env.pot_provider_url,
        )
        uploader = TelegramUploader(
            bot=ctx.bot,
            cache=cache,
            max_upload_bytes=ctx.platform.max_upload_bytes,
            direct_link_base_url=env.direct_link_base_url,
            direct_link_secret=(
                ctx.platform.direct_link_secret.get_secret_value() if ctx.platform.direct_link_secret else None
            ),
            public_dir=env.public_dir,
            direct_link_ttl_seconds=env.direct_link_ttl_seconds,
        )

        ctx.extras["cache"] = cache
        ctx.extras["queue"] = queue
        ctx.extras["quota"] = quota
        ctx.extras["download_stats"] = download_stats
        ctx.extras["cookies"] = cookie_jar
        ctx.extras["proxies"] = proxy_pool
        ctx.extras["engine"] = engine
        ctx.extras["uploader"] = uploader
        ctx.extras["download_lock"] = DownloadLock(ctx.redis, keys=ctx.keys)
        ctx.extras["downloads"] = DownloadService(ctx)

    def routers(self, ctx: BotContext) -> list[Router]:
        return [
            start.build_router(ctx),
            settings.build_router(ctx),
            profile.build_router(ctx),
            callbacks.build_router(ctx),
            link.build_router(ctx),
            # Last among message handlers: plain text without a link becomes a search.
            search.build_router(ctx),
            inline.build_router(ctx),
        ]

    def commands(self) -> list[CommandSpec]:
        # /start, /vip, /referral, /lang, /terms and /support are registered by core (localized).
        return [
            CommandSpec("settings", "Quality, audio format and captions"),
            CommandSpec("profile", "Your plan, limits and stats"),
            CommandSpec("search", "Search YouTube videos"),
            CommandSpec("music", "Search and download music"),
            CommandSpec("help", "How to use this bot"),
        ]

    def admin_sections(self) -> list[AdminSection]:
        return [
            AdminSection(tab="downloads", title="sd-btn-admin-tab", router_factory=admin_downloads.build_router),
        ]

    def processes(self):
        return {
            "worker": run_worker,
        }

    def scheduled_jobs(self) -> list[ScheduledJob]:
        return [
            ScheduledJob(name="cleanup", interval=timedelta(minutes=10), handler=run_cleanup),
            ScheduledJob(name="ytdlp_update_check", interval=timedelta(hours=12), handler=check_ytdlp_update,
                         timeout=timedelta(minutes=1)),
        ]

    async def stats(self, ctx: BotContext) -> list[StatLine]:
        download_stats: DownloadStatsService = ctx.extras.get("download_stats") or DownloadStatsService(ctx.sessionmaker)
        m = await download_stats.get_metrics()
        queue: JobQueue = ctx.extras["queue"]
        depth = await queue.depth()
        lines = [
            StatLine("Downloads", "Total Downloads", f"{m['total_downloads']:,}"),
            StatLine("Downloads", "Last 24 Hours", f"{m['dl_24h']:,}"),
            StatLine("Downloads", "Success Rate (24h)", f"{m['success_rate_24h']:.1f}%"),
            StatLine("Downloads", "Cache Hit Ratio", f"{m['cache_hit_ratio']:.1f}%"),
            StatLine("Downloads", "Total Delivered", human_size(m["total_bytes"])),
            StatLine("Queue", "Waiting (VIP / free)", f"{depth['high']} / {depth['normal']}"),
            StatLine("Queue", "Running / dead-lettered", f"{depth['inflight']} / {depth['dead']}"),
        ]
        lines += [StatLine("Top platforms (7d)", p, f"{c:,}") for p, c in m["top_platforms"]]
        return lines

    async def reset_user_limits(self, ctx: BotContext, user_id: int) -> bool:
        quota: QuotaService = ctx.extras["quota"]
        await quota.reset(user_id)
        return True

    async def on_force_sub_passed(self, ctx: BotContext, user: BotUser, payload: dict[str, Any], chat_id: int) -> None:
        """The user joined the required channels: finish the download they asked for."""
        url = payload.get("url")
        if not url:
            return
        lang = ctx.translator.resolve(user.lang)

        def t(key: str, /, **kwargs: Any) -> str:
            return ctx.translator.get(lang, key, **kwargs)

        await link.process_link(
            ctx,
            user=user,
            lang=lang,
            t=t,
            chat_id=chat_id,
            chat_type=payload.get("chat_type", "private"),
            reply_to=payload.get("reply_to"),
            raw_url=url,
            check_subscription=False,
        )

    async def vip_info(self, ctx: BotContext) -> dict[str, Any]:
        stg: SocialDownloadSettings = await ctx.settings.get()
        uploader: TelegramUploader = ctx.extras["uploader"]
        vip_bytes = uploader.effective_max_bytes(stg.vip_max_mb * MB, stg.direct_links_enabled)
        return {
            "limit": stg.vip_daily_limit,
            "height": stg.vip_max_height,
            "size": human_size(vip_bytes),
            "concurrent": stg.vip_concurrent,
            "playlist": stg.vip_playlist_max,
            "free_limit": stg.free_daily_limit,
            "free_height": stg.free_max_height,
        }
