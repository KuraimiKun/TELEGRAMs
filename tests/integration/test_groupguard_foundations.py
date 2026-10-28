"""Distributed Group Guard foundations on an explicitly disposable PostgreSQL database."""

import asyncio
import os
from datetime import timedelta

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bots.groupguard import actions, challenges, durable, repeats
from bots.groupguard.models import GuardChallenge, GuardItem, GuardJob, GuardRepeat, GuardRestriction
from bots.groupguard.service import GuardService
from core.db.base import Base, utcnow
from core.db.models import Bot as BotRecord
from core.db.models import User as UserRecord
from core.sdk.registry import discover
from tests.bots.groupguard import test_phase01c as foundations
from tests.bots.groupguard.test_groupguard import ADMIN, GROUP, MEMBER, bound_callback, gctx
from tests.bots.groupguard.test_phase01a import env
from tests.bots.groupguard.test_phase01c import issue

__all__ = ["env", "gctx"]
pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_GG_DATABASE_URL") or not os.environ.get("TEST_GG_REDIS_URL"),
    reason="TEST_GG_DATABASE_URL and TEST_GG_REDIS_URL required for distributed Group Guard foundations",
)


@pytest.fixture
async def redis():
    from urllib.parse import urlparse

    from redis.asyncio import Redis
    url = os.environ["TEST_GG_REDIS_URL"]
    parsed = urlparse(url)
    assert parsed.hostname in {"localhost", "127.0.0.1"} and parsed.port == 56380 and parsed.path == "/2"
    client = Redis.from_url(url)
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.fixture
async def sm():
    url = os.environ["TEST_GG_DATABASE_URL"]
    engine = create_async_engine(url, pool_size=12, max_overflow=12)
    assert engine.url.host in {"127.0.0.1", "localhost"} and engine.url.database.startswith("gg_long_")
    discover()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        session.add(BotRecord(id=123456, slug="socialdownload", title="Test", active=True))
        session.add(UserRecord(id=777, first_name="Factory owner", language_code="en"))
        await session.commit()
    yield maker
    await engine.dispose()


async def test_pg_two_writers_preserve_fields_and_unknown_extension(env):
    one, two = env.extras["guard"], GuardService(env.sm, env.bot_id)
    await one.update_config(GROUP, external_extension={"opaque": "preserved"})

    async def edits(svc, name):
        for value in range(8):
            await svc.update_config(GROUP, **{name: value})

    await asyncio.gather(edits(one, "writer_one"), edits(two, "writer_two"))
    cfg = await one.config(GROUP)
    assert cfg.model_extra["writer_one"] == cfg.model_extra["writer_two"] == 7
    assert cfg.model_extra["external_extension"] == {"opaque": "preserved"}
    assert cfg._revision >= 17


async def test_pg_parallel_warning_claims_and_cutoff_preserve_later_history(env, api):
    svc = env.extras["guard"]
    await svc.update_config(GROUP, warn_limit=3)
    decisions = await asyncio.gather(
        *(
            durable.record_warning(
                env, GROUP, MEMBER, str(n), ADMIN, limit=3, action="ban", duration_seconds=None, name="Member"
            )
            for n in range(8)
        )
    )
    claimed = [d for d in decisions if d.job_id is not None]
    assert len(claimed) == 1
    results = await asyncio.gather(*(durable.execute_warning(env, claimed[0].job_id) for _ in range(8)))
    assert sum(r is not None for r in results) == 1 and len(api.calls("BanChatMember")) == 1
    assert await svc.count_warns(GROUP, MEMBER) == 5  # only the claimed cutoff's three warnings reset
    first = (await svc.list_warns(GROUP, MEMBER))[0]
    removed = await asyncio.gather(*(svc.remove_warning(GROUP, MEMBER, first.id) for _ in range(8)))
    assert sum(removed) == 1 and await svc.count_warns(GROUP, MEMBER) == 4


