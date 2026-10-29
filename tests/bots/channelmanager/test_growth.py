"""Phase 6 authorization, disclosure, consent, invitation and sender boundaries."""

from dataclasses import replace
from datetime import timedelta

import pytest
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import ChatInviteLink, ChatMemberLeft, ChatMemberMember, MessageEntity, User
from sqlalchemy import func, select, update

from bots.channelmanager import invitations, member_interactions, outbox
from bots.channelmanager.content import ContentError, PostSpec, TextBody
from bots.channelmanager.growth import lock_token
from bots.channelmanager.growth_specs import DelegateSpec, private_content
from bots.channelmanager.member_specs import MemberSpec
from bots.channelmanager.models import (
    CampaignRecipient,
    Channel,
    Feedback,
    GrowthAction,
    InviteCredit,
    JoinRequest,
    LeadPrivacy,
    MemberInvite,
    MemberLead,
    Operation,
    PostVersion,
    SenderBinding,
)
from bots.channelmanager.permissions import AccessDenied, post_rights, publishing_access
from bots.channelmanager.senders import allowed, token_epoch
from core.db.base import utcnow
from core.db.models import Bot as BotRecord
from core.db.models import ChildBot
from core.sdk.context import ChildInfo
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR, admin_member
from tests.bots.channelmanager.test_members import ingest, join_event, latest, person, plan, setup_members
from tests.bots.channelmanager.test_publishing import drain
from tests.conftest import BOT_ID

DELEGATE = 77


@pytest.fixture(autouse=True)
def immediate(monkeypatch):
    async def reserve(*args):
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", reserve)


def body(text="Hello"):
    return PostSpec(body=TextBody(text=text))


async def setup_growth(chm, api):
    await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    def member(method):
        if method.user_id in {BOT_ID, OPERATOR}:
            return admin_member(method.user_id).model_copy(update={"can_promote_members": True})
        return ChatMemberMember(user=person(method.user_id))
    api.responses["GetChatMember"] = member


async def grant(chm, spec=None):
    return await chm.extras["team"].save(CHANNEL_ID, OPERATOR, DELEGATE, spec or DelegateSpec())


async def lead(chm, user_id=77, *, channel_id=CHANNEL_ID, **values):
    async with chm.sm() as session:
        session.add(MemberLead(bot_id=chm.bot_id, channel_id=channel_id, user_id=user_id,
            **({"private_interacted_at": utcnow(), "reachable": True, "campaign_opt_in": True} | values)))
        await session.commit()


async def test_native_promotion_authority_required_for_delegation(chm, api):
    await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    with pytest.raises(AccessDenied):
        await grant(chm)
    await setup_growth(chm, api)
    row = await grant(chm)
    assert row.active
    with pytest.raises(AccessDenied):
        await chm.extras["team"].save(CHANNEL_ID, DELEGATE, 88, DelegateSpec())


async def test_delegate_own_all_schedule_and_settings_permissions(chm, api):
    await setup_growth(chm, api)
    await grant(chm)
    own = await chm.extras["posts"].create(CHANNEL_ID, DELEGATE, body())
    other = await chm.extras["posts"].create(CHANNEL_ID, OPERATOR, body())
    await post_rights(chm, CHANNEL_ID, DELEGATE, own.creator_id, "edit")
    for action in ["edit", "delete", "view"]:
        with pytest.raises(AccessDenied):
            await post_rights(chm, CHANNEL_ID, DELEGATE, other.creator_id, action)
    for action in ["schedule", "settings"]:
        with pytest.raises(AccessDenied):
            await publishing_access(chm, CHANNEL_ID, DELEGATE, action=action)
    await chm.extras["team"].save(CHANNEL_ID, OPERATOR, DELEGATE, DelegateSpec(edit_all=True, delete_all=True, schedules=True, settings=True), generation=1)
    await chm.extras["posts"].configure(CHANNEL_ID, DELEGATE, timezone="Asia/Jakarta")
    await chm.extras["presets"].set_reactions(CHANNEL_ID, DELEGATE, ["👍", "👎"])
    assert (await post_rights(chm, CHANNEL_ID, DELEGATE, other.creator_id, "delete"))["_virtual"]


