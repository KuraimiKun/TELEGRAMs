"""Real Group Guard standalone/two-child routes and selected data lifecycle behavior."""
import json

import pytest
from aiogram.types import File
from sqlalchemy import select

from bots.groupguard import portability, privacy
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.contracts import Actor
from bots.groupguard.models import (
    GuardConnection,
    GuardFedObservation,
    GuardMember,
    GuardRestriction,
)
from tests.bots.groupguard.test_groupguard import ADMIN, GROUP, MEMBER, bound_callback, gctx, group_msg
from tests.bots.groupguard.test_phase01a import env, send
from tests.bots.groupguard.test_phase03 import pm

__all__=['env','gctx']
OTHER=GROUP-1


@pytest.mark.parametrize('family',tuple(portability.MODULES))
async def test_actual_selected_module_roundtrip_and_omission(env,api,family):
    svc=env.extras['guard']
    await svc.ensure_chat(OTHER,'Destination')
    actor=Actor(env.bot_id,GROUP,'human',ADMIN)
    await svc.update_config(GROUP,rules='Source <b>rules</b>',welcome_text='Hello {mention}',night=False,
        extra_extension={'version':1,'meaning':'opaque'})
    await svc.save_item(GROUP,'note','legacy broad name',text='Source note',media_kind=None,file_id=None,limit=150)
    await svc.save_item(GROUP,'filter','word',text='Source filter',media_kind=None,file_id=None,limit=150)
    await svc.update_config(OTHER,rules='Keep destination rules',extra_destination={'owned':True},flood_count=0)
    await svc.save_item(OTHER,'note','keep',text='Destination note',media_kind=None,file_id=None,limit=150)
    selected=frozenset({family})
    body=await portability.export(env,actor,GROUP,selected)
    document=portability.parse(body,selected)
    assert document.source_bot_id==env.bot_id and family in document.modules
    before=await svc.config(OTHER,fresh=True)
    await portability.apply(env,actor,portability.Intent(OTHER,selected,body,before._revision))
    after=await svc.config(OTHER,fresh=True)
    expected=ChatConfig().model_dump()
    source=await svc.config(GROUP,fresh=True)
    for field in portability.MODULES[family]:
        assert getattr(after,field)==getattr(source,field)
    assert after.model_extra['extra_destination']=={'owned':True}
    if family!='rules':
        assert after.rules==before.rules
    notes=await svc.list_items(OTHER,'note')
    assert [row.key for row in notes]==(['legacy broad name'] if family=='notes' else ['keep'])
    for sibling in env.extras['test_contexts']:
        if sibling.bot_id!=env.bot_id:
            assert not await sibling.extras['guard'].list_items(OTHER,'note')
    await portability.apply(env,actor,portability.Intent(OTHER,selected,None,after._revision,True))
    reset=await svc.config(OTHER,fresh=True)
    for field in portability.MODULES[family]:
        assert getattr(reset,field)==expected[field]
    if family!='extensions':
        assert reset.model_extra['extra_destination']=={'owned':True}


async def test_bad_import_does_not_change_data_and_limits_media_rights(env,api):
    actor=Actor(env.bot_id,GROUP,'human',ADMIN)
    svc=env.extras['guard']
    original=await portability.export(env,actor,GROUP,frozenset({'notes'}))
    document=json.loads(original)
    document['items']=[dict(kind='note',key='test',text='Hi',format='html',media_kind='photo',file_id='photo')]
    document['source_bot_id']=env.bot_id+1
    cfg=await svc.config(GROUP,fresh=True)
    with pytest.raises(portability.PortableError,match='media'):
        await portability.apply(env,actor,portability.Intent(GROUP,frozenset({'notes'}),json.dumps(document).encode(),cfg._revision))
    assert not await svc.list_items(GROUP,'note')
    with pytest.raises(portability.PortableError,match='authority'):
        await portability.apply(env,Actor(env.bot_id,GROUP,'human',MEMBER),
            portability.Intent(GROUP,frozenset({'notes'}),original,cfg._revision))
    document['version']=99
    with pytest.raises(portability.PortableError,match='version'):
        portability.parse(json.dumps(document).encode(),frozenset({'notes'}))
    document['version']=1
    document['source_bot_id']=env.bot_id
    api.responses['GetFile']=File(file_id='photo',file_unique_id='u',file_path='photo',file_size=100)
    document['items'][0]['options']={'private':'false'}
    with pytest.raises(portability.PortableError,match='item'):
        portability.parse(json.dumps(document).encode(),frozenset({'notes'}))
    assert (await svc.config(GROUP,fresh=True))._revision==cfg._revision


async def test_personal_reset_card_replay_wrong_actor_and_stale_revision(env,api):
    svc=env.extras['guard']
    await svc.update_config(GROUP,rules='Original')
    await send(env,group_msg('/reset rules',ADMIN))
    request=next(m for m in reversed(api.calls('SendMessage')) if m.chat_id==ADMIN and m.reply_markup)
    card=next(m for m in reversed(api.messages) if m.chat.id==ADMIN and m.text==request.text)
    button=request.reply_markup.inline_keyboard[0][0]
    wrong=bound_callback(button.callback_data,card,MEMBER)
    await send(env,wrong)
    assert (await svc.config(GROUP,fresh=True)).rules=='Original'
    await send(env,bound_callback(button.callback_data,card,ADMIN))
    assert (await svc.config(GROUP,fresh=True)).rules==''
    await svc.update_config(GROUP,rules='New')
    await send(env,bound_callback(button.callback_data,card,ADMIN))
    assert (await svc.config(GROUP,fresh=True)).rules=='New'
    await env.redis.delete(env.keys('gg','portability','rate',GROUP))
    await send(env,group_msg('/reset rules',ADMIN))
    request=next(m for m in reversed(api.calls('SendMessage')) if m.chat_id==ADMIN and m.reply_markup)
    card=next(m for m in reversed(api.messages) if m.chat.id==ADMIN and m.text==request.text)
    await svc.update_config(GROUP,rules='Changed after preview')
    await send(env,bound_callback(request.reply_markup.inline_keyboard[0][0].callback_data,card,ADMIN))
    assert (await svc.config(GROUP,fresh=True)).rules=='Changed after preview'


