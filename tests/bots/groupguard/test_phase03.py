"""Content behavior through standalone and two actual factory child dispatchers."""
from datetime import timedelta

import pytest
from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter
from aiogram.methods import SendMessage
from aiogram.types import CallbackQuery, Chat, ChatMemberLeft, MessageEntity, PhotoSize, Update
from sqlalchemy import select, update

from bots.groupguard import durable, jobs, repeats
from bots.groupguard.models import GuardJob, GuardRepeat
from core.db.base import utcnow
from tests.bots.groupguard.test_groupguard import (
    ADMIN,
    GROUP,
    MEMBER,
    gctx,
    group_msg,
    join_update,
    plain,
    tg_user,
)
from tests.bots.groupguard.test_phase01a import env, send

__all__ = ["env", "gctx"]


def pm(text, uid=MEMBER):
    request = group_msg(text, uid)
    return request.model_copy(update={"message": request.message.model_copy(update={"chat": Chat(id=uid, type="private")})})


async def make_due(ctx):
    # Stable distinct due identities even when a test crosses a wall-clock second.
    ctx.extras["test_due_time"] = ctx.extras.get("test_due_time", utcnow()) - timedelta(seconds=2)
    async with ctx.sm() as session:
        await session.execute(update(GuardRepeat).where(GuardRepeat.bot_id == ctx.bot_id).values(
            next_run=ctx.extras["test_due_time"]))
        await session.commit()


async def schedule(ctx):
    async with ctx.sm() as session:
        return (await session.execute(select(GuardRepeat).where(GuardRepeat.bot_id == ctx.bot_id))).scalar_one_or_none()


async def test_single_word_names_batch_filters_and_atomic_quota(env, api):
    for text in ('/save "two words" forbidden', '/save missing', '/filter ("unclosed" body', '/save faq okay%%%'+ 'x'*4097):
        await send(env, group_msg(text, ADMIN))
    assert not await env.extras["guard"].list_items(GROUP, "note")
    await send(env, group_msg('/save "faq" *Hello* {first}', ADMIN))
    reply = plain(30).model_copy(update={"from_user": tg_user(30).model_copy(update={"first_name": "Reply person"})})
    await send(env, group_msg('/get faq', MEMBER, reply_to=reply))
    assert api.calls("SendMessage")[-1].text == "<b>Hello</b> Reply person"
    await send(env, group_msg('/filter ("red apple", pear, "green, apple") Fruit!', ADMIN))
    assert {item.key for item in await env.extras["guard"].filters(GROUP)} == {"red apple", "pear", "green, apple"}
    await send(env, group_msg("a green, apple", MEMBER))
    assert api.calls("SendMessage")[-1].text == "Fruit!"
    await env.settings.set("max_items", 4)
    await send(env, group_msg('/filter (one, two) exceed', ADMIN))
    assert len(await env.extras["guard"].filters(GROUP)) == 3


async def test_native_entities_prefix_exact_and_privileged_filters(env, api):
    text = '/save rich 😀 hello'
    offset = len(text[:text.index('hello')].encode('utf-16-le')) // 2
    await send(env, group_msg(text, ADMIN, entities=[MessageEntity(type="bold", offset=offset, length=5)]))
    await send(env, group_msg('#rich', MEMBER))
    assert api.calls("SendMessage")[-1].text == '😀 <b>hello</b>'
    await send(env, group_msg('/filter "prefix:hey" Hello {replytag}{user} {first}', ADMIN))
    await send(env, group_msg('/filter "exact:stop now" Exact {admin}', ADMIN))
    before = len(api.calls("SendMessage"))
    for text in ('some hey', 'stop now please', 'stop now'):
        await send(env, group_msg(text, MEMBER))
    await send(env, group_msg('hey there', ADMIN))
    assert len(api.calls("SendMessage")) == before
    reply = plain(30).model_copy(update={"from_user": tg_user(30).model_copy(update={"first_name": "Reply person"})})
    await send(env, group_msg('hey there', MEMBER, reply_to=reply))
    assert api.calls("SendMessage")[-1].text == 'Hello  Reply person'
    await send(env, group_msg('stop now', ADMIN))
    assert api.calls("SendMessage")[-1].text == 'Exact '


