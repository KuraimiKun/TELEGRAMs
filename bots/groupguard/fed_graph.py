"""Bounded directed federation subscriptions. A subscribes to B means A enforces B's bans."""
from __future__ import annotations

from collections import deque

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from bots.groupguard import federations
from bots.groupguard.contracts import Actor
from bots.groupguard.federations import FedError
from bots.groupguard.models import GuardFederation, GuardFedSub
from core.db.base import upsert, utcnow
from core.sdk.context import BotContext

MAX_REACHED = 128
MAX_OUTDEGREE = 32
MAX_DEPTH = 16
MAX_NAMESPACE_EDGES = 10000


def closure(graph: dict[str, set[str]], root: str) -> set[str]:
    visited: set[str] = set()
    pending = deque([(root, 0)])
    while pending:
        node, depth = pending.popleft()
        if node in visited:
            continue
        if depth > MAX_DEPTH or len(visited) >= MAX_REACHED:
            raise FedError('graph_limit')
        visited.add(node)
        pending.extend((next_id, depth + 1) for next_id in graph.get(node, set()))
    return visited


async def reached(ctx: BotContext, root: str, session: AsyncSession) -> set[str]:
    visited = {root}
    frontier = {root}
    for _depth in range(MAX_DEPTH + 1):
        if not frontier:
            return visited
        edges = (await session.execute(select(GuardFedSub.target_id).where(
            GuardFedSub.bot_id == ctx.bot_id, GuardFedSub.fed_id.in_(frontier)).limit(
                MAX_REACHED * MAX_OUTDEGREE + 1))).scalars().all()
        upcoming = set(edges) - visited
        if len(visited | upcoming) > MAX_REACHED:
            raise FedError('graph_limit')
        visited.update(upcoming)
        frontier = upcoming
    if frontier:
        raise FedError('graph_limit')
    return visited


async def change(ctx: BotContext, actor: Actor, fed_id: str, target_id: str, *, subscribe: bool) -> GuardFederation:
    uid = await federations.human(ctx, actor)
    target_id = federations.identifier(target_id)
    async with ctx.extras['guard'].member_session(0, 0) as (session, _member):
        fed = await federations.get(ctx, fed_id, session, lock=True)
        target = await federations.get(ctx, target_id, session)
        if fed is None or target is None:
            raise FedError('missing')
        if fed.owner_id != uid:
            raise FedError('authority')
        if fed.id == target.id:
            raise FedError('cycle')
        edges = (await session.execute(select(GuardFedSub.fed_id, GuardFedSub.target_id).where(
            GuardFedSub.bot_id == ctx.bot_id).limit(MAX_NAMESPACE_EDGES + 1))).all()
        if len(edges) > MAX_NAMESPACE_EDGES:
            raise FedError('graph_limit')
        graph: dict[str, set[str]] = {}
        for origin, destination in edges:
            graph.setdefault(origin, set()).add(destination)
        targets = graph.setdefault(fed.id, set())
        if subscribe:
            targets.add(target.id)
            if len(targets) > MAX_OUTDEGREE or len(edges) >= MAX_NAMESPACE_EDGES:
                raise FedError('graph_limit')
            # The proposed destination must not lead back to the subscriber.
            if fed.id in closure(graph, target.id):
                raise FedError('cycle')
            # Bound every affected upstream root, not only this direct subscriber.
            for root in graph:
                closure(graph, root)
            await session.execute(upsert(session, GuardFedSub).values(bot_id=ctx.bot_id, fed_id=fed.id,
                target_id=target.id, created_at=utcnow()).on_conflict_do_nothing())
        else:
            await session.execute(delete(GuardFedSub).where(GuardFedSub.bot_id == ctx.bot_id,
                GuardFedSub.fed_id == fed.id, GuardFedSub.target_id == target.id))
        fed.revision += 1
        fed.graph_generation += 1
        fed.updated_at = utcnow()
        federations.audit(ctx, session, actor, 'subscribe' if subscribe else 'unsubscribe', fed.id, target_id=target.id)
        await federations.human(ctx, actor, session)
        from bots.groupguard import fed_enforcement
        await fed_enforcement.enqueue_network(ctx, session, fed, user_id=0, version=fed.graph_generation,
            by_id=uid, event='graph')
    await federations.emit(ctx, fed, actor, 'subscribe' if subscribe else 'unsubscribe')
    return fed


async def subscriptions(ctx: BotContext, fed_id: str) -> list[GuardFederation]:
    async with ctx.sm() as session:
        return list((await session.execute(select(GuardFederation).join(GuardFedSub,
            (GuardFedSub.bot_id == GuardFederation.bot_id) & (GuardFedSub.target_id == GuardFederation.id))
            .where(GuardFedSub.bot_id == ctx.bot_id, GuardFedSub.fed_id == federations.identifier(fed_id))
            .order_by(GuardFederation.id).limit(MAX_OUTDEGREE))).scalars())
