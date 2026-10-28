"""Pluggable AI layer: ``ctx.ai.ask(...)`` works the same with Claude (default) or OpenAI."""

from core.ai.base import AIError, AIProvider, AIRequest, AIResult, AIUnavailable, Attachment, Turn
from core.ai.client import AIClient

__all__ = ["AIClient", "AIError", "AIProvider", "AIRequest", "AIResult", "AIUnavailable", "Attachment", "Turn"]