async def test_pg_answer_timeout_claim_and_restart_generation_fence(env, api, monkeypatch):
    state, message, data = await issue(env, api, monkeypatch)
    entered, release = asyncio.Event(), asyncio.Event()
    primitive = actions._unmute_api

    async def hold(*a, **kw):
        entered.set()
        await release.wait()
        return await primitive(*a, **kw)

    monkeypatch.setattr(actions, "_unmute_api", hold)
    query = bound_callback(data, message, 30).callback_query.as_(env.bot)
    answer = asyncio.create_task(challenges.answer(env, query, GROUP, 30, data.rsplit(":", 1)[1]))
    await asyncio.wait_for(entered.wait(), 5)
    async with env.sm() as session:
        claimed = await session.get(GuardChallenge, (env.bot_id, GROUP, 30))
    assert claimed.status == "answering"
    expiry = asyncio.create_task(challenges.expire(env, GROUP, 30, state.generation, force=True))
    release.set()
    accepted, expired = await asyncio.gather(answer, expiry)
    assert accepted.status == "accepted" and not expired.primary_completed and not api.calls("BanChatMember")
    # Verification memory means an ordinary rejoin does not issue again; explicit reset/reissue does.
    await challenges.reset(env, GROUP, 30, forget=True)
    replacement, _, _ = await issue(env, api, monkeypatch)
    assert replacement.generation != state.generation
    env.extras["guard"] = GuardService(env.sm, env.bot_id)  # another process/service view
    assert not (await challenges.expire(env, GROUP, 30, state.generation, force=True)).primary_completed
    assert not api.calls("BanChatMember")


async def test_pg_interrupted_dispatch_is_uncertain_and_not_repeated(env):
    jid = await durable.enqueue(
        env, "warning_expire", GROUP, user_id=MEMBER, dedupe_key="restart", payload={"warning_id": 99999}
    )
    owners = await asyncio.gather(*(durable.claim(env, jid) for _ in range(12)))
    owner = next(x for x in owners if x is not None)
    assert sum(x is not None for x in owners) == 1
    await durable.dispatched(env, owner)
    async with env.sm() as session:
        await session.execute(
            update(GuardJob).where(GuardJob.id == jid).values(lease_until=utcnow() - timedelta(seconds=1))
        )
        await session.commit()
    await durable.recover(env)
    assert await durable.claim(env, jid) is None
    async with env.sm() as session:
        row = await session.get(GuardJob, jid)
    assert row.status == "uncertain"


async def test_pg_redis_duplicate_delivery(env, api):
    await foundations.test_update_and_message_replay_do_not_warn_or_notify_twice(env, api)


async def test_pg_redis_recovery(env, api):
    await foundations.test_received_update_recovers_interrupted_processing_is_uncertain(env, api)


async def test_pg_redis_failed_api_retry_and_permission_revocation(env, api):
    await foundations.test_job_retry_and_revoked_warning_actor_preserve_history(env, api)


async def test_pg_redis_child_pause_restores_owned_night_and_fences_cached_runtime(env, api):
    await foundations.test_child_pause_fences_cached_dispatcher_and_releases_owned_night(env, api)


async def test_pg_interrupted_manual_mute_cannot_be_released_by_verification(env, api, monkeypatch):
    _state, message, data = await issue(env, api, monkeypatch)
    original = actions.perform

    async def interrupted(operation, call, **kwargs):
        result = await original(operation, call, **kwargs)
        if operation == "mute":
            raise asyncio.CancelledError
        return result

    monkeypatch.setattr(actions, "perform", interrupted)
    with pytest.raises(asyncio.CancelledError):
        await actions.punish(env, GROUP, 30, "mute", None, origin="manual")
    async with env.sm() as session:
        evidence = await session.get(GuardRestriction, (env.bot_id, GROUP, 30, "manual"))
        assert evidence.state == "pending" and evidence.until is None
        await session.execute(update(GuardRestriction).where(GuardRestriction.bot_id == env.bot_id,
            GuardRestriction.chat_id == GROUP, GuardRestriction.user_id == 30, GuardRestriction.source == "manual")
            .values(updated_at=utcnow() - timedelta(seconds=241)))
        await session.commit()
    await durable.recover(env)
    query = bound_callback(data, message, 30).callback_query.as_(env.bot)
    before = len(api.calls("RestrictChatMember"))
    result = await challenges.answer(env, query, GROUP, 30, data.rsplit(":", 1)[1])
    assert result.status == "accepted" and len(api.calls("RestrictChatMember")) == before
    async with env.sm() as session:
        evidence = await session.get(GuardRestriction, (env.bot_id, GROUP, 30, "manual"))
        assert evidence.state == "uncertain"


