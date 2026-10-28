"""PDF, image, assignment and citation tools with a dedicated worker."""

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from aiogram import Router
from aiogram.types import Message, TelegramObject

from bots.doctools import admin, handlers
from bots.doctools.citations import CitationService
from bots.doctools.config import DocToolsEnv
from bots.doctools.queue import JobQueue
from bots.doctools.service import DocToolsService
from bots.doctools.settings import DocToolsSettings
from bots.doctools.worker import run_worker
from core.db.models import BotUser
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.sdk.module import AdminSection, BotModule, CommandSpec, PlanSpec, StatLine


class DocToolsBot(BotModule):
    slug = "doctools"
    title = "Student Document Tools"
    table_prefix = "dt_"
    features = {Feature.ADMIN, Feature.LANG, Feature.VIP, Feature.REFERRAL, Feature.FORCE_SUB,
                Feature.BROADCAST, Feature.DAILY_STATS}
    env_model = DocToolsEnv
    settings_model = DocToolsSettings
    locales_dir = Path(__file__).resolve().parent / "locales"
    default_plans = [PlanSpec("1 Month VIP", 30, 50, 1), PlanSpec("1 Year VIP", 365, 400, 2)]

    async def setup(self, ctx: BotContext) -> None:
        ctx.extras["doctools_queue"] = JobQueue(ctx.redis, ctx.keys)
        ctx.extras["doctools"] = DocToolsService(ctx)
        ctx.extras["citations"] = CitationService(ctx)

    def routers(self, ctx: BotContext) -> list[Router]:
        return [handlers.build_router(ctx)]

    def throttle_exempt(self, event: TelegramObject) -> bool:
        return (isinstance(event, Message) and event.chat.type == "private"
                and bool(event.document or event.photo)
                and not (event.text or event.caption or "").lstrip().startswith("/")
                and handlers.asset_from_message(event) is not None)

    def commands(self) -> list[CommandSpec]:
        return [CommandSpec("tools", "Your file basket"), CommandSpec("cite", "Format a DOI, ISBN or URL citation"),
                CommandSpec("count", "Count words, characters and pages"), CommandSpec("clear", "Clear your basket"),
                CommandSpec("help", "Document tools help")]

    def processes(self) -> dict[str, Callable[[BotContext], Awaitable[None]]]:
        return {"worker": run_worker}

    def admin_sections(self) -> list[AdminSection]:
        return [AdminSection("doctools", "dt-admin-tab", admin.build_router)]

    async def stats(self, ctx: BotContext) -> list[StatLine]:
        totals = await ctx.extras["doctools"].totals()
        return [StatLine("Documents", "Completed jobs", totals["ok"]),
                StatLine("Documents", "Failed jobs", totals["failed"])]

    async def vip_info(self, ctx: BotContext) -> dict[str, Any]:
        settings: DocToolsSettings = await ctx.settings.get()
        return {"size": settings.vip_max_mb, "pages": settings.vip_max_pages,
                "ai": settings.vip_ai_daily_limit}

    async def reset_user_limits(self, ctx: BotContext, user_id: int) -> bool:
        await ctx.extras["doctools"].quota.reset(user_id)
        return True

    async def on_force_sub_passed(self, ctx: BotContext, user: BotUser, payload: dict[str, Any], chat_id: int) -> None:
        operation = payload.get("operation")
        if isinstance(operation, str):
            await handlers.enqueue_action(ctx, user, chat_id, operation, options=payload.get("options"),
                                          reply_to=payload.get("reply_to"), gate=False)
