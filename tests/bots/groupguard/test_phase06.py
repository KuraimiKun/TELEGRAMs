"""Typed blocklists through actual dispatcher and two actual factory children."""

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import GetCustomEmojiStickers
from aiogram.types import (
    Document,
    MessageEntity,
    MessageOriginHiddenUser,
    MessageOriginUser,
    RichBlockParagraph,
    RichMessage,
    Sticker,
    Update,
)

from bots.groupguard import verification
from bots.groupguard.blocklist_types import trigger
from core.db.base import utcnow
from tests.bots.groupguard.test_groupguard import ADMIN, GROUP, MEMBER, gctx, group_msg, join_update, tg_user
from tests.bots.groupguard.test_phase01a import admin_member, env, send

__all__ = ['env', 'gctx']


async def test_multiple_quoted_wildcard_aliases_remove_only_requested_and_owner_clear(env, api):
    svc = env.extras['guard']
    await send(env, group_msg('/addblocklist ("café bar", "c\\?t", casino) custom reason', ADMIN))
    cfg = await svc.config(GROUP)
    assert {r['key'] for r in cfg.blocklist_entries} == {'café bar', r'c\?t', 'casino'}
    await send(env, group_msg('/blocklist', MEMBER))
    assert 'custom reason' in api.calls('SendMessage')[-1].text
    await send(env, group_msg('/blocklist exact:other', ADMIN))
    await send(env, group_msg('/rmblocklist "café bar"', ADMIN))
    assert {r['key'] for r in (await svc.config(GROUP)).blocklist_entries} == {r'c\?t', 'casino', 'exact:other'}
    await send(env, group_msg('/addblock red,blue', ADMIN))
    await send(env, group_msg('/rmblock red', ADMIN))
    assert 'blue' in (await svc.config(GROUP)).blocklist
    await send(env, group_msg('/rmblocklistall confirm', MEMBER))
    assert (await svc.config(GROUP)).blocklist_entries
    await send(env, group_msg('/rmblocklistall', ADMIN))
    assert (await svc.config(GROUP)).blocklist_entries
    await send(env, group_msg('/rmblocklistall confirm', ADMIN))
    assert not (await svc.config(GROUP)).blocklist_entries


@pytest.mark.parametrize('mode', ['nothing', 'warn', 'kick', 'ban', 'tban 1h', 'mute', 'tmute 1h'])
@pytest.mark.parametrize('delete', [False, True])
async def test_default_modes_independent_actual_delete_warning_duration(env, api, mode, delete):
    svc = env.extras['guard']
    await send(env, group_msg('/addblocklist casino', ADMIN))
    await send(env, group_msg('/blocklistmode '+mode, ADMIN))
    await send(env, group_msg('/blocklistdelete '+('on' if delete else 'off'), ADMIN))
    await svc.update_config(GROUP, warn_limit=20)
    request = group_msg('Casino!', MEMBER)
    await send(env, request)
    assert bool(api.calls('DeleteMessage')) is delete
    assert await svc.count_warns(GROUP, MEMBER) == (1 if mode == 'warn' else 0)
    if mode == 'nothing' or mode == 'warn':
        assert not api.calls('BanChatMember') and not api.calls('RestrictChatMember')
    else:
        call = (api.calls('RestrictChatMember') if 'mute' in mode else api.calls('BanChatMember'))[-1]
        assert call.user_id == MEMBER
        assert bool(api.calls('UnbanChatMember')) is (mode == 'kick')
        if mode.startswith('t'):
            assert 3590 <= call.until_date - utcnow().timestamp() <= 3601
        else:
            assert call.until_date is None


@pytest.mark.parametrize('key,text,extra', [
    ('casino', 'casino!', {}),
    ('prefix:spam', 'spam anywhere', {}),
    ('exact:spam', 'spam', {}),
    ('lookalike:spam', 'ѕраm', {}),
    ('file:.exe', 'caption', {'document': Document(file_id='f',file_unique_id='u',file_name='Bad.EXE')}),
    ('file:evil*.pdf', 'caption', {'document': Document(file_id='f',file_unique_id='u',file_name='evil-report.pdf')}),
    ('forward:88', 'forward', {'forward_origin': MessageOriginUser(date=utcnow(), sender_user=tg_user(88))}),
    ('inline:88', 'inline', {'via_bot': tg_user(88).model_copy(update={'is_bot': True})}),
    ('name:spam*', 'body', {'from_user': tg_user(MEMBER).model_copy(update={'first_name': 'Spammer'})}),
    ('username:bad*', 'body', {'from_user': tg_user(MEMBER).model_copy(update={'username': 'bad_user'})}),
    ('stickerpack:Bad', 'body', {'sticker': Sticker(file_id='f',file_unique_id='u',type='regular',width=10,height=10,is_animated=False,is_video=False,set_name='Bad')}),
    ('casino', None, {'caption': 'Casino caption'}),
    ('casino', None, {'rich_message': RichMessage(blocks=[RichBlockParagraph(text='casino rich')])}),
])
async def test_all_typed_actual_evidence_and_no_neighbor_match(env, api, key, text, extra):
    await send(env, group_msg('/addblocklist '+key, ADMIN))
    request = group_msg('temporary', MEMBER)
    request = request.model_copy(update={'message': request.message.model_copy(update={'text': text, **extra})})
    await send(env, request)
    assert api.calls('DeleteMessage')[-1].message_id == request.message.message_id
    before = len(api.calls('DeleteMessage'))
    await send(env, group_msg('scasino spammer evil.pdf clean text', MEMBER))
    assert len(api.calls('DeleteMessage')) == before


