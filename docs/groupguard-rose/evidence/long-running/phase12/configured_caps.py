"""Supplemental review check for custom cap values; run this file explicitly."""
from tests.bots.groupguard.conftest import no_throttle
from tests.bots.groupguard.test_groupguard import ADMIN, GROUP, MEMBER, gctx, group_msg, plain
from tests.bots.groupguard.test_phase01a import env, send
from tests.conftest import api, redis, sm

__all__=['api', 'env', 'gctx', 'no_throttle', 'redis', 'sm']


async def test_configured_caps_have_real_positive_negative_effects_and_sibling_isolation(env,api):
    await env.settings.set('max_purge',2)
    await send(env,group_msg('/purgefrom',ADMIN,reply_to=plain(MEMBER).model_copy(update={'message_id':100})))
    await send(env,group_msg('/purgeto',ADMIN,reply_to=plain(MEMBER).model_copy(update={'message_id':102})))
    assert not api.calls('DeleteMessages')
    await env.settings.set('max_purge',3)
    await send(env,group_msg('/purgeto',ADMIN,reply_to=plain(MEMBER).model_copy(update={'message_id':102})))
    assert api.calls('DeleteMessages')[-1].message_ids==[100,101,102]
    await env.settings.set('max_blocklist',1)
    await send(env,group_msg('/addblocklist firstcap',ADMIN))
    await send(env,group_msg('/addblocklist secondcap',ADMIN))
    assert [row['key'] for row in (await env.extras['guard'].config(GROUP,fresh=True)).blocklist_entries]==['firstcap']
    await env.settings.set('max_blocklist',2)
    await send(env,group_msg('/addblocklist secondcap',ADMIN))
    assert len((await env.extras['guard'].config(GROUP,fresh=True)).blocklist_entries)==2
    await env.settings.set('max_items',1)
    await send(env,group_msg('/save capone First',ADMIN))
    await send(env,group_msg('/save captwo Second',ADMIN))
    assert [row.key for row in await env.extras['guard'].list_items(GROUP,'note')]==['capone']
    await env.settings.set('max_items',2)
    await send(env,group_msg('/save captwo Second',ADMIN))
    assert len(await env.extras['guard'].list_items(GROUP,'note'))==2
    for sibling in env.extras['test_contexts']:
        if sibling.bot_id!=env.bot_id:
            settings=await sibling.settings.get()
            assert settings.max_purge>3 and settings.max_blocklist>2 and settings.max_items>2


async def test_onboarding_link_uses_actual_instance_and_exposes_precise_rights(env,api):
    from dataclasses import replace
    from urllib.parse import parse_qs, urlparse

    from tests.bots.groupguard.test_phase03 import pm

    if env.child:
        env.child=replace(env.child,factory_username='review_factory',branding=True)
    await send(env,pm('/start',MEMBER))
    notice=api.calls('SendMessage')[-1]
    urls=[button.url for row in notice.reply_markup.inline_keyboard for button in row if button.url]
    link=next(urlparse(value) for value in urls if 'startgroup=' in value)
    assert link.netloc=='t.me' and link.path=='/'+env.username
    rights=set(parse_qs(link.query)['admin'][0].split(' '))
    assert {'delete_messages','restrict_members','pin_messages','invite_users','change_info'}<=rights
    await send(env,pm('/help',MEMBER))
    assert '/help' in api.calls('SendMessage')[-1].text
    if env.child:
        assert '@review_factory' in notice.text
