"""Typed download errors mapped to i18n keys."""

from __future__ import annotations

import re


class DownloadFailed(Exception):
    """Raised for user-facing failures. `code` maps to the i18n key `error-<code>`."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


class Cancelled(Exception):
    pass


# Order matters: first match wins.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private", re.compile(r"private|only available to (?:followers|registered)|this account is private",
                           re.I)),
    ("login", re.compile(r"login required|sign in to confirm|log in|cookies|authentication|age.?restrict"
                         r"|inappropriate for some users|confirm your age", re.I)),
    ("geo", re.compile(r"geo.?restrict|not available in your country|blocked it in your country|unavailable in your country", re.I)),
    ("live", re.compile(r"live event|is live|premieres in|live stream", re.I)),
    ("too_large", re.compile(r"file is larger than max-filesize|max.?filesize", re.I)),
    ("rate_limited", re.compile(r"429|too many requests|rate.?limit", re.I)),
    ("removed", re.compile(r"removed|deleted|no longer available|does not exist|not found|404|"
                           r"video unavailable|unavailable", re.I)),
    ("no_media", re.compile(r"no video formats|no media|there(?:'s| is) no video|requested format is not "
                            r"available|no video could be found|no video in this|unable to extract video",
                            re.I)),
    ("unsupported", re.compile(r"unsupported url|no suitable extractor", re.I)),
    ("timeout", re.compile(
        r"timed? ?out|connection reset|temporary failure|unable to connect|tunnel connection failed|proxyerror"
        r"|name or service not known|failed to resolve|network is unreachable|connection refused",
        re.I,
    )),
]

# Errors that are worth retrying with a different proxy.
RETRYABLE = frozenset({"rate_limited", "timeout", "login", "unknown"})


def classify_error(message: str) -> str:
    for code, pattern in _PATTERNS:
        if pattern.search(message or ""):
            return code
    return "unknown"
