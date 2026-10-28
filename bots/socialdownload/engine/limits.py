"""Tier policy engine: turns runtime settings + user tier into concrete limits."""

from __future__ import annotations

from dataclasses import dataclass

from bots.socialdownload.settings import SocialDownloadSettings
from core.config import MB

QUALITY_HEIGHTS = (2160, 1440, 1080, 720, 480, 360)


@dataclass(frozen=True, slots=True)
class TierPolicy:
    is_vip: bool
    daily_limit: int
    max_height: int
    max_bytes: int  # max size we are willing to download
    playlist_max: int
    concurrent: int
    max_duration_s: int
    priority: str  # "high" | "normal"
    direct_links: bool
    show_sponsor: bool
    force_sub: bool

    def allows_height(self, height: int) -> bool:
        return height <= self.max_height


def policy_for(is_vip: bool, s: SocialDownloadSettings) -> TierPolicy:
    if is_vip:
        return TierPolicy(
            is_vip=True,
            daily_limit=s.vip_daily_limit,
            max_height=s.vip_max_height,
            max_bytes=s.vip_max_mb * MB,
            playlist_max=s.vip_playlist_max,
            concurrent=max(1, s.vip_concurrent),
            max_duration_s=s.vip_max_duration_min * 60,
            priority="high",
            direct_links=s.direct_links_enabled,
            show_sponsor=False,
            force_sub=False,
        )
    return TierPolicy(
        is_vip=False,
        daily_limit=s.free_daily_limit,
        max_height=s.free_max_height,
        max_bytes=s.free_max_mb * MB,
        playlist_max=s.free_playlist_max,
        concurrent=max(1, s.free_concurrent),
        max_duration_s=s.free_max_duration_min * 60,
        priority="normal",
        direct_links=False,
        show_sponsor=s.sponsor_enabled and bool(s.sponsor_text.strip()),
        force_sub=s.force_sub_enabled,
    )
