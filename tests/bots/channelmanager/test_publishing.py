from datetime import timedelta

import pytest
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
)
from aiogram.methods import PinChatMessage
from aiogram.types import Chat, ChatMemberMember, Message, MessageEntity, User
from sqlalchemy import select, update

from bots.channelmanager import outbox, worker
from bots.channelmanager.content import ContentError, PostSpec, TextBody, parse_buttons, parse_html, utf16len
from bots.channelmanager.models import Delivery, Entitlement, Operation, PostSchedule, PostVersion
from bots.channelmanager.permissions import AccessDenied
from core.db.base import utcnow
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR, admin_member
from tests.conftest import BOT_ID

SECOND = CHANNEL_ID - 1


@pytest.fixture(autouse=True)
def instant_budgets(monkeypatch):
    async def reserve(*args):
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", reserve)


async def setup_post(chm, api, spec=None, *, second=False):
    await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    if second:
        api.responses["GetChat"] = Chat(id=SECOND, type="channel", title="Second")
        await chm.extras["channelmanager"].connect(SECOND, OPERATOR)
    return await chm.extras["posts"].create(CHANNEL_ID, OPERATOR, spec or PostSpec(body=TextBody(text="Hello")))


async def drain(chm):
    for _ in range(30):
        op = await outbox.claim(chm)
        if op is None:
            return
        await outbox.execute(chm, op)
    raise AssertionError("unexpected repeated work")


async def due(chm, kind):
    async with chm.sm() as session:
        await session.execute(update(Operation).where(Operation.kind == kind, Operation.status == "pending").values(run_at=utcnow()))
        await session.commit()


def channel_sends(api, channel=CHANNEL_ID):
    return [m for m in api.calls("SendMessage") if m.chat_id == channel]


async def test_preview_publish_signature_and_utf16_entities_match(chm, api):
    body = TextBody(text="👋 مرحبا", entities=[MessageEntity(type="bold", offset=3, length=5)])
    signature = TextBody(text="توقيع", entities=[MessageEntity(type="italic", offset=0, length=5)])
    spec = PostSpec(body=body, signature=signature, buttons=parse_buttons("Visit - https://example.com"), notifications=False)
    post = await setup_post(chm, api, spec)
    preview = spec.send_method(OPERATOR, preview=True)
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    actual = channel_sends(api)[0]
    assert actual.text == preview.text and actual.entities == preview.entities
    assert actual.parse_mode is None and actual.disable_notification is not False
    assert actual.entities[-1].offset == utf16len(body.text + "\n\n")
    view = await chm.extras["posts"].view(post.id, OPERATOR)
    assert view.state == "sent" and view.deliveries[0].message_id


@pytest.mark.parametrize("kind,method", [("photo", "SendPhoto"), ("video", "SendVideo"), ("animation", "SendAnimation"), ("document", "SendDocument")])
async def test_basic_media_publication(chm, api, kind, method):
    spec = PostSpec(kind=kind, file_id="file_reference", media_bot_id=BOT_ID, body=TextBody(text="وصف"), protected=True)
    post = await setup_post(chm, api, spec)
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    sent = [m for m in api.calls(method) if m.chat_id == CHANNEL_ID]
    assert len(sent) == 1 and sent[0].caption == "وصف" and sent[0].protect_content


@pytest.mark.parametrize("text", ["<b>open", "<a href", "<script>x</script>", "<a href='javascript:x'>x</a>"])
def test_invalid_html_is_rejected_before_transport(text):
    with pytest.raises(ValueError):
        parse_html(text)


def test_html_formatting_and_invalid_surrogate_boundaries():
    body = parse_html("<b>👋 مرحبا</b> &amp; <i>hello</i>")
    assert body.text == "👋 مرحبا & hello" and body.entities[0].length == 8
    with pytest.raises(ValueError):
        TextBody(text="👋", entities=[MessageEntity(type="bold", offset=1, length=1)])
    with pytest.raises(ValueError):
        parse_buttons("Bad - javascript:alert(1)")


async def test_multichannel_partial_failure_retries_only_failed_target(chm, api):
    post = await setup_post(chm, api, second=True)
    svc = chm.extras["posts"]
    post = await svc.targets(post.id, OPERATOR, post.generation, [CHANNEL_ID, SECOND])

    def respond(method):
        if method.chat_id == SECOND:
            return TelegramForbiddenError(method=method, message="no access")
        return Message(message_id=500, date=utcnow(), chat=Chat(id=int(method.chat_id), type="private" if int(method.chat_id) > 0 else "channel"))

    api.responses["SendMessage"] = respond
    post = await svc.publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    assert (await svc.view(post.id, OPERATOR)).state == "partial"
    api.responses.pop("SendMessage")
    await svc.publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    assert len(channel_sends(api)) == 1 and len(channel_sends(api, SECOND)) == 2
    assert (await svc.view(post.id, OPERATOR)).state == "sent"