@pytest.mark.parametrize("mutation", ["revoke", "revise", "grantor_lost"])
async def test_delegation_change_holds_queued_work_before_send(chm, api, mutation):
    await setup_growth(chm, api)
    await grant(chm)
    post = await chm.extras["posts"].create(CHANNEL_ID, DELEGATE, body("Delegated"))
    await chm.extras["posts"].publish(post.id, DELEGATE, post.generation)
    if mutation == "grantor_lost":
        previous = api.responses["GetChatMember"]
        api.responses["GetChatMember"] = lambda m: ChatMemberLeft(user=person(m.user_id)) if m.user_id == OPERATOR else previous(m)
    else:
        await chm.extras["team"].save(CHANNEL_ID, OPERATOR, DELEGATE, DelegateSpec(), generation=1, active=mutation != "revoke")
    await drain(chm)
    assert not [m for m in api.calls("SendMessage") if m.chat_id == CHANNEL_ID and m.text == "Delegated"]
    async with chm.sm() as session:
        op = await session.scalar(select(Operation).where(Operation.kind == "publish"))
        assert op.status == "cancelled"
    if mutation != "grantor_lost":
        adopted = await chm.extras["team"].adopt(post.id, OPERATOR)
        assert adopted.creator_id == OPERATOR
        view = await chm.extras["posts"].view(post.id, OPERATOR)
        assert view.deliveries[0].state == "held"


async def test_virtual_grant_and_media_never_cross_bot_or_channel(chm, api):
    await setup_growth(chm, api)
    await grant(chm)
    with pytest.raises(AccessDenied):
        await publishing_access(chm, CHANNEL_ID - 1, DELEGATE)
    other = replace(chm, bot_id=222222)
    with pytest.raises(AccessDenied):
        await publishing_access(other, CHANNEL_ID, DELEGATE)
    with pytest.raises(ContentError):
        private_content(PostSpec(kind="photo", body=TextBody(), file_id="foreign", media_bot_id=222222), BOT_ID)


async def test_private_reveal_contains_no_public_secret_and_rechecks_membership(chm, api):
    await setup_growth(chm, api)
    row = await chm.extras["growth"].create_lock(CHANNEL_ID, OPERATOR, body("Teaser"), body("SECRET"))
    async with chm.sm() as session:
        public = await session.get(PostVersion, (BOT_ID, row.post_id, 1))
        assert "SECRET" not in str(public.spec)
        assert "chl_" in str(public.spec)
    action = await chm.extras["growth"].reveal(77, lock_token(chm, row), "receipt")
    assert (await chm.extras["growth"].reveal(77, lock_token(chm, row), "receipt")).id == action.id
    await drain(chm)
    secret = [m for m in api.calls("SendMessage") if m.text == "SECRET"]
    assert len(secret) == 1 and secret[0].chat_id == 77 and secret[0].protect_content
    assert not api.calls("EditMessageText")
    previous = api.responses["GetChatMember"]
    await chm.extras["growth"].reveal(77, lock_token(chm, row), "second")
    api.responses["GetChatMember"] = lambda m: ChatMemberLeft(user=person(77)) if m.user_id == 77 else previous(m)
    await drain(chm)
    assert len([m for m in api.calls("SendMessage") if m.text == "SECRET"]) == 1