async def test_private_note_and_rules_tokens_require_current_membership(env, api):
    await send(env, group_msg('/save secret Private {private} {mention}', ADMIN))
    await send(env, group_msg('#secret', MEMBER))
    button = api.calls("SendMessage")[-1].reply_markup.inline_keyboard[0][0]
    token = button.url.split('start=')[1]
    await send(env, pm('/start ' + token))
    assert 'tg://user?id=20' in api.calls("SendMessage")[-1].text
    before = len(api.calls("SendMessage"))
    await send(env, pm('/start ' + token, 30))
    assert len(api.calls("SendMessage")) == before + 1 and 'unavailable' in api.calls("SendMessage")[-1].text
    old = api.responses['GetChatMember']
    api.responses['GetChatMember'] = lambda m: ChatMemberLeft(user=tg_user(MEMBER)) if m.user_id == MEMBER else old(m)
    await send(env, pm('/start ' + token))
    assert 'unavailable' in api.calls("SendMessage")[-1].text
    api.responses['GetChatMember'] = old
    await send(env, group_msg('/setrules *Be nice* {first}', ADMIN))
    await send(env, group_msg('/privaterules on', ADMIN))
    await send(env, group_msg('/setrulesbutton Read me', ADMIN))
    await send(env, group_msg('/rules', MEMBER))
    button = api.calls("SendMessage")[-1].reply_markup.inline_keyboard[0][0]
    assert button.text == 'Read me'
    await send(env, pm('/start ' + button.url.split('start=')[1]))
    assert api.calls("SendMessage")[-1].text == '<b>Be nice</b> Alice'


async def test_bound_menu_cannot_substitute_group_message_or_private_owner(env, api):
    await send(env, group_msg('/save answer Answer {admin}', ADMIN))
    await send(env, group_msg('/save menu [Answer](buttonurl://#answer)', ADMIN))
    await send(env, group_msg('#menu', ADMIN))
    msg = api.messages[-1]
    data = api.calls('SendMessage')[-1].reply_markup.inline_keyboard[0][0].callback_data
    async def click(message=msg, value=data, uid=ADMIN):
        await send(env, Update(update_id=group_msg('new', uid).update_id,
            callback_query=CallbackQuery(id='click', from_user=tg_user(uid), chat_instance='x', data=value, message=message)))
    await click(uid=MEMBER)
    assert api.calls('AnswerCallbackQuery')[-1].show_alert
    before = len(api.calls('SendMessage'))
    await click(value=data.replace(str(GROUP), '-1009'))
    await click(message=msg.model_copy(update={'message_id': msg.message_id+1}))
    assert len(api.calls('SendMessage')) == before
    await click()
    assert api.calls('SendMessage')[-1].text == 'Answer '


async def test_slash_filter_suggestions_use_actual_chat_scope_and_failure_is_partial(env, api):
    await send(env, group_msg('/filter /price Free {command Prices}', ADMIN))
    registered = api.calls('SetMyCommands')[-1]
    assert registered.scope.chat_id == GROUP and registered.language_code is None
    assert any(c.command == 'price' and c.description == 'Prices' for c in registered.commands)
    await send(env, group_msg('/price', MEMBER))
    assert api.calls('SendMessage')[-1].text == 'Free '
    await send(env, group_msg('/stop /price', ADMIN))
    assert api.calls('DeleteMyCommands')[-1].scope.chat_id == GROUP
    api.responses['SetMyCommands'] = False
    await send(env, group_msg('/filter /price Free {command}', ADMIN))
    assert (await env.audit.recent(1))[0].details['outcome'] == 'partial'
    before = len(await env.extras['guard'].filters(GROUP))
    await send(env, group_msg('/filter /ban Bad {command}', ADMIN))
    assert len(await env.extras['guard'].filters(GROUP)) == before


