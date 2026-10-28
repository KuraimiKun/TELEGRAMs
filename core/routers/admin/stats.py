"""Admin stats dashboard."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from core.callback_data import AdminNavCb
from core.i18n import Translate
from core.routers.admin.common import admin_router, back_row, markup, nav, show
from core.sdk.context import BotContext
from core.ui.text import esc, kv


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "stats")

    @router.callback_query(AdminNavCb.filter(F.tab == "stats"))
    async def stats_view(query: CallbackQuery, t: Translate) -> None:
        d = await ctx.stats.get_overview()
        text = t(
            "adm-stats",
            bot=esc(ctx.module.title),
            users=f"{d['total_users']:,}",
            active24=f"{d['active_24h']:,}",
            active7=f"{d['active_7d']:,}",
            vip=f"{d['vip_users']:,}",
            actions=f"{d['total_actions']:,}",
            groups=f"{await ctx.groups.count_active():,}",
            revenue=f"{d['revenue_total']:,}",
            revenue30=f"{d['revenue_30d']:,}",
        )
        sections: dict[str, list[str]] = {}
        for line in await ctx.module.stats(ctx):
            sections.setdefault(line.section, []).append(kv(esc(line.label), esc(line.value)))
        for name, lines in sections.items():
            text += f"\n\n📈 <b>{esc(name)}</b>\n" + "\n".join(lines)
        await show(query, text, markup([nav("stats", t("btn-adm-refresh"))], back_row(t)))

    return router
