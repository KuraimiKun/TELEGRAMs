"""Actual flood/raid/night API effects, independent boundaries and restart ownership."""

from datetime import timedelta

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SetChatPermissions
from aiogram.types import Chat, ChatJoinRequest, ChatMemberMember, ChatPermissions, Update
from sqlalchemy import select, update

from bots.groupguard import actions, durable, flood, jobs, raids, verification
from bots.groupguard.models import GuardChat, GuardJob, GuardNight, GuardRaid, GuardRestriction
from core.db.base import utcnow
from tests.bots.groupguard.test_groupguard import (
    ADMIN,
    GROUP,
    MEMBER,
    NEWBIE,
    bound_callback,
    gctx,
    group_msg,
    join_update,
    tg_user,
)
from tests.bots.groupguard.test_phase01a import admin_member, env, send

__all__ = ["env", "gctx"]


async def test_consecutive_exact_threshold_other_origins_break_and_independent_timer(env, api):
    await send(env, group_msg("/setflood 2", ADMIN))
    await send(env, group_msg("first", MEMBER))
    await send(env, group_msg("admin interleaves", ADMIN))
    await send(env, group_msg("again first", MEMBER))
    assert not api.calls("RestrictChatMember")
    last = group_msg("second", MEMBER)
    await send(env, last)
    assert api.calls("RestrictChatMember")[-1].user_id == MEMBER
    assert api.calls("DeleteMessage")[-1].message_id == last.message.message_id
    assert (await env.extras["guard"].config(GROUP)).flood_count == 0


async def test_timer_interleaved_exact_more_than_limit_and_clear_observed_only(env, api):
    await send(env, group_msg("/setfloodtimer 2 10s", ADMIN))
    await send(env, group_msg("/clearflood on", ADMIN))
    observed = []
    for n in range(2):
        request = group_msg("member" + str(n), MEMBER)
        observed.append(request.message.message_id)
        await send(env, request)
        await send(env, group_msg("other" + str(n), NEWBIE))
    assert not api.calls("RestrictChatMember")
    request = group_msg("beyond", MEMBER)
    observed.append(request.message.message_id)
    await send(env, request)
    assert api.calls("DeleteMessages")[-1].message_ids == observed
    assert api.calls("RestrictChatMember")[-1].user_id == MEMBER


async def test_window_equality_cutoff_and_replay_edit_do_not_recount(env, api, monkeypatch):
    await send(env, group_msg("/setfloodtimer 2 1s", ADMIN))
    clock = [1000.0]
    monkeypatch.setattr(flood.time, "time", lambda: clock[0])
    original = group_msg("first", MEMBER)
    await send(env, original)
    await send(env, original.model_copy(update={"update_id": group_msg("unique", MEMBER).update_id}))
    await send(
        env,
        Update(
            update_id=group_msg("unique", MEMBER).update_id,
            edited_message=original.message.model_copy(
                update={"text": "edited", "edit_date": int(utcnow().timestamp())}
            ),
        ),
    )
    clock[0] += 1
    await send(env, group_msg("cutoff removes first", MEMBER))
    await send(env, group_msg("second in window", MEMBER))
    assert not api.calls("RestrictChatMember")
    await send(env, group_msg("third in window", MEMBER))
    assert len(api.calls("RestrictChatMember")) == 1


@pytest.mark.parametrize("mode", ["kick", "ban", "mute", "tban 5m", "tmute 5m"])
async def test_flood_modes_actual_permanent_temporary_and_whole_sequence_off(env, api, mode):
    await send(env, group_msg("/setfloodmode " + mode, ADMIN))
    await send(env, group_msg("/setflood 2", ADMIN))
    await send(env, group_msg("one", MEMBER))
    last = group_msg("two", MEMBER)
    await send(env, last)
    call = (api.calls("RestrictChatMember") if "mute" in mode else api.calls("BanChatMember"))[-1]
    assert call.user_id == MEMBER
    assert bool(api.calls("UnbanChatMember")) == (mode == "kick")
    assert api.calls("DeleteMessage")[-1].message_id == last.message.message_id
    if mode.startswith("t"):
        assert 290 <= call.until_date - utcnow().timestamp() <= 301
    else:
        assert call.until_date is None


