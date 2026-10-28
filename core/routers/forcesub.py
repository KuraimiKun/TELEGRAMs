"""Forced channel subscription for every bot.

Bots gate their core action with::

    if not await require_subscription(ctx, user, chat_id, t, payload={...}, reply_to=msg_id):
        return  # a join prompt was shown; the action resumes via module.on_force_sub_passed(payload)
"""

from __future__ import annotations

import contextlib
from typing import Any

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyParameters

from core.callback_data import CoreForceSubCb
from core.db.models import BotUser
from core.i18n import Translate
from core.log import get_logger
from core.sdk.context import BotContext
from core.sdk.features import Feature

log = get_logger(__name__)


async def require_subscription(
    ctx: BotContext,
    user: BotUser,
    chat_id: int,
    t: Translate,
    payload: dict[str, Any] | None = None,
    reply_to: int | None = None,
) -> bool:
    """True if the user may proceed. Otherwise sends the join prompt and returns False.

    VIP users and admins are exempt; the feature can be switched off at runtime (``force_sub_enabled``).
    """
    if Feature.FORCE_SUB not in ctx.features or user.is_vip() or ctx.is_admin(user.user_id):
        return True
    stg = await ctx.settings.get()
    if not stg.force_sub_enabled:
        return True
    missing = await ctx.forcesub.missing(user.user_id)
    if not missing:
        return True

    token = await ctx.forcesub.save_pending(user.user_id, payload or {})
    rows = [
        [InlineKeyboardButton(text=t("btn-fsub-join", title=ch.title), url=ch.invite_link)]
        for ch in missing
        if ch.invite_link
    ]
    rows.append([InlineKeyboardButton(text=t("btn-fsub-check"), callback_data=CoreForceSubCb(token=token).pack())])
    reply = ReplyParameters(message_id=reply_to, allow_sending_without_reply=True) if reply_to else None
    await ctx.bot.send_message(
        chat_id=chat_id,
        text=t("fsub-required"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        reply_parameters=reply,
    )
    return False


def build_router(ctx: BotContext) -> Router:
    router = Router(name=f"core_forcesub_{ctx.slug}")

    @router.callback_query(CoreForceSubCb.filter())
    async def recheck(query: CallbackQuery, callback_data: CoreForceSubCb, user: BotUser, t: Translate) -> None:
        await ctx.forcesub.forget(user.user_id)
        if await ctx.forcesub.missing(user.user_id):
            await query.answer(t("fsub-not-yet"), show_alert=True)
            return
        payload = await ctx.forcesub.pop_pending(callback_data.token, user.user_id)
        if isinstance(query.message, Message):
            with contextlib.suppress(TelegramBadRequest):
                await query.message.edit_text(t("fsub-ok") if payload else t("fsub-ok-nolink"))
        await query.answer()
        if payload:
            chat_id = query.message.chat.id if query.message else user.user_id
            try:
                await ctx.module.on_force_sub_passed(ctx, user, payload, chat_id)
            except Exception as e:
                log.exception("force_sub_replay_failed", bot=ctx.slug, error=str(e))

    return router
