"""User preference handlers for SocialDownload (referrals and language live in core)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bots.socialdownload.callback_data import SettingCb
from bots.socialdownload.keyboards import quality_choice_kb, settings_kb
from core.db.models import BotUser
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.respond import show


def build_router(ctx: BotContext) -> Router:
    router = Router(name="sd_settings")

    @router.message(Command("settings"))
    @router.callback_query(SettingCb.filter(F.action == "menu"))
    async def show_settings(
        event: Message | CallbackQuery,
        user: BotUser,
        t: Translate,
    ) -> None:
        prefs = user.prefs or {}
        q = prefs.get("quality", "auto")
        aud = prefs.get("audio", "mp3")
        cap = t("state-on") if prefs.get("caption", True) else t("state-off")

        text = t("settings-text", quality=q.upper(), audio=aud.upper(), caption=cap)
        kb = settings_kb(prefs, t)

        await show(event, text, kb)

    @router.callback_query(SettingCb.filter(F.action == "set_q"))
    async def setting_choose_quality(
        query: CallbackQuery,
        callback_data: SettingCb,
        user: BotUser,
        t: Translate,
    ) -> None:
        if callback_data.value:
            await ctx.users.update_pref(user.id, "quality", callback_data.value)
            user.prefs = dict(user.prefs or {})
            user.prefs["quality"] = callback_data.value
            await show_settings(query, user, t)
            return

        text = t("settings-choose-quality")
        await show(query, text, quality_choice_kb(t))

    @router.callback_query(SettingCb.filter(F.action == "set_aud"))
    async def setting_toggle_audio(
        query: CallbackQuery,
        user: BotUser,
        t: Translate,
    ) -> None:
        current = user.pref("audio", "mp3")
        new_fmt = "m4a" if current == "mp3" else "mp3"
        await ctx.users.update_pref(user.id, "audio", new_fmt)
        user.prefs = dict(user.prefs or {})
        user.prefs["audio"] = new_fmt
        await show_settings(query, user, t)

    @router.callback_query(SettingCb.filter(F.action == "toggle_cap"))
    async def setting_toggle_caption(
        query: CallbackQuery,
        user: BotUser,
        t: Translate,
    ) -> None:
        current = user.pref("caption", True)
        await ctx.users.update_pref(user.id, "caption", not current)
        user.prefs = dict(user.prefs or {})
        user.prefs["caption"] = not current
        await show_settings(query, user, t)

    return router
