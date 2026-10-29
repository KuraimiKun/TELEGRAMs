from datetime import timedelta

import pytest
from aiogram.exceptions import TelegramForbiddenError, TelegramNetworkError
from aiogram.types import (
    Chat,
    ChatJoinRequest,
    ChatMemberBanned,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberUpdated,
    Message,
    Update,
    User,
)
from sqlalchemy import func, select, update

from bots.channelmanager import ingress, member_interactions, members, outbox
from bots.channelmanager.content import ContentError, PostSpec, TextBody
from bots.channelmanager.member_specs import MemberSpec, ProfilePolicy, RequiredChat
from bots.channelmanager.models import (
    Event,
    JoinRequest,
    MemberAction,
    MemberBan,
    MemberLead,
    Operation,
)
from core.db.base import utcnow
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR, admin_member
from tests.bots.channelmanager.test_publishing import drain
from tests.conftest import BOT_ID

PERSON = 77
REQUIRED = CHANNEL_ID - 10
GROUP = -99887766
LOG = CHANNEL_ID - 20


def person(user_id=PERSON, **values):
    return User(id=user_id, is_bot=False, **{"first_name": "Person", "language_code": "en", **values})


@pytest.fixture(autouse=True)
def immediate_budgets(monkeypatch):
    async def immediate(*args):
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", immediate)


async def setup_members(chm, api, spec=None):
    state = {}
    def get_chat(method):
        chat = Chat(id=int(method.chat_id), type="supergroup" if int(method.chat_id) == GROUP else "channel", title="Members")
        return chat.model_copy(update={"linked_chat_id": GROUP}) if int(method.chat_id) == CHANNEL_ID else chat
    def get_member(method):
        if method.user_id in {BOT_ID, OPERATOR}:
            return admin_member(method.user_id)
        return state.get((int(method.chat_id), method.user_id), ChatMemberLeft(user=person(method.user_id)))
    def approve(method):
        state[(int(method.chat_id), method.user_id)] = ChatMemberMember(user=person(method.user_id))
        return True
    def ban(method):
        state[(int(method.chat_id), method.user_id)] = ChatMemberBanned(user=person(method.user_id), until_date=method.until_date or 0)
        return True
    def unban(method):
        state[(int(method.chat_id), method.user_id)] = ChatMemberLeft(user=person(method.user_id))
        return True
    api.responses.update(GetChat=get_chat, GetChatMember=get_member, ApproveChatJoinRequest=approve, BanChatMember=ban, UnbanChatMember=unban)
    await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    if spec and spec.log_channel:
        await chm.extras["channelmanager"].connect(spec.log_channel, OPERATOR)
    await chm.extras["members"].save(CHANNEL_ID, OPERATOR, spec or MemberSpec(enabled=True))
    return state


def join_event(*, user_id=PERSON, update_id=12001, date=None, **user_values):
    return Update(update_id=update_id, chat_join_request=ChatJoinRequest(chat=Chat(id=CHANNEL_ID, type="channel", title="Source"),
        from_user=person(user_id, **user_values), user_chat_id=user_id + 1000000, date=date or utcnow() - timedelta(seconds=1)))


def member_event(*, user_id=PERSON, actor=None, update_id=13001, joined=False, date=None, kicked=False):
    user = person(user_id)
    left = ChatMemberBanned(user=user, until_date=0) if kicked else ChatMemberLeft(user=user)
    return Update(update_id=update_id, chat_member=ChatMemberUpdated(chat=Chat(id=CHANNEL_ID, type="channel", title="Source"),
        from_user=person(user_id if actor is None else actor), date=date or utcnow(),
        old_chat_member=left if joined else ChatMemberMember(user=user), new_chat_member=ChatMemberMember(user=user) if joined else left))


async def ingest(chm, dp, event):
    await dp.feed_update(chm.bot, event)
    for _ in range(30):
        if not await ingress.process_one(chm):
            return
    raise AssertionError("inbox did not settle")


async def plan(chm, *, wake=False):
    if wake:
        async with chm.sm() as session:
            await session.execute(update(JoinRequest).values(next_check=utcnow()))
            await session.commit()
    for _ in range(30):
        if not await members.plan_one(chm):
            return
    raise AssertionError("planner did not settle")


async def latest(chm):
    async with chm.sm() as session:
        return await session.scalar(select(JoinRequest).order_by(JoinRequest.generation.desc(), JoinRequest.id))


