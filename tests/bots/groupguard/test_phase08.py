"""Connections, policy, delayed cleanup, forum effects and operator isolation through real routers."""

from datetime import timedelta
from types import SimpleNamespace

from aiogram.types import ChatMemberLeft, ForumTopic
from sqlalchemy import select, update

from bots.groupguard import connections, durable, group_broadcast
from bots.groupguard.delivery import Content
from bots.groupguard.models import GuardChat, GuardJob
from core.db.base import utcnow
from tests.bots.groupguard.test_groupguard import (
    ADMIN,
    GROUP,
    MEMBER,
    bound_callback,
    gctx,
    group_msg,
    tg_user,
)
from tests.bots.groupguard.test_phase01a import admin_member, env, send
from tests.bots.groupguard.test_phase03 import pm

__all__ = ["env", "gctx"]


async def test_member_connection_reads_admin_mutation_actual_source_and_revocation(env, api):
    await send(env, pm("/connect " + str(GROUP), MEMBER))
    state = await connections.get(env, MEMBER)
    assert state.chat_id == GROUP and state.history == [GROUP]
    await send(env, pm("/addblocklist denied", MEMBER))
    assert not (await env.extras["guard"].config(GROUP)).blocklist_entries
    await send(env, pm("/connect " + str(GROUP), ADMIN))
    await send(env, pm("/addblocklist connected", ADMIN))
    assert (await env.extras["guard"].config(GROUP)).blocklist == ["connected"]
    async with env.sm() as session:
        assert await session.get(GuardChat, (env.bot_id, ADMIN)) is None
    old = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: (
        ChatMemberLeft(user=tg_user(ADMIN)) if m.user_id == ADMIN else old(m)
    )
    await send(env, pm("/addblocklist removed", ADMIN))
    assert (await env.extras["guard"].config(GROUP)).blocklist == ["connected"]
    assert (await connections.get(env, ADMIN)).chat_id is None


async def test_history_lastfive_personal_token_wrong_human_child_and_stale_role(env, api):
    for n in range(7):
        await send(env, pm("/connect " + str(-100500 - n), MEMBER))
    state = await connections.get(env, MEMBER)
    assert state.history == [-100506, -100505, -100504, -100503, -100502]
    await send(env, pm("/disconnect", MEMBER))
    assert (await connections.get(env, MEMBER)).chat_id is None
    await send(env, group_msg("/connect", MEMBER))
    start = api.calls("SendMessage")[-1].reply_markup.inline_keyboard[0][0].url.split("start=")[1]
    await send(env, pm("/start " + start, ADMIN))
    assert await connections.get(env, ADMIN) is None
    await send(env, pm("/start " + start, MEMBER))
    assert (await connections.get(env, MEMBER)).chat_id == GROUP
    for other in env.extras["test_contexts"]:
        if other.bot_id != env.bot_id:
            await send(other, pm("/start " + start, MEMBER))
            assert await connections.get(other, MEMBER) is None


async def test_disabled_alias_private_and_content_rule_link_policy_recovery(env, api):
    await send(env, group_msg("/setrules Visible rules", ADMIN))
    await send(env, group_msg("/disable rules antiflood", ADMIN))
    cfg = await env.extras["guard"].config(GROUP)
    assert set(cfg.disabled_commands) == {"rules", "flood"}
    before = len(api.calls("SendMessage"))
    await send(env, group_msg("/rules", MEMBER))
    await send(env, group_msg("/antiflood", MEMBER))
    assert len(api.calls("SendMessage")) == before
    await send(env, pm("/connect " + str(GROUP), MEMBER))
    before = len(api.calls("SendMessage"))
    await send(env, pm("/rules", MEMBER))
    assert len(api.calls("SendMessage")) == before
    await send(env, group_msg("/disableadmin on", ADMIN))
    before = len(api.calls("SendMessage"))
    await send(env, group_msg("/rules", ADMIN))
    assert len(api.calls("SendMessage")) == before
    await send(env, group_msg("/enable rules", ADMIN))
    await send(env, group_msg("/rules", ADMIN))
    assert api.calls("SendMessage")[-1].text == "Visible rules"


