"""Federation intent/enforcement effects use real dispatchers and shared-server member state."""

from types import SimpleNamespace

from aiogram.types import ChatMemberBanned
from sqlalchemy import select, update

from bots.groupguard import durable, fed_bans, fed_enforcement, fed_graph, federations
from bots.groupguard.contracts import Actor
from bots.groupguard.models import GuardJob, GuardRestriction
from core.db.base import utcnow
from tests.bots.groupguard.test_groupguard import ADMIN, GROUP, gctx, tg_user
from tests.bots.groupguard.test_phase01a import env

__all__ = ['env', 'gctx']


def actual_bans(api):
    banned = set()
    prior = api.responses['GetChatMember']
    api.responses['GetChatMember'] = lambda m: ChatMemberBanned(user=tg_user(m.user_id), until_date=0) if (
        m.chat_id, m.user_id) in banned else prior(m)

    def ban(method):
        banned.add((method.chat_id, method.user_id))
        return True

    def unban(method):
        banned.discard((method.chat_id, method.user_id))
        return True

    api.responses['BanChatMember'] = ban
    api.responses['UnbanChatMember'] = unban
    return banned


async def network(env, owner=ADMIN, name='Effect federation'):
    actor = Actor(env.bot_id, owner, 'human', owner)
    fed = await federations.create(env, actor, name)
    await federations.membership(env, Actor(env.bot_id, GROUP, 'human', ADMIN), fed.id)
    return actor, fed


async def drain(env):
    for _ in range(20):
        async with env.sm() as session:
            count = list((await session.execute(select(GuardJob.id).where(GuardJob.bot_id == env.bot_id,
                GuardJob.kind.in_({'fed_fanout', 'fed_enforce'}), GuardJob.status == 'pending'))).scalars())
            if not count:
                return
            await session.execute(update(GuardJob).where(GuardJob.id.in_(count)).values(run_at=utcnow()))
            await session.commit()
        await durable.sweep(env, limit=200)
    raise AssertionError('Bounded federation jobs did not finish')


async def test_owned_fban_and_unban_real_observed_effects(env, api):
    actual_bans(api)
    actor, fed = await network(env)
    await fed_enforcement.observe(env, GROUP, tg_user(30))
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30, 'Evidence'), active=True)
    await drain(env)
    assert len(api.calls('BanChatMember')) == 1 and api.calls('BanChatMember')[0].user_id == 30
    async with env.sm() as session:
        owned = await session.get(GuardRestriction, (env.bot_id, GROUP, 30, 'fed:' + fed.id))
        assert owned.state == 'applied' and owned.generation == '1'
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30), active=False)
    await drain(env)
    assert len(api.calls('UnbanChatMember')) == 1
    async with env.sm() as session:
        assert await session.get(GuardRestriction, (env.bot_id, GROUP, 30, 'fed:' + fed.id)) is None


async def test_old_ban_job_cannot_overtake_new_unban_and_unobserved_not_enumerated(env, api):
    actual_bans(api)
    actor, fed = await network(env)
    await fed_enforcement.observe(env, GROUP, tg_user(30))
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30, 'Old'), active=True)
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30), active=False)
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(31, 'Never seen'), active=True)
    await drain(env)
    assert not api.calls('BanChatMember') and not api.calls('UnbanChatMember')


