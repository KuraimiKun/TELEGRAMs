"""Real image verification and issued-policy behavior in standalone and two children."""
import io
from datetime import timedelta

import pytest
from aiogram.types import Update
from PIL import Image
from sqlalchemy import update

from bots.groupguard import actions, captcha_modes, challenges, durable, verification
from bots.groupguard.keyboards import GgCb
from bots.groupguard.models import GuardChallenge, GuardJob, GuardRestriction
from core.db.base import utcnow
from tests.bots.groupguard.test_groupguard import (
    ADMIN,
    GROUP,
    MEMBER,
    bound_callback,
    gctx,
    group_msg,
    join_update,
)
from tests.bots.groupguard.test_phase01a import env, send
from tests.bots.groupguard.test_phase03 import pm

__all__ = ["env", "gctx"]


@pytest.mark.parametrize('mode', ['text', 'text2', 'math'])
async def test_image_modes_open_real_pm_png_and_verify_progress(env, api, mode):
    await env.extras['guard'].update_config(GROUP, captcha=mode, cas=False)
    await send(env, join_update(MEMBER))
    banner = api.calls('SendMessage')[-1]
    link = banner.reply_markup.inline_keyboard[0][0].url.split('start=')[1]
    state = await verification.state_of(env, GROUP, MEMBER)
    assert state.status == 'pending' and not api.calls('SendPhoto')
    await send(env, pm('/start ' + link))
    photo = api.calls('SendPhoto')[-1]
    assert photo.chat_id == MEMBER
    image = Image.open(io.BytesIO(photo.photo.data))
    assert image.size == (640, 180) and len(photo.photo.data) > 1000
    image.verify()
    state = await verification.state_of(env, GROUP, MEMBER)
    message = api.messages[-1]
    before = len(api.calls('RestrictChatMember'))
    answers = state.answer if mode == 'text2' else [state.answer]
    for sequence, choice in enumerate(answers):
        value = GgCb(action='cap', chat=GROUP, user=MEMBER, arg=f'{state.generation}.{sequence}.{choice}').pack()
        await send(env, bound_callback(value, message, MEMBER))
        if sequence < len(answers)-1:
            assert len(api.calls('RestrictChatMember')) == before
            assert len((await verification.state_of(env, GROUP, MEMBER)).progress) == sequence+1
            # A second delivered callback with this prior sequence cannot advance again.
            await send(env, bound_callback(value, message, MEMBER))
            assert len((await verification.state_of(env, GROUP, MEMBER)).progress) == sequence+1
    assert await challenges.verified(env, GROUP, MEMBER)
    assert (await verification.state_of(env, GROUP, MEMBER)).status == 'solved'
    assert len(api.calls('RestrictChatMember')) == before+1 and api.calls('EditMessageCaption')


async def test_rules_are_an_actual_frozen_acceptance_stage(env, api):
    svc = env.extras['guard']
    await svc.update_config(GROUP, captcha='button', captcha_rules=True, rules='Original rules', cas=False)
    await send(env, join_update(MEMBER))
    link = api.calls('SendMessage')[-1].reply_markup.inline_keyboard[0][0].url.split('start=')[1]
    await send(env, pm('/start ' + link))
    state = await verification.state_of(env, GROUP, MEMBER)
    message = api.messages[-1]
    await svc.update_config(GROUP, captcha_rules=False, rules='Changed rules')
    value = GgCb(action='cap', chat=GROUP, user=MEMBER, arg=state.generation+'.0.0').pack()
    before = len(api.calls('RestrictChatMember'))
    await send(env, bound_callback(value, message, MEMBER))
    assert not await challenges.verified(env, GROUP, MEMBER) and len(api.calls('RestrictChatMember')) == before
    assert api.calls('SendMessage')[-1].text == 'Original rules'
    accept = api.calls('SendMessage')[-1].reply_markup.inline_keyboard[-1][0].callback_data
    rules_message = api.messages[-1]
    await send(env, bound_callback(accept, rules_message, 30))
    assert len(api.calls('RestrictChatMember')) == before
    await send(env, bound_callback(accept, rules_message, MEMBER))
    assert await challenges.verified(env, GROUP, MEMBER)


