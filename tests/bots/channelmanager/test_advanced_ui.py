from datetime import timedelta

import pytest
from aiogram.types import Chat, ChatMemberLeft, User
from sqlalchemy import func, select

from bots.channelmanager import interactions, outbox
from bots.channelmanager.advanced_ui import AdvancedCb
from bots.channelmanager.content import PostSpec, TextBody, parse_buttons
from bots.channelmanager.models import Batch, Calendar, Preset, Recurrence, Vote
from bots.channelmanager.publishing_ui import PostCb
from core.db.base import utcnow
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR, admin_member
from tests.bots.channelmanager.test_publishing import channel_sends, drain, setup_post
from tests.bots.channelmanager.test_publishing_ui import feed, new_draft
from tests.conftest import callback_update, message_update


@pytest.fixture(autouse=True)
def instant_budgets(monkeypatch):
    async def immediate(*args):
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", immediate)


async def click(chm, dp, action, resource="0", generation=0, actor=OPERATOR):
    await feed(chm, dp, callback_update(AdvancedCb(a=action, x=str(resource), g=generation, u=OPERATOR).pack(), user_id=actor))


async def test_advanced_markdown_editor_preserves_entities(chm, dp):
    post = await new_draft(chm, dp)
    await click(chm, dp, "md2", post.id, post.generation)
    await feed(chm, dp, message_update("*مرحبا 👋* __world__"))
    view = await chm.extras["posts"].view(post.id, OPERATOR)
    assert view.spec.body.text == "مرحبا 👋 world" and {e.type for e in view.spec.body.entities} == {"bold", "underline"}


async def test_recurrence_preview_requires_actor_bound_confirmation_and_shared_edit(chm, dp, api):
    post = await new_draft(chm, dp)
    await click(chm, dp, "repeat", post.id, post.generation)
    point = (utcnow() + timedelta(hours=2)).replace(second=0, microsecond=0)
    await feed(chm, dp, message_update(f"anchor={point.isoformat()}\nevery=2h\nreplace=yes"))
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(Recurrence)) == 0
    await click(chm, dp, "seriesok", post.id, post.generation, actor=77)
    assert api.calls("AnswerCallbackQuery")[-1].show_alert
    await click(chm, dp, "seriesok", post.id, post.generation)
    async with chm.sm() as session:
        series = await session.scalar(select(Recurrence))
    assert series is not None and series.replace_previous
    view = await chm.extras["posts"].view(post.id, OPERATOR)
    await feed(chm, dp, callback_update(PostCb(a="body", p=post.id, g=view.post.generation, u=OPERATOR).pack()))
    await feed(chm, dp, message_update("Shared replacement"))
    assert (await chm.extras["posts"].view(post.id, OPERATOR)).post.version == 1
    await feed(chm, dp, callback_update(PostCb(a="apply", p=post.id, g=view.post.generation, u=OPERATOR).pack()))
    assert (await chm.extras["posts"].view(post.id, OPERATOR)).spec.body.text == "Shared replacement"
    series = await chm.extras["recurring"].get(series.id, OPERATOR)
    await click(chm, dp, "pause", series.id, series.generation)
    assert (await chm.extras["recurring"].get(series.id, OPERATOR)).status == "paused"


async def test_multipost_per_item_collection_and_confirmed_publication(chm, dp):
    channel = await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    await feed(chm, dp, message_update("/multipost"))
    await click(chm, dp, "newbatch", CHANNEL_ID, channel.generation)
    async with chm.sm() as session:
        batch = await session.scalar(select(Batch))
    await click(chm, dp, "bm", batch.id, batch.generation)
    batch = await chm.extras["batches"].get(batch.id, OPERATOR)
    await click(chm, dp, "rm", batch.id, batch.generation)
    batch = await chm.extras["batches"].get(batch.id, OPERATOR)
    assert batch.buttons_mode == batch.reactions_mode == "per_item"
    await click(chm, dp, "collect", batch.id, batch.generation)
    await feed(chm, dp, message_update("One collected post"))
    await feed(chm, dp, message_update("Website - https://example.com"))
    await feed(chm, dp, message_update("👍 | 👎"))
    batch = await chm.extras["batches"].get(batch.id, OPERATOR)
    item = (await chm.extras["batches"].items(batch.id, OPERATOR))[0]
    view = await chm.extras["posts"].view(item.post_id, OPERATOR)
    assert view.spec.reactions == ["👍", "👎"] and view.spec.buttons[0][0].url == "https://example.com"
    await click(chm, dp, "batchok", batch.id, batch.generation)
    assert (await chm.extras["posts"].view(item.post_id, OPERATOR)).state == "draft"
    await click(chm, dp, "batchnow", batch.id, batch.generation)
    await click(chm, dp, "batchok", batch.id, batch.generation)
    await drain(chm)
    assert (await chm.extras["posts"].view(item.post_id, OPERATOR)).state == "sent"


@pytest.mark.parametrize("from_now", [False, True])
async def test_calendar_creation_and_batch_slot_confirmation(chm, dp, from_now):
    channel = await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    await click(chm, dp, "newcal", CHANNEL_ID, channel.generation)
    await feed(chm, dp, message_update("Weekly\nMon 09:00\nWed 16:30"))
    async with chm.sm() as session:
        calendar = await session.scalar(select(Calendar))
    assert calendar.name == "Weekly" and len(calendar.slots) == 2
    batch = await chm.extras["batches"].create(CHANNEL_ID, OPERATOR)
    await chm.extras["batches"].add(batch.id, OPERATOR, batch.generation, PostSpec(body=TextBody(text="Planned")), "ui")
    batch = await chm.extras["batches"].get(batch.id, OPERATOR)
    await click(chm, dp, "batchcal", batch.id, batch.generation)
    await click(chm, dp, "pickcal", calendar.id, calendar.generation)
    if from_now:
        await click(chm, dp, "calnow", calendar.id, calendar.generation)
    else:
        await feed(chm, dp, message_update((utcnow() + timedelta(hours=1)).isoformat()))
    await click(chm, dp, "batchok", batch.id, batch.generation)
    assert (await chm.extras["batches"].get(batch.id, OPERATOR)).status == "queued"


