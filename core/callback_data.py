"""Typed CallbackData factories for core platform features (prefixed with c_)."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class CoreLangCb(CallbackData, prefix="c_lng"):
    code: str


class CoreVipCb(CallbackData, prefix="c_vip"):
    action: str  # info | buy
    plan_id: int = 0


class CoreForceSubCb(CallbackData, prefix="c_fsub"):
    token: str


class CoreGroupToggleCb(CallbackData, prefix="c_grp"):
    chat_id: int


class AdminNavCb(CallbackData, prefix="c_adm"):
    tab: str  # home | stats | users | broadcast | settings | channels | plans | audit | <custom>
    page: int = 1


class AdminUsersCb(CallbackData, prefix="c_aul"):
    kind: str  # new | active | vip | banned
    page: int = 1


class AdminUserCb(CallbackData, prefix="c_ausr"):
    user_id: int
    action: str  # view | ban | ban_skip | unban | grant | revoke | reset | payments | refund | refund_ok
    arg: int = 0  # days for grant, payment id for refund


class AdminPlanCb(CallbackData, prefix="c_apl"):
    action: str  # view | add | edit | toggle | delete
    plan_id: int = 0


class AdminChannelCb(CallbackData, prefix="c_ach"):
    action: str  # view | add | test | toggle | delete
    chat_id: int = 0


class AdminSettingCb(CallbackData, prefix="c_astg"):
    group: str
    idx: int = -1  # index of the key inside the group (keeps callback data short)
    action: str = "view"  # view | toggle | edit


class AdminBroadcastCb(CallbackData, prefix="c_abc"):
    action: str  # target | start | stop | view
    target: str = "all"  # all | free | vip | active7 | lang:<code>
    bid: int = 0
