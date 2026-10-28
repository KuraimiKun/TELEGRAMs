"""Feedback (contact) bot template: a Livegram-style inbox for the bot's owner. Factory-only."""

from __future__ import annotations

from pathlib import Path

from aiogram import Router

from bots.feedback import handlers
from bots.feedback.config import FeedbackEnv
from bots.feedback.settings import FeedbackSettings
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.sdk.module import BotModule


class FeedbackBot(BotModule):
    slug = "feedback"
    title = "Feedback Bot"
    table_prefix = "fb_"
    standalone = False
    factory_template = "feedback"
    features = {Feature.ADMIN, Feature.LANG, Feature.BROADCAST}
    child_features = {Feature.ADMIN, Feature.LANG, Feature.BROADCAST}
    env_model = FeedbackEnv
    settings_model = FeedbackSettings
    locales_dir = Path(__file__).resolve().parent / "locales"

    def routers(self, ctx: BotContext) -> list[Router]:
        return [handlers.build_router(ctx)]
