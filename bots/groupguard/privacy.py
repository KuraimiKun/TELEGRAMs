"""Own private data access and bounded deletion, preserving active moderation and other tenants."""
from __future__ import annotations

import base64
import json
import time
import uuid
from datetime import datetime
from typing import Any

from redis.exceptions import RedisError
from sqlalchemy import delete, inspect, or_, select, tuple_, update

from bots.groupguard import durable, federations
from bots.groupguard.contracts import Actor
from bots.groupguard.models import (
    GuardApproval,
    GuardBroadcast,
    GuardChallenge,
    GuardConnection,
    GuardFedAdmin,
    GuardFedBan,
    GuardFederation,
    GuardFedObservation,
    GuardInbox,
    GuardJob,
    GuardMember,
    GuardRestriction,
    GuardWarn,
)
from core.db.base import affected, utcnow
from core.db.models import AdminAuditLog, BotUser, ChildBot, Payment, VipGrant
from core.sdk.context import BotContext

MAX_BYTES = 2 * 1024 * 1024
PAGE = 200


def owned_update(uid: int):
    return or_(*(GuardInbox.payload[kind]['from_user']['id'].as_integer()==uid for kind in (
        'message','edited_message','callback_query','chat_join_request','chat_member','my_chat_member')))


class PrivacyError(ValueError):
    pass


async def requester(ctx: BotContext, actor: Actor, session=None) -> int:
    uid = await federations.human(ctx,actor,session)
    if actor.source_chat_id != uid:
        raise PrivacyError('private')
    return uid


def serial(value: Any) -> Any:
    if isinstance(value,datetime):
        return value.isoformat()
    return value


async def inventory(ctx: BotContext, actor: Actor, cursor: str = '') -> bytes:
    uid = await requester(ctx,actor)
    scope: list[tuple[str,Any,Any,tuple[str,...]]] = [
        ('connections',GuardConnection,GuardConnection.user_id==uid,('chat_id','history','updated_at')),
        ('member_observations',GuardMember,GuardMember.user_id==uid,('chat_id','username','first_name','last_seen','verified')),
        ('federation_observations',GuardFedObservation,GuardFedObservation.user_id==uid,('chat_id','username','first_name','last_seen')),
        ('warnings_subject',GuardWarn,GuardWarn.user_id==uid,('id','chat_id','reason','by_id','created_at','expires_at')),
        ('approvals_subject',GuardApproval,GuardApproval.user_id==uid,('chat_id','reason','by_id','created_at')),
        ('restrictions_subject',GuardRestriction,GuardRestriction.user_id==uid,('chat_id','source','mode','state','generation','until')),
        ('verification_status',GuardChallenge,GuardChallenge.user_id==uid,('chat_id','status','mode','deadline','created_at')),
        ('federations_owned',GuardFederation,GuardFederation.owner_id==uid,('id','name','reason_required','notifications','created_at')),
        ('federation_roles',GuardFedAdmin,GuardFedAdmin.user_id==uid,('fed_id','by_id','created_at')),
        ('federation_bans_subject',GuardFedBan,GuardFedBan.user_id==uid,('fed_id','active','version','reason','by_id','created_at','updated_at')),
        ('federation_actions',GuardFedBan,GuardFedBan.by_id==uid,('fed_id','user_id','active','version','reason','created_at','updated_at')),
        ('owned_group_campaigns',GuardBroadcast,GuardBroadcast.author_id==uid,('id','status','created_at','updated_at')),
        ('queued_security_work',GuardJob,GuardJob.user_id==uid,('kind','chat_id','status','generation','run_at','error_code')),
        ('update_receipts',GuardInbox,owned_update(uid),('update_id','event_type','status','created_at','error_code')),
        # The shared global User row is outside this bot's erasure scope. These
        # platform records belong to this exact bot/user and must be visible too.
        ('platform_membership',BotUser,BotUser.user_id==uid,('lang','is_banned','ban_reason','blocked_bot',
            'vip_until','vip_notice','vip_notice_for','referred_by','referral_count','referral_qualified',
            'actions_count','prefs','started_at','last_seen')),
        ('own_payments',Payment,Payment.user_id==uid,('id','plan_id','stars','days','status','created_at','refunded_at')),
        ('own_entitlement_ledger',VipGrant,VipGrant.user_id==uid,('id','days','source','payment_id','actor_id','created_at')),
        ('owned_instance',ChildBot,ChildBot.owner_id==uid,('factory_bot_id','template','username','title','status',
            'branding','public','description','created_at','updated_at')),
        ('authored_audit_metadata',AdminAuditLog,AdminAuditLog.admin_id==uid,('id','action','target','created_at')),
    ]
    index,after = 0,[]
    if cursor:
        try:
            if len(cursor)>1024:
                raise ValueError('cursor')
            index,after=json.loads(base64.urlsafe_b64decode(cursor.encode()))
            if type(index) is not int or not 0<=index<len(scope) or not isinstance(after,list):
                raise ValueError('cursor')
        except (ValueError,TypeError) as error:
            raise PrivacyError('cursor') from error
    sections: dict[str,list[dict]] = {}
    total,next_cursor = 0,''
    async with ctx.sm() as session:
        for i in range(index,len(scope)):
            title,model,own,fields=scope[i]
            primary=list(inspect(model).primary_key)
            statement=select(model).where(model.bot_id==ctx.bot_id,own).order_by(*primary)
            if i==index and after:
                if len(after)!=len(primary) or any(type(v) is not column.type.python_type
                        for column,v in zip(primary,after,strict=True)):
                    raise PrivacyError('cursor')
                statement=statement.where(tuple_(*primary)>tuple(after))
            values=list((await session.execute(statement.limit(PAGE-total+1))).scalars())
            shown=values[:PAGE-total]
            sections[title]=[{field:serial(getattr(row,field)) for field in fields} for row in shown]
            total+=len(shown)
            if len(values)>len(shown):
                last=shown[-1] if shown else None
                position=[getattr(last,str(column.key)) for column in primary] if last else []
                next_cursor=base64.urlsafe_b64encode(json.dumps([i,position]).encode()).decode()
                break
            if total==PAGE and i+1<len(scope):
                next_cursor=base64.urlsafe_b64encode(json.dumps([i+1,[]]).encode()).decode()
                break
    body = json.dumps(dict(schema='groupguard.privacy',version=1,bot_id=ctx.bot_id,user_id=uid,
        generated_at=utcnow().isoformat(),data=sections,next_cursor=next_cursor,
        retained_policy='Active security/ownership/order/audit identifiers stay; global core profile is shared and not deleted by this bot.',
        omitted='Other humans private content, authentication/token material, issued challenge answers and raw uploads are excluded.'),
        ensure_ascii=False).encode()
    if len(body)>MAX_BYTES:
        raise PrivacyError('limit')
    return body


