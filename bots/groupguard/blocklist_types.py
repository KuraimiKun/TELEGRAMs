"""Validated typed blocklist entries and explicit observed-profile/lookalike grammar."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bots.groupguard.blocklist_matcher import normalize, tokens

KINDS = {
    "text",
    "prefix",
    "exact",
    "lookalike",
    "file",
    "forward",
    "inline",
    "stickerpack",
    "name",
    "username",
}
MODES = {"nothing", "warn", "kick", "ban", "tban", "mute", "tmute"}


class Entry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    key: str = Field(min_length=1)
    kind: str = "text"
    pattern: str = Field(min_length=1)
    reason: str = Field(default="", max_length=256)
    action: str | None = None
    duration_seconds: int | None = Field(default=None, ge=60, le=365 * 86400)
    silent: bool = False
    legacy: bool = False

    @model_validator(mode="after")
    def contract(self):
        if self.kind not in KINDS or (self.action is not None and self.action not in MODES):
            raise ValueError("blocklist_entry_invalid")
        if (self.action in {"tban", "tmute"}) != (self.duration_seconds is not None):
            raise ValueError("blocklist_duration_invalid")
        if self.silent and self.action not in {"kick", "ban", "tban", "mute", "tmute", "warn"}:
            raise ValueError("blocklist_silent_invalid")
        if self.legacy:
            if self.kind != "text" or self.action is not None or self.silent:
                raise ValueError("blocklist_legacy_invalid")
        elif len(self.key) > 256 or len(self.pattern) > 256:
            raise ValueError("blocklist_pattern_invalid")
        elif self.kind in {"text", "prefix", "exact", "lookalike", "name", "username", "file"}:
            tokens(normalize(self.pattern))
        return self


def trigger(key: str, *, reason="", action=None, duration_seconds=None, silent=False) -> Entry:
    kind, colon, pattern = key.partition(":")
    if not colon or kind not in KINDS:
        kind, pattern = "text", key
    return Entry(
        key=key,
        kind=kind,
        pattern=pattern,
        reason=reason,
        action=action,
        duration_seconds=duration_seconds,
        silent=silent,
    )


LOOKALIKE = str.maketrans(
    {
        "а": "a",
        "е": "e",
        "о": "o",
        "р": "p",
        "с": "c",
        "х": "x",
        "у": "y",
        "і": "i",
        "ј": "j",
        "ѕ": "s",
        "α": "a",
        "ο": "o",
        "ρ": "p",
        "ν": "v",
        "ι": "i",
        "κ": "k",
        "τ": "t",
        "ϲ": "c",
        "ꞵ": "b",
    }
)