async def test_subscribed_policy_and_multiple_sources_preserve_remaining_ban(env, api):
    actual_bans(api)
    actor, root = await network(env)
    owner = Actor(env.bot_id, 20, 'human', 20)
    subscribed = await federations.create(env, owner, 'Subscribed source')
    await fed_graph.change(env, actor, root.id, subscribed.id, subscribe=True)
    await fed_enforcement.observe(env, GROUP, tg_user(30))
    await fed_bans.change(env, actor, root.id, fed_bans.BanInput(30, 'Direct'), active=True)
    await fed_bans.change(env, owner, subscribed.id, fed_bans.BanInput(30, 'Subscribed'), active=True)
    await drain(env)
    assert len(api.calls('BanChatMember')) == 1
    await fed_bans.change(env, owner, subscribed.id, fed_bans.BanInput(30), active=False)
    await drain(env)
    assert not api.calls('UnbanChatMember')
    async with env.sm() as session:
        assert await session.get(GuardRestriction, (env.bot_id, GROUP, 30, 'fed:' + root.id)) is not None
        assert await session.get(GuardRestriction, (env.bot_id, GROUP, 30, 'fed:' + subscribed.id)) is None
    await fed_bans.change(env, actor, root.id, fed_bans.BanInput(30), active=False)
    await drain(env)
    assert len(api.calls('UnbanChatMember')) == 1


async def test_dispatcher_group_fed_role_private_connection_and_reason_required(env, api):
    from bots.groupguard.models import GuardFedBan
    from tests.bots.groupguard.test_groupguard import group_msg
    from tests.bots.groupguard.test_phase01a import send
    from tests.bots.groupguard.test_phase03 import pm

    _actor, owned = await network(env)
    another = await federations.create(env, Actor(env.bot_id, 20, 'human', 20), 'Group federation')
    await federations.membership(env, Actor(env.bot_id, GROUP, 'human', ADMIN), another.id)
    await send(env, group_msg('/fban 30 Local creator is not fed owner', ADMIN))
    async with env.sm() as session:
        assert await session.get(GuardFedBan, (env.bot_id, another.id, 30)) is None
    await send(env, group_msg('/fban 30 Fed owner is not local admin', 20))
    async with env.sm() as session:
        assert (await session.get(GuardFedBan, (env.bot_id, another.id, 30))).active
    await send(env, pm('/connect ' + str(GROUP), ADMIN))
    await send(env, pm('/fedreason on', ADMIN))
    await send(env, pm('/fban 31', ADMIN))
    async with env.sm() as session:
        assert await session.get(GuardFedBan, (env.bot_id, owned.id, 31)) is None
    await send(env, pm('/fban 31 Private owned target', ADMIN))
    async with env.sm() as session:
        assert (await session.get(GuardFedBan, (env.bot_id, owned.id, 31))).reason == 'Private owned target'
        assert await session.get(GuardFedBan, (env.bot_id, another.id, 31)) is None


async def test_passive_speech_beats_approval_and_quiet_does_not_disable_enforcement(env, api):
    from tests.bots.groupguard.test_groupguard import group_msg
    from tests.bots.groupguard.test_phase01a import send

    banned = actual_bans(api)
    actor, fed = await network(env)
    await env.extras['guard'].approve(GROUP, 30, None, ADMIN)
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30, '<reason>'), active=True)
    before = len(api.calls('SendMessage'))
    await send(env, group_msg('Actual speaking', 30))
    assert (GROUP, 30) in banned
    notice = api.calls('SendMessage')[-1].text
    assert fed.id in notice and '&lt;reason&gt;' in notice
    assert len(api.calls('SendMessage')) == before + 1
    await federations.membership(env, Actor(env.bot_id, GROUP, 'human', ADMIN), None, quiet=True)
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(31, 'Quiet'), active=True)
    before = len(api.calls('SendMessage'))
    await send(env, group_msg('Quiet still enforced', 31))
    assert (GROUP, 31) in banned and len(api.calls('SendMessage')) == before


