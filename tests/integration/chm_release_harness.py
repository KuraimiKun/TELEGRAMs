"""Disposable Phase 7 load, rollback and restore evidence; never uses real Telegram credentials."""
import asyncio
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

from redis.asyncio import from_url
from sqlalchemy import func, select, text, update

from bots.channelmanager import outbox
from bots.channelmanager.diagnostics import snapshot
from bots.channelmanager.models import ChannelGrant, ChannelInvoice, Event, GrowthAction, MemberLead, Operation
from core.db.base import create_engine, create_sessionmaker, utcnow
from core.db.migrate import upgrade
from core.db.models import Bot as BotRecord
from core.db.models import Payment
from core.redis import KeySpace
from core.sdk.registry import discover
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR, admin_member
from tests.bots.channelmanager.test_channel_billing import buy, catalog
from tests.bots.channelmanager.test_growth import body
from tests.conftest import BOT_ID, RecordingSession, build_test_ctx

ROOT = Path(__file__).resolve().parents[2]
URL = "postgresql+asyncpg://chmtest@127.0.0.1:55438/channelmanager_phase7_test"


async def manifest(url=URL):
    engine = create_engine(url)
    sm = create_sessionmaker(engine)
    try:
        async with sm() as session:
            values = {}
            for model in [BotRecord, ChannelInvoice, ChannelGrant, Payment, Event, Operation, GrowthAction]:
                values[model.__tablename__] = int(await session.scalar(select(func.count()).select_from(model)) or 0)
            values["payments"] = [list(row) for row in (await session.execute(select(Payment.charge_id, Payment.stars, Payment.days, Payment.status).order_by(Payment.id))).all()]
            values["grants"] = [[v.isoformat() if isinstance(v, datetime) else v for v in row] for row in (await session.execute(
                select(ChannelGrant.invoice_id, ChannelGrant.status, ChannelGrant.seconds, ChannelGrant.starts_at, ChannelGrant.ends_at,
                    ChannelGrant.parent_id, ChannelGrant.payment_id).order_by(ChannelGrant.id))).all()]
            values["invoices"] = [list(row) for row in (await session.execute(select(ChannelInvoice.id, ChannelInvoice.channel_id,
                ChannelInvoice.payer_id, ChannelInvoice.amount, ChannelInvoice.status, ChannelInvoice.payment_id, ChannelInvoice.charge_id)
                .order_by(ChannelInvoice.id))).all()]
            values["growth_actions"] = [list(row) for row in (await session.execute(select(GrowthAction.id, GrowthAction.kind,
                GrowthAction.status, GrowthAction.operation_id, GrowthAction.resource_id).order_by(GrowthAction.id))).all()]
            values["operations"] = [list(row) for row in (await session.execute(select(Operation.id, Operation.status, Operation.kind, Operation.dedupe_key).order_by(Operation.id))).all()]
            values["revision"] = await session.scalar(text("select version_num from alembic_version"))
            return values
    finally:
        await engine.dispose()


