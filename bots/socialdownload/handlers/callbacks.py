"""Callback handlers: format / playlist pickers and cancellation."""

from __future__ import annotations

import contextlib

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from bots.socialdownload.callback_data import CancelCb, FormatCb, PlaylistCb
from bots.socialdownload.handlers.flow import submit_from_status
from bots.socialdownload.services.requests import DownloadService, Outcome, PendingRequest
from core.db.models import BotUser
from core.i18n import Translate
from core.sdk.context import BotContext


def build_router(ctx: BotContext) -> Router:
    router = Router(name="sd_callbacks")
    svc: DownloadService = ctx.extras["downloads"]

    async def edit(query: CallbackQuery, text: str) -> None:
        if isinstance(query.message, Message):
            with contextlib.suppress(TelegramBadRequest):
                await query.message.edit_text(text)

    async def claim(query: CallbackQuery, token: str, t: Translate) -> PendingRequest | None:
        """Atomically take ownership of a pending menu (a double tap can't submit twice)."""
        raw = await ctx.redis.getdel(ctx.keys("pending", token))
        if not raw:
            await query.answer(t("expired-menu"), show_alert=True)
            return None
        req = PendingRequest.model_validate_json(raw)
        if req.user_id != query.from_user.id:
            await svc.ctx.redis.set(ctx.keys("pending", token), raw, ex=600)  # put it back for its owner
            await query.answer(t("not-your-menu"), show_alert=True)
            return None
        return req

    async def submit(
        query: CallbackQuery,
        token: str,
        req: PendingRequest,
        user: BotUser,
        lang: str,
        t: Translate,
        *,
        kind: str,
        height: int | None,
        playlist_count: int | None = None,
    ) -> None:
        status = query.message
        if not isinstance(status, Message):
            await query.answer(t("expired-menu"), show_alert=True)
            return
        result = await submit_from_status(
            svc,
            status,
            user=user,
            lang=lang,
            t=t,
            url=req.url,
            platform=req.platform,
            kind=kind,
            height=height,
            audio_format=req.audio_format,
            reply_to=req.reply_to,
            playlist_count=playlist_count,
        )
        if result.outcome in (Outcome.LIMIT, Outcome.BUSY, Outcome.LOCKED):
            await svc.save_pending(req)  # keep the menu usable after the user frees a slot
        await query.answer()

    @router.callback_query(FormatCb.filter())
    async def cb_format_chosen(
        query: CallbackQuery, callback_data: FormatCb, user: BotUser, lang: str, t: Translate
    ) -> None:
        req = await claim(query, callback_data.job_id, t)
        if req is None:
            return
        await submit(
            query,
            callback_data.job_id,
            req,
            user,
            lang,
            t,
            kind=callback_data.kind,
            height=callback_data.height if callback_data.kind == "video" else None,
        )

    @router.callback_query(PlaylistCb.filter())
    async def cb_playlist_chosen(
        query: CallbackQuery, callback_data: PlaylistCb, user: BotUser, lang: str, t: Translate
    ) -> None:
        req = await claim(query, callback_data.job_id, t)
        if req is None:
            return
        await submit(
            query,
            callback_data.job_id,
            req,
            user,
            lang,
            t,
            kind=callback_data.kind,
            height=None,
            playlist_count=callback_data.count,
        )

    @router.callback_query(CancelCb.filter())
    async def cb_cancel(query: CallbackQuery, callback_data: CancelCb, t: Translate) -> None:
        user_id = query.from_user.id
        result, job = await svc.queue.cancel(callback_data.job_id, user_id)
        if result.found:
            if result.removed_from_queue and job is not None:
                await svc.refund(job)  # never reached a worker: we own the refund
            # Otherwise the worker sees the flag, stops, refunds and edits the message.
            if result.removed_from_queue:
                await edit(query, t("dl-cancelled"))
            await query.answer(t("dl-cancelled"))
            return

        # Not a job: maybe an open picker menu.
        req = await svc.load_pending(callback_data.job_id)
        if req is not None and req.user_id == user_id:
            await svc.drop_pending(callback_data.job_id)
            await edit(query, t("dl-cancelled"))
            await query.answer()
            return
        if req is not None:
            await query.answer(t("not-your-menu"), show_alert=True)
            return
        await query.answer(t("dl-cancel-too-late"), show_alert=True)

    return router
