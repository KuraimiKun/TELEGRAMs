"""YouTube search: /search, /music, and plain text sent in a private chat."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bots.socialdownload.callback_data import FormatCb
from bots.socialdownload.engine.errors import DownloadFailed
from bots.socialdownload.engine.ytdl import DownloadEngine
from bots.socialdownload.services.requests import DownloadService, PendingRequest
from core.db.models import BotUser
from core.i18n import Translate
from core.log import get_logger
from core.sdk.context import BotContext
from core.ui.text import esc

log = get_logger(__name__)

MAX_QUERY = 200


def _short(title: str, n: int) -> str:
    return (title[:n] + "…") if len(title) > n else title


def build_router(ctx: BotContext) -> Router:
    router = Router(name="sd_search")
    engine: DownloadEngine = ctx.extras["engine"]
    svc: DownloadService = ctx.extras["downloads"]

    async def run_search(message: Message, user: BotUser, t: Translate, query: str, *, music: bool) -> None:
        stg = await svc.settings()
        if not stg.search_enabled or "youtube" in stg.disabled_platforms:
            await message.reply(t("search-disabled"))
            return

        query = query.strip()[:MAX_QUERY]
        status = await message.reply(t("search-searching"))
        try:
            results = await engine.search(f"{query} audio" if music else query, limit=5)
        except DownloadFailed as e:
            log.info("search_failed", code=e.code)
            await status.edit_text(t("error-unknown"))
            return
        if not results:
            await status.edit_text(t("search-empty"))
            return

        audio_format = user.pref("audio", "mp3")
        builder = InlineKeyboardBuilder()
        for idx, res in enumerate(results, 1):
            token = await svc.save_pending(
                PendingRequest(
                    user_id=user.user_id,
                    chat_id=message.chat.id,
                    chat_type=message.chat.type,
                    reply_to=message.message_id,
                    url=res.url,
                    platform="youtube",
                    title=res.title,
                    audio_format=audio_format,
                )
            )
            dur = f" ({res.duration // 60}:{res.duration % 60:02d})" if res.duration else ""
            audio_btn = InlineKeyboardButton(
                text=f"🎵 {audio_format.upper()}" if not music else f"🎵 {idx}. {_short(res.title, 35)}{dur}",
                callback_data=FormatCb(job_id=token, kind="audio", height=0).pack(),
            )
            if music:
                builder.row(audio_btn)
            else:
                builder.row(
                    InlineKeyboardButton(
                        text=f"🎬 {idx}. {_short(res.title, 30)}{dur}",
                        # height 0 = the best quality the user's plan allows
                        callback_data=FormatCb(job_id=token, kind="video", height=0).pack(),
                    ),
                    audio_btn,
                )
        builder.row(InlineKeyboardButton(text=t("btn-close"), callback_data="nav:close"))
        await status.edit_text(t("search-results", query=esc(query)), reply_markup=builder.as_markup())

    @router.message(Command("search"))
    async def cmd_search(message: Message, command: CommandObject, user: BotUser, t: Translate) -> None:
        if not command.args:
            await message.reply(t("search-usage"))
            return
        await run_search(message, user, t, command.args, music=False)

    @router.message(Command("music"))
    async def cmd_music(message: Message, command: CommandObject, user: BotUser, t: Translate) -> None:
        if not command.args:
            await message.reply(t("music-usage"))
            return
        await run_search(message, user, t, command.args, music=True)

    # Plain text in a private chat (no URL — links are handled by the link router first).
    @router.message(F.chat.type == ChatType.PRIVATE, F.text, ~F.text.startswith("/"), ~F.via_bot)
    async def free_text(message: Message, user: BotUser, t: Translate) -> None:
        text = (message.text or "").strip()
        if len(text) < 2:
            await message.reply(t("dl-no-url"))
            return
        await run_search(message, user, t, text, music=False)

    return router
