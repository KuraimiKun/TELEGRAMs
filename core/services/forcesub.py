"""Forced channel subscription ("join our channel to use the bot"), available to every bot.

Bots call :meth:`ForceSubService.missing` before a core action. When channels are missing they show the
join prompt via :func:`core.routers.forcesub.prompt`, storing a small replay payload; once the user taps
"I've joined" the core router calls the module's ``on_force_sub_passed`` hook with that payload.
"""

from __future__ import annotations

import json
import secrets
from typing import Any

from aiogram import Bot
from redis.asyncio import Redis

from core.db.models import ForceSubChannel
from core.log import get_logger
from core.redis import KeySpace
from core.services.groups import GroupService

log = get_logger(__name__)

MEMBER_OK_TTL = 600  # a positive check is trusted for 10 minutes
PENDING_TTL = 1800
LEFT_STATUSES = {"left", "kicked"}


class ForceSubService:
    def __init__(self, bot: Bot, groups: GroupService, redis: Redis, keys: KeySpace) -> None:
        self.bot = bot
        self.groups = groups
        self.redis = redis
        self.keys = keys

    async def missing(self, user_id: int, *, fail_closed: bool = False) -> list[ForceSubChannel]:
        """Channels the user still has to join. Errors (bot not admin, channel gone) are logged and treated
        as "joined" unless ``fail_closed``, so a misconfigured channel never locks every user out."""
        ok_key = self.keys("fsub", "ok", user_id)
        if await self.redis.exists(ok_key):
            return []
        channels = await self.groups.list_channels()
        unjoined: list[ForceSubChannel] = []
        for ch in channels:
            try:
                member = await self.bot.get_chat_member(chat_id=ch.chat_id, user_id=user_id)
                if member.status in LEFT_STATUSES:
                    unjoined.append(ch)
            except Exception as e:
                log.warning("force_sub_check_failed", chat_id=ch.chat_id, error=str(e))
                if fail_closed:
                    unjoined.append(ch)
        if not unjoined:
            await self.redis.set(ok_key, "1", ex=MEMBER_OK_TTL)
        return unjoined

    async def forget(self, user_id: int) -> None:
        await self.redis.delete(self.keys("fsub", "ok", user_id))

    async def save_pending(self, user_id: int, payload: dict[str, Any]) -> str:
        token = secrets.token_hex(5)
        data = json.dumps({"user_id": user_id, "payload": payload})
        await self.redis.set(self.keys("fsub", "pending", token), data, ex=PENDING_TTL)
        return token

    async def pop_pending(self, token: str, user_id: int) -> dict[str, Any] | None:
        raw = await self.redis.getdel(self.keys("fsub", "pending", token))
        if not raw:
            return None
        data = json.loads(raw)
        return data["payload"] if data.get("user_id") == user_id else None
