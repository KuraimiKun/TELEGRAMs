"""Bot Factory admin tab: totals per template and moderation (search a user bot, revoke it)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from core.callback_data import AdminNavCb
from core.factory.children import ChildService
from core.i18n import Translate
from core.routers.admin.common import actor, admin_router, back_row, btn, markup, nav, show
from core.sdk.context import BotContext
from core.ui.text import esc

TAB = "factory"


class FacAdminCb(CallbackData, prefix="fac_adm"):
    action: str  # search | revoke | revoke_ok
    id: int = 0


class FacAdminStates(StatesGroup):
    search = State()


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "factory_admin")
    children: ChildService = ctx.extras["children"]

    @router.callback_query(AdminNavCb.filter(F.tab == TAB))
    async def overview(query: CallbackQuery, state: FSMContext, t: Translate) -> None:
        await state.clear()
        totals = await children.totals()
        lines = [t("fac-adm")]
        for key in sorted(totals):
            template, status = key.split(":")
            lines.append(f"• {esc(template)} · {esc(status)}: <b>{totals[key]:,}</b>")
        await show(query, "\n".join(lines), markup(
            [btn(t("fac-adm-btn-search"), FacAdminCb(action="search").pack()), nav(TAB, t("btn-adm-refresh"))],
            back_row(t),
        ))

    @router.callback_query(FacAdminCb.filter(F.action == "search"))
    async def ask(query: CallbackQuery, state: FSMContext, t: Translate) -> None:
        await state.set_state(FacAdminStates.search)
        await show(query, t("fac-adm-search"), markup(back_row(t, TAB)))

    @router.message(FacAdminStates.search, F.text)
    async def search(message: Message, state: FSMContext, t: Translate) -> None:
        await state.clear()
        found = await children.search(message.text or "")
        if not found:
            await message.answer(t("adm-list-empty"), reply_markup=markup(back_row(t, TAB)))
            return
        lines, rows = [], []
        for c in found:
            lines.append(f"• @{esc(c.username)} · {esc(c.template)} · {esc(c.status)} · owner <code>{c.owner_id}</code>")
            if c.status != "revoked":
                rows.append([btn(t("fac-adm-btn-revoke", username=c.username), FacAdminCb(action="revoke", id=c.bot_id).pack())])
        await message.answer("\n".join(lines), reply_markup=markup(*rows, back_row(t, TAB)))

    @router.callback_query(FacAdminCb.filter(F.action == "revoke"))
    async def confirm(query: CallbackQuery, callback_data: FacAdminCb, t: Translate) -> None:
        child = await children.get(callback_data.id)
        if child is None:
            await query.answer()
            return
        await show(query, t("fac-adm-confirm", username=child.username), markup(
            [btn(t("btn-adm-confirm"), FacAdminCb(action="revoke_ok", id=child.bot_id).pack())], back_row(t, TAB),
        ))

    @router.callback_query(FacAdminCb.filter(F.action == "revoke_ok"))
    async def revoke(query: CallbackQuery, callback_data: FacAdminCb, t: Translate) -> None:
        child = await children.get(callback_data.id)
        if child is None:
            await query.answer()
            return
        await children.revoke(child, f"revoked by admin {actor(query)}")
        await ctx.audit.record(actor(query), "factory.revoke", child.bot_id, owner=child.owner_id)
        await show(query, t("fac-adm-revoked", username=child.username), markup(back_row(t, TAB)))

    return router
