"""User middleware: registers/upserts bot membership, resolves language, provides translator."""

from __future__ import annotations

import contextlib
import re
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import Message, TelegramObject

from core.i18n import Translate
from core.middlewares._event import unwrap
from core.sdk.context import BotContext


class UserMiddleware(BaseMiddleware):
    def __init__(self, ctx: BotContext) -> None:
        self.ctx = ctx

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        inner = unwrap(event)
        if not tg_user or tg_user.is_bot or not _worth_tracking(inner):
            # Group small talk (no command, no link) must not register every group member as a bot user.
            data["lang"] = self.ctx.translator.resolve(tg_user.language_code if tg_user else None)
            data["t"] = self._translator(data["lang"])
            return await handler(event, data)

        referred_by = None
        if isinstance(inner, Message) and inner.text and inner.text.startswith("/start ref_"):
            with contextlib.suppress(ValueError, IndexError):
                referred_by = int(inner.text.split("ref_", 1)[1].split()[0])

        user, is_new = await self.ctx.users.get_or_create(
            user_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            language_code=self.ctx.translator.resolve(tg_user.language_code),
            referred_by=referred_by,
        )

        user_lang = self.ctx.translator.resolve(user.lang or tg_user.language_code)
        data["user"] = user
        data["is_new_user"] = is_new
        data["lang"] = user_lang

        data["t"] = self._translator(user_lang)
        return await handler(event, data)

    def _translator(self, lang: str) -> Translate:
        def t(key: str, /, **kwargs: Any) -> str:
            return self.ctx.translator.get(lang, key, **kwargs)

        return t


_TRACKED_ENTITIES = {"url", "text_link", "bot_command"}
_LINKISH = re.compile(r"https?://|\b[\w-]+\.[a-z]{2,}/", re.IGNORECASE)


def _worth_tracking(event: TelegramObject) -> bool:
    """Everything except plain group chatter counts as using the bot."""
    if not isinstance(event, Message) or event.chat.type == ChatType.PRIVATE:
        return True
    entities = (event.entities or []) + (event.caption_entities or [])
    if any(e.type in _TRACKED_ENTITIES for e in entities):
        return True
    text = event.text or event.caption or ""
    return text.startswith("/") or bool(_LINKISH.search(text))
