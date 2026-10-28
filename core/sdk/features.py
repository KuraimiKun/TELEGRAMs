"""Standard feature toggles supported by the platform core."""

from __future__ import annotations

from enum import StrEnum


class Feature(StrEnum):
    ADMIN = "admin"
    LANG = "lang"
    VIP = "vip"
    REFERRAL = "referral"
    FORCE_SUB = "force_sub"
    GROUPS = "groups"
    BROADCAST = "broadcast"
    DAILY_STATS = "daily_stats"
