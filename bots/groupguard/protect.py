"""Automatic protection for every group message: flood, locks, blocklist, newcomer links, AI anti-spam.

Runs as an outer middleware on the bot's group router so it sees *every* message before any handler;
offending messages are deleted and never reach commands, notes or filters.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, Update

from bots.groupguard import actions, authz, blocklists, flood, lock_runtime, perms
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.service import GuardService
from core.ai import AIError
from core.log import get_logger
from core.sdk.context import BotContext

log = get_logger(__name__)

INVITE = re.compile(r"(t\.me|telegram\.(me|dog))/(\+|joinchat/)[\w-]+", re.IGNORECASE)
LINK = re.compile(r"(https?://|www\.)\S+|\b[\w-]+\.(com|net|org|io|me|ru|xyz|top|link|ly|gg|app)\b", re.IGNORECASE)
NEWBIE_AI_MESSAGES = 3

_SPAM_SCHEMA = {
    "type": "object",
    "properties": {"spam": {"type": "boolean"}},
    "required": ["spam"],
    "additionalProperties": False,
}
_SPAM_SYSTEM = (
    "You detect spam in Telegram group chats: ads, crypto/investment scams, adult promotion, "
    "'DM me' recruiting, fake giveaways, mass-posted links. Normal conversation, questions and greetings are "
    "not spam. Answer in JSON."
)


def message_kinds(message: Message) -> set[str]:
    kinds: set[str] = set()
    text = message.text or message.caption or ""
    entities = (message.entities or []) + (message.caption_entities or [])
    if INVITE.search(text):
        kinds.add("invites")
    if any(e.type in ("url", "text_link") for e in entities) or LINK.search(text):
        kinds.add("links")
    if message.forward_origin is not None:
        kinds.add("forwards")
    if message.photo or message.video or message.document or message.audio:
        kinds.add("media")
    if message.sticker:
        kinds.add("stickers")
    if message.animation:
        kinds.add("gifs")
    if message.voice or message.video_note:
        kinds.add("voice")
    if message.poll:
        kinds.add("polls")
    return kinds


def blocked_word(cfg: ChatConfig, text: str) -> str | None:
    low = text.lower()
    for word in cfg.blocklist:
        if re.search(rf"(?<!\w){re.escape(word)}(?!\w)", low):
            return word
    return None



def newbie_key(ctx: BotContext, chat_id: int, user_id: int) -> str:
    return ctx.keys("newbie", chat_id, user_id)


async def mark_newbie(ctx: BotContext, cfg: ChatConfig, chat_id: int, user_id: int) -> None:
    if cfg.newbie_hours > 0 or cfg.ai_spam:
        hours = max(cfg.newbie_hours, 24)
        await ctx.redis.set(newbie_key(ctx, chat_id, user_id), "0", ex=hours * 3600)


async def is_spam(ctx: BotContext, text: str, user_id: int) -> bool:
    if ctx.ai is None or len(text.strip()) < 8:
        return False
    try:
        res = await ctx.ai.ask(
            text[:1500], system=_SPAM_SYSTEM, bot=ctx.metric_name, user_id=user_id, schema=_SPAM_SCHEMA,
            max_tokens=50, fast=True,
        )
    except AIError:
        return False
    return isinstance(res.data, dict) and bool(res.data.get("spam"))


async def cas_banned(ctx: BotContext, url: str, user_id: int) -> bool:
    """Combot Anti-Spam lookup, cached for a day. Network problems never block a join."""
    key = ctx.keys("cas", user_id)
    cached = await (ctx.cache_redis or ctx.redis).get(key)
    if cached is not None:
        return cached == b"1"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url, params={"user_id": user_id})
            banned = bool(resp.json().get("ok"))
    except (httpx.HTTPError, ValueError):
        return False
    await (ctx.cache_redis or ctx.redis).set(key, "1" if banned else "0", ex=86400)
    return banned


@dataclass(frozen=True, slots=True)
class EventIdentity:
    bot_id: int
    chat_id: int
    message_id: int
    update_id: int | None
    edited: bool
    content_version: str

    @classmethod
    def of(cls, ctx: BotContext, message: Message, data: dict[str, Any]) -> EventIdentity:
        update = data.get("event_update")
        edited = isinstance(update, Update) and update.edited_message is not None
        payload = message.model_dump(mode="json", exclude={"date", "edit_date"}, exclude_none=True)
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        return cls(ctx.bot_id, message.chat.id, message.message_id, update.update_id if isinstance(update, Update) else None,
                   edited, digest)


class ProtectMiddleware(BaseMiddleware):
    def __init__(self, ctx: BotContext, svc: GuardService) -> None:
        self.ctx = ctx
        self.svc = svc

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or event.chat.type not in {"group", "supergroup"}:
            return await handler(event, data)
        from bots.groupguard.cleanup import service_kind
        if service_kind(event) is not None:
            return await handler(event, data)
        from bots.groupguard.handlers.tools import linked_controls
        if await linked_controls(self.ctx, event):
            return None
        ctx, msg = self.ctx, event
        actor = authz.actor_from_message(ctx, msg)
        identity = EventIdentity.of(ctx, msg, data)
        data["guard_event"] = identity
        data["guard_actor"] = actor
        user = msg.from_user
        if actor.kind == "human":
            await perms.remember(ctx, user)
        cfg = await self.svc.config(msg.chat.id, fresh=True)
        exempt = actor.kind == "anonymous_group" or (user is not None and msg.sender_chat is None and user.id == ctx.bot_id)
        if not exempt and user is not None and msg.sender_chat is None:
            actual = await perms.fresh_rights(ctx, msg.chat.id, user.id)
            exempt = actual is not None and actual.is_admin
        if actor.kind == "human" and user is not None:
            from bots.groupguard import fed_enforcement
            await fed_enforcement.observe(ctx, msg.chat.id, user)
            if not exempt and await fed_enforcement.passive(ctx, msg.chat.id, user,
                    event=f"message:{msg.message_id}"):
                return None
        if not exempt and actor.kind == "human" and user is not None:
            exempt = await self.svc.approval(msg.chat.id, user.id) is not None
        if await flood.enforce(ctx, msg, actor, cfg, eligible=not exempt and actor.kind == "human", edited=identity.edited):
            return None
        if exempt:
            return await handler(event, data)
        chat_id = msg.chat.id
        t = actions.group_t(ctx, cfg)
        name = actions.mention(user.id, user.first_name) if user is not None and actor.kind == "human" else "sender"
        title = msg.chat.title

        kinds = message_kinds(msg)
        if await lock_runtime.enforce(ctx,msg,actor,cfg):
            return None

        text = msg.text or msg.caption or ""
        if await blocklists.enforce(ctx,msg,actor,cfg):
            return None

        newbie = await ctx.redis.get(newbie_key(ctx, chat_id, user.id)) if actor.kind == "human" and user is not None else None
        if newbie is not None and user is not None:
            if cfg.newbie_hours > 0 and kinds & {"links", "invites", "forwards"}:
                result = await actions.delete(ctx, chat_id, msg.message_id)
                await actions.announce(ctx, cfg, chat_id, title, result,
                                       t("gg-newbie-links", user=name, hours=str(cfg.newbie_hours)))
                return None
            seen = await ctx.redis.incr(newbie_key(ctx, chat_id, user.id)) if not identity.edited else int(newbie)
            if cfg.ai_spam and seen <= NEWBIE_AI_MESSAGES and await is_spam(ctx, text, user.id):
                cfg = await self.svc.config(chat_id, fresh=True)
                if not cfg.ai_spam:
                    return await handler(event, data)
                cap = await authz.internal_authorize(ctx, chat_id, frozenset({"delete_messages", "restrict_members"}))
                if not cap.allowed:
                    await actions.announce(ctx, cfg, chat_id, title, actions.failure("ai_spam", cap.code), "")
                    return None
                deleted = await actions.delete(ctx, chat_id, msg.message_id)
                result = await actions.punish(ctx, chat_id, user.id, "ban", None)
                await actions.announce(ctx, cfg, chat_id, title, result.with_steps(*deleted.steps),
                                       t("gg-spam-banned", user=name))
                return None

        return await handler(event, data)