async def test_locked_content_ordered_requirements_and_secret_generation(chm, api):
    await setup_growth(chm, api)
    required = [{"chat_id": CHANNEL_ID - i, "url": f"https://t.me/required{i}"} for i in [1, 2]]
    row = await chm.extras["growth"].create_lock(CHANNEL_ID, OPERATOR, body("Teaser"), body("old secret"), required)
    api.requests.clear()
    await chm.extras["growth"].reveal(77, lock_token(chm, row), "a")
    checked = [m.chat_id for m in api.calls("GetChatMember") if m.user_id == 77]
    assert checked == [CHANNEL_ID, CHANNEL_ID - 1, CHANNEL_ID - 2]
    await chm.extras["growth"].edit_lock(row.id, OPERATOR, body("new secret"), 1)
    await drain(chm)
    assert not [m for m in api.calls("SendMessage") if m.text in {"old secret", "new secret"}]
    await chm.extras["growth"].disable_lock(row.id, OPERATOR)
    with pytest.raises(ContentError):
        await chm.extras["growth"].reveal(77, lock_token(chm, row), "b")


async def test_reveal_unknown_remote_result_never_replays(chm, api):
    await setup_growth(chm, api)
    row = await chm.extras["growth"].create_lock(CHANNEL_ID, OPERATOR, body("Teaser"), body("secret"))
    action = await chm.extras["growth"].reveal(77, lock_token(chm, row), "a")
    api.responses["SendMessage"] = lambda m: TelegramNetworkError(method=m, message="lost")
    await drain(chm)
    async with chm.sm() as session:
        assert (await session.get(GrowthAction, (BOT_ID, action.id))).status == "uncertain"
    api.responses.pop("SendMessage")
    await drain(chm)
    assert not [m for m in api.calls("SendMessage") if m.text == "secret" and m.chat_id != 77]


async def test_campaign_snapshot_uses_explicit_optin_exact_channel_and_private_proof(chm, api):
    await setup_growth(chm, api)
    await lead(chm, 77)
    await lead(chm, 78, campaign_opt_in=False)
    await lead(chm, 79, private_interacted_at=None)
    await lead(chm, 80, opted_out=True)
    async with chm.sm() as session:
        session.add(Channel(bot_id=BOT_ID, channel_id=CHANNEL_ID - 1, title="Other"))
        await session.commit()
    await lead(chm, 81, channel_id=CHANNEL_ID - 1)
    campaign = await chm.extras["growth"].snapshot(CHANNEL_ID, OPERATOR, body("Campaign"))
    assert campaign.total == 1
    await lead(chm, 82)
    await chm.extras["growth"].confirm(campaign.id, OPERATOR, 1)
    await chm.extras["growth"].confirm(campaign.id, OPERATOR, 1)
    await drain(chm)
    assert [m.chat_id for m in api.calls("SendMessage") if m.text == "Campaign"] == [77]


async def test_optout_after_snapshot_skips_send_and_forget_scrubs_scoped_data(chm, api):
    await setup_growth(chm, api)
    await lead(chm)
    campaign = await chm.extras["growth"].snapshot(CHANNEL_ID, OPERATOR, body("Campaign"))
    await chm.extras["growth"].confirm(campaign.id, OPERATOR, 1)
    await chm.extras["growth"].consent(CHANNEL_ID, 77, subscribe=False)
    await drain(chm)
    assert not [m for m in api.calls("SendMessage") if m.text == "Campaign"]
    await chm.extras["growth"].forget(CHANNEL_ID, 77)
    async with chm.sm() as session:
        assert await session.get(MemberLead, (BOT_ID, CHANNEL_ID, 77)) is None
        assert await session.scalar(select(func.count()).select_from(CampaignRecipient)) == 0
        assert await session.scalar(select(func.count()).select_from(LeadPrivacy)) == 1


