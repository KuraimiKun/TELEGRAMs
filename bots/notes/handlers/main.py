"""Notes & Reminders handlers: plain text becomes a note; /remind schedules a reminder."""

from __future__ import annotations

import contextlib
import math

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bots.notes.service import LimitReached, NotesService, parse_when
from bots.notes.settings import NotesSettings
from core.callback_data import CoreVipCb
from core.db.base import utcnow
from core.db.models import BotUser
from core.i18n import Translate
from core.sdk.actions import record_user_action
from core.sdk.context import BotContext
from core.ui.text import esc

PER_PAGE = 5


class NoteCb(CallbackData, prefix="nt"):
    action: str  # list | del | rlist | rdel
    arg: int = 0


def build_router(ctx: BotContext) -> Router:
    router = Router(name="notes_main")
    svc: NotesService = ctx.extras["notes"]

    async def limits(user: BotUser) -> tuple[int, int]:
        stg: NotesSettings = await ctx.settings.get()
        if user.is_vip():
            return stg.vip_max_notes, stg.vip_max_reminders
        return stg.free_max_notes, stg.free_max_reminders

    def main_kb(t: Translate) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=t("notes-btn-notes"), callback_data=NoteCb(action="list", arg=1).pack()),
                    InlineKeyboardButton(text=t("notes-btn-reminders"), callback_data=NoteCb(action="rlist").pack()),
                ],
                [
                    InlineKeyboardButton(text=t("btn-vip"), callback_data=CoreVipCb(action="info").pack()),
                    InlineKeyboardButton(text=t("btn-lang"), callback_data="nav:lang"),
                ],
            ]
        )

    def vip_kb(t: Translate) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=t("btn-vip"), callback_data=CoreVipCb(action="info").pack())]]
        )

    async def edit(query: CallbackQuery, text: str, kb: InlineKeyboardMarkup | None) -> None:
        if isinstance(query.message, Message):
            with contextlib.suppress(TelegramBadRequest):
                await query.message.edit_text(text, reply_markup=kb)
        await query.answer()

    @router.message(CommandStart())
    async def cmd_start(message: Message, t: Translate) -> None:
        name = (message.from_user.first_name if message.from_user else None) or "there"
        await message.answer(t("notes-start", name=esc(name)), reply_markup=main_kb(t))

    @router.callback_query(F.data == "nav:main")
    async def nav_main(query: CallbackQuery, t: Translate) -> None:
        name = query.from_user.first_name or "there"
        await edit(query, t("notes-start", name=esc(name)), main_kb(t))

    @router.message(Command("help"))
    async def cmd_help(message: Message, t: Translate) -> None:
        await message.answer(t("notes-help"))

    # ------------------------------------------------------------------ notes
    @router.message(Command("notes"))
    async def cmd_notes(message: Message, user: BotUser, t: Translate) -> None:
        text, kb = await render_notes(user, 1, t)
        await message.answer(text, reply_markup=kb)

    async def render_notes(user: BotUser, page: int, t: Translate) -> tuple[str, InlineKeyboardMarkup]:
        notes, total = await svc.page(user.user_id, page, PER_PAGE)
        pages = max(1, math.ceil(total / PER_PAGE))
        max_notes, _ = await limits(user)
        lines = [t("notes-list-title", count=total, max=max_notes)]
        rows = []
        for n in notes:
            lines.append(f"\n<b>#{n.id}</b> · <i>{n.created_at:%Y-%m-%d}</i>\n{esc(n.text[:300])}")
            rows.append([InlineKeyboardButton(text=t("notes-btn-delete", id=n.id), callback_data=NoteCb(action="del", arg=n.id).pack())])
        if not notes:
            lines.append("\n" + t("notes-empty"))
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton(text="◀️", callback_data=NoteCb(action="list", arg=page - 1).pack()))
        if page < pages:
            nav.append(InlineKeyboardButton(text="▶️", callback_data=NoteCb(action="list", arg=page + 1).pack()))
        if nav:
            rows.append(nav)
        rows.append([InlineKeyboardButton(text=t("btn-back"), callback_data="nav:main")])
        return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)

    @router.callback_query(NoteCb.filter(F.action == "list"))
    async def cb_notes(query: CallbackQuery, callback_data: NoteCb, user: BotUser, t: Translate) -> None:
        text, kb = await render_notes(user, max(1, callback_data.arg), t)
        await edit(query, text, kb)

    @router.callback_query(NoteCb.filter(F.action == "del"))
    async def cb_delete(query: CallbackQuery, callback_data: NoteCb, user: BotUser, t: Translate) -> None:
        await svc.delete_note(user.user_id, callback_data.arg)  # scoped to the owner
        text, kb = await render_notes(user, 1, t)
        await edit(query, text, kb)

    # ------------------------------------------------------------------ reminders
    @router.message(Command("remind"))
    async def cmd_remind(message: Message, command: CommandObject, user: BotUser, lang: str, t: Translate) -> None:
        parts = (command.args or "").split(maxsplit=1)
        due = parse_when(parts[0], utcnow()) if parts else None
        if due is None or len(parts) < 2:
            await message.answer(t("notes-remind-usage"))
            return
        _, max_reminders = await limits(user)
        try:
            await svc.add_reminder(user.user_id, message.chat.id, parts[1], due, lang, max_reminders)
        except LimitReached:
            await message.answer(t("notes-limit-reminders", max=max_reminders), reply_markup=vip_kb(t))
            return
        await record_user_action(ctx, user.user_id)
        await message.answer(t("notes-remind-set", when=f"{due:%Y-%m-%d %H:%M}"))

    async def render_reminders(user: BotUser, t: Translate) -> tuple[str, InlineKeyboardMarkup]:
        items = await svc.pending_reminders(user.user_id)
        lines = [t("notes-reminders-title", count=len(items))]
        rows = []
        for r in items:
            lines.append(f"\n⏰ <b>{r.due_at:%Y-%m-%d %H:%M}</b> UTC\n{esc(r.text[:200])}")
            rows.append([InlineKeyboardButton(text=t("notes-btn-cancel-reminder", when=f"{r.due_at:%m-%d %H:%M}"),
                                              callback_data=NoteCb(action="rdel", arg=r.id).pack())])
        if not items:
            lines.append("\n" + t("notes-reminders-empty"))
        rows.append([InlineKeyboardButton(text=t("btn-back"), callback_data="nav:main")])
        return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)

    @router.message(Command("reminders"))
    async def cmd_reminders(message: Message, user: BotUser, t: Translate) -> None:
        text, kb = await render_reminders(user, t)
        await message.answer(text, reply_markup=kb)

    @router.callback_query(NoteCb.filter(F.action == "rlist"))
    async def cb_reminders(query: CallbackQuery, user: BotUser, t: Translate) -> None:
        text, kb = await render_reminders(user, t)
        await edit(query, text, kb)

    @router.callback_query(NoteCb.filter(F.action == "rdel"))
    async def cb_cancel_reminder(query: CallbackQuery, callback_data: NoteCb, user: BotUser, t: Translate) -> None:
        await svc.cancel_reminder(user.user_id, callback_data.arg)
        text, kb = await render_reminders(user, t)
        await edit(query, text, kb)

    # ------------------------------------------------------------------ plain text = new note (last!)
    @router.message(F.chat.type == ChatType.PRIVATE, F.text, ~F.text.startswith("/"))
    async def save_note(message: Message, user: BotUser, t: Translate) -> None:
        max_notes, _ = await limits(user)
        try:
            note = await svc.add_note(user.user_id, message.text or "", max_notes)
        except LimitReached:
            await message.answer(t("notes-limit-notes", max=max_notes), reply_markup=vip_kb(t))
            return
        await record_user_action(ctx, user.user_id)
        await message.answer(
            t("notes-saved", id=note.id),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=t("notes-btn-delete", id=note.id), callback_data=NoteCb(action="del", arg=note.id).pack()),
                        InlineKeyboardButton(text=t("notes-btn-notes"), callback_data=NoteCb(action="list", arg=1).pack()),
                    ]
                ]
            ),
        )

    return router
