"""Phase2 commands through standalone and two actual child dispatchers."""
from datetime import timedelta

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendMessage
from aiogram.types import (
    Chat,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberOwner,
    MessageOriginChannel,
    Update,
)
from sqlalchemy import update

from bots.groupguard import durable
from bots.groupguard.models import GuardJob, GuardWarn
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
from tests.bots.groupguard.test_phase01a import admin_member, env, send

__all__ = ["env", "gctx"]
VARIANTS = ("ban", "tban", "dban", "sban", "mute", "tmute", "dmute", "smute", "kick", "dkick", "skick", "warn", "dwarn", "swarn")


@pytest.mark.parametrize("command", VARIANTS)
async def test_variants_succeed_with_documented_deletions(env, api, command):
    await env.extras["guard"].update_config(GROUP, warn_limit=20)
    arg = "2m reason" if command in {"tban", "tmute"} else "reason"
    request = group_msg(f"/{command} {arg}", ADMIN, reply_to=plain(MEMBER))
    before = len(api.calls("SendMessage"))
    await send(env, request)
    if "warn" in command:
        assert await env.extras["guard"].count_warns(GROUP, MEMBER) == 1
    elif "mute" in command:
        assert api.calls("RestrictChatMember")[-1].user_id == MEMBER
    else:
        assert api.calls("BanChatMember")[-1].user_id == MEMBER
        if "kick" in command:
            assert api.calls("UnbanChatMember")[-1].only_if_banned
    deleted = {call.message_id for call in api.calls("DeleteMessage")}
    if command.startswith(("d", "s")):
        assert request.message.reply_to_message.message_id in deleted
    if command.startswith("s"):
        assert request.message.message_id in deleted and len(api.calls("SendMessage")) == before
    else:
        assert len(api.calls("SendMessage")) > before


@pytest.mark.parametrize("command", VARIANTS)
async def test_variants_deny_unprivileged_sender(env, api, command):
    await send(env, group_msg(f"/{command} 2m reason", MEMBER, reply_to=plain(30)))
    assert not api.calls("BanChatMember") and not api.calls("RestrictChatMember") and not api.calls("DeleteMessage")
    assert await env.extras["guard"].count_warns(GROUP, 30) == 0


@pytest.mark.parametrize("command", VARIANTS)
async def test_variants_report_api_failure_truthfully(env, api, command):
    method = "DeleteMessage" if command == "swarn" else "SendMessage" if "warn" in command else "RestrictChatMember" if "mute" in command else "BanChatMember"
    api.responses[method] = TelegramBadRequest(method=SendMessage(chat_id=GROUP, text="test"), message="controlled failure")
    await send(env, group_msg(f"/{command} 2m reason", ADMIN, reply_to=plain(MEMBER)))
    if "warn" in command:
        assert await env.extras["guard"].count_warns(GROUP, MEMBER) == 1
        assert (await env.audit.recent(1))[0].details["outcome"] == "partial"
    else:
        assert not api.calls("UnbanChatMember")
        assert all("was banned" not in (m.text or "") and "was muted" not in (m.text or "") and "was kicked" not in (m.text or "") for m in api.calls("SendMessage"))


async def test_delete_union_and_invalid_temporary_inputs_never_mutate(env, api):
    old = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: admin_member(ADMIN, can_restrict_members=True) if m.user_id == ADMIN else old(m)
    for command in ("dban", "dmute", "dkick", "dwarn", "sban", "smute", "skick", "swarn"):
        await send(env, group_msg(f"/{command} reason", ADMIN, reply_to=plain(MEMBER)))
    assert not api.calls("BanChatMember") and not api.calls("RestrictChatMember") and not api.calls("DeleteMessage")
    assert await env.extras["guard"].count_warns(GROUP, MEMBER) == 0
    api.responses["GetChatMember"] = old
    for text in ("/tban", "/tmute 20s", "/tban 999999999999d", "/dban 20"):
        await send(env, group_msg(text, ADMIN))
    assert not api.calls("BanChatMember") and not api.calls("RestrictChatMember")


async def test_kickme_is_self_only_and_creator_protected(env, api):
    for text, uid in (("/kickme 30", MEMBER), ("/kickme", ADMIN)):
        await send(env, group_msg(text, uid))
    assert not api.calls("BanChatMember")
    await send(env, group_msg("/kickme", MEMBER))
    assert api.calls("BanChatMember")[-1].user_id == MEMBER and api.calls("UnbanChatMember")[-1].user_id == MEMBER
    before = len(api.calls("UnbanChatMember"))
    api.responses["BanChatMember"] = False
    await send(env, group_msg("/kickme", MEMBER))
    assert len(api.calls("UnbanChatMember")) == before
    assert (await env.audit.recent(1))[0].details["primary_completed"] is False


