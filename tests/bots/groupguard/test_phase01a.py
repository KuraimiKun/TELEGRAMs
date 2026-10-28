"""Adversarial authorization and outcome evidence through real Group Guard routers and child registry."""

from __future__ import annotations

import asyncio
import json
import time
from datetime import timedelta

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.methods import BanChatMember, GetChat, UnbanChatMember
from aiogram.types import (
    Chat,
    ChatMemberAdministrator,
    ChatMemberMember,
    ChatMemberOwner,
    MessageEntity,
    User,
)
from redis.exceptions import ConnectionError

from bots.groupguard import actions, authz, perms, reviews
from bots.groupguard.contracts import Actor
from bots.groupguard.handlers.moderation import apply_warn
from bots.groupguard.jobs import apply_night
from bots.groupguard.operations import execute, operation_for
from core.db.models import Bot as BotRecord
from core.db.models import ChildBot
from core.factory.crypto import encrypt_token
from core.factory.runtime import ChildRegistry
from core.runtime.dispatcher import build_dispatcher
from core.sdk.registry import SharedInfra
from tests.bots.groupguard.test_groupguard import (
    ADMIN,
    GROUP,
    MEMBER,
    bound_callback,
    gctx,
    group_msg,
    plain,
    tg_user,
)

__all__ = ["gctx"]
CHILDREN = (710011, 710012)


def admin_member(uid, **rights):
    fields = dict(
        can_change_info=False,
        can_delete_messages=False,
        can_restrict_members=False,
        can_pin_messages=False,
        can_invite_users=False,
        can_promote_members=False,
        can_manage_topics=False,
        can_post_messages=False,
    )
    fields.update(rights)
    return ChatMemberAdministrator(
        user=tg_user(uid),
        is_anonymous=False,
        can_be_edited=False,
        can_manage_chat=True,
        can_manage_video_chats=False,
        can_post_stories=False,
        can_edit_stories=False,
        can_delete_stories=False,
        can_send_welcome_messages=False,
        **fields,
    )


@pytest.fixture(params=["standalone", *CHILDREN], ids=["standalone", "child-A", "child-B"])
async def env(request, gctx, api, sm, redis):
    registry = None
    contexts = [gctx]
    if request.param != "standalone":
        async with sm() as s:
            for bid in CHILDREN:
                s.add(BotRecord(id=bid, slug=f"c{bid}", title="Guard child", active=True))
                s.add(
                    ChildBot(
                        bot_id=bid,
                        owner_id=777,
                        factory_bot_id=gctx.bot_id,
                        template="groupguard",
                        token_enc=encrypt_token(gctx.platform, f"{bid}:" + "A" * 35),
                        username=f"guard{bid}_bot",
                        title="Guard child",
                    )
                )
            await s.commit()
        infra = SharedInfra(engine=sm.kw["bind"], sm=sm, redis=redis, cache_redis=redis, session=api)
        registry = ChildRegistry(gctx.platform, infra, asyncio.Event(), templates={"groupguard": gctx.module})
        for bid in CHILDREN:
            api.responses["GetMe"] = User(id=bid, is_bot=True, first_name="Guard", username=f"guard{bid}_bot")
            runtime = await registry.get(bid)
            assert runtime is not None and runtime.ctx.child.template == "groupguard"
            contexts.append(runtime.ctx)
        ctx = next(c for c in contexts if c.bot_id == request.param)
    else:
        ctx = gctx
    bot_ids = {c.bot_id for c in contexts}
    original = api.responses["GetChatMember"]

    def membership(m):
        if m.user_id in bot_ids:
            return admin_member(
                m.user_id,
                can_restrict_members=True,
                can_delete_messages=True,
                can_pin_messages=True,
                can_change_info=True,
                can_invite_users=True,
            ).model_copy(update={"user": tg_user(m.user_id).model_copy(update={"is_bot": True})})
        if m.user_id == ADMIN:
            return ChatMemberOwner(user=tg_user(ADMIN), is_anonymous=False)
        return ChatMemberMember(user=tg_user(m.user_id).model_copy(update={"username": f"u{m.user_id}"}))

    api.responses["GetChatMember"] = membership
    for c in contexts:
        await c.extras["guard"].update_config(GROUP, flood_count=0)
    ctx.extras["test_contexts"] = contexts
    ctx.extras["test_registry"] = registry
    yield ctx
    api.responses["GetChatMember"] = original
    if registry:
        await registry.close()