async def test_repeat_is_actual_delivery_one_catchup_and_cancelled_on_replace_delete(env, api):
    await send(env, group_msg('/save daily Daily {repeat 1m}', ADMIN, message_thread_id=19))
    original = (await schedule(env)).generation
    await make_due(env)
    await repeats.tick(env)
    before = len(api.calls('SendMessage'))
    assert await durable.sweep(env) == 1
    assert len(api.calls('SendMessage')) == before+1 and api.calls('SendMessage')[-1].message_thread_id == 19
    assert (await schedule(env)).next_run > utcnow()
    assert await durable.sweep(env) == 0
    await make_due(env)
    await repeats.tick(env)
    await send(env, group_msg('/save daily New {repeated 2m}', ADMIN))
    assert (await schedule(env)).generation != original
    before = len(api.calls('SendMessage'))
    assert await durable.sweep(env) == 0 and len(api.calls('SendMessage')) == before
    await send(env, group_msg('/clear daily', ADMIN))
    assert await schedule(env) is None


async def test_repeat_revoked_author_private_policy_and_retry(env, api):
    await send(env, group_msg('/save daily Daily {repeat 1m}', ADMIN))
    await make_due(env)
    await repeats.tick(env)
    api.responses['SendMessage'] = TelegramRetryAfter(method=SendMessage(chat_id=GROUP, text='Daily'), message='slow', retry_after=1)
    assert await durable.sweep(env) == 0 and (await schedule(env)).status == 'active'
    api.responses.pop('SendMessage')
    async with env.sm() as session:
        await session.execute(update(GuardJob).where(GuardJob.bot_id == env.bot_id, GuardJob.kind == 'repeat_note').values(run_at=utcnow()))
        await session.commit()
    assert await durable.sweep(env) == 1
    await make_due(env)
    await repeats.tick(env)
    await env.extras['guard'].update_config(GROUP, private_notes=True)
    before = len(api.calls('SendMessage'))
    assert await durable.sweep(env) == 0 and len(api.calls('SendMessage')) == before
    assert (await schedule(env)).status == 'cancelled'


async def test_repeat_revoked_author_is_cancelled_before_delivery(env, api):
    from aiogram.types import ChatMemberMember
    await send(env, group_msg('/save daily Daily {repeat 1m}', ADMIN))
    await make_due(env)
    await repeats.tick(env)
    old = api.responses['GetChatMember']
    api.responses['GetChatMember'] = lambda m: ChatMemberMember(user=tg_user(ADMIN)) if m.user_id == ADMIN else old(m)
    before = len(api.calls('SendMessage'))
    await durable.sweep(env)
    assert len(api.calls('SendMessage')) == before and (await schedule(env)).status == 'cancelled'


async def test_repeat_network_uncertainty_and_restart_never_blindly_resend(env, api):
    await send(env, group_msg('/save daily Daily {repeat 1m}', ADMIN))
    await make_due(env)
    await repeats.tick(env)
    api.responses['SendMessage'] = TelegramNetworkError(method=SendMessage(chat_id=GROUP, text='Daily'), message='unknown')
    assert await durable.sweep(env) == 0
    assert (await schedule(env)).status == 'uncertain'
    api.responses.pop('SendMessage')
    before = len(api.calls('SendMessage'))
    await repeats.tick(env)
    assert await durable.sweep(env) == 0 and len(api.calls('SendMessage')) == before
    await send(env, group_msg('/save daily New {repeat 1m}', ADMIN))
    await make_due(env)
    await repeats.tick(env)
    async with env.sm() as session:
        job = (await session.execute(select(GuardJob).where(GuardJob.bot_id == env.bot_id,
            GuardJob.kind == 'repeat_note', GuardJob.status == 'pending'))).scalar_one()
    claimed = await durable.claim(env, job.id)
    await durable.dispatched(env, claimed)
    async with env.sm() as session:
        await session.execute(update(GuardJob).where(GuardJob.id == job.id).values(lease_until=utcnow()-timedelta(seconds=1)))
        await session.commit()
    await repeats.tick(env)
    assert (await schedule(env)).status == 'uncertain'


