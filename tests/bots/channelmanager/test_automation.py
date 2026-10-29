from datetime import timedelta

import pytest
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
)
from aiogram.types import Chat, Message, MessageEntity, MessageId, PhotoSize, Update
from sqlalchemy import func, select, update

from bots.channelmanager import automation, automation_delivery, ingress, interactions, outbox
from bots.channelmanager.auto_content import (
    Filters,
    MediaReference,
    Replacement,
    RouteSpec,
    RuleSpec,
    SourceItem,
    splice,
    transform,
)
from bots.channelmanager.content import ContentError, TextBody, parse_buttons, utf16len
from bots.channelmanager.keywords import Expression
from bots.channelmanager.models import (
    AutoAction,
    AutoSnapshot,
    AutoSource,
    Delivery,
    Operation,
    Vote,
)
from bots.channelmanager.permissions import AccessDenied
from core.db.base import utcnow
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR, admin_member
from tests.bots.channelmanager.test_publishing import drain
from tests.conftest import BOT_ID

DESTINATION = CHANNEL_ID - 1
GROUP = -987654321


@pytest.fixture(autouse=True)
def instant_budgets(monkeypatch):
    async def immediate(*args):
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", immediate)


@pytest.mark.parametrize("expression,text,expected", [
    ("chelp", "Welcome to chelp", True), ("chelp", "chelpbot", False),
    ("c(*)bot", "cbot", True), ("c(*)bot", "chelpbot", True), ("c(*)bot", "chelp bot", False),
    ("c(+)bot", "cbot", False), ("c(+)bot", "chbot", True),
    ("c(?)bot", "cbot", True), ("c(?)bot", "chbot", True), ("c(?)bot", "chelpbot", False),
    ('"exact message"', "exact message", True), ('"exact message"', "the exact message", False),
    ("bot && help", "Help is available from this bot!", True), ("bot && help", "bot without assistance", False),
    ("café", "CAFE\u0301!", True), ("strasse", "Straße", True), ("مرحبا", "مرحبا، بالعالم", True),
    ("مرحبا", "مرحباً", False), ("word", "sword", False),
])
def test_bounded_keyword_contract(expression, text, expected):
    assert Expression.parse(expression).matches(text) is expected


@pytest.mark.parametrize("expression", ["", "x &&", "[a-z]+ ", '"open', "a b", "x(*)" * 5, "x" * 65])
def test_invalid_keyword_syntax_is_rejected(expression):
    with pytest.raises(ContentError):
        Expression.parse(expression)


def test_keyword_budget_and_case_sensitive_mode():
    assert not Expression.parse("Word", case_sensitive=True).matches("word")
    with pytest.raises(ContentError, match="keyword_budget"):
        Expression.parse("(*)a(*)b(*)c").matches("a" * 500, budget=[2])


def item(text="hello", *, kind="text", message_id=501):
    return SourceItem(message_id=message_id, kind=kind, body=TextBody(text=text), sent_at=utcnow(),
        file_id="photo_ref" if kind != "text" else None, unique_id="unique" if kind != "text" else None)


def test_transform_preserves_arabic_emoji_entities_and_simultaneous_replacements():
    original = item("/ad 👋 مرحبا one two!")
    original.body = TextBody(text=original.body.text, entities=[MessageEntity(type="bold", offset=4, length=utf16len("👋 مرحبا one two!"))])
    rule = RuleSpec(filters=Filters(command="/ad"), header=TextBody(text="عنوان"), signature=TextBody(text="توقيع"),
        replacements=[Replacement(old="one", new="two"), Replacement(old="two", new="three")])
    values, metadata, _ = transform([original], rule, BOT_ID)
    assert values[0].body.text == "عنوان\n\n👋 مرحبا two three!\n\nتوقيع"
    entity = values[0].body.entities[0]
    assert entity.offset == utf16len("عنوان\n\n") and entity.length == utf16len("👋 مرحبا two three!")
    assert metadata[501] == {"prefix": "عنوان\n\n", "suffix": "\n\nتوقيع"}
    assert original.body.text.startswith("/ad")


