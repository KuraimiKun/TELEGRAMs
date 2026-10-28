"""Bounded federation graph expansion and current intent enforcement with local provenance."""
from __future__ import annotations

import hashlib
import time

from aiogram.types import User
from redis.exceptions import RedisError
from sqlalchemy import func, select, update

from bots.groupguard import actions, authz, durable, fed_bans, fed_graph, federations, group_broadcast, perms
from bots.groupguard.contracts import ActionResult, StepResult, result_of
from bots.groupguard.federations import FedError
from bots.groupguard.models import (
    GuardChat,
    GuardFedBan,
    GuardFedChat,
    GuardFederation,
    GuardFedObservation,
    GuardFedSub,
    GuardJob,
    GuardRestriction,
)
from core.db.base import affected, upsert, utcnow
from core.sdk.context import BotContext

BATCH = 100
MAX_BACKLOG = 5000


def source(fed_id: str) -> str:
    return 'fed:' + fed_id


def dedupe(*parts) -> str:
    return hashlib.sha256(':'.join(map(str, parts)).encode()).hexdigest()


async def enqueue_network(ctx: BotContext, session, fed: GuardFederation, *, user_id: int, version: int,
        by_id: int, event: str, node_id: str | None = None) -> str:
    node_id = node_id or fed.id
    return await durable.enqueue(ctx, 'fed_fanout', 0, user_id=user_id, generation=str(version),
        dedupe_key='fedgraph:' + dedupe(fed.id, user_id, version, event, node_id),
        payload=dict(fed_id=fed.id, node_id=node_id, version=version, by_id=by_id, event=event,
            chat_cursor=-(2**63), parent_cursor='', chats_done=False, parents_done=False), session=session)


async def enqueue_chat(ctx: BotContext, session, attachment: GuardFedChat, *, user_id: int = 0,
        root_id: str | None = None, version: int = 0, by_id: int | None = None, event: str = 'membership') -> str:
    return await durable.enqueue(ctx, 'fed_enforce', attachment.chat_id, user_id=user_id or None,
        generation=attachment.generation,
        dedupe_key='fedeffect:' + dedupe(attachment.chat_id, attachment.generation, root_id, user_id, version, event),
        payload=dict(fed_id=root_id or attachment.fed_id, node_id=attachment.fed_id,
            version=version, by_id=by_id, event=event, user_cursor=0), session=session)


async def observe(ctx: BotContext, chat_id: int, user: User) -> None:
    if user.is_bot or not perms.valid_human_id(user.id) or chat_id >= 0 or not await authz.active_namespace(ctx):
        return
    await ctx.extras['guard'].ensure_chat(chat_id)
    async with ctx.sm() as session:
        values = dict(first_name=user.first_name[:256], username=(user.username or '')[:64] or None,
            last_seen=utcnow())
        await session.execute(upsert(session, GuardFedObservation).values(bot_id=ctx.bot_id,
            chat_id=chat_id, user_id=user.id, **values).on_conflict_do_update(
                index_elements=['bot_id', 'chat_id', 'user_id'], set_=values))
        await session.commit()


async def quota(ctx: BotContext, job: GuardJob | None) -> bool:
    try:
        count = int(await ctx.redis.eval(group_broadcast.QUOTA, 1,
            ctx.keys('guard_outbound_rate', int(time.time()))))  # type: ignore[misc]
    except RedisError:
        if job is not None:
            await durable.defer(ctx, job, 5, 'rate_state_unavailable')
        return False
    if count > 20:
        if job is not None:
            await durable.defer(ctx, job, 1)
        return False
    return True


async def issuer(ctx: BotContext, session, job: GuardJob) -> bool:
    if job.payload.get('event') not in {'ban', 'graph'}:
        return True  # A fresh group attachment applies already committed security policy.
    fed = await federations.get(ctx, job.payload['fed_id'], session)
    by_id = job.payload.get('by_id')
    if fed is None or not isinstance(by_id, int):
        return False
    role = await federations.role(ctx, fed, by_id, session)
    return role == 'owner' if job.payload['event'] == 'graph' else role in {'owner', 'admin'}


async def current_event(ctx: BotContext, session, job: GuardJob) -> bool:
    if not await authz.active_namespace(ctx, session) or not await issuer(ctx, session, job):
        return False
    fed = await federations.get(ctx, job.payload['fed_id'], session)
    if fed is None:
        return False
    event = job.payload.get('event')
    if event == 'graph':
        return fed.graph_generation == job.payload.get('version')
    if event == 'ban':
        row = await session.get(GuardFedBan, (ctx.bot_id, fed.id, job.user_id or 0), populate_existing=True)
        return row is not None and row.version == job.payload.get('version')
    return True


