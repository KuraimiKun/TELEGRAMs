"""Review regressions for Telegram bounds, source shape errors and basket fencing."""

import hashlib
import json
from html.parser import HTMLParser

import pymupdf as fitz
import pytest
from aiogram.types import InlineQuery, Update

from bots.doctools.citations import (
    Author,
    CitationError,
    CitationService,
    Reference,
    bounded_citation,
    check_url,
    crossref_reference,
    format_citations,
    openlibrary_reference,
    page_reference,
)
from bots.doctools.handlers import DtCb
from bots.doctools.module import DocToolsBot
from bots.doctools.operations import process
from core.middlewares.throttling import ThrottlingMiddleware
from core.runtime.dispatcher import build_dispatcher
from tests.bots.doctools.test_citations import CROSSREF
from tests.bots.doctools.test_handlers import pdf_update
from tests.conftest import build_test_ctx, callback_update, message_update, tg_user


@pytest.fixture(autouse=True)
def no_throttle(monkeypatch):
    async def passthrough(self, handler, event, data):
        return await handler(event, data)
    monkeypatch.setattr(ThrottlingMiddleware, "__call__", passthrough)


@pytest.fixture
async def doc_ctx(sm, redis, api, tmp_path):
    return await build_test_ctx(DocToolsBot(), sm, redis, api, tmp_path)


@pytest.mark.parametrize("data", [[], {"message": []}, {"message": {"title": []}}])
def test_bad_crossref_shapes_have_controlled_error(data):
    with pytest.raises(CitationError):
        crossref_reference(data)


def test_partial_metadata_retains_title_and_skips_invalid_records():
    ref = crossref_reference({"message": {"title": "Actual full title", "published": "unknown",
                              "issued": {"date-parts": ["malformed"]}, "author": [None, "bad", {"family": "Valid"}]}})
    assert ref.title == "Actual full title" and ref.year == "n.d."
    assert ref.authors == [Author("Valid")]
    book = openlibrary_reference({"ISBN:9780140328721": {"title": "Book", "authors": [None],
                                  "publishers": ["bad", {"name": "Publisher"}]}}, "9780140328721")
    assert book.authors == [] and book.publisher == "Publisher"


def test_no_author_webpage_puts_title_before_date_in_apa_and_harvard():
    ref = Reference(title="Useful study page", year="2026", container="Example University",
                    url="https://example.org/study", kind="web")
    citations = format_citations(ref)
    assert citations["APA"].startswith("<i>Useful study page</i>. (2026). Example University.")
    assert citations["Harvard"].startswith("<i>Useful study page</i> (2026).")
    assert "<i>Example University</i>" not in citations["APA"]


@pytest.mark.parametrize("url", ["https://[broken", "https://example.org:broken"])
def test_malformed_urls_have_controlled_error(url):
    with pytest.raises(CitationError):
        check_url(url)


def test_malformed_html_and_invalid_encoding_are_controlled():
    with pytest.raises(CitationError):
        page_reference(b"<![bogus]><title>Study</title>", "https://example.org")
    assert page_reference(b"<title>Study \xff</title>", "https://example.org").title.startswith("Study")


@pytest.mark.parametrize("declaration", ["bogus", "BOGUS", "unexpected"])
def test_unsupported_marked_declaration_does_not_produce_a_reference(declaration):
    value = f'<![{declaration}]><meta name="citation_title" content="Valid metadata">'.encode()
    with pytest.raises(CitationError, match="invalid page metadata"):
        page_reference(value, "https://example.org")


@pytest.mark.parametrize("prefix", ["<!DOCTYPE html>", "<!-- <![bogus]> -->", "<![if IE]><![endif]>"])
def test_ordinary_html_declarations_comments_and_legacy_conditionals_remain_readable(prefix):
    value = (prefix + "<title>Study &amp; research</title>").encode()
    assert page_reference(value, "https://example.org").title == "Study & research"


async def test_corrupt_citation_cache_is_discarded_and_refetched(doc_ctx):
    value = "10.1038/nphys1170"
    key = doc_ctx.keys("dt", "citation", hashlib.sha256(f"doi:{value}".encode()).hexdigest())
    await doc_ctx.redis.set(key, '{"authors": [null]}')

    async def fetch(url):
        return json.dumps(CROSSREF).encode()

    ref = await CitationService(doc_ctx, fetch=fetch).lookup(value)
    assert ref.title == "The rise of quantum technology"
    assert json.loads(await doc_ctx.redis.get(key))["authors"][0]["family"] == "O'Brien"


async def test_bad_citation_json_returns_localized_error_and_inline_help(doc_ctx, api):
    async def fetch(url):
        return b"[]"

    doc_ctx.extras["citations"].fetch = fetch
    dp = build_dispatcher(doc_ctx)
    await dp.feed_update(doc_ctx.bot, message_update("/cite 10.1038/nphys1170"))
    assert "couldn't retrieve" in api.calls("SendMessage")[-1].text
    query = InlineQuery(id="bad-inline", from_user=tg_user(), query="cite invalid", offset="")
    await dp.feed_update(doc_ctx.bot, Update(update_id=900, inline_query=query))
    answer = api.calls("AnswerInlineQuery")[-1]
    assert answer.results == [] and answer.button.start_parameter == "cite"


