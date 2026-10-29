import asyncio
import json
from dataclasses import replace
from datetime import timedelta

import pytest
from sqlalchemy import select, update

from bots.channelmanager import health, outbox, release, worker
from bots.channelmanager.diagnostics import snapshot
from bots.channelmanager.models import Channel, Delivery, Operation, SenderBinding
from bots.channelmanager.preflight import configuration, report
from core.db.base import utcnow
from core.db.models import Bot as BotRecord
from core.db.models import BotSetting, ChildBot
from core.sdk.context import ChildInfo
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR
from tests.bots.channelmanager.test_channel_billing import buy, catalog
from tests.bots.channelmanager.test_growth import body, setup_growth
from tests.bots.channelmanager.test_publishing import drain
from tests.conftest import BOT_ID


@pytest.fixture(autouse=True)
def immediate(monkeypatch):
    async def budget(*args):
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", budget)


async def test_rollout_matrix_and_cleanup_contract(chm):
    for stage, rank in release.STAGES.items():
        await chm.settings.set("rollout_stage", stage)
        for family, required in release.FAMILIES.items():
            assert await release.allowed(chm, family) is (rank >= required)
        for kind in release.CLEANUP:
            assert await release.operation_allowed(chm, kind)
    with pytest.raises(ValueError):
        await chm.settings.set("rollout_stage", "not-a-stage")


async def test_final_dispatch_reads_stage_from_sql_despite_stale_settings_cache(chm, api, monkeypatch):
    await setup_growth(chm, api)
    post = await chm.extras["posts"].create(CHANNEL_ID, OPERATOR, body("No publish after pause"))
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    assert (await chm.settings.get()).rollout_stage == "commercial"
    async def change_stage(*args):
        async with chm.sm() as session:
            session.add(BotSetting(bot_id=BOT_ID, key="rollout_stage", value="paused"))
            await session.commit()
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", change_stage)
    async with chm.sm() as session:
        await session.execute(update(Operation).where(Operation.kind == "notice").values(status="cancelled"))
        await session.commit()
    op = await outbox.claim(chm)
    await outbox.execute(chm, op)
    async with chm.sm() as session:
        assert (await session.get(Operation, (BOT_ID, op.id))).status == "cancelled"
    assert not [m for m in api.calls("SendMessage") if m.chat_id == CHANNEL_ID]


async def test_maintenance_retains_and_executes_cleanup_without_new_publication(chm, api):
    plan = await catalog(chm, api)
    invoice, _ = await buy(chm, plan)
    post = await chm.extras["posts"].create(CHANNEL_ID, OPERATOR, body("Delete this"))
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    view = await chm.extras["posts"].view(post.id, OPERATOR)
    await chm.extras["posts"].delete(post.id, OPERATOR, view.post.generation)
    await chm.extras["billing"].request_refund(invoice.id, OPERATOR)
    new = await chm.extras["posts"].create(CHANNEL_ID, OPERATOR, body("Keep queued"))
    await chm.extras["posts"].publish(new.id, OPERATOR, new.generation)
    await chm.settings.set("maintenance", True)
    await worker.tick(chm)
    assert api.calls("DeleteMessage") and api.calls("RefundStarPayment")
    assert not [m for m in api.calls("SendMessage") if m.text == "Keep queued"]
    async with chm.sm() as session:
        assert (await session.scalar(select(Delivery).where(Delivery.post_id == new.id))).state == "pending"


async def test_child_gate_uses_only_its_channel_control_bot(chm):
    async with chm.sm() as session:
        for bot_id in [222222, 333333]:
            session.add(BotRecord(id=bot_id, slug=f"c{bot_id}", title="Scoped", active=True))
        await session.flush()
        session.add(ChildBot(bot_id=222222, factory_bot_id=BOT_ID, owner_id=OPERATOR, template="channelmanager",
            token_enc="opaque", username="child", title="Child", status="active"))
        session.add(Channel(bot_id=BOT_ID, channel_id=CHANNEL_ID, title="A"))
        session.add(Channel(bot_id=333333, channel_id=CHANNEL_ID - 1, title="B"))
        await session.flush()
        for control, channel in [(BOT_ID, CHANNEL_ID), (333333, CHANNEL_ID - 1)]:
            session.add(SenderBinding(bot_id=control, channel_id=channel, sender_bot_id=222222, owner_id=OPERATOR,
                token_epoch="opaque", control_username="control"))
        session.add(BotSetting(bot_id=BOT_ID, key="rollout_stage", value="paused"))
        await session.commit()
    child = replace(chm, bot_id=222222, child=ChildInfo(owner_id=OPERATOR, template="channelmanager", factory_username="factory"))
    assert not await release.allowed(child, "branded", channel_id=CHANNEL_ID)
    assert await release.allowed(child, "branded", channel_id=CHANNEL_ID - 1)