async def test_pg_repeat_distributed_claim_and_generation_replacement(env, api):
    from tests.bots.groupguard.test_groupguard import group_msg
    from tests.bots.groupguard.test_phase01a import send
    from tests.bots.groupguard.test_phase03 import make_due
    await send(env, group_msg("/save daily Durable {repeat 1m}", ADMIN))
    await make_due(env)
    await asyncio.gather(*(repeats.tick(env) for _ in range(8)))
    before = len(api.calls("SendMessage"))
    outcomes = await asyncio.gather(*(durable.sweep(env) for _ in range(8)))
    assert sum(outcomes) == 1 and len(api.calls("SendMessage")) == before + 1
    async with env.sm() as session:
        row = (await session.execute(select(GuardRepeat).where(GuardRepeat.bot_id == env.bot_id))).scalar_one()
        assert row.next_run > utcnow()
        old = row.generation
    await make_due(env)
    await asyncio.gather(*(repeats.tick(env) for _ in range(8)))
    await send(env, group_msg("/save daily Replaced {repeat 2m}", ADMIN))
    before = len(api.calls("SendMessage"))
    assert sum(await asyncio.gather(*(durable.sweep(env) for _ in range(8)))) == 0
    assert len(api.calls("SendMessage")) == before
    async with env.sm() as session:
        row = (await session.execute(select(GuardRepeat).where(GuardRepeat.bot_id == env.bot_id))).scalar_one()
        assert row.generation != old


async def test_pg_batch_content_quota_serializes_between_workers(env):
    from bots.groupguard.service import LimitReached
    one, two = env.extras["guard"], GuardService(env.sm, env.bot_id)
    async def batch(svc, keys):
        try:
            return await svc.save_items(GROUP, "filter", keys, text="Value", content_format="rose",
                media_kind=None, file_id=None, limit=3)
        except LimitReached:
            return None
    results = await asyncio.gather(batch(one, ["one", "two"]), batch(two, ["three", "four"]))
    assert sum(result is not None for result in results) == 1
    async with env.sm() as session:
        rows = list((await session.execute(select(GuardItem).where(GuardItem.bot_id == env.bot_id,
            GuardItem.chat_id == GROUP))).scalars())
    assert len(rows) == 2


async def test_pg_partial_captcha_kick_completes_owned_unban(env, api):
    from tests.bots.groupguard.test_phase04 import test_partial_timeout_kick_completes_only_owned_unban
    await test_partial_timeout_kick_completes_only_owned_unban(env, api)


async def test_pg_interrupted_captcha_issuance_preserves_manual_hold(env, api):
    from tests.bots.groupguard.test_phase04 import test_interrupted_issuance_refunds_only_transient_ownership
    await test_interrupted_issuance_refunds_only_transient_ownership(env, api)


async def test_pg_concurrent_semantic_join_deliveries_issue_once(env, api):
    from aiogram.types import Update

    from tests.bots.groupguard.test_groupguard import group_msg, join_update
    from tests.bots.groupguard.test_phase01a import send
    await env.extras['guard'].update_config(GROUP, cas=False)
    event = join_update(MEMBER).chat_member
    deliveries = [Update(update_id=group_msg('unique', MEMBER).update_id, chat_member=event) for _ in range(8)]
    await asyncio.gather(*(send(env, delivery) for delivery in deliveries))
    assert len(api.calls('RestrictChatMember')) == 1
    assert len([m for m in api.calls('SendMessage') if m.reply_markup and m.reply_markup.inline_keyboard[0][0].callback_data]) == 1


async def test_pg_lock_and_allowlist_deltas_do_not_overwrite_parallel_edits(env):
    from tests.bots.groupguard.test_groupguard import group_msg
    from tests.bots.groupguard.test_phase01a import send

    kinds = ["url", "photo", "cjk", "voice", "document", "emojicustom", "reaction", "contact"]
    await asyncio.gather(*(send(env, group_msg("/lock " + kind, ADMIN)) for kind in kinds))
    assert set(kinds) <= set((await env.extras["guard"].config(GROUP)).locks)
    await asyncio.gather(*(send(env, group_msg(f"/allowlist domain{i}.example", ADMIN)) for i in range(8)))
    assert len((await env.extras["guard"].config(GROUP)).allowlist) == 8


async def test_pg_semantic_reaction_receipt_removes_once(env, api):
    from aiogram.types import Update

    from tests.bots.groupguard.test_groupguard import group_msg
    from tests.bots.groupguard.test_phase01a import send
    from tests.bots.groupguard.test_phase05 import reaction

    await send(env, group_msg("/lock reaction", ADMIN))
    event = reaction()
    await asyncio.gather(
        *(
            send(env, Update(update_id=group_msg("unique", MEMBER).update_id, message_reaction=event))
            for _ in range(8)
        )
    )
    assert len(api.calls("DeleteMessageReaction")) == 1


