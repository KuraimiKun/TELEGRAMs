"""Validated membership policies and bounded profile filters."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bots.channelmanager.content import ContentError, PostSpec, safe_url, utf16len
from bots.channelmanager.keywords import Expression, any_match

SCRIPTS = {"LATIN", "ARABIC", "CYRILLIC", "GREEK", "HEBREW", "DEVANAGARI", "THAI", "HANGUL", "HIRAGANA", "KATAKANA", "CJK", "OTHER"}
EVENTS = {"request", "approved", "declined", "expired", "joined", "left", "removed", "banned", "unbanned", "filter_rejected", "contact_failed", "cleanup_failed"}
CLEAN_SERVICES = {"new_chat_title", "new_chat_photo", "delete_chat_photo", "pinned_message", "video_chat_started", "video_chat_ended", "video_chat_scheduled"}
MEMBER_KINDS = frozenset(f"member_{kind}" for kind in {"contact", "approve", "decline", "ban", "unban", "welcome", "goodbye", "log", "clean"})
MEMBER_CLEANUP = frozenset({"member_unban", "member_clean"})


class RequiredChat(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chat_id: int = Field(lt=0)
    url: str = Field(max_length=2048)

    @model_validator(mode="after")
    def valid(self):
        safe_url(self.url)
        if not self.url.startswith("https://t.me/"):
            raise ContentError("required_chat")
        return self


class ProfilePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_block: bool = False
    max_per_ten_seconds: int | None = Field(default=None, ge=1, le=10000)
    outcome: Literal["decline", "ban"] = "decline"
    blocked_names: list[str] = Field(default_factory=list, max_length=20)
    blocked_usernames: list[str] = Field(default_factory=list, max_length=20)
    scripts: list[str] = Field(default_factory=list, max_length=12)
    script_mode: Literal["allow", "block"] = "block"
    languages: list[str] = Field(default_factory=list, max_length=20)
    language_mode: Literal["any", "allow", "block"] = "any"
    reject_unknown_language: bool = False

    @model_validator(mode="after")
    def valid(self):
        if not set(self.scripts) <= SCRIPTS or (self.script_mode == "allow" and not self.scripts):
            raise ContentError("profile_filter")
        if self.language_mode != "any" and not self.languages:
            raise ContentError("profile_filter")
        if any(not re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]{2,8})*", lang) for lang in self.languages):
            raise ContentError("profile_filter")
        for term in self.blocked_names + self.blocked_usernames:
            Expression.parse(term)
        return self

    def rejects(self, profile: dict, count: int) -> str | None:
        if self.total_block:
            return "total_block"
        if self.max_per_ten_seconds is not None and count > self.max_per_ten_seconds:
            return "join_rate"
        name = " ".join(str(profile.get(k) or "") for k in ("first_name", "last_name")).strip()
        if any_match(self.blocked_names, name) or any_match(self.blocked_usernames, str(profile.get("username") or "")):
            return "profile_keyword"
        found = set()
        for char in name:
            if unicodedata.category(char).startswith("L"):
                script = unicodedata.name(char, "OTHER").split()[0]
                found.add(script if script in SCRIPTS else "OTHER")
        if (self.script_mode == "allow" and found - set(self.scripts)) or (self.script_mode == "block" and found & set(self.scripts)):
            return "profile_alphabet"
        language = str(profile.get("language_code") or "").lower()
        if not language and self.reject_unknown_language:
            return "profile_language_unknown"
        match = any(language == v or language.split("-")[0] == v for v in self.languages)
        if language and ((self.language_mode == "allow" and not match) or (self.language_mode == "block" and match)):
            return "profile_language"
        return None


class MemberSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    mode: Literal["immediate", "timed", "manual"] = "manual"
    delay_seconds: int = Field(default=60, ge=1, le=86400)
    expires_seconds: int = Field(default=3600, ge=60, le=604800)
    captcha: bool = False
    captcha_attempts: int = Field(default=3, ge=1, le=10)
    required: list[RequiredChat] = Field(default_factory=list, max_length=10)
    invite_threshold: int = Field(default=0, ge=0, le=100)
    invite_timeout_seconds: int | None = Field(default=None, ge=60, le=604800)
    invite_timeout_bypass: bool = False
    profile: ProfilePolicy = Field(default_factory=ProfilePolicy)
    introduction: PostSpec | None = None
    welcome: PostSpec | None = None
    goodbye: PostSpec | None = None
    departure_ban: bool = False
    ban_seconds: int | None = Field(default=None, ge=60, le=31536000)
    linked_group: int | None = Field(default=None, lt=0)
    log_channel: int | None = Field(default=None, lt=0)
    log_language: Literal["en", "ar"] = "en"
    log_events: list[str] = Field(default_factory=lambda: sorted(EVENTS), max_length=12)
    cleanup: list[str] = Field(default_factory=list, max_length=7)

    @model_validator(mode="after")
    def valid(self):
        if not set(self.log_events) <= EVENTS or not set(self.cleanup) <= CLEAN_SERVICES:
            raise ContentError("member_policy")
        if len({r.chat_id for r in self.required}) != len(self.required):
            raise ContentError("required_chat")
        if self.mode == "timed" and self.delay_seconds >= self.expires_seconds:
            raise ContentError("member_delay")
        if self.linked_group and not self.departure_ban:
            raise ContentError("member_policy")
        if self.invite_timeout_bypass and (not self.invite_threshold or self.invite_timeout_seconds is None):
            raise ContentError("member_policy")
        for spec in (self.introduction, self.welcome, self.goodbye):
            if spec and (spec.reactions or spec.pin or spec.reply_message_id or spec.delete_after_seconds or any(
                    b.kind not in {"link", "copy"} for row in spec.buttons for b in row)):
                raise ContentError("member_content")
        if self.introduction and utf16len(self.introduction.render()[0]) > (4096 if self.introduction.kind == "text" else 1024) - 512:
            raise ContentError("member_content")
        return self
