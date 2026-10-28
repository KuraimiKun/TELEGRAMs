"""Runtime settings persisted in the database per bot, cached in-process."""

from __future__ import annotations

import time
from types import UnionType
from typing import Any, Union, get_args, get_origin

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.db.models import BotSetting
from core.log import get_logger
from core.sdk.module import BaseBotSettings

log = get_logger(__name__)


def field_type(model: type[BaseBotSettings], key: str) -> type:
    """Editable kind of a setting: bool, int, float, str or list (``list[str]``). ``X | None`` unwraps to X."""
    ann = model.model_fields[key].annotation
    args = [a for a in get_args(ann) if a is not type(None)]
    if get_origin(ann) in (Union, UnionType) and len(args) == 1:
        ann = args[0]
    if get_origin(ann) is list or ann is list:
        return list
    if ann in (bool, int, float, str):
        return ann
    raise TypeError(f"setting {key!r} has unsupported type {ann!r}")


def is_optional(model: type[BaseBotSettings], key: str) -> bool:
    return type(None) in get_args(model.model_fields[key].annotation)


def parse_value(model: type[BaseBotSettings], key: str, raw: str) -> Any:
    """Parse admin text input into the proper type for ``key``; '-' clears strings/lists/optionals."""
    kind = field_type(model, key)
    raw = raw.strip()
    if raw == "-" and is_optional(model, key):
        return None
    if kind is bool:
        if raw.lower() in ("1", "true", "yes", "on"):
            return True
        if raw.lower() in ("0", "false", "no", "off"):
            return False
        raise ValueError("expected on/off (or 1/0)")
    if kind is int:
        value = int(raw)
        if value < 0:
            raise ValueError("must be >= 0")
        return value
    if kind is float:
        return float(raw)
    if kind is list:
        if raw in ("-", ""):
            return []
        return [x.strip().lower() for x in raw.split(",") if x.strip()]
    return "" if raw == "-" else raw


class SettingsService[T: BaseBotSettings]:
    """Reads and writes bot-scoped settings with short in-process caching."""

    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
        bot_id: int,
        model: type[T] = BaseBotSettings,  # type: ignore[assignment]
        ttl: float = 10.0,
    ) -> None:
        self._sm = sessionmaker
        self.bot_id = bot_id
        self.model = model
        self._ttl = ttl
        self._cached: T | None = None
        self._loaded_at = 0.0

    async def get(self) -> T:
        if self._cached is None or time.monotonic() - self._loaded_at > self._ttl:
            async with self._sm() as session:
                stmt = select(BotSetting).where(BotSetting.bot_id == self.bot_id)
                rows = (await session.execute(stmt)).scalars().all()
            data = {r.key: r.value for r in rows if r.key in self.model.model_fields}
            try:
                self._cached = self.model(**data)
            except ValidationError as e:
                # Keep every valid stored value; drop only the broken ones (and say so loudly).
                bad = {str(err["loc"][0]) for err in e.errors() if err.get("loc")}
                log.error("invalid_stored_settings", bot_id=self.bot_id, keys=sorted(bad))
                self._cached = self.model(**{k: v for k, v in data.items() if k not in bad})
            self._loaded_at = time.monotonic()
        return self._cached

    async def set(self, key: str, value: Any) -> T:
        if key not in self.model.model_fields:
            raise KeyError(key)

        current = (await self.get()).model_dump()
        current[key] = value
        validated = self.model(**current)

        async with self._sm() as session:
            stmt = select(BotSetting).where(BotSetting.bot_id == self.bot_id, BotSetting.key == key)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                session.add(BotSetting(bot_id=self.bot_id, key=key, value=getattr(validated, key)))
            else:
                row.value = getattr(validated, key)
            await session.commit()

        self._cached = validated
        self._loaded_at = time.monotonic()
        return validated

    def invalidate(self) -> None:
        self._cached = None
