"""Personal immutable import/reset and privacy confirmations, bound to actual delivered cards."""
from __future__ import annotations

import base64
import json
import secrets
import time

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from redis.exceptions import RedisError

from bots.groupguard import authz, fed_files, portability, privacy
from bots.groupguard.federations import FedError
from bots.groupguard.keyboards import GgCb
from bots.groupguard.reviews import CLAIM
from bots.groupguard.scope import GroupMessages, target_chat
from core.sdk.context import BotContext
from core.ui.text import esc


async def rate(ctx: BotContext, name: str, scope: int) -> None:
    if not await ctx.redis.set(ctx.keys('gg',name,'rate',scope),'1',ex=300,nx=True):
        raise portability.PortableError('rate')


async def card(ctx: BotContext, message: Message, state: dict, t) -> None:
    user=message.from_user
    if user is None or user.is_bot:
        raise portability.PortableError('authority')
    nonce=secrets.token_urlsafe(16)
    state.update(created=time.time(),bot_id=ctx.bot_id,user_id=user.id,source_chat_id=message.chat.id,source_message_id=message.message_id)
    key=ctx.keys('gg','data_confirm',user.id,nonce)
    raw=json.dumps(state)
    if not await ctx.redis.set(key,raw,ex=300,nx=True):
        raise portability.PortableError('delivery')
    kind=state['kind']
    sent=await ctx.bot.send_message(user.id,t('gg-data-confirm',operation=t('gg-data-'+kind),
        group=str(state['chat_id']),modules=esc(', '.join(state.get('modules',[]))),digest=state.get('digest','—')),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=t('gg-data-confirm-button'),callback_data=GgCb(action='dc',chat=state['chat_id'],arg=nonce).pack()),
            InlineKeyboardButton(text=t('gg-fed-cancel'),callback_data=GgCb(action='dx',chat=state['chat_id'],arg=nonce).pack())]]))
    if not isinstance(sent,Message) or not await authz.bind_message(ctx,sent,target_chat_id=state['chat_id'],
            owner_id=user.id,kind='data_confirm',data=nonce,slot='data'):
        await ctx.redis.delete(key)
        raise portability.PortableError('delivery')
    await message.reply(t('gg-data-personal'))


def build_router(ctx: BotContext) -> Router:
    router=Router(name='gg_data')

    @router.message(GroupMessages(),Command('export','import','reset'))
    async def modules(message: Message,command: CommandObject,t):
        try:
            actor=authz.actor_from_message(ctx,message)
            chat=target_chat(message).id
            selected=portability.selected(command.args or 'all')
            if command.command=='export':
                exported=await portability.export(ctx,actor,chat,selected)
                await rate(ctx,'portability',chat)
                await message.answer_document(BufferedInputFile(exported,filename='groupguard-modules-v1.json'))
                return
            await portability.authorize(ctx,actor,chat,creator=True)
            body: bytes | None=None
            if command.command=='import':
                body,_filename=await fed_files.download(ctx,message)
                portability.parse(body,selected)
            cfg=await ctx.extras['guard'].config(chat,fresh=True)
            intent=portability.Intent(chat,selected,body,cfg._revision,command.command=='reset')
            await card(ctx,message,dict(kind=command.command,chat_id=chat,modules=sorted(selected),
                body=base64.b64encode(body).decode() if body is not None else None,
                revision=cfg._revision,digest=intent.digest),t)
        except (portability.PortableError,FedError,privacy.PrivacyError,RedisError,ValueError,TelegramAPIError) as error:
            code=str(error) if isinstance(error,(portability.PortableError,privacy.PrivacyError)) else 'format'
            await message.reply(t('gg-data-error-'+code) if code in DATA_ERRORS else t('gg-data-error-format'))

    @router.message(Command('privacy'))
    async def personal(message: Message,command: CommandObject,t):
        try:
            actor=authz.actor_from_message(ctx,message)
            uid=await privacy.requester(ctx,actor)
            mode,_,cursor=(command.args or 'policy').strip().partition(' ')
            if mode=='policy' and not cursor:
                await message.reply(t('gg-privacy-policy'))
            elif mode=='data':
                body=await privacy.inventory(ctx,actor,cursor)
                await message.answer_document(BufferedInputFile(body,filename='groupguard-own-data-v1.json'))
                next_cursor=json.loads(body)['next_cursor']
                if next_cursor:
                    await message.answer(t('gg-privacy-next',cursor=next_cursor))
            elif mode=='delete' and not cursor:
                await card(ctx,message,dict(kind='privacy-delete',chat_id=uid),t)
            else:
                await message.reply(t('gg-privacy-usage'))
        except (privacy.PrivacyError,FedError,RedisError,TelegramAPIError,ValueError):
            await message.reply(t('gg-privacy-private'))

    @router.callback_query(GgCb.filter(F.action.in_({'dc','dx'})))
    async def confirm(query: CallbackQuery,callback_data: GgCb,t):
        key=ctx.keys('gg','data_confirm',query.from_user.id,callback_data.arg)
        try:
            if not await authz.bound_message(ctx,query,target_chat_id=callback_data.chat,kind='data_confirm',
                    data=callback_data.arg,slot='data'):
                raise portability.PortableError('stale')
            raw=await ctx.redis.get(key)
            state=json.loads(raw) if raw else {}
            if (state.get('bot_id')!=ctx.bot_id or state.get('user_id')!=query.from_user.id or
                    state.get('chat_id')!=callback_data.chat):
                raise portability.PortableError('stale')
            actor=authz.actor_from_callback(ctx,query)
            kind=state['kind']
            if callback_data.action=='dc':
                if kind=='privacy-delete':
                    await privacy.requester(ctx,actor)
                else:
                    await portability.authorize(ctx,actor,callback_data.chat,creator=True)
            if await ctx.redis.execute_command('EVAL',CLAIM,1,key,raw)!=1:
                raise portability.PortableError('stale')
            if callback_data.action=='dx':
                await query.answer(t('gg-fed-cancel'))
                if isinstance(query.message,Message):
                    await query.message.edit_text(t('gg-fed-cancel'))
                return
            if kind=='privacy-delete':
                await rate(ctx,'privacy',query.from_user.id)
                await privacy.erase(ctx,actor)
                text=t('gg-privacy-deleted')
            else:
                body=base64.b64decode(state['body']) if state['body'] is not None else None
                intent=portability.Intent(state['chat_id'],frozenset(state['modules']),body,state['revision'],kind=='reset')
                if intent.digest!=state['digest']:
                    raise portability.PortableError('stale')
                await rate(ctx,'portability',intent.chat_id)
                await portability.apply(ctx,actor,intent)
                text=t('gg-data-saved')
            await query.answer(text)
            if isinstance(query.message,Message):
                await query.message.edit_text(text)
        except (portability.PortableError,privacy.PrivacyError,FedError,RedisError,TelegramAPIError,ValueError,KeyError,TypeError) as error:
            code=str(error) if isinstance(error,(portability.PortableError,privacy.PrivacyError)) else 'stale'
            await query.answer(t('gg-data-error-'+code) if code in DATA_ERRORS else t('gg-data-error-format'),show_alert=True)
    return router


DATA_ERRORS={'authority','format','limit','version','module','field','item','media','destination','language',
    'stale','restore','rate','delivery','saved_delivery','cache_pending'}