async def test_flood_silent_gate_missing_rights_and_independent_off(env, api):
    svc = env.extras["guard"]
    await send(env, group_msg("/setfloodmode sban", ADMIN))
    assert not (await svc.config(GROUP)).flood_silent
    await svc.update_config(GROUP, silent_actions_allowed=True, log_chat_id=-10088)
    await send(env, group_msg("/setfloodmode stmute 5m", ADMIN))
    await send(env, group_msg("/setflood 2", ADMIN))
    await send(env, group_msg("/setfloodtimer 4 20s", ADMIN))
    await send(env, group_msg("/setflood off", ADMIN))
    cfg = await svc.config(GROUP)
    assert cfg.flood_consecutive_count == 0 and cfg.flood_count == 4
    await send(env, group_msg("/setfloodtimer off", ADMIN))
    await send(env, group_msg("/setflood 2", ADMIN))
    before = len([m for m in api.calls("SendMessage") if m.chat_id == GROUP])
    await send(env, group_msg("one", MEMBER))
    await send(env, group_msg("two", MEMBER))
    assert len([m for m in api.calls("SendMessage") if m.chat_id == GROUP]) == before
    await svc.update_config(GROUP, log_chat_id=None)
    await send(env, group_msg("three", MEMBER))
    await send(env, group_msg("four", MEMBER))
    assert api.calls("SendMessage")[-1].chat_id == GROUP
    old = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: (
        admin_member(env.bot_id, can_delete_messages=True) if m.user_id == env.bot_id else old(m)
    )
    before = len(api.calls("DeleteMessage"))
    await send(env, group_msg("five", MEMBER))
    await send(env, group_msg("six", MEMBER))
    assert len(api.calls("DeleteMessage")) == before


async def test_raid_defaults_override_off_retains_bans_and_bot_scopes(env, api):
    svc = env.extras["guard"]
    await svc.update_config(GROUP, cas=False)
    await send(env, group_msg("/antiraid on", MEMBER))
    assert not raids.active(await raids.state(env, GROUP))
    await send(env, group_msg("/antiraid on", ADMIN))
    first = await raids.state(env, GROUP)
    assert 21590 <= (first.deadline - utcnow()).total_seconds() <= 21601 and first.ban_seconds == 3600
    await send(env, join_update(MEMBER))
    assert api.calls("BanChatMember")[-1].user_id == MEMBER
    assert 3590 <= api.calls("BanChatMember")[-1].until_date - utcnow().timestamp() <= 3601
    assert not await verification.state_of(env, GROUP, MEMBER)
    await send(env, group_msg("/antiraid 10m", ADMIN))
    current = await raids.state(env, GROUP)
    assert (
        current.generation != first.generation and 590 <= (current.deadline - utcnow()).total_seconds() <= 601
    )
    assert (await svc.config(GROUP)).raid_seconds == 21600
    await send(env, group_msg("/antiraid off", ADMIN))
    assert not raids.active(await raids.state(env, GROUP)) and not api.calls("UnbanChatMember")
    async with env.sm() as session:
        own = await session.get(GuardRestriction, (env.bot_id, GROUP, MEMBER, "raid"))
    assert own.mode == "ban"
    for other in env.extras["test_contexts"]:
        if other.bot_id != env.bot_id:
            assert not raids.active(await raids.state(other, GROUP))


async def test_auto_raid_more_than_threshold_duplicates_and_protected_joins(env, api):
    svc = env.extras["guard"]
    await svc.update_config(GROUP, cas=False, captcha="off")
    await send(env, group_msg("/autoantiraid 2", ADMIN))
    await svc.approve(GROUP, NEWBIE, None, ADMIN)
    await send(env, join_update(NEWBIE))
    first = join_update(41)
    await send(env, first)
    await send(env, Update(update_id=group_msg("unique", MEMBER).update_id, chat_member=first.chat_member))
    await send(env, join_update(42))
    assert not api.calls("BanChatMember")
    await send(env, join_update(43))
    assert api.calls("BanChatMember")[-1].user_id == 43 and raids.active(await raids.state(env, GROUP))
    await send(env, group_msg("/antiraid off", ADMIN))
    await send(env, join_update(44))
    assert not raids.active(await raids.state(env, GROUP))  # Off creates a new observed counter generation.
    await send(env, group_msg("/autoantiraid off", ADMIN))
    assert (await svc.config(GROUP)).auto_raid_count == 0