async def test_pg_blocklist_parallel_deltas_and_review_intent_keep_unrelated_entries(env):
    from tests.bots.groupguard.test_groupguard import group_msg
    from tests.bots.groupguard.test_phase01a import send
    await asyncio.gather(*(send(env, group_msg(f'/addblocklist key{i}', ADMIN)) for i in range(8)))
    await asyncio.gather(*(send(env, group_msg(f'/rmblocklist key{i}', ADMIN)) for i in range(4)))
    cfg = await env.extras['guard'].config(GROUP)
    assert {entry['key'] for entry in cfg.blocklist_entries} == {'key4','key5','key6','key7'}


async def test_pg_legacy_blocklist_normalizes_without_losing_phrases_or_unknown_fields(env):
    from sqlalchemy import update

    from bots.groupguard.models import GuardChat
    svc = env.extras['guard']
    await svc.ensure_chat(GROUP)
    old = ['Casino*', 'café  bar', 'x'*500]
    async with env.sm() as session:
        await session.execute(update(GuardChat).where(GuardChat.bot_id==env.bot_id,GuardChat.chat_id==GROUP)
                              .values(config=dict(blocklist=old, blocklist_warn=True, opaque={'y': 2})))
        await session.commit()
    cfg = await svc.config(GROUP)
    assert cfg.blocklist == old and cfg.blocklist_mode == 'warn'
    assert [entry['pattern'] for entry in cfg.blocklist_entries] == old
    await svc.update_config(GROUP, reports=False)
    cfg = await svc.config(GROUP)
    assert cfg.blocklist == old and cfg.model_extra['opaque'] == {'y':2}
    assert [entry['pattern'] for entry in cfg.blocklist_entries] == old


async def test_pg_parallel_raid_activation_has_one_current_owning_job(env):
    from bots.groupguard import raids
    from bots.groupguard.models import GuardJob, GuardRaid
    await asyncio.gather(*(raids.change(env,GROUP,600+n) for n in range(8)))
    async with env.sm() as session:
        raid=await session.get(GuardRaid,(env.bot_id,GROUP))
        jobs=list((await session.execute(select(GuardJob).where(GuardJob.bot_id==env.bot_id,
            GuardJob.kind=='raid_expire',GuardJob.status=='pending'))).scalars())
    assert len(jobs)==1 and jobs[0].generation==raid.generation and jobs[0].run_at==raid.deadline


async def test_pg_real_redis_parallel_flood_actual_actions_not_counter_only(env,api):
    from tests.bots.groupguard.test_groupguard import group_msg
    from tests.bots.groupguard.test_phase01a import send
    await env.extras['guard'].update_config(GROUP,flood_consecutive_count=5)
    await asyncio.gather(*(send(env,group_msg('flood '+str(n),MEMBER)) for n in range(20)))
    calls=api.calls('RestrictChatMember')
    assert len(calls)==4 and all(call.user_id==MEMBER and not call.permissions.can_send_messages for call in calls)
    assert len(api.calls('DeleteMessage'))==4


async def test_pg_durable_sweep_cursor_replicas_do_not_duplicate_pages(env):
    from bots.groupguard import fair_sweeps
    from bots.groupguard.models import GuardChat
    async with env.sm() as session:
        session.add_all([GuardChat(bot_id=env.bot_id,chat_id=-100000-n,night=True,config={}) for n in range(240)])
        await session.commit()
    query=select(GuardChat.chat_id).where(GuardChat.bot_id==env.bot_id,GuardChat.night.is_(True))
    pages=await asyncio.gather(*(fair_sweeps.batch(env.sm,env.bot_id,'race_sweep',0,query,GuardChat.chat_id,limit=20) for _ in range(8)))
    ids=[value for page in pages for value in page]
    assert len(ids)==len(set(ids))==160


async def test_pg_connection_concurrent_switches_keep_one_active_and_lastfive(env):
    from bots.groupguard import connections
    await asyncio.gather(*(connections.change(env,MEMBER,-100700-n) for n in range(8)))
    state=await connections.get(env,MEMBER)
    assert len(state.history)==len(set(state.history))==5 and state.chat_id==state.history[0]
    assert state.revision==8


