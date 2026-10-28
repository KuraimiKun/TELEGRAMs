"""Real Redis atomic claim, SQLite audit, and recorded Telegram API (no live credentials)."""
import asyncio
import os

import pytest
from redis.asyncio import from_url

from bots.groupguard import authz, reviews
from bots.groupguard.operations import operation_for
from tests.bots.groupguard.test_groupguard import ADMIN, GROUP, MEMBER, bound_callback, gctx, group_msg, plain

__all__ = ["gctx"]
pytestmark = pytest.mark.skipif(not os.environ.get("TEST_REDIS_CLAIM_URL"), reason="TEST_REDIS_CLAIM_URL required for real Redis approval claim")


async def test_real_redis_concurrent_approval_once(gctx, api):
    client = from_url(os.environ["TEST_REDIS_CLAIM_URL"])
    assert await client.dbsize() == 0, "Use an empty disposable Redis database"
    original = gctx.redis
    gctx.redis = client
    nonce = None
    try:
        message = group_msg("/ban spam", 1087968824, reply_to=plain(MEMBER), sender_chat=plain(MEMBER).chat).message
        op = operation_for(message, "ban", target_id=MEMBER, target_name="Member", reason="spam")
        nonce = await reviews.create_review(gctx, authz.actor_from_message(gctx, message), op)
        assert nonce
        sent = api.messages[-1]
        callbacks = [bound_callback("unused", sent, ADMIN).callback_query.as_(gctx.bot) for _ in range(40)]
        results = await asyncio.gather(*(reviews.approve_review(gctx, q, nonce, callback_chat=GROUP) for q in callbacks))
        assert sum(r is not None for r in results) == 1
        assert sum(r.primary_completed for r in results if r is not None) == 1
        assert len(api.calls("BanChatMember")) == 1
        assert not await client.exists(reviews.review_key(gctx, nonce))
    finally:
        if nonce:
            await client.delete(reviews.review_key(gctx, nonce))
        gctx.redis = original
        await client.aclose()
