"""Anonymous Inbox: share a personal link, receive anonymous messages, reply anonymously.

Viral loop: every sender is invited to get their own link; story cards and inline sharing put links in
bios, stories and group chats. Also offered by the bot factory as the "anonymous" template, where a
user-created bot is a single branded inbox for its owner.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from aiogram import Router

from bots.anonymous import admin
from bots.anonymous.config import AnonEnv
from bots.anonymous.handlers import main
from bots.anonymous.jobs import daily_prompt
from bots.anonymous.service import AnonService
from bots.anonymous.settings import AnonSettings
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.sdk.module import AdminSection, BotModule, CommandSpec, PlanSpec, ScheduledJob, StatLine


class AnonymousBot(BotModule):
    slug = "anonymous"
    title = "Anonymous Inbox"
    table_prefix = "anon_"
    features = {
        Feature.ADMIN, Feature.LANG, Feature.VIP, Feature.REFERRAL, Feature.BROADCAST, Feature.FORCE_SUB,
        Feature.DAILY_STATS,
    }
    child_features = {Feature.ADMIN, Feature.LANG, Feature.BROADCAST}
    factory_template = "anonymous"
    env_model = AnonEnv
    settings_model = AnonSettings
    locales_dir = Path(__file__).resolve().parent / "locales"
    default_plans = [
        PlanSpec(name="1 Week VIP", days=7, stars=25, sort=1),
        PlanSpec(name="1 Month VIP", days=30, stars=75, sort=2),
    ]

    async def setup(self, ctx: BotContext) -> None:
        ctx.extras["anon"] = AnonService(ctx.sm, ctx.bot_id)

    def routers(self, ctx: BotContext) -> list[Router]:
        return [main.build_router(ctx)]

    def commands(self) -> list[CommandSpec]:
        return [
            CommandSpec("link", "Your anonymous link"),
            CommandSpec("stats", "Inbox stats"),
            CommandSpec("help", "How it works"),
        ]

    def admin_sections(self) -> list[AdminSection]:
        return [AdminSection(tab=admin.TAB, title="anon-btn-admin-tab", router_factory=admin.build_router)]

    def scheduled_jobs(self) -> list[ScheduledJob]:
        return [ScheduledJob("daily_prompt", timedelta(minutes=10), daily_prompt, timeout=timedelta(minutes=30))]

    async def stats(self, ctx: BotContext) -> list[StatLine]:
        totals = await ctx.extras["anon"].totals()
        return [
            StatLine("Inbox", "Links", f"{totals['links']:,}"),
            StatLine("Inbox", "Messages (24h)", f"{totals['today']:,}"),
            StatLine("Inbox", "Messages (total)", f"{totals['messages']:,}"),
            StatLine("Inbox", "Reports", f"{totals['reports']:,}"),
        ]

    async def vip_info(self, ctx: BotContext) -> dict:
        stg = await ctx.settings.get()
        assert isinstance(stg, AnonSettings)
        return {"vip_daily": str(stg.vip_daily_messages), "free_daily": str(stg.free_daily_messages)}

