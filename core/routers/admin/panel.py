"""Admin panel home: entry point, feature-aware navigation, /cancel, and the audit log."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from core.callback_data import AdminNavCb
from core.i18n import Translate
from core.routers.admin.common import ClearStateOnNavigation, admin_router, back_row, btn, markup, nav, show
from core.sdk.context import BotContext
from core.sdk.features import Feature
from core.ui.text import esc


def home_kb(ctx: BotContext, t: Translate) -> InlineKeyboardMarkup:
    features = ctx.features
    buttons = [nav("stats", t("btn-adm-stats")), nav("users", t("btn-adm-users"))]
    if Feature.BROADCAST in features:
        buttons.append(nav("broadcast", t("btn-adm-broadcast")))
    buttons.append(nav("settings", t("btn-adm-settings")))
    if Feature.FORCE_SUB in features:
        buttons.append(nav("channels", t("btn-adm-channels")))
    if Feature.VIP in features:
        buttons.append(nav("plans", t("btn-adm-plans")))
    buttons.append(nav("audit", t("btn-adm-audit")))
    buttons += [nav(sec.tab, t(sec.title)) for sec in ctx.module.admin_sections()]  # title: i18n key or text
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    rows.append([btn(t("btn-close"), "nav:close")])
    return markup(*rows)


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "panel")
    # Runs for every callback entering the admin routers (this one is included first).
    router.callback_query.outer_middleware(ClearStateOnNavigation())

    async def home_text(t: Translate) -> str:
        data = await ctx.stats.get_overview()
        return t(
            "adm-title",
            bot=esc(ctx.module.title),
            users=f"{data['total_users']:,}",
            vip=f"{data['vip_users']:,}",
            active=f"{data['active_24h']:,}",
        )

    @router.message(Command("admin"))
    async def cmd_admin(message: Message, state: FSMContext, t: Translate) -> None:
        await state.clear()
        await message.answer(await home_text(t), reply_markup=home_kb(ctx, t))

    @router.message(Command("cancel"))
    async def cmd_cancel(message: Message, state: FSMContext, t: Translate) -> None:
        await state.clear()
        await message.answer(t("adm-cancelled"), reply_markup=markup(back_row(t)))

    @router.callback_query(AdminNavCb.filter(F.tab == "home"))
    async def nav_home(query: CallbackQuery, t: Translate) -> None:
        await show(query, await home_text(t), home_kb(ctx, t))

    @router.callback_query(AdminNavCb.filter(F.tab == "audit"))
    async def nav_audit(query: CallbackQuery, t: Translate) -> None:
        entries = await ctx.audit.recent(15)
        if not entries:
            body = t("adm-audit-empty")
        else:
            lines = []
            for e in entries:
                target = f" → <code>{esc(e.target)}</code>" if e.target else ""
                lines.append(f"<code>{e.created_at:%m-%d %H:%M}</code> · {e.admin_id} · <b>{esc(e.action)}</b>{target}")
            body = "\n".join(lines)
        await show(
            query,
            t("adm-audit", count=len(entries)) + "\n\n" + body,
            markup([nav("audit", t("btn-adm-refresh"))], back_row(t)),
        )

    return router