async def test_uncertain_delivery_cannot_be_blindly_republished(chm, api):
    post = await setup_post(chm, api)
    api.responses["SendMessage"] = lambda method: TelegramNetworkError(method=method, message="unknown") if method.chat_id == CHANNEL_ID else Message(
        message_id=501, date=utcnow(), chat=Chat(id=OPERATOR, type="private"))
    svc = chm.extras["posts"]
    post = await svc.publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    assert (await svc.view(post.id, OPERATOR)).state == "uncertain"
    with pytest.raises(ContentError, match="already_sent"):
        await svc.publish(post.id, OPERATOR, post.generation)
    assert len(channel_sends(api)) == 1


async def test_scheduled_versions_rescheduling_and_cancellation_survive_service_restart(chm, api):
    post = await setup_post(chm, api)
    svc = chm.extras["posts"]
    post = await svc.publish(post.id, OPERATOR, post.generation, run_at=utcnow() + timedelta(hours=1))
    post = await svc.edit(post.id, OPERATOR, post.generation, PostSpec(body=TextBody(text="New version")))
    post = await svc.publish(post.id, OPERATOR, post.generation, run_at=utcnow() + timedelta(hours=2))
    await drain(chm)
    assert not channel_sends(api)
    async with chm.sm() as session:
        versions = (await session.scalars(select(PostVersion).order_by(PostVersion.number))).all()
        assert versions[0].spec["body"]["text"] == "Hello" and versions[1].spec["body"]["text"] == "New version"
        assert (await session.get(PostSchedule, (BOT_ID, post.id))).run_at > utcnow() + timedelta(minutes=110)
    await svc.cancel(post.id, OPERATOR, post.generation)
    await due(chm, "publish")
    await drain(chm)
    assert not channel_sends(api) and (await svc.view(post.id, OPERATOR)).state == "cancelled"


async def test_overdue_schedule_is_held_until_explicit_publish_now(chm, api):
    post = await setup_post(chm, api)
    svc = chm.extras["posts"]
    post = await svc.publish(post.id, OPERATOR, post.generation)
    async with chm.sm() as session:
        await session.execute(update(PostSchedule).values(run_at=utcnow() - timedelta(hours=1)))
        await session.commit()
    await drain(chm)
    assert not channel_sends(api) and (await svc.view(post.id, OPERATOR)).state == "held"
    await svc.publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    assert len(channel_sends(api)) == 1


async def test_published_edit_uses_edit_method_and_immutable_version(chm, api):
    post = await setup_post(chm, api)
    svc = chm.extras["posts"]
    post = await svc.publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    post = await svc.edit(post.id, OPERATOR, post.generation, PostSpec(body=TextBody(text="Edited")))
    await drain(chm)
    assert len(channel_sends(api)) == 1 and api.calls("EditMessageText")[-1].text == "Edited"
    view = await svc.view(post.id, OPERATOR)
    assert view.deliveries[0].version == 2 and view.deliveries[0].edit_status == "succeeded"


async def test_pin_failure_does_not_erase_publication_success(chm, api):
    post = await setup_post(chm, api, PostSpec(body=TextBody(text="Pinned"), pin=True))
    api.responses["PinChatMessage"] = TelegramBadRequest(method=PinChatMessage(chat_id=CHANNEL_ID, message_id=1), message="pin failed")
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    view = await chm.extras["posts"].view(post.id, OPERATOR)
    assert view.state == "sent" and view.deliveries[0].pin_status == "failed" and len(channel_sends(api)) == 1


async def test_deletion_and_detach_are_different_actions(chm, api):
    post = await setup_post(chm, api)
    svc = chm.extras["posts"]
    post = await svc.publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    await svc.cancel(post.id, OPERATOR, post.generation, detach=True)
    await drain(chm)
    assert not api.calls("DeleteMessage") and (await svc.view(post.id, OPERATOR)).state == "detached"
    other = await svc.create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text="Delete me")))
    other = await svc.publish(other.id, OPERATOR, other.generation)
    await drain(chm)
    await svc.delete(other.id, OPERATOR, other.generation)
    await drain(chm)
    assert len(api.calls("DeleteMessage")) == 1 and (await svc.view(other.id, OPERATOR)).state == "deleted"