def domain_calls(api):
    return [
        m
        for m in api.requests
        if type(m).__name__
        in {
            "BanChatMember",
            "UnbanChatMember",
            "RestrictChatMember",
            "DeleteMessage",
            "DeleteMessages",
            "PinChatMessage",
            "UnpinChatMessage",
            "SetChatPermissions",
            "ApproveChatJoinRequest",
        }
    ]


def bad(method):
    return TelegramBadRequest(method=method, message="mock failure")


async def send(ctx, update):
    await build_dispatcher_once(ctx).feed_update(ctx.bot, update)


def build_dispatcher_once(ctx):
    if "test_dp" not in ctx.extras:
        ctx.extras["test_dp"] = build_dispatcher(ctx)
    return ctx.extras["test_dp"]


async def make_review(ctx, api, text="/ban spam <bad>"):
    update = group_msg(
        text, 1087968824, reply_to=plain(MEMBER), sender_chat=Chat(id=GROUP, type="supergroup")
    )
    await send(ctx, update)
    msg = next(m for m in reversed(api.messages) if m.chat.id == GROUP and "Review:" in (m.text or ""))
    call = next(m for m in reversed(api.calls("SendMessage")) if m.reply_markup and m.chat_id == GROUP)
    data = call.reply_markup.inline_keyboard[0][0].callback_data
    nonce = data.rsplit(":", 1)[1]
    return msg, data, nonce


async def test_actor_escalation_creator_and_cached_aliases(env, api):
    for uid, extras in [
        (1087968824, {}),
        (777, {}),
        (999, {}),
        (MEMBER, {"sender_chat": Chat(id=-100888, type="channel")}),
    ]:
        await send(env, group_msg("/warn spam", uid, reply_to=plain(30), **extras))
    bot_update = group_msg("/warn spam", MEMBER, reply_to=plain(30))
    bot_update = bot_update.model_copy(
        update={
            "message": bot_update.message.model_copy(
                update={"from_user": tg_user(MEMBER).model_copy(update={"is_bot": True})}
            )
        }
    )
    await send(env, bot_update)
    assert not domain_calls(api) and await env.extras["guard"].count_warns(GROUP, 30) == 0
    anonymous = authz.actor_from_message(
        env, group_msg("/ban", 1087968824, sender_chat=Chat(id=GROUP, type="supergroup")).message
    )
    assert anonymous.kind == "anonymous_group" and anonymous.human_id is None
    lookup = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: (
        admin_member(ADMIN, can_change_info=True) if m.user_id == ADMIN else lookup(m)
    )
    actor = Actor(env.bot_id, GROUP, "human", ADMIN)
    assert not (
        await authz.authorize(
            env, actor, target_chat_id=GROUP, caller_rights=frozenset({"creator"}), bot_rights=frozenset()
        )
    ).allowed
    api.responses["GetChatMember"] = lookup
    assert (
        await authz.authorize(
            env, actor, target_chat_id=GROUP, caller_rights=frozenset({"creator"}), bot_rights=frozenset()
        )
    ).allowed
    await env.redis.set(
        env.keys("admins", GROUP), json.dumps({str(ADMIN): {"is_admin": True, "restrict": True}})
    )
    cached = (await perms.admins(env, GROUP))[ADMIN]
    assert cached.allows("restrict_members") and not cached.allows("manage_topics")