async def test_transport_unknown_not_replayed_and_external_manual_ban_not_unbanned(env, api):
    from aiogram.exceptions import TelegramNetworkError

    from bots.groupguard import actions

    actual_bans(api)
    actual_response = api.responses['BanChatMember']
    actor, fed = await network(env)
    await fed_enforcement.observe(env, GROUP, tg_user(30))
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30, 'Unknown'), active=True)
    api.responses['BanChatMember'] = lambda m: TelegramNetworkError(method=m, message='unknown response')
    await drain(env)
    before = len(api.calls('BanChatMember'))
    await durable.recover(env)
    await durable.sweep(env)
    assert len(api.calls('BanChatMember')) == before
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30), active=False)
    await drain(env)
    assert not api.calls('UnbanChatMember')
    async with env.sm() as session:
        assert (await session.get(GuardRestriction, (env.bot_id, GROUP, 30, 'fed:' + fed.id))).state == 'uncertain'
    api.responses['BanChatMember'] = actual_response
    await actions.punish(env, GROUP, 31, 'ban', None, source='manual')
    await fed_enforcement.observe(env, GROUP, tg_user(31))
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(31, 'Other owner'), active=True)
    await drain(env)
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(31), active=False)
    await drain(env)
    assert not api.calls('UnbanChatMember')
    async with env.sm() as session:
        assert await session.get(GuardRestriction, (env.bot_id, GROUP, 31, 'manual')) is not None


async def test_directed_graph_cycles_self_and_namespace_are_denied(env):
    import pytest

    actor, fed = await network(env)
    other_actor = Actor(env.bot_id, 20, 'human', 20)
    another = await federations.create(env, other_actor, 'Second node')
    with pytest.raises(federations.FedError, match='cycle'):
        await fed_graph.change(env, actor, fed.id, fed.id, subscribe=True)
    await fed_graph.change(env, actor, fed.id, another.id, subscribe=True)
    with pytest.raises(federations.FedError, match='cycle'):
        await fed_graph.change(env, other_actor, another.id, fed.id, subscribe=True)
    assert [row.id for row in await fed_graph.subscriptions(env, fed.id)] == [another.id]
    for sibling in env.extras['test_contexts']:
        if sibling.bot_id != env.bot_id:
            with pytest.raises(federations.FedError, match='missing'):
                await fed_graph.change(sibling, Actor(sibling.bot_id, ADMIN, 'human', ADMIN), fed.id,
                    another.id, subscribe=True)


async def test_import_csv_jsonl_real_validation_atomicity_duplicates_and_rate(env, api):
    import pytest

    from bots.groupguard import fed_files
    from bots.groupguard.models import GuardFedBan

    actor, fed = await network(env)
    invalid = b'{"user_id":30,"reason":"First"}\n{"user_id":true,"reason":"Bad"}\n'
    with pytest.raises(federations.FedError):
        await fed_files.import_rows(env, actor, fed.id, invalid, 'input.ndjson')
    async with env.sm() as session:
        assert await session.get(GuardFedBan, (env.bot_id, fed.id, 30)) is None
    body = b'{"user_id":30,"reason":"First"}\n{"user_id":30,"reason":"First"}\n{"user_id":31,"reason":"Second"}\n'
    parsed = await fed_files.import_rows(env, actor, fed.id, body, 'input.jsonl')
    assert len(parsed.rows) == 2 and parsed.duplicates == 1
    with pytest.raises(federations.FedError, match='file_rate'):
        await fed_files.export(env, actor, fed.id, 'minicsv')
    await env.redis.delete(env.keys('fed_file_interval', fed.id))
    exported = await fed_files.export(env, actor, fed.id, 'minicsv')
    assert exported.data.startswith(b'id,reason\n') and b'30,First' in exported.data
    with pytest.raises(federations.FedError, match='file_duplicate'):
        fed_files.parse(env, b'{"user_id":30,"reason":"A"}\n{"user_id":30,"reason":"B"}\n', 'bad.jsonl')
    with pytest.raises(federations.FedError, match='file_format'):
        fed_files.parse(env, b'[{"user_id":32}]', 'array.jsonl')
    with pytest.raises(federations.FedError, match='file_format'):
        fed_files.parse(env, b'id,reason\n32\n', 'short.csv')
    for kind in ['csv', 'json']:
        await env.redis.delete(env.keys('fed_file_interval', fed.id))
        export = await fed_files.export(env, actor, fed.id, kind)
        assert [row.user_id for row in fed_files.parse(env, export.data, export.filename).rows] == [30, 31]


