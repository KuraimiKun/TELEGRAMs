"""Actual federation ban, status, subscription and bounded-file command routes."""
from __future__ import annotations

from contextlib import suppress
from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from redis.exceptions import RedisError

from bots.groupguard import authz, fed_bans, fed_files, fed_graph, federations, pagination, perms
from bots.groupguard.federations import FedError
from bots.groupguard.handlers.federations import target
from core.sdk.context import BotContext

COMMANDS = ('fban', 'unfban', 'fedstat', 'fbanstat', 'fbanlist', 'importfbans', 'subfed', 'unsubfed', 'fedsubs')


async def status_text(ctx: BotContext, user_id: int, t, fed_id: str | None = None, *, after: str = '', empty: bool = True) -> str | None:
    rows = await fed_bans.status(ctx, user_id, fed_id, after=after,limit=21)
    lines: list[str] = []
    shown=0
    for row in rows[:20]:
        source = await federations.get(ctx, row.fed_id)
        entry=[t('gg-fed-stat-line', name=escape(source.name[:32] if source else row.fed_id),
            id=row.fed_id, status=t('gg-on') if row.active else t('gg-off'), date=row.updated_at.isoformat())]
        if fed_id is not None:
            entry.append(t('gg-fed-ban-details', user=str(row.user_id), reason=escape(row.reason or '—')))
        reserve=t('gg-fed-stat-more')+'\n/fedstat '+str(user_id)+' after:'+row.fed_id
        candidate_rows='\n'.join([*lines,*entry,reserve])
        candidate=t('gg-fed-stat',user=str(user_id),rows=candidate_rows)
        if lines and pagination.units(candidate)>3800:
            break
        lines.extend(entry)
        shown+=1
    if len(rows)>shown:
        lines.append(t('gg-fed-stat-more')+'\n/fedstat '+str(user_id)+' after:'+rows[shown-1].fed_id)
    if not rows and not empty:
        return None
    return t('gg-fed-stat', user=str(user_id), rows='\n'.join(lines) or t('gg-none'))


def build_router(ctx: BotContext) -> Router:
    router = Router(name='gg_fed_bans')

    @router.message(F.chat.type.in_({'private', 'group', 'supergroup'}), Command(*COMMANDS))
    async def command(message: Message, command: CommandObject, t):
        actor = authz.actor_from_message(ctx, message)
        try:
            name, args = command.command, (command.args or '').strip()
            uid=await federations.public_actor(ctx,actor) if name in {'fedstat','fbanstat','fedsubs'} else await federations.human(ctx,actor)
            after=''
            if name=='fedstat' and ' after:' in args:
                args,after=args.rsplit(' after:',1)
                after=federations.identifier(after)
            if name in {'fedstat', 'fbanstat'}:
                if name == 'fbanstat':
                    if not args or len(args.split()) != 1:
                        raise FedError('id')
                    user_id, fed_id = uid, federations.identifier(args)
                elif not args and message.reply_to_message is None:
                    user_id, fed_id = uid, None
                else:
                    # A trailing UUID selects reason/date in exactly that source federation.
                    tokens = args.split()
                    explicit = None
                    if tokens:
                        with suppress(FedError):
                            explicit = federations.identifier(tokens[-1])
                    target_args = ' '.join(tokens[:-1]) if explicit else args
                    fed = await federations.context(ctx, actor)
                    selected = await target(ctx, message, target_args, fed) if fed else await perms.resolve_target(ctx, message, target_args)
                    if selected is None:
                        if explicit and not target_args and message.reply_to_message is None:
                            user_id = uid
                        else:
                            raise FedError('target')
                    else:
                        if selected.remaining:
                            raise FedError('value')
                        user_id = selected.user_id
                    fed_id = explicit
                if user_id is None:
                    raise FedError('target')
                if fed_id is not None and await federations.get(ctx, fed_id) is None:
                    raise FedError('missing')
                text = await status_text(ctx,user_id,t,fed_id,after=after)
                if text is not None:
                    await message.reply(text)
                return
            fed = await federations.context(ctx, actor)
            if fed is None:
                raise FedError('missing')
            if name in {'fban', 'unfban'}:
                selected = await target(ctx, message, args, fed)
                if selected is None:
                    raise FedError('target')
                row = await fed_bans.change(ctx, actor, fed.id,
                    fed_bans.BanInput(selected.user_id, selected.remaining or None, selected.name), active=name == 'fban')
                await message.reply(t('gg-fed-intent-saved', user=str(row.user_id), version=str(row.version)))
            elif name in {'subfed', 'unsubfed'}:
                await fed_graph.change(ctx, actor, fed.id, args, subscribe=name == 'subfed')
                await message.reply(t('gg-done'))
            elif name == 'fedsubs':
                if args:
                    raise FedError('value')
                subscriptions = await fed_graph.subscriptions(ctx, fed.id)
                await message.reply(t('gg-fed-subscriptions', rows='\n'.join(
                    escape(row.name[:32]) + ' — <code>' + row.id + '</code>' for row in subscriptions) or t('gg-none')))
            elif name == 'fbanlist':
                file = await fed_files.export(ctx, actor, fed.id, args.lower() or 'csv')
                sent = await message.reply_document(file)
                if not isinstance(sent, Message):
                    raise FedError('delivery')
            elif name == 'importfbans':
                if args:
                    raise FedError('value')
                await fed_files.owner(ctx, actor, fed.id)
                body, filename = await fed_files.download(ctx, message)
                parsed = await fed_files.import_rows(ctx, actor, fed.id, body, filename)
                await message.reply(t('gg-fed-imported', count=str(len(parsed.rows)), duplicates=str(parsed.duplicates)))
        except (FedError, perms.TargetError, RedisError, TelegramAPIError, ValueError, TypeError, KeyError) as error:
            code = str(error) if isinstance(error, FedError) else 'delivery' if isinstance(error, TelegramAPIError) else 'target'
            await message.reply(t('gg-fed-error-' + (code.replace('_','-') if code.startswith('file_') else code)) if code in {'authority', 'id', 'missing', 'target', 'value',
                'delivery', 'file_format', 'file_limit', 'file_duplicate', 'file_rate', 'reason', 'reason_required',
                'cycle', 'graph_limit'} else t('gg-setting-invalid'))

    return router