async def test_own_privacy_isolation_pagination_and_active_security_retention(env,api):
    async with env.sm() as session:
        session.add(GuardConnection(bot_id=env.bot_id,user_id=MEMBER,chat_id=GROUP,history=[GROUP]))
        session.add(GuardRestriction(bot_id=env.bot_id,chat_id=GROUP,user_id=MEMBER,source='manual',mode='ban',state='applied',generation='retain'))
        for uid in range(1000,1201):
            session.add(GuardMember(bot_id=env.bot_id,chat_id=-uid,user_id=MEMBER,first_name='Own name',username='own'))
        session.add(GuardMember(bot_id=env.bot_id,chat_id=GROUP,user_id=ADMIN,first_name='Other name',username='other'))
        session.add(GuardFedObservation(bot_id=env.bot_id,chat_id=GROUP,user_id=MEMBER,first_name='Own name',username='own'))
        await session.commit()
    await env.redis.set(env.keys('uname','own'),json.dumps({'id':MEMBER}))
    await env.redis.set(env.keys('uname','other'),json.dumps({'id':ADMIN}))
    actor=Actor(env.bot_id,MEMBER,'human',MEMBER)
    page=json.loads(await privacy.inventory(env,actor))
    assert page['next_cursor'] and len(page['data']['member_observations'])==199
    second=json.loads(await privacy.inventory(env,actor,page['next_cursor']))
    assert len(second['data']['member_observations'])==2
    assert 'Other name' not in json.dumps(page)+json.dumps(second)
    await privacy.erase(env,actor)
    async with env.sm() as session:
        assert await session.get(GuardConnection,(env.bot_id,MEMBER)) is None
        assert (await session.get(GuardRestriction,(env.bot_id,GROUP,MEMBER,'manual'))).state=='applied'
        assert (await session.get(GuardMember,(env.bot_id,GROUP,ADMIN))).first_name=='Other name'
        names=(await session.execute(select(GuardMember.first_name).where(GuardMember.bot_id==env.bot_id,GuardMember.user_id==MEMBER))).scalars().all()
        assert not any(names)
    assert await env.redis.get(env.keys('uname','own')) is None
    assert await env.redis.get(env.keys('uname','other')) is not None
    with pytest.raises(privacy.PrivacyError,match='private'):
        await privacy.inventory(env,Actor(env.bot_id,GROUP,'human',MEMBER))
    await send(env,pm('/privacy policy',MEMBER))
    assert 'Your data' in api.calls('SendMessage')[-1].text


async def test_group_and_connected_language_help_and_rendered_aliases(env,api):
    await send(env,group_msg('/setlang ar',ADMIN))
    assert (await env.extras['guard'].config(GROUP,fresh=True)).lang=='ar'
    await send(env,pm('/connect '+str(GROUP),ADMIN))
    await send(env,pm('/setlang en',ADMIN))
    assert (await env.extras['guard'].config(GROUP,fresh=True)).lang=='en'
    await send(env,group_msg('/help moderation',MEMBER))
    assert '/tban' in api.calls('SendMessage')[-1].text
    await send(env,pm('/help portability',ADMIN))
    assert '2MiB' in api.calls('SendMessage')[-1].text


async def test_import_actual_document_getfile_confirmation_and_selected_repeat_reset(env,api):
    from aiogram.types import Document

    from bots.groupguard import durable
    from bots.groupguard.models import GuardItem, GuardJob, GuardRepeat
    actor=Actor(env.bot_id,GROUP,'human',ADMIN)
    svc=env.extras['guard']
    await send(env,group_msg('/save scheduled Hello {repeat 1m}',ADMIN))
    note=await svc.get_item(GROUP,'note','scheduled')
    assert note is not None
    async with env.sm() as session:
        cadence=await session.get(GuardRepeat,(env.bot_id,GROUP,note.id))
        assert cadence is not None
    jid=await durable.enqueue(env,'repeat_note',GROUP,dedupe_key='phase11-old-repeat',generation=cadence.generation,
        payload={'item_id':note.id})
    body=await portability.export(env,actor,GROUP,frozenset({'rules'}))
    actual_get=api.responses.get('GetFile')
    api.responses['GetFile']=File(file_id='export',file_unique_id='file',file_path='export',file_size=len(body))
    original_download=env.bot.download_file
    async def download(path,destination,**kwargs):
        assert path=='export'
        destination.write(body)
        return destination
    env.bot.download_file=download
    original=group_msg('document',ADMIN).message.model_copy(update={'document':Document(
        file_id='export',file_unique_id='file',file_name='groupguard.json',file_size=len(body))})
    await send(env,group_msg('/import rules',ADMIN,reply_to=original))
    request=next(m for m in reversed(api.calls('SendMessage')) if m.chat_id==ADMIN and m.reply_markup)
    card=next(m for m in reversed(api.messages) if m.chat.id==ADMIN and m.text==request.text)
    await send(env,bound_callback(request.reply_markup.inline_keyboard[0][0].callback_data,card,ADMIN))
    async with env.sm() as session:
        assert await session.get(GuardRepeat,(env.bot_id,GROUP,note.id)) is not None
        assert (await session.get(GuardJob,jid)).status=='pending'
    cfg=await svc.config(GROUP,fresh=True)
    await portability.apply(env,actor,portability.Intent(GROUP,frozenset({'notes'}),None,cfg._revision,True))
    async with env.sm() as session:
        assert await session.get(GuardRepeat,(env.bot_id,GROUP,note.id)) is None
        assert (await session.get(GuardJob,jid)).status=='cancelled'
        assert await session.get(GuardItem,note.id) is None
    assert api.calls('GetFile')
    env.bot.download_file=original_download
    if actual_get is not None:
        api.responses['GetFile']=actual_get


