"""Federation commands use their actual group or private owner context, never a connected alias."""
from __future__ import annotations

import json
import secrets
import time
from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from redis.exceptions import RedisError

from bots.groupguard import authz, federations, pagination, perms
from bots.groupguard.federations import Change, FedError
from bots.groupguard.keyboards import GgCb
from bots.groupguard.models import GuardFederation
from bots.groupguard.reviews import CLAIM
from core.sdk.context import BotContext

COMMANDS = ('newfed', 'renamefed', 'delfed', 'fedpromote', 'feddemote', 'feddemoteme', 'fedreason', 'fednotif',
    'setfedlog', 'unsetfedlog', 'fedinfo', 'fedadmins', 'chatfed', 'myfeds', 'joinfed', 'leavefed', 'quietfed')


def boolean(value: str) -> bool:
    if value.lower() in {'on', 'yes', 'true', '1'}:
        return True
    if value.lower() in {'off', 'no', 'false', '0'}:
        return False
    raise FedError('value')


async def confirm(ctx: BotContext, fed, source: Message, *, kind: str, target: int | None = None) -> None:
    nonce = secrets.token_urlsafe(16)
    state = dict(created=time.time(),bot_id=ctx.bot_id, fed_id=fed.id, revision=fed.revision, owner_id=fed.owner_id,
        kind=kind, target=target, source_chat_id=source.chat.id, source_message_id=source.message_id)
    profile=await ctx.users.get(fed.owner_id)
    t = ctx.translator.bind(profile.lang if profile is not None else None)
    key = ctx.keys('fed_confirm', nonce)
    await ctx.redis.set(key, json.dumps(state), ex=300, nx=True)
    sent = await ctx.bot.send_message(fed.owner_id,
        t('gg-fed-confirm-' + kind, name=escape(fed.name), id=fed.id, destination=str(target or source.chat.id)),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=t('gg-btn-confirm-delete') if kind == 'delete' else t('gg-done'),
                callback_data=GgCb(action='fc', chat=source.chat.id, arg=nonce).pack()),
            InlineKeyboardButton(text=t('gg-fed-cancel'),
                callback_data=GgCb(action='fx', chat=source.chat.id, arg=nonce).pack())]]))
    if not isinstance(sent, Message) or not await authz.bind_message(ctx, sent, target_chat_id=source.chat.id,
            owner_id=fed.owner_id, kind='fed_confirm', data=nonce, slot='fed'):
        await ctx.redis.delete(key)
        raise FedError('delivery')


async def target(ctx: BotContext, message: Message, args: str, fed) -> perms.Target | None:
    # Group @username resolution uses the shared live member proof. Private usernames require
    # a currently observed user in one of the owned federation's actual groups.
    if message.chat.type != 'private' or not args.startswith('@') or message.reply_to_message is not None:
        return await perms.resolve_target(ctx, message, args)
    first, _, remaining = args.partition(' ')
    raw = await ctx.redis.get(ctx.keys('uname', first[1:].lower()))
    data = json.loads(raw) if raw else None
    if not data or (isinstance(data, dict) and data.get('ambiguous')):
        raise FedError('target')
    uid = int(data['id'] if isinstance(data, dict) else data)
    from sqlalchemy import select

    from bots.groupguard.models import GuardFedChat
    async with ctx.sm() as session:
        chats = list((await session.execute(select(GuardFedChat.chat_id).where(
            GuardFedChat.bot_id == ctx.bot_id, GuardFedChat.fed_id == fed.id).order_by(
                GuardFedChat.chat_id).limit(50))).scalars())
    for chat in chats:
        receiver = await perms.fresh_rights(ctx, chat, ctx.bot_id)
        member = await perms.fresh_member(ctx, chat, uid) if receiver is not None and receiver.is_admin else None
        if member is not None and not member.user.is_bot and (member.user.username or '').lower() == first[1:].lower():
            return perms.Target(uid, member.user.first_name, remaining.split(), remaining)
    raise FedError('target')


