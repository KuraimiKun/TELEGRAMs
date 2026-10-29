"""Optional real Redis replica-lock evidence, using owned loopback test keys only."""

import asyncio
import os
import uuid
from datetime import timedelta
from urllib.parse import urlparse

import pytest
from redis.asyncio import from_url

from core.redis import KeySpace
from core.runtime.scheduler import CentralScheduler, _Job, _Target, every

REDIS_URL = os.environ.get("TEST_CHM_REDIS_URL")
pytestmark = pytest.mark.skipif(not REDIS_URL, reason="TEST_CHM_REDIS_URL not set")


@pytest.fixture
async def real_redis():
    assert REDIS_URL
    parsed = urlparse(REDIS_URL)
    assert parsed.hostname in {"127.0.0.1", "localhost"} and parsed.port == 56388
    redis = from_url(REDIS_URL)
    yield redis
    await redis.aclose()


async def test_two_real_scheduler_replicas_run_factory_job_once(real_redis):
    keys = KeySpace("test_chm_phase7_" + uuid.uuid4().hex)
    stop = asyncio.Event()
    calls = []
    async def call():
        calls.append("run")
        await asyncio.sleep(0.05)
        stop.set()
    job = _Job("factory_sweep", None, every(timedelta(seconds=30)), timeout=2)
    target = _Target(real_redis, keys, "readiness", "channelmanager_readiness", call)
    schedulers = [CentralScheduler([], stop) for _ in range(2)]
    try:
        await asyncio.wait_for(asyncio.gather(*(s._job_loop(target, job) for s in schedulers)), timeout=5)
        assert calls == ["run"]
        assert await real_redis.get(keys("sched", "next", job.name))
        assert await real_redis.get(keys("sched", "lock", job.name)) is None
    finally:
        await real_redis.delete(keys("sched", "next", job.name), keys("sched", "lock", job.name))


async def test_stale_scheduler_owner_cannot_release_successor_lock(real_redis):
    from core.runtime.scheduler import _RELEASE_LUA
    key = "test_chm_phase7_lock:" + uuid.uuid4().hex
    try:
        await real_redis.set(key, "old", px=50)
        await asyncio.sleep(0.08)
        assert await real_redis.set(key, "new", nx=True, ex=5)
        assert await real_redis.eval(_RELEASE_LUA, 1, key, "old") == 0
        assert await real_redis.get(key) == b"new"
    finally:
        await real_redis.delete(key)