async def test_federation_delete_and_leave_preserve_remote_bans_retire_only_fed_source(env, api):
    from bots.groupguard import actions

    banned = actual_bans(api)
    actor, fed = await network(env)
    await fed_enforcement.observe(env, GROUP, tg_user(30))
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30, 'Owned'), active=True)
    await drain(env)
    await actions.punish(env, GROUP, 31, 'ban', None, source='manual')
    await federations.change(env, actor, fed.id, federations.Change('delete', expected_revision=fed.revision))
    assert not api.calls('UnbanChatMember') and (GROUP, 30) in banned
    async with env.sm() as session:
        assert await session.get(GuardRestriction, (env.bot_id, GROUP, 30, 'fed:' + fed.id)) is None
        assert await session.get(GuardRestriction, (env.bot_id, GROUP, 31, 'manual')) is not None
    assert (await actions.unban(env, GROUP, 30, origin='manual')).primary_completed
    actor, fresh = await network(env, name='New membership')
    await fed_bans.change(env, actor, fresh.id, fed_bans.BanInput(30, 'Leave'), active=True)
    await drain(env)
    prior = len(api.calls('UnbanChatMember'))
    await federations.membership(env, Actor(env.bot_id, GROUP, 'human', ADMIN), None)
    assert len(api.calls('UnbanChatMember')) == prior and (GROUP, 30) in banned


async def test_queued_issuer_demotion_and_bot_right_revocation_deny_actual_effects(env, api):
    from tests.bots.groupguard.test_phase01a import admin_member

    actual_bans(api)
    actor, fed = await network(env)
    await federations.change(env, actor, fed.id, federations.Change('promote', 20))
    await fed_enforcement.observe(env, GROUP, tg_user(30))
    await fed_bans.change(env, Actor(env.bot_id, 20, 'human', 20), fed.id,
        fed_bans.BanInput(30, 'Issuer later revoked'), active=True)
    await federations.change(env, actor, fed.id, federations.Change('demote', 20))
    await drain(env)
    # New membership may apply committed policy. Isolate the revoked issuer's own active jobs.
    async with env.sm() as session:
        revoked = list((await session.execute(select(GuardJob).where(GuardJob.bot_id == env.bot_id,
            GuardJob.kind == 'fed_fanout', GuardJob.user_id == 30))).scalars())
        assert revoked and all(j.status == 'cancelled' for j in revoked)
    await fed_enforcement.observe(env, GROUP, tg_user(31))
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(31, 'Rights revoked'), active=True)
    original = api.responses['GetChatMember']
    api.responses['GetChatMember'] = lambda m: admin_member(env.bot_id, can_restrict_members=False).model_copy(
        update={'user': tg_user(env.bot_id).model_copy(update={'is_bot': True})}) if m.user_id == env.bot_id else original(m)
    await drain(env)
    assert not any(m.user_id == 31 for m in api.calls('BanChatMember'))
    async with env.sm() as session:
        assert await session.get(GuardRestriction, (env.bot_id, GROUP, 31, 'fed:' + fed.id)) is None


async def test_new_join_and_pending_request_precede_captcha_with_semantic_decline(env, api):
    from aiogram.types import Chat, ChatJoinRequest, Update

    from tests.bots.groupguard.test_groupguard import join_update
    from tests.bots.groupguard.test_phase01a import send

    actual_bans(api)
    actor, fed = await network(env)
    await env.extras['guard'].update_config(GROUP, captcha='button')
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30, 'Join'), active=True)
    await send(env, join_update(30))
    assert any(m.user_id == 30 for m in api.calls('BanChatMember'))
    assert not api.calls('RestrictChatMember')
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(31, 'Request'), active=True)
    request = ChatJoinRequest(chat=Chat(id=GROUP, type='supergroup', title='Group'), from_user=tg_user(31),
        user_chat_id=31, date=utcnow())
    await send(env, Update(update_id=992200, chat_join_request=request))
    await send(env, Update(update_id=992201, chat_join_request=request))
    assert len(api.calls('DeclineChatJoinRequest')) == 1 and not api.calls('ApproveChatJoinRequest')