async def test_pg_policy_atomic_deltas_preserve_parallel_disabled_commands(env):
    from tests.bots.groupguard.test_groupguard import group_msg
    from tests.bots.groupguard.test_phase01a import send
    names=['id','info','notes','rules','locks','locktypes','flood','warnings']
    await asyncio.gather(*(send(env,group_msg('/disable '+name,ADMIN)) for name in names))
    assert set((await env.extras['guard'].config(GROUP)).disabled_commands)==set(names)
    await asyncio.gather(*(send(env,group_msg('/enable '+name,ADMIN)) for name in names[:4]))
    assert set((await env.extras['guard'].config(GROUP)).disabled_commands)==set(names[4:])


async def test_pg_broadcast_concurrent_creation_and_expansion_actual_one_delivery(env,api):
    from bots.groupguard import group_broadcast
    from bots.groupguard.delivery import Content
    from tests.bots.groupguard.test_groupguard import tg_user
    operator=env.child.owner_id if env.child else (env.env.admin_ids or env.platform.super_admin_ids)[0]
    results=await asyncio.gather(*(group_broadcast.create(env,tg_user(operator),Content('Concurrent')) for _ in range(8)))
    assert sum(row is not None for row in results)==1
    await asyncio.gather(*(group_broadcast.tick(env) for _ in range(4)))
    await asyncio.gather(*(durable.sweep(env) for _ in range(4)))
    assert len([m for m in api.calls('SendMessage') if m.chat_id==GROUP and m.text=='Concurrent'])==1


async def test_pg_federation_one_owner_parallel_create_and_role_writes(env):
    from bots.groupguard import federations
    from bots.groupguard.contracts import Actor
    from bots.groupguard.models import GuardFederation

    actor = Actor(env.bot_id, ADMIN, 'human', ADMIN)
    results = await asyncio.gather(*(federations.create(env, actor, 'Concurrent fed ' + str(n))
        for n in range(8)), return_exceptions=True)
    created = [row for row in results if isinstance(row, GuardFederation)]
    assert len(created) == 1
    assert sum(isinstance(row, federations.FedError) and str(row) == 'owned' for row in results) == 7
    fed = created[0]
    await asyncio.gather(*(federations.change(env, actor, fed.id, federations.Change('promote', n))
        for n in range(100, 112)))
    assert await federations.admins(env, fed.id) == [ADMIN, *range(100, 112)]
    assert (await federations.get(env, fed.id)).revision == 12


async def test_pg_federation_composite_foreign_key_rejects_sibling_role(env):
    from sqlalchemy.exc import IntegrityError

    from bots.groupguard import federations
    from bots.groupguard.contracts import Actor
    from bots.groupguard.models import GuardFedAdmin

    fed = await federations.create(env, Actor(env.bot_id, ADMIN, 'human', ADMIN), 'Scoped fed')
    sibling = next((c for c in env.extras['test_contexts'] if c.bot_id != env.bot_id), None)
    if sibling is None:
        async with env.sm() as session:
            session.add(BotRecord(id=991999, slug='fed-scope-fixture', title='Scope fixture', active=True))
            await session.commit()
        sibling_id = 991999
    else:
        sibling_id = sibling.bot_id
    async with env.sm() as session:
        session.add(GuardFedAdmin(bot_id=sibling_id, fed_id=fed.id, user_id=MEMBER, by_id=ADMIN))
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()
    assert await federations.admins(env, fed.id) == [ADMIN]


async def test_pg_federation_membership_switch_generation_and_current_creator(env, api):
    from aiogram.types import ChatMemberMember

    from bots.groupguard import federations
    from bots.groupguard.contracts import Actor
    from tests.bots.groupguard.test_groupguard import tg_user

    actor = Actor(env.bot_id, GROUP, 'human', ADMIN)
    fed = await federations.create(env, Actor(env.bot_id, ADMIN, 'human', ADMIN), 'Creator membership')
    first = await federations.membership(env, actor, fed.id)
    second = await federations.membership(env, actor, fed.id)
    assert first.generation != second.generation
    original = api.responses['GetChatMember']
    api.responses['GetChatMember'] = lambda m: ChatMemberMember(user=tg_user(ADMIN)) if m.user_id == ADMIN else original(m)
    with pytest.raises(federations.FedError):
        await federations.membership(env, actor, None)
    assert (await federations.attached(env, GROUP)).generation == second.generation


