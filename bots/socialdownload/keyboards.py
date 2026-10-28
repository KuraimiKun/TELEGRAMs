"""Inline keyboard builders."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bots.socialdownload.callback_data import (
    CancelCb,
    FormatCb,
    PlaylistCb,
    SettingCb,
    VipCb,
)
from bots.socialdownload.engine.limits import TierPolicy
from bots.socialdownload.engine.ytdl import MediaInfo
from core.i18n import Translate


def start_kb(t: Translate, bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("btn-vip"), callback_data=VipCb(action="info").pack()),
        InlineKeyboardButton(text=t("btn-profile"), callback_data="nav:profile"),
    )
    builder.row(
        InlineKeyboardButton(text=t("btn-settings"), callback_data=SettingCb(action="menu").pack()),
        InlineKeyboardButton(text=t("btn-lang"), callback_data="nav:lang"),
    )
    builder.row(
        InlineKeyboardButton(text=t("btn-help"), callback_data="nav:help"),
        InlineKeyboardButton(text=t("btn-referral"), callback_data="nav:referral"),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn-add-group"),
            url=f"https://t.me/{bot_username}?startgroup=true",
        )
    )
    return builder.as_markup()


def format_picker_kb(
    info: MediaInfo,
    job_id: str,
    policy: TierPolicy,
    audio_format: str,
    t: Translate,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Audio button
    audio_label = t("btn-audio", format=audio_format.upper())
    if info.audio_size:
        audio_label += f" (~{info.audio_size // (1024 * 1024)}MB)"
    builder.row(
        InlineKeyboardButton(
            text=audio_label,
            callback_data=FormatCb(job_id=job_id, kind="audio", height=0).pack(),
        )
    )

    # Video resolutions
    rows: list[InlineKeyboardButton] = []
    # Always provide 'Best' button
    best_allowed = policy.max_height
    builder.row(
        InlineKeyboardButton(
            text=t("btn-best"),
            callback_data=FormatCb(job_id=job_id, kind="video", height=best_allowed).pack(),
        )
    )

    for h in info.heights:
        size_str = ""
        if h in info.sizes:
            size_mb = max(1, info.sizes[h] // (1024 * 1024))
            size_str = f" • ~{size_mb}MB"

        if policy.allows_height(h):
            text = f"🎬 {h}p{size_str}"
            cb = FormatCb(job_id=job_id, kind="video", height=h).pack()
        else:
            text = f"🔒 {h}p (VIP)"
            cb = VipCb(action="info").pack()

        rows.append(InlineKeyboardButton(text=text, callback_data=cb))

    for i in range(0, len(rows), 2):
        builder.row(*rows[i : i + 2])

    builder.row(
        InlineKeyboardButton(
            text=t("btn-cancel"),
            callback_data=CancelCb(job_id=job_id).pack(),
        )
    )
    return builder.as_markup()


def playlist_picker_kb(
    job_id: str,
    allowed_count: int,
    t: Translate,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=t("btn-pl-video", n=allowed_count),
            callback_data=PlaylistCb(job_id=job_id, kind="video", count=allowed_count).pack(),
        ),
        InlineKeyboardButton(
            text=t("btn-pl-audio", n=allowed_count),
            callback_data=PlaylistCb(job_id=job_id, kind="audio", count=allowed_count).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn-cancel"),
            callback_data=CancelCb(job_id=job_id).pack(),
        )
    )
    return builder.as_markup()


def settings_kb(
    prefs: dict,
    t: Translate,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    q = prefs.get("quality", "auto")
    aud = prefs.get("audio", "mp3")
    cap = t("state-on") if prefs.get("caption", True) else t("state-off")

    builder.row(
        InlineKeyboardButton(
            text=f"{t('btn-set-quality')}: {q.upper()}",
            callback_data=SettingCb(action="set_q").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{t('btn-set-audio')}: {aud.upper()}",
            callback_data=SettingCb(action="set_aud").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{t('btn-set-caption')}: {cap}",
            callback_data=SettingCb(action="toggle_cap").pack(),
        )
    )
    builder.row(InlineKeyboardButton(text=t("btn-back"), callback_data="nav:main"))
    return builder.as_markup()


def quality_choice_kb(t: Translate) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("q-auto"), callback_data=SettingCb(action="set_q", value="auto").pack()),
        InlineKeyboardButton(text=t("q-ask"), callback_data=SettingCb(action="set_q", value="ask").pack()),
    )
    builder.row(
        InlineKeyboardButton(text=t("q-best"), callback_data=SettingCb(action="set_q", value="best").pack()),
        InlineKeyboardButton(text=t("q-audio"), callback_data=SettingCb(action="set_q", value="audio").pack()),
    )
    builder.row(InlineKeyboardButton(text=t("btn-back"), callback_data=SettingCb(action="menu").pack()))
    return builder.as_markup()