async def test_immediate_request_attempts_contact_before_approval_and_never_infers_private_lead(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, mode="immediate", welcome=PostSpec(body=TextBody(text="Welcome"))))
    await ingest(chm, dp, join_event())
    await plan(chm)
    await drain(chm)
    row = await latest(chm)
    assert row.status == "approved"
    contact = next(i for i, m in enumerate(api.requests) if type(m).__name__ == "SendMessage" and m.chat_id == PERSON + 1000000)
    approval = next(i for i, m in enumerate(api.requests) if type(m).__name__ == "ApproveChatJoinRequest")
    assert contact < approval
    assert not [m for m in api.calls("SendMessage") if m.chat_id == PERSON]
    async with chm.sm() as session:
        lead = await session.get(MemberLead, (BOT_ID, CHANNEL_ID, PERSON))
        assert lead.private_interacted_at is None and not lead.reachable
        assert (await session.scalar(select(MemberAction).where(MemberAction.kind == "welcome"))).error_code == "no_private_interaction"


async def test_timer_and_manual_release_cannot_bypass_captcha_or_required_chats(chm, dp, api):
    state = await setup_members(chm, api, MemberSpec(enabled=True, mode="timed", delay_seconds=1, captcha=True,
        required=[RequiredChat(chat_id=REQUIRED, url="https://t.me/required")]))
    await ingest(chm, dp, join_event(date=utcnow() - timedelta(seconds=2)))
    await plan(chm)
    await drain(chm)
    assert not api.calls("ApproveChatJoinRequest")
    row = await latest(chm)
    await chm.extras["members"].decide(row.id, OPERATOR, "release")
    await member_interactions.interact(chm, row.id, person(), answer=row.challenge["answer"], generation=row.generation)
    await plan(chm)
    await drain(chm)
    assert not api.calls("ApproveChatJoinRequest")
    state[(REQUIRED, PERSON)] = ChatMemberMember(user=person())
    await member_interactions.interact(chm, row.id, person(), answer=-1, generation=row.generation)
    await plan(chm)
    await drain(chm)
    assert len(api.calls("ApproveChatJoinRequest")) == 1


async def test_duplicate_and_completed_request_never_reset_captcha_or_generation(chm, dp, api, monkeypatch):
    # Keep this immediate-drain test in the contact-priority share. The oldest-first
    # share can legitimately defer approval until the initial contact finishes.
    instant = utcnow()
    if int(instant.timestamp()) % 3 == 2:
        instant += timedelta(seconds=1)
    monkeypatch.setattr(outbox, "utcnow", lambda: instant)
    await setup_members(chm, api, MemberSpec(enabled=True, captcha=True))
    event = join_event()
    await ingest(chm, dp, event)
    row = await latest(chm)
    wrong = (row.challenge["answer"] + 1) % 4
    await member_interactions.interact(chm, row.id, person(), answer=wrong, generation=row.generation)
    await ingest(chm, dp, event)
    await ingest(chm, dp, event.model_copy(update={"update_id": 12002}))
    assert (await latest(chm)).captcha_attempts == 1
    await member_interactions.interact(chm, row.id, person(), answer=row.challenge["answer"], generation=row.generation)
    await chm.extras["members"].decide(row.id, OPERATOR, "release")
    await plan(chm)
    await drain(chm)
    await ingest(chm, dp, event.model_copy(update={"update_id": 12003}))
    assert (await latest(chm)).status == "approved"
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(JoinRequest)) == 1


async def test_owned_signed_continuation_records_only_this_channel_interaction(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True))
    await ingest(chm, dp, join_event())
    row = await latest(chm)
    token = members.start_token(chm, row)
    assert len(token) <= 64
    with pytest.raises(ContentError, match="stale"):
        await member_interactions.interact(chm, row.id, person(78), token=token)
    with pytest.raises(ContentError, match="stale"):
        await member_interactions.interact(chm, row.id, person(), token=token[:-1] + ("a" if token[-1] != "a" else "b"))
    await member_interactions.interact(chm, row.id, person(), token=token)
    async with chm.sm() as session:
        leads = (await session.scalars(select(MemberLead))).all()
        assert len(leads) == 1 and leads[0].private_interacted_at and leads[0].reachable


