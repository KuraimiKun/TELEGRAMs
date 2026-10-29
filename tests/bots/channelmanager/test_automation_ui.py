import pytest
from aiogram.types import Chat, Message, PhotoSize, Sticker, Update
from sqlalchemy import func, select

from bots.channelmanager import outbox
from bots.channelmanager.auto_content import RuleSpec
from bots.channelmanager.automation_ui import AutoCb
from bots.channelmanager.models import AutoAction, AutoRule, ForwardRoute
from core.db.base import utcnow
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR
from tests.bots.channelmanager.test_automation import DESTINATION, setup_automation
from tests.bots.channelmanager.test_publishing_ui import feed
from tests.conftest import callback_update, message_update, tg_user


@pytest.fixture(autouse=True)
def instant_budgets(monkeypatch):
    async def immediate(*args):
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", immediate)


async def click(chm, dp, action, resource, generation=0, *, actor=OPERATOR):
    await feed(chm, dp, callback_update(AutoCb(a=action, x=str(resource), g=generation, u=OPERATOR).pack(), user_id=actor))


async def first_rule(chm):
    async with chm.sm() as session:
        return await session.scalar(select(AutoRule))


async def test_new_set_editor_native_text_and_activation_confirmation(chm, dp, api):
    await setup_automation(chm, api, route=False)
    await feed(chm, dp, message_update("/automation"))
    await click(chm, dp, "newrule", CHANNEL_ID)
    await feed(chm, dp, message_update("Editorial"))
    rule = await first_rule(chm)
    assert rule and not rule.active
    await click(chm, dp, "header", rule.id, rule.generation)
    await feed(chm, dp, message_update("عنوان"))
    rule = await first_rule(chm)
    assert RuleSpec.model_validate(rule.spec).header.text == "عنوان"
    await click(chm, dp, "on", rule.id, rule.generation)
    assert not (await first_rule(chm)).active
    await click(chm, dp, "enable", rule.id, rule.generation)
    await click(chm, dp, "on", rule.id, rule.generation, actor=77)
    assert not (await first_rule(chm)).active
    await click(chm, dp, "on", rule.id, rule.generation)
    assert (await first_rule(chm)).active


async def test_rule_filters_command_priority_and_replacements(chm, dp, api):
    rule, _ = await setup_automation(chm, api, rule=RuleSpec(), route=False)
    fields = [("filterin", "bot && help\nc(*)bot"), ("filterout", '"blocked"'), ("media", "text,photo"),
        ("command", "/ad"), ("priority", "5"), ("replace", "old => new\nword => replacement")]
    for action, text in fields:
        rule = await first_rule(chm)
        await click(chm, dp, action, rule.id, rule.generation)
        await feed(chm, dp, message_update(text))
    rule = await first_rule(chm)
    spec = RuleSpec.model_validate(rule.spec)
    assert rule.priority == 5 and spec.filters.command == "/ad"
    assert spec.filters.media == ["text", "photo"] and len(spec.replacements) == 2


async def test_rule_media_refs_come_from_uploaded_bot_media(chm, dp, api):
    rule, _ = await setup_automation(chm, api, rule=RuleSpec(), route=False)
    await click(chm, dp, "attach", rule.id, rule.generation)
    photo = Message(message_id=555, date=utcnow(), chat=Chat(id=OPERATOR, type="private"), from_user=tg_user(),
        photo=[PhotoSize(file_id="attachment_ref", file_unique_id="attachment_unique", width=10, height=10)])
    await feed(chm, dp, Update(update_id=556, message=photo))
    rule = await first_rule(chm)
    assert RuleSpec.model_validate(rule.spec).attachment.file_id == "attachment_ref"
    await click(chm, dp, "sticker", rule.id, rule.generation)
    sticker = Message(message_id=557, date=utcnow(), chat=photo.chat, from_user=tg_user(),
        sticker=Sticker(file_id="sticker_ref", file_unique_id="sticker_unique", width=10, height=10, is_animated=False, is_video=False, type="regular"))
    await feed(chm, dp, Update(update_id=558, message=sticker))
    assert RuleSpec.model_validate((await first_rule(chm)).spec).separator.file_id == "sticker_ref"


async def test_route_creation_modes_and_forward_edit_fallback(chm, dp, api):
    await setup_automation(chm, api, route=False)
    await click(chm, dp, "newroute", CHANNEL_ID)
    await feed(chm, dp, message_update("Destination route"))
    await feed(chm, dp, message_update(str(DESTINATION)))
    async with chm.sm() as session:
        route = await session.scalar(select(ForwardRoute))
    assert route and not route.active
    await click(chm, dp, "mode", route.id, route.generation)
    route = await chm.extras["automation"].get("route", route.id, OPERATOR)
    assert route.spec["mode"] == "forward"
    await click(chm, dp, "propagate", route.id, route.generation)
    route = await chm.extras["automation"].get("route", route.id, OPERATOR)
    assert route.spec["propagate_edits"] is False
    assert "propagation is supported for copies" in api.calls("EditMessageText")[-1].text


async def test_sample_preview_does_not_enable_or_queue_source_work(chm, dp, api):
    await setup_automation(chm, api, route=False)
    rule = await chm.extras["automation"].save_rule(CHANNEL_ID, OPERATOR, "Sample", RuleSpec(header={"text": "Header"}))
    await click(chm, dp, "test", rule.id, rule.generation)
    await feed(chm, dp, message_update("hello"))
    assert any(m.chat_id == OPERATOR and m.text == "Header\n\nhello" for m in api.calls("SendMessage"))
    assert not (await first_rule(chm)).active
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(AutoAction)) == 0


async def test_stale_resource_callback_and_cancel_input_are_safe(chm, dp, api):
    rule, _ = await setup_automation(chm, api, rule=RuleSpec(), route=False)
    await click(chm, dp, "header", rule.id, rule.generation)
    await feed(chm, dp, message_update("/cancel"))
    await feed(chm, dp, message_update("unrelated"))
    assert RuleSpec.model_validate((await first_rule(chm)).spec).header.text == ""
    await chm.extras["automation"].stop("rule", rule.id, OPERATOR, rule.generation)
    await click(chm, dp, "enable", rule.id, rule.generation)
    assert not (await first_rule(chm)).active


def test_automation_callback_bytes_fit_telegram_limit():
    assert len(AutoCb(a="filterout", x="f" * 16, g=2147483647, u=4503599627370495).pack().encode()) <= 64
    assert len(AutoCb(a="r", x="f" * 32, g=0, u=4503599627370495).pack().encode()) <= 64
