"""Content delivery with actual media/flags, bounded menus and scoped private opening tokens."""
from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from typing import Any, cast

from aiogram.exceptions import TelegramAPIError
from aiogram.types import Chat, InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions, Message, User
from redis.exceptions import RedisError

from bots.groupguard import actions, authz, perms
from bots.groupguard.contracts import ActionResult, StepResult, result_of
from bots.groupguard.formatting import ContentError, Fillings, Format, Rendered, html_size, render
from bots.groupguard.keyboards import GgCb
from core.sdk.context import BotContext

MEDIA = {"photo", "video", "animation", "document", "audio", "voice", "sticker", "video_note"}
MENU_TTL = 3600
OPEN_TTL = 86400


@dataclass(frozen=True, slots=True)
class Content:
    raw: str = ""
    format: Format = "html"
    media_kind: str | None = None
    file_id: str | None = None

    @classmethod
    def from_dict(cls, value: dict) -> Content:
        format = value.get("format", "html")
        if format not in {"html", "rose"}:
            raise ContentError("format_invalid")
        media = value.get("media_kind")
        file = value.get("file_id")
        if media is not None and (media not in MEDIA or not isinstance(file, str) or not file or len(file) > 256):
            raise ContentError("media_invalid")
        if not isinstance(value.get("raw", ""), str) or (file is not None and media is None):
            raise ContentError("content_invalid")
        return cls(value.get("raw", ""), cast(Format, format), media, file)

    def to_dict(self) -> dict:
        return dict(raw=self.raw, format=self.format, media_kind=self.media_kind, file_id=self.file_id)


@dataclass(frozen=True, slots=True)
class Delivered:
    result: ActionResult
    messages: tuple[Message, ...] = ()


async def fillings(ctx: BotContext, chat_id: int, user: User | None, *, chat_name: str = "",
                   sender_chat: Chat | None = None, raw: str = "") -> Fillings:
    cfg = await ctx.extras["guard"].config(chat_id)
    count = None
    if "{count}" in raw.lower():
        try:
            actual = await ctx.bot.get_chat_member_count(chat_id)
            count = actual if isinstance(actual, int) else None
        except TelegramAPIError:
            pass
    name = chat_name or await ctx.extras["guard"].title(chat_id) or str(chat_id)
    t = actions.group_t(ctx, cfg)
    return Fillings(user, chat_id, name, sender_chat, count, cfg.rules_button or t("gg-btn-rules"))


async def current_member(ctx: BotContext, chat_id: int, user_id: int) -> bool:
    if not await authz.active_namespace(ctx):
        return False
    bot = await perms.fresh_rights(ctx, chat_id, ctx.bot_id)
    if bot is None or not bot.is_admin:
        return False
    member = await perms.fresh_member(ctx, chat_id, user_id)
    return member is not None and not member.user.is_bot and member.status not in {"left", "kicked"} and (
        member.status != "restricted" or getattr(member, "is_member", False))


def keyboard(ctx: BotContext, chat_id: int, rendered: Rendered) -> tuple[InlineKeyboardMarkup | None, dict]:
    rows: list[list[InlineKeyboardButton]] = []
    targets = {}
    for spec in rendered.buttons:
        if spec.kind == "url":
            button = InlineKeyboardButton(text=spec.label, url=spec.target)
        else:
            token = secrets.token_urlsafe(9)
            targets[token] = dict(kind=spec.kind, key=spec.target)
            button = InlineKeyboardButton(text=spec.label,
                callback_data=GgCb(action="menu", chat=chat_id, arg=token).pack())
        if spec.same_row and rows and len(rows[-1]) < 8:
            rows[-1].append(button)
        else:
            rows.append([button])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None, targets


