"""Read-only platform diagnostics; channel operators never gain platform administrator rights."""

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select

from bots.channelmanager.models import Inbox, Operation
from bots.channelmanager.service import ChannelService
from core.callback_data import AdminNavCb
from core.i18n import Translate
from core.routers.admin.common import admin_router, back_row, markup, nav, show
from core.sdk.context import BotContext
from core.ui.text import esc


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "channelmanager")

    @router.callback_query(AdminNavCb.filter(F.tab == "channelmanager"))
    async def diagnostics(query: CallbackQuery, t: Translate) -> None:
        svc: ChannelService = ctx.extras["channelmanager"]
        totals = await svc.totals()
        text = t("chm-admin", **totals) + "\n" + t("chm4-admin", collecting=totals["auto_collecting"],
            held=totals["auto_held"], failed=totals["auto_failed"], uncertain=totals["auto_uncertain"])
        text += "\n" + t("chm5-admin", pending=totals["members_pending"], held=totals["members_held"],
            uncertain=totals["members_uncertain"], cleanup=totals["members_cleanup"])
        from bots.channelmanager.diagnostics import snapshot
        text += "\n" + t("chm7-admin", **{k: str(v) for k, v in (await snapshot(ctx)).items()})
        async with ctx.sm() as session:
            rows = (await session.execute(select(Operation).where(Operation.bot_id == ctx.bot_id,
                Operation.status.in_({"failed", "uncertain"})).order_by(Operation.updated_at.desc()).limit(5))).scalars().all()
            inbox = (await session.execute(select(Inbox).where(Inbox.bot_id == ctx.bot_id,
                Inbox.status == "failed").order_by(Inbox.created_at.desc()).limit(5))).scalars().all()
        for row in rows:
            text += f"\n<code>{esc(row.id)}</code> · {esc(row.error_code or row.status)}"
        for receipt in inbox:
            text += "\n" + t("chm-admin-inbox-error", id=str(receipt.update_id), code=esc(receipt.error_code or "unknown"))
        await show(query, text, markup([nav("channelmanager", t("chm-btn-refresh"))], back_row(t)))

    return router