async def test_campaign_resume_excludes_sent_and_uncertain_recipients(chm, api):
    await setup_growth(chm, api)
    for user in [77, 78, 79]:
        await lead(chm, user)
    campaign = await chm.extras["growth"].snapshot(CHANNEL_ID, OPERATOR, body("Campaign"))
    await chm.extras["growth"].confirm(campaign.id, OPERATOR, 1)
    previous = api._respond
    async def respond(method):
        if getattr(method, "text", None) == "Campaign" and method.chat_id == 78:
            api.requests.append(method)
            raise TelegramNetworkError(method=method, message="lost")
        return await previous(method)
    api._respond = respond
    await drain(chm)
    row, counts = await chm.extras["growth"].campaign_report(campaign.id, OPERATOR)
    assert counts == {"succeeded": 2, "uncertain": 1}
    row = await chm.extras["growth"].resume_campaign(campaign.id, OPERATOR, row.generation)
    await chm.extras["growth"].confirm(campaign.id, OPERATOR, row.generation)
    await drain(chm)
    assert len([m for m in api.calls("SendMessage") if m.text == "Campaign"]) == 3


async def test_feedback_scope_and_single_reply(chm, api):
    await setup_growth(chm, api)
    await lead(chm)
    await chm.extras["growth"].menu(CHANNEL_ID, OPERATOR, body("Menu"), feedback=True)
    item = await chm.extras["growth"].feedback(CHANNEL_ID, 77, "Question <x>", "receipt")
    assert (await chm.extras["growth"].feedback(CHANNEL_ID, 77, "repeat", "receipt")).id == item.id
    with pytest.raises(AccessDenied):
        await chm.extras["growth"].reply(item.id, 88, "reply")
    await drain(chm)
    await chm.extras["growth"].reply(item.id, OPERATOR, "Answer")
    await chm.extras["growth"].reply(item.id, OPERATOR, "Answer")
    await drain(chm)
    assert len([m for m in api.calls("SendMessage") if m.text == "Answer" and m.chat_id == 77]) == 1
    await chm.extras["growth"].forget(CHANNEL_ID, 77)
    async with chm.sm() as session:
        saved = await session.get(Feedback, (BOT_ID, item.id))
        assert saved.text == "[removed]" and saved.status == "erased"


async def setup_invite(chm, dp, api, *, captcha=False, bypass=False):
    await setup_members(chm, api, MemberSpec(enabled=True, mode="immediate", captcha=captcha,
        invite_threshold=2, invite_timeout_seconds=60, invite_timeout_bypass=bypass))
    api.responses["CreateChatInviteLink"] = ChatInviteLink(invite_link="https://t.me/+own", creator=User(id=BOT_ID, is_bot=True, first_name="Bot"),
        creates_join_request=True, is_primary=False, is_revoked=False)
    await ingest(chm, dp, join_event(user_id=77))
    await plan(chm)
    await drain(chm)
    return await latest(chm)


async def test_invite_credit_distinct_self_stale_and_gate_completion(chm, dp, api):
    request = await setup_invite(chm, dp, api)
    async with chm.sm() as session:
        invite = await session.scalar(select(MemberInvite))
        assert not await invitations._credit(session, chm, CHANNEL_ID, 77, invite.link_hash)
        assert await invitations._credit(session, chm, CHANNEL_ID, 88, invite.link_hash)
        assert not await invitations._credit(session, chm, CHANNEL_ID, 88, invite.link_hash)
        assert not await invitations._credit(session, chm, CHANNEL_ID - 1, 89, invite.link_hash)
        assert await invitations._credit(session, chm, CHANNEL_ID, 89, invite.link_hash)
        await session.commit()
    await plan(chm, wake=True)
    async with chm.sm() as session:
        # Defer the initial temporary-contact operation once so it can follow link creation.
        await session.execute(update(Operation).where(Operation.status == "pending").values(run_at=utcnow()))
        await session.commit()
    await drain(chm)
    # The oldest-first share may defer approval until the pending contact finishes.
    async with chm.sm() as session:
        await session.execute(update(Operation).where(Operation.status == "pending").values(run_at=utcnow()))
        await session.commit()
    await drain(chm)
    async with chm.sm() as session:
        assert (await session.get(JoinRequest, (BOT_ID, request.id))).status == "approved"
        assert await session.scalar(select(func.count()).select_from(InviteCredit)) == 2
    assert await invitations.cleanup_one(chm)
    async with chm.sm() as session:
        invite = await session.scalar(select(MemberInvite))
        assert invite.status == "revoking"


