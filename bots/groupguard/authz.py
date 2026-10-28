"""Execution-time rights and bounded server-created callback bindings."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

from aiogram.types import CallbackQuery, Message
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from bots.groupguard import perms
from bots.groupguard.contracts import Actor, ActorKind, Right
from core.db.models import ChildBot
from core.sdk.context import BotContext

PANEL_TTL = 3600


def actor_from_message(ctx: BotContext, message: Message) -> Actor:
    kind: ActorKind = "unknown"
    human = None
    sender = message.sender_chat
    if sender is not None:
        kind = "anonymous_group" if sender.id == message.chat.id and message.chat.type in {"group", "supergroup"} else "channel"
    elif message.from_user is not None:
        kind = "bot" if message.from_user.is_bot else "human" if perms.valid_human_id(message.from_user.id) else "unknown"
        human = message.from_user.id if kind == "human" else None
    return Actor(ctx.bot_id, message.chat.id, kind, human, sender.id if sender else None,
                 message.message_id, message.message_thread_id,
                 message.from_user.id if kind == "bot" and message.from_user is not None else None)


def actor_from_callback(ctx: BotContext, query: CallbackQuery) -> Actor:
    msg = query.message if isinstance(query.message, Message) else None
    kind: ActorKind = "human" if not query.from_user.is_bot and perms.valid_human_id(query.from_user.id) else "bot"
    return Actor(ctx.bot_id, msg.chat.id if msg else 0, kind, query.from_user.id if kind == "human" else None,
                 message_id=msg.message_id if msg else None, thread_id=msg.message_thread_id if msg else None)


@dataclass(frozen=True, slots=True)
class Authorization:
    allowed: bool
    code: str
    human_id: int | None = None
    missing: frozenset[str] = frozenset()

    def __bool__(self) -> bool:
        raise TypeError("Inspect Authorization.allowed explicitly")


async def active_namespace(ctx: BotContext, session: AsyncSession | None = None) -> bool:
    if ctx.extras.get("owned_maintenance"):
        return False  # A private cleanup context can never receive human/automated command authority.
    if ctx.child is None:
        return True
    if session is None:
        async with ctx.sm() as owned:
            return await active_namespace(ctx, owned)
    child = await session.get(ChildBot, ctx.bot_id, populate_existing=True)
    return child is not None and child.status == "active" and child.template == "groupguard"


async def authorize(ctx: BotContext, actor: Actor, *, target_chat_id: int,
                    caller_rights: frozenset[Right], bot_rights: frozenset[Right], require_admin: bool = True,
                    session: AsyncSession | None = None) -> Authorization:
    if not await active_namespace(ctx,session):
        return Authorization(False, "namespace_inactive")
    if actor.bot_id != ctx.bot_id or target_chat_id >= 0:
        return Authorization(False, "wrong_scope")
    if actor.kind == "bot":
        cfg = await ctx.extras["guard"].config(target_chat_id, fresh=True)
        if (cfg.bot2bot_mode == "off" or actor.bot_sender_id is None or actor.bot_sender_id == ctx.bot_id
                or actor.source_chat_id != target_chat_id or "creator" in caller_rights):
            return Authorization(False, "unattributed")
        member = await perms.fresh_member(ctx,target_chat_id,actor.bot_sender_id)
        if (member is None or not member.user.is_bot or member.status in {"creator", "left", "kicked"}
                or (member.status == "restricted" and not member.is_member)):
            return Authorization(False, "caller_denied")
        actual = perms.member_rights(member)
        if (cfg.bot2bot_mode == "admin" or require_admin) and not actual.is_admin:
            return Authorization(False, "caller_denied")
        missing = frozenset(right for right in caller_rights if not actual.allows(right))
        if missing:
            return Authorization(False, "caller_denied", missing=missing)
        receiver = await perms.fresh_rights(ctx,target_chat_id,ctx.bot_id)
        absent = frozenset(right for right in bot_rights if receiver is None or not receiver.allows(right))
        if receiver is None or not receiver.is_admin or absent:
            return Authorization(False,"bot_denied",missing=absent)
        return Authorization(True,"bot")
    assumed = actor.kind == "anonymous_group" and actor.source_chat_id == target_chat_id and "creator" not in caller_rights
    if assumed:
        cfg = await ctx.extras["guard"].config(target_chat_id, fresh=True)
        assumed = cfg.anonadmin and require_admin
    if not assumed and (actor.kind != "human" or actor.human_id is None):
        return Authorization(False, "unattributed")
    bot = await perms.fresh_rights(ctx, target_chat_id, ctx.bot_id)
    if bot is None:
        return Authorization(False, "lookup_failed")
    if not bot.is_admin or not bot.allows_all(bot_rights):
        return Authorization(False, "bot_denied", missing=bot_rights)
    if assumed:
        # Explicit group opt-in assumes ordinary admin rights bounded by this bot's actual rights.
        if not bot.allows_all(caller_rights):
            return Authorization(False, "caller_denied", missing=caller_rights)
        return Authorization(True, "assumed_anonymous")
    assert actor.human_id is not None
    member = await perms.fresh_member(ctx, target_chat_id, actor.human_id)
    if member is None or member.user.is_bot:
        return Authorization(False, "lookup_failed")
    caller = perms.member_rights(member)
    missing = frozenset(r for r in caller_rights if not caller.allows(r))
    if ((require_admin and not caller.is_admin) or missing or member.status in {"left", "kicked"}
            or (member.status == "restricted" and not member.is_member)):
        return Authorization(False, "caller_denied", missing=missing)
    return Authorization(True, "ok", actor.human_id)


async def internal_authorize(ctx: BotContext, chat_id: int, required: frozenset[Right]) -> Authorization:
    """Internal origin has no human rights. Policy is checked by the owning flow."""
    if not await active_namespace(ctx):
        return Authorization(False, "namespace_inactive")
    if chat_id >= 0:
        return Authorization(False, "wrong_scope")
    bot = await perms.fresh_rights(ctx, chat_id, ctx.bot_id)
    if bot is None:
        return Authorization(False, "lookup_failed")
    if not bot.is_admin or not bot.allows_all(required):
        return Authorization(False, "bot_denied", missing=required)
    return Authorization(True, "ok")


def binding_key(ctx: BotContext, message: Message, *, slot: str = "panel") -> str:
    return ctx.keys("gg", slot, message.chat.id, message.message_id)


async def bind_message(ctx: BotContext, message: Message, *, target_chat_id: int,
                       owner_id: int | None, kind: str, data: str = "", slot: str = "panel") -> bool:
    state = dict(bot_id=ctx.bot_id, target_chat_id=target_chat_id, owner_id=owner_id,
                 message_chat_id=message.chat.id, message_id=message.message_id,
                 thread_id=message.message_thread_id, kind=kind, data=data,created=time.time())
    try:
        return bool(await ctx.redis.set(binding_key(ctx, message, slot=slot), json.dumps(state), ex=PANEL_TTL))
    except RedisError:
        return False


async def bound_message(ctx: BotContext, query: CallbackQuery, *, target_chat_id: int,
                        kind: str, data: str | None = None, slot: str = "panel") -> bool:
    if not isinstance(query.message, Message) or query.from_user.is_bot:
        return False
    msg = query.message
    if msg.from_user is None or msg.from_user.id != ctx.bot_id:
        return False
    try:
        raw = await ctx.redis.get(binding_key(ctx, msg, slot=slot))
        state = json.loads(raw) if raw else {}
        return (state.get("bot_id") == ctx.bot_id and state.get("target_chat_id") == target_chat_id
                and state.get("message_chat_id") == msg.chat.id and state.get("message_id") == msg.message_id
                and state.get("thread_id") == msg.message_thread_id and state.get("kind") == kind
                and state.get("owner_id") in (None, query.from_user.id)
                and (msg.chat.type != "private" or kind == "join_request" or msg.chat.id == query.from_user.id)
                and (data is None or state.get("data") == data))
    except (RedisError, ValueError, TypeError, AttributeError):
        return False