async def test_privacy_terminal_payload_live_job_and_personal_tokens(env,api):
    from bots.groupguard import durable
    from bots.groupguard.models import GuardInbox, GuardJob
    from core.db.base import utcnow
    actor=Actor(env.bot_id,MEMBER,'human',MEMBER)
    own={'message':{'from_user':{'id':MEMBER,'first_name':'Private name'},'text':'Old private content'}}
    other={'message':{'from_user':{'id':ADMIN},'text':'Other content'}}
    async with env.sm() as session:
        session.add(GuardInbox(bot_id=env.bot_id,update_id=9911,event_type='message',payload=own,status='completed',created_at=utcnow()))
        session.add(GuardInbox(bot_id=env.bot_id,update_id=9912,event_type='message',payload=other,status='uncertain',created_at=utcnow()))
        await session.commit()
    jid=await durable.enqueue(env,'warning_threshold',GROUP,user_id=MEMBER,dedupe_key='privacy-live',
        payload={'name':'Private name','limit':3,'by_id':ADMIN,'action':'ban','reason':'Active reason'})
    mine=env.keys('gg','data_confirm',MEMBER,'nonce')
    theirs=env.keys('gg','data_confirm',ADMIN,'nonce')
    await env.redis.set(mine,'private uploaded file')
    await env.redis.set(theirs,'other uploaded file')
    await privacy.erase(env,actor)
    async with env.sm() as session:
        assert (await session.get(GuardInbox,(env.bot_id,9911))).payload=={}
        assert (await session.get(GuardInbox,(env.bot_id,9912))).payload==other
        job=await session.get(GuardJob,jid)
        assert job.status=='pending' and job.payload['name']=='' and job.payload['reason']=='Active reason'
    assert await env.redis.get(mine) is None and await env.redis.get(theirs) is not None
    await send(env,pm('/privacy delete',MEMBER))
    request=next(m for m in reversed(api.calls('SendMessage')) if m.chat_id==MEMBER and m.reply_markup)
    card=next(m for m in reversed(api.messages) if m.chat.id==MEMBER and m.text==request.text)
    await send(env,bound_callback(request.reply_markup.inline_keyboard[0][0].callback_data,card,MEMBER))
    assert 'Optional personal data removed' in api.calls('EditMessageText')[-1].text