@pytest.mark.parametrize(
    "case", ["unrelated", "bot-missing", "demoted", "lookup", "compound-human", "compound-bot"]
)
async def test_fresh_union_zero_mutations(env, api, case):
    original = api.responses["GetChatMember"]
    await env.redis.set(
        env.keys("admins", GROUP), json.dumps({str(ADMIN): {"is_admin": True, "creator": True}})
    )

    def current(m):
        if case == "lookup":
            return bad(m)
        if m.user_id == ADMIN and case in {"unrelated", "compound-human"}:
            return admin_member(ADMIN, can_restrict_members=case == "compound-human", can_pin_messages=True)
        if m.user_id == ADMIN and case == "demoted":
            return ChatMemberMember(user=tg_user(ADMIN))
        if m.user_id == env.bot_id and case in {"bot-missing", "compound-bot"}:
            return admin_member(env.bot_id, can_restrict_members=case == "compound-bot")
        return original(m)

    api.responses["GetChatMember"] = current
    await send(
        env,
        group_msg(
            "/sban spam" if case.startswith("compound") else "/warn spam", ADMIN, reply_to=plain(MEMBER)
        ),
    )
    assert not domain_calls(api) and await env.extras["guard"].count_warns(GROUP, MEMBER) == 0
    assert api.calls("GetChatMember")


async def test_settings_pure_sql_and_bound_panel_scope_revocation(env, api):
    original = api.responses["GetChatMember"]

    def current(m):
        if m.user_id == env.bot_id:
            return admin_member(env.bot_id)  # Pure settings do not require restrict/delete.
        if m.user_id == ADMIN:
            return admin_member(ADMIN, can_change_info=True)
        return original(m)

    api.responses["GetChatMember"] = current
    await send(env, group_msg("/lock links", ADMIN))
    assert (await env.extras["guard"].config(GROUP, fresh=True)).locks == ["url"]  # canonical storage; links remains an alias
    await send(env, group_msg("/settings", ADMIN))
    panel = next(m for m in reversed(api.messages) if m.chat.id == ADMIN)
    callback = f"gg:set:{GROUP}:0:cap"
    for changes, user in [
        ({}, MEMBER),
        ({"message_id": panel.message_id + 9}, ADMIN),
        ({"chat": Chat(id=22, type="private")}, ADMIN),
        ({"message_thread_id": 9}, ADMIN),
        ({"from_user": User(id=987654, is_bot=True, first_name="Other")}, ADMIN),
    ]:
        await send(env, bound_callback(callback, panel.model_copy(update=changes), user))
    await send(env, bound_callback(callback.replace(str(GROUP), "-10099"), panel, ADMIN))
    assert (await env.extras["guard"].config(GROUP, fresh=True)).captcha == "button"
    await send(env, bound_callback(callback, panel, ADMIN))
    assert (await env.extras["guard"].config(GROUP, fresh=True)).captcha == "math"
    await send(env, bound_callback(f"gg:locks:{GROUP}:0:", panel, ADMIN))
    assert api.calls("EditMessageText")[-1].reply_markup
    await send(env, bound_callback(f"gg:lock:{GROUP}:0:links", panel, ADMIN))
    assert (await env.extras["guard"].config(GROUP, fresh=True)).locks == []
    api.responses["GetChatMember"] = lambda m: (
        ChatMemberMember(user=tg_user(ADMIN)) if m.user_id == ADMIN else current(m)
    )
    await send(env, bound_callback(callback, panel, ADMIN))
    await send(env, bound_callback(f"gg:close:{GROUP}:0:", panel.model_copy(update={"message_id": 1}), ADMIN))
    assert (await env.extras["guard"].config(GROUP, fresh=True)).captcha == "math" and not api.calls(
        "DeleteMessage"
    )