async def test_cap_settings_authority_plaintext_label_and_bounds(env, api):
    svc = env.extras['guard']
    for text in ('/captchamode text2', '/setcaptchatext literal {mention}', '/captchakicktime 1d', '/captchamutetime 1h'):
        await send(env, group_msg(text, MEMBER))
    cfg = await svc.config(GROUP)
    assert cfg.captcha == 'button' and not cfg.captcha_text and cfg.captcha_kick_seconds is None
    await send(env, group_msg('/setcaptchatext literal {mention}', ADMIN))
    await svc.update_config(GROUP, cas=False)
    await send(env, join_update(MEMBER))
    assert api.calls('SendMessage')[-1].reply_markup.inline_keyboard[0][0].text == 'literal {mention}'
    for text in ('/captchakicktime 4m', '/captchakicktime 25h'):
        await send(env, group_msg(text, ADMIN))
    assert (await svc.config(GROUP)).captcha_kick_seconds is None
    await send(env, group_msg('/captchakicktime 1d', ADMIN))
    assert (await svc.config(GROUP)).captcha_kick_seconds == 86400
    await send(env, group_msg('/captchakicktime 5m', ADMIN))
    assert (await svc.config(GROUP)).captcha_kick_seconds == 300
    await send(env, group_msg('/captchamutetime off', ADMIN))
    assert (await svc.config(GROUP)).captcha_mute_seconds is None


async def test_duplicate_observed_join_does_not_renew_or_repeat_prompt(env, api):
    await env.extras['guard'].update_config(GROUP, cas=False)
    request = join_update(MEMBER)
    await send(env, request)
    old = await verification.state_of(env, GROUP, MEMBER)
    before = len(api.calls('SendMessage'))
    await send(env, Update(update_id=group_msg('unused', MEMBER).update_id, chat_member=request.chat_member))
    current = await verification.state_of(env, GROUP, MEMBER)
    assert current.generation == old.generation and current.deadline == old.deadline
    assert len(api.calls('SendMessage')) == before


def test_choice_callbacks_fit_real_maximum_ids():
    from types import SimpleNamespace
    state = SimpleNamespace(policy={}, question_solved=False, chat_id=-(2**52-1), user_id=2**52-1,
        generation='a'*16, progress='012', mode='text2', prompt=captcha_modes.question('text2').to_dict())
    from bots.groupguard.module import GroupGuardBot
    from core.i18n import Translator
    ctx = SimpleNamespace(translator=Translator(GroupGuardBot.locales_dir))
    for row in verification.markup(ctx, state).inline_keyboard:
        for button in row:
            assert len(button.callback_data.encode()) <= 64


async def test_duplicate_join_without_captcha_does_not_repeat_welcome(env, api):
    await env.extras['guard'].update_config(GROUP, captcha='off', cas=False)
    request = join_update(MEMBER)
    await send(env, request)
    before = len(api.calls('SendMessage'))
    await send(env, Update(update_id=group_msg('unused', MEMBER).update_id, chat_member=request.chat_member))
    assert len(api.calls('SendMessage')) == before


async def test_verification_release_timer_uses_issued_deadline_and_keeps_manual_hold(env, api):
    await env.extras['guard'].update_config(GROUP, captcha_mute_seconds=60, cas=False)
    assert (await actions.punish(env, GROUP, MEMBER, 'mute', None, origin='manual')).primary_completed
    await send(env, join_update(MEMBER))
    async with env.sm() as session:
        await session.execute(update(GuardJob).where(GuardJob.bot_id == env.bot_id, GuardJob.kind == 'verification_release').values(run_at=utcnow()))
        await session.commit()
    before = len(api.calls('RestrictChatMember'))
    assert await durable.sweep(env) == 0 and len(api.calls('RestrictChatMember')) == before
    # Test the legitimate due path with both durable deadline and wake-up time advanced.
    async with env.sm() as session:
        await session.execute(update(GuardChallenge).where(GuardChallenge.bot_id == env.bot_id,
            GuardChallenge.chat_id == GROUP, GuardChallenge.user_id == MEMBER).values(created_at=utcnow()-timedelta(seconds=61)))
        await session.execute(update(GuardJob).where(GuardJob.bot_id == env.bot_id, GuardJob.kind == 'verification_release').values(
            status='pending', dispatched=False, run_at=utcnow()))
        await session.commit()
    await env.extras['guard'].update_config(GROUP, captcha_mute_seconds=None)
    assert await durable.sweep(env) == 1
    assert len(api.calls('RestrictChatMember')) == before and not await challenges.verified(env, GROUP, MEMBER)
    async with env.sm() as session:
        assert await session.get(GuardRestriction, (env.bot_id, GROUP, MEMBER, 'manual')) is not None
        assert await session.get(GuardRestriction, (env.bot_id, GROUP, MEMBER, 'captcha')) is None
    assert (await verification.state_of(env, GROUP, MEMBER)).status == 'released'