async def test_greeting_media_flags_and_old_welcome_cleanup_preserve_captcha(env, api):
    photo = plain(ADMIN, '*Hello* {mention} {preview}{mediaspoiler}{rules}').model_copy(update={
        'photo': [PhotoSize(file_id='photo-file', file_unique_id='unique', width=10, height=10)]})
    await send(env, group_msg('/setwelcome', ADMIN, reply_to=photo))
    await send(env, group_msg('/setrules Be kind', ADMIN))
    await send(env, group_msg('/cleanwelcome on', ADMIN))
    await env.extras['guard'].update_config(GROUP, captcha='button', cas=False)
    await send(env, join_update(MEMBER))
    first = api.calls('SendPhoto')[-1]
    assert first.has_spoiler and '<b>Hello</b>' in first.caption
    from bots.groupguard.models import GuardChallenge
    async with env.sm() as session:
        challenge = await session.get(GuardChallenge, (env.bot_id, GROUP, MEMBER))
    assert challenge.status == 'pending' and challenge.message_id == api.messages[-1].message_id
    first_photo = next(m for m in reversed(api.messages) if m.message_id != challenge.message_id)
    await send(env, join_update(30))
    async with env.sm() as session:
        pending = list((await session.execute(select(GuardJob).where(GuardJob.bot_id == env.bot_id, GuardJob.kind == 'content_delete'))).scalars())
        assert any(j.payload['message_id'] == first_photo.message_id and j.run_at > utcnow()+timedelta(seconds=295) for j in pending)
        await session.execute(update(GuardJob).where(GuardJob.bot_id == env.bot_id, GuardJob.kind == 'content_delete').values(run_at=utcnow()))
        await session.commit()
    await durable.sweep(env)
    assert any(m.message_id == first_photo.message_id for m in api.calls('DeleteMessage'))
    assert not api.calls('UnbanChatMember')
    await send(env, group_msg('/resetwelcome', ADMIN))
    cfg = await env.extras['guard'].config(GROUP)
    assert cfg.welcome_content is None and cfg.welcome_text == ''


async def test_creator_clearall_and_media_permapin(env, api):
    await send(env, group_msg('/save one One', ADMIN))
    await send(env, group_msg('/clearall confirm', MEMBER))
    assert await env.extras['guard'].get_item(GROUP, 'note', 'one') is not None
    await send(env, group_msg('/clearall', ADMIN))
    assert await env.extras['guard'].get_item(GROUP, 'note', 'one') is not None
    await send(env, group_msg('/clearall confirm', ADMIN))
    assert await env.extras['guard'].get_item(GROUP, 'note', 'one') is None
    photo = plain(ADMIN, '*Pinned*').model_copy(update={
        'photo': [PhotoSize(file_id='photo-file', file_unique_id='unique', width=10, height=10)]})
    await send(env, group_msg('/permapin', ADMIN, reply_to=photo))
    assert api.calls('SendPhoto')[-1].caption == '<b>Pinned</b>' and api.calls('PinChatMessage')


async def test_scheduler_hook_delivers_due_repeats(env, api):
    await send(env, group_msg('/save daily Work {repeat 1m}', ADMIN))
    await make_due(env)
    await jobs.captcha_job(env)
    assert api.calls('SendMessage')[-1].text == 'Work '