async def test_raid_expiry_generation_and_join_request_cannot_bypass(env, api):
    svc = env.extras["guard"]
    await svc.update_config(GROUP, cas=False)
    request = ChatJoinRequest(
        chat=Chat(id=GROUP, type="supergroup"), from_user=tg_user(MEMBER), date=utcnow(), user_chat_id=MEMBER
    )
    await send(env, Update(update_id=group_msg("unique", MEMBER).update_id, chat_join_request=request))
    state = await verification.state_of(env, GROUP, MEMBER)
    message = api.messages[-1]
    callback = api.calls("SendMessage")[-1].reply_markup.inline_keyboard[0][0].callback_data
    await send(env, group_msg("/antiraid on", ADMIN))
    old = await raids.state(env, GROUP)
    await send(env, bound_callback(callback, message, MEMBER))
    assert not api.calls("ApproveChatJoinRequest") and api.calls("DeclineChatJoinRequest")
    await send(env, group_msg("/antiraid 10m", ADMIN))
    async with env.sm() as session:
        old_job = (
            await session.execute(
                select(GuardJob).where(
                    GuardJob.bot_id == env.bot_id,
                    GuardJob.kind == "raid_expire",
                    GuardJob.generation == old.generation,
                )
            )
        ).scalar_one()
    await raids.expire_job(env, old_job)
    assert raids.active(await raids.state(env, GROUP))
    current = await raids.state(env, GROUP)
    async with env.sm() as session:
        await session.execute(
            update(GuardRaid)
            .where(GuardRaid.bot_id == env.bot_id, GuardRaid.chat_id == GROUP)
            .values(deadline=utcnow() - timedelta(seconds=1))
        )
        await session.execute(
            update(GuardJob)
            .where(GuardJob.bot_id == env.bot_id, GuardJob.generation == current.generation)
            .values(run_at=utcnow() - timedelta(seconds=1))
        )
        await session.commit()
    await durable.sweep(env)
    assert not raids.active(await raids.state(env, GROUP))
    assert (await raids.state(env, GROUP)).status == "expired"
    assert state.request_contact_id == MEMBER


def track_permissions(api):
    original = api.responses["GetChat"]
    current = {}
    api.responses["GetChat"] = lambda m: original(m).model_copy(
        update={"permissions": current.get(m.chat_id, original(m).permissions)}
    )

    def set_permissions(method):
        current[method.chat_id] = method.permissions
        return True

    api.responses["SetChatPermissions"] = set_permissions
    return current


async def configure_night(ctx):
    hour = utcnow().hour
    return await ctx.extras["guard"].update_config(
        GROUP, night=True, night_start=0, night_end=23, tz_offset=-hour if hour <= 12 else 24 - hour
    )


async def test_night_off_immediate_owned_restore_and_later_admin_change_wins(env, api):
    current = track_permissions(api)
    cfg = await configure_night(env)
    await jobs.apply_night(env, GROUP, cfg)
    assert current[GROUP].can_send_messages is False
    await send(env, group_msg("/night off", ADMIN))
    assert current[GROUP].can_send_messages is True and current[GROUP].can_send_polls is False
    cfg = await configure_night(env)
    await jobs.apply_night(env, GROUP, cfg)
    later = ChatPermissions(can_send_messages=True, can_send_polls=True)
    current[GROUP] = later
    before = len(api.calls("SetChatPermissions"))
    await send(env, group_msg("/night off", ADMIN))
    assert len(api.calls("SetChatPermissions")) == before and current[GROUP] == later
    async with env.sm() as session:
        assert (await session.get(GuardNight, (env.bot_id, GROUP))).status == "superseded"


async def test_night_prepared_restart_failed_close_retry_and_unknown_not_replayed(env, api):
    current = track_permissions(api)
    cfg = await configure_night(env)
    snapshot = (await actions.default_permissions(env, GROUP)).permissions.model_dump(exclude_none=True)
    closed = {key: False for key in snapshot}
    await jobs.persist_night(
        env, GROUP, "prepared", "prepared", snapshot, closed, window_key=jobs.night_window(cfg)
    )
    api.responses["SetChatPermissions"] = TelegramBadRequest(
        method=SetChatPermissions(chat_id=GROUP, permissions=ChatPermissions(**closed)), message="failed"
    )
    result = await jobs.apply_night(env, GROUP, cfg)
    assert not result.primary_completed
    async with env.sm() as session:
        assert (await session.get(GuardNight, (env.bot_id, GROUP))).status == "failed"
    track_permissions(api)
    assert (await jobs.apply_night(env, GROUP, cfg)).primary_completed
    before = len(api.calls("SetChatPermissions"))
    await jobs.persist_night(env, GROUP, "uncertain", "dispatched", snapshot, closed)
    await jobs.apply_night(env, GROUP, cfg)
    assert len(api.calls("SetChatPermissions")) == before
    assert current == {}  # This earlier observer received no invented mutation on failure.