async def test_policy_change_holds_queue_and_adoption_does_not_restore_attempts(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, captcha=True))
    await ingest(chm, dp, join_event())
    row = await latest(chm)
    await member_interactions.interact(chm, row.id, person(), answer=(row.challenge["answer"] + 1) % 4, generation=row.generation)
    svc = chm.extras["members"]
    cfg = await svc.config(CHANNEL_ID, OPERATOR)
    await svc.save(CHANNEL_ID, OPERATOR, MemberSpec(enabled=True, captcha=True, captcha_attempts=2), cfg.generation)
    assert (await latest(chm)).status == "held"
    await svc.decide(row.id, OPERATOR, "adopt")
    row = await latest(chm)
    assert row.status == "pending" and row.captcha_attempts == 1 and not row.captcha_solved


async def test_contact_window_and_blocked_user_are_bounded(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True))
    await ingest(chm, dp, join_event(date=utcnow() - timedelta(minutes=6)))
    await plan(chm)
    await drain(chm)
    assert not [m for m in api.calls("SendMessage") if m.chat_id == PERSON + 1000000]
    async with chm.sm() as session:
        contact = await session.scalar(select(MemberAction).where(MemberAction.kind == "contact"))
        assert contact.status == "skipped" and contact.error_code == "contact_window_expired"
    api.responses["SendMessage"] = lambda m: TelegramForbiddenError(method=m, message="blocked") if m.chat_id == PERSON + 1000001 else Message(
        message_id=100, date=utcnow(), chat=Chat(id=int(m.chat_id), type="private"))
    await ingest(chm, dp, join_event(user_id=78, update_id=12002))
    await plan(chm)
    await drain(chm)
    await plan(chm, wake=True)
    await drain(chm)
    assert len([m for m in api.calls("SendMessage") if m.chat_id == PERSON + 1000001]) == 1


async def test_bulk_snapshots_observed_queue_and_respects_gates(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, captcha=True))
    await ingest(chm, dp, join_event())
    svc = chm.extras["members"]
    batch = await svc.prepare_bulk(CHANNEL_ID, OPERATOR)
    await ingest(chm, dp, join_event(user_id=78, update_id=12002))
    result = await svc.confirm_bulk(batch.id, OPERATOR)
    assert result.result == {"selected": 1, "released": 1, "skipped": 0}
    assert (await svc.confirm_bulk(batch.id, OPERATOR)).result == result.result
    await plan(chm)
    await drain(chm)
    assert not api.calls("ApproveChatJoinRequest")
    async with chm.sm() as session:
        rows = (await session.scalars(select(JoinRequest).order_by(JoinRequest.user_id))).all()
        assert rows[0].manual_release and not rows[1].manual_release


async def test_unknown_approval_is_not_replayed(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, mode="immediate"))
    api.responses["ApproveChatJoinRequest"] = lambda m: TelegramNetworkError(method=m, message="unknown")
    await ingest(chm, dp, join_event())
    await plan(chm)
    await drain(chm)
    row = await latest(chm)
    assert row.status == "uncertain"
    await plan(chm, wake=True)
    await drain(chm)
    assert len(api.calls("ApproveChatJoinRequest")) == 1


@pytest.mark.parametrize("policy,values,expected", [
    (ProfilePolicy(total_block=True), {}, "total_block"),
    (ProfilePolicy(max_per_ten_seconds=1), {}, "join_rate"),
    (ProfilePolicy(blocked_names=["person"]), {}, "profile_keyword"),
    (ProfilePolicy(scripts=["LATIN"], script_mode="block"), {}, "profile_alphabet"),
    (ProfilePolicy(languages=["ar"], language_mode="allow"), {}, "profile_language"),
    (ProfilePolicy(reject_unknown_language=True), {"language_code": None}, "profile_language_unknown"),
])
def test_profile_filter_outcomes_are_explicit(policy, values, expected):
    assert policy.rejects({"first_name": "Person", "language_code": "en", **values}, 2) == expected


async def test_expiry_for_old_request_cannot_decline_new_rejoin(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, expires_seconds=60))
    await ingest(chm, dp, join_event(date=utcnow() - timedelta(seconds=70)))
    await plan(chm)
    old = await latest(chm)
    await ingest(chm, dp, join_event(update_id=12002))
    await plan(chm)
    await drain(chm)
    current = await latest(chm)
    assert current.generation == 2 and current.status == "pending"
    assert not api.calls("DeclineChatJoinRequest")
    async with chm.sm() as session:
        assert (await session.get(JoinRequest, (BOT_ID, old.id))).status == "superseded"