async def test_owned_temporary_ban_release_keeps_unrelated_mute_and_rejoin_reapplies(env, api):
    await env.extras['guard'].update_config(GROUP, captcha='off', cas=False)
    await actions.punish(env, GROUP, MEMBER, 'mute', None, origin='manual')
    ban = await actions.punish(env, GROUP, MEMBER, 'ban', timedelta(minutes=1), source='captcha', generation='a'*16)
    assert ban.primary_completed
    released = await actions.unban(env, GROUP, MEMBER, source='captcha', generation='a'*16)
    assert released.primary_completed and api.calls('UnbanChatMember')
    async with env.sm() as session:
        assert await session.get(GuardRestriction, (env.bot_id, GROUP, MEMBER, 'manual')) is not None
    before = len(api.calls('RestrictChatMember'))
    await send(env, join_update(MEMBER))
    assert len(api.calls('RestrictChatMember')) == before+1 and not api.calls('RestrictChatMember')[-1].permissions.can_send_messages


async def test_known_failed_release_retries_but_mutation_uncertainty_does_not(env, api):
    from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
    from aiogram.methods import GetChat, RestrictChatMember
    await env.extras['guard'].update_config(GROUP, cas=False)
    await send(env, join_update(MEMBER))
    message = api.messages[-1]
    data = api.calls('SendMessage')[-1].reply_markup.inline_keyboard[0][0].callback_data
    before = len(api.calls('RestrictChatMember'))
    original_chat = api.responses['GetChat']
    api.responses['GetChat'] = TelegramBadRequest(method=GetChat(chat_id=GROUP), message='lookup failed')
    await send(env, bound_callback(data, message, MEMBER))
    assert len(api.calls('RestrictChatMember')) == before and (await verification.state_of(env, GROUP, MEMBER)).status == 'pending'
    api.responses['GetChat'] = original_chat
    api.responses['RestrictChatMember'] = TelegramNetworkError(method=RestrictChatMember(chat_id=GROUP, user_id=MEMBER,
        permissions=actions.MUTED), message='unknown remote outcome')
    await send(env, bound_callback(data, message, MEMBER))
    assert (await verification.state_of(env, GROUP, MEMBER)).status == 'uncertain'
    api.responses.pop('RestrictChatMember')
    before = len(api.calls('RestrictChatMember'))
    await send(env, bound_callback(data, message, MEMBER))
    assert len(api.calls('RestrictChatMember')) == before and not await challenges.verified(env, GROUP, MEMBER)


async def test_wrong_attempts_apply_real_temporary_ban_and_do_not_verify(env, api):
    await env.extras['guard'].update_config(GROUP, captcha='math', cas=False)
    await send(env, join_update(MEMBER))
    link = api.calls('SendMessage')[-1].reply_markup.inline_keyboard[0][0].url.split('start=')[1]
    await send(env, pm('/start ' + link))
    state = await verification.state_of(env, GROUP, MEMBER)
    message = api.messages[-1]
    wrong = next(str(i) for i in range(4) if str(i) != state.answer)
    data = GgCb(action='cap', chat=GROUP, user=MEMBER, arg=state.generation+'.0.'+wrong).pack()
    for _ in range(3):
        await send(env, bound_callback(data, message, MEMBER))
    assert len(api.calls('BanChatMember')) == 1 and not api.calls('UnbanChatMember')
    assert 3590 <= api.calls('BanChatMember')[-1].until_date - utcnow().timestamp() <= 3601
    assert not await challenges.verified(env, GROUP, MEMBER)
    assert (await verification.state_of(env, GROUP, MEMBER)).status == 'failed'
    assert 'Verification failed' in api.calls('AnswerCallbackQuery')[-1].text


async def test_partial_timeout_kick_completes_only_owned_unban(env, api):
    from aiogram.exceptions import TelegramRetryAfter
    from aiogram.methods import UnbanChatMember
    await env.extras['guard'].update_config(GROUP, cas=False)
    await send(env, join_update(MEMBER))
    async with env.sm() as session:
        await session.execute(update(GuardChallenge).where(GuardChallenge.bot_id == env.bot_id,
            GuardChallenge.chat_id == GROUP, GuardChallenge.user_id == MEMBER).values(deadline=utcnow()))
        await session.execute(update(GuardJob).where(GuardJob.bot_id == env.bot_id, GuardJob.kind == 'captcha_expire').values(run_at=utcnow()))
        await session.commit()
    api.responses['UnbanChatMember'] = TelegramRetryAfter(method=UnbanChatMember(chat_id=GROUP,user_id=MEMBER), message='slow', retry_after=1)
    assert await durable.sweep(env) == 0
    assert len(api.calls('BanChatMember')) == 1
    api.responses.pop('UnbanChatMember')
    async with env.sm() as session:
        await session.execute(update(GuardJob).where(GuardJob.bot_id == env.bot_id,
            GuardJob.kind.in_({'captcha_expire','verification_unban'})).values(run_at=utcnow()))
        await session.commit()
    assert await durable.sweep(env) == 1 and len(api.calls('BanChatMember')) == 1
    assert len(api.calls('UnbanChatMember')) == 2
    assert (await verification.state_of(env, GROUP, MEMBER)).status == 'expired'


