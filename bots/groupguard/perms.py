"""Display caches, fresh Telegram rights, observed targets and separate timer/action parsing."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import timedelta

from aiogram.exceptions import TelegramAPIError
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner, Message, User
from redis.exceptions import RedisError

from bots.groupguard.scope import target_chat
from core.sdk.context import BotContext

ADMIN_TTL = 300
USERNAME_TTL = 30 * 86400
PSEUDO_USERS = {1087968824, 136817688}
_DURATION = re.compile(r"^(\d{1,12})([smhdw])$", re.IGNORECASE)
_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
MIN_UNTIL, MAX_UNTIL = timedelta(seconds=60), timedelta(days=365)
ALIASES = {"restrict_members": "restrict", "delete_messages": "delete", "pin_messages": "pin",
           "invite_users": "invite", "promote_members": "promote", "post_messages": "post"}


def parse_duration(token: str) -> timedelta | None:
    """General timer utility: deliberately independent of sanction bounds."""
    match = _DURATION.fullmatch(token.strip())
    if not match:
        return None
    seconds = int(match[1]) * _UNITS[match[2].lower()]
    return timedelta(seconds=seconds) if 0 < seconds <= 366 * 86400 else None


@dataclass(frozen=True, slots=True)
class DurationResult:
    kind: str  # absent | valid | invalid
    value: timedelta | None = None
    error: str | None = None


def parse_action_duration(token: str | None, *, required: bool = False) -> DurationResult:
    if token is None:
        return DurationResult("invalid" if required else "absent", error="duration_required" if required else None)
    value = parse_duration(token)
    if value is None or not MIN_UNTIL <= value <= MAX_UNTIL:
        return DurationResult("invalid", error="duration_invalid")
    return DurationResult("valid", value)


def split_action_args(args: str, *, temporary_required: bool = False) -> tuple[DurationResult, str]:
    parts = args.strip().split(maxsplit=1)
    if not parts:
        return parse_action_duration(None, required=temporary_required), ""
    token = parts[0]
    shaped = bool(re.match(r"^[+\-\d.]", token))
    if temporary_required or shaped:
        return parse_action_duration(token, required=temporary_required), parts[1] if len(parts) > 1 else ""
    return DurationResult("absent"), args.strip()


def human(delta: timedelta) -> str:
    seconds = int(delta.total_seconds())
    for unit, size in (("w", 604800), ("d", 86400), ("h", 3600), ("m", 60)):
        if seconds >= size and seconds % size == 0:
            return f"{seconds // size}{unit}"
    return f"{seconds}s"


@dataclass(frozen=True, slots=True)
class Rights:
    is_admin: bool = False
    creator: bool = False
    restrict: bool = False
    delete: bool = False
    pin: bool = False
    invite: bool = False
    change_info: bool = False
    promote: bool = False
    manage_topics: bool = False
    post: bool = False

    def allows(self, right: str) -> bool:
        field = ALIASES.get(right, right)
        if field not in {*self.__slots__, "admin"}:
            return False
        return self.creator or (self.is_admin and (field == "admin" or bool(getattr(self, field, False))))

    def allows_all(self, rights: frozenset[str]) -> bool:
        return all(self.allows(r) for r in rights)


def member_rights(member: object) -> Rights:
    if isinstance(member, ChatMemberOwner):
        return Rights(is_admin=True, creator=True)
    if isinstance(member, ChatMemberAdministrator):
        return Rights(is_admin=True, restrict=member.can_restrict_members, delete=member.can_delete_messages,
                      pin=bool(member.can_pin_messages), invite=bool(member.can_invite_users),
                      change_info=member.can_change_info, promote=member.can_promote_members,
                      manage_topics=bool(member.can_manage_topics), post=bool(member.can_post_messages))
    return Rights()


async def fresh_member(ctx: BotContext, chat_id: int, user_id: int):
    try:
        member = await ctx.bot.get_chat_member(chat_id, user_id)
    except TelegramAPIError:
        return None
    if member is None or member.user.id != user_id:
        return None
    return member


async def fresh_rights(ctx: BotContext, chat_id: int, user_id: int) -> Rights | None:
    member = await fresh_member(ctx, chat_id, user_id)
    return member_rights(member) if member is not None else None


async def admins(ctx: BotContext, chat_id: int) -> dict[int, Rights]:
    """Cached display only; old records omit new fields, which default false."""
    key = ctx.keys("admins", chat_id)
    raw = await ctx.redis.get(key)
    if raw:
        try:
            return {int(k): Rights(**{n: v for n, v in vals.items() if n in Rights.__slots__})
                    for k, vals in json.loads(raw).items()}
        except (ValueError, TypeError, AttributeError):
            pass
    try:
        members = await ctx.bot.get_chat_administrators(chat_id)
        out = {m.user.id: member_rights(m) for m in members}
    except (TelegramAPIError, TypeError):
        return {}
    await ctx.redis.set(key, json.dumps({k: vars_of(v) for k, v in out.items()}), ex=ADMIN_TTL)
    return out


def vars_of(r: Rights) -> dict[str, bool]:
    return {f: getattr(r, f) for f in Rights.__slots__}


async def forget_admins(ctx: BotContext, chat_id: int) -> None:
    await ctx.redis.delete(ctx.keys("admins", chat_id))


async def rights(ctx: BotContext, chat_id: int, user_id: int) -> Rights:
    return await fresh_rights(ctx, chat_id, user_id) or Rights()


async def is_admin(ctx: BotContext, chat_id: int, user_id: int | None) -> bool:
    return user_id is not None and (await rights(ctx, chat_id, user_id)).is_admin


async def sender_rights(ctx: BotContext, message: Message) -> Rights:
    if message.sender_chat is not None or message.from_user is None or message.from_user.is_bot:
        return Rights()
    return await rights(ctx, message.chat.id, message.from_user.id)


def valid_human_id(user_id: int) -> bool:
    return 0 < user_id < 2**52 and user_id not in PSEUDO_USERS


async def remember(ctx: BotContext, user: User | None) -> None:
    if user is None or not user.username or user.is_bot or not valid_human_id(user.id):
        return
    key = ctx.keys("uname", user.username.lower())
    try:
        old = await ctx.redis.get(key)
        ambiguous = False
        if old:
            decoded = json.loads(old)
            ambiguous = (decoded.get("ambiguous", False) or decoded["id"] != user.id) if isinstance(decoded, dict) else decoded != user.id
        await ctx.redis.set(key, json.dumps({"id": user.id, "username": user.username.lower(),
                                           "ambiguous": ambiguous}), ex=USERNAME_TTL)
    except (RedisError, ValueError, TypeError, KeyError):
        return


class TargetError(ValueError):
    pass


@dataclass(slots=True)
class Target:
    user_id: int
    name: str
    args: list[str]
    remaining: str = ""


async def resolve_target(ctx: BotContext, message: Message, args: str | list[str]) -> Target | None:
    raw = args.strip() if isinstance(args, str) else " ".join(args)
    reply = message.reply_to_message
    if reply is not None:
        if reply.sender_chat is not None or reply.from_user is None or reply.from_user.is_bot:
            raise TargetError("target_invalid")
        uid, name, remaining = reply.from_user.id, reply.from_user.first_name, raw
    else:
        parts = raw.split(maxsplit=1)
        if not parts:
            return None
        first, remaining = parts[0], parts[1] if len(parts) > 1 else ""
        text = message.text or ""
        command_end = text.find(" ")
        arg_start = command_end + 1 if command_end >= 0 else len(text)
        while arg_start < len(text) and text[arg_start].isspace():
            arg_start += 1
        offset = len(text[:arg_start].encode("utf-16-le")) // 2
        entity = next((e for e in message.entities or [] if e.type == "text_mention" and e.offset == offset), None)
        if entity is not None and entity.user is not None:
            if entity.user.is_bot:
                raise TargetError("target_invalid")
            uid, name = entity.user.id, entity.user.first_name
            visible = text.encode("utf-16-le")[offset * 2:(offset + entity.length) * 2].decode("utf-16-le")
            remaining = raw[len(visible):].lstrip()
        elif first.startswith("@"):
            try:
                cached = await ctx.redis.get(ctx.keys("uname", first[1:].lower()))
                data = json.loads(cached) if cached else None
                if data is None or (isinstance(data, dict) and data.get("ambiguous")):
                    raise TargetError("target_unknown")
                uid = int(data["id"] if isinstance(data, dict) else data)
                bot = await fresh_rights(ctx, target_chat(message).id, ctx.bot_id)
                member = await fresh_member(ctx, target_chat(message).id, uid) if bot is not None and bot.is_admin else None
                if member is None or member.user.is_bot or (member.user.username or "").lower() != first[1:].lower():
                    raise TargetError("target_unknown")
                name = member.user.first_name
            except (RedisError, ValueError, TypeError, KeyError) as e:
                raise TargetError("target_unknown") from e
        elif re.fullmatch(r"[+-]?\d+", first):
            if len(first) > 16:
                raise TargetError("target_invalid")
            uid, name = int(first), first
        else:
            return None
    if not valid_human_id(uid) or uid == ctx.bot_id:
        raise TargetError("target_invalid")
    return Target(uid, name, remaining.split(), remaining)


async def target_error(ctx: BotContext, chat_id: int, user_id: int) -> str | None:
    if not valid_human_id(user_id) or user_id == ctx.bot_id:
        return "target_invalid"
    bot = await fresh_rights(ctx, chat_id, ctx.bot_id)
    if bot is None or not bot.is_admin:
        return "lookup_failed"
    member = await fresh_member(ctx, chat_id, user_id)
    if member is None:
        return "lookup_failed"
    if member.user.is_bot:
        return "target_invalid"
    if member_rights(member).is_admin:
        return "target_admin"
    return None