async def test_disabled_delete_and_after_handler_command_clean_actual_source(env, api):
    await send(env, group_msg("/disable id", ADMIN))
    await send(env, group_msg("/disabledel on", ADMIN))
    request = group_msg("/id", MEMBER)
    await send(env, request)
    assert api.calls("DeleteMessage")[-1].message_id == request.message.message_id
    await send(env, group_msg("/cleancommand user other", ADMIN))
    request = group_msg("/unknown@other_bot", MEMBER)
    await send(env, request)
    assert api.calls("DeleteMessage")[-1].message_id == request.message.message_id
    await send(env, pm("/connect " + str(GROUP), MEMBER))
    request = pm("/notes", MEMBER)
    await send(env, request)
    assert (
        api.calls("DeleteMessage")[-1].chat_id == MEMBER
        and api.calls("DeleteMessage")[-1].message_id == request.message.message_id
    )


async def test_actual_note_clean_job_receipt_five_minutes_restart_and_keep_cancels(env, api):
    await send(env, group_msg("/save card Body", ADMIN))
    await send(env, group_msg("/cleanmsg note", ADMIN))
    await send(env, group_msg("/get card", MEMBER))
    actual = api.messages[-1]
    async with env.sm() as session:
        job = (
            await session.execute(
                select(GuardJob).where(GuardJob.bot_id == env.bot_id, GuardJob.kind == "bot_message_clean")
            )
        ).scalar_one()
    assert (
        job.payload["message_id"] == actual.message_id
        and 290 <= (job.run_at - utcnow()).total_seconds() <= 301
    )
    await durable.sweep(env)
    assert not api.calls("DeleteMessage")
    async with env.sm() as session:
        await session.execute(
            update(GuardJob).where(GuardJob.id == job.id).values(run_at=utcnow() - timedelta(seconds=1))
        )
        await session.commit()
    await durable.sweep(env)
    assert api.calls("DeleteMessage")[-1].message_id == actual.message_id
    await send(env, group_msg("/get card", MEMBER))
    await send(env, group_msg("/keepmsg note", ADMIN))
    before = len(api.calls("DeleteMessage"))
    async with env.sm() as session:
        await session.execute(
            update(GuardJob)
            .where(GuardJob.bot_id == env.bot_id, GuardJob.status == "pending")
            .values(run_at=utcnow() - timedelta(seconds=1))
        )
        await session.commit()
    await durable.sweep(env)
    assert len(api.calls("DeleteMessage")) == before


async def test_topic_actual_general_methods_scoped_confirmation_role_and_replay(env, api):
    old_chat = api.responses["GetChat"]
    api.responses["GetChat"] = lambda m: old_chat(m).model_copy(update={"is_forum": True})
    old = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: (
        admin_member(
            env.bot_id,
            can_manage_topics=True,
            can_change_info=True,
            can_delete_messages=True,
            can_restrict_members=True,
        )
        if m.user_id == env.bot_id
        else old(m)
    )
    api.responses["CreateForumTopic"] = ForumTopic(message_thread_id=77, name="New", icon_color=0x6FB9F0)
    await send(env, group_msg("/newtopic New", MEMBER))
    assert not api.calls("CreateForumTopic")
    await send(env, group_msg("/newtopic New", ADMIN))
    assert api.calls("CreateForumTopic")[-1].name == "New"
    await send(env, group_msg("/closetopic", ADMIN))
    assert api.calls("CloseGeneralForumTopic")
    await send(env, group_msg("/reopentopic", ADMIN))
    assert api.calls("ReopenGeneralForumTopic")
    await send(env, group_msg("/deletetopic", ADMIN, message_thread_id=77))
    card = api.messages[-1]
    value = api.calls("SendMessage")[-1].reply_markup.inline_keyboard[0][0].callback_data
    await send(env, bound_callback(value, card, MEMBER))
    assert not api.calls("DeleteForumTopic")
    await send(env, bound_callback(value, card, ADMIN))
    assert api.calls("DeleteForumTopic")[-1].message_thread_id == 77
    await send(env, bound_callback(value, card, ADMIN))
    assert len(api.calls("DeleteForumTopic")) == 1