def test_splice_clips_partial_entities_and_never_splits_surrogates():
    body = TextBody(text="👋 hello world", entities=[MessageEntity(type="italic", offset=5, length=6)])
    changed = splice(body, 2, 7, "مرحبا")
    assert changed.text == "👋 مرحبا world" and changed.entities[0].offset == 8
    TextBody.model_validate(changed.model_dump(mode="json"))


def test_album_transformation_only_adds_one_signature_and_reports_fallbacks():
    rule = RuleSpec(header=TextBody(text="ignored"), signature=TextBody(text="sig"), buttons=parse_buttons("Like | vote"), reactions=["A"],
        replacements=[Replacement(old="one", new="two")])
    values, _, warnings = transform([item("one", kind="photo"), item("", kind="video", message_id=502)], rule, BOT_ID, album=True)
    assert values[0].body.text == "one\n\nsig" and values[1].body.text == ""
    assert warnings == ["album_signature_only"] and values[0].buttons == []


async def setup_automation(chm, api, *, rule=None, route=None, destination=DESTINATION, content="original", mode="copy", propagate=False):
    api.responses["GetChat"] = lambda method: Chat(id=int(method.chat_id), type="supergroup" if int(method.chat_id) == GROUP else "channel", title="Automation test")
    api.responses["GetChatMember"] = lambda method: admin_member(method.user_id)
    api.responses["EditMessageMedia"] = True
    api.responses["SendMediaGroup"] = lambda method: [Message(message_id=2000 + n, date=utcnow(), chat=Chat(id=int(method.chat_id), type="channel")) for n, _ in enumerate(method.media)]
    api.responses["ForwardMessages"] = lambda method: [MessageId(message_id=3000 + n) for n, _ in enumerate(method.message_ids)]
    await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    if destination != GROUP:
        await chm.extras["channelmanager"].connect(destination, OPERATOR)
    svc = chm.extras["automation"]
    saved_rule = await svc.save_rule(CHANNEL_ID, OPERATOR, "Default", rule, active=True) if rule is not None else None
    saved_route = await svc.save_route(CHANNEL_ID, OPERATOR, "Route", destination, route or RouteSpec(mode=mode, content=content, propagate_edits=propagate), active=True) if route is not False else None
    return saved_rule, saved_route


def source_update(text="hello", *, message_id=501, update_id=9001, edited=False, album=None, kind="text", protected=False):
    kwargs = {"text": text} if kind == "text" else {"photo": [PhotoSize(file_id=f"photo_{message_id}", file_unique_id=f"unique_{message_id}", width=100, height=100)], "caption": text}
    message = Message(message_id=message_id, date=utcnow() - timedelta(seconds=10), edit_date=int(utcnow().timestamp()) if edited else None,
        chat=Chat(id=CHANNEL_ID, type="channel", title="Source"), media_group_id=album, has_protected_content=protected or None, **kwargs)
    return Update(update_id=update_id, **{"edited_channel_post" if edited else "channel_post": message})


async def ingest_all(chm, dp, event, *, ready_album=False):
    await dp.feed_update(chm.bot, event)
    for _ in range(30):
        if not await ingress.process_one(chm):
            break
    if ready_album:
        async with chm.sm() as session:
            await session.execute(update(AutoSource).values(available_at=utcnow()))
            await session.commit()


async def plan_all(chm):
    for _ in range(30):
        if not await automation.plan_one(chm):
            return
    raise AssertionError("unexpected repeated planning")


async def test_source_receipt_is_durable_and_duplicate_enrichment_is_suppressed(chm, dp, api):
    await setup_automation(chm, api, rule=RuleSpec(header=TextBody(text="Header"), signature=TextBody(text="Sig")), route=False)
    event = source_update("hello")
    await ingest_all(chm, dp, event)
    await ingest_all(chm, dp, event)
    await plan_all(chm)
    await drain(chm)
    edits = [m for m in api.calls("EditMessageText") if m.chat_id == CHANNEL_ID]
    assert len(edits) == 1 and edits[0].text == "Header\n\nhello\n\nSig"
    self_edit = source_update(edits[0].text, edited=True, update_id=9002)
    await ingest_all(chm, dp, self_edit)
    await plan_all(chm)
    await drain(chm)
    assert len([m for m in api.calls("EditMessageText") if m.chat_id == CHANNEL_ID]) == 1
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(AutoSnapshot)) == 1