async def test_pg_federation_ban_unban_cannot_commit_over_dispatch(env, api, monkeypatch):
    from bots.groupguard import fed_bans, fed_enforcement, federations
    from bots.groupguard.contracts import Actor
    from tests.bots.groupguard.test_groupguard import tg_user
    from tests.bots.groupguard.test_phase10 import actual_bans, drain

    actual_bans(api)
    actor = Actor(env.bot_id, ADMIN, 'human', ADMIN)
    fed = await federations.create(env, actor, 'Serialized effects')
    attachment = await federations.membership(env, Actor(env.bot_id, GROUP, 'human', ADMIN), fed.id)
    await drain(env)
    await fed_enforcement.observe(env, GROUP, tg_user(30))
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30, 'Before newer unban'), active=True)
    async with env.sm() as session:
        jid = await fed_enforcement.enqueue_chat(env, session, attachment, user_id=30,
            root_id=fed.id, version=1, by_id=ADMIN, event='ban')
        await session.commit()
    job = await durable.claim(env, jid)
    assert job is not None
    entered, release = asyncio.Event(), asyncio.Event()
    original = api._respond

    async def response(method):
        if type(method).__name__ == 'BanChatMember':
            entered.set()
            await release.wait()
        return await original(method)

    monkeypatch.setattr(api, '_respond', response)
    worker = asyncio.create_task(fed_enforcement.run(env, job))
    await asyncio.wait_for(entered.wait(), 10)
    newer = asyncio.create_task(fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30), active=False))
    await asyncio.sleep(0.05)
    assert not newer.done()
    release.set()
    effect = await asyncio.wait_for(worker, 10)
    assert effect.primary_completed
    await durable.finish(env, job, effect)
    intent = await asyncio.wait_for(newer, 10)
    assert intent.version == 2 and not intent.active
    await drain(env)
    assert len(api.calls('BanChatMember')) == 1 and len(api.calls('UnbanChatMember')) == 1


async def test_pg_federation_parallel_cycles_and_import_transaction(env):
    from bots.groupguard import fed_files, fed_graph, federations
    from bots.groupguard.contracts import Actor
    from bots.groupguard.models import GuardFedBan

    actor = Actor(env.bot_id, ADMIN, 'human', ADMIN)
    other_actor = Actor(env.bot_id, 20, 'human', 20)
    one = await federations.create(env, actor, 'First root')
    two = await federations.create(env, other_actor, 'Second root')
    results = await asyncio.gather(fed_graph.change(env, actor, one.id, two.id, subscribe=True),
        fed_graph.change(env, other_actor, two.id, one.id, subscribe=True), return_exceptions=True)
    assert sum(isinstance(result, federations.FedError) and str(result) == 'cycle' for result in results) == 1
    await federations.change(env, actor, one.id, federations.Change('reason', True))
    body = b'{"user_id":30,"reason":"Good"}\n{"user_id":31}\n'
    with pytest.raises(federations.FedError, match='reason_required'):
        await fed_files.import_rows(env, actor, one.id, body, 'whole.ndjson')
    async with env.sm() as session:
        assert await session.get(GuardFedBan, (env.bot_id, one.id, 30)) is None
    assert not await env.redis.exists(env.keys('fed_file_interval', one.id))
    await fed_files.import_rows(env, actor, one.id, b'id,reason\n30,Valid\n31,Also valid\n', 'all.csv')
    async with env.sm() as session:
        assert (await session.get(GuardFedBan, (env.bot_id, one.id, 30))).active
        assert (await session.get(GuardFedBan, (env.bot_id, one.id, 31))).active


async def test_pg_federation_concurrent_passive_event_has_one_api_effect(env, api):
    from bots.groupguard import fed_bans, fed_enforcement, federations
    from bots.groupguard.contracts import Actor
    from tests.bots.groupguard.test_groupguard import tg_user
    from tests.bots.groupguard.test_phase10 import actual_bans, drain

    actual_bans(api)
    actor = Actor(env.bot_id, ADMIN, 'human', ADMIN)
    fed = await federations.create(env, actor, 'Concurrent passive')
    await federations.membership(env, Actor(env.bot_id, GROUP, 'human', ADMIN), fed.id)
    await drain(env)
    await fed_bans.change(env, actor, fed.id, fed_bans.BanInput(30, 'Shared observed event'), active=True)
    await asyncio.gather(*(fed_enforcement.passive(env, GROUP, tg_user(30), event='message:98765') for _ in range(8)))
    assert len(api.calls('BanChatMember')) == 1
    assert len([call for call in api.calls('SendMessage') if call.chat_id == GROUP and fed.id in call.text]) == 1


