import time

import fakeredis.aioredis
import pytest

from bots.socialdownload.engine.queue import LEASE_SECONDS, MAX_ATTEMPTS, Job, JobQueue


@pytest.fixture
def queue():
    return JobQueue(fakeredis.aioredis.FakeRedis())


def make_job(user_id=1, priority="normal", **kw) -> Job:
    return Job(user_id=user_id, url="https://x.com/i/status/1", platform="twitter", max_bytes=1, cache_key="k",
               priority=priority, **kw)


async def test_enqueue_enforces_concurrency_atomically(queue):
    assert await queue.enqueue(make_job(), max_active=2) == 1
    assert await queue.enqueue(make_job(), max_active=2) == 2
    assert await queue.enqueue(make_job(), max_active=2) == -1
    assert await queue.active_count(1) == 2


async def test_pop_leases_and_finish_releases(queue):
    job = make_job()
    await queue.enqueue(job)
    popped = await queue.pop()
    assert popped and popped.id == job.id
    assert await queue.depth() == {"high": 0, "normal": 0, "inflight": 1, "dead": 0}
    await queue.finish(popped)
    assert await queue.depth() == {"high": 0, "normal": 0, "inflight": 0, "dead": 0}
    assert await queue.active_count(1) == 0


async def test_crashed_worker_job_is_requeued_then_dead_lettered(queue):
    job = make_job()
    await queue.enqueue(job)
    for attempt in range(1, MAX_ATTEMPTS):
        assert await queue.pop()
        requeued, exhausted = await queue.reap(now=time.time() + LEASE_SECONDS + 1)
        assert [j.id for j in requeued] == [job.id] and not exhausted
        assert (await queue.get(job.id)).attempts == attempt

    assert await queue.pop()
    requeued, exhausted = await queue.reap(now=time.time() + LEASE_SECONDS + 1)
    assert not requeued and [j.id for j in exhausted] == [job.id]
    await queue.dead_letter(exhausted[0], "test")
    assert (await queue.depth())["dead"] == 1
    assert await queue.active_count(1) == 0


async def test_heartbeat_keeps_lease_alive(queue):
    await queue.enqueue(make_job())
    job = await queue.pop()
    await queue.heartbeat(job.id)
    requeued, exhausted = await queue.reap(now=time.time() + 5)
    assert not requeued and not exhausted


async def test_vip_first_but_free_users_are_not_starved(queue):
    for _ in range(8):
        await queue.enqueue(make_job(user_id=2, priority="high"))
    free = make_job(user_id=3)
    await queue.enqueue(free)
    served = [(await queue.pop()).priority for _ in range(4)]
    assert served[:3] == ["high", "high", "high"]
    assert served[3] == "normal"


async def test_cancel_queued_job_removes_it_and_checks_owner(queue):
    job = make_job()
    await queue.enqueue(job)
    result, _ = await queue.cancel(job.id, user_id=999)
    assert not result.found
    result, cancelled = await queue.cancel(job.id, user_id=1)
    assert result.found and result.removed_from_queue and cancelled.id == job.id
    assert await queue.pop() is None
    assert (await queue.cancel("../../etc", 1))[0].found is False


async def test_parked_followers_are_woken_to_the_front(queue):
    leader, follower, other = make_job(), make_job(user_id=4), make_job(user_id=5)
    for j in (leader, follower, other):
        await queue.enqueue(j)
    await queue.pop()  # leader
    f = await queue.pop()
    await queue.park(f, "k")
    assert await queue.wake("k") == 1
    nxt = await queue.pop()
    assert nxt.id == follower.id and nxt.parked