async def test_warning_controls_expiry_and_legacy_spellings(env, api):
    await send(env, group_msg("/setwarnlimit 20", ADMIN))
    await send(env, group_msg("/setwarnmode tmute 2m", ADMIN))
    await send(env, group_msg("/warntime 1m", ADMIN))
    cfg = await env.extras["guard"].config(GROUP)
    assert cfg.warn_action == "mute" and cfg.warn_duration_seconds == 120 and cfg.warn_time_seconds == 60
    await send(env, group_msg("/warn first", ADMIN, reply_to=plain(MEMBER)))
    warn = (await env.extras["guard"].list_warns(GROUP, MEMBER))[0]
    assert warn.expires_at > utcnow()
    async with env.sm() as session:
        await session.execute(update(GuardWarn).where(GuardWarn.id == warn.id).values(expires_at=utcnow() - timedelta(seconds=1)))
        await session.execute(update(GuardJob).where(GuardJob.bot_id == env.bot_id, GuardJob.kind == "warning_expire").values(run_at=utcnow()))
        await session.commit()
    assert await durable.sweep(env) == 1
    assert await durable.sweep(env) == 0 and await env.extras["guard"].count_warns(GROUP, MEMBER) == 0
    await send(env, group_msg("/warn cancel age", ADMIN, reply_to=plain(MEMBER)))
    await send(env, group_msg("/setwarntime off", ADMIN))
    assert (await env.extras["guard"].list_warns(GROUP, MEMBER))[0].expires_at is None
    await send(env, group_msg("/resetwarn", ADMIN, reply_to=plain(MEMBER)))
    for text in ("/warn one", "/warn two", "/rmwarn", "/resetwarn"):
        await send(env, group_msg(text, ADMIN, reply_to=plain(MEMBER)))
    assert await env.extras["guard"].count_warns(GROUP, MEMBER) == 0
    await send(env, group_msg("/warnings", MEMBER))
    assert "20" in api.calls("SendMessage")[-1].text and "mute" in api.calls("SendMessage")[-1].text


async def test_approvals_exempt_automation_not_manual_and_creator_clear(env, api):
    await send(env, group_msg("/approve trusted", ADMIN, reply_to=plain(MEMBER)))
    assert (await env.extras["guard"].approval(GROUP, MEMBER)).reason == "trusted"
    await env.extras["guard"].update_config(GROUP, locks=["links"])
    await send(env, group_msg("https://example.com", MEMBER))
    assert not api.calls("DeleteMessage")
    await send(env, group_msg("/ban reason", ADMIN, reply_to=plain(MEMBER)))
    assert api.calls("BanChatMember")[-1].user_id == MEMBER
    old = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: admin_member(ADMIN, can_change_info=True) if m.user_id == ADMIN else old(m)
    await send(env, group_msg("/unapproveall", ADMIN))
    assert await env.extras["guard"].approval(GROUP, MEMBER) is not None
    api.responses["GetChatMember"] = old
    await send(env, group_msg("/unapproveall", ADMIN))
    assert await env.extras["guard"].approval(GROUP, MEMBER) is None


async def test_promotion_intersection_demotion_editability_and_privacy(env, api):
    old = api.responses["GetChatMember"]
    def members(m):
        if m.user_id == env.bot_id:
            return admin_member(m.user_id, can_promote_members=True, can_delete_messages=True, can_restrict_members=True)
        if m.user_id == ADMIN:
            return admin_member(ADMIN, can_promote_members=True, can_delete_messages=True, can_pin_messages=True)
        return old(m)
    api.responses["GetChatMember"] = members
    await send(env, group_msg("/promote", ADMIN, reply_to=plain(MEMBER)))
    promoted = api.calls("PromoteChatMember")[-1]
    assert promoted.can_delete_messages and not promoted.can_restrict_members and not promoted.can_pin_messages
    assert not promoted.can_promote_members and not promoted.is_anonymous
    before = len(api.calls("PromoteChatMember"))
    api.responses["GetChatMember"] = lambda m: admin_member(MEMBER) if m.user_id == MEMBER else members(m)
    await send(env, group_msg("/demote", ADMIN, reply_to=plain(MEMBER)))
    assert len(api.calls("PromoteChatMember")) == before
    api.responses["GetChatMember"] = lambda m: admin_member(MEMBER).model_copy(update={"can_be_edited": True}) if m.user_id == MEMBER else members(m)
    await send(env, group_msg("/demote", ADMIN, reply_to=plain(MEMBER)))
    assert all(getattr(api.calls("PromoteChatMember")[-1], k) is False for k in type(promoted).model_fields if k.startswith("can_"))
    api.responses["GetChatAdministrators"] = [ChatMemberOwner(user=tg_user(ADMIN), is_anonymous=False),
        admin_member(555).model_copy(update={"is_anonymous": True})]
    await send(env, group_msg("/adminlist", MEMBER))
    assert "555" not in api.calls("SendMessage")[-1].text and "id=10" in api.calls("SendMessage")[-1].text