async def test_anonymous_review_invalid_attempt_concurrent_one_use_attribution(env, api):
    msg, data, nonce = await make_review(env, api)
    assert "&lt;bad&gt;" in msg.text and len(nonce) == 22 and not api.calls("BanChatMember")
    key = reviews.review_key(env, nonce)
    assert 0 < await env.redis.ttl(key) <= 120
    await send(env, bound_callback(data, msg, MEMBER))
    await send(env, bound_callback(data, msg.model_copy(update={"message_thread_id": 999}), ADMIN))
    await send(env, bound_callback(data.replace(str(GROUP), "-100999"), msg, ADMIN))
    assert await env.redis.exists(key) and not api.calls("BanChatMember")
    # Any currently privileged human may approve an anonymous operation.
    original = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: (
        admin_member(11, can_restrict_members=True) if m.user_id == 11 else original(m)
    )
    await asyncio.gather(
        *(
            reviews.approve_review(
                env, bound_callback(data, msg, 11).callback_query.as_(env.bot), nonce, callback_chat=GROUP
            )
            for _ in range(8)
        )
    )
    assert len(api.calls("BanChatMember")) == 1 and not await env.redis.exists(key)
    audit = (await env.audit.recent())[0]
    assert (
        audit.admin_id == 11
        and audit.details["reviewed"]
        and audit.details["original_actor"] == "anonymous_group"
    )
    assert all("tg://user?id=11" not in (m.text or "") for m in api.calls("SendMessage"))
    await send(env, bound_callback(data, msg, ADMIN))
    assert len(api.calls("BanChatMember")) == 1


@pytest.mark.parametrize(
    "case",
    ["expired", "altered", "wrong-message", "wrong-bot", "redis", "execution-failure", "after-claim-revoked"],
)
async def test_review_state_denial_and_failed_execution_consumed(env, api, monkeypatch, case):
    msg, data, nonce = await make_review(env, api)
    key = reviews.review_key(env, nonce)
    if case in {"expired", "altered"}:
        state = json.loads(await env.redis.get(key))
        if case == "expired":
            state["expires"] = time.time() - 1
        else:
            op = json.loads(state["operation"])
            op["target_id"] = 30
            state["operation"] = json.dumps(op)
        await env.redis.set(key, json.dumps(state), ex=120)
    if case == "wrong-message":
        msg = msg.model_copy(update={"message_id": msg.message_id + 1})
    if case == "wrong-bot":
        msg = msg.model_copy(update={"from_user": tg_user(987654)})
    if case == "redis":

        async def fail(*a, **kw):
            raise ConnectionError("unavailable")

        monkeypatch.setattr(env.redis, "execute_command", fail)
    if case == "execution-failure":
        api.responses["BanChatMember"] = bad(BanChatMember(chat_id=GROUP, user_id=MEMBER))
    if case == "after-claim-revoked":
        orig_execute = reviews.execute

        async def revoked(ctx, actor, op, **kw):
            original = api.responses["GetChatMember"]
            api.responses["GetChatMember"] = lambda m: (
                ChatMemberMember(user=tg_user(ADMIN)) if m.user_id == ADMIN else original(m)
            )
            return await orig_execute(ctx, actor, op, **kw)

        monkeypatch.setattr(reviews, "execute", revoked)
    await send(env, bound_callback(data, msg, ADMIN))
    if case == "redis":
        assert not api.calls("BanChatMember")
        return
    assert len(api.calls("BanChatMember")) == (1 if case == "execution-failure" else 0)
    if case in {"execution-failure", "after-claim-revoked"}:
        assert not await env.redis.exists(key)
        await send(env, bound_callback(data, msg, ADMIN))
        assert len(api.calls("BanChatMember")) == (1 if case == "execution-failure" else 0)
    else:
        assert await env.redis.exists(key)


