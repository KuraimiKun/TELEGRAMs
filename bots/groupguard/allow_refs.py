"""Only observed invite target metadata and actual public-chat API resolve numeric exceptions."""

from __future__ import annotations

import contextlib
import hashlib

from aiogram.exceptions import TelegramAPIError
from redis.exceptions import RedisError

from bots.groupguard import locks
from core.sdk.context import BotContext


def key(ctx, link):
    return ctx.keys("invite_target", hashlib.sha256(link.encode()).hexdigest())


async def remember(ctx: BotContext, event) -> None:
    invite = getattr(event, "invite_link", None)
    if invite is None:
        return
    with contextlib.suppress(RedisError):
        await ctx.redis.set(key(ctx, invite.invite_link), str(event.chat.id), ex=30 * 86400)


async def exceptions(ctx: BotContext, message, entries: list[dict]) -> list[dict]:
    numeric = {
        e.get("value")
        for e in entries
        if e.get("kind") == "chat"
        and str(e.get("value", "")).startswith("-")
        and str(e.get("value", ""))[1:].isdigit()
    }
    if not numeric:
        return entries
    result = list(entries)
    targets = list(
        dict.fromkeys(
            item.value for item in locks.detect(message) if item.kind in {"url", "invitelink", "button"}
        )
    )[:20]
    for target in targets:
        kind, identity = locks.url_identity(target)
        if kind != "invitelink":
            continue
        try:
            observed = await ctx.redis.get(key(ctx, target))
            chat_id = observed.decode() if isinstance(observed, bytes) else observed
            if chat_id in numeric:
                result.append(dict(kind="invite", value=target))
                continue
        except RedisError:
            pass
        if (
            identity
            and not identity.startswith(("+", "http", "tg:"))
            and identity not in {"joinchat", "c", "s"}
        ):
            try:
                actual = await ctx.bot.get_chat("@" + identity)
                if (
                    actual is not None
                    and actual.type in {"group", "supergroup", "channel"}
                    and str(actual.id) in numeric
                    and (actual.username or "").lower() == identity.lower()
                ):
                    result.append(dict(kind="invite", value=target))
            except (TelegramAPIError, ValueError):
                pass
    return result
