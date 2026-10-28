"""Document worker queue and aggregate usage in the core admin panel."""

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bots.doctools.service import DocToolsService
from core.callback_data import AdminNavCb
from core.i18n import Translate
from core.routers.admin.common import admin_router, back_row, markup, nav, show
from core.sdk.context import BotContext


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "doctools")
    service: DocToolsService = ctx.extras["doctools"]

    @router.callback_query(AdminNavCb.filter(F.tab == "doctools"))
    async def overview(query: CallbackQuery, t: Translate) -> None:
        totals = await service.totals()
        await show(query, t("dt-admin", **totals),
                   markup([nav("doctools", t("btn-adm-refresh"))], back_row(t)))

    return router