async def test_invite_timeout_only_bypasses_invites_and_consent_stays_separate(chm, dp, api):
    request = await setup_invite(chm, dp, api, captcha=True, bypass=True)
    async with chm.sm() as session:
        row = await session.get(JoinRequest, (BOT_ID, request.id))
        row.requested_at = utcnow() - timedelta(seconds=61)
        await session.commit()
    await plan(chm, wake=True)
    await drain(chm)
    assert not api.calls("ApproveChatJoinRequest")
    await chm.extras["growth"].consent(CHANNEL_ID, 77, subscribe=False)
    await member_interactions.interact(chm, request.id, person(77), answer=request.challenge["answer"], generation=request.generation, receipt_id="answer")
    await plan(chm, wake=True)
    async with chm.sm() as session:
        await session.execute(update(Operation).where(Operation.status == "pending").values(run_at=utcnow()))
        await session.commit()
    await drain(chm)
    async with chm.sm() as session:
        await session.execute(update(Operation).where(Operation.status == "pending").values(run_at=utcnow()))
        await session.commit()
    await drain(chm)
    async with chm.sm() as session:
        saved = await session.get(MemberLead, (BOT_ID, CHANNEL_ID, 77))
        assert saved.opted_out and not saved.campaign_opt_in
    assert api.calls("ApproveChatJoinRequest")


async def test_invite_dynamic_content_preserves_unicode_entities(chm, dp, api):
    from bots.channelmanager.member_delivery import contact_method
    request = await setup_invite(chm, dp, api)
    text = "😀 {invite_count}/{invite_required} {invite_url}"
    spec = MemberSpec(invite_threshold=2, introduction=PostSpec(body=TextBody(text=text,
        entities=[MessageEntity(type="bold", offset=3, length=14)])))
    method = await contact_method(chm, request, spec)
    assert "0/2 https://t.me/+own" in method.text and "{invite_" not in method.text


async def test_sender_epoch_owner_status_and_parent_pause_fence(chm, api):
    await setup_growth(chm, api)
    child_id = 222222
    async with chm.sm() as session:
        session.add(BotRecord(id=child_id, slug="c222222", title="Child", active=True))
        await session.flush()
        child = ChildBot(bot_id=child_id, factory_bot_id=BOT_ID, owner_id=OPERATOR, template="channelmanager", token_enc="encrypted", username="child", title="Child", status="active")
        session.add(child)
        session.add(Channel(bot_id=child_id, channel_id=CHANNEL_ID, title="Child channel", status="active"))
        await session.flush()
        session.add(SenderBinding(bot_id=BOT_ID, channel_id=CHANNEL_ID, sender_bot_id=child_id, owner_id=OPERATOR,
            token_epoch=token_epoch(child), control_username="control"))
        parent = await session.get(Channel, (BOT_ID, CHANNEL_ID))
        parent.sender_paused = True
        await session.commit()
    child_ctx = replace(chm, bot_id=child_id, child=ChildInfo(owner_id=OPERATOR, template="channelmanager", factory_username="factory"))
    async with chm.sm() as session:
        assert not await allowed(chm, CHANNEL_ID, session=session)
        assert await allowed(child_ctx, CHANNEL_ID, session=session)
        child = await session.get(ChildBot, child_id)
        child.token_enc = "rotated"
        await session.commit()
    async with chm.sm() as session:
        assert not await allowed(child_ctx, CHANNEL_ID, session=session)
    await chm.extras["senders"].unbind(CHANNEL_ID, OPERATOR)
    async with chm.sm() as session:
        assert await allowed(chm, CHANNEL_ID, session=session)
        assert not await allowed(child_ctx, CHANNEL_ID, session=session)


