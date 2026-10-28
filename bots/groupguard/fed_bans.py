"""Federation ban intents retain inactive versions so obsolete jobs cannot resurrect a ban."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from bots.groupguard import fed_graph, federations, perms
from bots.groupguard.contracts import Actor
from bots.groupguard.federations import FedError
from bots.groupguard.models import GuardFedBan
from core.db.base import utcnow
from core.sdk.context import BotContext

MAX_REASON = 1024


@dataclass(frozen=True, slots=True)
class BanInput:
    user_id: int
    reason: str | None = None
    first_name: str | None = None
    username: str | None = None


def validate(ctx: BotContext, value: BanInput, *, reason_required: bool) -> BanInput:
    if isinstance(value.user_id, bool) or not perms.valid_human_id(value.user_id) or value.user_id == ctx.bot_id:
        raise FedError('target')
    reason = (value.reason or '').strip()
    if len(reason) > MAX_REASON or any(ord(char) < 32 and char not in '\n\t' for char in reason):
        raise FedError('reason')
    if reason_required and not reason:
        raise FedError('reason_required')
    if value.first_name is not None and len(value.first_name) > 256:
        raise FedError('target')
    if value.username is not None and len(value.username) > 64:
        raise FedError('target')
    return BanInput(value.user_id, reason or None, value.first_name, value.username)


async def change(ctx: BotContext, actor: Actor, fed_id: str, value: BanInput, *, active: bool) -> GuardFedBan:
    uid = await federations.human(ctx, actor)
    async with ctx.extras['guard'].member_session(0, 0) as (session, _member):
        fed = await federations.get(ctx, fed_id, session, lock=True)
        if fed is None:
            raise FedError('missing')
        if await federations.role(ctx, fed, uid, session) not in {'owner', 'admin'}:
            raise FedError('authority')
        value = validate(ctx, value, reason_required=fed.reason_required and active)
        row = await session.get(GuardFedBan, (ctx.bot_id, fed.id, value.user_id), populate_existing=True)
        if row is None:
            row = GuardFedBan(bot_id=ctx.bot_id, fed_id=fed.id, user_id=value.user_id, version=1,
                active=active, reason=value.reason, first_name=value.first_name, username=value.username, by_id=uid)
            session.add(row)
        else:
            row.version += 1
            row.active = active
            row.reason = value.reason if active or value.reason else row.reason
            if value.first_name is not None:
                row.first_name = value.first_name
            if value.username is not None:
                row.username = value.username
            row.by_id = uid
            row.updated_at = utcnow()
        await federations.human(ctx, actor, session)
        await session.flush()
        federations.audit(ctx, session, actor, 'ban' if active else 'unban', fed.id,
            user_id=row.user_id, version=row.version)
        from bots.groupguard import fed_enforcement
        await fed_enforcement.enqueue_network(ctx, session, fed, user_id=row.user_id,
            version=row.version, by_id=uid, event='ban')
    await federations.emit(ctx, fed, actor, 'ban' if active else 'unban',
        target_user_id=row.user_id, reason=row.reason)
    return row


async def effective(ctx: BotContext, fed_id: str, user_id: int, session) -> list[GuardFedBan]:
    sources = await fed_graph.reached(ctx, fed_id, session)
    return list((await session.execute(select(GuardFedBan).where(GuardFedBan.bot_id == ctx.bot_id,
        GuardFedBan.fed_id.in_(sources), GuardFedBan.user_id == user_id, GuardFedBan.active.is_(True))
        .order_by(GuardFedBan.fed_id).execution_options(populate_existing=True))).scalars())


async def status(ctx: BotContext, user_id: int, fed_id: str | None = None, *, after: str = '', limit: int = 25) -> list[GuardFedBan]:
    async with ctx.sm() as session:
        query = select(GuardFedBan).where(GuardFedBan.bot_id == ctx.bot_id, GuardFedBan.user_id == user_id,
            GuardFedBan.fed_id > after)
        if fed_id is not None:
            query = query.where(GuardFedBan.fed_id == federations.identifier(fed_id))
        else:
            query = query.where(GuardFedBan.active.is_(True))
        return list((await session.execute(query.order_by(GuardFedBan.fed_id).limit(min(limit, 100)))).scalars())
