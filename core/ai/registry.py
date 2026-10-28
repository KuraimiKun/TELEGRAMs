"""Build the configured AI provider from platform settings (or None when AI is not configured)."""

from __future__ import annotations

from redis.asyncio import Redis

from core.ai.base import AIProvider
from core.ai.client import AIClient
from core.config import PlatformConfig
from core.log import get_logger

log = get_logger(__name__)


def build_provider(platform: PlatformConfig) -> AIProvider | None:
    name = platform.ai_provider
    if name == "anthropic" and platform.anthropic_api_key:
        from core.ai.anthropic import AnthropicProvider

        return AnthropicProvider(
            platform.anthropic_api_key.get_secret_value(),
            model=platform.ai_model or "claude-opus-5-5",
            fast_model=platform.ai_fast_model or "claude-haiku-5-5",
        )
    if name == "openai" and platform.openai_api_key:
        from core.ai.openai import OpenAIProvider

        return OpenAIProvider(
            platform.openai_api_key.get_secret_value(),
            model=platform.ai_model or "gpt-5",
            fast_model=platform.ai_fast_model or "gpt-5-mini",
        )
    return None


def build_ai(platform: PlatformConfig, redis: Redis) -> AIClient | None:
    provider = build_provider(platform)
    if provider is None:
        log.info("ai_disabled", provider=platform.ai_provider)
        return None
    log.info("ai_enabled", provider=provider.name)
    return AIClient(
        provider, redis, daily_token_budget=platform.ai_daily_token_budget, concurrency=platform.ai_concurrency
    )
