"""Start and help handlers (terms/support/close are provided by core)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from bots.socialdownload.handlers.inline import load_deeplink
from bots.socialdownload.handlers.link import process_link
from bots.socialdownload.keyboards import start_kb
from core.db.models import BotUser
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.respond import show
from core.ui.text import esc


def build_router(ctx: BotContext) -> Router:
    router = Router(name="sd_start")

    @router.message(CommandStart(deep_link=True, magic=F.args.regexp(r"^dl_[0-9a-f]{12}$")))
    async def start_download(message: Message, command: CommandObject, user: BotUser, lang: str, t: Translate) -> None:
        """Deep link from inline mode: continue the download in the private chat."""
        url = await load_deeplink(ctx, (command.args or "")[3:])
        if not url:
            await message.answer(t("expired-menu"))
            return
        await process_link(
            ctx,
            user=user,
            lang=lang,
            t=t,
            chat_id=message.chat.id,
            chat_type=message.chat.type,
            reply_to=message.message_id,
            raw_url=url,
        )

    @router.message(CommandStart())
    async def cmd_start(
        message: Message,
        user: BotUser,
        is_new_user: bool,
        t: Translate,
    ) -> None:
        name = (message.from_user.first_name if message.from_user else None) or "there"
        welcome_text = t("start-welcome", name=esc(name))
        if is_new_user and user.referred_by:
            welcome_text += "\n\n" + t("start-referred")

        kb = start_kb(t, ctx.username or "bot")
        await message.answer(welcome_text, reply_markup=kb)

    @router.message(Command("help"))
    @router.callback_query(F.data == "nav:help")
    async def cmd_help(event: Message | CallbackQuery, t: Translate) -> None:
        text = t("help-text", bot=ctx.username or "bot")
        await show(event, text, start_kb(t, ctx.username or "bot"))

    @router.callback_query(F.data == "nav:main")
    async def nav_main(query: CallbackQuery, t: Translate) -> None:
        name = (query.from_user.first_name if query.from_user else "there") or "there"
        welcome_text = t("start-welcome", name=esc(name))
        await show(query, welcome_text, start_kb(t, ctx.username or "bot"))

    return router
