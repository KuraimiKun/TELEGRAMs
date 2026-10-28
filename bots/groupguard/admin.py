"""Group Guard admin tab: protected groups and moderation activity."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bots.groupguard.service import GuardService
from core.callback_data import AdminNavCb
from core.i18n import Translate
from core.routers.admin.common import admin_router, back_row, markup, nav, show
from core.sdk.context import BotContext

TAB = "guard"


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "gg_admin")
    svc: GuardService = ctx.extras["guard"]

    @router.callback_query(AdminNavCb.filter(F.tab == TAB))
    async def overview(query: CallbackQuery, t: Translate) -> None:
        totals = await svc.totals()
        await show(query, t("gg-adm", **{k: str(v) for k, v in totals.items()}),
                   markup([nav(TAB, t("btn-adm-refresh"))], back_row(t)))

    return router
