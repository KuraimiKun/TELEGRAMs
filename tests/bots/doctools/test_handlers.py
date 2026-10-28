"""User-facing baskets, owner isolation, group count and inline citation updates."""

from datetime import UTC, datetime

import pytest
from aiogram.types import Chat, Document, InlineQuery, Message, Update

from bots.doctools.citations import CitationService
from bots.doctools.handlers import DtCb
from bots.doctools.module import DocToolsBot
from core.middlewares.throttling import ThrottlingMiddleware
from core.runtime.dispatcher import build_dispatcher
from tests.bots.doctools.test_citations import CROSSREF
from tests.conftest import build_test_ctx, callback_update, message_update, tg_user


@pytest.fixture(autouse=True)
def no_throttle(monkeypatch):
    async def passthrough(self, handler, event, data):
        return await handler(event, data)
    monkeypatch.setattr(ThrottlingMiddleware, "__call__", passthrough)


@pytest.fixture
async def doc_ctx(sm, redis, api, tmp_path):
    return await build_test_ctx(DocToolsBot(), sm, redis, api, tmp_path)


def pdf_update(file_id, user_id=42):
    return Update(update_id=100, message=Message(message_id=10, date=datetime.now(UTC), chat=Chat(id=user_id, type="private"),
                  from_user=tg_user(user_id), document=Document(file_id=file_id, file_unique_id=file_id,
                                                              file_name=f"{file_id}.pdf", file_size=200)))


async def test_two_pdfs_offer_merge_then_enqueue_in_order(doc_ctx, api):
    dp = build_dispatcher(doc_ctx)
    await dp.feed_update(doc_ctx.bot, pdf_update("first"))
    await dp.feed_update(doc_ctx.bot, pdf_update("second"))
    basket = await doc_ctx.extras["doctools"].basket(42, 42)
    keyboard = api.calls("SendMessage")[-1].reply_markup
    choices = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    cb = DtCb(action="merge", owner=42, stamp=basket.callback_stamp).pack()
    assert cb in choices
    await dp.feed_update(doc_ctx.bot, callback_update(cb))
    job = await doc_ctx.extras["doctools_queue"].pop()
    assert job.operation == "merge"
    assert [asset.file_id for asset in job.assets] == ["first", "second"]
    assert api.calls("SendMessage")[-1].text.startswith("⏳")


async def test_forged_basket_buttons_and_expired_basket_are_rejected(doc_ctx, api):
    dp = build_dispatcher(doc_ctx)
    await dp.feed_update(doc_ctx.bot, pdf_update("first"))
    basket = await doc_ctx.extras["doctools"].basket(42, 42)
    cb = DtCb(action="count", owner=42, stamp=basket.callback_stamp).pack()
    await dp.feed_update(doc_ctx.bot, callback_update(cb, user_id=77))
    assert api.calls("AnswerCallbackQuery")[-1].show_alert
    await doc_ctx.extras["doctools"].clear_basket(42, 42)
    await dp.feed_update(doc_ctx.bot, callback_update(cb))
    assert await doc_ctx.extras["doctools_queue"].pop() is None


async def test_group_count_and_inline_citations(doc_ctx, api):
    import json

    dp = build_dispatcher(doc_ctx)
    await dp.feed_update(doc_ctx.bot, message_update("/count two words", chat_type="supergroup", chat_id=-100))
    job = await doc_ctx.extras["doctools_queue"].pop()
    assert job.chat_id == -100
    assert job.assets[0].text == "two words"

    async def fetch(url):
        return json.dumps(CROSSREF).encode()

    # The router closes over its service, so install the recorded fetch on that instance.
    svc: CitationService = doc_ctx.extras["citations"]
    svc.fetch = fetch
    query = InlineQuery(id="inline", from_user=tg_user(), query="cite 10.1038/nphys1170", offset="")
    await dp.feed_update(doc_ctx.bot, Update(update_id=111, inline_query=query))
    results = api.calls("AnswerInlineQuery")[-1].results
    assert len(results) == 4
    assert results[0].input_message_content.parse_mode == "HTML"


async def test_ai_actions_hidden_when_unconfigured_and_password_is_not_basket_text(doc_ctx, api):
    dp = build_dispatcher(doc_ctx)
    await dp.feed_update(doc_ctx.bot, pdf_update("first"))
    basket = await doc_ctx.extras["doctools"].basket(42, 42)
    choices = [button.callback_data for row in api.calls("SendMessage")[-1].reply_markup.inline_keyboard for button in row]
    assert not any(":summarize:" in choice or ":quiz:" in choice for choice in choices)
    await dp.feed_update(doc_ctx.bot, callback_update(DtCb(action="encrypt", owner=42, stamp=basket.callback_stamp).pack()))
    await dp.feed_update(doc_ctx.bot, message_update("private-password"))
    job = await doc_ctx.extras["doctools_queue"].pop()
    assert job.options == {"password": "private-password"}
    assert len((await doc_ctx.extras["doctools"].basket(42, 42)).assets) == 1