async def test_target_forms_reason_preservation_username_staleness(env, api):
    reply = group_msg("/ban spam 2026  <x>", ADMIN, reply_to=plain(MEMBER)).message
    assert (await perms.resolve_target(env, reply, "spam 2026  <x>")).remaining == "spam 2026  <x>"
    entity = group_msg(
        "/ban Alice Smith 1m first  reason",
        ADMIN,
        entities=[MessageEntity(type="text_mention", offset=5, length=11, user=tg_user(MEMBER))],
    ).message
    target = await perms.resolve_target(env, entity, "Alice Smith 1m first  reason")
    duration, reason = perms.split_action_args(target.remaining)
    assert target.user_id == MEMBER and duration.value == timedelta(minutes=1) and reason == "first  reason"
    await perms.remember(env, tg_user(MEMBER).model_copy(update={"username": f"u{MEMBER}"}))
    target = await perms.resolve_target(
        env, group_msg(f"/ban @u{MEMBER} spam", ADMIN).message, f"@u{MEMBER} spam"
    )
    assert target.user_id == MEMBER and target.remaining == "spam"
    for raw in ["@unknown spam", "-100 spam", "1087968824 spam", "99999999999999999999 spam"]:
        with pytest.raises(perms.TargetError):
            await perms.resolve_target(env, group_msg("/ban " + raw, ADMIN).message, raw)
    old = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: (
        ChatMemberMember(user=tg_user(MEMBER).model_copy(update={"username": "changed"}))
        if m.user_id == MEMBER
        else old(m)
    )
    with pytest.raises(perms.TargetError):
        await perms.resolve_target(env, group_msg("/ban @u20 spam", ADMIN).message, "@u20 spam")
    api.responses["GetChatMember"] = old
    await send(env, group_msg("/ban 20 spam 2026", ADMIN))
    assert api.calls("BanChatMember")[-1].until_date is None
    await send(env, group_msg("/ban 10 spam", ADMIN))
    assert len(api.calls("BanChatMember")) == 1
    await send(env, group_msg("/warn " + "x" * 257, ADMIN, reply_to=plain(MEMBER)))
    assert await env.extras["guard"].count_warns(GROUP, MEMBER) == 0


@pytest.mark.parametrize(
    "command",
    [
        "/tban",
        "/tmute spam",
        "/ban 0s",
        "/mute -1h",
        "/sban 59s",
        "/ban 366d",
        "/ban 123456789123456789h",
        "/ban 12x",
        "/ban 1.5h",
    ],
)
async def test_invalid_duration_zero_mutations(env, api, command):
    await send(env, group_msg(command, ADMIN, reply_to=plain(MEMBER)))
    assert not domain_calls(api) and await env.extras["guard"].count_warns(GROUP, MEMBER) == 0


async def test_valid_duration_units_deadline_and_general_timer(env, api):
    for token in ["60s", "1m", "2h", "3d", "2w", "365d"]:
        assert perms.parse_action_duration(token).kind == "valid"
    assert perms.parse_duration("10s") == timedelta(seconds=10)
    assert perms.split_action_args("spam first reason")[0].kind == "absent"
    await send(env, group_msg("/tban 1m precise", ADMIN, reply_to=plain(MEMBER)))
    deadline = api.calls("BanChatMember")[-1].until_date
    if hasattr(deadline, "timestamp"):
        deadline = deadline.timestamp()
    assert 59 <= deadline - time.time() <= 61
    for deadline in [0, int(time.time()) - 1, int(time.time()) + 30, int(time.time()) + 366 * 86400]:
        result = await actions.punish(env, GROUP, MEMBER, "mute", None, absolute=deadline)
        assert not result.primary_completed
    assert not api.calls("RestrictChatMember")


async def test_warning_failure_retains_history_completed_failed_log_resets(env, api):
    svc = env.extras["guard"]
    cfg = await svc.update_config(GROUP, warn_limit=1)
    api.responses["BanChatMember"] = bad(BanChatMember(chat_id=GROUP, user_id=MEMBER))
    result = await apply_warn(env, svc, cfg, plain(MEMBER).chat, MEMBER, "Member", "first", ADMIN)
    assert not result.primary_completed and await svc.count_warns(GROUP, MEMBER) == 1
    assert not any("limit reached" in (m.text or "").lower() for m in api.calls("SendMessage"))
    api.responses.pop("BanChatMember")
    cfg = await svc.update_config(GROUP, log_chat_id=-100999)
    api.responses["SendMessage"] = lambda m: bad(m) if m.chat_id == -100999 else True
    result = await apply_warn(env, svc, cfg, plain(MEMBER).chat, MEMBER, "Member", "second", ADMIN)
    assert (
        result.primary_completed and result.status == "partial" and await svc.count_warns(GROUP, MEMBER) == 0
    )
    assert any(s.operation == "log" and s.status == "failed" for s in result.steps)


