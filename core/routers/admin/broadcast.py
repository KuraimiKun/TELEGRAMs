"""Broadcast composer: audience -> message -> preview -> queued for the scheduler's runner.

The send itself runs in the scheduler process (persisted, resumable). This screen shows live progress
from the database and can stop a running broadcast.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from core.callback_data import AdminBroadcastCb, AdminNavCb
from core.db.models import Broadcast
from core.i18n import LANGUAGES, Translate
from core.routers.admin.common import actor, admin_router, back_row, btn, markup, nav, show
from core.sdk.context import BotContext
from core.ui.text import progress_bar

STATUS_ICON = {"pending": "⏳", "running": "📤", "done": "✅", "cancelled": "⛔", "failed": "❌"}


class BroadcastStates(StatesGroup):
    message = State()


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "broadcast")

    def target_label(target: str, t: Translate) -> str:
        if target.startswith("lang:"):
            return LANGUAGES.get(target[5:], target[5:])
        return t(f"btn-adm-bc-{target}")

    def progress_text(b: Broadcast, t: Translate) -> str:
        done = b.sent + b.blocked + b.failed
        percent = min(100, int(done * 100 / b.total)) if b.total else (100 if b.status == "done" else 0)
        return t(
            "adm-bc-active",
            id=b.id,
            status=f"{STATUS_ICON.get(b.status, '')} {b.status}",
            bar=progress_bar(percent),
            percent=percent,
            sent=b.sent,
            blocked=b.blocked,
            failed=b.failed,
            total=b.total,
        )

    @router.callback_query(AdminNavCb.filter(F.tab == "broadcast"))
    async def broadcast_home(query: CallbackQuery, t: Translate) -> None:
        active = await ctx.broadcast.active()
        if active:
            await show(
                query,
                progress_text(active, t),
                markup(
                    [nav("broadcast", t("btn-adm-refresh"))],
                    [btn(t("btn-adm-bc-cancel"), AdminBroadcastCb(action="stop", bid=active.id).pack())],
                    back_row(t),
                ),
            )
            return

        def cb(target: str) -> str:
            return AdminBroadcastCb(action="target", target=target).pack()

        langs = [btn(LANGUAGES.get(c, c), cb(f"lang:{c}")) for c in ctx.translator.locales]
        history = [
            f"{STATUS_ICON.get(b.status, '')} #{b.id} · {target_label(b.target, t)} · {b.sent}/{b.total}"
            for b in await ctx.broadcast.recent(5)
        ]
        text = t("adm-bc") + ("\n\n" + "\n".join(history) if history else "")
        await show(
            query,
            text,
            markup(
                [btn(t("btn-adm-bc-all"), cb("all")), btn(t("btn-adm-bc-active7"), cb("active7"))],
                [btn(t("btn-adm-bc-free"), cb("free")), btn(t("btn-adm-bc-vip"), cb("vip"))],
                *[langs[i : i + 3] for i in range(0, len(langs), 3)],
                back_row(t),
            ),
        )

    @router.callback_query(AdminBroadcastCb.filter(F.action == "target"))
    async def choose_target(query: CallbackQuery, callback_data: AdminBroadcastCb, state: FSMContext, t: Translate) -> None:
        target = callback_data.target
        count = await ctx.broadcast.count_audience(target)
        await state.set_state(BroadcastStates.message)
        await state.update_data(target=target)
        await show(
            query, t("adm-bc-send", target=target_label(target, t), count=count), markup(back_row(t, "broadcast"))
        )

    @router.message(BroadcastStates.message)
    async def got_message(message: Message, state: FSMContext, t: Translate) -> None:
        data = await state.get_data()
        target = data.get("target", "all")
        await state.update_data(from_chat_id=message.chat.id, message_id=message.message_id)
        # Preview exactly what users will receive.
        await ctx.bot.copy_message(chat_id=message.chat.id, from_chat_id=message.chat.id, message_id=message.message_id)
        count = await ctx.broadcast.count_audience(target)
        await message.answer(
            t("adm-bc-preview", count=count),
            reply_markup=markup(
                [btn(t("btn-adm-bc-start"), AdminBroadcastCb(action="start", target=target).pack())],
                back_row(t, "broadcast"),
            ),
        )

    @router.callback_query(AdminBroadcastCb.filter(F.action == "start"))
    async def start(query: CallbackQuery, state: FSMContext, t: Translate) -> None:
        data = await state.get_data()
        await state.clear()
        if not data.get("message_id"):
            await query.answer(t("expired-menu"), show_alert=True)
            return
        if await ctx.broadcast.active():
            await query.answer(t("adm-bc-busy"), show_alert=True)
            return
        b = await ctx.broadcast.create(actor(query), data["target"], data["from_chat_id"], data["message_id"])
        await ctx.audit.record(actor(query), "broadcast.create", b.id, audience=b.target, total=b.total)
        await show(query, t("adm-bc-queued", id=b.id), markup([nav("broadcast", t("btn-adm-refresh"))], back_row(t)))

    @router.callback_query(AdminBroadcastCb.filter(F.action == "stop"))
    async def stop(query: CallbackQuery, callback_data: AdminBroadcastCb, t: Translate) -> None:
        if await ctx.broadcast.cancel(callback_data.bid):
            await ctx.audit.record(actor(query), "broadcast.cancel", callback_data.bid)
        await broadcast_home(query, t)

    return router
