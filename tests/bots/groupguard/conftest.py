import pytest

from core.middlewares.throttling import ThrottlingMiddleware


@pytest.fixture(autouse=True)
def no_throttle(monkeypatch):
    async def passthrough(self, handler, event, data):
        return await handler(event, data)
    monkeypatch.setattr(ThrottlingMiddleware, "__call__", passthrough)
