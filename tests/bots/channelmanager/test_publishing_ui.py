from datetime import timedelta

import pytest
from aiogram.types import Chat, Message, PhotoSize, Update
from sqlalchemy import select

from bots.channelmanager.content import ContentError
from bots.channelmanager.models import Operation, Post
from bots.channelmanager.posts import parse_time
from bots.channelmanager.publishing_ui import PostCb
from core.db.base import utcnow
from tests.bots.channelmanager.conftest import CHANNEL_ID, OPERATOR
from tests.bots.channelmanager.test_publishing import drain
from tests.conftest import callback_update, message_update, tg_user


async def feed(ctx, dp, event):
    for user_id in (OPERATOR, 77):
        await ctx.redis.delete(ctx.keys("throttle", "Message", user_id), ctx.keys("throttle", "CallbackQuery", user_id))
    await dp.feed_update(ctx.bot, event)


async def click(ctx, dp, post, action, *, actor=OPERATOR):
    await feed(ctx, dp, callback_update(PostCb(a=action, p=post.id, g=post.generation, u=OPERATOR).pack(), user_id=actor))


async def new_draft(chm, dp, text="Draft"):
    channel = await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    await feed(chm, dp, message_update("/newpost"))
    await feed(chm, dp, callback_update(PostCb(a="new", p=str(CHANNEL_ID), g=channel.generation, u=OPERATOR).pack()))
    await feed(chm, dp, message_update(text))
    async with chm.sm() as session:
        return await session.scalar(select(Post).order_by(Post.created_at.desc()))


@pytest.fixture(autouse=True)
def instant_budgets(monkeypatch):
    from bots.channelmanager import outbox
    async def reserve(*args):
        return 0
    monkeypatch.setattr(outbox, "reserve_budget", reserve)


async def test_complete_private_composer_confirmation_publish_edit_delete_flow(chm, dp, api):
    post = await new_draft(chm, dp, "👋 مرحبا")
    assert post is not None
    await click(chm, dp, post, "prev")
    assert any(m.chat_id == OPERATOR and m.text == "👋 مرحبا" for m in api.calls("SendMessage"))
    await click(chm, dp, post, "ok")
    async with chm.sm() as session:
        assert not (await session.scalars(select(Operation).where(Operation.kind == "publish"))).all()
    await click(chm, dp, post, "send")
    assert "Confirm publication" in api.calls("EditMessageText")[-1].text
    await click(chm, dp, post, "ok")
    await drain(chm)
    view = await chm.extras["posts"].view(post.id, OPERATOR)
    assert view.state == "sent"
    await click(chm, dp, view.post, "body")
    await feed(chm, dp, message_update("Edited through the menu"))
    await drain(chm)
    view = await chm.extras["posts"].view(post.id, OPERATOR)
    assert view.spec.body.text == "Edited through the menu" and view.deliveries[0].edit_status == "succeeded"
    await click(chm, dp, view.post, "askdel")
    assert "Delete the known" in api.calls("EditMessageText")[-1].text
    await click(chm, dp, view.post, "del")
    await drain(chm)
    assert (await chm.extras["posts"].view(post.id, OPERATOR)).state == "deleted"


async def test_stale_or_other_actor_cannot_confirm_publication(chm, dp, api):
    post = await new_draft(chm, dp)
    await click(chm, dp, post, "send")
    await click(chm, dp, post, "ok", actor=77)
    assert api.calls("AnswerCallbackQuery")[-1].show_alert
    await chm.extras["posts"].targets(post.id, OPERATOR, post.generation, [CHANNEL_ID])
    await click(chm, dp, post, "ok")
    async with chm.sm() as session:
        assert not (await session.scalars(select(Operation).where(Operation.kind == "publish"))).all()