async def test_captcha_attempt_limit_declines_once(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, captcha=True, captcha_attempts=2))
    await ingest(chm, dp, join_event())
    row = await latest(chm)
    for _ in range(2):
        await member_interactions.interact(chm, row.id, person(), answer=(row.challenge["answer"] + 1) % 4, generation=row.generation)
    with pytest.raises(ContentError, match="captcha_attempts"):
        await member_interactions.interact(chm, row.id, person(), answer=row.challenge["answer"], generation=row.generation)
    await plan(chm)
    await drain(chm)
    assert (await latest(chm)).status == "declined"
    assert len(api.calls("DeclineChatJoinRequest")) == 1 and not api.calls("ApproveChatJoinRequest")


async def test_required_membership_is_rechecked_immediately_before_approval(chm, dp, api):
    state = await setup_members(chm, api, MemberSpec(enabled=True, mode="immediate", required=[RequiredChat(chat_id=REQUIRED, url="https://t.me/required")]))
    state[(REQUIRED, PERSON)] = ChatMemberMember(user=person())
    await ingest(chm, dp, join_event())
    row = await latest(chm)
    await member_interactions.interact(chm, row.id, person(), answer=-1, generation=row.generation)
    await plan(chm)
    state[(REQUIRED, PERSON)] = ChatMemberLeft(user=person())
    await drain(chm)
    assert not api.calls("ApproveChatJoinRequest")
    row = await latest(chm)
    assert row.required_index == 0 and row.status == "pending"


async def test_total_block_rejects_before_contact(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, mode="immediate", profile=ProfilePolicy(total_block=True)))
    await ingest(chm, dp, join_event())
    await plan(chm)
    await drain(chm)
    assert len(api.calls("DeclineChatJoinRequest")) == 1
    assert not [m for m in api.calls("SendMessage") if m.chat_id == PERSON + 1000000]


async def test_private_continuation_after_approval_sends_welcome_once(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, mode="immediate", welcome=PostSpec(body=TextBody(text="Welcome"))))
    await ingest(chm, dp, join_event())
    await plan(chm)
    await drain(chm)
    row = await latest(chm)
    for _ in range(2):
        await member_interactions.interact(chm, row.id, person(), token=members.start_token(chm, row))
        await drain(chm)
    assert [m.text for m in api.calls("SendMessage") if m.chat_id == PERSON] == ["Welcome"]


@pytest.mark.parametrize("actor,kicked,expected", [(None, False, 1), (OPERATOR, False, 0), (BOT_ID, True, 0)])
async def test_only_voluntary_departure_triggers_goodbye_and_ban(chm, dp, api, actor, kicked, expected):
    await setup_members(chm, api, MemberSpec(enabled=True, departure_ban=True, ban_seconds=60,
        goodbye=PostSpec(body=TextBody(text="Goodbye"))))
    await ingest(chm, dp, join_event())
    row = await latest(chm)
    await member_interactions.interact(chm, row.id, person(), token=members.start_token(chm, row))
    await ingest(chm, dp, member_event(actor=actor, kicked=kicked))
    await drain(chm)
    assert len(api.calls("BanChatMember")) == expected
    assert len([m for m in api.calls("SendMessage") if m.chat_id == PERSON and m.text == "Goodbye"]) == expected


async def test_timed_unban_survives_policy_disable_and_never_removes_rejoined_member(chm, dp, api):
    state = await setup_members(chm, api, MemberSpec(enabled=True, departure_ban=True, ban_seconds=60))
    await ingest(chm, dp, member_event())
    await drain(chm)
    svc = chm.extras["members"]
    cfg = await svc.config(CHANNEL_ID, OPERATOR)
    await svc.save(CHANNEL_ID, OPERATOR, MemberSpec(enabled=False), cfg.generation)
    state[(CHANNEL_ID, PERSON)] = ChatMemberMember(user=person())
    async with chm.sm() as session:
        await session.execute(update(Operation).where(Operation.kind == "member_unban").values(run_at=utcnow()))
        await session.commit()
    await drain(chm)
    assert not api.calls("UnbanChatMember")
    async with chm.sm() as session:
        ban = await session.scalar(select(MemberBan))
        assert ban.status == "released"


async def test_timed_unban_releases_only_owned_unchanged_ban(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, departure_ban=True, ban_seconds=60))
    await ingest(chm, dp, member_event())
    await drain(chm)
    async with chm.sm() as session:
        await session.execute(update(Operation).where(Operation.kind == "member_unban").values(run_at=utcnow()))
        await session.commit()
    await drain(chm)
    assert len(api.calls("UnbanChatMember")) == 1
    assert api.calls("UnbanChatMember")[0].only_if_banned is True