async def test_echo_real_formatted_output_connected_and_owner_broadcast_separate(env, api):
    await send(env, pm("/connect " + str(GROUP), ADMIN))
    await send(env, pm("/say *Bold* {mention}", ADMIN))
    call = api.calls("SendMessage")[-1]
    assert call.chat_id == GROUP and "<b>Bold</b>" in call.text and "tg://user?id=10" in call.text
    await send(env, group_msg("/broadcast Nope", ADMIN))
    assert not await group_broadcast.create(env, tg_user(ADMIN), Content("Nope"))
    operator = (
        env.child.owner_id
        if env.child is not None
        else (env.env.admin_ids or env.platform.super_admin_ids)[0]
    )
    await send(env, pm("/broadcast Announcement", operator))
    await group_broadcast.tick(env)
    await durable.sweep(env)
    assert any(m.chat_id == GROUP and m.text == "Announcement" for m in api.calls("SendMessage"))
    for other in env.extras["test_contexts"]:
        if other.bot_id != env.bot_id:
            async with env.sm() as session:
                assert (
                    not (
                        await session.execute(
                            select(GuardJob).where(
                                GuardJob.bot_id == other.bot_id, GuardJob.kind == "group_broadcast"
                            )
                        )
                    )
                    .scalars()
                    .all()
                )


def bot_command(text):
    request = group_msg(text, 88)
    return request.model_copy(
        update={
            "message": request.message.model_copy(
                update={
                    "from_user": tg_user(88).model_copy(update={"is_bot": True, "username": "builder_bot"})
                }
            )
        }
    )


def bot_admin(api, *, restrict=True):
    original = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: (
        admin_member(
            88, can_change_info=True, can_restrict_members=restrict, can_delete_messages=True
        ).model_copy(update={"user": tg_user(88).model_copy(update={"is_bot": True})})
        if m.user_id == 88
        else original(m)
    )
    return original


async def test_bot_mutation_default_off_human_review_revocation_and_no_creator(env, api):
    bot_admin(api)
    await send(env, bot_command("/ban 20 reason"))
    assert not api.calls("BanChatMember")
    await send(env, group_msg("/bot2bot admin", ADMIN))
    await send(env, bot_command("/ban 20 reason"))
    assert not api.calls("BanChatMember")
    card = api.messages[-1]
    value = api.calls("SendMessage")[-1].reply_markup.inline_keyboard[0][0].callback_data
    await send(env, bound_callback(value, card, MEMBER))
    assert not api.calls("BanChatMember")
    await send(env, bound_callback(value, card, ADMIN))
    assert api.calls("BanChatMember")[-1].user_id == MEMBER
    before = len(api.calls("BanChatMember"))
    await send(env, bound_callback(value, card, ADMIN))
    assert len(api.calls("BanChatMember")) == before
    await send(env, bot_command("/ban 30 another"))
    card = api.messages[-1]
    value = api.calls("SendMessage")[-1].reply_markup.inline_keyboard[0][0].callback_data
    bot_admin(api, restrict=False)
    await send(env, bound_callback(value, card, ADMIN))
    assert len(api.calls("BanChatMember")) == before
    await env.extras["guard"].update_config(GROUP, log_chat_id=-10088)
    await send(env, bot_command("/silentactions on"))
    assert not (await env.extras["guard"].config(GROUP)).silent_actions_allowed


async def test_skipreview_keeps_real_bot_rights_and_blocks_own_reply_and_repeat_loops(env, api):
    bot_admin(api)
    await send(env, group_msg("/bot2bot admin", ADMIN))
    await send(env, group_msg("/bot2botskipreview on", ADMIN))
    request = bot_command("/ban 20 direct")
    await send(env, request)
    assert len(api.calls("BanChatMember")) == 1
    request = bot_command("/ban 20 direct")
    await send(env, request)
    assert len(api.calls("BanChatMember")) == 1
    replied = bot_command("/ban 30 loop")
    replied = replied.model_copy(
        update={"message": replied.message.model_copy(update={"reply_to_message": api.messages[-1]})}
    )
    await send(env, replied)
    assert len(api.calls("BanChatMember")) == 1
    bot_admin(api, restrict=False)
    await send(env, bot_command("/ban 30 no right"))
    assert len(api.calls("BanChatMember")) == 1