async def test_replied_custom_pack_and_unknown_forward_are_real(env, api):
    sticker = Sticker(file_id='f',file_unique_id='u',type='custom_emoji',width=10,height=10,is_animated=False,is_video=False,set_name='Bad',custom_emoji_id='99')
    api.responses['GetCustomEmojiStickers'] = [sticker]
    reply = group_msg('😀', MEMBER, entities=[MessageEntity(type='custom_emoji',offset=0,length=2,custom_emoji_id='99')]).message
    await send(env, group_msg('/addblocklist stickerpack:<>', ADMIN, reply_to=reply))
    await send(env, group_msg('😀', MEMBER, entities=reply.entities))
    assert api.calls('DeleteMessage')
    await send(env, group_msg('/addblocklist forward:88', ADMIN))
    before = len(api.calls('DeleteMessage'))
    await send(env, group_msg('hidden', MEMBER, forward_origin=MessageOriginHiddenUser(date=utcnow(),sender_user_name='88')))
    assert len(api.calls('DeleteMessage')) == before


async def test_fallback_override_reason_admin_approval_and_locks_first(env, api):
    svc = env.extras['guard']
    await send(env, group_msg('/setblocklistreason fallback', ADMIN))
    await send(env, group_msg('/blocklistmode warn', ADMIN))
    await svc.update_config(GROUP, warn_limit=20)
    await send(env, group_msg('/addblocklist casino', ADMIN))
    await send(env, group_msg('/addblocklist spam custom {tban 1h}', ADMIN))
    await send(env, group_msg('casino', ADMIN))
    assert not api.calls('DeleteMessage')
    await svc.approve(GROUP, MEMBER, None, ADMIN)
    await send(env, group_msg('casino', MEMBER))
    assert not api.calls('DeleteMessage')
    await svc.unapprove(GROUP, MEMBER)
    await send(env, group_msg('casino', MEMBER))
    assert 'fallback' in api.calls('SendMessage')[-1].text
    await send(env, group_msg('spam', MEMBER))
    assert 'custom' in api.calls('SendMessage')[-1].text and api.calls('BanChatMember')
    before = await svc.count_warns(GROUP, MEMBER)
    await send(env, group_msg('/lock url', ADMIN))
    await send(env, group_msg('casino https://evil.example', MEMBER))
    assert await svc.count_warns(GROUP, MEMBER) == before


async def test_join_and_observed_profile_change_without_synthetic_message(env, api):
    svc = env.extras['guard']
    await svc.update_config(GROUP, cas=False)
    await send(env, group_msg('/addblocklist username:bad* blocked {ban}', ADMIN))
    event = join_update(MEMBER)
    user = tg_user(MEMBER).model_copy(update={'username': 'bad_joiner'})
    joined = event.chat_member.model_copy(update={'new_chat_member': event.chat_member.new_chat_member.model_copy(update={'user': user})})
    await send(env, event.model_copy(update={'chat_member': joined}))
    assert api.calls('BanChatMember')[-1].user_id == MEMBER
    assert not api.calls('DeleteMessage') and (await verification.state_of(env, GROUP, MEMBER)) is None
    before = len(api.calls('BanChatMember'))
    await send(env, Update(update_id=group_msg('unique',MEMBER).update_id, chat_member=joined))
    assert len(api.calls('BanChatMember')) == before
    await send(env, group_msg('normal speaking', MEMBER))
    assert len(api.calls('BanChatMember')) == before
    changed = group_msg('normal speaking', MEMBER)
    changed = changed.model_copy(update={'message': changed.message.model_copy(update={'from_user': user})})
    await send(env, changed)
    assert len(api.calls('BanChatMember')) == before+1


async def test_delete_only_join_continues_captcha_and_nonhuman_no_fabricated_target(env, api):
    svc = env.extras['guard']
    await svc.update_config(GROUP, cas=False)
    await send(env, group_msg('/addblocklist name:*', ADMIN))
    await send(env, join_update(MEMBER))
    assert (await verification.state_of(env, GROUP, MEMBER)).status == 'pending' and not api.calls('DeleteMessage')