@pytest.mark.parametrize('mode', ['button','math'])
async def test_request_contact_window_and_frozen_rules_approval(env, api, mode):
    from aiogram.types import Chat, ChatJoinRequest

    from tests.bots.groupguard.test_groupguard import tg_user
    cfg = dict(captcha=mode, captcha_rules=True, rules='Request rules', cas=False)
    await env.extras['guard'].update_config(GROUP, **cfg)
    contact = 991120
    request = ChatJoinRequest(chat=Chat(id=GROUP, type='supergroup'), from_user=tg_user(MEMBER),
        user_chat_id=contact, date=(utcnow()-timedelta(seconds=10)).replace(microsecond=0))
    update_event = Update(update_id=group_msg('unused', MEMBER).update_id, chat_join_request=request)
    await send(env, update_event)
    state = await verification.state_of(env, GROUP, MEMBER)
    assert state.message_chat_id == contact and state.contact_deadline <= request.date+timedelta(minutes=5)
    message = api.messages[-1]
    value = GgCb(action='cap', chat=GROUP, user=MEMBER, arg=state.generation+'.0.'+state.answer).pack()
    await send(env, bound_callback(value, message, MEMBER))
    assert not api.calls('ApproveChatJoinRequest') and api.calls('SendMessage')[-1].text == 'Request rules'
    message = api.messages[-1]
    accept = api.calls('SendMessage')[-1].reply_markup.inline_keyboard[-1][0].callback_data
    await send(env, bound_callback(accept, message, MEMBER))
    assert api.calls('ApproveChatJoinRequest')[-1].chat_id == GROUP and api.calls('ApproveChatJoinRequest')[-1].user_id == MEMBER
    assert await challenges.verified(env, GROUP, MEMBER)


async def test_expired_request_is_not_contacted_and_own_ban_blocks_approval(env, api):
    from aiogram.types import Chat, ChatJoinRequest

    from tests.bots.groupguard.test_groupguard import tg_user
    await env.extras['guard'].update_config(GROUP, captcha='button', cas=False)
    expired = ChatJoinRequest(chat=Chat(id=GROUP, type='supergroup'), from_user=tg_user(MEMBER), user_chat_id=MEMBER,
        date=utcnow()-timedelta(minutes=6))
    await send(env, Update(update_id=group_msg('unused', MEMBER).update_id, chat_join_request=expired))
    assert not api.calls('SendMessage') and not api.calls('ApproveChatJoinRequest')
    fresh = expired.model_copy(update={'date':utcnow()})
    await send(env, Update(update_id=group_msg('unused', MEMBER).update_id, chat_join_request=fresh))
    message = api.messages[-1]
    value = api.calls('SendMessage')[-1].reply_markup.inline_keyboard[0][0].callback_data
    await actions.punish(env, GROUP, MEMBER, 'ban', None, origin='manual')
    await send(env, bound_callback(value, message, MEMBER))
    assert not api.calls('ApproveChatJoinRequest') and not await challenges.verified(env, GROUP, MEMBER)


async def test_verification_memory_voluntary_leave_and_admin_kick(env, api):
    from aiogram.types import ChatMemberBanned, ChatMemberLeft

    from tests.bots.groupguard.test_groupguard import tg_user
    await env.extras['guard'].update_config(GROUP, cas=False)
    joined = join_update(MEMBER)
    await send(env, joined)
    message = api.messages[-1]
    value = api.calls('SendMessage')[-1].reply_markup.inline_keyboard[0][0].callback_data
    await send(env, bound_callback(value, message, MEMBER))
    assert await challenges.verified(env, GROUP, MEMBER)
    left = joined.chat_member.model_copy(update={'old_chat_member':joined.chat_member.new_chat_member,
        'new_chat_member':ChatMemberLeft(user=tg_user(MEMBER))})
    await send(env, Update(update_id=group_msg('unused', MEMBER).update_id, chat_member=left))
    assert await challenges.verified(env, GROUP, MEMBER)
    kicked = left.model_copy(update={'from_user':tg_user(ADMIN),
        'new_chat_member':ChatMemberBanned(user=tg_user(MEMBER), until_date=utcnow()+timedelta(hours=1))})
    await send(env, Update(update_id=group_msg('unused', MEMBER).update_id, chat_member=kicked))
    assert not await challenges.verified(env, GROUP, MEMBER)


