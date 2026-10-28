from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from core.runtime.dispatcher import build_dispatcher
from core.runtime.gateway import _health_routes


async def test_health_and_metrics_endpoints(ctx, builders):
    dp = build_dispatcher(ctx)
    await dp.feed_update(ctx.bot, builders["message"]("/terms", user_id=61))

    app = web.Application()
    _health_routes(app, [ctx])
    async with TestClient(TestServer(app)) as client:
        live = await client.get("/health/live")
        assert live.status == 200

        ready = await client.get("/health/ready")
        body = await ready.json()
        assert ready.status == 200 and body["checks"] == {"database": "ok", "redis": "ok"}

        metrics = await (await client.get("/metrics")).text()
        assert 'tg_updates_total{bot="socialdownload",type="message"}' in metrics
        assert "tg_update_seconds_bucket" in metrics


async def test_readiness_fails_when_redis_is_down(ctx):
    class DeadRedis:
        async def ping(self):
            raise ConnectionError("down")

    ctx.redis = DeadRedis()  # type: ignore[assignment]
    app = web.Application()
    _health_routes(app, [ctx])
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/health/ready")
        assert resp.status == 503 and (await resp.json())["checks"]["redis"].startswith("error")
