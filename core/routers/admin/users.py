"""Admin user management: lists, search, user card, ban (with reason), VIP grant/revoke, refunds."""

from __future__ import annotations

import contextlib
import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from core.callback_data import AdminNavCb, AdminUserCb, AdminUsersCb
from core.db.models import BotUser
from core.i18n import Translate
from core.routers.admin.common import PER_PAGE, actor, admin_router, back_row, btn, markup, pager, show
from core.sdk.context import BotContext
from core.ui.text import esc


class UserStates(StatesGroup):
    search = State()
    ban_reason = State()


def user_label(u: BotUser) -> str:
    name = u.first_name or (f"@{u.username}" if u.username else str(u.user_id))
    flags = ("⭐" if u.is_vip() else "") + ("🚫" if u.is_banned else "") + ("📵" if u.blocked_bot else "")
    return f"{flags}{name[:24]} · {u.user_id}"


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "users")

    async def notify_user(user_id: int, key: str, **kwargs: object) -> None:
        member = await ctx.users.get(user_id)
        lang = ctx.translator.resolve(member.lang if member else None)
        with contextlib.suppress(Exception):
            await ctx.bot.send_message(chat_id=user_id, text=ctx.translator.get(lang, key, **kwargs))

    # ------------------------------------------------------------------ menu, lists, search
    @router.callback_query(AdminNavCb.filter(F.tab == "users"))
    async def users_menu(query: CallbackQuery, t: Translate) -> None:
        await show(
            query,
            t("adm-users"),
            markup(
                [btn(t("btn-adm-search"), AdminUserCb(user_id=0, action="search").pack())],
                [
                    btn(t("btn-adm-list-new"), AdminUsersCb(kind="new").pack()),
                    btn(t("btn-adm-list-active"), AdminUsersCb(kind="active").pack()),
                ],
                [
                    btn(t("btn-adm-list-vip"), AdminUsersCb(kind="vip").pack()),
                    btn(t("btn-adm-list-banned"), AdminUsersCb(kind="banned").pack()),
                ],
                back_row(t),
            ),
        )

    @router.callback_query(AdminUsersCb.filter())
    async def users_list(query: CallbackQuery, callback_data: AdminUsersCb, t: Translate) -> None:
        kind = callback_data.kind if callback_data.kind in ("new", "active", "vip", "banned") else "new"
        items, total = await ctx.users.list_page(kind, callback_data.page, PER_PAGE)
        pages = max(1, math.ceil(total / PER_PAGE))
        rows = [[btn(user_label(u), AdminUserCb(user_id=u.user_id, action="view").pack())] for u in items]
        text = t("adm-users-list", title=t(f"btn-adm-list-{kind}"), total=total, page=callback_data.page, pages=pages)
        if not items:
            text += "\n\n" + t("adm-list-empty")
        await show(
            query,
            text,
            markup(
                *rows,
                pager(t, callback_data.page, pages, lambda p: AdminUsersCb(kind=kind, page=p).pack()),
                back_row(t, "users"),
            ),
        )

    @router.callback_query(AdminUserCb.filter(F.action == "search"))
    async def search_prompt(query: CallbackQuery, state: FSMContext, t: Translate) -> None:
        await state.set_state(UserStates.search)
        await show(query, t("adm-search-prompt"), markup(back_row(t, "users")))

    @router.message(UserStates.search, F.text)
    async def search_run(message: Message, state: FSMContext, t: Translate) -> None:
        await state.clear()
        found = await ctx.users.search(message.text or "")
        if len(found) == 1:
            await render_card(message, found[0], t)
            return
        if not found:
            await message.answer(
                t("adm-search-empty", query=esc((message.text or "")[:64])), reply_markup=markup(back_row(t, "users"))
            )
            return
        rows = [[btn(user_label(u), AdminUserCb(user_id=u.user_id, action="view").pack())] for u in found]
        await message.answer(
            t("adm-users-list", title="🔍", total=len(found), page=1, pages=1),
            reply_markup=markup(*rows, back_row(t, "users")),
        )

    # ------------------------------------------------------------------ user card
    async def render_card(event: Message | CallbackQuery, u: BotUser, t: Translate) -> None:
        payments = await ctx.subs.payments_of(u.user_id, limit=100)
        paid = [p for p in payments if p.status == "paid"]
        if u.is_banned:
            status = t("adm-status-banned", reason=esc(u.ban_reason or "—"))
        elif u.blocked_bot:
            status = t("adm-status-blocked")
        else:
            status = t("adm-status-active")
        vip = t("adm-vip-until", until=f"{u.vip_until:%Y-%m-%d %H:%M}") if u.is_vip() and u.vip_until else "—"
        text = t(
            "adm-user-card",
            name=esc(u.first_name or "—"),
            username=f"@{esc(u.username)}" if u.username else "",
            id=u.user_id,
            lang=(u.lang or "—").upper(),
            joined=f"{u.started_at:%Y-%m-%d}",
            seen=f"{u.last_seen:%Y-%m-%d %H:%M}",
            status=status,
            vip=vip,
            actions=u.actions_count,
            refs=u.referral_count,
            payments=len(paid),
            stars=sum(p.stars for p in paid),
        )
        uid = u.user_id

        def cb(action: str, arg: int = 0) -> str:
            return AdminUserCb(user_id=uid, action=action, arg=arg).pack()

        kb = markup(
            [btn(t("btn-adm-unban"), cb("unban"))] if u.is_banned else [btn(t("btn-adm-ban"), cb("ban"))],
            [btn("+7d ⭐", cb("grant", 7)), btn("+30d ⭐", cb("grant", 30)), btn("+365d ⭐", cb("grant", 365))],
            [btn(t("btn-adm-revoke"), cb("revoke")), btn(t("btn-adm-reset-limits"), cb("reset"))],
            [btn(t("btn-adm-payments"), cb("payments"))],
            back_row(t, "users"),
        )
        await show(event, text, kb)

    @router.callback_query(AdminUserCb.filter(F.action == "view"))
    async def card(query: CallbackQuery, callback_data: AdminUserCb, t: Translate) -> None:
        u = await ctx.users.get(callback_data.user_id)
        if u is None:
            await query.answer(t("adm-not-found"), show_alert=True)
            return
        await render_card(query, u, t)

    # ------------------------------------------------------------------ actions
    @router.callback_query(AdminUserCb.filter(F.action == "ban"))
    async def ban_prompt(query: CallbackQuery, callback_data: AdminUserCb, state: FSMContext, t: Translate) -> None:
        await state.set_state(UserStates.ban_reason)
        await state.update_data(ban_user=callback_data.user_id)
        await show(
            query,
            t("adm-ban-prompt"),
            markup(
                [btn(t("btn-adm-skip"), AdminUserCb(user_id=callback_data.user_id, action="ban_skip").pack())],
                back_row(t, "users"),
            ),
        )

    async def do_ban(event: Message | CallbackQuery, user_id: int, reason: str | None, t: Translate) -> None:
        await ctx.users.set_banned(user_id, True, reason)
        await ctx.audit.record(actor(event), "user.ban", user_id, reason=reason)
        u = await ctx.users.get(user_id)
        if u:
            await render_card(event, u, t)

    @router.message(UserStates.ban_reason, F.text)
    async def ban_with_reason(message: Message, state: FSMContext, t: Translate) -> None:
        data = await state.get_data()
        await state.clear()
        await do_ban(message, int(data.get("ban_user", 0)), (message.text or "")[:200], t)

    @router.callback_query(AdminUserCb.filter(F.action == "ban_skip"))
    async def ban_without_reason(query: CallbackQuery, callback_data: AdminUserCb, state: FSMContext, t: Translate) -> None:
        await state.clear()
        await do_ban(query, callback_data.user_id, None, t)

    @router.callback_query(AdminUserCb.filter(F.action.in_({"unban", "grant", "revoke", "reset"})))
    async def quick_action(query: CallbackQuery, callback_data: AdminUserCb, t: Translate) -> None:
        uid, action, admin = callback_data.user_id, callback_data.action, actor(query)
        if action == "unban":
            await ctx.users.set_banned(uid, False)
            await ctx.audit.record(admin, "user.unban", uid)
        elif action == "grant":
            days = max(1, min(callback_data.arg, 3650))
            until = await ctx.subs.grant_vip(uid, days, source="admin", actor_id=admin)
            await ctx.audit.record(admin, "vip.grant", uid, days=days)
            await notify_user(uid, "vip-granted", days=days, until=f"{until:%Y-%m-%d}")
            await query.answer(t("adm-vip-granted-toast", days=days))
        elif action == "revoke":
            await ctx.subs.revoke_vip(uid, actor_id=admin)
            await ctx.audit.record(admin, "vip.revoke", uid)
            await notify_user(uid, "vip-revoked")
        elif action == "reset":
            ok = await ctx.module.reset_user_limits(ctx, uid)
            await ctx.audit.record(admin, "user.reset_limits", uid)
            await query.answer(t("adm-limits-reset") if ok else t("adm-not-found"), show_alert=not ok)
        u = await ctx.users.get(uid)
        if u:
            await render_card(query, u, t)

    # ------------------------------------------------------------------ payments & refunds
    @router.callback_query(AdminUserCb.filter(F.action == "payments"))
    async def payments(query: CallbackQuery, callback_data: AdminUserCb, t: Translate) -> None:
        uid = callback_data.user_id
        items = await ctx.subs.payments_of(uid, limit=10)
        lines = [
            t("adm-payment-line", date=f"{p.created_at:%Y-%m-%d}", stars=p.stars, days=p.days, status=p.status)
            for p in items
        ]
        rows = [
            [btn(t("btn-adm-refund", stars=p.stars, date=f"{p.created_at:%m-%d}"),
                 AdminUserCb(user_id=uid, action="refund", arg=p.id).pack())]
            for p in items
            if p.status == "paid"
        ]
        body = "\n".join(lines) if lines else t("adm-no-payments")
        await show(
            query,
            t("adm-payments", id=uid) + "\n\n" + body,
            markup(*rows, [btn(t("btn-back"), AdminUserCb(user_id=uid, action="view").pack())]),
        )

    @router.callback_query(AdminUserCb.filter(F.action == "refund"))
    async def refund_confirm(query: CallbackQuery, callback_data: AdminUserCb, t: Translate) -> None:
        p = await ctx.payments.get(callback_data.arg)
        if p is None or p.status != "paid" or p.user_id != callback_data.user_id:
            await query.answer(t("adm-not-found"), show_alert=True)
            return
        await show(
            query,
            t("adm-refund-confirm", stars=p.stars, id=p.user_id, days=p.days),
            markup(
                [btn(t("btn-adm-confirm"), AdminUserCb(user_id=p.user_id, action="refund_ok", arg=p.id).pack())],
                [btn(t("btn-back"), AdminUserCb(user_id=p.user_id, action="payments").pack())],
            ),
        )

    @router.callback_query(AdminUserCb.filter(F.action == "refund_ok"))
    async def refund_execute(query: CallbackQuery, callback_data: AdminUserCb, t: Translate) -> None:
        p = await ctx.payments.get(callback_data.arg)
        if p is None or p.status != "paid":
            await query.answer(t("adm-not-found"), show_alert=True)
            return
        try:
            await ctx.bot.refund_star_payment(user_id=p.user_id, telegram_payment_charge_id=p.charge_id)
        except Exception as e:
            await query.answer(t("adm-refund-failed", error=str(e)[:150]), show_alert=True)
            return
        result = await ctx.payments.process_refund(p.charge_id, actor_id=actor(query))
        await ctx.audit.record(actor(query), "payment.refund", p.user_id, payment_id=p.id, stars=p.stars)
        if result:
            await notify_user(p.user_id, "vip-refunded")
        await query.answer(t("adm-refund-done"), show_alert=True)
        await payments(query, AdminUserCb(user_id=p.user_id, action="payments"), t)

    return router
