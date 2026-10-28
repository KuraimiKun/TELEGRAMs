"""Inline mode: ``@bot <link>`` in any chat.

* Cache hit  -> the media itself is offered as an inline result (instant).
* Cache miss -> a "download" result; when the user picks it (``chosen_inline_result`` — enable inline
  feedback in @BotFather) the download is queued and delivered to their private chat, and the inline
  message is updated. Its button opens the bot via ``/start dl_<token>`` as a fallback.
"""

from __future__ import annotations

import secrets

from aiogram import F, Router
from aiogram.types import (
    ChosenInlineResult,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultCachedAudio,
    InlineQueryResultCachedDocument,
    InlineQueryResultCachedGif,
    InlineQueryResultCachedPhoto,
    InlineQueryResultCachedVideo,
    InlineQueryResultsButton,
    InputTextMessageContent,
)

from bots.socialdownload.engine.cache import CachedItem, MediaCache, request_key
from bots.socialdownload.engine.limits import policy_for
from bots.socialdownload.engine.platforms import PLATFORM_EMOJI, detect_platform, extract_urls, normalize_url
from bots.socialdownload.services.requests import DownloadService, Outcome
from core.db.models import BotUser
from core.i18n import Translate
from core.sdk.context import BotContext
from core.ui.text import esc

DEEPLINK_TTL = 3600


def deeplink_key(ctx: BotContext, token: str) -> str:
    return ctx.keys("deeplink", token)


async def save_deeplink(ctx: BotContext, url: str) -> str:
    token = secrets.token_hex(6)
    await ctx.redis.set(deeplink_key(ctx, token), url, ex=DEEPLINK_TTL)
    return token


async def load_deeplink(ctx: BotContext, token: str) -> str | None:
    raw = await ctx.redis.get(deeplink_key(ctx, token))
    return raw.decode() if isinstance(raw, bytes) else raw


def cached_result(item: CachedItem, rid: str, title: str, caption: str):
    if item.kind == "video":
        return InlineQueryResultCachedVideo(id=rid, video_file_id=item.file_id, title=title, caption=caption)
    if item.kind == "photo":
        return InlineQueryResultCachedPhoto(id=rid, photo_file_id=item.file_id, title=title, caption=caption)
    if item.kind == "audio":
        return InlineQueryResultCachedAudio(id=rid, audio_file_id=item.file_id, caption=caption)
    if item.kind == "animation":
        return InlineQueryResultCachedGif(id=rid, gif_file_id=item.file_id, title=title, caption=caption)
    return InlineQueryResultCachedDocument(id=rid, document_file_id=item.file_id, title=title, caption=caption)


def build_router(ctx: BotContext) -> Router:
    router = Router(name="sd_inline")
    cache: MediaCache = ctx.extras["cache"]
    svc: DownloadService = ctx.extras["downloads"]

    @router.inline_query()
    async def inline_handler(inline_query: InlineQuery, user: BotUser, t: Translate) -> None:
        stg = await svc.settings()
        open_bot = InlineQueryResultsButton(text=t("inline-open-bot"), start_parameter="inline")
        if not stg.inline_enabled:
            await inline_query.answer([], cache_time=60, is_personal=True, button=open_bot)
            return

        urls = extract_urls(inline_query.query)
        if not urls:
            hint = InlineQueryResultArticle(
                id="hint",
                title=t("inline-hint"),
                description=t("inline-hint-desc"),
                input_message_content=InputTextMessageContent(message_text=t("inline-hint-message", bot=ctx.username)),
            )
            await inline_query.answer([hint], cache_time=30, is_personal=True, button=open_bot)
            return

        url = normalize_url(urls[0])
        platform = detect_platform(url)
        if platform in stg.disabled_platforms:
            await inline_query.answer([], cache_time=30, is_personal=True, button=open_bot)
            return

        policy = policy_for(user.is_vip(), stg)
        audio_format = user.pref("audio", "mp3")
        emoji = PLATFORM_EMOJI.get(platform, "🌐")
        results = []
        for kind in ("video", "audio"):
            cached = await cache.get(request_key(url, kind, policy.max_height, audio_format))
            if cached and cached.items:
                caption = f"🎬 {esc(cached.title)}\n\n📥 via @{ctx.username}" if cached.title else f"📥 via @{ctx.username}"
                title = cached.title or f"{emoji} {platform.title()}"
                results.append(cached_result(cached.items[0], f"c{kind[0]}{secrets.token_hex(4)}", title, caption))

        if not results:
            token = await save_deeplink(ctx, url)
            results.append(
                InlineQueryResultArticle(
                    id=f"dl:{token}",
                    title=t("inline-download", platform=platform.title()),
                    description=t("inline-download-desc"),
                    input_message_content=InputTextMessageContent(message_text=t("inline-processing")),
                    # A keyboard is required for Telegram to report inline_message_id back to us.
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text=t("inline-open-bot"), url=f"https://t.me/{ctx.username}?start=dl_{token}")]
                        ]
                    ),
                )
            )
        await inline_query.answer(results, cache_time=5, is_personal=True, button=open_bot)

    @router.chosen_inline_result(F.result_id.startswith("dl:"))
    async def inline_chosen(result: ChosenInlineResult, user: BotUser, lang: str, t: Translate) -> None:
        url = await load_deeplink(ctx, result.result_id[3:])
        if not url or not result.inline_message_id:
            return
        stg = await svc.settings()
        res = await svc.submit(
            user=user,
            chat_id=user.user_id,  # the file is delivered to the user's private chat
            chat_type="private",
            url=url,
            platform=detect_platform(url),
            kind="video",
            audio_format=user.pref("audio", "mp3"),
            inline_message_id=result.inline_message_id,
            lang=lang,
        )
        if res.outcome is Outcome.QUEUED:
            return
        if res.outcome is Outcome.LIMIT and res.policy:
            hours, minutes = res.limit_reset()
            text = t("dl-limit-reached", limit=res.policy.daily_limit, hours=hours, minutes=minutes)
        elif res.outcome is Outcome.BUSY:
            text = t("dl-too-many-active", count=res.active or stg.free_concurrent)
        else:
            text = t("inline-failed")
        await ctx.bot.edit_message_text(inline_message_id=result.inline_message_id, text=text)

    return router
