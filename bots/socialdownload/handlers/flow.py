"""Shared presentation of download submissions (used by links, pickers, search and force-sub replay)."""

from __future__ import annotations

import contextlib

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bots.socialdownload.callback_data import CancelCb, VipCb
from bots.socialdownload.services.requests import DownloadService, Outcome, SubmitResult
from core.db.models import BotUser
from core.i18n import Translate


def cancel_kb(job_id: str, t: Translate) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("btn-cancel"), callback_data=CancelCb(job_id=job_id).pack())]]
    )


def vip_kb(t: Translate) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("btn-vip"), callback_data=VipCb(action="info").pack())]]
    )


async def report(status: Message, result: SubmitResult, t: Translate) -> None:
    """Turn a SubmitResult into the status message the user sees."""
    with contextlib.suppress(TelegramBadRequest):
        if result.outcome is Outcome.QUEUED and result.job:
            await status.edit_text(t("dl-queued", position=str(result.position)), reply_markup=cancel_kb(result.job.id, t))
        elif result.outcome is Outcome.DELIVERED:
            await status.delete()
        elif result.outcome is Outcome.LIMIT and result.policy:
            hours, minutes = result.limit_reset()
            await status.edit_text(
                t("dl-limit-reached", limit=result.policy.daily_limit, hours=hours, minutes=minutes),
                reply_markup=None if result.policy.is_vip else vip_kb(t),
            )
        elif result.outcome is Outcome.BUSY:
            await status.edit_text(t("dl-too-many-active", count=result.active))
        elif result.outcome is Outcome.LOCKED and result.policy:
            await status.edit_text(
                t("dl-quality-locked", quality=f"{result.policy.max_height}p+"), reply_markup=vip_kb(t)
            )


async def submit_from_status(
    svc: DownloadService,
    status: Message,
    *,
    user: BotUser,
    lang: str,
    t: Translate,
    url: str,
    platform: str,
    kind: str,
    height: int | None,
    audio_format: str,
    reply_to: int | None,
    playlist_count: int | None = None,
) -> SubmitResult:
    """Submit a request whose progress will be shown in ``status`` (an existing bot message)."""
    result = await svc.submit(
        user=user,
        chat_id=status.chat.id,
        chat_type=status.chat.type,
        url=url,
        platform=platform,
        kind=kind,
        height=height,
        audio_format=audio_format,
        playlist_count=playlist_count,
        reply_to=reply_to,
        status_msg_id=status.message_id,
        lang=lang,
    )
    await report(status, result, t)
    return result
