"""Telegram delivery: uploads (up to 2 GB via the local Bot API), cached file_id re-delivery, direct links.

Media-group rules (Telegram API):
* a group holds 2-10 items; a single item must be sent with the per-type method;
* photos and videos may be mixed; audio only with audio; documents only with documents;
* animations (GIFs) can never be grouped.
"""

from __future__ import annotations

import asyncio
import os
import secrets
import shutil
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.types import (
    FSInputFile,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
    ReplyParameters,
)

from bots.socialdownload.engine.cache import CachedItem, CachedMedia, MediaCache
from bots.socialdownload.engine.errors import Cancelled, DownloadFailed
from bots.socialdownload.engine.media import MediaFile
from bots.socialdownload.engine.queue import Job
from core.config import MB
from core.i18n import Translate
from core.links import signed_url
from core.log import get_logger
from core.ui.text import esc

log = get_logger(__name__)

GROUP_MAX = 10
UPLOAD_TIMEOUT = 30 * 60  # seconds; 2 GB over a slow uplink takes a while
CancelCheck = Callable[[], Awaitable[bool]]


@dataclass(slots=True)
class Sendable:
    """One item to deliver: either a fresh local file or a cached Telegram file_id."""

    kind: str  # video | audio | photo | animation | document
    media: str | FSInputFile
    thumb: FSInputFile | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class UploadResult:
    items: list[CachedItem]
    complete: bool  # False when some files went out as direct links (don't cache a partial set)


def _group_class(kind: str) -> str | None:
    if kind in ("photo", "video"):
        return "visual"
    if kind in ("audio", "document"):
        return kind
    return None  # animation: never grouped


def plan_batches(items: list[Sendable]) -> list[list[Sendable]]:
    """Split items (keeping order) into batches that are valid media groups or single sends."""
    batches: list[list[Sendable]] = []
    current: list[Sendable] = []
    current_cls: str | None = None
    for item in items:
        cls = _group_class(item.kind)
        if cls is None:
            if current:
                batches.append(current)
                current, current_cls = [], None
            batches.append([item])
            continue
        if current and (cls != current_cls or len(current) >= GROUP_MAX):
            batches.append(current)
            current = []
        current.append(item)
        current_cls = cls
    if current:
        batches.append(current)
    return batches


def _file_id(msg: Message) -> CachedItem | None:
    if msg.video:
        return CachedItem("video", msg.video.file_id)
    if msg.animation:
        return CachedItem("animation", msg.animation.file_id)
    if msg.photo:
        return CachedItem("photo", msg.photo[-1].file_id)
    if msg.audio:
        return CachedItem("audio", msg.audio.file_id)
    if msg.document:
        return CachedItem("document", msg.document.file_id)
    return None


def _publish_file(src: Path, dest: Path) -> None:
    """Move (or copy across filesystems) a finished file into the public dir and stamp mtime = now,
    so the cleanup job measures the link TTL from publication, not from the server's Last-Modified."""
    tmp = dest.with_name(dest.name + ".part")
    try:
        os.link(src, tmp)
    except OSError:
        shutil.copyfile(src, tmp)
    os.replace(tmp, dest)
    os.utime(dest, None)