async def test_rule_priority_filters_and_removable_leading_command(chm, dp, api):
    await setup_automation(chm, api, route=False)
    svc = chm.extras["automation"]
    await svc.save_rule(CHANNEL_ID, OPERATOR, "Low", RuleSpec(header=TextBody(text="Low")), priority=100, active=True)
    await svc.save_rule(CHANNEL_ID, OPERATOR, "High", RuleSpec(filters=Filters(command="/ad", triggers=["hello"], excludes=["blocked"]),
        header=TextBody(text="High")), priority=1, active=True)
    await ingest_all(chm, dp, source_update("  /ad hello!"))
    await plan_all(chm)
    await drain(chm)
    assert next(m for m in api.calls("EditMessageText") if m.chat_id == CHANNEL_ID).text == "High\n\nhello!"


async def test_original_and_transformed_copies_are_independent_of_source_edit(chm, dp, api):
    await setup_automation(chm, api, rule=RuleSpec(signature=TextBody(text="Sig")))
    await chm.extras["automation"].save_route(CHANNEL_ID, OPERATOR, "Enhanced group", GROUP,
        RouteSpec(content="transformed"), active=True)
    await ingest_all(chm, dp, source_update("hello"))
    await plan_all(chm)
    await drain(chm)
    assert [m.text for m in api.calls("SendMessage") if m.chat_id == DESTINATION] == ["hello"]
    assert [m.text for m in api.calls("SendMessage") if m.chat_id == GROUP] == ["hello\n\nSig"]


async def test_original_attributed_forward_precedes_enrichment(chm, dp, api):
    await setup_automation(chm, api, rule=RuleSpec(signature=TextBody(text="Sig")), mode="forward")
    await ingest_all(chm, dp, source_update())
    await plan_all(chm)
    await drain(chm)
    calls = [type(m).__name__ for m in api.requests]
    assert calls.index("ForwardMessage") < calls.index("EditMessageText")


async def test_group_failure_does_not_block_other_destination(chm, dp, api):
    await setup_automation(chm, api)
    await chm.extras["automation"].save_route(CHANNEL_ID, OPERATOR, "Group", GROUP, RouteSpec(), active=True)
    api.responses["SendMessage"] = lambda method: TelegramForbiddenError(method=method, message="group lost") if method.chat_id == GROUP else Message(
        message_id=120, date=utcnow(), chat=Chat(id=int(method.chat_id), type="channel" if int(method.chat_id) < 0 else "private"))
    await ingest_all(chm, dp, source_update())
    await plan_all(chm)
    await drain(chm)
    async with chm.sm() as session:
        actions = (await session.scalars(select(AutoAction).where(AutoAction.kind == "copy"))).all()
        assert {a.status for a in actions} == {"succeeded", "failed"}


async def test_protected_source_never_reuploads_or_forwards(chm, dp, api):
    await setup_automation(chm, api)
    await ingest_all(chm, dp, source_update(protected=True))
    await plan_all(chm)
    await drain(chm)
    assert not [m for m in api.calls("SendMessage") if m.chat_id == DESTINATION]
    async with chm.sm() as session:
        assert (await session.scalar(select(AutoAction))).error_code == "protected_source"


async def test_copy_edit_propagation_updates_known_message_without_resending(chm, dp, api):
    await setup_automation(chm, api, propagate=True)
    await ingest_all(chm, dp, source_update("first"))
    await plan_all(chm)
    await drain(chm)
    await ingest_all(chm, dp, source_update("second", edited=True, update_id=9002))
    await plan_all(chm)
    await drain(chm)
    assert len([m for m in api.calls("SendMessage") if m.chat_id == DESTINATION]) == 1
    assert [m.text for m in api.calls("EditMessageText") if m.chat_id == DESTINATION] == ["second"]