async def test_creator_silent_gate_does_not_convert_policies_and_manual_silence_stays_separate(env, api):
    svc = env.extras["guard"]
    await send(env, group_msg("/silentactions on", ADMIN))
    assert not (await svc.config(GROUP)).silent_actions_allowed
    await svc.update_config(GROUP, log_chat_id=-10088)
    await send(env, group_msg("/silentactions on", MEMBER))
    assert not (await svc.config(GROUP)).silent_actions_allowed
    await send(env, group_msg("/silentactions on", ADMIN))
    cfg = await svc.config(GROUP)
    assert cfg.silent_actions_allowed and not cfg.flood_silent
    await send(env, group_msg("/silentactions off", ADMIN))
    await send(env, group_msg("/sban 20", ADMIN))
    assert api.calls("BanChatMember")[-1].user_id == MEMBER


async def test_native_payment_handler_commits_before_service_cleanup(gctx, api, monkeypatch):
    from aiogram.types import Chat

    from core.routers.vip import InvoicePayload
    from tests.conftest import payment_update

    await send(gctx, group_msg("/cleanservice other", ADMIN))
    request = payment_update(
        InvoicePayload(slug=gctx.slug, plan_id=1, user_id=MEMBER, days=30, stars=100).encode(),
        100,
        "phase08-payment",
        MEMBER,
    )
    request = request.model_copy(
        update={"message": request.message.model_copy(update={"chat": Chat(id=GROUP, type="supergroup")})}
    )
    actual_id = request.message.message_id
    original = gctx.payments.record_payment
    observed = []

    async def record(*args, **kwargs):
        assert not any(m.message_id == actual_id for m in api.calls("DeleteMessage"))
        result = await original(*args, **kwargs)
        observed.append(result)
        return result

    monkeypatch.setattr(gctx.payments, "record_payment", record)
    await send(gctx, request)
    assert observed and (await gctx.users.get(MEMBER)).is_vip()
    assert api.calls("DeleteMessage")[-1].message_id == actual_id


async def test_context_id_and_private_group_message_deletion_deny(env, api):
    await send(env, pm("/connect " + str(GROUP), ADMIN))
    await send(env, pm("/id", ADMIN))
    assert str(GROUP) in api.calls("SendMessage")[-1].text
    await send(env, pm("/purge", ADMIN))
    assert not api.calls("DeleteMessages")


async def test_private_silent_action_deletes_actual_private_command_and_never_group_id(env, api):
    await send(env, pm("/connect " + str(GROUP), ADMIN))
    request = pm("/sban 20", ADMIN)
    await send(env, request)
    assert api.calls("BanChatMember")[-1].chat_id == GROUP
    assert api.calls("DeleteMessage")[-1].chat_id == ADMIN
    assert api.calls("DeleteMessage")[-1].message_id == request.message.message_id


async def test_direct_reconnect_cannot_bypass_disabled_connection_and_public_username_proof(env, api):
    await send(env, group_msg("/disable connect", ADMIN))
    await send(env, pm("/connect " + str(GROUP), MEMBER))
    assert await connections.get(env, MEMBER) is None
    await send(env, pm("/reconnect " + str(GROUP), MEMBER))
    assert await connections.get(env, MEMBER) is None
    await send(env, group_msg("/enable connect", ADMIN))
    original = api.responses["GetChat"]
    api.responses["GetChat"] = lambda m: (
        original(type("Request", (), {"chat_id": GROUP})()).model_copy(update={"username": "clubgroup"})
        if isinstance(m.chat_id, str)
        else original(m)
    )
    await send(env, pm("/connect @wronggroup", MEMBER))
    assert await connections.get(env, MEMBER) is None
    await send(env, pm("/connect @clubgroup", MEMBER))
    assert (await connections.get(env, MEMBER)).chat_id == GROUP


