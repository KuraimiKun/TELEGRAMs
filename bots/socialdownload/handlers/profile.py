"""User profile and stats handler."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bots.socialdownload.callback_data import VipCb
from bots.socialdownload.engine.limits import policy_for
from bots.socialdownload.services.quota import QuotaService
from core.db.models import BotUser
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.respond import show


def build_router(ctx: BotContext) -> Router:
    router = Router(name="sd_profile")
    quota: QuotaService = ctx.extras["quota"]

    @router.message(Command("profile"))
    @router.callback_query(F.data == "nav:profile")
    async def show_profile(
        event: Message | CallbackQuery,
        user: BotUser,
        t: Translate,
    ) -> None:
        stg = await ctx.settings.get()
        policy = policy_for(user.is_vip(), stg)

        used = await quota.used(user.id)
        limit_str = str(policy.daily_limit)

        if user.is_vip() and user.vip_until:
            plan_str = t("plan-vip", until=user.vip_until.strftime("%Y-%m-%d %H:%M"))
        else:
            plan_str = t("plan-free")

        text = t(
            "profile-text",
            id=user.id,
            plan=plan_str,
            used=used,
            limit=limit_str,
            total=user.total_downloads,
            refs=user.referral_count,
            lang=(user.lang or "auto").upper(),
        )

        builder = InlineKeyboardBuilder()
        if not user.is_vip():
            builder.row(InlineKeyboardButton(text=t("btn-vip"), callback_data=VipCb(action="info").pack()))
        builder.row(
            InlineKeyboardButton(text=t("btn-referral"), callback_data="nav:referral"),
            InlineKeyboardButton(text=t("btn-back"), callback_data="nav:main"),
        )

        await show(event, text, builder.as_markup())

    return router
