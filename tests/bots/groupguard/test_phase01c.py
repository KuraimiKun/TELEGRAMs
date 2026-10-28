import asyncio
from datetime import timedelta

from aiogram.types import User
from sqlalchemy import select, update

from bots.groupguard import actions, challenges, durable
from bots.groupguard.models import GuardChallenge, GuardInbox, GuardJob, GuardNight, GuardRestriction
from bots.groupguard.replay import recover_inbox
from bots.groupguard.service import GuardService
from core.db.base import utcnow
from tests.bots.groupguard.test_groupguard import (
    ADMIN,
    GROUP,
    MEMBER,
    bound_callback,
    gctx,
    group_msg,
    join_update,
    plain,
)
from tests.bots.groupguard.test_phase01a import build_dispatcher_once, env, send

__all__ = ["env", "gctx"]


async def test_field_patches_stale_models_and_unknown_json_survive(env):
    first = env.extras["guard"]
    second = GuardService(env.sm, env.bot_id)
    await first.update_config(GROUP, external_extension={"preserve": [1, 2]})
    a, b = await first.config(GROUP), await second.config(GROUP)
    a.welcome = False
    b.goodbye = True
    await first.save_config(GROUP, a)
    await second.save_config(GROUP, b)
    actual = await first.config(GROUP)
    assert actual.welcome is False and actual.goodbye is True
    assert actual.model_extra["external_extension"] == {"preserve": [1, 2]}
    assert actual._revision > a._revision


async def test_warning_button_is_exact_and_replay_does_not_remove_new_warning(env, api):
    await env.extras["guard"].update_config(GROUP, warn_limit=20)
    await send(env, group_msg("/warn first", ADMIN, reply_to=plain(MEMBER)))
    call, msg = api.calls("SendMessage")[-1], api.messages[-1]
    data = call.reply_markup.inline_keyboard[0][0].callback_data
    await send(env, group_msg("/warn second", ADMIN, reply_to=plain(MEMBER)))
    await send(env, bound_callback(data, msg, ADMIN))
    assert [w.reason for w in await env.extras["guard"].list_warns(GROUP, MEMBER)] == ["second"]
    await send(env, bound_callback(data, msg, ADMIN))
    assert [w.reason for w in await env.extras["guard"].list_warns(GROUP, MEMBER)] == ["second"]


async def issue(ctx, api, monkeypatch, user_id=30):
    from bots.groupguard.handlers import welcome

    async def no_cas(*args):
        return False

    monkeypatch.setattr(welcome, "cas_banned", no_cas)
    event = join_update(user_id)
    # This fixture deliberately requests a fresh observed event, not redelivery within one server second.
    ctx.extras["test_join_date"] = ctx.extras.get("test_join_date", utcnow()-timedelta(minutes=1)) + timedelta(seconds=2)
    event = event.model_copy(update={"chat_member": event.chat_member.model_copy(update={"date": ctx.extras["test_join_date"]})})
    await send(ctx, event)
    msg, call = api.messages[-1], api.calls("SendMessage")[-1]
    async with ctx.sm() as session:
        state = await session.get(GuardChallenge, (ctx.bot_id, GROUP, user_id))
    return state, msg, call.reply_markup.inline_keyboard[0][0].callback_data


async def test_replacement_fences_old_answer_and_expiry_and_preserves_manual_mute(env, api, monkeypatch):
    old, msg, data = await issue(env, api, monkeypatch)
    # Explicit fresh issuance, rather than another delivery of the same observed join event.
    await challenges.reset(env, GROUP, 30, forget=True)
    current, new_msg, new_data = await issue(env, api, monkeypatch)
    assert old.generation != current.generation
    before = len(api.calls("RestrictChatMember"))
    await send(env, bound_callback(data, msg, 30))
    assert len(api.calls("RestrictChatMember")) == before
    result = await challenges.expire(env, GROUP, 30, old.generation, force=True)
    assert not result.primary_completed and not api.calls("BanChatMember")
    assert (await actions.punish(env, GROUP, 30, "mute", None, origin="manual")).primary_completed
    before = len(api.calls("RestrictChatMember"))
    await send(env, bound_callback(new_data, new_msg, 30))
    assert len(api.calls("RestrictChatMember")) == before
    async with env.sm() as session:
        state = await session.get(GuardChallenge, (env.bot_id, GROUP, 30))
        restrictions = list(
            (
                await session.execute(
                    select(GuardRestriction).where(
                        GuardRestriction.bot_id == env.bot_id,
                        GuardRestriction.chat_id == GROUP,
                        GuardRestriction.user_id == 30,
                    )
                )
            ).scalars()
        )
    assert state.status == "solved" and [r.source for r in restrictions] == ["manual"]


