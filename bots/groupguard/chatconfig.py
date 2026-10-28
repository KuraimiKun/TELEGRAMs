"""Per-group configuration, stored as JSON on ``gg_chats.config`` and edited from the settings panel."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

from bots.groupguard.lock_types import CANONICAL_LOCKS, LEGACY_LOCKS
from bots.groupguard.lock_types import LOCK_TYPES as LOCK_TYPES

CaptchaMode = Literal["off", "button", "math", "text", "text2"]
Action = Literal["mute", "kick", "ban"]


class ChatConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    _revision: int = PrivateAttr(default=0)
    _base: dict = PrivateAttr(default_factory=dict)
    lang: str | None = None  # language of the bot's messages in this group (None = platform default)

    welcome: bool = True
    welcome_text: str = ""  # HTML; empty = the localized default
    welcome_content: dict | None = None
    goodbye: bool = False
    goodbye_content: dict | None = None
    clean_welcome: bool = False
    welcome_messages: list[int] = Field(default_factory=list)
    clean_service: bool = True  # delete "X joined / left" service messages
    rules: str = ""
    rules_format: Literal["html", "rose"] = "html"
    private_rules: bool = False
    rules_button: str = ""
    private_notes: bool = False
    action_topic: int | None = Field(default=None, ge=1, le=2147483647)
    credit: bool = True  # "Protected by @bot" under welcomes (VIP admins may hide it)

    captcha: CaptchaMode = "button"
    captcha_enabled: bool = True
    captcha_minutes: int = Field(default=5, ge=1, le=60)
    captcha_text: str = Field(default="", max_length=128)
    captcha_rules: bool = False
    captcha_kick: bool = True
    captcha_kick_seconds: int | None = Field(default=None, ge=300, le=86400)
    captcha_mute_seconds: int | None = Field(default=None, ge=60, le=86400)
    cas: bool = True  # ban accounts listed by the Combot Anti-Spam database on join
    newbie_hours: int = Field(default=24, ge=0, le=168)  # no links from new members for N hours
    ai_spam: bool = False  # screen newcomers' first messages with the fast AI model

    flood_count: int = Field(default=6, ge=0, le=50)  # 0 = off
    flood_seconds: int = Field(default=8, ge=1, le=86400)
    flood_action: Action = "mute"
    flood_consecutive_count: int = Field(default=0, ge=0, le=50)
    flood_duration_seconds: int | None = Field(default=None, ge=60, le=365 * 86400)
    flood_legacy_duration: bool = True
    flood_silent: bool = False
    clear_flood: bool = False
    action_minutes: int = Field(default=60, ge=1, le=60 * 24 * 30)  # mute/ban length for automatic actions
    raid_seconds: int = Field(default=21600, ge=60, le=30 * 86400)
    raid_ban_seconds: int = Field(default=3600, ge=60, le=30 * 86400)
    auto_raid_count: int = Field(default=0, ge=0, le=10000)

    warn_limit: int = Field(default=3, ge=1, le=20)
    warn_action: Action = "ban"
    warn_duration_seconds: int | None = Field(default=None, ge=60, le=365 * 86400)
    warn_legacy_duration: bool = True
    warn_time_seconds: int | None = Field(default=None, ge=1, le=366 * 86400)
    adminerror: bool = True
    anonadmin: bool = False
    reports: bool = True
    antichannelpin: bool = False
    cleanlinked: bool = False
    log_categories: list[str] = Field(default_factory=lambda: ["settings", "admin", "user", "automated", "reports", "other"])

    locks: list[str] = Field(default_factory=list)
    lock_schema_version: int = 1
    lock_policies: dict[str, dict] = Field(default_factory=dict)
    lock_warns: bool = False
    allowlist: list[dict] = Field(default_factory=list)
    blocklist: list[str] = Field(default_factory=list)
    blocklist_warn: bool = False  # also warn (not only delete) on blocklisted words
    blocklist_entries: list[dict] = Field(default_factory=list)
    blocklist_mode: Literal["nothing", "warn", "kick", "ban", "tban", "mute", "tmute"] = "nothing"
    blocklist_duration_seconds: int | None = Field(default=None,ge=60,le=365*86400)
    blocklist_delete: bool = True
    blocklist_reason: str = Field(default="",max_length=256)
    silent_actions_allowed: bool = False
    disabled_commands: list[str] = Field(default_factory=list)
    disabled_delete: bool = False
    disable_admin: bool = False
    command_clean_types: list[str] = Field(default_factory=list)
    bot_clean_types: list[str] = Field(default_factory=list)
    service_clean_types: list[str] | None = None
    bot2bot_mode: Literal["off", "admin", "all"] = "off"
    bot2bot_skip_review: bool = False

    night: bool = False
    night_policy_version: int = Field(default=0, ge=0, le=2147483647)
    night_start: int = Field(default=23, ge=0, le=23)
    night_end: int = Field(default=7, ge=0, le=23)
    tz_offset: int = Field(default=0, ge=-12, le=14)  # hours from UTC for night mode

    log_chat_id: int | None = None

    @model_validator(mode="after")
    def blocklist_contract(self) -> ChatConfig:
        from bots.groupguard.blocklist_types import Entry
        from bots.groupguard.command_metadata import DISABLEABLE
        if (self.blocklist_mode in {"tban", "tmute"}) != (self.blocklist_duration_seconds is not None):
            raise ValueError("blocklist_duration_invalid")
        for entry in self.blocklist_entries:
            Entry.model_validate(entry)
        if not set(self.disabled_commands) <= DISABLEABLE:
            raise ValueError("disabled_command_invalid")
        for selected, known in ((self.command_clean_types, {"admin","user","other"}),
                                (self.bot_clean_types, {"action","filter","note"}),
                                (self.service_clean_types or [], {"join","leave","other","photo","pin","title","videochat"})):
            if not set(selected) <= known:
                raise ValueError("cleanup_type_invalid")
        return self

    @staticmethod
    def normalized_storage(value: dict) -> dict:
        if isinstance(value, dict) and "lock_schema_version" not in value and "voice" in value.get("locks", []):
            # Historical voice blocked both voice messages and video notes; canonical categories are separate.
            value = {**value, "locks": list(dict.fromkeys([*value["locks"], "videonote"])), "lock_schema_version": 1}
        if "blocklist_entries" not in value and value.get("blocklist"):
            value={**value,"blocklist_entries":[dict(key=text,kind="text",pattern=text,reason="",action=None,
                duration_seconds=None,silent=False,legacy=True) for text in value["blocklist"]]}
        if "blocklist_mode" not in value and value.get("blocklist_warn"):
            value={**value,"blocklist_mode":"warn"}
        return value

    @classmethod
    def from_storage(cls, value: dict) -> ChatConfig:
        return cls.model_validate(cls.normalized_storage(value))

    def effective_captcha(self) -> CaptchaMode:
        return self.captcha if self.captcha_enabled and self.welcome else "off"

    def verification_seconds(self) -> int:
        return self.captcha_kick_seconds or self.captcha_minutes * 60

    def effective_warning_duration(self) -> int | None:
        if self.warn_action == "kick":
            return None
        if self.warn_duration_seconds is not None:
            return self.warn_duration_seconds
        return self.action_minutes * 60 if self.warn_legacy_duration and self.warn_action == "mute" else None

    def locked(self, kind: str) -> bool:
        wanted = set(LEGACY_LOCKS.get(kind, (kind,)))
        if "all" in self.locks:
            return bool(wanted & set(CANONICAL_LOCKS))
        return bool(wanted & {canonical for name in self.locks for canonical in LEGACY_LOCKS.get(name, (name,))})
