import fakeredis.aioredis

from bots.socialdownload.services.quota import QuotaService


async def test_consume_and_limits():
    quota = QuotaService(redis=fakeredis.aioredis.FakeRedis())
    uid, limit = 999999, 3

    assert await quota.used(uid) == 0
    day = await quota.consume(uid, limit)
    assert day is not None and len(day) == 8
    assert await quota.consume(uid, limit) == day
    assert await quota.consume(uid, limit) == day
    assert await quota.used(uid) == 3
    assert await quota.consume(uid, limit) is None
    assert await quota.used(uid) == 3


async def test_multi_unit_consume_is_all_or_nothing():
    quota = QuotaService(redis=fakeredis.aioredis.FakeRedis())
    assert await quota.consume(1, 10, units=8)
    assert await quota.consume(1, 10, units=3) is None  # would exceed
    assert await quota.used(1) == 8
    assert await quota.consume(1, 10, units=2)
    assert await quota.used(1) == 10


async def test_refund_is_once_per_token_and_hits_charged_day():
    quota = QuotaService(redis=fakeredis.aioredis.FakeRedis())
    day = await quota.consume(5, 10, units=2)
    assert await quota.refund(5, 2, day, token="job-a") is True
    assert await quota.refund(5, 2, day, token="job-a") is False  # double cancel / retry: no double refund
    assert await quota.used(5) == 0

    # Refund for yesterday's charge must not give today's quota back.
    await quota.consume(5, 10)
    assert await quota.refund(5, 1, "19990101", token="job-b") is True
    assert await quota.used(5) == 1