async def fanout(ctx: BotContext, job: GuardJob) -> ActionResult:
    async with ctx.sm() as session:
        origin = await federations.get(ctx, job.payload['fed_id'], session, lock=True)
        node = await federations.get(ctx, job.payload['node_id'], session)
        if origin is None or node is None or not await current_event(ctx, session, job):
            return result_of(StepResult('fed_fanout', 'skipped', 'intent_or_role_changed'))
        count = int((await session.execute(select(func.count()).select_from(GuardJob).where(
            GuardJob.bot_id == ctx.bot_id, GuardJob.kind == 'fed_enforce',
            GuardJob.status.in_({'pending', 'running'})))).scalar_one())
        if count >= MAX_BACKLOG:
            await durable.defer(ctx, job, 30, 'fanout_backlog')
            return actions.failure('fed_fanout', 'fanout_backlog')
        payload = dict(job.payload)
        if not payload['chats_done']:
            query = select(GuardFedChat).join(GuardChat, (GuardChat.bot_id == GuardFedChat.bot_id) &
                (GuardChat.chat_id == GuardFedChat.chat_id)).where(GuardFedChat.bot_id == ctx.bot_id,
                GuardFedChat.fed_id == node.id, GuardChat.active.is_(True),
                GuardFedChat.chat_id > payload['chat_cursor'])
            if job.user_id:
                observed = select(GuardFedObservation.chat_id).where(GuardFedObservation.bot_id == ctx.bot_id,
                    GuardFedObservation.user_id == job.user_id)
                query = query.where(GuardFedChat.chat_id.in_(observed))
            chats = list((await session.execute(query.order_by(GuardFedChat.chat_id).limit(BATCH))).scalars())
            for attachment in chats:
                await enqueue_chat(ctx, session, attachment, user_id=job.user_id or 0,
                    root_id=origin.id, version=int(payload['version']), by_id=int(payload['by_id']), event=payload['event'])
            if chats:
                payload['chat_cursor'] = chats[-1].chat_id
            else:
                payload['chats_done'] = True
        if not payload['parents_done']:
            parents = list((await session.execute(select(GuardFedSub.fed_id).where(GuardFedSub.bot_id == ctx.bot_id,
                GuardFedSub.target_id == node.id, GuardFedSub.fed_id > payload['parent_cursor'])
                .order_by(GuardFedSub.fed_id).limit(BATCH))).scalars())
            for parent in parents:
                await enqueue_network(ctx, session, origin, user_id=job.user_id or 0,
                    version=int(payload['version']), by_id=int(payload['by_id']), event=payload['event'], node_id=parent)
            if parents:
                payload['parent_cursor'] = parents[-1]
            else:
                payload['parents_done'] = True
        changed = await session.execute(update(GuardJob).where(GuardJob.bot_id == ctx.bot_id, GuardJob.id == job.id,
            GuardJob.status == 'running', GuardJob.lease_owner == job.lease_owner,
            GuardJob.lease_until > utcnow()).values(payload=payload, updated_at=utcnow()))
        if affected(changed) != 1:
            await session.rollback()
            return actions.failure('fed_fanout', 'lease_lost')
        await session.commit()
    if payload['chats_done'] and payload['parents_done']:
        return result_of(StepResult('fed_fanout', 'applied'))
    await durable.defer(ctx, job, 1, 'fanout_continues')
    return result_of(StepResult('fed_fanout', 'skipped', 'fanout_continues'))