async def test_actual_file_reply_download_import_and_owner_document_export(env, api, monkeypatch):
    from aiogram.types import Document, File

    from bots.groupguard.models import GuardFedBan
    from tests.bots.groupguard.test_groupguard import plain
    from tests.bots.groupguard.test_phase01a import send
    from tests.bots.groupguard.test_phase03 import pm

    _actor, fed = await network(env)
    body = b'id,reason\n30,Downloaded evidence\n'
    api.responses['GetFile'] = File(file_id='import-file', file_unique_id='unique', file_path='documents/list.csv', file_size=len(body))

    async def download(file_path, destination, **kwargs):
        assert file_path == 'documents/list.csv'
        destination.write(body)
        return destination

    monkeypatch.setattr(env.bot, 'download_file', download)
    reply = plain(ADMIN).model_copy(update={'document': Document(file_id='import-file', file_unique_id='unique',
        file_name='list.csv', file_size=len(body))})
    request = pm('/importfbans', ADMIN)
    request = request.model_copy(update={'message': request.message.model_copy(update={'reply_to_message': reply})})
    await send(env, request)
    async with env.sm() as session:
        assert (await session.get(GuardFedBan, (env.bot_id, fed.id, 30))).reason == 'Downloaded evidence'
    await env.redis.delete(env.keys('fed_file_interval', fed.id))
    await send(env, pm('/fbanlist json', ADMIN))
    assert api.calls('SendDocument')[-1].document.filename.endswith('.json')
    before = len(api.calls('SendDocument'))
    await send(env, pm('/fbanlist csv', 20))
    assert len(api.calls('SendDocument')) == before


async def test_public_stats_forms_and_disabled_subscription_list(env, api):
    from tests.bots.groupguard.test_groupguard import group_msg
    from tests.bots.groupguard.test_phase01a import send
    from tests.bots.groupguard.test_phase03 import pm

    actor, fed = await network(env)
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30, 'Exact public reason'), active=True)
    await send(env, pm('/fedstat', 30))
    assert fed.id in api.calls('SendMessage')[-1].text
    await send(env, pm('/fbanstat ' + fed.id, 30))
    assert 'Exact public reason' in api.calls('SendMessage')[-1].text
    await send(env, group_msg('/fedstat 30 ' + fed.id, 20))
    assert 'Exact public reason' in api.calls('SendMessage')[-1].text
    other = await federations.create(env, Actor(env.bot_id, 20, 'human', 20), 'Subscription')
    await send(env, pm('/subfed ' + other.id, ADMIN))
    await send(env, group_msg('/fedsubs', 20))
    assert other.id in api.calls('SendMessage')[-1].text
    await send(env, group_msg('/disable fedsubs', ADMIN))
    before = len(api.calls('SendMessage'))
    await send(env, group_msg('/fedsubs', 20))
    assert len(api.calls('SendMessage')) == before
    await send(env, pm('/unsubfed ' + other.id, ADMIN))
    assert not await fed_graph.subscriptions(env, fed.id)


async def test_fban_after_issued_request_captcha_cannot_approve(env, api):
    from aiogram.types import Chat, ChatJoinRequest, Update

    from bots.groupguard import verification
    from bots.groupguard.keyboards import GgCb
    from tests.bots.groupguard.test_groupguard import bound_callback
    from tests.bots.groupguard.test_phase01a import send

    actor, fed = await network(env)
    await env.extras['guard'].update_config(GROUP, captcha='button', cas=False)
    request = ChatJoinRequest(chat=Chat(id=GROUP, type='supergroup'), from_user=tg_user(30),
        user_chat_id=30, date=utcnow())
    await send(env, Update(update_id=991177, chat_join_request=request))
    state = await verification.state_of(env, GROUP, 30)
    assert state is not None
    card = api.messages[-1]
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30, 'New policy'), active=True)
    value = GgCb(action='cap', chat=GROUP, user=30, arg=state.generation+'.0.'+state.answer).pack()
    await send(env, bound_callback(value, card, 30))
    assert not api.calls('ApproveChatJoinRequest') and not api.calls('RestrictChatMember')
    assert api.calls('DeclineChatJoinRequest')


