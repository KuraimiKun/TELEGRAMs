"""Our own bot-scoped federation network, with SQL roles and fresh Telegram membership authority."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from html import escape
from typing import Literal

from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bots.groupguard import actions, authz, perms
from bots.groupguard.contracts import ActionResult, Actor, StepResult, result_of
from bots.groupguard.models import (
    GuardFedAdmin,
    GuardFedBan,
    GuardFedChat,
    GuardFederation,
    GuardFedSub,
    GuardJob,
    GuardRestriction,
)
from core.db.base import upsert, utcnow
from core.db.models import AdminAuditLog
from core.sdk.context import BotContext

Role = Literal['owner', 'admin', 'none']


class FedError(ValueError):
    pass


def identifier(value: str) -> str:
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError) as error:
        raise FedError('id') from error


def name(value: str) -> str:
    value = value.strip()
    if not value or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise FedError('name')
    return value[:64]


async def human(ctx: BotContext, actor: Actor, session: AsyncSession | None = None) -> int:
    if (actor.bot_id != ctx.bot_id or actor.kind != 'human' or actor.human_id is None
            or not perms.valid_human_id(actor.human_id) or not await authz.active_namespace(ctx, session)):
        raise FedError('authority')
    if actor.source_chat_id > 0 and actor.source_chat_id != actor.human_id:
        raise FedError('authority')
    return actor.human_id


async def get(ctx: BotContext, fed_id: str, session: AsyncSession | None = None, *, lock: bool = False) -> GuardFederation | None:
    fed_id = identifier(fed_id)
    if session is not None:
        query = select(GuardFederation).where(GuardFederation.bot_id == ctx.bot_id, GuardFederation.id == fed_id).execution_options(populate_existing=True)
        return (await session.execute(query.with_for_update() if lock else query)).scalar_one_or_none()
    async with ctx.sm() as owned:
        return await get(ctx, fed_id, owned, lock=lock)


async def owned(ctx: BotContext, user_id: int, session: AsyncSession | None = None) -> GuardFederation | None:
    if session is None:
        async with ctx.sm() as owned_session:
            return await owned(ctx, user_id, owned_session)
    return (await session.execute(select(GuardFederation).where(
        GuardFederation.bot_id == ctx.bot_id, GuardFederation.owner_id == user_id))).scalar_one_or_none()


async def attached(ctx: BotContext, chat_id: int, session: AsyncSession | None = None,
        *, lock: bool = False) -> GuardFedChat | None:
    if session is None:
        async with ctx.sm() as owned_session:
            return await attached(ctx, chat_id, owned_session, lock=lock)
    query = select(GuardFedChat).where(GuardFedChat.bot_id == ctx.bot_id,
        GuardFedChat.chat_id == chat_id).execution_options(populate_existing=True)
    return (await session.execute(query.with_for_update() if lock else query)).scalar_one_or_none()


async def context(ctx: BotContext, actor: Actor, explicit: str | None = None) -> GuardFederation | None:
    uid = await public_actor(ctx,actor)
    if explicit:
        return await get(ctx, explicit)
    if actor.source_chat_id > 0:
        if uid is None:
            raise FedError('authority')
        return await owned(ctx, uid)  # Connections never retarget private federation commands.
    chat = await attached(ctx, actor.source_chat_id)
    return await get(ctx, chat.fed_id) if chat is not None else None


async def public_actor(ctx: BotContext, actor: Actor) -> int | None:
    """Public reads accept own anonymous posts and eligible current bots, without federation roles."""
    if actor.kind=='human':
        return await human(ctx,actor)
    if actor.bot_id!=ctx.bot_id or actor.source_chat_id>=0 or not await authz.active_namespace(ctx):
        raise FedError('authority')
    if actor.kind=='anonymous_group':
        if not (await authz.internal_authorize(ctx,actor.source_chat_id,frozenset())).allowed:
            raise FedError('authority')
        return None
    authorized=await authz.authorize(ctx,actor,target_chat_id=actor.source_chat_id,
        caller_rights=frozenset(),bot_rights=frozenset(),require_admin=False)
    if not authorized.allowed:
        raise FedError('authority')
    return actor.bot_sender_id


async def role(ctx: BotContext, fed: GuardFederation, user_id: int, session: AsyncSession) -> Role:
    if fed.bot_id != ctx.bot_id:
        return 'none'
    if fed.owner_id == user_id:
        return 'owner'
    return 'admin' if await session.get(GuardFedAdmin, (ctx.bot_id, fed.id, user_id)) is not None else 'none'


def audit(ctx: BotContext, session: AsyncSession, actor: Actor, action: str, fed_id: str, **details) -> None:
    session.add(AdminAuditLog(bot_id=ctx.bot_id, admin_id=actor.human_id or 0, action='gg_fed_' + action,
        target=fed_id, details=dict(source_chat_id=actor.source_chat_id, message_id=actor.message_id, **details)))


async def destination(ctx: BotContext, owner_id: int, chat_id: int) -> bool:
    if chat_id >= 0:
        return False
    try:
        chat = await ctx.bot.get_chat(chat_id)
    except TelegramAPIError:
        return False
    if chat.id != chat_id or chat.type not in {'group', 'supergroup', 'channel'}:
        return False
    caller = await perms.fresh_rights(ctx, chat_id, owner_id)
    receiver = await perms.fresh_rights(ctx, chat_id, ctx.bot_id)
    return (caller is not None and caller.allows('change_info') and receiver is not None and receiver.is_admin
        and (chat.type != 'channel' or receiver.allows('post_messages')))


async def emit(ctx: BotContext, fed: GuardFederation, actor: Actor, action: str, *,
        target_user_id: int | None = None, reason: str | None = None) -> ActionResult:
    # Private owner notifications and the configured log have independent results.
    profile=await ctx.users.get(fed.owner_id)
    t = ctx.translator.bind(profile.lang if profile is not None else None)
    text = t('gg-fed-event', name=escape(fed.name), id=fed.id, event=t('gg-fed-event-' + action.replace('_', '-')),
        user=str(actor.human_id or 0))
    if target_user_id is not None:
        text += '\n' + t('gg-fed-ban-details', user=str(target_user_id), reason=escape(reason or '—'))
    steps: list[StepResult] = []

    async def send(chat_id: int):
        sent = await ctx.bot.send_message(chat_id, text)
        return sent if isinstance(sent, Message) else False

    if fed.notifications:
        steps.append(await actions.perform('fed_notification', lambda: send(fed.owner_id)))
    log_chat_id = fed.log_chat_id
    if log_chat_id is not None:
        if not await destination(ctx, fed.owner_id, log_chat_id):
            steps.append(StepResult('fed_log', 'failed', 'destination_authority_changed'))
        else:
            steps.append(await actions.perform('fed_log', lambda: send(log_chat_id)))
    result = result_of(*steps) if steps else result_of(StepResult('fed_delivery', 'skipped'))
    await ctx.audit.record(actor.human_id or 0, 'gg_fed_delivery', fed.id, event=action,
        outcomes=[dict(operation=s.operation, status=s.status, error=s.error_code) for s in steps])
    return result


async def create(ctx: BotContext, actor: Actor, value: str) -> GuardFederation:
    uid = await human(ctx, actor)
    if actor.source_chat_id != uid:
        raise FedError('private')
    value = name(value)
    async with ctx.extras['guard'].member_session(0, 0) as (session, _member):
        if await owned(ctx, uid, session) is not None:
            raise FedError('owned')
        await human(ctx, actor, session)
        fed = GuardFederation(bot_id=ctx.bot_id, id=str(uuid.uuid4()), owner_id=uid, name=value,
            reason_required=False, notifications=True, revision=0)
        session.add(fed)
        await session.flush()
        audit(ctx, session, actor, 'create', fed.id)
        return fed


@dataclass(frozen=True, slots=True)
class Change:
    kind: str
    value: str | bool | int | None = None
    expected_revision: int | None = None


async def change(ctx: BotContext, actor: Actor, fed_id: str, request: Change) -> tuple[GuardFederation, ActionResult]:
    uid = await human(ctx, actor)
    async with ctx.extras['guard'].member_session(0, 0) as (session, _member):
        fed = await get(ctx, fed_id, session, lock=True)
        if fed is None:
            raise FedError('missing')
        current_role = await role(ctx, fed, uid, session)
        if request.kind == 'self_remove':
            if current_role != 'admin':
                raise FedError('authority')
        elif current_role != 'owner':
            raise FedError('authority')
        if request.expected_revision is not None and fed.revision != request.expected_revision:
            raise FedError('stale')
        if request.kind in {'rename', 'delete'} and actor.source_chat_id != uid:
            raise FedError('private')
        if request.kind in {'delete', 'log'} and request.expected_revision is None:
            raise FedError('stale')
        if request.kind == 'rename':
            if not isinstance(request.value, str):
                raise FedError('name')
            fed.name = name(request.value)
        elif request.kind in {'promote', 'demote', 'self_remove'}:
            target = uid if request.kind == 'self_remove' else request.value
            if not isinstance(target, int) or isinstance(target, bool) or not perms.valid_human_id(target) or target in {ctx.bot_id, fed.owner_id}:
                raise FedError('target')
            if request.kind == 'promote':
                await session.execute(upsert(session, GuardFedAdmin).values(bot_id=ctx.bot_id,
                    fed_id=fed.id, user_id=target, by_id=uid, created_at=utcnow()).on_conflict_do_nothing())
            else:
                await session.execute(delete(GuardFedAdmin).where(GuardFedAdmin.bot_id == ctx.bot_id,
                    GuardFedAdmin.fed_id == fed.id, GuardFedAdmin.user_id == target))
        elif request.kind in {'reason', 'notif'}:
            if not isinstance(request.value, bool):
                raise FedError('value')
            if request.kind == 'reason':
                fed.reason_required = request.value
            else:
                fed.notifications = request.value
        elif request.kind == 'log':
            if not isinstance(request.value, int) or not await destination(ctx, uid, request.value):
                raise FedError('destination')
            fed.log_chat_id = request.value
        elif request.kind == 'unlog':
            fed.log_chat_id = None
        elif request.kind == 'delete':
            # Retire only this source's local evidence. Existing Telegram bans remain untouched.
            await session.execute(delete(GuardRestriction).where(GuardRestriction.bot_id == ctx.bot_id,
                GuardRestriction.source == 'fed:' + fed.id))
            await session.execute(delete(GuardFedSub).where(GuardFedSub.bot_id == ctx.bot_id,
                or_(GuardFedSub.fed_id == fed.id, GuardFedSub.target_id == fed.id)))
            await session.execute(delete(GuardFedBan).where(GuardFedBan.bot_id == ctx.bot_id,
                GuardFedBan.fed_id == fed.id))
            chats = select(GuardFedChat.chat_id).where(GuardFedChat.bot_id == ctx.bot_id,
                GuardFedChat.fed_id == fed.id)
            await session.execute(update(GuardJob).where(GuardJob.bot_id == ctx.bot_id,
                GuardJob.kind.in_({'fed_fanout', 'fed_enforce'}),
                or_(GuardJob.payload['fed_id'].as_string() == fed.id,
                    GuardJob.payload['node_id'].as_string() == fed.id, GuardJob.chat_id.in_(chats)),
                GuardJob.status.in_({'pending', 'running'}), GuardJob.dispatched.is_(False)).values(status='cancelled'))
            await session.execute(delete(GuardFedAdmin).where(GuardFedAdmin.bot_id == ctx.bot_id, GuardFedAdmin.fed_id == fed.id))
            await session.execute(delete(GuardFedChat).where(GuardFedChat.bot_id == ctx.bot_id, GuardFedChat.fed_id == fed.id))
            await session.delete(fed)
        else:
            raise FedError('value')
        await human(ctx, actor, session)
        if request.kind != 'delete':
            fed.revision += 1
            fed.updated_at = utcnow()
        audit(ctx, session, actor, request.kind, fed.id, value=request.value)
        await session.flush()
    return fed, await emit(ctx, fed, actor, request.kind)


async def change_quiet(ctx: BotContext, actor: Actor, fed_id: str, generation: str, value: bool) -> None:
    """Ordinary group policy, invoked through the immutable operation/review pipeline."""
    chat_id=actor.source_chat_id
    async with ctx.extras['guard'].member_session(0,0) as (session,_member):
        allowed=await authz.authorize(ctx,actor,target_chat_id=chat_id,
            caller_rights=frozenset({'change_info'}),bot_rights=frozenset(),session=session)
        if not allowed.allowed:
            raise FedError('authority')
        row=await attached(ctx,chat_id,session,lock=True)
        if row is None or row.fed_id!=fed_id or row.generation!=generation:
            raise FedError('stale')
        allowed=await authz.authorize(ctx,actor,target_chat_id=chat_id,
            caller_rights=frozenset({'change_info'}),bot_rights=frozenset(),session=session)
        if not allowed.allowed:
            raise FedError('authority')
        row.quiet=value
        row.updated_at=utcnow()
        audit(ctx,session,actor,'quiet',row.fed_id,quiet=value,chat_id=chat_id)
        await session.flush()


async def membership(ctx: BotContext, actor: Actor, fed_id: str | None, *, quiet: bool | None = None) -> GuardFedChat | None:
    await human(ctx, actor)
    chat_id = actor.source_chat_id
    allowed = await authz.authorize(ctx, actor, target_chat_id=chat_id,
        caller_rights=frozenset({'change_info'} if quiet is not None else {'creator'}), bot_rights=frozenset())
    if not allowed.allowed:
        raise FedError('creator' if quiet is None else 'authority')
    await ctx.extras['guard'].ensure_chat(chat_id)
    async with ctx.extras['guard'].member_session(0, 0) as (session, _member):
        allowed = await authz.authorize(ctx, actor, target_chat_id=chat_id,
            caller_rights=frozenset({'change_info'} if quiet is not None else {'creator'}), bot_rights=frozenset())
        if not allowed.allowed:
            raise FedError('authority')
        initial = await attached(ctx, chat_id, session)
        ids = {initial.fed_id} if initial is not None else set()
        if fed_id is not None:
            ids.add(identifier(fed_id))
        for locked_id in sorted(ids):
            await get(ctx, locked_id, session, lock=True)
        row = await attached(ctx, chat_id, session, lock=True)
        if quiet is not None:
            if row is None:
                raise FedError('missing')
            row.quiet = quiet
            row.updated_at = utcnow()
            audit(ctx, session, actor, 'quiet', row.fed_id, quiet=quiet, chat_id=chat_id)
            return row
        previous = row.fed_id if row else None
        if previous is not None and previous != fed_id:
            await session.execute(delete(GuardRestriction).where(GuardRestriction.bot_id == ctx.bot_id,
                GuardRestriction.chat_id == chat_id, GuardRestriction.source.startswith('fed:')))
        if fed_id is None:
            if row is None:
                raise FedError('missing')
            await session.delete(row)
        else:
            fed = await get(ctx, fed_id, session, lock=True)
            if fed is None:
                raise FedError('missing')
            if row is None:
                row = GuardFedChat(bot_id=ctx.bot_id, chat_id=chat_id, fed_id=fed.id, quiet=False,
                    generation=uuid.uuid4().hex)
                session.add(row)
            else:
                row.fed_id = fed.id
                row.generation = uuid.uuid4().hex
                row.updated_at = utcnow()
        await session.execute(update(GuardJob).where(GuardJob.bot_id == ctx.bot_id,
            GuardJob.chat_id == chat_id, GuardJob.kind == 'fed_enforce',
            GuardJob.status.in_({'pending', 'running'}), GuardJob.dispatched.is_(False)).values(status='cancelled'))
        audit(ctx, session, actor, 'leave' if fed_id is None else 'join', previous or fed_id or '', chat_id=chat_id)
        await session.flush()
        if fed_id is not None and row is not None:
            from bots.groupguard import fed_enforcement
            await fed_enforcement.enqueue_chat(ctx, session, row, by_id=actor.human_id, event='membership')
        return row if fed_id is not None else None


async def admins(ctx: BotContext, fed_id: str, limit: int = 100, *, after: int = 0) -> list[int]:
    async with ctx.sm() as session:
        fed = await get(ctx, fed_id, session, lock=True)
        if fed is None:
            raise FedError('missing')
        values = list((await session.execute(select(GuardFedAdmin.user_id).where(
            GuardFedAdmin.bot_id == ctx.bot_id, GuardFedAdmin.fed_id == fed.id, GuardFedAdmin.user_id > after).order_by(
                GuardFedAdmin.user_id).limit(min(limit, 500)))).scalars())
        return [fed.owner_id, *values]


async def mine(ctx: BotContext, user_id: int, *, after: str = '', limit: int = 30) -> list[GuardFederation]:
    async with ctx.sm() as session:
        admin_ids = select(GuardFedAdmin.fed_id).where(GuardFedAdmin.bot_id == ctx.bot_id,
            GuardFedAdmin.user_id == user_id)
        return list((await session.execute(select(GuardFederation).where(GuardFederation.bot_id == ctx.bot_id,
            GuardFederation.id > after, or_(GuardFederation.owner_id == user_id, GuardFederation.id.in_(admin_ids)))
            .order_by(GuardFederation.id).limit(min(limit, 100)))).scalars())


async def admin_count(ctx: BotContext, fed_id: str) -> int:
    async with ctx.sm() as session:
        return int((await session.execute(select(func.count()).select_from(GuardFedAdmin).where(
            GuardFedAdmin.bot_id == ctx.bot_id, GuardFedAdmin.fed_id == identifier(fed_id)))).scalar_one())