def build_router(ctx: BotContext) -> Router:
    router = Router(name='gg_federations')

    @router.message(F.chat.type.in_({'private', 'group', 'supergroup'}), Command(*COMMANDS))
    async def command(message: Message, command: CommandObject, t):
        actor = authz.actor_from_message(ctx, message)
        fed: GuardFederation | None
        try:
            name, args = command.command, (command.args or '').strip()
            if name in {'fedinfo','fedadmins','chatfed','quietfed'}:
                await federations.public_actor(ctx,actor)
                uid=actor.human_id or 0
            else:
                uid=await federations.human(ctx,actor)
            if name == 'newfed':
                fed = await federations.create(ctx, actor, args)
                await message.reply(t('gg-fed-created', name=escape(fed.name), id=fed.id))
                return
            if name == 'myfeds':
                cursor = federations.identifier(args) if args else ''
                rows = await federations.mine(ctx, uid, after=cursor, limit=21)
                lines: list[str]=[]
                shown=0
                for listed in rows[:20]:
                    entry=escape(listed.name)+' — <code>'+listed.id+'</code>'
                    candidate=t('gg-fed-list',rows='\n'.join([*lines,entry,'/myfeds '+listed.id]))
                    if lines and pagination.units(candidate)>3800:
                        break
                    lines.append(entry)
                    shown+=1
                body='\n'.join(lines)
                if len(rows)>shown:
                    body+='\n/myfeds '+rows[shown-1].id
                await message.reply(t('gg-fed-list', rows=body or t('gg-none')))
                return
            if name in {'joinfed', 'leavefed', 'quietfed'}:
                if message.chat.type not in {'group', 'supergroup'}:
                    raise FedError('group')
                if name == 'quietfed' and not args:
                    row = await federations.attached(ctx, message.chat.id)
                    if row is None:
                        raise FedError('missing')
                    await message.reply(t('gg-fed-quiet', value=t('gg-on') if row.quiet else t('gg-off')))
                    return
                if name=='quietfed':
                    from bots.groupguard.operations import operation_for, submit
                    desired=boolean(args)
                    row=await federations.attached(ctx,message.chat.id)
                    if row is None:
                        raise FedError('missing')
                    await submit(ctx,message,operation_for(message,'fed_quiet',key=row.fed_id,loud=desired,
                        options_json=json.dumps({'expected_generation':row.generation})))
                    return
                if name == 'leavefed' and args:
                    raise FedError('value')
                await federations.membership(ctx, actor, args if name == 'joinfed' else None,
                    quiet=boolean(args) if name == 'quietfed' else None)
                await message.reply(t('gg-done'))
                return
            if name == 'chatfed':
                if message.chat.type not in {'group', 'supergroup'} or args:
                    raise FedError('group')
                row = await federations.attached(ctx, message.chat.id)
                if row is None:
                    raise FedError('missing')
                fed = await federations.get(ctx, row.fed_id)
            else:
                parts = args.split()
                explicit = parts[0] if name in {'fedinfo', 'fedadmins', 'feddemoteme'} and parts else None
                if len(parts) > (2 if name == 'fedadmins' else 1) and name in {'fedinfo', 'fedadmins', 'feddemoteme'}:
                    raise FedError('value')
                fed = await federations.context(ctx, actor, explicit)
            if fed is None:
                raise FedError('missing')
            if name in {'fedinfo', 'chatfed'}:
                count = await federations.admin_count(ctx, fed.id)
                await message.reply(t('gg-fed-info', name=escape(fed.name), id=fed.id, owner=str(fed.owner_id),
                    admins=str(count), reasons=t('gg-on') if fed.reason_required else t('gg-off'),
                    notifications=t('gg-on') if fed.notifications else t('gg-off'), log=str(fed.log_chat_id or '—')))
                return
            if name == 'fedadmins':
                parts = args.split()
                after_user = 0
                if len(parts) == 2:
                    if not parts[1].isdigit() or len(parts[1]) > 16:
                        raise FedError('value')
                    after_user = int(parts[1])
                admins = await federations.admins(ctx, fed.id, limit=101, after=after_user)
                body = '\n'.join(map(str, admins[:101]))
                if len(admins) > 101:
                    body += '\n/fedadmins ' + fed.id + ' ' + str(admins[100])
                await message.reply(t('gg-fed-admins', rows=body))
                return
            if name == 'feddemoteme':
                if not args:
                    raise FedError('id')
                request = Change('self_remove')
            else:
                if fed.owner_id != uid:
                    raise FedError('authority')
                if name == 'delfed':
                    if message.chat.id != uid or args:
                        raise FedError('private')
                    await confirm(ctx, fed, message, kind='delete')
                    await message.reply(t('gg-fed-confirm-sent'))
                    return
                if name == 'setfedlog':
                    if not args.lstrip('-').isdigit() or len(args) > 17:
                        raise FedError('destination')
                    destination = int(args)
                    if not await federations.destination(ctx, uid, destination):
                        raise FedError('destination')
                    await confirm(ctx, fed, message, kind='log', target=destination)
                    await message.reply(t('gg-fed-confirm-sent'))
                    return
                if name in {'fedreason', 'fednotif'} and not args:
                    await message.reply(t('gg-fed-policy', reasons=t('gg-on') if fed.reason_required else t('gg-off'),
                        notifications=t('gg-on') if fed.notifications else t('gg-off')))
                    return
                if name in {'fedpromote', 'feddemote'}:
                    selected = await target(ctx, message, args, fed)
                    if selected is None or selected.remaining:
                        raise FedError('target')
                    request = Change('promote' if name == 'fedpromote' else 'demote', selected.user_id)
                elif name == 'renamefed':
                    request = Change('rename', args)
                elif name == 'fedreason':
                    request = Change('reason', boolean(args))
                elif name == 'fednotif':
                    request = Change('notif', boolean(args))
                elif name == 'unsetfedlog' and not args:
                    request = Change('unlog')
                else:
                    raise FedError('value')
            _fed, delivered = await federations.change(ctx, actor, fed.id, request)
            await message.reply(t('gg-done') if delivered.status != 'failed' else t('gg-fed-saved-delivery-failed'))
        except (FedError, perms.TargetError, RedisError, ValueError, TypeError, KeyError) as error:
            code = str(error) if isinstance(error, FedError) else 'target'
            await message.reply(t('gg-fed-error-' + code) if code in {
                'authority', 'private', 'group', 'owned', 'name', 'id', 'missing', 'creator', 'target',
                'value', 'stale', 'destination', 'delivery'} else t('gg-setting-invalid'))

    @router.channel_post(Command('setfedlog'))
    async def channel(message: Message, command: CommandObject):
        t = ctx.translator.bind(None)
        try:
            if not await authz.active_namespace(ctx):
                raise FedError('authority')
            fed = await federations.get(ctx, (command.args or '').strip())
            if fed is None:
                raise FedError('missing')
            if not await federations.destination(ctx, fed.owner_id, message.chat.id):
                raise FedError('destination')
            await confirm(ctx, fed, message, kind='log', target=message.chat.id)
            await message.reply(t('gg-fed-confirm-sent'))
        except (FedError, RedisError):
            await message.reply(t('gg-fed-error-destination'))

    @router.callback_query(GgCb.filter(F.action.in_({'fc', 'fx'})))
    async def confirmation(query: CallbackQuery, callback_data: GgCb, t):
        key = ctx.keys('fed_confirm', callback_data.arg)
        try:
            if not await authz.bound_message(ctx, query, target_chat_id=callback_data.chat,
                    kind='fed_confirm', data=callback_data.arg, slot='fed'):
                raise FedError('authority')
            raw = await ctx.redis.get(key)
            state = json.loads(raw) if raw else {}
            actor = authz.actor_from_callback(ctx, query)
            uid = await federations.human(ctx, actor)
            fed = await federations.get(ctx, state['fed_id'])
            if (state.get('bot_id') != ctx.bot_id or state.get('owner_id') != uid
                    or state.get('source_chat_id') != callback_data.chat or fed is None or fed.owner_id != uid
                    or fed.revision != state.get('revision')):
                raise FedError('stale')
            if callback_data.action == 'fx':
                if await ctx.redis.eval(CLAIM, 1, key, raw) != 1:  # type: ignore[misc]
                    raise FedError('stale')
                await query.answer(t('gg-fed-cancelled'))
                return
            kind = state['kind']
            if kind not in {'delete', 'log'}:
                raise FedError('value')
            if kind == 'log' and not await federations.destination(ctx, uid, state['target']):
                raise FedError('destination')
            if await ctx.redis.eval(CLAIM, 1, key, raw) != 1:  # type: ignore[misc]
                raise FedError('stale')
            fed, result = await federations.change(ctx, actor, fed.id,
                Change(kind, state.get('target'), expected_revision=state['revision']))
            await ctx.audit.record(uid, 'gg_fed_confirmation', fed.id, kind=kind,
                source_chat_id=state['source_chat_id'], source_message_id=state['source_message_id'],
                confirmation_chat_id=actor.source_chat_id, confirmation_message_id=actor.message_id)
            await query.answer(t('gg-fed-saved-delivery-failed') if result.status == 'failed' else t('gg-done'),
                show_alert=result.status == 'failed')
            if isinstance(query.message, Message):
                await query.message.edit_text(t('gg-fed-deleted') if kind == 'delete' else
                    t('gg-fed-log-set', destination=str(fed.log_chat_id)))
        except (FedError, RedisError, ValueError, TypeError, KeyError):
            await query.answer(t('gg-fed-error-stale'), show_alert=True)

    return router