async def test_financial_and_invite_cleanup_survive_channel_disconnect(chm, api):
    from bots.channelmanager.growth import enqueue
    await setup_growth(chm, api)
    async with chm.sm() as session:
        channel = await session.get(Channel, (BOT_ID, CHANNEL_ID))
        for kind in ["refund", "revoke_invite", "campaign"]:
            await enqueue(session, chm, channel, kind=kind, actor_id=OPERATOR, key=kind)
        await session.commit()
    channel = await chm.extras["channelmanager"].get(CHANNEL_ID)
    await chm.extras["channelmanager"].disconnect(CHANNEL_ID, OPERATOR, channel.generation)
    async with chm.sm() as session:
        rows = dict((await session.execute(select(Operation.kind, Operation.status).where(Operation.growth_action_id.is_not(None)))).all())
    assert rows == {"growth_refund": "pending", "growth_revoke_invite": "pending", "growth_campaign": "cancelled"}


async def test_bind_then_immediate_unbind_does_not_resume_old_publication(chm, api):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from bots.channelmanager.service import ChannelService
    await setup_growth(chm, api)
    post = await chm.extras["posts"].create(CHANNEL_ID, OPERATOR, body("Old queued work"))
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    async with chm.sm() as session:
        session.add(BotRecord(id=222222, slug="c222222", title="Child", active=True))
        await session.flush()
        session.add(ChildBot(bot_id=222222, factory_bot_id=BOT_ID, owner_id=OPERATOR, template="channelmanager", token_enc="encrypted", username="child", title="Child", status="active"))
        session.add(Channel(bot_id=222222, channel_id=CHANNEL_ID, connected_by=OPERATOR, title="Child", status="active"))
        await session.commit()
    child = replace(chm, bot_id=222222, extras={}, child=ChildInfo(owner_id=OPERATOR, template="channelmanager", factory_username="factory"))
    child.extras["channelmanager"] = ChannelService(child)
    chm.extras["chm_child_registry"] = SimpleNamespace(evict=AsyncMock(), get=AsyncMock(return_value=SimpleNamespace(ctx=child)))
    api.responses["GetChatMember"] = lambda m: admin_member(m.user_id)
    await chm.extras["senders"].bind(CHANNEL_ID, OPERATOR, 222222)
    await chm.extras["senders"].unbind(CHANNEL_ID, OPERATOR)
    await drain(chm)
    assert not [m for m in api.calls("SendMessage") if m.chat_id == CHANNEL_ID and m.text == "Old queued work"]
    async with chm.sm() as session:
        assert (await session.scalar(select(Operation).where(Operation.kind == "publish"))).status == "cancelled"


async def test_factory_sweep_only_active_children_and_round_robin(chm, monkeypatch):
    from types import SimpleNamespace

    from bots.channelmanager import worker
    from bots.channelmanager.senders import factory_sweep
    async with chm.sm() as session:
        for offset in range(9):
            child_id = 222222 + offset
            session.add(BotRecord(id=child_id, slug=f"c{child_id}", title="Child", active=True))
            await session.flush()
            session.add(ChildBot(bot_id=child_id, factory_bot_id=BOT_ID, owner_id=OPERATOR, template="channelmanager", token_enc="encrypted", username="child", title="Child",
                status="active" if offset < 6 else ["paused", "error", "revoked"][offset - 6]))
        await session.commit()
    called = []
    async def tick(ctx):
        called.append(ctx.bot_id)
    async def sweep(ctx):
        return None
    async def get(bot_id):
        return SimpleNamespace(ctx=SimpleNamespace(bot_id=bot_id))
    registry = SimpleNamespace(infra=SimpleNamespace(sm=chm.sm), get=get)
    monkeypatch.setattr(worker, "tick", tick)
    monkeypatch.setattr(worker, "sweep", sweep)
    await factory_sweep(registry)
    assert len(called) == 5
    await factory_sweep(registry)
    assert set(called) == set(range(222222, 222228))