async def test_silent_selection_requires_creator_consent_log_and_loud_fallback(env, api):
    svc = env.extras['guard']
    await send(env, group_msg('/addblocklist casino hidden {sban}', ADMIN))
    assert not (await svc.config(GROUP)).blocklist_entries
    await svc.update_config(GROUP, silent_actions_allowed=True, log_chat_id=-10088)
    await send(env, group_msg('/addblocklist casino hidden {sban}', ADMIN))
    before = len([m for m in api.calls('SendMessage') if m.chat_id == GROUP])
    await send(env, group_msg('casino', MEMBER))
    assert api.calls('BanChatMember') and api.calls('SendMessage')[-1].chat_id == -10088
    assert len([m for m in api.calls('SendMessage') if m.chat_id == GROUP]) == before
    await svc.update_config(GROUP, log_chat_id=None)
    await send(env, group_msg('casino', MEMBER))
    assert api.calls('SendMessage')[-1].chat_id == GROUP
    await svc.update_config(GROUP, log_chat_id=-10088)
    original = api.responses.get('SendMessage')
    def denied(method):
        if method.chat_id == -10088:
            return TelegramBadRequest(method=method,message='log unavailable')
        return original(method) if callable(original) else original
    api.responses['SendMessage'] = denied
    await send(env, group_msg('casino', MEMBER))
    assert api.calls('SendMessage')[-1].chat_id == GROUP


async def test_warning_replay_edit_and_denied_capability_union(env, api):
    svc = env.extras['guard']
    await send(env, group_msg('/addblocklist casino {warn}', ADMIN))
    await svc.update_config(GROUP, warn_limit=20)
    request = group_msg('casino', MEMBER)
    await send(env, request)
    await send(env, request.model_copy(update={'update_id': group_msg('unique',MEMBER).update_id}))
    assert await svc.count_warns(GROUP, MEMBER) == 1
    changed = group_msg('clean', MEMBER)
    await send(env, changed)
    await send(env, Update(update_id=changed.update_id+100000, edited_message=changed.message.model_copy(update={'text': 'casino', 'edit_date': int(utcnow().timestamp())})))
    assert await svc.count_warns(GROUP, MEMBER) == 2
    old = api.responses['GetChatMember']
    api.responses['GetChatMember'] = lambda m: admin_member(env.bot_id, can_delete_messages=True) if m.user_id == env.bot_id else old(m)
    before = len(api.calls('DeleteMessage'))
    await send(env, group_msg('casino', MEMBER))
    assert await svc.count_warns(GROUP, MEMBER) == 2 and len(api.calls('DeleteMessage')) == before


async def test_legacy_writer_keeps_typed_entries_and_quota_does_not_truncate(env):
    svc = env.extras['guard']
    await svc.update_config(GROUP, blocklist_entries=[trigger('file:.exe').model_dump()])
    await svc.update_config(GROUP, blocklist=['old phrase'])
    cfg = await svc.config(GROUP)
    assert [r['key'] for r in cfg.blocklist_entries] == ['file:.exe', 'old phrase']
    for offset in range(0,150,30):
        await send(env, group_msg('/addblocklist ('+','.join('key'+str(n) for n in range(offset,offset+30))+')', ADMIN))
    cfg = await svc.config(GROUP)
    assert len(cfg.blocklist_entries) == 122  # Last whole batch rejected; existing entries survive.
    await send(env, group_msg('/addblocklist overflow', MEMBER))
    assert (await svc.config(GROUP)).blocklist_entries == cfg.blocklist_entries


async def test_entry_nothing_overrides_default_ban_and_extension_neighbor_is_safe(env, api):
    await send(env, group_msg('/blocklistmode ban', ADMIN))
    await send(env, group_msg('/addblocklist harmless {nothing}', ADMIN))
    await send(env, group_msg('/addblocklist file:.exe', ADMIN))
    await send(env, group_msg('harmless', MEMBER))
    assert api.calls('DeleteMessage') and not api.calls('BanChatMember')
    before = len(api.calls('DeleteMessage'))
    await send(env, group_msg('safe attachment', MEMBER, document=Document(file_id='f',file_unique_id='u',file_name='bad.exe.txt')))
    assert len(api.calls('DeleteMessage')) == before


async def test_canonical_username_optional_at_and_casefold_on_actual_join(env, api):
    await env.extras['guard'].update_config(GROUP, cas=False, captcha='off')
    await send(env, group_msg('/addblocklist username:@bad* {kick}', ADMIN))
    event = join_update(MEMBER)
    user = tg_user(MEMBER).model_copy(update={'username': 'BAD_user'})
    joined = event.chat_member.model_copy(update={'new_chat_member': event.chat_member.new_chat_member.model_copy(update={'user': user})})
    await send(env, event.model_copy(update={'chat_member': joined}))
    assert api.calls('BanChatMember')[-1].user_id == MEMBER and api.calls('UnbanChatMember')


async def test_pack_lookup_failure_no_guessed_match(env, api):
    await send(env, group_msg('/addblocklist stickerpack:Bad {ban}', ADMIN))
    api.responses['GetCustomEmojiStickers'] = TelegramBadRequest(method=GetCustomEmojiStickers(custom_emoji_ids=['99']),message='unknown pack')
    await send(env, group_msg('😀', MEMBER, entities=[MessageEntity(type='custom_emoji',offset=0,length=2,custom_emoji_id='99')]))
    assert not api.calls('DeleteMessage') and not api.calls('BanChatMember')
