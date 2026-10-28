"""Link receiver: validates the URL, applies group/platform rules, then shows a picker or downloads.

The core logic lives in :func:`process_link` so it can also be replayed after force-subscription,
from a ``/start dl_<token>`` deep link (inline mode) and from tests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.types import InlineKeyboardMarkup, Message, ReplyParameters

from bots.socialdownload.engine.errors import DownloadFailed
from bots.socialdownload.engine.limits import policy_for
from bots.socialdownload.engine.network import UnsafeURL, assert_public_url, expand_short_link
from bots.socialdownload.engine.platforms import (
    AUDIO_FIRST,
    LONG_FORM,
    detect_platform,
    is_playlist,
    is_short_link,
    normalize_url,
)
from bots.socialdownload.engine.ytdl import DownloadEngine
from bots.socialdownload.filters import HasURL
from bots.socialdownload.handlers.flow import submit_from_status
from bots.socialdownload.keyboards import format_picker_kb, playlist_picker_kb
from bots.socialdownload.services.requests import DownloadService, PendingRequest
from core.db.models import BotUser
from core.i18n import Translate
from core.log import get_logger
from core.routers.forcesub import require_subscription
from core.sdk.context import BotContext
from core.ui.text import esc

log = get_logger(__name__)

GROUP_CHATS = {ChatType.GROUP, ChatType.SUPERGROUP}
Send = Callable[[str, InlineKeyboardMarkup | None], Awaitable[Message]]


async def resolve_url(raw_url: str) -> tuple[str, str]:
    """Expand short links, refuse non-public targets, return (normalized_url, platform)."""
    url = raw_url if raw_url.lower().startswith(("http://", "https://")) else "https://" + raw_url
    if is_short_link(url):
        url = await expand_short_link(url)
    platform = detect_platform(url)
    if platform == "other":
        # Known platforms are public by definition; arbitrary sites must resolve to public addresses.
        await assert_public_url(url)
    return normalize_url(url), platform


def sender(ctx: BotContext, chat_id: int, reply_to: int | None) -> Send:
    reply = ReplyParameters(message_id=reply_to, allow_sending_without_reply=True) if reply_to else None

    async def send(text: str, markup: InlineKeyboardMarkup | None = None) -> Message:
        return await ctx.bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, reply_parameters=reply)

    return send


async def process_link(
    ctx: BotContext,
    *,
    user: BotUser,
    lang: str,
    t: Translate,
    chat_id: int,
    chat_type: str,
    reply_to: int | None,
    raw_url: str,
    check_subscription: bool = True,
) -> None:
    svc: DownloadService = ctx.extras["downloads"]
    engine: DownloadEngine = ctx.extras["engine"]
    send = sender(ctx, chat_id, reply_to)
    stg = await svc.settings()
    in_group = chat_type in GROUP_CHATS

    try:
        norm_url, platform = await resolve_url(raw_url)
    except UnsafeURL as e:
        log.info("unsafe_url_rejected", user_id=user.user_id, reason=str(e))
        if not in_group:
            await send(t("error-unsupported"), None)
        return

    if in_group and platform == "other" and not stg.groups_allow_other_sites:
        return
    if platform in stg.disabled_platforms:
        if not in_group:
            await send(t("dl-platform-disabled"), None)
        return

    if check_subscription and not await require_subscription(
        ctx,
        user,
        chat_id,
        t,
        payload={"url": raw_url, "chat_type": chat_type, "reply_to": reply_to},
        reply_to=reply_to,
    ):
        return

    policy = policy_for(user.is_vip(), stg)
    # Cheap pre-check before spending time on analysis (submit() re-checks atomically).
    active = await svc.queue.active_count(user.user_id)
    if active >= policy.concurrent:
        await send(t("dl-too-many-active", count=active), None)
        return

    pref_quality = user.pref("quality", "auto")
    pref_audio = user.pref("audio", "mp3")
    pending = PendingRequest(
        user_id=user.user_id,
        chat_id=chat_id,
        chat_type=chat_type,
        reply_to=reply_to,
        url=norm_url,
        platform=platform,
        audio_format=pref_audio,
    )

    if is_playlist(norm_url):
        status = await send(t("dl-analyzing"), None)
        try:
            info = await engine.extract(norm_url, platform, playlist=True)
        except DownloadFailed as e:
            await status.edit_text(t(f"error-{e.code}"))
            return
        pending.title, pending.entries = info.title, info.entries_count
        token = await svc.save_pending(pending)
        count = min(info.entries_count or policy.playlist_max, policy.playlist_max)
        await status.edit_text(
            t("dl-playlist", title=esc(info.title), count=info.entries_count or count, max=policy.playlist_max),
            reply_markup=playlist_picker_kb(job_id=token, allowed_count=count, t=t),
        )
        return

    if pref_quality == "ask" or (platform in LONG_FORM and pref_quality not in ("audio", "best")):
        status = await send(t("dl-analyzing"), None)
        try:
            info = await engine.extract(norm_url, platform)
        except DownloadFailed as e:
            await status.edit_text(t(f"error-{e.code}"))
            return
        if info.is_live:
            await status.edit_text(t("error-live"))
            return
        pending.title = info.title
        token = await svc.save_pending(pending)
        dur = f"{info.duration // 60}:{info.duration % 60:02d}" if info.duration else "--"
        await status.edit_text(
            t(
                "dl-choose-format",
                title=esc(info.title or "Video"),
                uploader=esc(info.uploader or t("unknown")),
                duration=dur,
            ),
            reply_markup=format_picker_kb(info, token, policy, pref_audio, t),
        )
        return

    kind = "audio" if (pref_quality == "audio" or platform in AUDIO_FIRST) else "video"
    status = await send(t("dl-queued", position="…"), None)
    await submit_from_status(
        svc,
        status,
        user=user,
        lang=lang,
        t=t,
        url=norm_url,
        platform=platform,
        kind=kind,
        height=None,
        audio_format=pref_audio,
        reply_to=reply_to,
    )


def build_router(ctx: BotContext) -> Router:
    router = Router(name="sd_link")

    @router.message(HasURL())
    async def handle_link(message: Message, urls: list[str], user: BotUser, lang: str, t: Translate) -> None:
        if message.chat.type in GROUP_CHATS:
            stg = await ctx.settings.get()
            if not stg.groups_enabled:
                return
            grp = await ctx.groups.get_or_create(message.chat.id, title=message.chat.title)
            if not grp.auto_download:
                return
        await process_link(
            ctx,
            user=user,
            lang=lang,
            t=t,
            chat_id=message.chat.id,
            chat_type=message.chat.type,
            reply_to=message.message_id,
            raw_url=urls[0],
        )

    return router