async def test_welcome_dependency_and_disabled_captcha_preserve_saved_content(env, api):
    await env.extras['guard'].update_config(GROUP, welcome=False, welcome_text='<b>Saved</b>', cas=False, captcha_enabled=False)
    await send(env, group_msg('/captcha on', ADMIN))
    cfg = await env.extras['guard'].config(GROUP)
    assert not cfg.captcha_enabled and cfg.welcome_text == '<b>Saved</b>'
    await send(env, join_update(MEMBER))
    assert not api.calls('RestrictChatMember')
    await send(env, group_msg('/welcome on', ADMIN))
    await send(env, group_msg('/captcha on', ADMIN))
    assert (await env.extras['guard'].config(GROUP)).effective_captcha() == 'button'


async def test_issued_challenge_does_not_change_with_later_settings_or_other_child(env, api):
    await env.extras['guard'].update_config(GROUP, captcha='text', cas=False)
    await send(env, join_update(MEMBER))
    link = api.calls('SendMessage')[-1].reply_markup.inline_keyboard[0][0].url.split('start=')[1]
    await send(env, pm('/start '+link))
    state = await verification.state_of(env, GROUP, MEMBER)
    message = api.messages[-1]
    data = GgCb(action='cap',chat=GROUP,user=MEMBER,arg=state.generation+'.0.'+state.answer).pack()
    await env.extras['guard'].update_config(GROUP, captcha='off', captcha_kick=False)
    for other in env.extras['test_contexts']:
        if other.bot_id == env.bot_id:
            continue
        before = len(api.calls('RestrictChatMember'))
        await send(other, bound_callback(data, message, MEMBER))
        assert len(api.calls('RestrictChatMember')) == before
    await send(env, bound_callback(data, message.model_copy(update={'message_id':message.message_id+1}), MEMBER))
    assert not await challenges.verified(env, GROUP, MEMBER)
    await send(env, bound_callback(data, message, MEMBER))
    assert await challenges.verified(env, GROUP, MEMBER)


async def test_promoted_target_is_not_punished_and_owned_cap_mute_is_retired(env, api):
    from tests.bots.groupguard.test_phase01a import admin_member
    await env.extras['guard'].update_config(GROUP, cas=False)
    await send(env, join_update(MEMBER))
    state = await verification.state_of(env, GROUP, MEMBER)
    original = api.responses['GetChatMember']
    api.responses['GetChatMember'] = lambda m: admin_member(MEMBER) if m.user_id==MEMBER else original(m)
    result = await challenges.expire(env, GROUP, MEMBER, state.generation, force=True)
    assert result.status == 'noop' and not api.calls('BanChatMember')
    async with env.sm() as session:
        assert await session.get(GuardRestriction, (env.bot_id,GROUP,MEMBER,'captcha')) is None


async def test_interrupted_issuance_refunds_only_transient_ownership(env, api):
    from bots.groupguard.chatconfig import ChatConfig
    cfg = ChatConfig(cas=False)
    prompt = captcha_modes.question('button')
    generation = await challenges.begin(env, GROUP, MEMBER, cfg, mode='button', answer='0',
        deadline=utcnow()+timedelta(minutes=5), prompt=prompt.to_dict())
    await actions.punish(env, GROUP, MEMBER, 'mute', None, origin='manual')
    await actions.punish(env, GROUP, MEMBER, 'mute', None, source='captcha', generation=generation)
    async with env.sm() as session:
        await session.execute(update(GuardChallenge).where(GuardChallenge.bot_id==env.bot_id,
            GuardChallenge.chat_id==GROUP, GuardChallenge.user_id==MEMBER).values(created_at=utcnow()-timedelta(seconds=241)))
        await session.commit()
    before = len(api.calls('RestrictChatMember'))
    assert await challenges.recover_claims(env) == 1
    assert await durable.sweep(env) == 1
    assert (await verification.state_of(env, GROUP, MEMBER)).status == 'refunded'
    assert not await challenges.verified(env, GROUP, MEMBER) and len(api.calls('RestrictChatMember')) == before
    async with env.sm() as session:
        assert await session.get(GuardRestriction, (env.bot_id,GROUP,MEMBER,'manual')) is not None
        assert await session.get(GuardRestriction, (env.bot_id,GROUP,MEMBER,'captcha')) is None
