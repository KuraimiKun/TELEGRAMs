"""Notes admin tab: storage overview."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bots.notes.service import NotesService
from core.callback_data import AdminNavCb
from core.i18n import Translate
from core.routers.admin.common import admin_router, back_row, markup, nav, show
from core.sdk.context import BotContext


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "notes")
    svc: NotesService = ctx.extras["notes"]

    @router.callback_query(AdminNavCb.filter(F.tab == "notes"))
    async def overview(query: CallbackQuery, t: Translate) -> None:
        totals = await svc.totals()
        await show(query, t("notes-adm", **totals), markup([nav("notes", t("btn-adm-refresh"))], back_row(t)))

    return router