async def test_silent_warning_threshold_logs_without_confirmation(env, api):
    await env.extras["guard"].update_config(GROUP, warn_limit=1, log_chat_id=-10077)
    await send(env, group_msg("/swarn final", ADMIN, reply_to=plain(MEMBER)))
    assert api.calls("BanChatMember")[-1].user_id == MEMBER
    assert not any(m.chat_id == GROUP for m in api.calls("SendMessage"))
    assert any(m.chat_id == -10077 for m in api.calls("SendMessage"))


async def test_actor_bound_ranges_permapin_and_unpinall(env, api):
    await send(env, group_msg("/purgefrom", ADMIN, reply_to=plain(MEMBER).model_copy(update={"message_id": 100})))
    await send(env, group_msg("/purgeto", MEMBER, reply_to=plain(MEMBER).model_copy(update={"message_id": 102})))
    assert not api.calls("DeleteMessages")
    await send(env, group_msg("/purgeto", ADMIN, reply_to=plain(MEMBER).model_copy(update={"message_id": 102})))
    assert api.calls("DeleteMessages")[-1].message_ids == [100, 101, 102]
    assert "unknown" in api.calls("SendMessage")[-1].text
    await send(env, group_msg("/permapin <b>new</b>", ADMIN))
    assert api.calls("PinChatMessage")[-1].message_id == api.messages[-2].message_id
    await send(env, group_msg("/unpinall", ADMIN))
    assert api.calls("UnpinAllChatMessages")


async def test_verified_channel_log_setup_reports_categories_and_linked_controls(env, api):
    old = api.responses["GetChatMember"]
    def rights(m):
        if m.chat_id == -10077 and m.user_id == env.bot_id:
            return admin_member(env.bot_id, can_post_messages=True, can_change_info=True)
        return old(m)
    api.responses["GetChatMember"] = rights
    channel = plain(ADMIN).model_copy(update={"chat": Chat(id=-10077, type="channel", title="Logs"),
        "text": "/setlog", "entities": group_msg("/setlog", ADMIN).message.entities})
    forwarded = group_msg("/setlog", ADMIN)
    forwarded = forwarded.model_copy(update={"message": forwarded.message.model_copy(update={
        "forward_origin": MessageOriginChannel(date=utcnow(), chat=channel.chat, message_id=channel.message_id)})})
    await send(env, forwarded)
    assert (await env.extras["guard"].config(GROUP)).log_chat_id is None
    await send(env, Update(update_id=99100000 + env.bot_id, channel_post=channel))
    forwarded = group_msg("/setlog", ADMIN).model_copy(update={"message": group_msg("/setlog", ADMIN).message.model_copy(update={
        "forward_origin": MessageOriginChannel(date=utcnow(), chat=channel.chat, message_id=channel.message_id)})})
    await send(env, forwarded)
    assert (await env.extras["guard"].config(GROUP)).log_chat_id == -10077
    await send(env, group_msg("/nolog admin", ADMIN))
    before = len([m for m in api.calls("SendMessage") if m.chat_id == -10077])
    await send(env, group_msg("/ban reason", ADMIN, reply_to=plain(MEMBER)))
    assert len([m for m in api.calls("SendMessage") if m.chat_id == -10077]) == before
    await send(env, group_msg("/reports off", ADMIN))
    before = len(api.calls("SendMessage"))
    await send(env, group_msg("@admin", MEMBER, reply_to=plain(30)))
    assert len(api.calls("SendMessage")) == before
    await send(env, group_msg("/antichannelpin on", ADMIN))
    await send(env, group_msg("/cleanlinked on", ADMIN))
    linked = group_msg("channel post", MEMBER, sender_chat=Chat(id=-10088, type="channel"))
    linked = linked.model_copy(update={"message": linked.message.model_copy(update={"is_automatic_forward": True})})
    await send(env, linked)
    assert api.calls("UnpinChatMessage")[-1].message_id == linked.message.message_id
    assert api.calls("DeleteMessage")[-1].message_id == linked.message.message_id