class TelegramUploader:
    def __init__(
        self,
        bot: Bot,
        cache: MediaCache,
        *,
        max_upload_bytes: int = 50 * MB,
        direct_link_base_url: str | None = None,
        direct_link_secret: str | None = None,
        public_dir: Path | None = None,
        direct_link_ttl_seconds: int = 3600,
    ) -> None:
        self.bot = bot
        self.cache = cache
        self.max_upload_bytes = max_upload_bytes
        self.direct_link_base_url = direct_link_base_url
        self.direct_link_secret = direct_link_secret
        self.public_dir = public_dir
        self.direct_link_ttl_seconds = direct_link_ttl_seconds
        if direct_link_base_url and not direct_link_secret:
            log.warning("direct_links_disabled", reason="DIRECT_LINK_SECRET is not configured")

    @property
    def direct_links_enabled(self) -> bool:
        return bool(self.direct_link_base_url and self.direct_link_secret)

    def effective_max_bytes(self, policy_max: int, user_direct_links: bool) -> int:
        """Never download more than we can deliver: Telegram's limit unless a direct link is possible."""
        if user_direct_links and self.direct_links_enabled:
            return policy_max
        return min(policy_max, self.max_upload_bytes)

    @staticmethod
    def build_caption(title: str, job: Job, bot_username: str) -> str:
        parts: list[str] = []
        if job.caption and title:
            parts.append(f"🎬 <b>{esc(title[:300])}</b>")
        if job.sponsor:
            parts.append(job.sponsor)  # admin-authored HTML
        parts.append(f"📥 via @{bot_username}")
        return "\n\n".join(parts)[:1024]

    # ------------------------------------------------------------------ low-level senders
    async def _call(self, fn: Callable[..., Awaitable[Any]], **kwargs: Any) -> Any:
        """Call a Bot API method, sleeping through one flood-wait."""
        try:
            return await fn(**kwargs)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            return await fn(**kwargs)

    async def _send_one(
        self, chat_id: int, item: Sendable, caption: str | None, reply: ReplyParameters | None
    ) -> Message:
        common: dict[str, Any] = {
            "chat_id": chat_id,
            "caption": caption,
            "reply_parameters": reply,
            "request_timeout": UPLOAD_TIMEOUT,
        }
        m = item.meta
        if item.kind == "video":
            return await self._call(
                self.bot.send_video, video=item.media, duration=m.get("duration"), width=m.get("width"),
                height=m.get("height"), thumbnail=item.thumb, supports_streaming=True, **common,
            )
        if item.kind == "audio":
            return await self._call(
                self.bot.send_audio, audio=item.media, duration=m.get("duration"), performer=m.get("performer"),
                title=m.get("title"), thumbnail=item.thumb, **common,
            )
        if item.kind == "photo":
            return await self._call(self.bot.send_photo, photo=item.media, **common)
        if item.kind == "animation":
            return await self._call(self.bot.send_animation, animation=item.media, thumbnail=item.thumb, **common)
        return await self._call(self.bot.send_document, document=item.media, thumbnail=item.thumb, **common)

    @staticmethod
    def _input_media(item: Sendable, caption: str | None) -> Any:
        m = item.meta
        if item.kind == "video":
            return InputMediaVideo(
                media=item.media, caption=caption, duration=m.get("duration"), width=m.get("width"),
                height=m.get("height"), thumbnail=item.thumb, supports_streaming=True,
            )
        if item.kind == "photo":
            return InputMediaPhoto(media=item.media, caption=caption)
        if item.kind == "audio":
            return InputMediaAudio(
                media=item.media, caption=caption, duration=m.get("duration"), performer=m.get("performer"),
                title=m.get("title"), thumbnail=item.thumb,
            )
        return InputMediaDocument(media=item.media, caption=caption, thumbnail=item.thumb)

    async def send_items(
        self,
        chat_id: int,
        items: list[Sendable],
        caption: str,
        reply_to: int | None,
        should_cancel: CancelCheck | None = None,
    ) -> list[CachedItem]:
        """Deliver items in valid batches; the caption goes on the first message only."""
        reply = ReplyParameters(message_id=reply_to, allow_sending_without_reply=True) if reply_to else None
        out: list[CachedItem] = []
        first = True
        for batch in plan_batches(items):
            if should_cancel and await should_cancel():
                raise Cancelled()
            cap = caption if first else None
            if len(batch) == 1:
                sent = [await self._send_one(chat_id, batch[0], cap, reply)]
            else:
                media = [self._input_media(it, cap if i == 0 else None) for i, it in enumerate(batch)]
                sent = await self._call(
                    self.bot.send_media_group, chat_id=chat_id, media=media, reply_parameters=reply,
                    request_timeout=UPLOAD_TIMEOUT,
                )
            first = False
            out.extend(ci for ci in (_file_id(m) for m in sent) if ci)
        return out

    # ------------------------------------------------------------------ public API
    async def deliver_cached(
        self,
        chat_id: int,
        cached: CachedMedia,
        job: Job,
        bot_username: str,
        reply_to: int | None = None,
        cache_key: str | None = None,
    ) -> bool:
        """Re-send cached file_ids instantly. A stale file_id evicts the entry so the caller re-downloads."""
        items = [Sendable(kind=i.kind, media=i.file_id) for i in cached.items]
        try:
            await self.send_items(chat_id, items, self.build_caption(cached.title, job, bot_username), reply_to)
            return True
        except TelegramBadRequest as e:
            log.info("cached_delivery_failed", error=str(e), job_id=job.id)
            if cache_key and "file" in str(e).lower():
                await self.cache.delete(cache_key)
            return False

    async def upload(
        self,
        chat_id: int,
        files: list[MediaFile],
        job: Job,
        bot_username: str,
        t: Translate,
        reply_to: int | None = None,
        should_cancel: CancelCheck | None = None,
    ) -> UploadResult:
        """Upload prepared files. Oversized files become signed direct links (VIP) or fail with too_large."""
        caption = self.build_caption(files[0].title or "", job, bot_username) if files else ""
        oversized = [f for f in files if f.size > self.max_upload_bytes]
        complete = True
        if oversized:
            if not (job.direct_links and self.direct_links_enabled):
                raise DownloadFailed("too_large")
            await self._send_direct_links(chat_id, oversized, t, reply_to)
            complete = False
            files = [f for f in files if f.size <= self.max_upload_bytes]
            if not files:
                return UploadResult(items=[], complete=False)

        items = [
            Sendable(
                kind=f.kind,
                media=FSInputFile(str(f.path)),
                thumb=FSInputFile(str(f.thumb)) if f.thumb else None,
                meta={
                    "duration": f.duration,
                    "width": f.width,
                    "height": f.height,
                    "performer": f.performer,
                    "title": f.title,
                },
            )
            for f in files
        ]
        try:
            cached = await self.send_items(chat_id, items, caption, reply_to, should_cancel)
        except TelegramBadRequest as e:
            log.warning("upload_rejected", job_id=job.id, error=str(e))
            raise DownloadFailed("upload", str(e)) from e
        return UploadResult(items=cached, complete=complete and len(cached) == len(items))

    async def _send_direct_links(
        self, chat_id: int, files: list[MediaFile], t: Translate, reply_to: int | None
    ) -> None:
        assert self.direct_link_base_url and self.direct_link_secret
        public_dir = self.public_dir or Path("./data/socialdownload/public")
        public_dir.mkdir(parents=True, exist_ok=True)
        reply = ReplyParameters(message_id=reply_to, allow_sending_without_reply=True) if reply_to else None
        for f in files:
            rel_name = f"{secrets.token_hex(16)}{f.path.suffix.lower()}"
            await asyncio.to_thread(_publish_file, f.path, public_dir / rel_name)
            url = signed_url(
                self.direct_link_base_url, rel_name, self.direct_link_secret, self.direct_link_ttl_seconds
            )
            text = t(
                "dl-direct-link",
                size=f"{f.size // MB} MB",
                minutes=self.direct_link_ttl_seconds // 60,
                link=esc(url),
            )
            await self._call(self.bot.send_message, chat_id=chat_id, text=text, reply_parameters=reply)