async def test_auto_deletion_is_timed_from_actual_send_and_survives_actor_revocation(chm, api):
    post = await setup_post(chm, api, PostSpec(body=TextBody(text="Temporary"), delete_after_seconds=60))
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    async with chm.sm() as session:
        target = await session.scalar(select(Delivery))
        op = await session.get(Operation, (BOT_ID, target.delete_op))
        assert op.run_at == target.sent_at + timedelta(seconds=60)
    api.responses["GetChatMember"] = lambda method: admin_member(BOT_ID) if method.user_id == BOT_ID else ChatMemberMember(
        user=User(id=OPERATOR, is_bot=False, first_name="Former admin"))
    await due(chm, "delete")
    await drain(chm)
    assert len(api.calls("DeleteMessage")) == 1


async def test_long_deletion_timer_creates_reminder_not_false_remote_deletion(chm, api):
    post = await setup_post(chm, api, PostSpec(body=TextBody(text="Long timer"), delete_after_seconds=176400))
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    await due(chm, "delete_reminder")
    await drain(chm)
    assert not api.calls("DeleteMessage")
    assert any("Manual deletion reminder" in (m.text or "") for m in api.calls("SendMessage"))
    view = await chm.extras["posts"].view(post.id, OPERATOR)
    assert view.state == "sent" and view.deliveries[0].delete_status == "reminder"


async def test_publication_rechecks_native_permission_at_dispatch(chm, api):
    post = await setup_post(chm, api)
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    api.responses["GetChatMember"] = lambda method: admin_member(BOT_ID) if method.user_id == BOT_ID else ChatMemberMember(
        user=User(id=OPERATOR, is_bot=False, first_name="Former admin"))
    await drain(chm)
    assert not channel_sends(api)
    async with chm.sm() as session:
        assert (await session.scalar(select(Delivery))).state == "held"


async def test_inflight_send_blocks_content_mutation_and_stale_edits(chm, api):
    post = await setup_post(chm, api)
    svc = chm.extras["posts"]
    post = await svc.publish(post.id, OPERATOR, post.generation)
    op = await outbox.claim(chm)
    while op.kind != "publish":
        await outbox.execute(chm, op)
        op = await outbox.claim(chm)
    assert await outbox.mark_dispatched(chm, op)
    with pytest.raises(ContentError, match="busy"):
        await svc.edit(post.id, OPERATOR, post.generation, PostSpec(body=TextBody(text="Racing")))
    with pytest.raises(ContentError, match="stale"):
        await svc.cancel(post.id, OPERATOR, post.generation - 1)


async def test_schedule_quota_and_cross_chat_reply_are_enforced(chm, api):
    post = await setup_post(chm, api, second=True)
    svc = chm.extras["posts"]
    async with chm.sm() as session:
        await session.execute(update(Entitlement).values(max_schedules=1))
        await session.commit()
    await svc.publish(post.id, OPERATOR, post.generation, run_at=utcnow() + timedelta(hours=1))
    second = await svc.create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text="Second"), reply_message_id=42))
    with pytest.raises(ContentError, match="limit"):
        await svc.publish(second.id, OPERATOR, second.generation, run_at=utcnow() + timedelta(hours=1))
    with pytest.raises(ContentError, match="reply"):
        await svc.targets(second.id, OPERATOR, second.generation, [SECOND])


async def test_own_vs_all_library_permissions_are_live(chm, api):
    post = await setup_post(chm, api)
    api.responses["GetChatMember"] = lambda method: admin_member(method.user_id).model_copy(update={
        "can_edit_messages": False, "can_delete_messages": False}) if method.user_id == 77 else admin_member(method.user_id)
    svc = chm.extras["posts"]
    assert await svc.list_posts(77, CHANNEL_ID) == []
    with pytest.raises(AccessDenied):
        await svc.view(post.id, 77)


async def test_failed_publish_after_lease_recovery_remains_uncertain(chm, api):
    post = await setup_post(chm, api)
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    op = await outbox.claim(chm)
    while op.kind != "publish":
        await outbox.execute(chm, op)
        op = await outbox.claim(chm)
    await outbox.mark_dispatched(chm, op)
    async with chm.sm() as session:
        await session.execute(update(Operation).where(Operation.id == op.id).values(lease_until=utcnow() - timedelta(seconds=1)))
        await session.commit()
    await worker.sweep(chm)
    assert (await chm.extras["posts"].view(post.id, OPERATOR)).state == "uncertain"


