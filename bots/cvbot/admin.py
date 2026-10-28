from aiogram import F, Router
from aiogram.types import CallbackQuery

from bots.cvbot.service import CVService
from core.callback_data import AdminNavCb
from core.i18n import Translate
from core.routers.admin.common import admin_router, back_row, markup, nav, show
from core.sdk.context import BotContext


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "cv")
    service: CVService = ctx.extras["cv"]

    @router.callback_query(AdminNavCb.filter(F.tab == "cv"))
    async def overview(query: CallbackQuery, t: Translate) -> None:
        await show(query, t("cv-admin", **await service.totals()), markup([nav("cv", t("btn-adm-refresh"))], back_row(t)))

    return router