async def enforce_user(ctx: BotContext, chat_id: int, user_id: int, *, job: GuardJob | None = None,
        passive: bool = False) -> tuple[list[GuardFedBan], ActionResult]:
    if chat_id >= 0 or not perms.valid_human_id(user_id) or not await authz.active_namespace(ctx):
        return [], actions.failure('fed_enforce', 'wrong_scope')
    svc = ctx.extras['guard']
    async with svc.member_session(chat_id, user_id) as (session, _member):
        chat = await session.get(GuardChat, (ctx.bot_id, chat_id))
        attachment = await federations.attached(ctx, chat_id, session)
        if chat is None or not chat.active or attachment is None:
            return [], result_of(StepResult('fed_enforce', 'skipped', 'attachment_changed'))
        if job is not None and (job.bot_id != ctx.bot_id or job.generation != attachment.generation
                or job.payload['node_id'] != attachment.fed_id):
            return [], result_of(StepResult('fed_enforce', 'skipped', 'attachment_changed'))
        reached = await fed_graph.reached(ctx, attachment.fed_id, session)
        locked_ids = reached | ({job.payload['fed_id']} if job is not None else set())
        for fed_id in sorted(locked_ids):
            await federations.get(ctx, fed_id, session, lock=True)
        expected_attachment = attachment.generation
        attachment = await federations.attached(ctx, chat_id, session, lock=True)
        if attachment is None or attachment.generation != expected_attachment:
            return [], result_of(StepResult('fed_enforce', 'skipped', 'attachment_changed'))
        if await fed_graph.reached(ctx, attachment.fed_id, session) != reached:
            if job is not None:
                await durable.defer(ctx, job, 1, 'graph_changed')
            return [], actions.failure('fed_enforce', 'graph_changed')
        if job is not None and not await current_event(ctx, session, job):
            return [], result_of(StepResult('fed_enforce', 'skipped', 'intent_or_role_changed'))
        desired = await fed_bans.effective(ctx, attachment.fed_id, user_id, session)
        where = (GuardRestriction.bot_id == ctx.bot_id, GuardRestriction.chat_id == chat_id,
            GuardRestriction.user_id == user_id)
        existing = list((await session.execute(select(GuardRestriction).where(*where))).scalars())
        fed_owned = [r for r in existing if r.source.startswith('fed:')]
        current_member = await perms.fresh_member(ctx, chat_id, user_id)
        if current_member is None:
            return desired, actions.failure('fed_enforce', 'lookup_failed')
        if perms.member_rights(current_member).is_admin or current_member.user.is_bot:
            return [], result_of(StepResult('fed_enforce', 'skipped', 'target_protected'))
        if desired:
            # An external pre-existing ban is no proof of our ownership.
            known = [r for r in existing if r.mode == 'ban' and r.state == 'applied']
            if current_member.status == 'kicked' and not known:
                return desired, result_of(StepResult('fed_enforce', 'acknowledged', 'external_ban_preserved'))
            capability = await authz.internal_authorize(ctx, chat_id, frozenset({'restrict_members'}))
            if not capability.allowed:
                return desired, actions.failure('fed_enforce', capability.code)
            if current_member.status == 'kicked' and known:
                result = result_of(StepResult('fed_enforce', 'acknowledged', 'known_ban_current'))
            else:
                if not await quota(ctx, job):
                    return desired, actions.failure('fed_enforce', 'local_rate')
                if job is not None:
                    await durable.dispatched(ctx, job)

                async def guard():
                    if not await authz.active_namespace(ctx, session):
                        return False
                    current = await federations.attached(ctx, chat_id, session)
                    if current is None or current.generation != attachment.generation:
                        return False
                    if job is not None and not await current_event(ctx, session, job):
                        return False
                    latest = await fed_bans.effective(ctx, attachment.fed_id, user_id, session)
                    return [(r.fed_id, r.version) for r in latest] == [(r.fed_id, r.version) for r in desired]

                primary = desired[0]
                result = await actions.punish(ctx, chat_id, user_id, 'ban', None, source=source(primary.fed_id),
                    generation=str(primary.version), dispatch_guard=guard)
            if result.primary_completed:
                # The actual current/applied ban satisfies every current source policy.
                for ban in desired:
                    values = dict(mode='ban', state='applied', generation=str(ban.version), until=None, updated_at=utcnow())
                    await session.execute(upsert(session, GuardRestriction).values(bot_id=ctx.bot_id, chat_id=chat_id,
                        user_id=user_id, source=source(ban.fed_id), **values).on_conflict_do_update(
                            index_elements=['bot_id', 'chat_id', 'user_id', 'source'], set_=values))
                active_sources = {source(b.fed_id) for b in desired}
                for prior in fed_owned:
                    if prior.source not in active_sources and prior.state == 'applied':
                        await session.delete(prior)
            return desired, result
        if passive or job is None or job.payload.get('event') != 'ban':
            # Policy removal/leave does not invent a remote unban. Current actual membership
            # proves an obsolete ban is already gone; retire only known local provenance.
            if current_member.status != 'kicked':
                for prior in fed_owned:
                    if prior.state == 'applied':
                        await session.delete(prior)
            return [], result_of(StepResult('fed_enforce', 'skipped', 'no_current_ban'))
        own = next((r for r in fed_owned if r.source == source(job.payload['fed_id'])), None)
        if own is None:
            return [], result_of(StepResult('fed_unban', 'skipped', 'no_owned_ban'))
        if own.state != 'applied':
            return [], actions.failure('fed_unban', 'ownership_uncertain')
        others = [r for r in existing if r is not own and r.mode == 'ban' and (r.until is None or r.until > utcnow())]
        if others:
            await session.delete(own)
            return [], result_of(StepResult('fed_source_retire', 'applied')).with_steps(
                StepResult('fed_unban', 'skipped', 'other_restriction_active'))
        if not await quota(ctx, job):
            return [], actions.failure('fed_unban', 'local_rate')
        await durable.dispatched(ctx, job)
        # The current origin ban row is locked above: a new ban cannot commit over this release.
        result = await actions.unban(ctx, chat_id, user_id, source=own.source, generation=own.generation)
        return [], result