async def test_schedule_then_publish_now_uses_new_generation(chm, dp, api):
    post = await new_draft(chm, dp)
    await click(chm, dp, post, "when")
    await feed(chm, dp, message_update((utcnow() + timedelta(hours=2)).isoformat()))
    await click(chm, dp, post, "ok")
    await drain(chm)
    assert not [m for m in api.calls("SendMessage") if m.chat_id == CHANNEL_ID]
    post = (await chm.extras["posts"].view(post.id, OPERATOR)).post
    await click(chm, dp, post, "send")
    await click(chm, dp, post, "ok")
    await drain(chm)
    assert len([m for m in api.calls("SendMessage") if m.chat_id == CHANNEL_ID]) == 1


async def test_html_editor_and_link_buttons_are_saved(chm, dp):
    post = await new_draft(chm, dp)
    await click(chm, dp, post, "html")
    await feed(chm, dp, message_update("<b>مرحبا</b> &amp; hello"))
    view = await chm.extras["posts"].view(post.id, OPERATOR)
    assert view.spec.body.text == "مرحبا & hello" and view.spec.body.entities[0].type == "bold"
    await click(chm, dp, view.post, "btns")
    await feed(chm, dp, message_update("Website - https://example.com && Docs - https://example.com/docs"))
    view = await chm.extras["posts"].view(post.id, OPERATOR)
    assert len(view.spec.buttons[0]) == 2


async def test_signature_snapshot_and_leaving_input_do_not_change_old_drafts(chm, dp):
    await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    await feed(chm, dp, message_update(f"/signature {CHANNEL_ID}"))
    await feed(chm, dp, message_update("Signature one"))
    post = await new_draft(chm, dp)
    assert (await chm.extras["posts"].view(post.id, OPERATOR)).spec.signature.text == "Signature one"
    await click(chm, dp, post, "body")
    await feed(chm, dp, message_update("/channels"))
    await feed(chm, dp, message_update("Unrelated chat text"))
    assert (await chm.extras["posts"].view(post.id, OPERATOR)).spec.body.text == "Draft"
    await feed(chm, dp, message_update(f"/signature {CHANNEL_ID}"))
    await feed(chm, dp, message_update("Signature two"))
    assert (await chm.extras["posts"].view(post.id, OPERATOR)).spec.signature.text == "Signature one"


async def test_album_rejected_but_single_photo_accepted(chm, dp, api):
    channel = await chm.extras["channelmanager"].connect(CHANNEL_ID, OPERATOR)
    await feed(chm, dp, callback_update(PostCb(a="new", p=str(CHANNEL_ID), g=channel.generation, u=OPERATOR).pack()))
    photo = Message(message_id=901, date=utcnow(), chat=Chat(id=OPERATOR, type="private"), from_user=tg_user(),
        media_group_id="album", photo=[PhotoSize(file_id="photo_ref", file_unique_id="unique", width=20, height=20)], caption="Caption")
    await feed(chm, dp, Update(update_id=902, message=photo))
    async with chm.sm() as session:
        assert not (await session.scalars(select(Post))).all()
    assert "Albums are not supported" in api.calls("SendMessage")[-1].text
    await feed(chm, dp, Update(update_id=903, message=photo.model_copy(update={"media_group_id": None, "message_id": 904})))
    async with chm.sm() as session:
        post = await session.scalar(select(Post))
    assert (await chm.extras["posts"].view(post.id, OPERATOR)).spec.kind == "photo"


@pytest.mark.parametrize("value", ["2027-03-14 02:30", "2027-11-07 01:30"])
def test_invalid_or_ambiguous_dst_local_time_requires_offset(value):
    with pytest.raises(ContentError, match="time"):
        parse_time(value, "America/New_York")


def test_timezone_conversion_explicit_offset_and_callback_size():
    assert parse_time("2027-01-10 15:30", "Asia/Jakarta").hour == 8
    assert parse_time("2027-11-07T01:30-04:00", "America/New_York").hour == 5
    value = PostCb(a="askcancel", p="f" * 16, g=2147483647, u=4503599627370495).pack()
    assert len(value.encode()) <= 64