async def test_failed_first_night_group_does_not_starve_tail_across_durable_pages(gctx, api):
    cfg = await configure_night(gctx)
    chat_ids = [GROUP - n for n in range(120)]
    async with gctx.sm() as session:
        session.add_all(
            [
                GuardChat(
                    bot_id=gctx.bot_id, chat_id=chat, title="Night", night=True, config=cfg.model_dump()
                )
                for chat in chat_ids
                if chat != GROUP
            ]
        )
        await session.commit()
    track_permissions(api)
    old = api.responses["GetChatMember"]
    bad = min(chat_ids)
    api.responses["GetChatMember"] = lambda m: (
        ChatMemberMember(user=tg_user(m.user_id)) if m.chat_id == bad and m.user_id == gctx.bot_id else old(m)
    )
    await jobs.night_job(gctx)
    assert len(api.calls("SetChatPermissions")) == 99
    gctx.extras.clear()
    from bots.groupguard.service import GuardService

    gctx.extras["guard"] = GuardService(gctx.sm, gctx.bot_id)
    await jobs.night_job(gctx)
    assert len(api.calls("SetChatPermissions")) == 119
    assert max(chat_ids) in {m.chat_id for m in api.calls("SetChatPermissions")}


@pytest.mark.parametrize("origin", ["approved", "bot", "channel"])
async def test_exempt_other_origins_break_consecutive_without_becoming_targets(env, api, origin):
    await send(env, group_msg("/setflood 2", ADMIN))
    await send(env, group_msg("first", MEMBER))
    other = group_msg("interleave", NEWBIE)
    if origin == "approved":
        await env.extras["guard"].approve(GROUP, NEWBIE, None, ADMIN)
    elif origin == "bot":
        other = other.model_copy(
            update={
                "message": other.message.model_copy(
                    update={"from_user": tg_user(NEWBIE).model_copy(update={"is_bot": True})}
                )
            }
        )
    else:
        other = other.model_copy(
            update={
                "message": other.message.model_copy(update={"sender_chat": Chat(id=-10099, type="channel")})
            }
        )
    await send(env, other)
    await send(env, group_msg("first again", MEMBER))
    assert not api.calls("RestrictChatMember")
    await send(env, group_msg("second again", MEMBER))
    assert len(api.calls("RestrictChatMember")) == 1 and api.calls("RestrictChatMember")[-1].user_id == MEMBER


async def test_burst_raid_actual_bans_bounded_and_failed_capability_never_issues_captcha(env, api):
    svc = env.extras["guard"]
    await svc.update_config(GROUP, cas=False, captcha="off")
    await send(env, group_msg("/autoantiraid 2", ADMIN))
    for user_id in range(81, 91):
        await send(env, join_update(user_id))
    assert [m.user_id for m in api.calls("BanChatMember")] == list(range(83, 91))
    assert all(3590 <= m.until_date - utcnow().timestamp() <= 3601 for m in api.calls("BanChatMember"))
    await svc.update_config(GROUP, captcha="button")
    old = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: (
        admin_member(env.bot_id, can_delete_messages=True) if m.user_id == env.bot_id else old(m)
    )
    before = len(api.calls("BanChatMember"))
    await send(env, join_update(92))
    assert len(api.calls("BanChatMember")) == before and await verification.state_of(env, GROUP, 92) is None


async def test_raid_off_before_dispatch_stops_rpc_preserves_unrelated_owner(env, api, monkeypatch):
    await env.extras["guard"].update_config(GROUP, cas=False)
    await send(env, group_msg("/antiraid on", ADMIN))
    original = actions._punish_api

    async def off_before_dispatch(*args, **kwargs):
        # A separate process has independent connection capacity and a different member lock.
        async with env.sm() as session:
            await session.execute(
                update(GuardRaid)
                .where(GuardRaid.bot_id == env.bot_id, GuardRaid.chat_id == GROUP)
                .values(status="inactive", generation="off")
            )
            await session.commit()
        return await original(*args, **kwargs)

    monkeypatch.setattr(actions, "_punish_api", off_before_dispatch)
    await send(env, join_update(MEMBER))
    assert not api.calls("BanChatMember")
    async with env.sm() as session:
        assert await session.get(GuardRestriction, (env.bot_id, GROUP, MEMBER, "raid")) is None


