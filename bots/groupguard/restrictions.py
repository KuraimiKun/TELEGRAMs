"""Reapply durable active ownership after Telegram resets individual permissions on rejoin."""
from __future__ import annotations

from sqlalchemy import or_, select

from bots.groupguard import actions, perms
from bots.groupguard.contracts import ActionResult
from bots.groupguard.models import GuardRestriction
from core.db.base import utcnow
from core.sdk.context import BotContext


async def on_join(ctx: BotContext, chat_id: int, user_id: int) -> tuple[str | None, ActionResult | None]:
    svc = ctx.extras["guard"]
    async with svc.member_session(chat_id, user_id) as (session, _member):
        rows = list((await session.execute(select(GuardRestriction).where(GuardRestriction.bot_id == ctx.bot_id,
            GuardRestriction.chat_id == chat_id, GuardRestriction.user_id == user_id,
            or_(GuardRestriction.until.is_(None), GuardRestriction.until > utcnow())))).scalars())
        if not rows:
            return None, None
        if any(row.source.startswith("fed:") for row in rows):
            from bots.groupguard import fed_enforcement
            _attachment, current_bans = await fed_enforcement.policy(ctx, chat_id, user_id, session)
            active_sources = {"fed:" + ban.fed_id for ban in current_bans}
            # Retain unresolved ownership evidence, but an inactive federation intent cannot
            # become a new automatic ban through the generic rejoin recovery path.
            rows = [row for row in rows if not row.source.startswith("fed:") or row.source in active_sources]
            if not rows:
                return None, None
        member = await perms.fresh_member(ctx, chat_id, user_id)
        if member is None or perms.member_rights(member).is_admin:
            return "protected", None
        if member.status not in {"left", "kicked"} and (member.status != "restricted" or getattr(member, "is_member", False)):
            # CAPTCHA's no-deadline ban can only be an interrupted kick, whose intent allows rejoin.
            # Actual current membership proves that interim ban is gone; never re-ban for its old kick.
            transient = [row for row in rows if row.source == "captcha" and row.mode == "ban" and row.until is None]
            for row in transient:
                await session.delete(row)
            rows = [row for row in rows if row not in transient]
            if not rows:
                return None, None
        mode = "ban" if any(row.mode == "ban" for row in rows) else "mute"
        effective = [row for row in rows if row.mode == mode]
        deadline = None if any(row.until is None for row in effective) else max(row.until for row in effective if row.until is not None)
        # Ownership already exists durably; this RPC renews its actual enforcement without replacing its generation/deadline.
        result = await actions._punish_api(ctx, chat_id, user_id, mode, None, absolute=deadline)
        if not result.primary_completed:
            for row in effective:
                row.state = "uncertain"
                row.updated_at = utcnow()
        return mode, result
