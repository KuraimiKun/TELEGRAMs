"""Group chat settings (/settings in a group, admins only)."""

from __future__ import annotations

import contextlib

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from core.callback_data import CoreGroupToggleCb
from core.i18n import Translate
from core.sdk.context import BotContext

GROUP_ADMINS = {"administrator", "creator"}
GROUP_CHATS = {ChatType.GROUP, ChatType.SUPERGROUP}


def build_router(ctx: BotContext) -> Router:
    router = Router(name=f"core_groups_{ctx.slug}")

    def settings_kb(chat_id: int, t: Translate) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t("btn-group-toggle"), callback_data=CoreGroupToggleCb(chat_id=chat_id).pack())]
            ]
        )

    async def is_group_admin(chat_id: int, message: Message | None, user_id: int | None) -> bool:
        if message is not None and message.sender_chat is not None and message.sender_chat.id == chat_id:
            return True  # anonymous group admin
        if user_id is None:
            return False
        try:
            member = await ctx.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        except TelegramBadRequest:
            return False
        return member.status in GROUP_ADMINS

    @router.message(F.chat.type.in_(GROUP_CHATS), Command("settings"))
    async def group_settings(message: Message, t: Translate) -> None:
        if not await is_group_admin(message.chat.id, message, message.from_user.id if message.from_user else None):
            await message.reply(t("group-admin-only"))
            return
        grp = await ctx.groups.get_or_create(message.chat.id, title=message.chat.title)
        state = t("state-on") if grp.auto_download else t("state-off")
        await message.reply(t("group-settings", state=state), reply_markup=settings_kb(message.chat.id, t))

    @router.callback_query(CoreGroupToggleCb.filter())
    async def toggle(query: CallbackQuery, callback_data: CoreGroupToggleCb, t: Translate) -> None:
        # The chat id must be the chat the button lives in: never trust it alone.
        if not isinstance(query.message, Message) or query.message.chat.id != callback_data.chat_id:
            await query.answer()
            return
        if not await is_group_admin(callback_data.chat_id, None, query.from_user.id):
            await query.answer(t("group-admin-only"), show_alert=True)
            return
        new_state = await ctx.groups.toggle_auto_download(callback_data.chat_id)
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(
                t("group-settings", state=t("state-on") if new_state else t("state-off")),
                reply_markup=settings_kb(callback_data.chat_id, t),
            )
        await query.answer(t("saved"))

    return router