async def test_failed_pin_can_be_retried_without_resending_content(chm, api):
    post = await setup_post(chm, api, PostSpec(body=TextBody(text="Pin retry"), pin=True))
    api.responses["PinChatMessage"] = TelegramBadRequest(method=PinChatMessage(chat_id=CHANNEL_ID, message_id=1), message="pin failed")
    svc = chm.extras["posts"]
    post = await svc.publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    api.responses.pop("PinChatMessage")
    await svc.retry_followups(post.id, OPERATOR, post.generation)
    await drain(chm)
    assert len(channel_sends(api)) == 1 and len(api.calls("PinChatMessage")) == 2
    assert (await svc.view(post.id, OPERATOR)).deliveries[0].pin_status == "succeeded"


async def test_media_edit_and_server_confirmed_identical_edit(chm, api):
    spec = PostSpec(kind="photo", body=TextBody(text="Photo"), file_id="photo_one", media_bot_id=BOT_ID)
    post = await setup_post(chm, api, spec)
    svc = chm.extras["posts"]
    post = await svc.publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    api.responses["EditMessageMedia"] = True
    changed = PostSpec(kind="video", body=TextBody(text="Video"), file_id="video_one", media_bot_id=BOT_ID)
    post = await svc.edit(post.id, OPERATOR, post.generation, changed)
    await drain(chm)
    assert api.calls("EditMessageMedia")[-1].media.media == "video_one"
    api.responses["EditMessageMedia"] = TelegramBadRequest(method=api.calls("EditMessageMedia")[-1], message="Bad Request: message is not modified")
    post = await svc.edit(post.id, OPERATOR, post.generation, changed)
    await drain(chm)
    assert (await svc.view(post.id, OPERATOR)).deliveries[0].edit_status == "succeeded"
    with pytest.raises(ContentError, match="conversion"):
        await svc.edit(post.id, OPERATOR, post.generation, PostSpec(body=TextBody(text="Text")))


async def test_own_edit_is_allowed_but_other_edit_requires_edit_all(chm, api):
    post = await setup_post(chm, api)
    svc = chm.extras["posts"]
    post = await svc.publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    api.responses["GetChatMember"] = lambda method: admin_member(method.user_id).model_copy(update={
        "can_edit_messages": False, "can_delete_messages": method.user_id == 77}) if method.user_id != BOT_ID else admin_member()
    post = await svc.edit(post.id, OPERATOR, post.generation, PostSpec(body=TextBody(text="Own edit")))
    await drain(chm)
    with pytest.raises(AccessDenied):
        await svc.edit(post.id, 77, post.generation, PostSpec(body=TextBody(text="Other edit")))
    await svc.delete(post.id, 77, post.generation)
    await drain(chm)
    assert len(api.calls("DeleteMessage")) == 1


async def test_library_categories_and_idempotent_draft_input(chm, api):
    await setup_post(chm, api)
    svc = chm.extras["posts"]
    first = await svc.create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text="Unique")), source_key="same-input")
    duplicate = await svc.create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text="Ignored duplicate")), source_key="same-input")
    assert first.id == duplicate.id
    await svc.publish(first.id, OPERATOR, first.generation, run_at=utcnow() + timedelta(hours=1))
    assert [p.id for p in await svc.list_posts(OPERATOR, category="scheduled")] == [first.id]
    assert len(await svc.list_posts(OPERATOR, category="draft")) == 1
    assert not await svc.list_posts(OPERATOR, category="sent")


async def test_cleanup_survives_channel_generation_change(chm, api):
    post = await setup_post(chm, api, PostSpec(body=TextBody(text="Cleanup"), delete_after_seconds=60))
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    await due(chm, "delete")
    await drain(chm)
    assert len(api.calls("DeleteMessage")) == 1


async def test_mixed_sent_pending_targets_edit_without_cancelling_new_edit(chm, api):
    post = await setup_post(chm, api, second=True)
    svc = chm.extras["posts"]
    post = await svc.targets(post.id, OPERATOR, post.generation, [CHANNEL_ID, SECOND])
    post = await svc.publish(post.id, OPERATOR, post.generation)
    # Dispatch exactly one destination, leaving another pending.
    while True:
        op = await outbox.claim(chm)
        await outbox.execute(chm, op)
        if op.kind == "publish":
            break
    post = await svc.edit(post.id, OPERATOR, post.generation, PostSpec(body=TextBody(text="Both updated")))
    await drain(chm)
    view = await svc.view(post.id, OPERATOR)
    assert view.state == "sent" and all(d.version == 2 for d in view.deliveries)
    assert len(api.calls("EditMessageText")) == 1
    sends = channel_sends(api) + channel_sends(api, SECOND)
    assert len(sends) == 2 and sum(m.text == "Both updated" for m in sends) == 1