async def test_kick_unmute_night_unknown_retry_and_bulk_truth(env, api):
    api.responses["UnbanChatMember"] = bad(UnbanChatMember(chat_id=GROUP, user_id=MEMBER))
    result = await actions.punish(env, GROUP, MEMBER, "kick", None)
    assert result.status == "partial" and not result.primary_completed
    with pytest.raises(TypeError):
        bool(result)
    before = len(api.calls("BanChatMember"))
    assert not (await actions.punish(env, GROUP, MEMBER, "not-an-action", None)).primary_completed
    assert len(api.calls("BanChatMember")) == before
    api.responses["GetChat"] = bad(GetChat(chat_id=GROUP))
    assert not (await actions.unmute(env, GROUP, MEMBER)).primary_completed
    assert not api.calls("RestrictChatMember")
    cfg = await env.extras["guard"].update_config(
        GROUP,
        night=True,
        night_start=0,
        night_end=23,
        tz_offset=-time.gmtime().tm_hour if time.gmtime().tm_hour <= 12 else 24 - time.gmtime().tm_hour,
    )
    assert not (await apply_night(env, GROUP, cfg)).primary_completed
    assert not api.calls("SetChatPermissions")
    api.responses["DeleteMessages"] = lambda m: bad(m) if m.message_ids[0] == 101 else True
    bulk = await actions.delete_many(env, GROUP, list(range(1, 206)))
    assert (
        bulk.status == "partial"
        and len(bulk.requested_message_ids) == 205
        and len(bulk.acknowledged_message_ids) == 105
    )
    assert bulk.confirmed_deleted_count is None
    api.responses["BanChatMember"] = TelegramRetryAfter(
        method=BanChatMember(chat_id=GROUP, user_id=MEMBER), message="retry", retry_after=7
    )
    retry = await actions.punish(env, GROUP, MEMBER, "ban", None)
    assert retry.steps[0].retry_after == 7 and retry.steps[0].error_code == "retry_after"


async def test_silent_failed_ancillary_private_audit(env, api):
    api.responses["DeleteMessages"] = lambda m: bad(m)
    api.responses["DeleteMessage"] = lambda m: bad(m)
    msg = group_msg("/sban spam", ADMIN, reply_to=plain(MEMBER)).message
    op = operation_for(
        msg,
        "ban",
        target_id=MEMBER,
        target_name="Member",
        silent=True,
        reason="spam",
        reply_id=msg.reply_to_message.message_id,
    )
    result = await execute(env, authz.actor_from_message(env, msg), op)
    assert result.primary_completed and result.status == "partial" and api.calls("BanChatMember")
    assert not api.calls("SendMessage")
    audit = (await env.audit.recent())[0]
    assert audit.details["outcome"] == "partial" and audit.details["operation"]["target_id"] == MEMBER


async def test_factory_scope_review_panel_and_target_cache(env, api):
    if env.child is None:
        return
    others = [c for c in env.extras["test_contexts"] if c.bot_id != env.bot_id]
    msg, data, nonce = await make_review(env, api)
    for other in others:
        assert await other.redis.get(reviews.review_key(other, nonce)) is None
        await send(other, bound_callback(data, msg, ADMIN))
        assert not api.calls("BanChatMember")
    await send(env, group_msg("/settings", ADMIN))
    panel = next(m for m in reversed(api.messages) if m.chat.id == ADMIN)
    for other in others:
        assert not await authz.bound_message(
            other, bound_callback("x", panel, ADMIN).callback_query, target_chat_id=GROUP, kind="settings"
        )
    await perms.remember(env, tg_user(MEMBER).model_copy(update={"username": "isolated"}))
    for other in others:
        assert await other.redis.get(other.keys("uname", "isolated")) is None
        with pytest.raises(perms.TargetError):
            await perms.resolve_target(
                other, group_msg("/ban @isolated spam", ADMIN).message, "@isolated spam"
            )
    await send(env, bound_callback(data, msg, ADMIN))
    assert len(api.calls("BanChatMember")) == 1