async def test_answer_claim_committed_before_restore_timeout_cannot_kick(env, api, monkeypatch):
    state, msg, data = await issue(env, api, monkeypatch)
    entered, release = asyncio.Event(), asyncio.Event()
    primitive = actions._unmute_api

    async def hold(*args, **kw):
        entered.set()
        await release.wait()
        return await primitive(*args, **kw)

    monkeypatch.setattr(actions, "_unmute_api", hold)
    query = bound_callback(data, msg, 30).callback_query.as_(env.bot)
    arg = data.rsplit(":", 1)[1]
    answer_task = asyncio.create_task(challenges.answer(env, query, GROUP, 30, arg))
    await asyncio.wait_for(entered.wait(), 3)
    async with env.sm() as session:
        claimed = await session.get(GuardChallenge, (env.bot_id, GROUP, 30))
    assert claimed.status == "answering"  # durable even before the API returns
    timeout = asyncio.create_task(challenges.expire(env, GROUP, 30, state.generation, force=True))
    release.set()
    answered, expired = await asyncio.gather(answer_task, timeout)
    assert answered.status == "accepted" and not expired.primary_completed
    assert not api.calls("BanChatMember")


async def test_job_lease_recovery_before_dispatch_and_uncertain_after(env):
    jid = await durable.enqueue(env, "test", GROUP, dedupe_key="recovery", payload={})
    first = await durable.claim(env, jid)
    async with env.sm() as session:
        await session.execute(
            update(GuardJob).where(GuardJob.id == jid).values(lease_until=utcnow() - timedelta(seconds=1))
        )
        await session.commit()
    assert await durable.recover(env) == 1
    second = await durable.claim(env, jid)
    assert second.lease_owner != first.lease_owner
    await durable.dispatched(env, second)
    async with env.sm() as session:
        await session.execute(
            update(GuardJob).where(GuardJob.id == jid).values(lease_until=utcnow() - timedelta(seconds=1))
        )
        await session.commit()
    assert await durable.recover(env) == 1 and await durable.claim(env, jid) is None
    async with env.sm() as session:
        final = await session.get(GuardJob, jid)
    assert final.status == "uncertain" and final.error_code == "interrupted_external_call"


async def test_update_and_message_replay_do_not_warn_or_notify_twice(env, api):
    request = group_msg("/warn one", ADMIN, reply_to=plain(MEMBER))
    await send(env, request)
    before = len(api.calls("SendMessage"))
    await send(env, request)
    await send(env, request.model_copy(update={"update_id": request.update_id + 1000000}))
    assert await env.extras["guard"].count_warns(GROUP, MEMBER) == 1
    assert len(api.calls("SendMessage")) == before


async def test_received_update_recovers_interrupted_processing_is_uncertain(env, api):
    build_dispatcher_once(env)
    request = group_msg("/warn recover", ADMIN, reply_to=plain(MEMBER))
    interrupted = group_msg("/warn interrupted", ADMIN, reply_to=plain(MEMBER))
    async with env.sm() as session:
        session.add(
            GuardInbox(
                bot_id=env.bot_id,
                update_id=request.update_id,
                event_type="message",
                payload=request.model_dump(mode="json", exclude_none=True),
                status="received",
                created_at=utcnow(),
            )
        )
        session.add(
            GuardInbox(
                bot_id=env.bot_id,
                update_id=interrupted.update_id,
                event_type="message",
                payload=interrupted.model_dump(mode="json", exclude_none=True),
                status="processing",
                lease_until=utcnow() - timedelta(seconds=1),
                created_at=utcnow(),
            )
        )
        await session.commit()
    assert await recover_inbox(env) == 1
    assert await env.extras["guard"].count_warns(GROUP, MEMBER) == 1
    async with env.sm() as session:
        row = await session.get(GuardInbox, (env.bot_id, interrupted.update_id))
    assert row.status == "uncertain"


async def test_child_pause_fences_cached_dispatcher_and_releases_owned_night(env, api):
    if env.child is None:
        return
    from bots.groupguard.jobs import apply_night
    from core.db.models import ChildBot
    from core.factory.children import ChildService

    base_get = api.responses["GetChat"]

    def changed(m):
        base = base_get(m)
        return (
            base.model_copy(update={"permissions": api.calls("SetChatPermissions")[-1].permissions})
            if api.calls("SetChatPermissions")
            else base
        )

    api.responses["GetChat"] = changed
    hour = utcnow().hour
    cfg = await env.extras["guard"].update_config(
        GROUP, night=True, night_start=0, night_end=23, tz_offset=-hour if hour <= 12 else 24 - hour
    )
    assert (await apply_night(env, GROUP, cfg)).primary_completed
    async with env.sm() as session:
        child = await session.get(ChildBot, env.bot_id)
    api.responses["GetMe"] = User(
        id=env.bot_id, is_bot=True, first_name="Guard", username=f"guard{env.bot_id}_bot"
    )
    service = ChildService(
        env.sm, env.redis, env.platform, factory_bot_id=123456, templates={"groupguard"}, session=api
    )
    await service.pause(child)
    assert api.calls("SetChatPermissions")[-1].permissions.can_send_messages is True
    before = len(api.calls("BanChatMember"))
    await send(env, group_msg("/ban 20 reason", ADMIN))
    assert len(api.calls("BanChatMember")) == before
    async with env.sm() as session:
        night = await session.get(GuardNight, (env.bot_id, GROUP))
    assert night.status == "restored"