async def run():
    await asyncio.to_thread(upgrade, URL)
    engine = create_engine(URL)
    sm = create_sessionmaker(engine)
    redis = from_url("redis://127.0.0.1:56388/0")
    api = RecordingSession()
    try:
        async with sm() as session:
            await session.execute(text("TRUNCATE bots CASCADE"))
            session.add(BotRecord(id=BOT_ID, slug="channelmanager", title="Load test", active=True))
            await session.commit()
        ctx = await build_test_ctx(discover(["channelmanager"])[0], sm, redis, api, ROOT / ".scratch")
        ctx.keys = KeySpace("channelmanager_phase7_load")
        from aiogram.types import Chat
        api.responses["GetChat"] = Chat(id=CHANNEL_ID, type="channel", title="Offline load")
        api.responses["GetChatMember"] = lambda m: admin_member(m.user_id)
        plan = await catalog(ctx, api)
        invoice, paid = await buy(ctx, plan)
        async with sm() as session:
            await session.execute(update(Operation).where(Operation.kind == "notice").values(status="cancelled"))
            for user_id in range(70000, 70300):
                session.add(MemberLead(bot_id=BOT_ID, channel_id=CHANNEL_ID, user_id=user_id,
                    private_interacted_at=utcnow(), reachable=True, campaign_opt_in=True))
            await session.commit()
        campaign = await ctx.extras["growth"].snapshot(CHANNEL_ID, OPERATOR, body("Offline representative campaign"))
        await ctx.extras["growth"].confirm(campaign.id, OPERATOR, campaign.generation)
        started = time.perf_counter()
        attempted = 0
        interactive = []
        async def draft_probe():
            tick = time.perf_counter()
            await ctx.extras["posts"].create(CHANNEL_ID, OPERATOR, body("Interactive draft during campaign"))
            interactive.append(time.perf_counter() - tick)
        # Claim a full sender budget before permitting another window, so pending sends cannot
        # race a fifth budget window against the evidence's fixed target count.
        while attempted < 300:
            jobs = [op for _ in range(25) if (op := await outbox.claim(ctx)) is not None]
            if not jobs:
                await asyncio.sleep(0.05)
                continue
            await asyncio.gather(*(outbox.execute(ctx, op) for op in jobs), draft_probe())
            async with sm() as session:
                succeeded = int(await session.scalar(select(func.count()).select_from(Operation).where(Operation.kind == "growth_campaign", Operation.status == "succeeded")) or 0)
                # Bring only rate-deferred jobs to the next window; never ambiguous results.
                await session.execute(update(Operation).where(Operation.status == "pending", Operation.kind == "growth_campaign").values(run_at=utcnow()))
                await session.commit()
            attempted = succeeded
            if succeeded < 300:
                await asyncio.sleep(1.05)
        elapsed = time.perf_counter() - started
        sent = [m for m in api.calls("SendMessage") if m.text == "Offline representative campaign"]
        assert len(sent) == 300 and len({m.chat_id for m in sent}) == 300
        lag = await snapshot(ctx)
        assert lag["operation_lag_seconds"] == 0
        # Rollback gates preserve the existing ledger and cancel an undispatched publication.
        queued = await ctx.extras["posts"].create(CHANNEL_ID, OPERATOR, body("Rollback must hold this"))
        await ctx.extras["posts"].publish(queued.id, OPERATOR, queued.generation)
        await ctx.settings.set("rollout_stage", "paused")
        for _ in range(10):
            op = await outbox.claim(ctx)
            if op is None:
                break
            await outbox.execute(ctx, op)
        assert not [m for m in api.calls("SendMessage") if m.text == "Rollback must hold this"]
        # Seed a valid payment-linked cleanup through the service, without dispatching its RPC.
        await ctx.extras["billing"].request_refund(invoice.id, OPERATOR)
        output = {"postgres": "16.15", "redis": "7.4.12", "recipients": 300, "sender_budget_per_second": 25,
            "elapsed_seconds": round(elapsed, 3), "recipients_per_second": round(300 / elapsed, 3),
            "interactive_draft_ms_median": round(statistics.median(interactive) * 1000, 3),
            "interactive_draft_ms_max": round(max(interactive) * 1000, 3), "queue_lag_after_drain_seconds": 0,
            "interactive_probes_during_campaign": len(interactive),
            "duplicate_deliveries": 0, "telegram_transport": "RecordingSession", "paid_invoice_preserved": invoice.id,
            "charge_preserved": paid.telegram_payment_charge_id}
        (ROOT / ".scratch/phase7-load.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
        (ROOT / ".scratch/phase7-before-restore.json").write_text(json.dumps(await manifest(), indent=2), encoding="utf-8")
        print(json.dumps({k: v for k, v in output.items() if k not in {"charge_preserved", "paid_invoice_preserved"}}, indent=2))
    finally:
        await redis.aclose()
        await api.close()
        await engine.dispose()


async def verify_restore():
    before = json.loads((ROOT / ".scratch/phase7-before-restore.json").read_text())
    after = await manifest(URL.replace("channelmanager_phase7_test", "channelmanager_phase7_restore_test"))
    assert before == after, "Restored ledger/audit/cleanup manifest differs"
    print("Restored manifest matches: payments, grants, invoice counts, audit, operations, cleanup and schema revision.")


if __name__ == "__main__":
    asyncio.run(verify_restore() if "--verify-restore" in sys.argv else run())