async def test_factory_pause_stops_activation_keeps_real_raid_ban(env, api):
    if env.child is None:
        pytest.skip("factory lifecycle applies to actual children")
    await env.extras["guard"].update_config(GROUP, cas=False)
    await send(env, group_msg("/antiraid on", ADMIN))
    await send(env, join_update(MEMBER))
    from core.db.models import ChildBot
    from core.factory.children import ChildService

    async with env.sm() as session:
        child = await session.get(ChildBot, env.bot_id)
    api.responses["GetMe"] = tg_user(env.bot_id).model_copy(update={"is_bot": True})
    service = ChildService(
        env.sm, env.redis, env.platform, factory_bot_id=123456, templates={"groupguard"}, session=api
    )
    await service.pause(child)
    assert not raids.active(await raids.state(env, GROUP)) and not api.calls("UnbanChatMember")


async def test_raid_request_semantic_replay_declines_once_and_preserves_receipt(env, api):
    await send(env, group_msg("/antiraid on", ADMIN))
    request = ChatJoinRequest(
        chat=Chat(id=GROUP, type="supergroup"),
        from_user=tg_user(MEMBER),
        date=utcnow().replace(microsecond=0),
        user_chat_id=MEMBER,
    )
    for _ in range(3):
        await send(env, Update(update_id=group_msg("unique", MEMBER).update_id, chat_join_request=request))
    assert len(api.calls("DeclineChatJoinRequest")) == 1 and not api.calls("ApproveChatJoinRequest")


async def test_failed_restore_and_lookup_retry_does_not_manufacture_open_defaults(env, api):
    from aiogram.methods import GetChat

    current = track_permissions(api)
    cfg = await configure_night(env)
    await jobs.apply_night(env, GROUP, cfg)
    cfg = await env.extras["guard"].update_config(GROUP, night=False)
    good_get = api.responses["GetChat"]
    good_set = api.responses["SetChatPermissions"]
    api.responses["GetChat"] = TelegramBadRequest(method=GetChat(chat_id=GROUP), message="not found")
    before = len(api.calls("SetChatPermissions"))
    assert not (await jobs.apply_night(env, GROUP, cfg)).primary_completed
    assert len(api.calls("SetChatPermissions")) == before and current[GROUP].can_send_messages is False
    api.responses["GetChat"] = good_get
    api.responses["SetChatPermissions"] = TelegramBadRequest(
        method=SetChatPermissions(chat_id=GROUP, permissions=ChatPermissions(can_send_messages=True)),
        message="failed restore",
    )
    assert not (await jobs.apply_night(env, GROUP, cfg)).primary_completed
    api.responses["SetChatPermissions"] = good_set
    await jobs.night_job(env)
    assert current[GROUP].can_send_messages is True
    async with env.sm() as session:
        assert (await session.get(GuardNight, (env.bot_id, GROUP))).status == "restored"


async def test_same_window_admin_override_survives_but_explicit_new_policy_rearms(env, api):
    current = track_permissions(api)
    cfg = await configure_night(env)
    await jobs.apply_night(env, GROUP, cfg)
    current[GROUP] = ChatPermissions(can_send_messages=True, can_send_polls=True)
    cfg = await env.extras["guard"].update_config(GROUP, night=False)
    await jobs.apply_night(env, GROUP, cfg)
    before = len(api.calls("SetChatPermissions"))
    await jobs.apply_night(env, GROUP, cfg)
    assert len(api.calls("SetChatPermissions")) == before
    await send(env, group_msg("/night 0 23 " + str(cfg.tz_offset), ADMIN))
    assert current[GROUP].can_send_messages is False
    assert len(api.calls("SetChatPermissions")) == before + 1


async def test_raid_enable_button_bound_current_rights_and_stale_replay(env, api):
    await send(env, group_msg("/antiraid", MEMBER))
    card = api.messages[-1]
    value = api.calls("SendMessage")[-1].reply_markup.inline_keyboard[0][0].callback_data
    await send(env, bound_callback(value, card, MEMBER))
    assert not raids.active(await raids.state(env, GROUP))
    await send(env, bound_callback(value, card, ADMIN))
    current = await raids.state(env, GROUP)
    assert raids.active(current)
    await send(env, bound_callback(value, card, ADMIN))
    assert (await raids.state(env, GROUP)).generation == current.generation
    await send(env, group_msg("/antiraid off", ADMIN))
    await send(env, bound_callback(value, card, ADMIN))
    assert not raids.active(await raids.state(env, GROUP))
