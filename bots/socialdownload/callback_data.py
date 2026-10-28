"""Typed CallbackData factories for SocialDownload bot."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData

from core.callback_data import (
    AdminBroadcastCb,
    AdminNavCb,
    AdminSettingCb,
    AdminUserCb,
)
from core.callback_data import (
    CoreForceSubCb as ForceSubCb,
)
from core.callback_data import (
    CoreGroupToggleCb as GroupToggleCb,
)
from core.callback_data import (
    CoreLangCb as LangCb,
)
from core.callback_data import (
    CoreVipCb as VipCb,
)

__all__ = [
    "AdminBroadcastCb",
    "AdminNavCb",
    "AdminSettingCb",
    "AdminUserCb",
    "CancelCb",
    "ForceSubCb",
    "FormatCb",
    "GroupToggleCb",
    "LangCb",
    "PlaylistCb",
    "SettingCb",
    "VipCb",
]


class FormatCb(CallbackData, prefix="fmt"):
    job_id: str
    kind: str  # video | audio
    height: int  # 0 for best/audio, or 2160, 1080, 720, etc.


class PlaylistCb(CallbackData, prefix="pl"):
    job_id: str
    kind: str  # video | audio
    count: int  # number of items to download


class CancelCb(CallbackData, prefix="cnl"):
    job_id: str


class SettingCb(CallbackData, prefix="stg"):
    action: str  # menu | set_q | set_aud | toggle_cap
    value: str = ""