async def run(ctx: BotContext, job: GuardJob) -> ActionResult:
    if job.user_id is not None:
        try:
            _sources, result = await enforce_user(ctx, job.chat_id, job.user_id, job=job)
            return result
        except FedError as error:
            return actions.failure('fed_enforce', str(error))
    # A fresh membership/graph change reconciles only real observations, in bounded pages.
    async with ctx.sm() as session:
        attachment = await federations.attached(ctx, job.chat_id, session)
        if attachment is None or attachment.generation != job.generation or not await current_event(ctx, session, job):
            return result_of(StepResult('fed_reconcile', 'skipped', 'attachment_or_intent_changed'))
        cursor = int(job.payload.get('user_cursor', 0))
        users = list((await session.execute(select(GuardFedObservation.user_id).where(
            GuardFedObservation.bot_id == ctx.bot_id, GuardFedObservation.chat_id == job.chat_id,
            GuardFedObservation.user_id > cursor).order_by(GuardFedObservation.user_id).limit(BATCH))).scalars())
        for uid in users:
            await enqueue_chat(ctx, session, attachment, user_id=uid, root_id=job.payload['fed_id'],
                version=job.payload['version'], by_id=job.payload.get('by_id'), event=job.payload['event'])
        if users:
            payload = {**job.payload, 'user_cursor': users[-1]}
            changed = await session.execute(update(GuardJob).where(GuardJob.bot_id == ctx.bot_id, GuardJob.id == job.id,
                GuardJob.status == 'running', GuardJob.lease_owner == job.lease_owner,
                GuardJob.lease_until > utcnow()).values(payload=payload, updated_at=utcnow()))
            if affected(changed) != 1:
                await session.rollback()
                return actions.failure('fed_reconcile', 'lease_lost')
        await session.commit()
    if users:
        await durable.defer(ctx, job, 1, 'reconcile_continues')
        return result_of(StepResult('fed_reconcile', 'skipped', 'reconcile_continues'))
    return result_of(StepResult('fed_reconcile', 'applied'))


async def policy(ctx: BotContext, chat_id: int, user_id: int, session=None) -> tuple[GuardFedChat | None, list[GuardFedBan]]:
    if not await authz.active_namespace(ctx, session):
        return None, []
    if session is None:
        async with ctx.sm() as owned:
            return await policy(ctx, chat_id, user_id, owned)
    attachment = await federations.attached(ctx, chat_id, session)
    return (attachment, await fed_bans.effective(ctx, attachment.fed_id, user_id, session)) if attachment else (None, [])


async def is_banned(ctx: BotContext, chat_id: int, user_id: int, session=None) -> bool:
    _attachment, sources = await policy(ctx, chat_id, user_id, session)
    if not sources:
        return False
    member = await perms.fresh_member(ctx, chat_id, user_id)
    return member is None or not perms.member_rights(member).is_admin