def test_help_escape_registry_mapping_and_native_locale_resolution():
    from pathlib import Path

    from bots.groupguard import help as discovery
    from bots.groupguard.command_metadata import REGISTRY
    from core.i18n import Translator
    translator=Translator(Path('bots/groupguard/locales'))
    assert translator.resolve('id')=='id'
    assert translator.resolve('en_PT')=='en-pt'
    assert 'catatan' in translator.get('id','gg-notes-list').lower()
    t=translator.bind('en')
    text,_=discovery.render(t,'<unsafe>')
    assert '<unsafe>' not in text and '&lt;unsafe&gt;' in text
    covered=set()
    for family in discovery.FAMILIES:
        names=[meta.name for meta in REGISTRY.values() if meta.module==family]
        for page in range((len(names)+discovery.PAGE-1)//discovery.PAGE):
            text,kb=discovery.render(t,family,page)
            assert len(text)<4096 and not text.startswith('gg-help-family-')
            for name in names[page*discovery.PAGE:(page+1)*discovery.PAGE]:
                assert '/'+name+' — ' in text
                covered.add(name)
            assert all(len(button.callback_data.encode())<=64 for row in kb.inline_keyboard for button in row)
    assert covered==set(REGISTRY)


def test_authored_locale_help_pages_and_shared_platform_contracts():
    from pathlib import Path

    from bots.groupguard import help as discovery
    from bots.groupguard import pagination
    from bots.groupguard.command_metadata import REGISTRY
    from core.i18n import Translator
    from tests.test_locales import ftl_messages

    base=Path('bots/groupguard/locales')
    translator=Translator(base)
    core_reference=ftl_messages(Path('core/locales/en/core.ftl'))
    for folder in sorted(base.iterdir()):
        if not (folder/'messages.ftl').exists():
            continue
        code=folder.name
        assert translator.resolve(code.upper().replace('-','_'))==code
        t=translator.bind(code)
        for family in discovery.FAMILIES:
            names=[item for item in REGISTRY.values() if item.module==family]
            for page in range((len(names)+discovery.PAGE-1)//discovery.PAGE):
                body,kb=discovery.render(t,family,page)
                assert pagination.units(body)<=4096,(code,family,page)
                assert not body.startswith('gg-help-family-')
                assert all(len(button.callback_data.encode())<=64 for row in kb.inline_keyboard for button in row)
        platform=folder/'platform.ftl'
        if platform.exists():
            translated=ftl_messages(platform)
            # Partial shared bundles are still being expanded. Every authored override
            # already has the exact core variable contract; full parity is a later gate.
            assert set(translated)<=set(core_reference)
            for key,variables in translated.items():
                assert variables==core_reference[key],(code,key)
                result=t(key,**{var:'<example>' for var in variables})
                assert '\ue000' not in result and '\ue001' not in result
                assert result!=key
        for key in ('gg-data-confirm','gg-data-error-authority','gg-privacy-policy','gg-review-request'):
            variables=ftl_messages(folder/'messages.ftl')[key]
            result=t(key,**{var:'42' for var in variables})
            assert pagination.units(result)<=4096,(code,key)


async def test_privacy_cache_outage_recovers_without_erasing_newcomer_security(env,monkeypatch):
    from redis.exceptions import ConnectionError

    from bots.groupguard import durable
    from bots.groupguard.models import GuardJob
    async with env.sm() as session:
        session.add(GuardMember(bot_id=env.bot_id,chat_id=GROUP,user_id=MEMBER,first_name='Old',username='oldname'))
        await session.commit()
    timestamp=env.keys('newbie',GROUP,MEMBER)
    await env.redis.set(timestamp,'security-timestamp',ex=3600)
    await env.redis.set(env.keys('uname','oldname'),json.dumps({'id':MEMBER}))
    original=env.redis.delete
    async def unavailable(*args,**kwargs):
        raise ConnectionError('test cache outage')
    monkeypatch.setattr(env.redis,'delete',unavailable)
    with pytest.raises(privacy.PrivacyError,match='cache_pending'):
        await privacy.erase(env,Actor(env.bot_id,MEMBER,'human',MEMBER))
    async with env.sm() as session:
        assert (await session.get(GuardMember,(env.bot_id,GROUP,MEMBER))).first_name is None
        pending=list((await session.execute(select(GuardJob.id).where(GuardJob.bot_id==env.bot_id,
            GuardJob.kind=='privacy_cache',GuardJob.user_id==MEMBER,GuardJob.status=='pending'))).scalars())
        assert pending
    monkeypatch.setattr(env.redis,'delete',original)
    import time
    later=env.keys('gg','data_confirm',MEMBER,'later')
    await env.redis.set(later,json.dumps({'user_id':MEMBER,'created':time.time()+1,'body':'new file'}))
    for jid in pending:
        job=await durable.claim(env,jid)
        assert job is not None
        result=await env.extras['guard_job_handlers']['privacy_cache'](env,job)
        assert result.primary_completed
        await durable.finish(env,job,result)
    assert await env.redis.get(env.keys('uname','oldname')) is None
    assert await env.redis.get(timestamp) is not None and await env.redis.ttl(timestamp)>0
    assert await env.redis.get(later) is not None
    for sibling in env.extras['test_contexts']:
        if sibling.bot_id!=env.bot_id:
            assert await sibling.redis.get(sibling.keys('uname','oldname')) is None


async def test_public_federation_reads_eligible_bot_own_anonymous_no_mutator_role(env,api):
    from aiogram.types import Chat, ChatMemberMember

    from bots.groupguard import federations
    from bots.groupguard.models import GuardFedBan
    from tests.conftest import tg_user
    owner=Actor(env.bot_id,ADMIN,'human',ADMIN)
    fed=await federations.create(env,owner,'Public source')
    await federations.membership(env,Actor(env.bot_id,GROUP,'human',ADMIN),fed.id)
    await env.extras['guard'].update_config(GROUP,bot2bot_mode='all',anonadmin=False)
    original=api.responses['GetChatMember']
    sender=91919
    api.responses['GetChatMember']=lambda m: ChatMemberMember(user=tg_user(sender).model_copy(update={'is_bot':True})) if m.user_id==sender else original(m)
    bot=group_msg('/fedinfo',sender)
    bot=bot.model_copy(update={'message':bot.message.model_copy(update={'from_user':tg_user(sender).model_copy(update={'is_bot':True})})})
    await send(env,bot)
    assert fed.id in api.calls('SendMessage')[-1].text
    anon=group_msg('/fedadmins',MEMBER,sender_chat=Chat(id=GROUP,type='supergroup'))
    await send(env,anon)
    assert str(ADMIN) in api.calls('SendMessage')[-1].text
    attempt=group_msg('/fban 42 Cannot acquire federation role',sender)
    attempt=attempt.model_copy(update={'message':attempt.message.model_copy(update={'from_user':tg_user(sender).model_copy(update={'is_bot':True})})})
    await send(env,attempt)
    async with env.sm() as session:
        assert await session.get(GuardFedBan,(env.bot_id,fed.id,42)) is None
    await env.extras['guard'].update_config(GROUP,bot2bot_mode='off')
    before=len(api.calls('SendMessage'))
    await send(env,bot.model_copy(update={'update_id':bot.update_id+991,'message':bot.message.model_copy(update={'message_id':bot.message.message_id+991})}))
    assert len(api.calls('SendMessage'))==before


async def test_personal_federation_notice_and_confirmation_follow_owner_language(env,api):
    from bots.groupguard import federations
    await send(env,pm('/newfed Native owner',ADMIN))
    fed=await federations.owned(env,ADMIN)
    await env.users.set_lang(ADMIN,'id')
    await send(env,pm('/renamefed Nama baru',ADMIN))
    assert any('Federasi' in request.text and 'nama diubah' in request.text for request in api.calls('SendMessage'))
    await send(env,pm('/delfed',ADMIN))
    confirmation=next(request for request in reversed(api.calls('SendMessage')) if request.reply_markup)
    assert 'Konfirmasi dalam lima menit' in confirmation.text
    await send(env,pm('/info',ADMIN))
    assert 'Nama:' in api.calls('SendMessage')[-1].text
    assert fed is not None


async def test_group_language_confirmation_and_private_settings_use_group_locale(env,api):
    await send(env,group_msg('/setlang fr',ADMIN))
    assert 'Langue de réponse' in api.calls('SendMessage')[-1].text
    await send(env,group_msg('/settings',ADMIN))
    personal=next(request for request in reversed(api.calls('SendMessage')) if request.chat_id==ADMIN and request.reply_markup)
    assert 'Paramètres' in personal.text
    assert any('Langue' in button.text for row in personal.reply_markup.inline_keyboard for button in row)


async def test_federation_lists_fit_utf16_and_reveal_all_sources_with_continuation(env,api,monkeypatch):
    import re
    import uuid

    from bots.groupguard import pagination
    from bots.groupguard.models import GuardFedAdmin, GuardFedBan, GuardFederation
    source_ids=[]
    async with env.sm() as session:
        for index in range(23):
            fid=str(uuid.uuid4())
            source_ids.append(fid)
            session.add(GuardFederation(bot_id=env.bot_id,id=fid,name='😀&<>'+str(index)+'😀'*55,owner_id=2000+index))
            await session.flush()
            session.add(GuardFedAdmin(bot_id=env.bot_id,fed_id=fid,user_id=ADMIN,by_id=2000+index))
            session.add(GuardFedBan(bot_id=env.bot_id,fed_id=fid,user_id=MEMBER,active=True,version=1,
                reason='Active reason',by_id=2000+index))
        await session.commit()
    original=env.translator.get
    def verbose(lang,key,**kwargs):
        value=original(lang,key,**kwargs)
        return ('Подробные сведения об источнике политики. '*5+value) if key=='gg-fed-stat-line' else value
    monkeypatch.setattr(env.translator,'get',verbose)
    seen=[]
    command='/fedstat '+str(MEMBER)
    for _page in range(10):
        await send(env,pm(command,ADMIN))
        body=api.calls('SendMessage')[-1].text
        assert pagination.units(body)<=4096
        found=re.findall(r'<code>([a-f0-9-]{36})</code>',body)
        assert found and not set(found)&set(seen)
        seen.extend(found)
        continuation=next((line for line in body.splitlines() if line.startswith('/fedstat ')),None)
        if continuation is None:
            break
        assert continuation.endswith(found[-1])
        command=continuation
    assert set(seen)==set(source_ids)
    seen=[]
    command='/myfeds'
    for _page in range(10):
        await send(env,pm(command,ADMIN))
        body=api.calls('SendMessage')[-1].text
        assert pagination.units(body)<=4096
        found=re.findall(r'<code>([a-f0-9-]{36})</code>',body)
        assert found and not set(found)&set(seen)
        seen.extend(found)
        continuation=next((line for line in body.splitlines() if line.startswith('/myfeds ')),None)
        if continuation is None:
            break
        assert continuation.endswith(found[-1])
        command=continuation
    assert set(seen)==set(source_ids)


def test_visible_telegram_length_keeps_literal_escaped_tags_and_supplementary_unicode():
    from bots.groupguard.pagination import units
    assert units('<b>😀</b> &lt;b&gt;&amp;')==2+1+3+1


async def test_quietfed_bot_default_review_replay_and_no_creator_authority(env,api):
    from bots.groupguard import federations
    from tests.bots.groupguard.test_phase08 import bot_admin, bot_command
    from tests.bots.groupguard.test_phase09 import make
    fed=await make(env)
    await send(env,group_msg('/joinfed '+fed.id,ADMIN))
    bot_admin(api)
    await send(env,bot_command('/quietfed on'))
    assert not (await federations.attached(env,GROUP)).quiet
    await send(env,group_msg('/bot2bot admin',ADMIN))
    await send(env,bot_command('/quietfed on'))
    assert not (await federations.attached(env,GROUP)).quiet
    request=next(m for m in reversed(api.calls('SendMessage')) if m.reply_markup)
    card=next(m for m in reversed(api.messages) if m.chat.id==GROUP and m.text==request.text)
    callback=request.reply_markup.inline_keyboard[0][0].callback_data
    assert 'gg-op-fed_quiet' not in request.text and fed.id in request.text
    await send(env,bound_callback(callback,card,MEMBER))
    assert not (await federations.attached(env,GROUP)).quiet
    for sibling in env.extras['test_contexts']:
        if sibling.bot_id!=env.bot_id:
            await send(sibling,bound_callback(callback,card,ADMIN))
            assert not (await federations.attached(env,GROUP)).quiet
    await send(env,bound_callback(callback,card,ADMIN))
    assert (await federations.attached(env,GROUP)).quiet
    await send(env,group_msg('/quietfed off',ADMIN))
    await send(env,bound_callback(callback,card,ADMIN))
    assert not (await federations.attached(env,GROUP)).quiet
    await send(env,group_msg('/bot2botskipreview on',ADMIN))
    await send(env,bot_command('/leavefed'))
    assert (await federations.attached(env,GROUP)).fed_id==fed.id
    # A distinct valid spelling exercises skip-review without being rejected as
    # the repeated bot command that was already reviewed earlier in this test.
    await send(env,bot_command('/quietfed yes'))
    assert (await federations.attached(env,GROUP)).quiet
    await send(env,bot_command('/delfed'))
    assert await federations.get(env,fed.id) is not None


async def test_quietfed_review_rechecks_sender_rights_and_attachment_generation(env,api):
    from bots.groupguard import federations
    from tests.bots.groupguard.test_phase01a import admin_member
    from tests.bots.groupguard.test_phase08 import bot_admin, bot_command
    from tests.bots.groupguard.test_phase09 import make
    fed=await make(env)
    await send(env,group_msg('/joinfed '+fed.id,ADMIN))
    bot_admin(api)
    await send(env,group_msg('/bot2bot admin',ADMIN))
    await send(env,bot_command('/quietfed on'))
    request=next(m for m in reversed(api.calls('SendMessage')) if m.reply_markup)
    card=next(m for m in reversed(api.messages) if m.chat.id==GROUP and m.text==request.text)
    callback=request.reply_markup.inline_keyboard[0][0].callback_data
    original=api.responses['GetChatMember']
    api.responses['GetChatMember']=lambda m: admin_member(88,can_change_info=False).model_copy(
        update={'user':original(m).user}) if m.user_id==88 else original(m)
    await send(env,bound_callback(callback,card,ADMIN))
    assert not (await federations.attached(env,GROUP)).quiet
    api.responses['GetChatMember']=original
    await send(env,group_msg('/leavefed',ADMIN))
    await send(env,group_msg('/joinfed '+fed.id,ADMIN))
    generation=(await federations.attached(env,GROUP)).generation
    await send(env,bound_callback(callback,card,ADMIN))
    row=await federations.attached(env,GROUP)
    assert not row.quiet and row.generation==generation
    await send(env,group_msg('/bot2botskipreview on',ADMIN))
    api.responses['GetChatMember']=lambda m: admin_member(88,can_change_info=False).model_copy(
        update={'user':original(m).user}) if m.user_id==88 else original(m)
    await send(env,bot_command('/quietfed true'))
    assert not (await federations.attached(env,GROUP)).quiet


async def test_reset_night_restores_only_owned_snapshot_and_failed_restore_keeps_config(env,api):
    from aiogram.exceptions import TelegramBadRequest
    from aiogram.methods import SetChatPermissions
    from aiogram.types import ChatPermissions

    from bots.groupguard import jobs
    from bots.groupguard.models import GuardNight
    from tests.bots.groupguard.test_phase07 import configure_night, track_permissions

    svc=env.extras['guard']
    actor=Actor(env.bot_id,GROUP,'human',ADMIN)
    current=track_permissions(api)
    cfg=await configure_night(env)
    assert (await jobs.apply_night(env,GROUP,cfg)).primary_completed
    cfg=await svc.config(GROUP,fresh=True)
    api.responses['SetChatPermissions']=TelegramBadRequest(
        method=SetChatPermissions(chat_id=GROUP,permissions=ChatPermissions(can_send_messages=True)),message='restore denied')
    with pytest.raises(portability.PortableError,match='restore'):
        await portability.apply(env,actor,portability.Intent(GROUP,frozenset({'night'}),None,cfg._revision,True))
    assert (await svc.config(GROUP,fresh=True)).night
    assert current[GROUP].can_send_messages is False
    async with env.sm() as session:
        assert (await session.get(GuardNight,(env.bot_id,GROUP))).status=='closed'
    def restore(method):
        current[method.chat_id]=method.permissions
        return True
    api.responses['SetChatPermissions']=restore
    await portability.apply(env,actor,portability.Intent(GROUP,frozenset({'night'}),None,cfg._revision,True))
    assert not (await svc.config(GROUP,fresh=True)).night
    assert current[GROUP].can_send_messages is True and current[GROUP].can_send_polls is False
    cfg=await configure_night(env)
    await jobs.apply_night(env,GROUP,cfg)
    changed=ChatPermissions(can_send_messages=True,can_send_polls=True)
    current[GROUP]=changed
    before=len(api.calls('SetChatPermissions'))
    cfg=await svc.config(GROUP,fresh=True)
    await portability.apply(env,actor,portability.Intent(GROUP,frozenset({'night'}),None,cfg._revision,True))
    assert len(api.calls('SetChatPermissions'))==before and current[GROUP]==changed


async def test_reset_captcha_failure_retains_issued_work_and_success_preserves_other_ban(env,api):
    from datetime import timedelta

    from aiogram.exceptions import TelegramBadRequest
    from aiogram.methods import RestrictChatMember
    from aiogram.types import ChatPermissions

    from bots.groupguard import durable
    from bots.groupguard.models import GuardChallenge, GuardJob
    from core.db.base import utcnow

    svc=env.extras['guard']
    actor=Actor(env.bot_id,GROUP,'human',ADMIN)
    generation='phase11capreset'
    async with env.sm() as session:
        session.add(GuardRestriction(bot_id=env.bot_id,chat_id=GROUP,user_id=MEMBER,
            source='captcha',mode='mute',state='applied',generation=generation))
        session.add(GuardChallenge(bot_id=env.bot_id,chat_id=GROUP,user_id=MEMBER,
            generation=generation,status='pending',message_id=100,message_chat_id=GROUP,mode='button',answer='ok',deadline=utcnow()+timedelta(minutes=2)))
        session.add(GuardRestriction(bot_id=env.bot_id,chat_id=GROUP,user_id=ADMIN+50,
            source='manual',mode='ban',state='applied',generation='manual-ban'))
        await session.commit()
    jid=await durable.enqueue(env,'captcha_expire',GROUP,user_id=MEMBER,generation=generation,dedupe_key='phase11-cap-reset',payload={})
    cfg=await svc.config(GROUP,fresh=True)
    api.responses['RestrictChatMember']=TelegramBadRequest(method=RestrictChatMember(
        chat_id=GROUP,user_id=MEMBER,permissions=ChatPermissions(can_send_messages=True)),message='restore denied')
    with pytest.raises(portability.PortableError,match='restore'):
        await portability.apply(env,actor,portability.Intent(GROUP,frozenset({'captcha'}),None,cfg._revision,True))
    async with env.sm() as session:
        assert (await session.get(GuardChallenge,(env.bot_id,GROUP,MEMBER))).status=='pending'
        assert (await session.get(GuardJob,jid)).status=='pending'
    api.responses['RestrictChatMember']=True
    await portability.apply(env,actor,portability.Intent(GROUP,frozenset({'captcha'}),None,cfg._revision,True))
    async with env.sm() as session:
        assert (await session.get(GuardChallenge,(env.bot_id,GROUP,MEMBER))).status=='cancelled'
        assert (await session.get(GuardJob,jid)).status=='cancelled'
        assert await session.get(GuardRestriction,(env.bot_id,GROUP,MEMBER,'captcha')) is None
        assert (await session.get(GuardRestriction,(env.bot_id,GROUP,ADMIN+50,'manual'))).state=='applied'
    assert not api.calls('UnbanChatMember')


async def test_privacy_includes_own_platform_records_without_payment_or_instance_secrets(env):
    import base64

    from core.db.models import BotUser, ChildBot, Payment, VipGrant

    await env.users.get_or_create(MEMBER,'own','Own','ta')
    await env.users.set_lang(MEMBER,'ta')
    await env.users.get_or_create(ADMIN,'other','Other','en')
    await env.users.set_lang(ADMIN,'en')
    async with env.sm() as session:
        own=await session.get(BotUser,(env.bot_id,MEMBER))
        own.prefs={'display':'optional'}
        session.add(Payment(bot_id=env.bot_id,user_id=MEMBER,stars=10,days=2,charge_id='DO-NOT-EXPORT-CHARGE'))
        session.add(Payment(bot_id=env.bot_id,user_id=ADMIN,stars=999,days=2,charge_id='OTHER-CHARGE'))
        session.add(VipGrant(bot_id=env.bot_id,user_id=MEMBER,days=2,source='payment'))
        child=await session.get(ChildBot,env.bot_id)
        if child is not None:
            child.owner_id=MEMBER
            child.token_enc='DO-NOT-EXPORT-TOKEN'
        await session.commit()
    actor=Actor(env.bot_id,MEMBER,'human',MEMBER)
    body=await privacy.inventory(env,actor)
    data=json.loads(body)['data']
    assert data['platform_membership'][0]['prefs']=={'display':'optional'}
    assert data['own_payments'][0]['stars']==10 and len(data['own_payments'])==1
    assert data['own_entitlement_ledger'][0]['days']==2
    assert b'DO-NOT-EXPORT' not in body and b'OTHER-CHARGE' not in body
    await privacy.erase(env,actor)
    async with env.sm() as session:
        assert (await session.get(BotUser,(env.bot_id,MEMBER))).prefs=={'display':'optional'}
        assert (await session.get(BotUser,(env.bot_id,ADMIN))).lang=='en'
        assert len(list((await session.execute(select(Payment).where(Payment.bot_id==env.bot_id,
            Payment.user_id==MEMBER))).scalars()))==1
    forged=base64.urlsafe_b64encode(json.dumps([0,['invalid-integer',MEMBER]]).encode()).decode()
    with pytest.raises(privacy.PrivacyError,match='cursor'):
        await privacy.inventory(env,actor,forged)


async def test_selected_raid_reset_retires_generation_job_and_keeps_real_bans(env,api):
    from bots.groupguard import raids
    from bots.groupguard.models import GuardJob

    svc=env.extras['guard']
    actor=Actor(env.bot_id,GROUP,'human',ADMIN)
    old=await raids.change(env,GROUP,600)
    async with env.sm() as session:
        session.add(GuardRestriction(bot_id=env.bot_id,chat_id=GROUP,user_id=MEMBER,
            source='raid',mode='ban',state='applied',generation=old.generation))
        await session.commit()
    cfg=await svc.config(GROUP,fresh=True)
    await portability.apply(env,actor,portability.Intent(GROUP,frozenset({'rules'}),None,cfg._revision,True))
    assert raids.active(await raids.state(env,GROUP))
    cfg=await svc.config(GROUP,fresh=True)
    await portability.apply(env,actor,portability.Intent(GROUP,frozenset({'raid'}),None,cfg._revision,True))
    final=await raids.state(env,GROUP)
    assert not raids.active(final) and final.generation!=old.generation
    async with env.sm() as session:
        job=(await session.execute(select(GuardJob).where(GuardJob.bot_id==env.bot_id,
            GuardJob.chat_id==GROUP,GuardJob.kind=='raid_expire',GuardJob.generation==old.generation))).scalar_one()
        assert job.status=='cancelled'
        assert (await session.get(GuardRestriction,(env.bot_id,GROUP,MEMBER,'raid'))).state=='applied'
    await raids.expire_job(env,job)
    assert (await raids.state(env,GROUP)).generation==final.generation
    assert not api.calls('UnbanChatMember')


async def test_nonempty_allowlist_roundtrip_enforces_links_and_rejects_bad_entries(env,api):
    from bots.groupguard import locks

    svc=env.extras['guard']
    actor=Actor(env.bot_id,GROUP,'human',ADMIN)
    entries=[locks.allow_entry(value) for value in ('example.org/public','https://t.me/+ValidInvite',
        '@samplechat','bot:samplebot','channel:samplechannel','inline:samplebot',
        'forward:samplechat','command:/help','stickerpack:Samples','emojipack:Samples')]
    await svc.update_config(GROUP,locks=['links'],allowlist=entries,cas=False,flood_count=0)
    body=await portability.export(env,actor,GROUP,frozenset({'locks'}))
    await svc.update_config(GROUP,locks=[],allowlist=[],rules='Unselected rules survive')
    cfg=await svc.config(GROUP,fresh=True)
    await portability.apply(env,actor,portability.Intent(GROUP,frozenset({'locks'}),body,cfg._revision))
    cfg=await svc.config(GROUP,fresh=True)
    assert cfg.allowlist==entries and cfg.rules=='Unselected rules survive' and cfg.locks==['links']
    before=len(api.calls('DeleteMessage'))
    await send(env,group_msg('https://example.org/public/safe',MEMBER))
    assert len(api.calls('DeleteMessage'))==before
    await send(env,group_msg('https://other.example/blocked',MEMBER))
    assert len(api.calls('DeleteMessage'))==before+1
    invalid=json.loads(body)
    for entry in ({'kind':'chat'}, {'kind':'url','host':''}, {'kind':'chat','value':'bad\x00name'},
            {'kind':'unknown','value':'x'}, {'kind':'chat','value':False}):
        invalid['modules']['locks']['allowlist']=[entry]
        with pytest.raises(portability.PortableError,match='field'):
            await portability.apply(env,actor,portability.Intent(GROUP,frozenset({'locks'}),json.dumps(invalid).encode(),cfg._revision))
        assert (await svc.config(GROUP,fresh=True)).allowlist==entries


async def test_info_reports_scoped_federation_sources_and_anonymous_id_is_real_chat(env,api):
    from aiogram.types import MessageOriginUser, User

    from bots.groupguard import fed_bans
    from tests.bots.groupguard.test_phase10 import network
    from tests.conftest import tg_user

    actor,fed=await network(env)
    await fed_bans.change(env,actor,fed.id,fed_bans.BanInput(30,'Status only'),active=True)
    forwarded=pm('Forwarded target',MEMBER).message
    forwarded=forwarded.model_copy(update={
        'forward_origin':MessageOriginUser(date=forwarded.date,sender_user=tg_user(30))})
    message=pm('/info',MEMBER)
    message=message.model_copy(update={'message':message.message.model_copy(update={'reply_to_message':forwarded})})
    before=len(api.calls('SendMessage'))
    await send(env,message)
    sent=api.calls('SendMessage')[before:]
    assert len(sent)==2 and '30' in sent[0].text and fed.id in sent[1].text
    assert 'Effect federation' in sent[1].text
    assert not api.calls('BanChatMember')
    for sibling in env.extras['test_contexts']:
        if sibling.bot_id==env.bot_id:
            continue
        before=len(api.calls('SendMessage'))
        message=pm('/info',MEMBER)
        await send(sibling,message.model_copy(update={'message':message.message.model_copy(update={'reply_to_message':forwarded})}))
        other=api.calls('SendMessage')[before:]
        assert len(other)==1 and fed.id not in other[0].text
    anon=group_msg('/id',MEMBER)
    anon=anon.model_copy(update={'message':anon.message.model_copy(update={
        'sender_chat':anon.message.chat,
        'from_user':User(id=1087968824,is_bot=True,first_name='Anonymous placeholder')})})
    await send(env,anon)
    actual=api.calls('SendMessage')[-1].text
    assert str(GROUP) in actual and '1087968824' not in actual


async def test_factory_record_token_identity_is_checked_before_runtime_or_pause_rpc(env,api):
    from core.db.models import ChildBot
    from core.factory.children import ChildService
    from core.factory.crypto import decrypt_token, encrypt_token

    own=f'{env.bot_id}:'+('A'*35)
    blob=encrypt_token(env.platform,own)
    assert decrypt_token(env.platform,blob,expected_bot_id=env.bot_id)==own
    assert decrypt_token(env.platform,blob,expected_bot_id=env.bot_id+1) is None
    malformed=encrypt_token(env.platform,f'{env.bot_id}:short')
    assert decrypt_token(env.platform,malformed,expected_bot_id=env.bot_id) is None
    if env.child is None:
        return
    sibling=next(ctx for ctx in env.extras['test_contexts'] if ctx.child is not None and ctx.bot_id!=env.bot_id)
    async with env.sm() as session:
        child=await session.get(ChildBot,env.bot_id)
        other=await session.get(ChildBot,sibling.bot_id)
        child.token_enc=other.token_enc
        await session.commit()
    registry=env.extras['test_registry']
    await registry.evict(env.bot_id)
    before=len(api.requests)
    assert await registry.get(env.bot_id) is None
    assert len(api.requests)==before
    service=ChildService(env.sm,env.redis,env.platform,factory_bot_id=123456,templates={'groupguard'},session=api)
    await service.pause(child)
    assert len(api.requests)==before
    async with env.sm() as session:
        paused=await session.get(ChildBot,env.bot_id)
        assert paused.status=='paused' and paused.last_error=='token_identity_or_decryption_unavailable'
        assert (await session.get(ChildBot,sibling.bot_id)).status=='active'
    assert not api.calls('DeleteWebhook') and not api.calls('SetChatPermissions')
