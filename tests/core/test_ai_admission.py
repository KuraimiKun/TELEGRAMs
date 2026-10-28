"""Requests waiting for an AI concurrency slot cannot bypass an exhausted budget."""

import asyncio

from core.ai.base import AIUnavailable
from tests.fake_ai import fake_ai


async def test_queued_requests_recheck_budget_on_admission(redis):
    client, provider = fake_ai(redis, daily_token_budget=1, concurrency=1)
    results = await asyncio.gather(*(client.ask("review", system="test", bot="cvbot", user_id=42)
                                     for _ in range(3)), return_exceptions=True)
    assert sum(not isinstance(result, BaseException) for result in results) == 1
    assert sum(isinstance(result, AIUnavailable) for result in results) == 2
    assert len(provider.requests) == 1
