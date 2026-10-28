from datetime import timedelta
from pathlib import Path

from aiogram import Router

from bots.cvbot import admin
from bots.cvbot.config import CVBotEnv
from bots.cvbot.payments import PREFIX, ProReviews
from bots.cvbot.service import CVService
from bots.cvbot.settings import CVSettings
from core.db.models import BotUser
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.sdk.module import AdminSection, BotModule, CommandSpec, PlanSpec, ScheduledJob, StatLine
from core.sdk.quota import DailyQuota


class CVBot(BotModule):
    slug = "cvbot"
    title = "CV Analyzer"
    table_prefix = "cv_"
    env_model = CVBotEnv
    settings_model = CVSettings
    features = {
        Feature.ADMIN, Feature.LANG, Feature.VIP, Feature.REFERRAL, Feature.FORCE_SUB,
        Feature.BROADCAST, Feature.DAILY_STATS,
    }
    locales_dir = Path(__file__).resolve().parent / "locales"
    default_plans = [PlanSpec(name="Monthly CV VIP", days=30, stars=100), PlanSpec(name="Yearly CV VIP", days=365, stars=750)]

    async def setup(self, ctx: BotContext) -> None:
        ctx.extras["cv"] = CVService(ctx)
        ctx.extras["cv_quota"] = DailyQuota(ctx.redis, ctx.keys, "cv_analysis")
        ctx.extras["cv_pro"] = ProReviews(ctx)
        ctx.extras["payment_payload_prefixes"] = (PREFIX,)

    def routers(self, ctx: BotContext) -> list[Router]:
        from bots.cvbot.handlers import build_router

        return [build_router(ctx)]

    def commands(self) -> list[CommandSpec]:
        return [CommandSpec(command, description) for command, description in [
            ("analyze", "Analyze your CV"), ("match", "Match a job description"),
            ("coverletter", "Write a cover letter"), ("linkedin", "Improve your LinkedIn profile"),
            ("export", "Export an improved CV PDF"), ("interview", "Practice a mock interview"),
            ("share", "Share your CV score"), ("forget", "Delete your CV reports"),
            ("pro", "Buy one Pro review"), ("cancel", "Cancel the current action"), ("help", "Help and privacy"),
        ]]

    def admin_sections(self) -> list[AdminSection]:
        return [AdminSection("cv", "cv-btn-admin", admin.build_router)]

    def scheduled_jobs(self) -> list[ScheduledJob]:
        return [ScheduledJob("cv_sessions", timedelta(seconds=60), _prune)]

    async def stats(self, ctx: BotContext) -> list[StatLine]:
        totals = await ctx.extras["cv"].totals()
        return [StatLine("CV", "Reports", totals["reports"]), StatLine("CV", "Average score", totals["average"])]

    async def reset_user_limits(self, ctx: BotContext, user_id: int) -> bool:
        await ctx.extras["cv_quota"].reset(user_id)
        return True

    async def vip_info(self, ctx: BotContext) -> dict:
        return {"free": (await ctx.settings.get()).free_analyses_per_day}

    async def on_force_sub_passed(self, ctx: BotContext, user: BotUser, payload: dict, chat_id: int) -> None:
        # Retain no CV text/file IDs in the force-sub replay payload.
        if payload.get("action") == "cv":
            lang = ctx.translator.resolve(user.lang)
            await ctx.bot.send_message(chat_id, ctx.translator.get(lang, "cv-start"))


async def _prune(ctx: BotContext) -> None:
    ctx.extras["cv"].prune()