async def test_edit_propagation_is_off_by_default(chm, dp, api):
    await setup_automation(chm, api)
    await ingest_all(chm, dp, source_update("first"))
    await plan_all(chm)
    await drain(chm)
    await ingest_all(chm, dp, source_update("second", edited=True, update_id=9002))
    await plan_all(chm)
    await drain(chm)
    assert not [m for m in api.calls("EditMessageText") if m.chat_id == DESTINATION]
    async with chm.sm() as session:
        latest = await session.scalar(select(AutoAction).where(AutoAction.version == 2))
        assert latest.status == "skipped" and latest.error_code == "edit_propagation_off"
    for version in range(3, 5):
        await ingest_all(chm, dp, source_update(str(version), edited=True, update_id=9000 + version))
        await plan_all(chm)
        await drain(chm)
    assert len([m for m in api.calls("SendMessage") if m.chat_id == DESTINATION]) == 1
    assert not [m for m in api.calls("EditMessageText") if m.chat_id == DESTINATION]


async def test_uncertain_copy_is_not_replayed_on_source_edit_or_retry(chm, dp, api):
    await setup_automation(chm, api, propagate=True)
    api.responses["SendMessage"] = lambda method: TelegramNetworkError(method=method, message="unknown")
    await ingest_all(chm, dp, source_update())
    await plan_all(chm)
    await drain(chm)
    async with chm.sm() as session:
        first = await session.scalar(select(AutoAction))
        assert first.status == "uncertain"
    with pytest.raises(ContentError, match="no_safe_retry"):
        await chm.extras["automation"].retry(first.id, OPERATOR)
    await ingest_all(chm, dp, source_update("new", edited=True, update_id=9002))
    await plan_all(chm)
    await drain(chm)
    assert len([m for m in api.calls("SendMessage") if m.chat_id == DESTINATION]) == 1
    await ingest_all(chm, dp, source_update("third", edited=True, update_id=9003))
    await plan_all(chm)
    await drain(chm)
    assert len([m for m in api.calls("SendMessage") if m.chat_id == DESTINATION]) == 1
    async with chm.sm() as session:
        latest = await session.scalar(select(AutoAction).where(AutoAction.version == 3))
        assert latest.status == "held" and latest.error_code == "previous_delivery_uncertain"


async def test_album_collection_signature_copy_and_layout_change_hold(chm, dp, api):
    await setup_automation(chm, api, rule=RuleSpec(signature=TextBody(text="Sig"), header=TextBody(text="Ignored")), content="transformed", propagate=True)
    await ingest_all(chm, dp, source_update("Caption", album="group", kind="photo"))
    assert not await automation.plan_one(chm)
    await ingest_all(chm, dp, source_update("", message_id=502, update_id=9002, album="group", kind="photo"), ready_album=True)
    await plan_all(chm)
    await drain(chm)
    sent = api.calls("SendMediaGroup")
    assert len(sent) == 1 and sent[0].media[0].caption == "Caption\n\nSig"
    assert not sent[0].media[1].caption
    await ingest_all(chm, dp, source_update("late", message_id=503, update_id=9003, album="group", kind="photo"), ready_album=True)
    await plan_all(chm)
    async with chm.sm() as session:
        source = await session.scalar(select(AutoSource))
        assert source.status == "held" and source.error_code == "album_layout_changed"
    assert len(api.calls("SendMediaGroup")) == 1


async def test_bot_generated_copy_is_not_processed_in_destination(chm, dp, api):
    await setup_automation(chm, api)
    await chm.extras["automation"].save_rule(DESTINATION, OPERATOR, "Secondary rule", RuleSpec(header=TextBody(text="Loop")), active=True)
    await ingest_all(chm, dp, source_update("manual"))
    await plan_all(chm)
    await drain(chm)
    async with chm.sm() as session:
        action = await session.scalar(select(AutoAction).where(AutoAction.kind == "copy"))
    generated = Message(message_id=action.remote_ids[0], date=utcnow(), chat=Chat(id=DESTINATION, type="channel"), text="manual")
    await ingest_all(chm, dp, Update(update_id=9900, channel_post=generated))
    await plan_all(chm)
    await drain(chm)
    assert not [m for m in api.calls("EditMessageText") if m.chat_id == DESTINATION]