async def test_passive_local_quota_defers_durable_effect_and_retry_after_restarts(env, api, monkeypatch):
    import time

    from aiogram.exceptions import TelegramRetryAfter

    banned = actual_bans(api)
    actor, fed = await network(env)
    await drain(env)
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30, 'Later enforcement'), active=True)
    now = time.time()
    # Passive enforcement must read the bucket seeded by this test.
    monkeypatch.setattr(fed_enforcement, 'time', SimpleNamespace(time=lambda: now))
    await env.redis.set(env.keys('guard_outbound_rate', int(now)), 100, ex=60)
    assert await fed_enforcement.passive(env, GROUP, tg_user(30), event='message:777001')
    assert not api.calls('BanChatMember')
    await env.redis.delete(env.keys('guard_outbound_rate', int(now)))
    original = api.responses['BanChatMember']
    api.responses['BanChatMember'] = lambda m: TelegramRetryAfter(method=m, message='known wait', retry_after=1)
    await durable.sweep(env)
    api.responses['BanChatMember'] = original
    await drain(env)
    assert (GROUP, 30) in banned


async def test_bounded_files_reject_excess_stream_and_records_before_any_change(env):
    import json

    import pytest

    from bots.groupguard import fed_files
    from bots.groupguard.models import GuardFedBan

    actor, fed = await network(env)
    buffer = fed_files.LimitedBuffer()
    buffer.write(b'a' * fed_files.MAX_BYTES)
    with pytest.raises(federations.FedError, match='file_limit'):
        buffer.write(b'x')
    body = json.dumps([{'user_id': n, 'reason': 'Bounded'} for n in range(100, 1101)]).encode()
    with pytest.raises(federations.FedError, match='file_limit'):
        await fed_files.import_rows(env, actor, fed.id, body, 'too-many.json')
    async with env.sm() as session:
        assert await session.get(GuardFedBan, (env.bot_id, fed.id, 100)) is None


async def test_inactive_uncertain_fed_source_never_becomes_new_rejoin_ban(env, api):
    from bots.groupguard import restrictions

    actor, fed = await network(env)
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30, 'Retired policy'), active=True)
    async with env.sm() as session:
        session.add(GuardRestriction(bot_id=env.bot_id, chat_id=GROUP, user_id=30,
            source='fed:' + fed.id, mode='ban', state='uncertain', generation='1'))
        await session.commit()
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30), active=False)
    mode, result = await restrictions.on_join(env, GROUP, 30)
    assert mode is None and result is None and not api.calls('BanChatMember')
    async with env.sm() as session:
        assert (await session.get(GuardRestriction, (env.bot_id, GROUP, 30, 'fed:' + fed.id))).state == 'uncertain'


async def test_spreadsheet_export_literal_values_roundtrip_and_nested_json_control(env):
    import pytest

    from bots.groupguard import fed_files

    actor, fed = await network(env)
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30, '=dangerous', '@name', '+handle'), active=True)
    file = await fed_files.export(env, actor, fed.id, 'csv')
    assert b"'=dangerous" in file.data and b"'@name" in file.data
    item = fed_files.parse(env, file.data, file.filename).rows[0]
    assert item.reason == '=dangerous' and item.first_name == '@name' and item.username == '+handle'
    with pytest.raises(federations.FedError, match='file_format'):
        fed_files.parse(env, b'[' * 2000 + b']' * 2000, 'nested.json')
