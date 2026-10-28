"""Private chat: introduction, the "add me to your group" button, command help and group rules."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bots.groupguard import help as discovery
from core.factory.branding import credit
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.respond import show
from core.ui.text import esc

ADMIN_RIGHTS = "delete_messages+restrict_members+pin_messages+invite_users+change_info"


def build_router(ctx: BotContext) -> Router:
    router = Router(name="gg_start")

    def home_kb(t: Translate) -> InlineKeyboardMarkup:
        add = f"https://t.me/{ctx.username}?startgroup=guard&admin={ADMIN_RIGHTS}"
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("gg-btn-add"), url=add)],
            [InlineKeyboardButton(text=t("gg-btn-commands"), callback_data="gg_help")],
        ])

    @router.message(CommandStart(deep_link=True), F.text.regexp(r"^/start rules_-?\d+$"))
    async def start_rules(message: Message, command: CommandObject, t: Translate) -> None:
        chat_id = int((command.args or "")[6:])
        from bots.groupguard.content_access import display
        sent = await display(ctx, chat_id=chat_id, destination=message.chat.id, user=message.from_user, kind="rules")
        if sent is None or not sent.result.primary_completed:
            await message.answer(t("gg-content-unavailable"))

    @router.message(F.chat.type == "private", CommandStart())
    async def start(message: Message, t: Translate) -> None:
        name = message.from_user.first_name if message.from_user else ""
        await message.answer(t("gg-start", name=esc(name)) + credit(ctx, t), reply_markup=home_kb(t))

    return router


def build_help_router(ctx: BotContext) -> Router:
    router=Router(name="gg_help")

    @router.message(Command("help"))
    async def cmd_help(message: Message, command: CommandObject, t: Translate) -> None:
        args=(command.args or "").split()
        page=int(args[1])-1 if len(args)==2 and args[1].isascii() and args[1].isdigit() else 0
        text,kb=discovery.render(t,args[0] if args else "",page)
        await message.answer(text,reply_markup=kb)

    @router.callback_query(F.data == "gg_help")
    async def cb_help(query: CallbackQuery, t: Translate) -> None:
        text,kb=discovery.render(t)
        await show(query,text,kb)

    @router.callback_query(F.data.startswith("gg_h:"))
    async def page_help(query: CallbackQuery,t: Translate) -> None:
        parts=(query.data or "").split(":",2)
        if len(parts)!=3 or not parts[1].isascii() or not parts[1].isdigit() or len(parts[2])>32:
            await query.answer()
            return
        text,kb=discovery.render(t,parts[2],int(parts[1]))
        await show(query,text,kb)

    return router
