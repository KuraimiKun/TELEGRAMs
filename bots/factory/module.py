"""Bot Factory: anyone can launch their own bot from a template in a minute — hosted by this platform.

Viral loop: every bot made here carries "Made with @factory" (removable with VIP), its visitors land on
the factory through an attributed deep link, and the public gallery promotes the best user bots.
"""

from __future__ import annotations

from pathlib import Path

from aiogram import Router

from bots.factory import admin, handlers
from bots.factory.config import FactoryEnv
from bots.factory.settings import FactorySettings
from core.factory.children import ChildService
from core.log import get_logger
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.sdk.module import AdminSection, BotModule, CommandSpec, PlanSpec, StatLine
from core.sdk.registry import factory_templates

log = get_logger(__name__)


class FactoryBot(BotModule):
    slug = "factory"
    title = "Bot Factory"
    table_prefix = "fac_"
    features = {
        Feature.ADMIN, Feature.LANG, Feature.VIP, Feature.REFERRAL, Feature.BROADCAST, Feature.FORCE_SUB,
        Feature.DAILY_STATS,
    }
    env_model = FactoryEnv
    settings_model = FactorySettings
    locales_dir = Path(__file__).resolve().parent / "locales"
    default_plans = [
        PlanSpec(name="1 Month Pro", days=30, stars=150, sort=1),
        PlanSpec(name="1 Year Pro", days=365, stars=1200, sort=2),
    ]

    async def setup(self, ctx: BotContext) -> None:
        if ctx.platform.factory_secret_key is None:
            log.warning("factory_secret_missing", hint="set FACTORY_SECRET_KEY to let users create bots")
        ctx.extras["children"] = ChildService(
            ctx.sm, ctx.redis, ctx.platform, factory_bot_id=ctx.bot_id, templates=set(factory_templates()),
            session=ctx.bot.session,
        )

    def routers(self, ctx: BotContext) -> list[Router]:
        return [handlers.build_router(ctx)]

    def commands(self) -> list[CommandSpec]:
        return [
            CommandSpec("newbot", "Create a bot"),
            CommandSpec("mybots", "Your bots"),
            CommandSpec("top", "Gallery of bots"),
        ]

    def admin_sections(self) -> list[AdminSection]:
        return [AdminSection(tab=admin.TAB, title="fac-btn-admin-tab", router_factory=admin.build_router)]

    async def stats(self, ctx: BotContext) -> list[StatLine]:
        totals = await ctx.extras["children"].totals()
        active = sum(v for k, v in totals.items() if k.endswith(":active"))
        return [
            StatLine("Factory", "Bots created", f"{sum(totals.values()):,}"),
            StatLine("Factory", "Active bots", f"{active:,}"),
        ]

    async def vip_info(self, ctx: BotContext) -> dict:
        stg = await ctx.settings.get()
        assert isinstance(stg, FactorySettings)
        return {"vip_bots": str(stg.vip_bots), "free_bots": str(stg.free_bots)}