async def erase(ctx: BotContext, actor: Actor) -> dict[str,int]:
    uid = await requester(ctx,actor)
    counts: dict[str,int] = {}
    cutoff=time.time()
    # No global core User delete/cascade. Only this module's bot/user convenience data.
    async with ctx.extras['guard'].member_session(0,uid) as (session,_member):
        await requester(ctx,actor,session)
        for title,model,where in [
            ('connections',GuardConnection,GuardConnection.user_id==uid),
        ]:
            counts[title] = affected(await session.execute(delete(model).where(model.bot_id==ctx.bot_id,where)))
        chats = list((await session.execute(select(GuardFedObservation.chat_id).where(
            GuardFedObservation.bot_id==ctx.bot_id,GuardFedObservation.user_id==uid))).scalars())
        usernames = list((await session.execute(select(GuardMember.username).where(
            GuardMember.bot_id==ctx.bot_id,GuardMember.user_id==uid))).scalars())
        generation=uuid.uuid4().hex
        for offset in range(0,max(len(chats),len(usernames),1),PAGE):
            await durable.enqueue(ctx,'privacy_cache',0,user_id=uid,
                dedupe_key=f'privacy:{uid}:{generation}:{offset}',
                payload=dict(cutoff=cutoff,chats=chats[offset:offset+PAGE],usernames=usernames[offset:offset+PAGE]),session=session)
        counts['federation_profiles'] = affected(await session.execute(update(GuardFedObservation).where(
            GuardFedObservation.bot_id==ctx.bot_id,GuardFedObservation.user_id==uid).values(username=None,first_name=None)))
        counts['member_profiles'] = affected(await session.execute(update(GuardMember).where(
            GuardMember.bot_id==ctx.bot_id,GuardMember.user_id==uid).values(username=None,first_name=None)))
        counts['ban_profiles'] = affected(await session.execute(update(GuardFedBan).where(
            GuardFedBan.bot_id==ctx.bot_id,GuardFedBan.user_id==uid).values(username=None,first_name=None)))
        # Inactive tombstone versions are still necessary while old outbox work can exist.
        counts['inactive_ban_reasons'] = affected(await session.execute(update(GuardFedBan).where(
            GuardFedBan.bot_id==ctx.bot_id,GuardFedBan.user_id==uid,GuardFedBan.active.is_(False))
            .values(reason=None)))
        counts['inactive_challenges'] = affected(await session.execute(delete(GuardChallenge).where(
            GuardChallenge.bot_id==ctx.bot_id,GuardChallenge.user_id==uid,
            GuardChallenge.status.in_({'verified','failed','cancelled','expired'}))))
        counts['completed_update_content']=affected(await session.execute(update(GuardInbox).where(
            GuardInbox.bot_id==ctx.bot_id,GuardInbox.status=='completed',owned_update(uid)).values(payload={})))
        # Keep security job identity/order and uncertain dispatch evidence, but omit convenience names.
        job_after=''
        while True:
            rows=list((await session.execute(select(GuardJob).where(GuardJob.bot_id==ctx.bot_id,
                GuardJob.user_id==uid,GuardJob.id>job_after).order_by(GuardJob.id).limit(PAGE))).scalars())
            if not rows:
                break
            for row in rows:
                row.payload={key:('' if key in {'name','first_name','username'} else value)
                    for key,value in row.payload.items()}
            job_after=rows[-1].id
        # Personal campaign content can be removed only from terminal work, not unknown/in-flight delivery.
        terminal = {'completed','cancelled'}
        counts['terminal_campaigns'] = affected(await session.execute(update(GuardBroadcast).where(
            GuardBroadcast.bot_id==ctx.bot_id,GuardBroadcast.author_id==uid,GuardBroadcast.status.in_(terminal))
            .values(content={},subject={'id':uid,'is_bot':False,'first_name':''})))
    try:
        await clear_cache(ctx,uid,chats,usernames,cutoff)
    except RedisError as error:
        raise PrivacyError("cache_pending") from error
    return counts