async def test_factory_sweep_discovers_due_cadence_without_preexisting_job(env, api):
    registry = env.extras['test_registry']
    if registry is None:
        pytest.skip('factory-specific sweep; standalone scheduled hook separately exercised')
    children = [ctx for ctx in env.extras['test_contexts'] if ctx.child is not None]
    for child in children:
        await send(child, group_msg(f'/save daily Work{child.bot_id} {{repeat 1m}}', ADMIN))
        await make_due(child)
    before = len(api.messages)
    await jobs.factory_captchas(registry)
    actual = {(m.from_user.id, m.text.strip()) for m in api.messages[before:]}
    assert {(c.bot_id, f'Work{c.bot_id}') for c in children} <= actual
    await jobs.factory_captchas(registry)
    assert len(api.messages) == before + 2


@pytest.mark.parametrize('kind', ['welcome', 'goodbye'])
@pytest.mark.parametrize('spelling,value', [('on', True), ('yes', True), ('true', True),
    ('off', False), ('no', False), ('false', False)])
async def test_greeting_boolean_forms_require_fresh_authority(env, api, kind, spelling, value):
    svc = env.extras['guard']
    await svc.update_config(GROUP, **{kind: not value})
    await send(env, group_msg(f'/{kind} {spelling}', MEMBER))
    assert getattr(await svc.config(GROUP), kind) == (not value)
    await send(env, group_msg(f'/{kind} {spelling}', ADMIN))
    assert getattr(await svc.config(GROUP), kind) == value


async def test_goodbye_actual_leave_preview_noformat_and_reset(env, api):
    from aiogram.types import ChatMemberUpdated
    await send(env, group_msg('/setgoodbye *Farewell* {id} {first}', ADMIN))
    await send(env, group_msg('/goodbye noformat', MEMBER))
    assert api.calls('SendMessage')[-1].text == '<pre>*Farewell* {id} {first}</pre>'
    await send(env, group_msg('/goodbye', MEMBER))
    assert api.calls('SendMessage')[-1].text == '<b>Farewell</b> 20 Alice'
    joined = join_update(MEMBER).chat_member
    left = joined.model_copy(update={'old_chat_member': joined.new_chat_member,
        'new_chat_member': ChatMemberLeft(user=tg_user(MEMBER))})
    assert isinstance(left, ChatMemberUpdated)
    await send(env, Update(update_id=group_msg('unused', MEMBER).update_id, chat_member=left))
    assert api.calls('SendMessage')[-1].text == '<b>Farewell</b> 20 Alice'
    await send(env, group_msg('/resetgoodbye', ADMIN))
    cfg = await env.extras['guard'].config(GROUP)
    assert cfg.goodbye and cfg.goodbye_content is None


async def test_private_note_overrides_admin_access_and_noformat(env, api):
    await send(env, group_msg('/privatenotes on', ADMIN))
    await send(env, group_msg('/save public *Public* {noprivate}', ADMIN))
    await send(env, group_msg('/get public', MEMBER))
    assert api.calls('SendMessage')[-1].text == '<b>Public</b> '
    await send(env, group_msg('/save secret Secret {admin}', ADMIN))
    before = len(api.calls('SendMessage'))
    await send(env, group_msg('#secret', MEMBER))
    assert len(api.calls('SendMessage')) == before
    await send(env, group_msg('/get secret noformat', ADMIN))
    button = api.calls('SendMessage')[-1].reply_markup.inline_keyboard[0][0]
    await send(env, pm('/start ' + button.url.split('start=')[1], ADMIN))
    assert api.calls('SendMessage')[-1].text == '<pre>Secret {admin}</pre>'


