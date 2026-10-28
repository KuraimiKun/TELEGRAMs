"""Metered AI client shared by all bots in a process: budget, per-user accounting, concurrency, metrics."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from redis.asyncio import Redis

from core.ai.base import AIError, AIProvider, AIRequest, AIResult, AIUnavailable, Attachment, Turn
from core.log import get_logger
from core.observability import AI_REQUESTS, AI_SECONDS, AI_TOKENS
from core.redis import PLATFORM

log = get_logger(__name__)

DAY_TTL = 3 * 86400


def _day() -> str:
    return f"{datetime.now(UTC):%Y%m%d}"


class AIClient:
    """What bots call (``ctx.ai``). One instance per process wraps the configured provider."""

    def __init__(
        self, provider: AIProvider, redis: Redis, *, daily_token_budget: int = 0, concurrency: int = 8
    ) -> None:
        self.provider = provider
        self.redis = redis
        self.daily_token_budget = daily_token_budget
        self._sem = asyncio.Semaphore(concurrency)

    @property
    def name(self) -> str:
        return self.provider.name

    def _budget_key(self, day: str | None = None) -> str:
        return PLATFORM("ai", "tokens", day or _day())

    def _user_key(self, bot: str, user_id: int, day: str | None = None) -> str:
        return PLATFORM("ai", "user", bot, user_id, day or _day())

    async def tokens_today(self) -> int:
        return int(await self.redis.get(self._budget_key()) or 0)

    async def user_tokens_today(self, bot: str, user_id: int) -> int:
        return int(await self.redis.get(self._user_key(bot, user_id)) or 0)

    async def available(self) -> bool:
        return not self.daily_token_budget or await self.tokens_today() < self.daily_token_budget

    async def ask(
        self,
        prompt: str | Sequence[Turn],
        *,
        system: str,
        bot: str,
        user_id: int | None = None,
        attachments: Sequence[Attachment] = (),
        schema: dict[str, Any] | None = None,
        max_tokens: int = 4096,
        fast: bool = False,
    ) -> AIResult:
        if not await self.available():
            AI_REQUESTS.labels(self.name, bot, "budget").inc()
            raise AIUnavailable("daily AI budget exhausted")
        turns = [Turn("user", prompt)] if isinstance(prompt, str) else list(prompt)
        req = AIRequest(system=system, turns=turns, attachments=tuple(attachments), max_tokens=max_tokens,
                        schema=schema, fast=fast)
        started = time.monotonic()
        try:
            async with self._sem:
                # A queued request may outlive the budget check above. Check again at admission and
                # account before releasing the slot, so later requests see completed usage.
                if not await self.available():
                    raise AIUnavailable("daily AI budget exhausted")
                result = await self.provider.complete(req)
                await self._account(bot, user_id, result.tokens)
        except AIError:
            AI_REQUESTS.labels(self.name, bot, "error").inc()
            raise
        except Exception as e:  # never leak provider internals to handlers
            AI_REQUESTS.labels(self.name, bot, "error").inc()
            log.exception("ai_request_failed", bot=bot, error=str(e))
            raise AIError("AI request failed") from e
        AI_SECONDS.labels(self.name).observe(time.monotonic() - started)
        AI_REQUESTS.labels(self.name, bot, "ok").inc()
        AI_TOKENS.labels(self.name, "input").inc(result.input_tokens)
        AI_TOKENS.labels(self.name, "output").inc(result.output_tokens)
        return result

    async def _account(self, bot: str, user_id: int | None, tokens: int) -> None:
        if tokens <= 0:
            return
        try:
            pipe = self.redis.pipeline()
            pipe.incrby(self._budget_key(), tokens)
            pipe.expire(self._budget_key(), DAY_TTL)
            if user_id is not None:
                pipe.incrby(self._user_key(bot, user_id), tokens)
                pipe.expire(self._user_key(bot, user_id), DAY_TTL)
            await pipe.execute()
        except Exception as e:
            log.warning("ai_accounting_failed", error=str(e))

    async def close(self) -> None:
        await self.provider.close()
