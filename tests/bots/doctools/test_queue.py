import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bots.doctools.operations import DocumentError
from bots.doctools.queue import LEASE_SECONDS, MAX_ATTEMPTS, DocAsset, Job, JobQueue
from bots.doctools.service import DocToolsService, QueueFull, QuotaExceeded
from bots.doctools.settings import DocToolsSettings
from core.redis import KeySpace


def make_job(user_id=42, **kwargs):
    return Job(user_id=user_id, chat_id=user_id, operation="count", assets=[DocAsset(file_id="file")], **kwargs)


@pytest.fixture
def queue(redis):
    return JobQueue(redis, KeySpace("doctools"))


async def test_queue_enforces_per_user_limit_and_releases_on_finish(queue):
    first = make_job()
    assert await queue.enqueue(first, max_active=1) == 1
    assert await queue.enqueue(make_job(), max_active=1) == -1
    leased = await queue.pop()
    assert leased and leased.lease_token
    assert await queue.depth() == {"high": 0, "normal": 0, "inflight": 1, "dead": 0}
    assert await queue.finish(leased)
    assert await queue.get(first.id) is None
    assert await queue.enqueue(make_job(), max_active=1) == 1


async def test_crash_recovery_fences_stale_worker(queue):
    job = make_job()
    await queue.enqueue(job)
    stale = await queue.pop()
    requeued, exhausted = await queue.reap(now=time.time() + LEASE_SECONDS + 1)
    assert len(requeued) == 1 and not exhausted
    replacement = await queue.pop()
    assert replacement.attempts == 1
    assert replacement.lease_token != stale.lease_token
    assert not await queue.heartbeat(stale)
    assert not await queue.finish(stale)
    assert not await queue.save(stale)
    assert not await queue.requeue(stale)
    assert await queue.heartbeat(replacement)
    assert await queue.finish(replacement)


async def test_dead_letter_discards_passwords_and_file_references(queue):
    job = make_job(options={"password": "super-private-password"})
    await queue.enqueue(job)
    for attempt in range(MAX_ATTEMPTS):
        leased = await queue.pop()
        assert leased
        requeued, exhausted = await queue.reap(now=time.time() + LEASE_SECONDS + 1)
        if attempt + 1 < MAX_ATTEMPTS:
            assert len(requeued) == 1 and not exhausted
        else:
            assert not requeued and len(exhausted) == 1
            await queue.dead_letter(exhausted[0], "expired")
    assert await queue.get(job.id) is None
    raw = (await queue.redis.lrange(queue.dead, 0, -1))[0]
    data = json.loads(raw)
    assert set(data) == {"id", "user_id", "operation", "reason"}
    assert b"super-private-password" not in raw


async def test_vip_priority_includes_free_user_fairness(queue):
    for user_id in range(1, 9):
        await queue.enqueue(make_job(user_id, is_vip=True))
    await queue.enqueue(make_job(100))
    popped = [await queue.pop() for _ in range(4)]
    assert all(job.is_vip for job in popped[:3])
    assert popped[3].user_id == 100


@pytest.fixture
def service(redis, queue):
    ctx = SimpleNamespace(
        redis=redis, keys=KeySpace("doctools"), extras={"doctools_queue": queue}, ai=object(),
        users=SimpleNamespace(get=AsyncMock(return_value=SimpleNamespace(is_vip=lambda: False))),
        settings=SimpleNamespace(get=AsyncMock(return_value=DocToolsSettings(free_ai_daily_limit=1))),
        platform=SimpleNamespace(uses_local_api=False),
    )
    return DocToolsService(ctx)


async def test_basket_fixed_expiry_and_chat_isolation(service):
    await service.add_asset(42, 42, DocAsset(file_id="first"))
    key = service._basket_key(42, 42)
    await service.ctx.redis.expire(key, 120)
    basket = await service.add_asset(42, 42, DocAsset(file_id="second"))
    assert [asset.file_id for asset in basket.assets] == ["first", "second"]
    assert await service.ctx.redis.ttl(key) <= 120
    assert await service.basket(42, -100) is None
    # Redis TTL rounds the final fraction of a second down to zero. Appending must not renew it.
    await service.ctx.redis.pexpire(key, 500)
    await service.add_asset(42, 42, DocAsset(file_id="third"))
    assert 0 < await service.ctx.redis.pttl(key) <= 500


async def test_ai_quota_refund_and_queue_rejection_are_exactly_once(service):
    await service.add_asset(42, 42, DocAsset(file_id="file"))
    job = await service.submit(42, 42, "summarize")
    assert await service.quota.used(42) == 1
    with pytest.raises(QuotaExceeded):
        await service.submit(42, 42, "summarize")
    await service.refund(job)
    await service.refund(job)
    assert await service.quota.used(42) == 0
    settings = DocToolsSettings(free_ai_daily_limit=1, max_active_jobs=1)
    service.ctx.settings.get.return_value = settings
    with pytest.raises(QueueFull):
        await service.submit(42, 42, "summarize")
    assert await service.quota.used(42) == 0
    assert (await service.basket(42, 42)).assets


async def test_unknown_operation_and_oversized_upload_are_rejected(service):
    await service.add_asset(42, 42, DocAsset(file_id="file"))
    with pytest.raises(DocumentError, match="invalid"):
        await service.submit(42, 42, "execute")
    with pytest.raises(DocumentError, match="large"):
        await service.add_asset(42, 42, DocAsset(file_id="big", size_bytes=21 * 1024 * 1024))
