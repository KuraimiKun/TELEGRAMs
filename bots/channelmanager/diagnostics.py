"""Aggregated operational evidence, without message contents, charge IDs or audience identifiers."""

from sqlalchemy import func, select

from bots.channelmanager.models import (
    BillingIncident,
    Channel,
    ChannelInvoice,
    GrowthAction,
    Inbox,
    Operation,
)
from bots.channelmanager.release import CLEANUP
from core.db.base import utcnow


async def snapshot(ctx):
    return await snapshot_for(ctx.sm, [ctx.bot_id])


async def snapshot_for(sm, bot_ids):
    now = utcnow()
    async with sm() as session:
        growth = dict((await session.execute(select(GrowthAction.status, func.count()).where(GrowthAction.bot_id.in_(bot_ids))
            .group_by(GrowthAction.status))).all())
        billing = await session.scalar(select(func.count()).select_from(BillingIncident).where(BillingIncident.bot_id.in_(bot_ids),
            BillingIncident.status.in_({"review", "refunding", "refund_uncertain"})))
        refunds = await session.scalar(select(func.count()).select_from(ChannelInvoice).where(ChannelInvoice.bot_id.in_(bot_ids),
            ChannelInvoice.status.in_({"refunding", "refund_uncertain", "refund_failed"})))
        paused = await session.scalar(select(func.count()).select_from(Channel).where(Channel.bot_id.in_(bot_ids), Channel.sender_paused.is_(True)))
        cleanup = await session.scalar(select(func.count()).select_from(Operation).where(Operation.bot_id.in_(bot_ids),
            Operation.kind.in_(CLEANUP), Operation.status.in_({"pending", "running", "failed", "uncertain"})))
        due = await session.scalar(select(func.min(Operation.run_at)).where(Operation.bot_id.in_(bot_ids),
            Operation.status == "pending", Operation.run_at <= now))
        receipt = await session.scalar(select(func.min(Inbox.created_at)).where(Inbox.bot_id.in_(bot_ids), Inbox.status == "pending"))
    return {"growth_failed": int(growth.get("failed", 0)), "growth_uncertain": int(growth.get("uncertain", 0)),
        "billing_review": int(billing or 0), "refund_review": int(refunds or 0), "sender_paused": int(paused or 0),
        "cleanup_backlog": int(cleanup or 0), "operation_lag_seconds": max(0, int((now - due).total_seconds())) if due else 0,
        "inbox_lag_seconds": max(0, int((now - receipt).total_seconds())) if receipt else 0}
