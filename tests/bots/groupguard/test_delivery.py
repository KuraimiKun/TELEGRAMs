"""Actual Bot API media, flags, menu binding and companion-message behavior."""
import json

import pytest
from aiogram.types import CallbackQuery, User

from bots.groupguard import authz, delivery
from bots.groupguard.formatting import Fillings
from tests.bots.groupguard.test_groupguard import GROUP, MEMBER, gctx
from tests.bots.groupguard.test_phase01a import env

__all__ = ["env", "gctx"]


@pytest.mark.parametrize("media,method", [("photo", "SendPhoto"), ("video", "SendVideo"),
    ("animation", "SendAnimation"), ("document", "SendDocument"), ("audio", "SendAudio"),
    ("voice", "SendVoice"), ("sticker", "SendSticker"), ("video_note", "SendVideoNote")])
async def test_all_attachments_deliver_actual_flags_text_and_bound_menus(env, api, media, method):
    f = Fillings(User(id=MEMBER, first_name="<user>", is_bot=False), GROUP, "Club")
    content = delivery.Content("Body {first} {nonotif}{protect}{rules}", "rose", media, "file-id")
    sent = await delivery.send(env, GROUP, content, f, reply_id=17, thread_id=19)
    assert sent.result.primary_completed and api.calls(method)
    call = api.calls(method)[-1]
    assert call.disable_notification and call.protect_content and call.reply_to_message_id == 17 and call.message_thread_id == 19
    carrier = api.calls("SendMessage")[-1] if media in {"sticker", "video_note"} else call
    assert "&lt;user&gt;" in (carrier.text if media in {"sticker", "video_note"} else carrier.caption)
    keyboard = carrier.reply_markup
    assert keyboard.inline_keyboard[0][0].callback_data.startswith("gg:menu:")
    query = CallbackQuery(id="test", from_user=f.user, chat_instance="x", message=sent.messages[-1])
    assert await authz.bound_message(env, query, target_chat_id=GROUP, kind="content", slot="content")
    raw = await env.redis.get(authz.binding_key(env, sent.messages[-1], slot="content"))
    assert json.loads(json.loads(raw)["data"])


async def test_caption_overflow_preserves_full_text_as_companion(env, api):
    f = Fillings(User(id=MEMBER, first_name="User", is_bot=False), GROUP)
    value = "😀" * 600
    sent = await delivery.send(env, GROUP, delivery.Content(value, "rose", "photo", "file-id"), f)
    assert sent.result.primary_completed and len(sent.messages) == 2
    assert api.calls("SendPhoto")[-1].caption is None and api.calls("SendMessage")[-1].text == value


async def test_media_spoiler_preview_and_invalid_media_flags(env, api):
    f = Fillings(User(id=MEMBER, first_name="User", is_bot=False), GROUP)
    sent = await delivery.send(env, GROUP, delivery.Content("Photo {mediaspoiler}", "rose", "photo", "file"), f)
    assert sent.result.primary_completed and api.calls("SendPhoto")[-1].has_spoiler
    before = len(api.requests)
    invalid = await delivery.send(env, GROUP, delivery.Content("Sticker {mediaspoiler}", "rose", "sticker", "file"), f)
    assert not invalid.result.primary_completed and len(api.requests) == before
    sent = await delivery.send(env, GROUP, delivery.Content("https://example.org {preview}", "rose"), f)
    assert sent.result.primary_completed and not api.calls("SendMessage")[-1].link_preview_options.is_disabled


async def test_media_failure_companion_and_menu_slots_remain_truthful(env, api):
    from aiogram.exceptions import TelegramBadRequest
    from aiogram.methods import SendPhoto
    f = Fillings(User(id=MEMBER, first_name="User", is_bot=False), GROUP)
    api.responses["SendPhoto"] = TelegramBadRequest(method=SendPhoto(chat_id=GROUP, photo="file"), message="invalid")
    sent = await delivery.send(env, GROUP, delivery.Content("Long " * 300 + "{rules}", "rose", "photo", "file"), f)
    assert sent.result.status == "partial" and not sent.result.primary_completed and len(sent.messages) == 1
    msg = sent.messages[0]
    await authz.bind_message(env, msg, target_chat_id=GROUP, owner_id=MEMBER, kind="captcha")
    query = CallbackQuery(id="test", from_user=f.user, chat_instance="x", message=msg)
    assert await authz.bound_message(env, query, target_chat_id=GROUP, kind="content", slot="content")
    assert await authz.bound_message(env, query, target_chat_id=GROUP, kind="captcha")