async def send(ctx: BotContext, destination: int, content: Content, f: Fillings, *, kind: str = "note",
               reply_id: int | None = None, thread_id: int | None = None, owner_id: int | None = None,
               extra_keyboard: InlineKeyboardMarkup | None = None, suffix: str = "") -> Delivered:
    if not await authz.active_namespace(ctx):
        return Delivered(actions.failure("content", "namespace_inactive"))
    try:
        rendered = render(content.raw, f, format=content.format, kind=kind)
    except ContentError as error:
        return Delivered(actions.failure("content", str(error)))
    if (content.media_kind is not None and (content.media_kind not in MEDIA or not content.file_id)) or (content.file_id is not None and content.media_kind is None):
        return Delivered(actions.failure("content", "media_invalid"))
    if rendered.controls.mediaspoiler and content.media_kind not in {"photo", "video", "animation"}:
        return Delivered(actions.failure("content", "media_spoiler_unsupported"))
    kb, targets = keyboard(ctx, f.chat_id, rendered)
    if extra_keyboard is not None:
        rows = [*(kb.inline_keyboard if kb else []), *extra_keyboard.inline_keyboard]
        if sum(map(len, rows)) > 100 or any(len(row) > 8 for row in rows):
            return Delivered(actions.failure("content", "button_limit"))
        kb = InlineKeyboardMarkup(inline_keyboard=rows)
    cfg = await ctx.extras["guard"].config(f.chat_id)
    t = actions.group_t(ctx, cfg)
    body = rendered.html + suffix
    body_size = html_size(body)
    if body_size > 4096:
        return Delivered(actions.failure("content", "content_long"))
    if not body and not content.file_id:
        if kb is None:
            return Delivered(actions.failure("content", "content_empty"))
        body = t("gg-menu-prompt")
    common = dict(reply_to_message_id=reply_id, message_thread_id=thread_id,
                  disable_notification=rendered.controls.nonotif, protect_content=rendered.controls.protect)
    messages: list[Message] = []
    steps: list[StepResult] = []
    carrier: Message | None = None

    async def call(method, *args, **kwargs):
        nonlocal carrier
        sent = await method(*args, **kwargs)
        if isinstance(sent, Message):
            messages.append(sent)
            if kwargs.get("reply_markup") is not None:
                carrier = sent
            return sent
        return False  # Every supported send method has a Message receipt, never a Boolean.

    companion = False
    if content.media_kind and content.file_id:
        captionable = content.media_kind not in {"sticker", "video_note"}
        # Keep complete text as a companion rather than cutting markup/entities to fit a caption.
        companion = bool(body) and (not captionable or body_size > 1024)
        kwargs: dict[str, Any] = {**common, "reply_markup": None if companion else kb}
        if captionable:
            kwargs["caption"] = None if companion else body or None
        if rendered.controls.mediaspoiler:
            kwargs["has_spoiler"] = True
        method = getattr(ctx.bot, "send_" + content.media_kind)
        steps.append(await actions.perform("media_send", lambda: call(method, destination, content.file_id, **kwargs)))
    if (not content.file_id or companion) and (body or kb is not None):
        steps.append(await actions.perform("content_send", lambda: call(ctx.bot.send_message, destination,
            body or t("gg-menu-prompt"), reply_markup=kb, link_preview_options=LinkPreviewOptions(
                is_disabled=not rendered.controls.preview), **common)))
    result = result_of(*steps)
    if targets and carrier is not None:
        bound = await authz.bind_message(ctx, carrier, target_chat_id=f.chat_id, owner_id=owner_id,
            kind="content", data=json.dumps(targets, sort_keys=True), slot="content")
        result = result.with_steps(StepResult("menu_binding", "applied" if bound else "failed", None if bound else "state_failed"))
    clean_category = "action" if kind in {"echo", "pin"} else kind
    if clean_category in {"note", "filter", "action"}:
        from bots.groupguard import cleanup
        for sent in messages:
            result = result.with_steps(await cleanup.schedule(ctx,f.chat_id,sent,clean_category))
    return Delivered(result, tuple(messages))


async def private_button(ctx: BotContext, chat_id: int, *, kind: str, key: str = "",
                         label: str, user_id: int | None = None, noformat: bool = False) -> InlineKeyboardMarkup | None:
    token = secrets.token_urlsafe(16)
    state = dict(bot_id=ctx.bot_id, chat_id=chat_id, kind=kind, key=key, owner_id=user_id, noformat=noformat)
    try:
        stored = await ctx.redis.set(ctx.keys("content_open", token), json.dumps(state), ex=OPEN_TTL)
    except RedisError:
        return None
    if not stored:
        return None
    url = f"https://t.me/{ctx.username}?start=ggo_{token}"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=label, url=url)]])