async def test_lock_explicit_silent_creator_gate_removed_log_loud_fallback(env, api):
    await send(env, group_msg("/lock url {sban}", ADMIN))
    assert not (await env.extras["guard"].config(GROUP)).locks
    await env.extras["guard"].update_config(GROUP, log_chat_id=-10088)
    await send(env, group_msg("/silentactions on", ADMIN))
    await send(env, group_msg("/lock url {sban}", ADMIN))
    before = len([m for m in api.calls("SendMessage") if m.chat_id == GROUP])
    await send(env, group_msg("https://evil.example", MEMBER))
    assert (
        api.calls("BanChatMember")
        and len([m for m in api.calls("SendMessage") if m.chat_id == GROUP]) == before
    )
    await env.extras["guard"].update_config(GROUP, log_chat_id=None)
    await send(env, group_msg("https://evil.example/new", MEMBER))
    assert api.calls("SendMessage")[-1].chat_id == GROUP


async def test_service_categories_native_fields_and_legacy_defaults(env, api):
    from aiogram.types import PhotoSize, VideoChatStarted

    await send(env, group_msg("/cleanservice photo title videochat", ADMIN))
    extras = [
        {"new_chat_photo": [PhotoSize(file_id="f", file_unique_id="u", width=10, height=10)]},
        {"new_chat_title": "New title"},
        {"video_chat_started": VideoChatStarted()},
    ]
    for extra in extras:
        request = group_msg("service", MEMBER)
        request = request.model_copy(
            update={"message": request.message.model_copy(update={"text": None, **extra})}
        )
        await send(env, request)
        assert api.calls("DeleteMessage")[-1].message_id == request.message.message_id
    await send(env, group_msg("/nocleanservice title", ADMIN))
    before = len(api.calls("DeleteMessage"))
    request = group_msg("service", MEMBER)
    request = request.model_copy(
        update={"message": request.message.model_copy(update={"text": None, "new_chat_title": "Keep"})}
    )
    await send(env, request)
    assert len(api.calls("DeleteMessage")) == before


async def test_topic_action_destination_and_revoked_confirmation_remains_denied(env, api):
    original = api.responses["GetChat"]
    api.responses["GetChat"] = lambda m: original(m).model_copy(update={"is_forum": True})
    old = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: (
        admin_member(
            env.bot_id,
            can_manage_topics=True,
            can_change_info=True,
            can_restrict_members=True,
            can_delete_messages=True,
        )
        if m.user_id == env.bot_id
        else old(m)
    )
    await send(env, group_msg("/setactiontopic", ADMIN, message_thread_id=77))
    assert (await env.extras["guard"].config(GROUP)).action_topic == 77
    await send(env, group_msg("/ban 20 topic", ADMIN, message_thread_id=8))
    assert api.calls("SendMessage")[-1].message_thread_id == 77
    await send(env, group_msg("/deletetopic", ADMIN, message_thread_id=88))
    card = api.messages[-1]
    value = api.calls("SendMessage")[-1].reply_markup.inline_keyboard[0][0].callback_data
    prior = api.responses["GetChatMember"]
    from aiogram.types import ChatMemberMember

    api.responses["GetChatMember"] = lambda m: (
        ChatMemberMember(user=tg_user(ADMIN)) if m.user_id == ADMIN else prior(m)
    )
    await send(env, bound_callback(value, card, ADMIN))
    assert not api.calls("DeleteForumTopic")


