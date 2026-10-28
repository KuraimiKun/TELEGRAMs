"""Delivering one anonymous message (any media kind), safety screening and VIP hints."""

from __future__ import annotations

import re
from dataclasses import dataclass

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, Message

from bots.anonymous.models import AnonMessage
from core.ai import AIError
from core.db.models import User
from core.log import get_logger
from core.sdk.context import BotContext
from core.ui.text import esc

log = get_logger(__name__)

CAPTIONABLE = {"photo", "video", "animation", "voice", "audio"}
UNCAPTIONED = {"sticker", "video_note"}
CAPTION_LIMIT = 1024
_EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿]")


def kind_of(message: Message) -> str | None:
    if message.text:
        return "text"
    for kind in ("photo", "video", "animation", "voice", "audio", "sticker", "video_note"):
        if getattr(message, kind, None):
            return kind
    return None


def body_of(message: Message) -> str:
    return message.text or message.caption or ""


def quote(text: str | None, limit: int = 160) -> str:
    if not text:
        return ""
    snippet = text if len(text) <= limit else text[: limit - 1] + "…"
    return f"\n<blockquote>{esc(snippet)}</blockquote>"


async def display_name(ctx: BotContext, user_id: int) -> str:
    async with ctx.sm() as session:
        user = await session.get(User, user_id)
    return (user.first_name if user and user.first_name else None) or "🙂"


@dataclass(slots=True)
class Delivered:
    ok: bool
    blocked_bot: bool = False


async def deliver(
    ctx: BotContext, source: Message, recipient_id: int, header: str, kb: InlineKeyboardMarkup
) -> Delivered:
    """Send ``source`` to ``recipient_id`` under ``header`` without revealing who sent it.

    Media is *copied* (never forwarded), so Telegram shows no "forwarded from".
    """
    kind = kind_of(source)
    body = body_of(source)
    try:
        if kind == "text":
            await ctx.bot.send_message(recipient_id, f"{header}\n\n{esc(body)}", reply_markup=kb)
        elif kind in CAPTIONABLE:
            caption = header + (f"\n\n{esc(body)}" if body else "")
            if len(caption) > CAPTION_LIMIT:
                caption = header + f"\n\n{esc(body[: CAPTION_LIMIT - len(header) - 10])}…"
            await ctx.bot.copy_message(
                chat_id=recipient_id, from_chat_id=source.chat.id, message_id=source.message_id,
                caption=caption, reply_markup=kb,
            )
        else:
            head = await ctx.bot.send_message(recipient_id, header, reply_markup=kb)
            await ctx.bot.copy_message(
                chat_id=recipient_id, from_chat_id=source.chat.id, message_id=source.message_id,
                reply_to_message_id=head.message_id,
            )
    except TelegramForbiddenError:
        await ctx.users.mark_blocked(recipient_id)
        return Delivered(ok=False, blocked_bot=True)
    except TelegramBadRequest as e:
        log.warning("anon_delivery_failed", bot=ctx.slug, kind=kind, error=str(e))
        return Delivered(ok=False)
    return Delivered(ok=True)


_FILTER_SCHEMA = {
    "type": "object",
    "properties": {"allowed": {"type": "boolean"}, "reason": {"type": "string"}},
    "required": ["allowed", "reason"],
    "additionalProperties": False,
}
_FILTER_SYSTEM = (
    "You moderate messages sent anonymously to people on Telegram. Block only clear abuse: threats, "
    "harassment or bullying aimed at the recipient, sexual content involving minors, doxxing, hate speech, "
    "or self-harm encouragement. Allow everything else, including flirting, criticism, jokes and profanity "
    "that is not aimed at hurting the recipient. Answer in JSON."
)


async def is_allowed(ctx: BotContext, text: str, sender_id: int) -> bool:
    """AI screening (fails open: an AI outage must not silence everyone)."""
    if ctx.ai is None or not text.strip():
        return True
    try:
        res = await ctx.ai.ask(
            f"Message:\n{text[:2000]}", system=_FILTER_SYSTEM, bot=ctx.metric_name, user_id=sender_id,
            schema=_FILTER_SCHEMA, max_tokens=200, fast=True,
        )
    except AIError:
        return True
    return bool(res.data.get("allowed", True)) if isinstance(res.data, dict) else True


def time_of_day(hour: int) -> str:
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "afternoon"
    if 18 <= hour < 23:
        return "evening"
    return "night"


_HINT_SYSTEM = (
    "You write one playful, kind sentence describing the *writing style and mood* of an anonymous message, "
    "like a fortune teller. Never guess or suggest who wrote it, their name, age, gender, location or any "
    "identifying detail; never quote the message. Reply in the language with code '{lang}'. Max 30 words."
)


async def hint_for(ctx: BotContext, msg: AnonMessage, lang: str, user_id: int) -> tuple[str, str, int, str | None]:
    """(time of day, kind, emoji count, AI vibe sentence or None)."""
    text = msg.text or ""
    vibe = None
    if ctx.ai is not None and text.strip():
        try:
            res = await ctx.ai.ask(
                text[:1500], system=_HINT_SYSTEM.format(lang=lang), bot=ctx.metric_name, user_id=user_id,
                max_tokens=120, fast=True,
            )
            vibe = res.text.strip() or None
        except AIError:
            vibe = None
    return time_of_day(msg.created_at.hour), msg.kind, len(_EMOJI.findall(text)), vibe
