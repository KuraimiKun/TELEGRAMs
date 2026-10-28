"""Language selector router."""

from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from core.callback_data import CoreLangCb
from core.db.models import BotUser
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.kb import lang_picker_kb
from core.ui.respond import show


def build_router(ctx: BotContext) -> Router:
    router = Router(name=f"core_lang_{ctx.slug}")

    @router.message(Command("lang"))
    @router.callback_query(F.data == "nav:lang")
    async def show_languages(
        event: Message | CallbackQuery,
        user: BotUser,
        t: Translate,
    ) -> None:
        current = user.lang or ctx.platform.default_lang
        text = t("lang-choose")
        kb = lang_picker_kb(current, back_to="main", locales=ctx.translator.locales)

        await show(event, text, kb)

    @router.callback_query(CoreLangCb.filter())
    async def change_lang(
        query: CallbackQuery,
        callback_data: CoreLangCb,
        user: BotUser,
    ) -> None:
        code = callback_data.code
        if code not in ctx.translator.locales:
            await query.answer()
            return
        await ctx.users.set_lang(user.user_id, code)
        user.lang = code

        def new_t(k: str, **kw: Any) -> str:
            return ctx.translator.get(code, k, **kw)

        await query.answer(new_t("lang-changed"), show_alert=True)
        await show(query, new_t("lang-choose"), lang_picker_kb(code, back_to="main", locales=ctx.translator.locales))

    return router