async def test_group_broadcast_destination_failures_are_isolated_and_recorded(env, api):
    from aiogram.exceptions import TelegramForbiddenError
    from aiogram.types import Chat, Message

    extra = -10044
    await env.extras["guard"].ensure_chat(extra, "Other group")
    operator = env.child.owner_id if env.child else (env.env.admin_ids or env.platform.super_admin_ids)[0]
    await send(env, pm("/broadcast Payload", operator))
    await group_broadcast.tick(env)

    def response(method):
        if method.text == "Payload" and method.chat_id == extra:
            return TelegramForbiddenError(method=method, message="bot removed")
        return Message(
            message_id=70000 + len(api.requests),
            date=utcnow(),
            chat=Chat(id=method.chat_id, type="supergroup" if method.chat_id < 0 else "private"),
            text=method.text,
        )

    api.responses["SendMessage"] = response
    await durable.sweep(env)
    async with env.sm() as session:
        jobs = list(
            (
                await session.execute(
                    select(GuardJob).where(GuardJob.bot_id == env.bot_id, GuardJob.kind == "group_broadcast")
                )
            ).scalars()
        )
    assert {job.chat_id: job.status for job in jobs} == {GROUP: "succeeded", extra: "failed"}
    assert any(m.chat_id == GROUP and m.text == "Payload" for m in api.calls("SendMessage"))


async def test_local_broadcast_rate_wait_does_not_consume_api_retry_budget(env, api, monkeypatch):
    operator = env.child.owner_id if env.child else (env.env.admin_ids or env.platform.super_admin_ids)[0]
    await send(env, pm("/broadcast Rate limited", operator))
    await group_broadcast.tick(env)
    import time

    now = time.time()
    # Seed and consume the same bucket even when the sweep crosses a second.
    monkeypatch.setattr(group_broadcast, "time", SimpleNamespace(time=lambda: now))
    await env.redis.set(env.keys("guard_outbound_rate", int(now)), 100, ex=60)
    await durable.sweep(env)
    async with env.sm() as session:
        job = (
            await session.execute(
                select(GuardJob).where(GuardJob.bot_id == env.bot_id, GuardJob.kind == "group_broadcast")
            )
        ).scalar_one()
    assert job.status == "pending" and job.attempts == 0 and job.error_code == "local_rate"
    assert not any(m.text == "Rate limited" and m.chat_id == GROUP for m in api.calls("SendMessage"))


async def test_invalid_legacy_night_key_does_not_abort_progress(gctx):
    from bots.groupguard import jobs

    await gctx.redis.set(gctx.keys("night_closed", "not-an-id"), "{}")
    await jobs.night_job(gctx)
    assert "night_scan_cursor" in gctx.extras


async def test_bot_clean_never_queues_a_boolean_notification_as_a_message_receipt(env, api):
    from bots.groupguard import actions
    from bots.groupguard.contracts import StepResult, result_of

    await env.extras["guard"].update_config(GROUP, bot_clean_types=["action"])
    api.responses["SendMessage"] = True
    cfg = await env.extras["guard"].config(GROUP)
    result = await actions.announce(
        env, cfg, GROUP, "Group", result_of(StepResult("test", "applied")), "Done"
    )
    assert result.primary_completed and result.status == "partial"
    assert any(step.error_code == "missing_owned_receipt" for step in result.steps)
    async with env.sm() as session:
        assert (
            not (
                await session.execute(
                    select(GuardJob).where(
                        GuardJob.bot_id == env.bot_id, GuardJob.kind == "bot_message_clean"
                    )
                )
            )
            .scalars()
            .all()
        )


async def test_campaign_cancelled_during_render_never_dispatches(env, api, monkeypatch):
    from bots.groupguard import delivery
    from bots.groupguard.models import GuardBroadcast

    operator = env.child.owner_id if env.child else env.platform.super_admin_ids[0]
    await send(env, pm('/broadcast Cancel during render', operator))
    await group_broadcast.tick(env)
    original = delivery.fillings

    async def cancel(*args, **kwargs):
        filled = await original(*args, **kwargs)
        async with env.sm() as session:
            await session.execute(update(GuardBroadcast).where(
                GuardBroadcast.bot_id == env.bot_id).values(status='cancelled'))
            await session.commit()
        return filled

    monkeypatch.setattr(delivery, 'fillings', cancel)
    await durable.sweep(env)
    assert not any(m.text == 'Cancel during render' and m.chat_id == GROUP for m in api.calls('SendMessage'))
    await send(env, pm('/broadcast', operator))
    assert 'cancelled' in api.calls('SendMessage')[-1].text


