"""Anonymous inbox admin tab: activity and the latest reported messages (with a ban button)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bots.anonymous.keyboards import AnonCb
from bots.anonymous.service import AnonService
from core.callback_data import AdminNavCb
from core.i18n import Translate
from core.routers.admin.common import admin_router, back_row, btn, markup, nav, show
from core.sdk.context import BotContext
from core.ui.text import esc

TAB = "anon"


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "anon_admin")
    svc: AnonService = ctx.extras["anon"]

    @router.callback_query(AdminNavCb.filter(F.tab == TAB))
    async def overview(query: CallbackQuery, t: Translate) -> None:
        totals = await svc.totals()
        lines = [t("anon-adm", **{k: str(v) for k, v in totals.items()})]
        rows = []
        for msg in await svc.reported(8):
            snippet = esc((msg.text or msg.kind)[:60])
            lines.append(f"• #{msg.id} <code>{msg.sender_id}</code> — {snippet}")
            rows.append([btn(t("anon-btn-adm-ban", id=str(msg.id)), AnonCb(action="ban", id=msg.id).pack())])
        await show(query, "\n".join(lines), markup(*rows, [nav(TAB, t("btn-adm-refresh"))], back_row(t)))

    return router
