"""Uncached rollout gates; previously authorized cleanup and financial receipts remain available."""

from sqlalchemy import select

from bots.channelmanager.content import ContentError
from bots.channelmanager.models import SenderBinding
from core.db.models import BotSetting

STAGES = {"paused": 0, "publishing": 1, "automation": 2, "members": 3, "commercial": 4}
FAMILIES = {"publishing": 1, "automation": 2, "members": 3, "growth": 4, "billing": 4, "branded": 4}
CLEANUP = frozenset({"delete", "delete_reminder", "auto_delete", "auto_reminder", "member_clean", "member_unban",
    "growth_revoke_invite", "growth_refund"})


async def allowed(ctx, family, *, session=None, channel_id=None):
    if session is None:
        async with ctx.sm() as owned:
            return await allowed(ctx, family, session=owned, channel_id=channel_id)
    ids = {ctx.bot_id}
    if ctx.is_child and channel_id is not None:
        control_ids = (await session.scalars(select(SenderBinding.bot_id).where(SenderBinding.sender_bot_id == ctx.bot_id,
            SenderBinding.channel_id == channel_id, SenderBinding.active.is_(True)))).all()
        ids.update(control_ids)
    rows = (await session.execute(select(BotSetting.bot_id, BotSetting.key, BotSetting.value).where(
        BotSetting.bot_id.in_(ids), BotSetting.key.in_({"rollout_stage", "maintenance"})))).all()
    for bot_id in ids:
        settings = {key: value for source, key, value in rows if source == bot_id}
        stage = settings.get("rollout_stage", "commercial")
        if settings.get("maintenance", False) is not False or not isinstance(stage, str) or STAGES.get(stage, -1) < FAMILIES[family]:
            return False
    return True


async def require(ctx, family):
    if not await allowed(ctx, family):
        raise ContentError("release_stage")


async def operation_allowed(ctx, kind, *, session=None, channel_id=None):
    if kind in CLEANUP:
        return True
    family = "billing" if kind == "growth_invoice" else "growth" if kind.startswith("growth_") else (
        "automation" if kind.startswith("auto_") else "members" if kind.startswith("member_") else "publishing")
    return await allowed(ctx, family, session=session, channel_id=channel_id)