async def clear_cache(ctx: BotContext, uid: int, chats: list[int], usernames: list[str | None], cutoff: float) -> None:
    # Remove only exact owned cache scopes after collecting actual observation usernames.
    # The newcomer timestamp is a minimal active security record; its existing expiry stays.
    keys = [ctx.keys('privacy_access',uid)]
    for username in {name for name in usernames if name}:
        key = ctx.keys('uname',username.lower())
        raw = await ctx.redis.get(key)
        try:
            cached = json.loads(raw) if raw else None
            mapped = cached.get('id') if isinstance(cached,dict) else cached
            if mapped == uid:
                keys.append(key)
        except (ValueError,TypeError):
            pass
    if keys:
        await ctx.redis.delete(*keys)
    # Personal imported files and confirmation payloads expire, but deletion removes them immediately.
    patterns=[ctx.keys('gg','data_confirm',uid,'*')]
    for pattern in patterns:
        cursor=0
        while True:
            cursor,owned=await ctx.redis.scan(cursor,match=pattern,count=100)
            for key in owned:
                raw=await ctx.redis.get(key)
                try:
                    state=json.loads(raw) if raw else {}
                except (ValueError,TypeError):
                    state={}
                if not isinstance(state,dict) or state.get('created',0)<=cutoff:
                    from bots.groupguard.reviews import CLAIM
                    if raw is not None:
                        await ctx.redis.execute_command('EVAL',CLAIM,1,key,raw)
            if cursor==0:
                break
    for category,part in [('connection_link',''),('fed_confirm',''),('gg','review'),
            ('gg','panel'),('gg','data'),('gg','fed')]:
        pattern=ctx.keys(category,part,'*') if part else ctx.keys(category,'*')
        cursor=0
        while True:
            cursor,candidates=await ctx.redis.scan(cursor,match=pattern,count=100)
            for key in candidates:
                raw=await ctx.redis.get(key)
                try:
                    state=json.loads(raw) if raw else {}
                    if (isinstance(state,dict) and uid in (state.get('owner_id'),state.get('user_id'))
                            and state.get('created',0)<=cutoff):
                        # Compare-and-delete does not remove a replacement owned by another actor.
                        from bots.groupguard.reviews import CLAIM
                        await ctx.redis.execute_command('EVAL',CLAIM,1,key,raw)
                except (ValueError,TypeError):
                    pass
            if cursor==0:
                break


async def run_cache(ctx: BotContext, job: GuardJob):
    from bots.groupguard.contracts import StepResult, result_of
    try:
        await clear_cache(ctx,job.user_id or 0,job.payload.get('chats',[]),job.payload.get('usernames',[]),float(job.payload.get('cutoff',0)))
    except RedisError:
        # Internal deletion is idempotent. An unavailable cache cannot exhaust an external RPC budget.
        await durable.defer(ctx,job,30,'privacy_cache_unavailable')
        return result_of(StepResult('privacy_cache','skipped','privacy_cache_pending'))
    async with ctx.sm() as session:
        await session.execute(update(GuardJob).where(GuardJob.bot_id==ctx.bot_id,GuardJob.id==job.id,
            GuardJob.status=='running',GuardJob.lease_owner==job.lease_owner).values(payload={}))
        await session.commit()
    return result_of(StepResult('privacy_cache','applied'))