async def test_internal_audit_survives_external_log_failure(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, mode="immediate", log_channel=LOG, log_events=["request", "approved"]))
    api.responses["SendMessage"] = lambda m: TelegramForbiddenError(method=m, message="log blocked") if m.chat_id == LOG else Message(
        message_id=100, date=utcnow(), chat=Chat(id=int(m.chat_id), type="private"))
    await ingest(chm, dp, join_event())
    await plan(chm)
    await drain(chm)
    assert (await latest(chm)).status == "approved"
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(Event).where(Event.action == "members.approved")) == 1
        assert (await session.scalar(select(MemberAction).where(MemberAction.kind == "log"))).status == "failed"


async def test_allowlisted_service_cleanup_does_not_remove_ordinary_posts(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, cleanup=["new_chat_title"]))
    chat = Chat(id=CHANNEL_ID, type="channel", title="Source")
    for update_id, message in [(12001, Message(message_id=501, date=utcnow(), chat=chat, new_chat_title="New name")),
        (12002, Message(message_id=502, date=utcnow(), chat=chat, text="Ordinary"))]:
        await ingest(chm, dp, Update(update_id=update_id, channel_post=message))
    await drain(chm)
    assert [m.message_id for m in api.calls("DeleteMessage")] == [501]


async def test_duplicate_callback_receipt_consumes_one_attempt(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, captcha=True))
    await ingest(chm, dp, join_event())
    row = await latest(chm)
    wrong = (row.challenge["answer"] + 1) % 4
    for _ in range(2):
        await member_interactions.interact(chm, row.id, person(), answer=wrong, generation=row.generation, receipt_id="same_callback")
    assert (await latest(chm)).captcha_attempts == 1


async def test_external_reban_is_not_lifted_by_old_cleanup(chm, dp, api):
    state = await setup_members(chm, api, MemberSpec(enabled=True, departure_ban=True, ban_seconds=60))
    await ingest(chm, dp, member_event())
    await drain(chm)
    state[(CHANNEL_ID, PERSON)] = ChatMemberBanned(user=person(), until_date=0)
    async with chm.sm() as session:
        await session.execute(update(Operation).where(Operation.kind == "member_unban").values(run_at=utcnow()))
        await session.commit()
    await drain(chm)
    assert not api.calls("UnbanChatMember")
    async with chm.sm() as session:
        assert (await session.scalar(select(MemberBan))).status == "review"


async def test_linked_group_ban_continues_after_own_channel_enforcement_event(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True, departure_ban=True, ban_seconds=60, linked_group=GROUP))
    await ingest(chm, dp, member_event())
    while True:
        op = await outbox.claim(chm)
        assert op is not None
        await outbox.execute(chm, op)
        if op.kind == "member_ban":
            break
    await ingest(chm, dp, member_event(actor=BOT_ID, kicked=True, update_id=13002))
    await drain(chm)
    assert {m.chat_id for m in api.calls("BanChatMember")} == {CHANNEL_ID, GROUP}


async def test_callback_alone_does_not_claim_permanent_private_reachability(chm, dp, api):
    await setup_members(chm, api, MemberSpec(enabled=True))
    await ingest(chm, dp, join_event())
    row = await latest(chm)
    await member_interactions.interact(chm, row.id, person(), answer=-1, generation=row.generation)
    async with chm.sm() as session:
        lead = await session.get(MemberLead, (BOT_ID, CHANNEL_ID, PERSON))
        assert lead.private_interacted_at and not lead.reachable


async def test_event_log_output_is_excluded_from_source_automation(chm, dp, api):
    from bots.channelmanager.auto_content import RuleSpec
    from bots.channelmanager.automation import plan_one
    await setup_members(chm, api, MemberSpec(enabled=True, log_channel=LOG, log_events=["request"]))
    await chm.extras["automation"].save_rule(LOG, OPERATOR, "Do not loop", RuleSpec(header=TextBody(text="Header")), active=True)
    await ingest(chm, dp, join_event())
    await drain(chm)
    async with chm.sm() as session:
        event_log = await session.scalar(select(MemberAction).where(MemberAction.kind == "log"))
    await ingest(chm, dp, Update(update_id=14001, channel_post=Message(message_id=event_log.remote_id, date=utcnow(),
        chat=Chat(id=LOG, type="channel"), text=event_log.payload["text"])))
    assert not await plan_one(chm)
    assert not api.calls("EditMessageText")