async def passive(ctx: BotContext, chat_id: int, user: User, *, event: str) -> bool:
    if user.is_bot:
        return False
    attachment, sources = await policy(ctx, chat_id, user.id)
    if attachment is None or not sources:
        return False
    member = await perms.fresh_member(ctx, chat_id, user.id)
    if member is not None and perms.member_rights(member).is_admin:
        return False
    from bots.groupguard.models import GuardEventReceipt
    identity = dedupe(user.id, event, *(f'{r.fed_id}:{r.version}' for r in sources))
    async with ctx.sm() as session:
        inserted = (await session.execute(upsert(session, GuardEventReceipt).values(bot_id=ctx.bot_id,
            chat_id=chat_id, kind='fed_passive', fingerprint=identity, user_id=user.id,
            status='processing', created_at=utcnow(), updated_at=utcnow()).on_conflict_do_nothing()
            .returning(GuardEventReceipt.fingerprint))).scalar_one_or_none()
        await session.commit()
    if inserted is None:
        return True  # Prior/unknown effects for this exact actual event are never blindly repeated.
    try:
        current, result = await enforce_user(ctx, chat_id, user.id, passive=True)
    except FedError as error:
        current, result = sources, actions.failure('fed_passive', str(error))
    status = 'succeeded' if result.primary_completed else 'uncertain' if any(
        s.error_code in {'TelegramNetworkError', 'TelegramServerError'} for s in result.steps) else 'failed'
    if any(step.retry_after is not None or step.error_code in {'local_rate', 'rate_state_unavailable'}
            for step in result.steps):
        async with ctx.sm() as session:
            active_attachment = await federations.attached(ctx, chat_id, session)
            if active_attachment is not None:
                await enqueue_chat(ctx, session, active_attachment, user_id=user.id,
                    root_id=current[0].fed_id if current else attachment.fed_id,
                    version=current[0].version if current else 0, event='passive')
                await session.commit()
    async with ctx.sm() as session:
        await session.execute(update(GuardEventReceipt).where(GuardEventReceipt.bot_id == ctx.bot_id,
            GuardEventReceipt.chat_id == chat_id, GuardEventReceipt.kind == 'fed_passive',
            GuardEventReceipt.fingerprint == identity).values(status=status, updated_at=utcnow()))
        await session.commit()
    if not current:
        return False
    attachment = await federations.attached(ctx, chat_id)
    if attachment is not None and not attachment.quiet:
        cfg = await ctx.extras['guard'].config(chat_id, fresh=True)
        t = actions.group_t(ctx, cfg)
        fed = await federations.get(ctx, current[0].fed_id)
        from html import escape

        from aiogram.types import Message

        from bots.groupguard import cleanup
        text = t('gg-fed-passive' if result.primary_completed else 'gg-fed-enforce-failed',
            user=actions.mention(user.id, user.first_name), source=escape(fed.name if fed else current[0].fed_id),
            id=current[0].fed_id, reason=escape(current[0].reason or '—'))

        async def notify():
            sent = await ctx.bot.send_message(chat_id, text,
                message_thread_id=None if cfg.action_topic in {None, 1} else cfg.action_topic)
            if isinstance(sent, Message):
                await cleanup.schedule(ctx, chat_id, sent, 'action')
                return sent
            return False

        await actions.perform('fed_passive_notice', notify)
    return True


async def request(ctx: BotContext, request) -> bool:
    if not await is_banned(ctx, request.chat.id, request.from_user.id):
        return False
    await observe(ctx, request.chat.id, request.from_user)
    await passive(ctx, request.chat.id, request.from_user,
        event=f'request:{request.user_chat_id}:{int(request.date.timestamp())}')
    if not await is_banned(ctx, request.chat.id, request.from_user.id):
        return False
    cap = await authz.internal_authorize(ctx, request.chat.id, frozenset({'invite_users'}))
    if not cap.allowed:
        return True
    attachment, sources = await policy(ctx, request.chat.id, request.from_user.id)
    if attachment is None or not sources:
        return False
    from bots.groupguard.models import GuardEventReceipt
    fingerprint = dedupe(request.from_user.id, request.user_chat_id, int(request.date.timestamp()),
        *(f'{r.fed_id}:{r.version}' for r in sources))
    async with ctx.sm() as session:
        inserted = (await session.execute(upsert(session, GuardEventReceipt).values(bot_id=ctx.bot_id,
            chat_id=request.chat.id, kind='fed_request', fingerprint=fingerprint, user_id=request.from_user.id,
            status='processing', created_at=utcnow(), updated_at=utcnow()).on_conflict_do_nothing()
            .returning(GuardEventReceipt.fingerprint))).scalar_one_or_none()
        await session.commit()
    if inserted is None:
        return True
    step = await actions.perform('fed_request_decline', lambda: ctx.bot.decline_chat_join_request(
        request.chat.id, request.from_user.id))
    async with ctx.sm() as session:
        await session.execute(update(GuardEventReceipt).where(GuardEventReceipt.bot_id == ctx.bot_id,
            GuardEventReceipt.chat_id == request.chat.id, GuardEventReceipt.kind == 'fed_request',
            GuardEventReceipt.fingerprint == fingerprint).values(status='succeeded' if step.completed else
                'uncertain' if step.error_code in {'TelegramNetworkError', 'TelegramServerError'} else 'failed',
                error_code=step.error_code, updated_at=utcnow()))
        await session.commit()
    return True