async def test_verified_during_night_restores_only_after_open(env, api, monkeypatch):
    from bots.groupguard.jobs import apply_night

    _state, message, data = await issue(env, api, monkeypatch)
    original = api.responses["GetChat"]

    def actual(m):
        chat = original(m)
        if api.calls("SetChatPermissions"):
            chat = chat.model_copy(update={"permissions": api.calls("SetChatPermissions")[-1].permissions})
        return chat

    api.responses["GetChat"] = actual
    hour = utcnow().hour
    cfg = await env.extras["guard"].update_config(
        GROUP, night=True, night_start=0, night_end=23, tz_offset=-hour if hour <= 12 else 24 - hour
    )
    assert (await apply_night(env, GROUP, cfg)).primary_completed
    before = len(api.calls("RestrictChatMember"))
    await send(env, bound_callback(data, message, 30))
    assert await challenges.verified(env, GROUP, 30)
    assert len(api.calls("RestrictChatMember")) == before
    cfg = await env.extras["guard"].update_config(GROUP, night=False)
    assert (await apply_night(env, GROUP, cfg)).primary_completed
    assert api.calls("RestrictChatMember")[-1].permissions.can_send_messages is True
    async with env.sm() as session:
        assert not list((await session.execute(select(GuardRestriction).where(
            GuardRestriction.bot_id == env.bot_id, GuardRestriction.chat_id == GROUP,
            GuardRestriction.user_id == 30))).scalars())


async def test_timed_source_cannot_shorten_or_remove_permanent_other_mute(env, api):
    assert (await actions.punish(env, GROUP, MEMBER, "mute", None, source="federation:test")).primary_completed
    timed = await actions.punish(env, GROUP, MEMBER, "mute", timedelta(minutes=1), origin="manual", generation="m1")
    assert timed.primary_completed and timed.until_date is None
    async with env.sm() as session:
        await session.execute(update(GuardRestriction).where(GuardRestriction.bot_id == env.bot_id,
            GuardRestriction.chat_id == GROUP, GuardRestriction.user_id == MEMBER,
            GuardRestriction.source == "manual").values(until=utcnow() - timedelta(seconds=1)))
        await session.commit()
    before = len(api.calls("RestrictChatMember"))
    expired = await actions.unmute(env, GROUP, MEMBER, source="manual", generation="m1", expiration=True)
    assert expired.primary_completed and len(api.calls("RestrictChatMember")) == before
    assert not (await actions.unmute(env, GROUP, MEMBER, origin="manual")).primary_completed


async def test_job_retry_and_revoked_warning_actor_preserve_history(env, api):
    from aiogram.exceptions import TelegramRetryAfter
    from aiogram.methods import BanChatMember

    decision = await durable.record_warning(env, GROUP, MEMBER, "retry", ADMIN,
        limit=1, action="ban", duration_seconds=None, name="Member")
    api.responses["BanChatMember"] = TelegramRetryAfter(method=BanChatMember(chat_id=GROUP, user_id=MEMBER),
                                                      message="wait", retry_after=2)
    result = await durable.execute_warning(env, decision.job_id)
    assert not result.primary_completed and await env.extras["guard"].count_warns(GROUP, MEMBER) == 1
    async with env.sm() as session:
        job = await session.get(GuardJob, decision.job_id)
        assert job.status == "pending" and not job.dispatched
        await session.execute(update(GuardJob).where(GuardJob.id == job.id).values(run_at=utcnow()))
        await session.commit()
    from aiogram.types import ChatMemberMember
    old = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: ChatMemberMember(user=User(id=ADMIN, first_name="Revoked", is_bot=False)) if m.user_id == ADMIN else old(m)
    before = len(api.calls("BanChatMember"))
    result = await durable.execute_warning(env, decision.job_id)
    assert not result.primary_completed and len(api.calls("BanChatMember")) == before
    assert await env.extras["guard"].count_warns(GROUP, MEMBER) == 1
