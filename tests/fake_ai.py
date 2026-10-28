"""Scripted AI provider for tests: no network, deterministic answers, records every request."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.ai.base import AIError, AIProvider, AIRequest, AIResult
from core.ai.client import AIClient


class FakeProvider(AIProvider):
    name = "fake"

    def __init__(self, reply: Any = "ok", tokens: int = 10) -> None:
        # ``reply`` is a string, a dict (returned as structured data), an exception, or a callable(req) -> any.
        self.reply = reply
        self.tokens = tokens
        self.requests: list[AIRequest] = []

    async def complete(self, req: AIRequest) -> AIResult:
        self.requests.append(req)
        reply = self.reply(req) if callable(self.reply) else self.reply
        if isinstance(reply, BaseException):
            raise reply
        if isinstance(reply, dict | list):
            if req.schema is None:
                raise AIError("structured reply scripted for a free-text request")
            import json

            return AIResult(text=json.dumps(reply), model="fake", input_tokens=self.tokens, output_tokens=self.tokens,
                            data=reply)
        return AIResult(text=str(reply), model="fake", input_tokens=self.tokens, output_tokens=self.tokens)


def fake_ai(redis, reply: Any = "ok", **kwargs: Any) -> tuple[AIClient, FakeProvider]:
    provider = FakeProvider(reply)
    return AIClient(provider, redis, **kwargs), provider


Reply = str | dict | BaseException | Callable[[AIRequest], Any]
