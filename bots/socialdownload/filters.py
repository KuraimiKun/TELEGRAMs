"""Custom aiogram filters for SocialDownload bot."""

from __future__ import annotations

from aiogram.filters import Filter
from aiogram.types import Message

from bots.socialdownload.engine.platforms import extract_urls
from core.filters import ChatType, IsAdmin, IsSuperAdmin

__all__ = ["ChatType", "HasURL", "IsAdmin", "IsSuperAdmin"]


class HasURL(Filter):
    async def __call__(self, message: Message) -> bool | dict[str, list[str]]:
        text = message.text or message.caption
        if not text:
            return False
        urls = extract_urls(text)
        if not urls:
            return False
        return {"urls": urls}
