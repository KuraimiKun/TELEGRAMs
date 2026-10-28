"""Referral tracking and invitation rewards router."""

from __future__ import annotations

from urllib.parse import urlencode

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.db.models import BotUser
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.respond import show


def build_router(ctx: BotContext) -> Router:
    router = Router(name=f"core_referral_{ctx.slug}")

    @router.message(Command("referral"))
    @router.callback_query(F.data == "nav:referral")
    async def show_referrals(
        event: Message | CallbackQuery,
        user: BotUser,
        t: Translate,
    ) -> None:
        stg = await ctx.settings.get()
        if not stg.referral_enabled:
            text = t("referral-disabled")
            await show(event, text)
            return

        ref_link = f"https://t.me/{ctx.username}?start=ref_{user.user_id}"
        req = stg.referral_required
        count = user.referral_count
        left = req - (count % req) if req > 0 else 0

        text = t(
            "referral-text",
            required=req,
            days=stg.referral_reward_days,
            count=count,
            left=left,
            link=ref_link,
        )

        share_text = t("referral-share-text")
        share_url = "https://t.me/share/url?" + urlencode({"url": ref_link, "text": share_text})
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=t("btn-share"), url=share_url))
        builder.row(InlineKeyboardButton(text=t("btn-back"), callback_data="nav:main"))

        await show(event, text, builder.as_markup())

    return router