async def test_forget_can_be_followed_by_explicit_subscription_with_fresh_membership(chm, api):
    await setup_growth(chm, api)
    await lead(chm)
    await chm.extras["growth"].forget(CHANNEL_ID, 77)
    await chm.extras["growth"].consent(CHANNEL_ID, 77, subscribe=True)
    async with chm.sm() as session:
        saved = await session.get(MemberLead, (BOT_ID, CHANNEL_ID, 77))
        assert saved.campaign_opt_in and not saved.opted_out


async def test_native_invite_attribution_requires_qualifying_distinct_request(chm, dp, api):
    owner = await setup_invite(chm, dp, api, captcha=True)
    async with chm.sm() as session:
        invite = await session.scalar(select(MemberInvite))
        link = invitations.unseal(chm, invite.link_enc)
    native = ChatInviteLink(invite_link=link, creator=User(id=BOT_ID, is_bot=True, first_name="Bot"),
        creates_join_request=True, is_primary=False, is_revoked=False)
    api.responses["CreateChatInviteLink"] = lambda m: native.model_copy(update={"invite_link": "https://t.me/+" + m.name})
    event = join_event(user_id=88, update_id=12002)
    event = event.model_copy(update={"chat_join_request": event.chat_join_request.model_copy(update={"invite_link": native})})
    await ingest(chm, dp, event)
    await plan(chm)
    async with chm.sm() as session:
        request = await session.scalar(select(JoinRequest).where(JoinRequest.user_id == 88))
        assert (await session.get(JoinRequest, (BOT_ID, owner.id))).invite_count == 0
    await member_interactions.interact(chm, request.id, person(88), answer=request.challenge["answer"], generation=request.generation, receipt_id="referee")
    await member_interactions.interact(chm, request.id, person(88), answer=request.challenge["answer"], generation=request.generation, receipt_id="referee")
    async with chm.sm() as session:
        assert (await session.get(JoinRequest, (BOT_ID, owner.id))).invite_count == 1
        assert not (await session.get(MemberLead, (BOT_ID, CHANNEL_ID, 88))).campaign_opt_in
    foreign = join_event(user_id=89, update_id=12003)
    native = native.model_copy(update={"creator": User(id=999888, is_bot=True, first_name="Other bot")})
    foreign = foreign.model_copy(update={"chat_join_request": foreign.chat_join_request.model_copy(update={"invite_link": native})})
    await ingest(chm, dp, foreign)
    async with chm.sm() as session:
        assert (await session.scalar(select(JoinRequest).where(JoinRequest.user_id == 89))).referral_hash is None


async def test_delegated_global_rights_cannot_exceed_current_grantor_rights(chm, api):
    await setup_growth(chm, api)
    previous = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: previous(m).model_copy(update={"can_edit_messages": False}) if m.user_id == OPERATOR else previous(m)
    with pytest.raises(AccessDenied, match="delegation_ceiling"):
        await grant(chm, DelegateSpec(edit_all=True))
    await grant(chm)
    api.responses["GetChatMember"] = previous
    await chm.extras["team"].save(CHANNEL_ID, OPERATOR, 77, DelegateSpec(delete_all=True), generation=1)
    api.responses["GetChatMember"] = lambda m: previous(m).model_copy(update={"can_delete_messages": False}) if m.user_id == OPERATOR else previous(m)
    with pytest.raises(AccessDenied, match="delegation_ceiling"):
        await publishing_access(chm, CHANNEL_ID, 77)


async def test_sender_binding_requires_live_edit_authority_even_after_menu_preview(chm, api):
    await setup_growth(chm, api)
    previous = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: previous(m).model_copy(update={"can_edit_messages": False}) if m.user_id == OPERATOR else previous(m)
    with pytest.raises(AccessDenied, match="sender_right"):
        await chm.extras["senders"].bind(CHANNEL_ID, OPERATOR, 222222)
    with pytest.raises(AccessDenied, match="sender_right"):
        await chm.extras["senders"].unbind(CHANNEL_ID, OPERATOR)