def test_progress_probe_rejects_stale_missing_corrupt_and_future(tmp_path):
    path = tmp_path / "progress"
    assert not health.healthy(path, now=100)
    for contents, expected in [("99", True), ("1", False), ("101", False), ("invalid", False)]:
        path.write_text(contents)
        assert health.healthy(path, now=100) is expected


async def test_stalled_native_call_is_bounded_and_remains_uncertain_on_recovery(chm, api, monkeypatch):
    await setup_growth(chm, api)
    op = await outbox.claim(chm)
    original = api.make_request
    async def stalled(bot, method, timeout=None):
        if type(method).__name__ == "SendMessage":
            api.requests.append(method)
            await asyncio.Event().wait()
        return await original(bot, method, timeout)
    monkeypatch.setattr(api, "make_request", stalled)
    monkeypatch.setattr(worker, "OP_TIMEOUT_SECONDS", 0.1)
    await worker.execute_bounded(chm, op)
    async with chm.sm() as session:
        stored = await session.get(Operation, (BOT_ID, op.id))
        assert stored.status == "running" and stored.dispatched
        stored.lease_until = utcnow() - timedelta(seconds=1)
        await session.commit()
    await outbox.recover(chm)
    async with chm.sm() as session:
        assert (await session.get(Operation, (BOT_ID, op.id))).status == "uncertain"


async def test_diagnostics_are_scoped_and_omit_private_payloads(chm, api):
    await setup_growth(chm, api)
    async with chm.sm() as session:
        op = await session.scalar(select(Operation))
        op.run_at = utcnow() - timedelta(seconds=35)
        op.payload = {"recipient_id": OPERATOR, "text": "secret-content"}
        await session.commit()
    data = await snapshot(chm)
    assert data["operation_lag_seconds"] >= 35
    assert "secret-content" not in json.dumps(data)
    assert all(isinstance(v, int) for v in data.values())


def test_preflight_never_returns_secrets_or_claims_native_validation():
    values = {"CHANNELMANAGER_TOKEN": "very-secret-token", "FACTORY_SECRET_KEY": "very-secret-key",
        "TELEGRAM_BOT_API_IMAGE": "aiogram/telegram-bot-api:latest"}
    result = report(values)
    assert "very-secret" not in json.dumps(result)
    assert not result["deployment_ready"] and result["live_canary"] == "deferred"
    assert configuration(values)[1]["status"] == "deferred"
    values["TELEGRAM_BOT_API_IMAGE"] = "aiogram/telegram-bot-api@sha256:" + "a" * 64
    assert configuration(values)[1]["status"] == "configured"


async def test_factory_metrics_aggregate_children_without_per_child_labels(chm):
    from bots.channelmanager.diagnostics import snapshot_for
    from bots.channelmanager.service import totals_for
    async with chm.sm() as session:
        for bot_id in [222222, 333333]:
            session.add(BotRecord(id=bot_id, slug=f"c{bot_id}", title="Child", active=True))
            await session.flush()
            session.add(ChildBot(bot_id=bot_id, factory_bot_id=BOT_ID, owner_id=OPERATOR, template="channelmanager", token_enc="opaque",
                username="child", title="Child", status="active"))
            session.add(Channel(bot_id=bot_id, channel_id=CHANNEL_ID, title="Child source"))
            await session.flush()
            session.add(Operation(bot_id=bot_id, id="a" * 32, channel_id=CHANNEL_ID, generation=1, kind="notice",
                dedupe_key="pending", payload={}, run_at=utcnow() - timedelta(seconds=5)))
        await session.commit()
    scope = select(ChildBot.bot_id).where(ChildBot.template == "channelmanager")
    assert (await totals_for(chm.sm, scope))["pending"] == 2
    assert (await snapshot_for(chm.sm, scope))["operation_lag_seconds"] >= 5
    await worker.emit_metrics(chm.sm, "factory_channelmanager", scope)
    assert worker.QUEUE.labels("factory_channelmanager", "pending")._value.get() == 2