async def test_route_cycle_and_forward_edit_configuration_are_rejected(chm, api):
    await setup_automation(chm, api)
    with pytest.raises(ContentError, match="route_cycle"):
        await chm.extras["automation"].save_route(DESTINATION, OPERATOR, "Back", CHANNEL_ID, RouteSpec(), active=True)
    with pytest.raises(ValueError, match="forward_edits"):
        RouteSpec(mode="forward", propagate_edits=True)


async def test_attachment_separator_and_source_deletion_are_independent(chm, dp, api):
    rule = RuleSpec(signature=TextBody(text="Sig"), delete_after_seconds=60,
        attachment=MediaReference(kind="photo", file_id="attachment", unique_id="unique_attachment", bot_id=BOT_ID),
        separator=MediaReference(kind="sticker", file_id="separator", unique_id="unique_sticker", bot_id=BOT_ID))
    await setup_automation(chm, api, rule=rule, route=False)
    await ingest_all(chm, dp, source_update("body"))
    await plan_all(chm)
    await drain(chm)
    assert api.calls("EditMessageMedia")[0].media.media == "attachment"
    assert len(api.calls("SendSticker")) == 1
    async with chm.sm() as session:
        timers = (await session.scalars(select(AutoAction).where(AutoAction.kind == "delete"))).all()
        assert len(timers) == 2
        timer = next(t for t in timers if not t.payload["own"])
        assert timer.payload["message_id"] == 501
        await session.execute(update(Operation).where(Operation.id == timer.operation_id).values(run_at=utcnow()))
        await session.commit()
    await drain(chm)
    assert api.calls("DeleteMessage")[-1].message_id == 501


async def test_source_vote_buttons_use_managed_version_scopes(chm, dp, api):
    await setup_automation(chm, api, rule=RuleSpec(reactions=["A", "B"]), route=False)
    await ingest_all(chm, dp, source_update("Vote"))
    await plan_all(chm)
    await drain(chm)
    async with chm.sm() as session:
        target = await session.scalar(select(Delivery))
    assert await interactions.cast(chm, target.id, target.version, 77, 40)
    await drain(chm)
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(Vote)) == 1


async def test_album_edits_reuse_all_remote_ids_across_multiple_versions(chm, dp, api):
    await setup_automation(chm, api, propagate=True)
    await ingest_all(chm, dp, source_update("One", kind="photo", album="album"))
    await ingest_all(chm, dp, source_update("Two", message_id=502, update_id=9002, kind="photo", album="album"), ready_album=True)
    await plan_all(chm)
    await drain(chm)
    for version in range(2, 4):
        await ingest_all(chm, dp, source_update(str(version), edited=True, update_id=9002 + version, kind="photo", album="album"), ready_album=True)
        await plan_all(chm)
        await drain(chm)
    assert len(api.calls("SendMediaGroup")) == 1
    edits = [m for m in api.calls("EditMessageMedia") if m.chat_id == DESTINATION]
    assert [m.message_id for m in edits] == [2000, 2001, 2000, 2001]


async def test_album_signature_acknowledgement_does_not_plan_another_version(chm, dp, api):
    await setup_automation(chm, api, rule=RuleSpec(signature=TextBody(text="Sig")), propagate=True)
    await ingest_all(chm, dp, source_update("One", kind="photo", album="album"))
    await ingest_all(chm, dp, source_update("", message_id=502, update_id=9002, kind="photo", album="album"), ready_album=True)
    await plan_all(chm)
    await drain(chm)
    await ingest_all(chm, dp, source_update("One\n\nSig", edited=True, update_id=9003, kind="photo", album="album"), ready_album=True)
    await plan_all(chm)
    await drain(chm)
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(AutoSnapshot)) == 1
    assert len(api.calls("SendMediaGroup")) == 1
    assert not [m for m in api.calls("EditMessageMedia") if m.chat_id == DESTINATION]