async def test_assumed_anonymous_mode_off_by_default_and_never_owner_authority(env, api):
    assert not (await env.extras["guard"].config(GROUP)).anonadmin
    await send(env, group_msg("/anonadmin on", ADMIN))
    anonymous = group_msg("/ban reason", 1087968824, reply_to=plain(MEMBER), sender_chat=Chat(id=GROUP, type="supergroup"))
    await send(env, anonymous)
    assert api.calls("BanChatMember")[-1].user_id == MEMBER
    await env.extras["guard"].approve(GROUP, 30, "trusted", ADMIN)
    await send(env, group_msg("/unapproveall", 1087968824, sender_chat=Chat(id=GROUP, type="supergroup")))
    assert await env.extras["guard"].approval(GROUP, 30) is not None
    before = len(api.calls("BanChatMember"))
    await send(env, group_msg("/ban reason", 1087968824, reply_to=plain(30), sender_chat=Chat(id=-10088, type="channel")))
    assert len(api.calls("BanChatMember")) == before
    await send(env, group_msg("/adminerror off", ADMIN))
    before = len(api.calls("SendMessage"))
    await send(env, group_msg("/ban", MEMBER, reply_to=plain(30)))
    assert len(api.calls("SendMessage")) == before


@pytest.mark.parametrize("command,method", [("pin", "PinChatMessage"), ("unpin", "UnpinChatMessage"),
    ("unpinall", "UnpinAllChatMessages"), ("permapin", "PinChatMessage"), ("purge", "DeleteMessages"),
    ("spurge", "DeleteMessages"), ("del", "DeleteMessage")])
async def test_message_tools_denial_failure_and_success(env, api, command, method):
    def request(uid):
        item = group_msg(f"/{command}" + (" content" if command == "permapin" else ""), uid)
        reply = plain(MEMBER).model_copy(update={"message_id": item.message.message_id - 2})
        return item.model_copy(update={"message": item.message.model_copy(update={"reply_to_message": reply})})
    await send(env, request(MEMBER))
    assert not api.calls(method)
    api.responses[method] = False
    await send(env, request(ADMIN))
    assert api.calls(method)
    assert (await env.audit.recent(1))[0].details["primary_completed"] is False
    api.responses[method] = True
    await send(env, request(ADMIN))
    assert (await env.audit.recent(1))[0].details["primary_completed"] is True


async def test_approval_forms_file_inventory_and_private_identity(env, api):
    await send(env, group_msg("/approve 30 reason", MEMBER))
    assert await env.extras["guard"].approval(GROUP, 30) is None
    await send(env, group_msg("/approve 30 reason", ADMIN))
    await send(env, group_msg("/approval 30", MEMBER))
    assert "reason" in api.calls("SendMessage")[-1].text
    await send(env, group_msg("/unapprove 30", ADMIN))
    assert await env.extras["guard"].approval(GROUP, 30) is None
    for uid in range(31, 62):
        await env.extras["guard"].approve(GROUP, uid, "file list", ADMIN)
    await send(env, group_msg("/approved", MEMBER))
    assert api.calls("SendDocument")[-1].document.data.count(b"file list") == 31
    await send(env, group_msg("/info @unknown", MEMBER))
    assert "could not be verified" in api.calls("SendMessage")[-1].text.lower()
    request = group_msg("/id", MEMBER)
    request = request.model_copy(update={"message": request.message.model_copy(update={"chat": Chat(id=MEMBER, type="private")})})
    await send(env, request)
    assert "20" in api.calls("SendMessage")[-1].text
    private_ban = group_msg("/ban 30", ADMIN)
    private_ban = private_ban.model_copy(update={"message": private_ban.message.model_copy(update={"chat": Chat(id=ADMIN, type="private")})})
    await send(env, private_ban)
    assert not api.calls("BanChatMember")


async def test_configuration_commands_deny_wrong_rights_and_validate_values(env, api):
    names = ("setwarnlimit 10", "setwarnmode tban 2m", "setwarntime 1d", "anonadmin on", "adminerror off",
        "reports off", "antichannelpin on", "cleanlinked on", "nolog reports")
    before = (await env.extras["guard"].config(GROUP)).model_dump()
    for name in names:
        await send(env, group_msg("/" + name, MEMBER))
    assert (await env.extras["guard"].config(GROUP)).model_dump() == before
    for name in names:
        await send(env, group_msg("/" + name, ADMIN))
    cfg = await env.extras["guard"].config(GROUP)
    assert cfg.warn_limit == 10 and cfg.warn_duration_seconds == 120 and cfg.warn_time_seconds == 86400
    assert cfg.anonadmin and not cfg.adminerror and not cfg.reports and cfg.antichannelpin and cfg.cleanlinked
    assert "reports" not in cfg.log_categories
    before = cfg.model_dump()
    for name in ("setwarnlimit 0", "setwarnmode tban 20s", "setwarntime broken", "reports maybe", "log private"):
        await send(env, group_msg("/" + name, ADMIN))
    assert (await env.extras["guard"].config(GROUP)).model_dump() == before


