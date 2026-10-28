"""Provider-neutral AI interface used by every bot (CV analysis, summaries, moderation, hints…)."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["user", "assistant"]


class AIError(RuntimeError):
    """The provider failed (network, refusal, malformed output). Safe to show a generic error."""


class AIUnavailable(AIError):
    """AI is not configured, or the platform's daily budget is spent."""


@dataclass(slots=True, frozen=True)
class Attachment:
    """A file sent along with the last user turn."""

    kind: Literal["image", "pdf"]
    data: bytes
    media_type: str = "application/pdf"

    @classmethod
    def image(cls, data: bytes, media_type: str = "image/jpeg") -> Attachment:
        return cls("image", data, media_type)

    @classmethod
    def pdf(cls, data: bytes) -> Attachment:
        return cls("pdf", data, "application/pdf")


@dataclass(slots=True, frozen=True)
class Turn:
    role: Role
    text: str


@dataclass(slots=True)
class AIResult:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    data: Any = field(default=None)

    @property
    def tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(slots=True)
class AIRequest:
    system: str
    turns: list[Turn]
    attachments: tuple[Attachment, ...] = ()
    max_tokens: int = 4096
    # JSON Schema (object). When set, the provider returns JSON and ``AIResult.data`` holds the parsed value.
    schema: dict[str, Any] | None = None
    # Use the cheaper/faster model (classification, short hints, moderation).
    fast: bool = False


def parse_json(text: str) -> Any:
    """Parse model JSON, tolerating a fenced block around it."""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else ""
        s = s.rsplit("```", 1)[0]
    try:
        return json.loads(s)
    except ValueError as e:
        raise AIError(f"model returned invalid JSON: {e}") from e


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def complete(self, req: AIRequest) -> AIResult: ...

    async def close(self) -> None:  # noqa: B027
        pass