async def test_recovery_is_not_starved_by_older_future_schedule(chm, api):
    from bots.channelmanager import delivery

    future = await setup_post(chm, api)
    svc = chm.extras["posts"]
    await svc.publish(future.id, OPERATOR, future.generation, run_at=utcnow() + timedelta(hours=1))
    failed = await svc.create(CHANNEL_ID, OPERATOR, PostSpec(body=TextBody(text="Cancelled externally")))
    await svc.publish(failed.id, OPERATOR, failed.generation)
    async with chm.sm() as session:
        target = await session.scalar(select(Delivery).where(Delivery.post_id == failed.id))
        await session.execute(update(Operation).where(Operation.id == target.publish_op).values(status="cancelled"))
        await session.commit()
    await delivery.reconcile(chm, limit=1)
    assert (await svc.view(failed.id, OPERATOR)).state == "cancelled"
    assert (await svc.view(future.id, OPERATOR)).state == "queued"


async def test_publish_retry_after_defers_without_losing_target(chm, api):
    post = await setup_post(chm, api)
    svc = chm.extras["posts"]
    await svc.publish(post.id, OPERATOR, post.generation)
    api.responses["SendMessage"] = lambda method: TelegramRetryAfter(method=method, retry_after=10, message="slow down") if method.chat_id == CHANNEL_ID else Message(
        message_id=501, date=utcnow(), chat=Chat(id=OPERATOR, type="private"))
    await drain(chm)
    async with chm.sm() as session:
        op = await session.scalar(select(Operation).where(Operation.kind == "publish"))
        assert op.status == "pending" and op.attempts == 1 and not op.dispatched
        assert op.run_at > utcnow() + timedelta(seconds=5)
    api.responses.pop("SendMessage")
    await due(chm, "publish")
    await drain(chm)
    assert (await svc.view(post.id, OPERATOR)).state == "sent"


async def test_rate_store_outage_keeps_publication_undispatched(chm, api, monkeypatch):
    post = await setup_post(chm, api)
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)

    async def unavailable(*args):
        raise ConnectionError("isolated test outage")
    monkeypatch.setattr(outbox, "reserve_budget", unavailable)
    await drain(chm)
    assert not channel_sends(api)
    async with chm.sm() as session:
        op = await session.scalar(select(Operation).where(Operation.kind == "publish"))
        assert op.status == "pending" and not op.dispatched and op.attempts == 0
        assert op.error_code == "rate_store_unavailable"


async def test_disconnecting_during_dispatched_send_does_not_recreate_followups(chm, api):
    from bots.channelmanager import delivery

    post = await setup_post(chm, api, PostSpec(body=TextBody(text="In flight"), pin=True, delete_after_seconds=60))
    svc = chm.extras["posts"]
    await svc.publish(post.id, OPERATOR, post.generation)
    op = await outbox.claim(chm)
    while op.kind != "publish":
        await outbox.execute(chm, op)
        op = await outbox.claim(chm)
    assert await outbox.mark_dispatched(chm, op)
    op.dispatched = True
    channel = await chm.extras["channelmanager"].get(CHANNEL_ID)
    await chm.extras["channelmanager"].disconnect(CHANNEL_ID, OPERATOR, channel.generation)
    await delivery.complete(chm, op, outbox.PostJob.model_validate(op.payload), "succeeded", result=Message(
        message_id=777, date=utcnow(), chat=Chat(id=CHANNEL_ID, type="channel")))
    view = await svc.view(post.id, OPERATOR)
    assert view.state == "sent" and view.deliveries[0].pin_status == view.deliveries[0].delete_status == "cancelled"
    await due(chm, "delete")
    await drain(chm)
    assert not api.calls("PinChatMessage") and not api.calls("DeleteMessage")
    with pytest.raises(AccessDenied, match="channel_inactive"):
        await svc.edit(post.id, OPERATOR, view.post.generation, PostSpec(body=TextBody(text="Disconnected edit"), pin=True, delete_after_seconds=60))