async def test_button_generator_real_note_menu_row_and_bot_optin_filter(env, api):
    await send(env, group_msg('/save faq FAQ', ADMIN))
    await send(env, group_msg('/button "Web Site" https://example.com\n"Note" #faq same', MEMBER))
    row = api.calls('SendMessage')[-1].reply_markup.inline_keyboard[0]
    assert len(row) == 2 and row[0].text == 'Web Site' and row[1].callback_data.startswith('gg:menu:')
    await send(env, group_msg('/filter beep Human only', ADMIN))
    botmsg = group_msg('beep', 909)
    botmsg = botmsg.model_copy(update={'message': botmsg.message.model_copy(update={'from_user': tg_user(909).model_copy(update={'is_bot': True})})})
    before = len(api.calls('SendMessage'))
    await send(env, botmsg)
    assert len(api.calls('SendMessage')) == before
    await send(env, group_msg('/filter beep Bots too {allow_bot}', ADMIN))
    botmsg = group_msg('beep', 909).model_copy(update={'message': group_msg('beep', 909).message.model_copy(update={
        'from_user': tg_user(909).model_copy(update={'is_bot': True})})})
    await send(env, botmsg)
    assert api.calls('SendMessage')[-1].text == 'Bots too '


@pytest.mark.parametrize('media', ['photo', 'video', 'animation', 'document', 'audio', 'voice', 'sticker', 'video_note'])
async def test_saved_attachment_and_filter_use_optional_command_caption(env, api, media):
    from aiogram.types import Animation, Audio, Document, Sticker, Video, VideoNote, Voice
    fields = dict(file_id='media-file', file_unique_id='unique')
    objects = {
        'photo': [PhotoSize(**fields, width=10, height=10)],
        'video': Video(**fields, width=10, height=10, duration=1),
        'animation': Animation(**fields, width=10, height=10, duration=1),
        'document': Document(**fields), 'audio': Audio(**fields, duration=1),
        'voice': Voice(**fields, duration=1),
        'sticker': Sticker(**fields, type='regular', width=10, height=10, is_animated=False, is_video=False),
        'video_note': VideoNote(**fields, length=10, duration=1),
    }
    replied = plain(ADMIN, 'Original').model_copy(update={media: objects[media]})
    await send(env, group_msg('/save media *Custom*', ADMIN, reply_to=replied))
    await send(env, group_msg('#media', MEMBER))
    method = 'Send' + ''.join(p.title() for p in media.split('_'))
    call = api.calls(method)[-1]
    assert getattr(call, media) == 'media-file'
    if media in {'sticker', 'video_note'}:
        assert api.calls('SendMessage')[-1].text == '<b>Custom</b>'
    else:
        assert call.caption == '<b>Custom</b>'
    await send(env, group_msg('/filter media Filter reply', ADMIN, reply_to=replied))
    await send(env, group_msg('media', MEMBER))
    if media in {'sticker', 'video_note'}:
        assert api.calls('SendMessage')[-1].text == 'Filter reply'
    else:
        assert api.calls(method)[-1].caption == 'Filter reply'


async def test_command_length_boundary_and_legacy_note_names(env, api):
    key = 'x' * 32
    await send(env, group_msg(f'/filter /{key} Allowed {{command}}', ADMIN))
    assert any(c.command == key for c in api.calls('SetMyCommands')[-1].commands)
    before = len(await env.extras['guard'].filters(GROUP))
    await send(env, group_msg(f'/filter /{key}x Invalid {{command}}', ADMIN))
    assert len(await env.extras['guard'].filters(GROUP)) == before
    await env.extras['guard'].save_item(GROUP, 'note', 'legacy phrase', text='<b>Old</b>',
        media_kind=None, file_id=None, limit=150)
    await send(env, group_msg('/get legacy phrase', MEMBER))
    assert api.calls('SendMessage')[-1].text == '<b>Old</b>'


async def test_caption_command_keeps_native_entity_and_attachment(env, api):
    caption = '/save caption *Raw* rich'
    request = group_msg('placeholder', ADMIN)
    request = request.model_copy(update={'message': request.message.model_copy(update={
        'text': None, 'caption': caption, 'caption_entities': [MessageEntity(type='bold', offset=20, length=4)],
        'photo': [PhotoSize(file_id='photo-file', file_unique_id='unique', width=10, height=10)]})})
    await send(env, request)
    await send(env, group_msg('#caption', MEMBER))
    assert api.calls('SendPhoto')[-1].caption == '*Raw* <b>rich</b>'
