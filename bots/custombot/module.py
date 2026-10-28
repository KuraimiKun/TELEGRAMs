"""No-code custom bot template: pages, buttons, links and commands built from inside the bot. Factory-only."""

from __future__ import annotations

from pathlib import Path

from aiogram import Router

from bots.custombot import handlers
from bots.custombot.config import CustomEnv
from bots.custombot.service import PageService
from bots.custombot.settings import CustomSettings
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.sdk.module import BotModule


class CustomBot(BotModule):
    slug = "custombot"
    title = "Custom Bot"
    table_prefix = "cb_"
    standalone = False
    factory_template = "custom"
    features = {Feature.ADMIN, Feature.LANG, Feature.BROADCAST}
    child_features = {Feature.ADMIN, Feature.LANG, Feature.BROADCAST}
    env_model = CustomEnv
    settings_model = CustomSettings
    locales_dir = Path(__file__).resolve().parent / "locales"

    async def setup(self, ctx: BotContext) -> None:
        ctx.extras["pages"] = PageService(ctx.sm, ctx.bot_id)

    def routers(self, ctx: BotContext) -> list[Router]:
        return [handlers.build_router(ctx)]