@pytest.mark.parametrize("flow", ["cas", "ai", "flood-union"])
async def test_automated_failure_never_announces_false_success(env, api, monkeypatch, flow):
    from bots.groupguard import protect
    from bots.groupguard.handlers import welcome
    from tests.bots.groupguard.test_groupguard import join_update

    svc = env.extras["guard"]
    api.responses["BanChatMember"] = bad(BanChatMember(chat_id=GROUP, user_id=30))
    if flow == "cas":

        async def banned(*args):
            return True

        monkeypatch.setattr(welcome, "cas_banned", banned)
        await send(env, join_update(30))
        assert api.calls("BanChatMember")
        assert not any(
            "CAS" in (m.text or "") or "spam-banned" in (m.text or "") for m in api.calls("SendMessage")
        )
    elif flow == "ai":
        cfg = await svc.update_config(GROUP, ai_spam=True, newbie_hours=0)
        await protect.mark_newbie(env, cfg, GROUP, MEMBER)

        async def spam(*args):
            return True

        monkeypatch.setattr(protect, "is_spam", spam)
        await send(env, group_msg("a spam promotion", MEMBER))
        assert api.calls("BanChatMember") and api.calls("DeleteMessage")
        assert not any("banned for spam" in (m.text or "").lower() for m in api.calls("SendMessage"))
    else:
        original = api.responses["GetChatMember"]
        api.responses["GetChatMember"] = lambda m: (
            admin_member(env.bot_id, can_delete_messages=True) if m.user_id == env.bot_id else original(m)
        )
        await svc.update_config(GROUP, flood_count=1)
        await send(env, group_msg("first", MEMBER))
        await send(env, group_msg("second", MEMBER))
        assert not domain_calls(api)


async def test_captcha_callback_binding_and_failed_restore(env, api, monkeypatch):
    from bots.groupguard.handlers import welcome
    from tests.bots.groupguard.test_groupguard import join_update

    async def not_banned(*args):
        return False

    monkeypatch.setattr(welcome, "cas_banned", not_banned)
    await send(env, join_update(30))
    prompt = api.messages[-1]
    call = api.calls("SendMessage")[-1]
    data = call.reply_markup.inline_keyboard[0][0].callback_data
    before = len(api.calls("RestrictChatMember"))
    await send(env, bound_callback(data, prompt.model_copy(update={"message_id": prompt.message_id + 1}), 30))
    assert len(api.calls("RestrictChatMember")) == before
    api.responses["GetChat"] = bad(GetChat(chat_id=GROUP))
    await send(env, bound_callback(data, prompt, 30))
    assert len(api.calls("RestrictChatMember")) == before
    assert not any("captcha-passed" in (getattr(m, "text", "") or "") for m in api.calls("EditMessageText"))
    assert "verified" not in api.calls("AnswerCallbackQuery")[-1].text.lower()


async def test_night_snapshot_precedes_close_actual_restore_sql_denial(env, api, monkeypatch):
    from bots.groupguard.jobs import in_night

    svc = env.extras["guard"]
    hour = time.gmtime().tm_hour
    cfg = await svc.update_config(
        GROUP, night=True, night_start=0, night_end=23, tz_offset=-hour if hour <= 12 else 24 - hour
    )
    assert in_night(cfg, hour)
    from sqlalchemy.exc import SQLAlchemyError

    from bots.groupguard import jobs
    from bots.groupguard.models import GuardNight

    observed = []
    base_get = api.responses["GetChat"]

    def actual_permissions(method):
        info = base_get(method)
        return (
            info.model_copy(update={"permissions": api.calls("SetChatPermissions")[-1].permissions})
            if api.calls("SetChatPermissions")
            else info
        )

    api.responses["GetChat"] = actual_permissions
    # A real API double checks stored state at dispatch, before Telegram receives the close.
    original_perform = actions.perform

    async def observe(operation, call, **kw):
        if operation == "night_close":
            async with env.sm() as session:
                state = await session.get(GuardNight, (env.bot_id, GROUP))
                assert state.status == "dispatched"
                observed.append(state.snapshot)
        return await original_perform(operation, call, **kw)

    monkeypatch.setattr(actions, "perform", observe)
    result = await apply_night(env, GROUP, cfg)
    assert result.primary_completed and observed[0]
    snapshot = observed[0]
    assert snapshot["can_send_messages"] and snapshot["can_send_polls"] is False
    cfg = await svc.update_config(GROUP, night=False)
    result = await apply_night(env, GROUP, cfg)
    async with env.sm() as session:
        state = await session.get(GuardNight, (env.bot_id, GROUP))
    assert result.primary_completed and state.status == "restored"
    permissions = api.calls("SetChatPermissions")[-1].permissions
    assert permissions.can_send_messages and permissions.can_send_polls is False
    cfg = await svc.update_config(GROUP, night=True)
    count = len(api.calls("SetChatPermissions"))

    async def fail(*a, **kw):
        raise SQLAlchemyError("snapshot unavailable")

    monkeypatch.setattr(jobs, "persist_night", fail)
    assert not (await apply_night(env, GROUP, cfg)).primary_completed
    assert len(api.calls("SetChatPermissions")) == count


