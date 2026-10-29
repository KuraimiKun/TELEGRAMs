import asyncio
from datetime import timedelta

import pytest
from aiogram.exceptions import TelegramForbiddenError, TelegramNetworkError, TelegramRetryAfter
from aiogram.methods import SendMessage
from sqlalchemy import select, update

from bots.channelmanager import outbox
from bots.channelmanager.models import Operation
from core.db.base import utcnow
from core.db.models import Bot as BotRecord
from tests.bots.channelmanager.test_foundations import connect


async def state(ctx, op):
    async with ctx.sm() as session:
        return await session.get(Operation, (ctx.bot_id, op.id))


async def test_claim_fencing_and_stale_generation(chm):
    row = await connect(chm)
    op = await outbox.claim(chm)
    assert op and await outbox.claim(chm) is None
    await chm.extras["channelmanager"].disconnect(row.channel_id, row.connected_by, row.generation)
    assert not await outbox.mark_dispatched(chm, op)
    assert not await outbox.finish(chm, op, "succeeded")
    assert (await state(chm, op)).status == "cancelled"


@pytest.mark.parametrize("dispatched,expected", [(False, "pending"), (True, "uncertain")])
async def test_expired_leases_recover_according_to_dispatch_marker(chm, dispatched, expected):
    await connect(chm)
    op = await outbox.claim(chm)
    async with chm.sm() as session:
        await session.execute(update(Operation).values(dispatched=dispatched, lease_until=utcnow() - timedelta(seconds=1)))
        await session.commit()
    await outbox.recover(chm)
    assert (await state(chm, op)).status == expected
    assert not await outbox.finish(chm, op, "succeeded")


@pytest.mark.parametrize("error,expected", [("network", "uncertain"), ("forbidden", "failed"), ("retry", "pending")])
async def test_external_failure_classification(chm, api, error, expected):
    await connect(chm)
    op = await outbox.claim(chm)
    method = SendMessage(chat_id=42, text="test")
    api.responses["SendMessage"] = {
        "network": TelegramNetworkError(method=method, message="secret not stored"),
        "forbidden": TelegramForbiddenError(method=method, message="secret not stored"),
        "retry": TelegramRetryAfter(method=method, message="slow", retry_after=8),
    }[error]
    await outbox.execute(chm, op)
    result = await state(chm, op)
    assert result.status == expected and "secret" not in result.error_code
    if expected == "pending":
        assert result.run_at > utcnow() and not result.dispatched


async def test_retry_budget_is_bounded(chm, api):
    await connect(chm)
    async with chm.sm() as session:
        await session.execute(update(Operation).values(attempts=4))
        await session.commit()
    op = await outbox.claim(chm)
    api.responses["SendMessage"] = TelegramRetryAfter(method=SendMessage(chat_id=42, text="t"), message="slow", retry_after=1)
    await outbox.execute(chm, op)
    assert (await state(chm, op)).status == "failed"


async def test_local_budget_wait_preserves_attempts_and_no_dispatch(chm):
    await connect(chm)
    assert await outbox.reserve_budget(chm, 42) == 0
    op = await outbox.claim(chm)
    await outbox.execute(chm, op)
    result = await state(chm, op)
    assert result.status == "pending" and result.attempts == 0 and not result.dispatched


async def test_bot_budget_shared_across_recipients(chm):
    assert [await outbox.reserve_budget(chm, i) for i in range(1, 26)] == [0] * 25
    assert await outbox.reserve_budget(chm, 100) >= 1


async def test_enqueuing_twice_deduplicates_within_channel_transaction(chm):
    channel = await connect(chm)
    async with chm.sm() as session:
        payload = {"recipient_id": 42, "text": "Hello"}
        a = await outbox.enqueue(session, chm, channel, kind="notice", dedupe_key="same", payload=payload)
        b = await outbox.enqueue(session, chm, channel, kind="notice", dedupe_key="same", payload=payload)
        assert a == b
        await session.commit()
    async with chm.sm() as session:
        assert len((await session.scalars(select(Operation))).all()) == 2


async def test_core_operator_broadcast_uses_same_sender_budget(chm, monkeypatch):
    calls = []

    async def before_send(recipient):
        calls.append(recipient)

    assert chm.broadcast.before_send is not None
    monkeypatch.setattr(chm.broadcast, "before_send", before_send)
    broadcast = await chm.broadcast.create(999, "all", 999, 1)
    assert await chm.broadcast._send(chm.bot, broadcast, 42) == "sent"
    assert calls == [42]


async def test_interrupted_http_call_is_not_automatically_replayed(chm, api):
    await connect(chm)
    op = await outbox.claim(chm)

    def interrupted(method):
        raise asyncio.CancelledError

    api.responses["SendMessage"] = interrupted
    with pytest.raises(asyncio.CancelledError):
        await outbox.execute(chm, op)
    row = await state(chm, op)
    assert row.status == "running" and row.dispatched
    async with chm.sm() as session:
        await session.execute(update(Operation).values(lease_until=utcnow() - timedelta(seconds=1)))
        await session.commit()
    await outbox.recover(chm)
    assert (await state(chm, op)).status == "uncertain"
    assert await outbox.claim(chm) is None


async def test_redis_outage_defers_without_attempting_telegram(chm, api, monkeypatch):
    await connect(chm)
    op = await outbox.claim(chm)

    async def unavailable(*args):
        raise RuntimeError("rate store unavailable")

    monkeypatch.setattr(outbox, "reserve_budget", unavailable)
    await outbox.execute(chm, op)
    row = await state(chm, op)
    assert row.status == "pending" and row.attempts == 0 and not row.dispatched
    assert not api.calls("SendMessage")


async def test_deactivated_bot_cannot_dispatch(chm, api):
    await connect(chm)
    op = await outbox.claim(chm)
    async with chm.sm() as session:
        await session.execute(update(BotRecord).where(BotRecord.id == chm.bot_id).values(active=False))
        await session.commit()
    await outbox.execute(chm, op)
    assert (await state(chm, op)).status == "cancelled"
    assert not api.calls("SendMessage")