async def test_promotion_api_failure_and_revoked_capability(env, api):
    old = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: admin_member(env.bot_id, can_promote_members=True) if m.user_id == env.bot_id else old(m)
    api.responses["PromoteChatMember"] = False
    await send(env, group_msg("/promote", ADMIN, reply_to=plain(MEMBER)))
    assert (await env.audit.recent(1))[0].details["primary_completed"] is False
    api.responses["GetChatMember"] = old
    before = len(api.calls("PromoteChatMember"))
    await send(env, group_msg("/promote", ADMIN, reply_to=plain(MEMBER)))
    assert len(api.calls("PromoteChatMember")) == before


async def test_leave_log_cutoff_and_category_are_effective(env, api):
    await env.extras["guard"].update_config(GROUP, log_chat_id=-10077)
    def leaving(uid):
        event = join_update(uid)
        return event.model_copy(update={"chat_member": event.chat_member.model_copy(update={
            "old_chat_member": ChatMemberMember(user=tg_user(uid)),
            "new_chat_member": ChatMemberLeft(user=tg_user(uid))})})
    api.responses["GetChatMemberCount"] = 49
    await send(env, leaving(30))
    assert "left" in api.calls("SendMessage")[-1].text and api.calls("SendMessage")[-1].chat_id == -10077
    before = len(api.calls("SendMessage"))
    api.responses["GetChatMemberCount"] = 50
    await send(env, leaving(31))
    assert len(api.calls("SendMessage")) == before

    await env.extras["guard"].update_config(GROUP, log_categories=["admin"])
    api.responses["GetChatMemberCount"] = 10
    await send(env, leaving(32))
    assert len(api.calls("SendMessage")) == before


@pytest.mark.parametrize("mode,method", [("ban", "BanChatMember"), ("mute", "RestrictChatMember"),
    ("kick", "BanChatMember"), ("tban 2m", "BanChatMember"), ("tmute 2m", "RestrictChatMember")])
async def test_each_warning_threshold_mode_has_actual_dispatch_and_reset(env, api, mode, method):
    await send(env, group_msg("/setwarnlimit 1", ADMIN))
    await send(env, group_msg("/setwarnmode " + mode, ADMIN))
    await send(env, group_msg("/warn threshold", ADMIN, reply_to=plain(MEMBER)))
    assert api.calls(method)[-1].user_id == MEMBER
    assert await env.extras["guard"].count_warns(GROUP, MEMBER) == 0
    if mode.startswith("t"):
        assert api.calls(method)[-1].until_date > utcnow().timestamp() + 100
    if mode == "kick":
        assert api.calls("UnbanChatMember")[-1].user_id == MEMBER


async def test_admincache_report_aliases_and_log_status_controls(env, api):
    await env.redis.set(env.keys("admins", GROUP), '{"555":{"creator":true,"is_admin":true}}')
    await send(env, group_msg("/admincache", ADMIN))
    assert await env.redis.get(env.keys("admins", GROUP)) is None
    assert "555" not in api.calls("SendMessage")[-1].text
    for name in ("report", "admin", "admins"):
        await send(env, group_msg("/" + name, MEMBER, reply_to=plain(30)))
        assert "id=10" in api.calls("SendMessage")[-1].text
    await env.extras["guard"].update_config(GROUP, log_chat_id=-10077, log_categories=["settings"])
    await send(env, group_msg("/log admin", ADMIN))
    assert "admin" in (await env.extras["guard"].config(GROUP)).log_categories
    await send(env, group_msg("/logchannel", MEMBER))
    assert "-10077" in api.calls("SendMessage")[-1].text
    await send(env, group_msg("/logcategories", MEMBER))
    assert "admin" in api.calls("SendMessage")[-1].text
    await send(env, group_msg("/unsetlog", ADMIN))
    assert (await env.extras["guard"].config(GROUP)).log_chat_id is None
    from aiogram.exceptions import TelegramBadRequest
    api.responses["GetChatAdministrators"] = TelegramBadRequest(method=SendMessage(chat_id=GROUP, text="test"), message="denied")
    await send(env, group_msg("/adminlist", MEMBER))
    assert "could not" in api.calls("SendMessage")[-1].text.lower()