async def test_known_review_owner_wrong_chat_and_binding(env, api):
    original = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: (
        admin_member(11, can_restrict_members=True) if m.user_id == 11 else original(m)
    )
    message = group_msg("/ban spam", ADMIN, reply_to=plain(MEMBER)).message
    op = operation_for(message, "ban", target_id=MEMBER, target_name="Member", reason="spam")
    nonce = await reviews.create_review(env, authz.actor_from_message(env, message), op)
    assert nonce
    msg = api.messages[-1]
    key = reviews.review_key(env, nonce)
    wrong = bound_callback("unused", msg, 11).callback_query.as_(env.bot)
    assert await reviews.approve_review(env, wrong, nonce, callback_chat=GROUP) is None
    wrong = bound_callback(
        "unused", msg.model_copy(update={"chat": Chat(id=-10099, type="supergroup")}), ADMIN
    ).callback_query.as_(env.bot)
    assert await reviews.approve_review(env, wrong, nonce, callback_chat=GROUP) is None
    assert await env.redis.exists(key) and not api.calls("BanChatMember")
    right = bound_callback("unused", msg, ADMIN).callback_query.as_(env.bot)
    assert (await reviews.approve_review(env, right, nonce, callback_chat=GROUP)).primary_completed
    assert len(api.calls("BanChatMember")) == 1
    assert (await env.audit.recent())[0].details["original_actor"] == "human"


async def test_panel_and_review_notice_failure_is_ancillary(env, api):
    from aiogram.methods import EditMessageText

    await send(env, group_msg("/settings", ADMIN))
    panel = next(m for m in reversed(api.messages) if m.chat.id == ADMIN)
    api.responses["EditMessageText"] = bad(
        EditMessageText(text="x", chat_id=ADMIN, message_id=panel.message_id)
    )
    await send(env, bound_callback(f"gg:set:{GROUP}:0:cap", panel, ADMIN))
    assert (await env.extras["guard"].config(GROUP, fresh=True)).captcha == "math"
    audit = (await env.audit.recent())[0]
    assert (
        audit.action == "gg_panel_config"
        and audit.details["outcome"] == "partial"
        and audit.details["primary_completed"]
    )
    msg, data, nonce = await make_review(env, api)
    query = bound_callback(data, msg, ADMIN).callback_query.as_(env.bot)
    result = await reviews.approve_review(env, query, nonce, callback_chat=GROUP)
    assert result.primary_completed and result.status == "partial"
    assert any(s.operation == "review_notice" and s.status == "failed" for s in result.steps)
    assert not await env.redis.exists(reviews.review_key(env, nonce))


async def test_target_promoted_after_review_denies_without_consuming(env, api):
    msg, data, nonce = await make_review(env, api)
    current = api.responses["GetChatMember"]
    before = len(api.calls("GetChatMember"))
    api.responses["GetChatMember"] = lambda m: (
        admin_member(MEMBER, can_change_info=True) if m.user_id == MEMBER else current(m)
    )
    query = bound_callback(data, msg, ADMIN).callback_query.as_(env.bot)
    assert await reviews.approve_review(env, query, nonce, callback_chat=GROUP) is None
    assert any(m.user_id == MEMBER for m in api.calls("GetChatMember")[before:])
    assert not api.calls("BanChatMember")
    assert await env.redis.exists(reviews.review_key(env, nonce))
