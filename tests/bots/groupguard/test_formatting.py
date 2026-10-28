"""Observable safe Telegram output, independent of command/editor implementation."""
import pytest
from aiogram.types import MessageEntity, User

from bots.groupguard.formatting import ContentError, Fillings, message_source, parse_controls, render
from tests.bots.groupguard.test_groupguard import ADMIN, group_msg

USER = User(id=20, is_bot=False, first_name="علي <admin>", last_name="*Name*", username="safe_name")
F = Fillings(USER, -100, "Group & club", count=49, rules_label="القواعد")


@pytest.mark.parametrize("raw,expected", [
    ("*bold _italic_* ~gone~ __line__ ||secret||", '<b>bold <i>italic</i></b> <s>gone</s> <u>line</u> <span class="tg-spoiler">secret</span>'),
    ("`<literal>{first}{nonotif}`", "<code>&lt;literal&gt;{first}{nonotif}</code>"),
    (r"\*plain\* \{first}", "*plain* {first}"),
    ("*unterminated <tag>", "*unterminated &lt;tag&gt;"),
    ("> line one\n> line two", "<blockquote>line one\nline two</blockquote>"),
    ("> line one\n> line two||", "<blockquote expandable>line one\nline two</blockquote>"),
    ("[site](https://example.org/?a=1&b=2)", '<a href="https://example.org/?a=1&amp;b=2">site</a>'),
])
def test_rose_styles_quotes_links_and_literal_markup(raw, expected):
    assert render(raw, F).html == expected


def test_fillings_escape_identities_without_parsing_their_markup():
    actual = render("{first} {last} {fullname} {username} {mention} {id} {chatname} {group} {count}", F)
    assert "علي &lt;admin&gt;" in actual.html and "*Name*" in actual.html
    assert "@safe_name" in actual.html and "Group &amp; club" in actual.html
    assert '<a href="tg://user?id=20">' in actual.html and "49" in actual.html
    fallback = render("{username}", Fillings(USER.model_copy(update={"username": None}), -100))
    assert fallback.html.startswith('<a href="tg://user?id=20">')


def test_all_controls_are_metadata_and_code_is_literal():
    raw = "Body {preview}{nonotif}{protect}{mediaspoiler}{rules}{admin}{private}{repeat 1h}"
    actual = render(raw, F)
    assert actual.html == "Body " and actual.controls.repeat_seconds == 3600
    assert actual.controls.preview and actual.controls.nonotif and actual.controls.protect and actual.controls.mediaspoiler
    assert actual.controls.admin and actual.controls.private
    assert actual.buttons[-1].kind == "rules" and actual.buttons[-1].label == "القواعد"
    _, alias = parse_controls("{repeated 1h}")
    assert alias.repeat_seconds == actual.controls.repeat_seconds
    filtered = render("Response {user}{allow_bot}{replytag}{command A helpful response}", F, kind="filter")
    assert filtered.controls.user and filtered.controls.allow_bot and filtered.controls.replytag and filtered.controls.command
    assert filtered.controls.command_description == "A helpful response"
    literal = render("`{admin} %%%` \\{nonotif}", F)
    assert not literal.controls.admin and not literal.controls.nonotif
    assert "{admin}" in literal.html and "%%%" in literal.html and "{nonotif}" in literal.html


def test_url_same_row_and_note_buttons_are_real_targets():
    actual = render("Message [Site](buttonurl://https://example.org) [FAQ](buttonurl://#faq:same)", F)
    assert actual.html == "Message  "
    assert [(b.kind, b.target, b.same_row) for b in actual.buttons] == [("url", "https://example.org", False), ("note", "faq", True)]
    assert not render(r"\[Site](buttonurl://https://example.org)", F).buttons
    assert not render("`[Site](buttonurl://https://example.org)`", F).buttons


def test_random_branches_are_rendered_and_code_does_not_split():
    assert render("*one*%%%_two_", F, alternative=0).html == "<b>one</b>"
    assert render("*one*%%%_two_", F, alternative=1).html == "<i>two</i>"
    assert render("`one%%%two`", F).html == "<code>one%%%two</code>"


def test_legacy_html_is_sanitized_and_balanced_without_losing_entities():
    actual = render('<b>Hello &amp; {first}<i>nested</b><script>literal</script>', F, format="html")
    assert actual.html == '<b>Hello &amp; علي &lt;admin&gt;<i>nested</i></b>literal'
    assert "<script>" not in actual.html


def test_rtl_emoji_utf16_limits_and_rich_entity_slicing():
    assert render("😀" * 2048, F).utf16_length == 4096
    with pytest.raises(ContentError, match="content_long"):
        render("😀" * 2049, F)
    request = group_msg("/save faq 😀 RTL", ADMIN)
    message = request.message.model_copy(update={"entities": [MessageEntity(type="bold", offset=10, length=6)]})
    raw, format = message_source(message, 10)
    assert format == "html" and raw == "<b>😀 RTL</b>"
    assert render(raw, F, format=format).html == raw


@pytest.mark.parametrize("raw", ["[bad](javascript:alert)", "[bad](buttonurl://javascript:alert)",
    "{admin}{user}", "{private}{noprivate}", "{repeat 10s}", "{repeat 1h}{repeated 2h}"])
def test_invalid_urls_and_control_conflicts_have_controlled_errors(raw):
    with pytest.raises(ContentError):
        render(raw, F, kind="filter" if raw == "{admin}{user}" else "note")
