"""Actual federation role/context/confirmation API effects across standalone and two live registry children."""

from aiogram.types import ChatMemberMember
from sqlalchemy import select

from bots.groupguard import federations
from bots.groupguard.contracts import Actor
from bots.groupguard.models import GuardFedAdmin, GuardFedChat, GuardFederation
from tests.bots.groupguard.test_groupguard import (
    ADMIN,
    GROUP,
    MEMBER,
    bound_callback,
    gctx,
    group_msg,
    tg_user,
)
from tests.bots.groupguard.test_phase01a import env, send
from tests.bots.groupguard.test_phase03 import pm

__all__ = ['env', 'gctx']


def confirmation_card(api):
    request = next(m for m in reversed(api.calls('SendMessage')) if m.reply_markup)
    card = next(m for m in reversed(api.messages) if m.chat.id == request.chat_id and m.text == request.text)
    return card, request.reply_markup.inline_keyboard[0][0].callback_data


async def make(env, user=ADMIN, value='Example federation'):
    await send(env, pm('/newfed ' + value, user))
    row = await federations.owned(env, user)
    assert row is not None
    return row


async def test_fed_one_owner_namespace_names_private_context_and_connection(env, api):
    fed = await make(env, value='界' * 80)
    assert len(fed.name) == 64 and len(fed.id) == 36
    await send(env, pm('/newfed Duplicate', ADMIN))
    async with env.sm() as session:
        ids = list((await session.execute(select(GuardFederation.id).where(
            GuardFederation.bot_id == env.bot_id, GuardFederation.owner_id == ADMIN))).scalars())
        assert ids == [fed.id]
    another = await make(env, MEMBER, 'Other owned fed')
    await send(env, group_msg('/joinfed ' + another.id, ADMIN))
    await send(env, pm('/connect ' + str(GROUP), ADMIN))
    await send(env, pm('/renamefed My private federation', ADMIN))
    assert (await federations.get(env, fed.id)).name == 'My private federation'
    assert (await federations.get(env, another.id)).name == 'Other owned fed'
    await send(env, group_msg('/newfed Group creation', ADMIN))
    assert (await federations.get(env, fed.id)).name == 'My private federation'
    for other in env.extras['test_contexts']:
        if other.bot_id != env.bot_id:
            assert await federations.get(other, fed.id) is None
            await send(other, pm('/fedinfo ' + fed.id, ADMIN))
            assert fed.name not in api.calls('SendMessage')[-1].text


async def test_local_admin_fed_owner_group_creator_and_fed_admin_are_distinct(env, api):
    fed = await make(env, MEMBER)
    await send(env, group_msg('/joinfed ' + fed.id, MEMBER))
    assert await federations.attached(env, GROUP) is None
    await send(env, group_msg('/joinfed ' + fed.id, ADMIN))
    assert (await federations.attached(env, GROUP)).fed_id == fed.id
    await send(env, group_msg('/fedpromote 30', ADMIN))
    assert await federations.admins(env, fed.id) == [MEMBER]
    await send(env, group_msg('/fedpromote 30', MEMBER))
    assert await federations.admins(env, fed.id) == [MEMBER, 30]
    await send(env, group_msg('/leavefed', MEMBER))
    assert (await federations.attached(env, GROUP)).fed_id == fed.id
    await send(env, group_msg('/quietfed on', ADMIN))
    assert (await federations.attached(env, GROUP)).quiet
    await send(env, group_msg('/leavefed', ADMIN))
    assert await federations.attached(env, GROUP) is None
    assert await federations.admins(env, fed.id) == [MEMBER, 30]


async def test_fed_admin_self_removal_never_demotes_owner_or_confers_group_authority(env, api):
    fed = await make(env)
    await send(env, pm('/fedpromote 20', ADMIN))
    await send(env, pm('/feddemoteme ' + fed.id, 20))
    assert await federations.admins(env, fed.id) == [ADMIN]
    await send(env, pm('/feddemoteme ' + fed.id, ADMIN))
    assert (await federations.get(env, fed.id)).owner_id == ADMIN
    await send(env, pm('/fedpromote 20', ADMIN))
    await send(env, pm('/fedreason on', 20))
    assert not (await federations.get(env, fed.id)).reason_required
    await send(env, group_msg('/joinfed ' + fed.id, ADMIN))
    await send(env, group_msg('/ban 30 local group ban', 20))
    assert not api.calls('BanChatMember')