async def test_saved_set_ui_and_default_reaction_snapshot(chm, dp):
    post = await new_draft(chm, dp)
    await feed(chm, dp, message_update("/presets"))
    await click(chm, dp, "newbuttons")
    await feed(chm, dp, message_update("Quick links\nHelp | alert | Some help"))
    async with chm.sm() as session:
        preset = await session.scalar(select(Preset))
    await click(chm, dp, "sets", post.id, post.generation)
    await click(chm, dp, "apply", preset.id, preset.generation)
    assert (await chm.extras["posts"].view(post.id, OPERATOR)).spec.buttons[0][0].kind == "alert"
    channel = await chm.extras["channelmanager"].get(CHANNEL_ID)
    await click(chm, dp, "defaults", CHANNEL_ID, channel.generation)
    await feed(chm, dp, message_update("👍 | 👎"))
    next_post = await new_draft(chm, dp, "With defaults")
    await chm.extras["presets"].set_reactions(CHANNEL_ID, OPERATOR, ["New"])
    assert (await chm.extras["posts"].view(next_post.id, OPERATOR)).spec.reactions == ["👍", "👎"]


async def public_click(chm, dp, data, target, *, wrong_chat=False):
    event = callback_update(data, user_id=77)
    message = event.callback_query.message.model_copy(update={"chat": Chat(id=CHANNEL_ID if not wrong_chat else CHANNEL_ID - 1, type="channel"),
        "message_id": target.message_id})
    query = event.callback_query.model_copy(update={"message": message})
    await feed(chm, dp, event.model_copy(update={"callback_query": query}))


async def test_public_callbacks_are_destination_bound_and_membership_is_live(chm, dp, api):
    buttons = parse_buttons(f"Info | popup | Hello\nMembers | member | {CHANNEL_ID} | Welcome | Please join")
    post = await setup_post(chm, api, PostSpec(body=TextBody(text="Public"), buttons=buttons))
    await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    target = (await chm.extras["posts"].view(post.id, OPERATOR)).deliveries[0]
    data = channel_sends(api)[0].reply_markup.inline_keyboard[0][0].callback_data
    await public_click(chm, dp, data, target, wrong_chat=True)
    assert "unavailable" in api.calls("AnswerCallbackQuery")[-1].text
    await public_click(chm, dp, data, target)
    assert api.calls("AnswerCallbackQuery")[-1].text == "Hello"
    member_data = channel_sends(api)[0].reply_markup.inline_keyboard[1][0].callback_data
    api.responses["GetChatMember"] = lambda method: admin_member(method.user_id) if method.user_id != 77 else ChatMemberLeft(
        user=User(id=77, is_bot=False, first_name="Visitor"))
    await public_click(chm, dp, member_data, target)
    assert api.calls("AnswerCallbackQuery")[-1].text == "Please join"
    api.responses["GetChatMember"] = lambda method: admin_member(method.user_id)
    await public_click(chm, dp, member_data, target)
    assert api.calls("AnswerCallbackQuery")[-1].text == "Welcome"


async def test_public_vote_callback_counts_and_closed_response(chm, dp, api):
    post = await setup_post(chm, api, PostSpec(body=TextBody(text="Vote"), reactions=["A", "B"]))
    post = await chm.extras["posts"].publish(post.id, OPERATOR, post.generation)
    await drain(chm)
    target = (await chm.extras["posts"].view(post.id, OPERATOR)).deliveries[0]
    data = channel_sends(api)[0].reply_markup.inline_keyboard[0][0].callback_data
    await public_click(chm, dp, data, target)
    await public_click(chm, dp, data, target)
    async with chm.sm() as session:
        assert await session.scalar(select(func.count()).select_from(Vote)) == 1
    await interactions.close(chm, post.id, OPERATOR, post.generation)
    await public_click(chm, dp, data, target)
    assert api.calls("AnswerCallbackQuery")[-1].text == "Voting is closed."


async def test_leaving_batch_input_does_not_append_unrelated_text(chm, dp):
    await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    batch = await chm.extras["batches"].create(CHANNEL_ID, OPERATOR)
    await click(chm, dp, "collect", batch.id, batch.generation)
    await feed(chm, dp, message_update("/advanced"))
    await feed(chm, dp, message_update("unrelated"))
    assert await chm.extras["batches"].items(batch.id, OPERATOR) == []


def test_advanced_callback_bytes_fit_telegram_limit():
    assert len(AdvancedCb(a="cancelbatch", x="a" * 16, g=2147483647, u=4503599627370495).pack().encode()) <= 64


async def test_shared_batch_flags_and_deletion_timer_apply_to_new_items(chm, dp):
    await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    svc = chm.extras["batches"]
    batch = await svc.create(CHANNEL_ID, OPERATOR)
    await click(chm, dp, "bf0", batch.id, batch.generation)
    batch = await svc.get(batch.id, OPERATOR)
    await click(chm, dp, "bttl", batch.id, batch.generation)
    await feed(chm, dp, message_update("2h"))
    batch = await svc.get(batch.id, OPERATOR)
    post = await svc.add(batch.id, OPERATOR, batch.generation, PostSpec(body=TextBody(text="New defaults")), "flags")
    spec = (await chm.extras["posts"].view(post.id, OPERATOR)).spec
    assert spec.notifications is False and spec.delete_after_seconds == 7200
