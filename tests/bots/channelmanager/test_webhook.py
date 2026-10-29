from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from sqlalchemy import select

from bots.channelmanager.models import Inbox
from core.factory.crypto import webhook_secret
from core.factory.serving import ChildWebhook
from tests.bots.channelmanager.conftest import membership_update


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_webhook_ack_requires_committed_receipt(chm, dp, monkeypatch, caplog):
    registry = SimpleNamespace(get=AsyncMock(return_value=SimpleNamespace(ctx=chm, dp=dp)))
    app = web.Application()
    webhook = ChildWebhook(registry, chm.platform)
    webhook.register(app)
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        path = f"/webhook/c/{chm.bot_id}"
        event = membership_update().model_dump(mode="json", exclude_none=True)
        response = await client.post(path, json=event)
        assert response.status == 401
        headers = {"X-Telegram-Bot-Api-Secret-Token": webhook_secret(chm.platform, chm.bot_id)}
        response = await client.post(path, json=event, headers=headers)
        assert response.status == 200 and not webhook._tasks
        async with chm.sm() as session:
            assert (await session.scalar(select(Inbox))).status == "pending"

        def unavailable():
            raise RuntimeError("private-channel-contents")
        monkeypatch.setattr(chm, "sm", unavailable)
        response = await client.post(path, json=event, headers=headers)
        assert response.status == 500
        assert "private-channel-contents" not in caplog.text
    finally:
        await client.close()