async def test_broadcast_retry_and_unknown_outcome_do_not_blindly_repeat(env, api):
    from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter

    operator = env.child.owner_id if env.child else env.platform.super_admin_ids[0]
    await send(env, pm('/broadcast Retry then uncertain', operator))
    await group_broadcast.tick(env)
    api.responses['SendMessage'] = lambda m: TelegramRetryAfter(method=m, message='wait', retry_after=2)
    await durable.sweep(env)
    async with env.sm() as session:
        job = (await session.execute(select(GuardJob).where(
            GuardJob.bot_id == env.bot_id, GuardJob.kind == 'group_broadcast'))).scalar_one()
        assert job.status == 'pending' and job.attempts == 1 and not job.dispatched
        await session.execute(update(GuardJob).where(GuardJob.id == job.id).values(run_at=utcnow()))
        await session.commit()
    api.responses['SendMessage'] = lambda m: TelegramNetworkError(method=m, message='unknown receipt')
    await durable.sweep(env)
    before = len(api.calls('SendMessage'))
    await durable.recover(env)
    await durable.sweep(env)
    assert len(api.calls('SendMessage')) == before
    async with env.sm() as session:
        state = await session.get(GuardJob, job.id)
        assert state.status == 'uncertain' and state.attempts == 2


async def test_posted_broadcast_attachment_is_not_repeated_after_companion_throttle(env, api):
    from aiogram.exceptions import TelegramRetryAfter

    operator = env.child.owner_id if env.child else env.platform.super_admin_ids[0]
    campaign = await group_broadcast.create(env, tg_user(operator), Content(
        'x' * 1100, media_kind='photo', file_id='photo-file'))
    assert campaign is not None
    await group_broadcast.tick(env)
    api.responses['SendMessage'] = lambda m: TelegramRetryAfter(method=m, message='companion wait', retry_after=1)
    await durable.sweep(env)
    await durable.sweep(env)
    assert len(api.calls('SendPhoto')) == 1
    async with env.sm() as session:
        job = (await session.execute(select(GuardJob).where(
            GuardJob.bot_id == env.bot_id, GuardJob.kind == 'group_broadcast'))).scalar_one()
        assert job.status == 'failed' and job.error_code == 'retry_after'


async def test_welcome_action_topic_missing_target_has_no_fallback(env, api):
    from aiogram.exceptions import TelegramBadRequest

    from bots.groupguard import greetings

    await env.extras['guard'].update_config(GROUP, action_topic=77)
    cfg = await env.extras['guard'].config(GROUP)
    api.responses['SendMessage'] = lambda m: TelegramBadRequest(method=m, message='message thread not found')
    sent = await greetings.send(env, cfg, GROUP, tg_user(MEMBER), thread_id=8)
    assert not sent.result.primary_completed
    assert api.calls('SendMessage')[-1].message_thread_id == 77
    assert len(api.calls('SendMessage')) == 1


async def test_bot_restricted_nonmember_cannot_gain_public_command_authority(env, api):
    from aiogram.types import ChatMemberRestricted

    from bots.groupguard import authz

    await env.extras['guard'].update_config(GROUP, bot2bot_mode='all')
    prior = api.responses['GetChatMember']
    api.responses['GetChatMember'] = lambda m: ChatMemberRestricted(
        user=tg_user(88).model_copy(update={'is_bot': True}), is_member=False, until_date=0,
        can_send_messages=False, can_send_audios=False, can_send_documents=False,
        can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
        can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
        can_add_web_page_previews=False, can_change_info=False, can_invite_users=False,
        can_pin_messages=False, can_manage_topics=False, can_react_to_messages=False,
        can_edit_tag=False) if m.user_id == 88 else prior(m)
    actor = authz.actor_from_message(env, bot_command('/id').message)
    allowed = await authz.authorize(env, actor, target_chat_id=GROUP,
        caller_rights=frozenset(), bot_rights=frozenset(), require_admin=False)
    assert not allowed.allowed
    before = len(api.calls('SendMessage'))
    await send(env, bot_command('/id'))
    assert len(api.calls('SendMessage')) == before