async def test_fed_deletion_personal_confirmation_wrong_actor_replay_retains_telegram_bans(env, api):
    fed = await make(env)
    await send(env, group_msg('/joinfed ' + fed.id, ADMIN))
    await send(env, pm('/fedpromote 20', ADMIN))
    await send(env, group_msg('/ban 20 Before delete', ADMIN))
    assert len(api.calls('BanChatMember')) == 1
    await send(env, pm('/delfed', ADMIN))
    card, value = confirmation_card(api)
    await send(env, bound_callback(value, card, MEMBER))
    assert await federations.get(env, fed.id) is not None
    for other in env.extras['test_contexts']:
        if other.bot_id != env.bot_id:
            await send(other, bound_callback(value, card, ADMIN))
            assert await federations.get(env, fed.id) is not None
    await send(env, bound_callback(value, card, ADMIN))
    assert await federations.get(env, fed.id) is None
    async with env.sm() as session:
        assert await session.get(GuardFedChat, (env.bot_id, GROUP)) is None
        assert await session.get(GuardFedAdmin, (env.bot_id, fed.id, 20)) is None
    assert not api.calls('UnbanChatMember')
    before = len(api.calls('SendMessage'))
    await send(env, bound_callback(value, card, ADMIN))
    assert len(api.calls('SendMessage')) == before


async def test_fed_stale_confirmation_after_rename_and_revoked_log_destination(env, api):
    fed = await make(env)
    await send(env, pm('/delfed', ADMIN))
    card, value = confirmation_card(api)
    await send(env, pm('/renamefed New generation', ADMIN))
    await send(env, bound_callback(value, card, ADMIN))
    assert await federations.get(env, fed.id) is not None
    await send(env, pm('/setfedlog ' + str(GROUP), ADMIN))
    card, value = confirmation_card(api)
    prior = api.responses['GetChatMember']
    api.responses['GetChatMember'] = lambda m: ChatMemberMember(user=tg_user(ADMIN)) if m.user_id == ADMIN else prior(m)
    await send(env, bound_callback(value, card, ADMIN))
    assert (await federations.get(env, fed.id)).log_chat_id is None


async def test_fed_notifications_off_preserves_log_and_failure_is_visible(env, api):
    from aiogram.exceptions import TelegramForbiddenError

    fed = await make(env)
    await send(env, pm('/setfedlog ' + str(GROUP), ADMIN))
    card, value = confirmation_card(api)
    await send(env, bound_callback(value, card, ADMIN))
    assert (await federations.get(env, fed.id)).log_chat_id == GROUP
    await send(env, pm('/fednotif off', ADMIN))
    before = len(api.calls('SendMessage'))
    await send(env, pm('/fedpromote 20', ADMIN))
    new = api.calls('SendMessage')[before:]
    assert any(m.chat_id == GROUP and fed.id in m.text for m in new)
    assert len([m for m in new if m.chat_id == ADMIN]) == 1  # Command response, no owner notification.
    api.responses['SendMessage'] = lambda m: TelegramForbiddenError(method=m, message='log refused')
    # Use the service to preserve the real command effect even when log transport fails.
    _, result = await federations.change(env, Actor(env.bot_id, ADMIN, 'human', ADMIN), fed.id,
        federations.Change('reason', True))
    assert (await federations.get(env, fed.id)).reason_required
    assert result.status == 'failed' and result.steps[0].operation == 'fed_log'


async def test_fed_bot_and_anonymous_sources_never_gain_owner_roles(env, api):
    from tests.bots.groupguard.test_phase08 import bot_command

    await make(env)
    await env.extras['guard'].update_config(GROUP, bot2bot_mode='all', anonadmin=True)
    await send(env, bot_command('/fedpromote 20'))
    actor = Actor(env.bot_id, GROUP, 'anonymous_group', sender_chat_id=GROUP)
    try:
        await federations.change(env, actor, (await federations.owned(env, ADMIN)).id,
            federations.Change('promote', 20))
    except federations.FedError:
        pass
    else:
        raise AssertionError('Anonymous federation ownership accepted')
    assert await federations.admins(env, (await federations.owned(env, ADMIN)).id) == [ADMIN]


async def test_channel_log_owner_confirmation_uses_actual_source_and_current_post_right(env, api):
    from aiogram.types import Chat, Message, Update

    from core.db.base import utcnow

    fed = await make(env)
    channel_id = -100990088
    original_chat = api.responses['GetChat']
    original_member = api.responses['GetChatMember']
    api.responses['GetChat'] = lambda m: original_chat(m).model_copy(update={'type': 'channel'}) if m.chat_id == channel_id else original_chat(m)
    from tests.bots.groupguard.test_phase01a import admin_member
    api.responses['GetChatMember'] = lambda m: admin_member(env.bot_id, can_post_messages=True).model_copy(
        update={'user': tg_user(env.bot_id).model_copy(update={'is_bot': True})}) if m.user_id == env.bot_id else original_member(m)
    source = Message(message_id=7788, date=utcnow(), chat=Chat(id=channel_id, type='channel', title='Fed log'),
        text='/setfedlog ' + fed.id, sender_chat=Chat(id=channel_id, type='channel', title='Fed log'))
    await send(env, Update(update_id=881100, channel_post=source))
    card, value = confirmation_card(api)
    assert card.chat.id == ADMIN
    assert (await federations.get(env, fed.id)).log_chat_id is None
    await send(env, bound_callback(value, card, MEMBER))
    assert (await federations.get(env, fed.id)).log_chat_id is None
    await send(env, bound_callback(value, card, ADMIN))
    assert (await federations.get(env, fed.id)).log_chat_id == channel_id
    audit = await env.audit.recent(30)
    confirmation = next(row for row in audit if row.action == 'gg_fed_confirmation')
    assert confirmation.details['source_chat_id'] == channel_id and confirmation.details['source_message_id'] == 7788


