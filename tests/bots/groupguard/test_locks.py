"""Typed message evidence and exception boundaries, before Bot API enforcement."""

import pytest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, MessageOriginUser

from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.lock_types import CANONICAL_LOCKS
from bots.groupguard.locks import allow_entry, allowed, detect, policy_arguments, violations
from tests.bots.groupguard.test_groupguard import plain, tg_user


@pytest.mark.parametrize(
    "text,kind",
    [
        ("$USD", "cashtag"),
        ("中文", "cjk"),
        ("Привет", "cyrillic"),
        ("مرحبا", "rtl"),
        ("a@example.org", "email"),
        ("+1 234 567 890", "phone"),
        ("/price arg", "command"),
        ("😀", "emoji"),
        ("😀 👩‍💻", "emojionly"),
        ("a\u0301\u0302\u0303\u0304", "zalgo"),
        ("https://t.me/+private", "invitelink"),
        ("tg://join?invite=private", "invitelink"),
        ("https://t.me/example_bot", "botlink"),
        ("https://example.org", "url"),
    ],
)
def test_text_and_unicode_types(text, kind):
    msg = plain(20, text)
    if kind == "cashtag":
        msg = msg.model_copy(update={"entities": [MessageEntity(type="cashtag", offset=0, length=4)]})
    assert kind in {e.kind for e in detect(msg)}


def test_non_emoji_text_and_normal_arabic_diacritics_are_not_broadly_classified():
    assert "emojionly" not in {e.kind for e in detect(plain(20, "Hello 😀"))}
    assert "zalgo" not in {e.kind for e in detect(plain(20, "السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ اللَّهِ"))}
    assert "zalgo" not in {e.kind for e in detect(plain(20, "café"))}


def test_hidden_entity_urls_and_duplicate_buttons_keep_all_targets():
    text = "😀 click"
    msg = plain(20, text).model_copy(
        update={
            "entities": [MessageEntity(type="text_link", offset=3, length=5, url="https://bad.example/x")],
            "reply_markup": InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="A", url="https://allowed.example"),
                        InlineKeyboardButton(text="A", url="https://allowed.example"),
                        InlineKeyboardButton(text="Bad", url="https://evil.example"),
                    ]
                ]
            ),
        }
    )
    hits = violations(msg, ["url", "button"], [allow_entry("allowed.example")])
    assert {"https://bad.example/x", "https://evil.example"} <= {e.value for e in hits}
    assert all(e.value != "https://allowed.example" for e in hits)


@pytest.mark.parametrize(
    "bad",
    [
        "https://trusted.example.evil.org/docs",
        "https://nottrusted.example/docs",
        "https://trusted.example/docs-evil",
        "https://u:pw@trusted.example/docs",
        "https://[broken",
    ],
)
def test_domain_path_exceptions_do_not_accept_prefix_or_credential_bypasses(bad):
    items = detect(plain(20, bad))
    assert any(e.kind == "url" and not allowed(e, [allow_entry("trusted.example/docs")]) for e in items)


def test_exception_only_exempts_matching_evidence_and_forward_identity():
    msg = plain(20, "https://trusted.example/docs/read https://evil.example").model_copy(
        update={"forward_origin": MessageOriginUser(date=plain(20).date, sender_user=tg_user(99))}
    )
    hits = violations(
        msg,
        ["url", "forward", "forwarduser"],
        [allow_entry("trusted.example/docs"), allow_entry("forward:99")],
    )
    assert [(e.kind, e.value) for e in hits] == [("url", "https://evil.example")]


def test_exact_private_invite_and_all_policy_limits():
    exact = "https://t.me/+private"
    hits = violations(plain(20, exact + " https://t.me/+different"), ["invitelink"], [allow_entry(exact)])
    assert [e.value for e in hits] == ["https://t.me/+different"]
    names, policy = policy_arguments("all ### reason {tban 1h}")
    assert (
        set(names) == set(CANONICAL_LOCKS) and policy.duration_seconds == 3600 and policy.reason == "reason"
    )
    assert "videonote" in ChatConfig.from_storage({"locks": ["voice"]}).locks
    assert "videonote" not in ChatConfig(locks=["voice"]).locks


@pytest.mark.parametrize(
    "raw", ["bogus", "url ### reason {tban}", "url ### {tmute 10s}", "url ### {kick 1h}", "url ### {silent}"]
)
def test_invalid_policy_never_turns_invalid_duration_into_permanent(raw):
    with pytest.raises(ValueError):
        policy_arguments(raw)


@pytest.mark.parametrize('path',['/docs/%2e%2e/admin','/docs/../admin','/docs/%252e%252e/admin','/docs/%25252e%25252e/admin'])
def test_encoded_dot_segments_cannot_bypass_path_exception(path):
    from bots.groupguard.locks import Evidence
    assert not allowed(Evidence('url','https://trusted.example'+path),[allow_entry('trusted.example/docs')])


def test_optional_action_without_reason_separator_is_an_actual_policy():
    names,policy=policy_arguments('url {tban 1h}')
    assert names==['url'] and policy.action=='tban' and policy.duration_seconds==3600 and not policy.reason
