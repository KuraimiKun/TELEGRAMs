"""Common user routers: terms, support, and navigation close."""

from __future__ import annotations

import contextlib

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from core.i18n import Translate
from core.sdk.context import BotContext


def build_router(ctx: BotContext) -> Router:
    router = Router(name=f"core_common_{ctx.slug}")

    @router.message(Command("terms"))
    async def cmd_terms(message: Message, t: Translate) -> None:
        await message.answer(t("terms-text"))

    @router.message(Command("support"))
    async def cmd_support(message: Message, t: Translate) -> None:
        if ctx.env.support_username:
            contact = f"@{ctx.env.support_username.lstrip('@')}"
            await message.answer(t("support-text", contact=contact))
        else:
            await message.answer(t("support-none"))

    @router.callback_query(F.data == "nav:close")
    async def nav_close(query: CallbackQuery) -> None:
        if isinstance(query.message, Message):
            with contextlib.suppress(TelegramBadRequest):  # older than 48h: can't be deleted
                await query.message.delete()
        await query.answer()

    return router