async def test_pg_selected_import_reset_one_revision_and_unknown_preservation(env):
    from bots.groupguard import portability
    from bots.groupguard.contracts import Actor
    svc=env.extras['guard']
    actor=Actor(env.bot_id,GROUP,'human',ADMIN)
    await svc.update_config(GROUP,rules='Round trip rules',unknown_preserved={'opaque':1})
    selected=frozenset({'rules'})
    body=await portability.export(env,actor,GROUP,selected)
    cfg=await svc.config(GROUP,fresh=True)
    intents=[portability.Intent(GROUP,selected,body,cfg._revision),portability.Intent(GROUP,selected,None,cfg._revision,True)]
    outcomes=await asyncio.gather(*(portability.apply(env,actor,intent) for intent in intents),return_exceptions=True)
    assert sum(result is None for result in outcomes)==1
    assert sum(isinstance(result,portability.PortableError) and str(result)=='stale' for result in outcomes)==1
    final=await svc.config(GROUP,fresh=True)
    assert final.rules in {'Round trip rules',''} and final.model_extra['unknown_preserved']=={'opaque':1}
    assert final._revision==cfg._revision+1


async def test_pg_privacy_keysets_cache_work_and_security_order(env):
    import json

    from bots.groupguard import privacy
    from bots.groupguard.contracts import Actor
    from bots.groupguard.models import GuardMember
    actor=Actor(env.bot_id,MEMBER,'human',MEMBER)
    async with env.sm() as session:
        for chat in range(-1200,-999):
            session.add(GuardMember(bot_id=env.bot_id,chat_id=chat,user_id=MEMBER,first_name='Observed name',username='observed'))
        await session.commit()
    page=json.loads(await privacy.inventory(env,actor))
    assert len(page['data']['member_observations'])==200 and page['next_cursor']
    second=json.loads(await privacy.inventory(env,actor,page['next_cursor']))
    assert len(second['data']['member_observations'])==1
    await env.redis.set(env.keys('uname','observed'),json.dumps({'id':MEMBER}))
    await privacy.erase(env,actor)
    async with env.sm() as session:
        jobs=list((await session.execute(select(GuardJob.id).where(GuardJob.bot_id==env.bot_id,
            GuardJob.user_id==MEMBER,GuardJob.kind=='privacy_cache'))).scalars())
        assert len(jobs)==2
        assert not any((await session.execute(select(GuardMember.first_name).where(
            GuardMember.bot_id==env.bot_id,GuardMember.user_id==MEMBER))).scalars())
    for jid in jobs:
        claimed=await durable.claim(env,jid)
        result=await privacy.run_cache(env,claimed)
        assert result.primary_completed
        await durable.finish(env,claimed,result)
    assert await env.redis.get(env.keys('uname','observed')) is None


async def test_pg_import_fresh_creator_after_delayed_media_validation(env,api,monkeypatch):
    import json

    from aiogram.types import ChatMemberMember, File

    from bots.groupguard import portability
    from bots.groupguard.contracts import Actor
    from tests.conftest import tg_user
    svc=env.extras['guard']
    actor=Actor(env.bot_id,GROUP,'human',ADMIN)
    selected=frozenset({'notes'})
    body=json.loads(await portability.export(env,actor,GROUP,selected))
    body['items']=[dict(kind='note',key='media',text='Hello',format='html',media_kind='photo',file_id='ownfile')]
    cfg=await svc.config(GROUP,fresh=True)
    entered,release=asyncio.Event(),asyncio.Event()
    async def delayed(file_id):
        assert file_id=='ownfile'
        entered.set()
        await asyncio.wait_for(release.wait(),5)
        return File(file_id='ownfile',file_unique_id='unique',file_path='file')
    monkeypatch.setattr(env.bot,'get_file',delayed)
    task=asyncio.create_task(portability.apply(env,actor,portability.Intent(GROUP,selected,json.dumps(body).encode(),cfg._revision)))
    await asyncio.wait_for(entered.wait(),5)
    original=api.responses['GetChatMember']
    api.responses['GetChatMember']=lambda m: ChatMemberMember(user=tg_user(ADMIN)) if m.user_id==ADMIN else original(m)
    release.set()
    with pytest.raises(portability.PortableError,match='authority'):
        await task
    assert not await svc.list_items(GROUP,'note')
    assert (await svc.config(GROUP,fresh=True))._revision==cfg._revision