async def test_fed_public_reads_disable_policy_and_explicit_private_context(env, api):
    fed = await make(env)
    await send(env, group_msg('/joinfed ' + fed.id, ADMIN))
    await send(env, group_msg('/fedinfo', MEMBER))
    assert fed.id in api.calls('SendMessage')[-1].text
    await send(env, group_msg('/chatfed', MEMBER))
    assert fed.name in api.calls('SendMessage')[-1].text
    await send(env, pm('/fedadmins ' + fed.id, MEMBER))
    assert str(ADMIN) in api.calls('SendMessage')[-1].text
    await send(env, pm('/fedpromote 30', ADMIN))
    await send(env, pm('/myfeds', 30))
    assert fed.id in api.calls('SendMessage')[-1].text
    await send(env, pm('/feddemote 30', ADMIN))
    await send(env, pm('/myfeds', 30))
    assert fed.id not in api.calls('SendMessage')[-1].text
    await send(env, group_msg('/disable fedinfo fedadmins', ADMIN))
    before = len(api.calls('SendMessage'))
    await send(env, group_msg('/fedinfo ' + fed.id, MEMBER))
    await send(env, group_msg('/fedadmins ' + fed.id, MEMBER))
    assert len(api.calls('SendMessage')) == before
    await send(env, pm('/connect ' + str(GROUP), MEMBER))
    await send(env, pm('/fedinfo ' + fed.id, MEMBER))
    assert fed.id in api.calls('SendMessage')[-1].text  # Explicit public fed read keeps actual PM context.


async def test_cancelled_and_expired_federation_confirmation_never_deletes(env, api):
    from bots.groupguard.keyboards import GgCb

    fed = await make(env)
    await send(env, pm('/delfed', ADMIN))
    card, value = confirmation_card(api)
    parsed = GgCb.unpack(value)
    cancelled = GgCb(action='fx', chat=parsed.chat, arg=parsed.arg).pack()
    await send(env, bound_callback(cancelled, card, ADMIN))
    await send(env, bound_callback(value, card, ADMIN))
    assert await federations.get(env, fed.id) is not None
    await send(env, pm('/delfed', ADMIN))
    card, value = confirmation_card(api)
    parsed = GgCb.unpack(value)
    await env.redis.delete(env.keys('fed_confirm', parsed.arg))
    await send(env, bound_callback(value, card, ADMIN))
    assert await federations.get(env, fed.id) is not None
    assert not api.calls('UnbanChatMember')


async def test_federation_inactive_child_or_owned_cleanup_has_no_authority(env, api):
    from sqlalchemy import update

    from core.db.models import ChildBot

    fed = await make(env)
    if env.child is not None:
        async with env.sm() as session:
            await session.execute(update(ChildBot).where(ChildBot.bot_id == env.bot_id).values(status='paused'))
            await session.commit()
    else:
        env.extras['owned_maintenance'] = True
    await send(env, pm('/fedpromote 30', ADMIN))
    assert await federations.admins(env, fed.id) == [ADMIN]
    assert not api.calls('BanChatMember')
    if env.child is None:
        env.extras.pop('owned_maintenance')


async def test_absent_confirmation_message_receipt_never_authorizes_deletion(env, api):
    fed = await make(env)
    api.responses['SendMessage'] = True
    await send(env, pm('/delfed', ADMIN))
    assert await federations.get(env, fed.id) is not None
    tokens = [key async for key in env.redis.scan_iter(match=env.keys('fed_confirm', '*'))]
    assert not tokens


async def test_actual_anonymous_and_bot_admin_commands_cannot_gain_fed_ownership(env, api):
    from aiogram.types import Chat

    from tests.bots.groupguard.test_phase08 import bot_admin, bot_command

    fed = await make(env)
    await send(env, group_msg('/joinfed ' + fed.id, ADMIN))
    await env.extras['guard'].update_config(GROUP, bot2bot_mode='admin', anonadmin=True, bot2bot_skip_review=True)
    bot_admin(api)
    await send(env, bot_command('/fedpromote 30'))
    await send(env, group_msg('/fedpromote 30', ADMIN,
        sender_chat=Chat(id=GROUP, type='supergroup', title='Club')))
    assert await federations.admins(env, fed.id) == [ADMIN]