async def test_route_destination_change_never_edits_ids_in_another_chat(chm, dp, api):
    _, route = await setup_automation(chm, api, propagate=True)
    await ingest_all(chm, dp, source_update("One"))
    await plan_all(chm)
    await drain(chm)
    await chm.extras["automation"].save_route(CHANNEL_ID, OPERATOR, route.name, GROUP, RouteSpec(propagate_edits=True),
        active=True, resource_id=route.id, generation=route.generation)
    await ingest_all(chm, dp, source_update("Two", edited=True, update_id=9002))
    await plan_all(chm)
    await drain(chm)
    assert [m.text for m in api.calls("SendMessage") if m.chat_id == GROUP] == ["Two"]
    assert not [m for m in api.calls("EditMessageText") if m.chat_id == GROUP]


async def test_forward_to_copy_mode_change_holds_existing_publication(chm, dp, api):
    _, route = await setup_automation(chm, api, mode="forward")
    await ingest_all(chm, dp, source_update("One"))
    await plan_all(chm)
    await drain(chm)
    await chm.extras["automation"].save_route(CHANNEL_ID, OPERATOR, route.name, DESTINATION, RouteSpec(propagate_edits=True),
        active=True, resource_id=route.id, generation=route.generation)
    for version in range(2, 4):
        await ingest_all(chm, dp, source_update(str(version), edited=True, update_id=9000 + version))
        await plan_all(chm)
        await drain(chm)
    async with chm.sm() as session:
        latest = await session.scalar(select(AutoAction).where(AutoAction.version == 3))
        assert latest.status == "held" and latest.error_code == "route_mode_changed"
    assert len(api.calls("ForwardMessage")) == 1
    assert not [m for m in api.calls("EditMessageText") if m.chat_id == DESTINATION]


@pytest.mark.parametrize("propagate", [False, True])
async def test_live_source_protection_blocks_already_planned_copy(chm, dp, api, propagate):
    await setup_automation(chm, api, propagate=propagate)
    await ingest_all(chm, dp, source_update())
    await plan_all(chm)
    if propagate:
        await drain(chm)
        await ingest_all(chm, dp, source_update("Private change", edited=True, update_id=9002))
        await plan_all(chm)
    api.responses["GetChat"] = lambda m: Chat(id=int(m.chat_id), type="channel", title="Protected", has_protected_content=True)
    await drain(chm)
    assert len([m for m in api.calls("SendMessage") if m.chat_id == DESTINATION]) == int(propagate)
    assert not [m for m in api.calls("EditMessageText") if m.chat_id == DESTINATION]
    async with chm.sm() as session:
        assert (await session.scalar(select(AutoAction).order_by(AutoAction.version.desc()))).error_code == "protected_source"


async def test_manual_edit_of_enriched_post_does_not_repeat_affixes(chm, dp, api):
    await setup_automation(chm, api, rule=RuleSpec(header=TextBody(text="Header"), signature=TextBody(text="Sig")), route=False)
    await ingest_all(chm, dp, source_update("One"))
    await plan_all(chm)
    await drain(chm)
    await ingest_all(chm, dp, source_update("Header\n\nTwo\n\nSig", edited=True, update_id=9002))
    await plan_all(chm)
    await drain(chm)
    assert [m.text for m in api.calls("EditMessageText") if m.chat_id == CHANNEL_ID] == ["Header\n\nOne\n\nSig", "Header\n\nTwo\n\nSig"]


async def test_failed_target_retry_does_not_repeat_successful_target(chm, dp, api):
    await setup_automation(chm, api)
    await chm.extras["automation"].save_route(CHANNEL_ID, OPERATOR, "Group", GROUP, RouteSpec(), active=True)
    api.responses["SendMessage"] = lambda m: TelegramForbiddenError(method=m, message="blocked") if m.chat_id == GROUP else Message(
        message_id=800, date=utcnow(), chat=Chat(id=int(m.chat_id), type="channel" if int(m.chat_id) < 0 else "private"))
    await ingest_all(chm, dp, source_update())
    await plan_all(chm)
    await drain(chm)
    async with chm.sm() as session:
        failed = await session.scalar(select(AutoAction).where(AutoAction.status == "failed"))
    api.responses.pop("SendMessage")
    await chm.extras["automation"].retry(failed.id, OPERATOR)
    await drain(chm)
    assert len([m for m in api.calls("SendMessage") if m.chat_id == DESTINATION]) == 1
    assert len([m for m in api.calls("SendMessage") if m.chat_id == GROUP]) == 2