async def test_pg_quiet_policy_waits_for_attachment_and_rechecks_current_rights(env,api,monkeypatch):
    import uuid

    from aiogram.types import ChatMemberMember

    from bots.groupguard import authz, federations
    from bots.groupguard.contracts import Actor
    from bots.groupguard.models import GuardFedChat
    from tests.conftest import tg_user
    actor=Actor(env.bot_id,GROUP,'human',ADMIN)
    fed=await federations.create(env,Actor(env.bot_id,ADMIN,'human',ADMIN),'Quiet fencing')
    await federations.membership(env,actor,fed.id)
    original_authorize=authz.authorize
    original_member=api.responses['GetChatMember']
    for replacement in (True,False):
        old=(await federations.attached(env,GROUP)).generation
        entered=asyncio.Event()
        calls=0
        async def observed(*args,_entered=entered,**kwargs):
            nonlocal calls
            result=await original_authorize(*args,**kwargs)
            calls+=1
            if calls==1:
                _entered.set()
            return result
        monkeypatch.setattr(authz,'authorize',observed)
        async with env.sm() as holder:
            row=(await holder.execute(select(GuardFedChat).where(GuardFedChat.bot_id==env.bot_id,
                GuardFedChat.chat_id==GROUP).with_for_update())).scalar_one()
            if replacement:
                row.generation=uuid.uuid4().hex
                await holder.flush()
            task=asyncio.create_task(federations.change_quiet(env,actor,fed.id,old,True))
            await asyncio.wait_for(entered.wait(),5)
            if not replacement:
                api.responses['GetChatMember']=lambda m: ChatMemberMember(user=tg_user(ADMIN)) if m.user_id==ADMIN else original_member(m)
            await holder.commit()
        with pytest.raises(federations.FedError,match='stale' if replacement else 'authority'):
            await asyncio.wait_for(task,5)
        final=await federations.attached(env,GROUP)
        assert not final.quiet
        assert (final.generation!=old) if replacement else (final.generation==old)
        api.responses['GetChatMember']=original_member
        monkeypatch.setattr(authz,'authorize',original_authorize)


async def test_pg_selected_owned_night_and_captcha_reset_outcomes(env,api):
    from tests.bots.groupguard.test_phase11 import (
        test_reset_captcha_failure_retains_issued_work_and_success_preserves_other_ban,
        test_reset_night_restores_only_owned_snapshot_and_failed_restore_keeps_config,
    )
    await test_reset_night_restores_only_owned_snapshot_and_failed_restore_keeps_config(env,api)
    await test_reset_captcha_failure_retains_issued_work_and_success_preserves_other_ban(env,api)


async def test_pg_scoped_platform_privacy_and_selected_raid_generation_reset(env,api):
    from tests.bots.groupguard.test_phase11 import (
        test_privacy_includes_own_platform_records_without_payment_or_instance_secrets,
        test_selected_raid_reset_retires_generation_job_and_keeps_real_bans,
    )
    await test_privacy_includes_own_platform_records_without_payment_or_instance_secrets(env)
    await test_selected_raid_reset_retires_generation_job_and_keeps_real_bans(env,api)


async def test_pg_nonempty_allowlist_import_effects(env,api):
    from tests.bots.groupguard.test_phase11 import (
        test_nonempty_allowlist_roundtrip_enforces_links_and_rejects_bad_entries,
    )
    await test_nonempty_allowlist_roundtrip_enforces_links_and_rejects_bad_entries(env,api)


async def test_pg_identity_scoped_federation_status_and_anonymous_chat(env,api):
    from tests.bots.groupguard.test_phase11 import (
        test_info_reports_scoped_federation_sources_and_anonymous_id_is_real_chat,
    )
    await test_info_reports_scoped_federation_sources_and_anonymous_id_is_real_chat(env,api)


async def test_pg_factory_record_token_identity_fences_runtime_and_cleanup(env,api):
    from tests.bots.groupguard.test_phase11 import (
        test_factory_record_token_identity_is_checked_before_runtime_or_pause_rpc,
    )
    await test_factory_record_token_identity_is_checked_before_runtime_or_pause_rpc(env,api)
