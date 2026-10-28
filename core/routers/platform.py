"""Cross-bot platform overview dashboard for super-admins (/platform)."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.filters import IsSuperAdmin
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.text import esc


def build_router(ctx: BotContext) -> Router:
    router = Router(name=f"core_platform_{ctx.slug}")
    router.message.filter(IsSuperAdmin())

    @router.message(Command("platform"))
    async def cmd_platform(message: Message, t: Translate) -> None:
        data = await ctx.stats.get_platform_overview()
        lines = [
            t(
                "plat-title",
                users=f"{data['total_global_users']:,}",
                bots=data["total_bots"],
                revenue=f"{data['total_revenue']:,}",
            ),
            "",
        ]
        for b in data["bots"]:
            name = f"@{b['username']}" if b["username"] else b["slug"]
            lines.append(
                t("plat-bot", title=esc(b["title"]), name=esc(name), users=f"{b['users']:,}", revenue=f"{b['revenue']:,}")
            )
        await message.answer("\n".join(lines))

    return router