async def test_native_source_rights_are_rechecked_for_mirror_edits(chm, dp, api):
    await setup_automation(chm, api, rule=RuleSpec(signature=TextBody(text="Sig")), route=False)
    await ingest_all(chm, dp, source_update())
    await plan_all(chm)
    await drain(chm)
    async with chm.sm() as session:
        source = await session.scalar(select(AutoSource))
    limited = admin_member(OPERATOR).model_copy(update={"can_edit_messages": False, "can_delete_messages": False})
    api.responses["GetChatMember"] = lambda m: limited if m.user_id == OPERATOR else admin_member(m.user_id)
    for action in ["edit", "delete"]:
        with pytest.raises(AccessDenied, match="manual_source_right"):
            await chm.extras["posts"].view(source.mirror_post_id, OPERATOR, action)


async def test_429_and_unavailable_budget_defer_without_duplicate_delivery(chm, dp, api, monkeypatch):
    await setup_automation(chm, api)
    await ingest_all(chm, dp, source_update())
    await plan_all(chm)
    async def unavailable(*args):
        raise ConnectionError("offline")
    monkeypatch.setattr(outbox, "reserve_budget", unavailable)
    await drain(chm)
    assert not [m for m in api.calls("SendMessage") if m.chat_id == DESTINATION]
    async def immediate(*args):
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", immediate)
    api.responses["SendMessage"] = lambda m: TelegramRetryAfter(method=m, message="rate", retry_after=1)
    async with chm.sm() as session:
        await session.execute(update(Operation).where(Operation.status == "pending").values(run_at=utcnow()))
        await session.commit()
    await drain(chm)
    async with chm.sm() as session:
        action = await session.scalar(select(AutoAction))
        op = await session.get(Operation, (BOT_ID, action.operation_id))
        assert action.status == "pending" and op.attempts == 1
        op.run_at = utcnow()
        await session.commit()
    api.responses.pop("SendMessage")
    await drain(chm)
    async with chm.sm() as session:
        assert (await session.get(AutoAction, (BOT_ID, action.id))).status == "succeeded"


async def test_recovered_unknown_source_edit_updates_both_reports(chm, dp, api):
    await setup_automation(chm, api, rule=RuleSpec(signature=TextBody(text="Sig")), route=False)
    await ingest_all(chm, dp, source_update())
    await plan_all(chm)
    async with chm.sm() as session:
        action = await session.scalar(select(AutoAction).where(AutoAction.kind == "edit"))
        op = await session.get(Operation, (BOT_ID, action.operation_id))
        op.status, op.error_code = "uncertain", "lease_expired"
        await session.commit()
    await automation_delivery.reconcile(chm)
    async with chm.sm() as session:
        assert (await session.get(AutoAction, (BOT_ID, action.id))).status == "uncertain"
        target = await session.scalar(select(Delivery))
        assert target.state == "sent" and target.edit_status == "uncertain"


async def test_partial_album_forward_is_held_on_later_edits(chm, dp, api):
    await setup_automation(chm, api, mode="forward")
    api.responses["ForwardMessages"] = [MessageId(message_id=3000)]
    await ingest_all(chm, dp, source_update("One", kind="photo", album="album"))
    await ingest_all(chm, dp, source_update("", message_id=502, update_id=9002, kind="photo", album="album"), ready_album=True)
    await plan_all(chm)
    await drain(chm)
    for version in range(2, 4):
        await ingest_all(chm, dp, source_update(str(version), edited=True, update_id=9002 + version, kind="photo", album="album"), ready_album=True)
        await plan_all(chm)
        await drain(chm)
    assert len(api.calls("ForwardMessages")) == 1
    async with chm.sm() as session:
        latest = await session.scalar(select(AutoAction).where(AutoAction.version == 3))
        assert latest.status == "held" and latest.error_code == "previous_delivery_uncertain"