async def test_long_escaped_citations_fit_inline_and_chat_exports_text(doc_ctx, api):
    ref = Reference(title="<&" * 200, authors=[Author("<&" * 30, "<&" * 20) for _ in range(20)],
                    container="<&" * 100, url="https://example.org/" + "<&" * 400)
    styles = format_citations(ref)
    assert len(styles["Chicago"]) > 4096
    for text in styles.values():
        clipped = bounded_citation(text)
        assert len(clipped) <= 3800
        HTMLParser(convert_charrefs=True).feed(clipped)
        assert not clipped.endswith(("&", "&a", "&am", "&amp", "<i"))

    async def lookup(value):
        return ref

    doc_ctx.extras["citations"].lookup = lookup
    dp = build_dispatcher(doc_ctx)
    await dp.feed_update(doc_ctx.bot, message_update("/cite 10.1234/test"))
    assert api.calls("SendDocument")
    query = InlineQuery(id="long-inline", from_user=tg_user(), query="cite 10.1234/test", offset="")
    await dp.feed_update(doc_ctx.bot, Update(update_id=901, inline_query=query))
    assert all(len(result.input_message_content.message_text) <= 4096
               for result in api.calls("AnswerInlineQuery")[-1].results)


async def test_basket_revision_rejects_same_second_and_pre_append_callbacks(doc_ctx, api, monkeypatch):
    monkeypatch.setattr("bots.doctools.queue.time.time", lambda: 1000.1)
    dp = build_dispatcher(doc_ctx)
    await dp.feed_update(doc_ctx.bot, pdf_update("first"))
    service = doc_ctx.extras["doctools"]
    first = await service.basket(42, 42)
    old = DtCb(action="count", owner=42, stamp=first.callback_stamp).pack()
    await dp.feed_update(doc_ctx.bot, pdf_update("second"))
    second = await service.basket(42, 42)
    assert second.created_at == first.created_at and second.callback_stamp != first.callback_stamp
    await dp.feed_update(doc_ctx.bot, callback_update(old))
    assert api.calls("AnswerCallbackQuery")[-1].show_alert
    await service.clear_basket(42, 42)
    await dp.feed_update(doc_ctx.bot, pdf_update("new"))
    await dp.feed_update(doc_ctx.bot, callback_update(old))
    assert await doc_ctx.extras["doctools_queue"].pop() is None


@pytest.mark.parametrize("format", ["zip", "album"])
async def test_image_output_selector_queues_format_and_checks_owner(doc_ctx, api, format):
    dp = build_dispatcher(doc_ctx)
    await dp.feed_update(doc_ctx.bot, pdf_update("first"))
    basket = await doc_ctx.extras["doctools"].basket(42, 42)
    await dp.feed_update(doc_ctx.bot, callback_update(DtCb(action="images", owner=42, stamp=basket.callback_stamp).pack()))
    keyboard = api.calls("SendMessage")[-1].reply_markup
    assert len(keyboard.inline_keyboard[0]) == 2
    selected = DtCb(action=f"images_{format}", owner=42, stamp=basket.callback_stamp).pack()
    await dp.feed_update(doc_ctx.bot, callback_update(selected, user_id=77))
    assert api.calls("AnswerCallbackQuery")[-1].show_alert
    assert await doc_ctx.extras["doctools_queue"].pop() is None
    await dp.feed_update(doc_ctx.bot, callback_update(selected))
    job = await doc_ctx.extras["doctools_queue"].pop()
    assert job.operation == "images" and job.options == {"format": format}


def test_album_images_are_bounded_jpegs(tmp_path):
    source = tmp_path / "source.pdf"
    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text((30, 40), "Page text")
        doc.save(source)
    result = process("images", [source], tmp_path, options={"format": "album"})
    assert len(result.files) == 1 and result.files[0].suffix == ".jpg"
    assert result.files[0].stat().st_size < 10 * 1024 * 1024


async def test_help_and_counts_preserve_assignment_whitespace(doc_ctx, api):
    dp = build_dispatcher(doc_ctx)
    for lang in ("en", "ar"):
        await dp.feed_update(doc_ctx.bot, message_update("/help", lang=lang, user_id=42 if lang == "en" else 43))
        assert "test_bot" in api.calls("SendMessage")[-1].text
        assert "{ $" not in api.calls("SendMessage")[-1].text
    text = "first line\n\n  مرحبا  "
    await dp.feed_update(doc_ctx.bot, message_update(text))
    await dp.feed_update(doc_ctx.bot, message_update("/count"))
    job = await doc_ctx.extras["doctools_queue"].pop()
    assert job.assets[0].text == text
