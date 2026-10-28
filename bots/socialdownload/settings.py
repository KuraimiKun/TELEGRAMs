"""Runtime settings model for SocialDownload bot."""

from __future__ import annotations

from pydantic import Field

from core.sdk.module import BaseBotSettings


class SocialDownloadSettings(BaseBotSettings):
    # Free tier
    free_daily_limit: int = 10
    free_max_height: int = 720
    free_max_mb: int = 500
    free_playlist_max: int = 5
    free_concurrent: int = 1
    free_max_duration_min: int = 60

    # VIP tier
    vip_daily_limit: int = 500
    vip_max_height: int = 2160
    vip_max_mb: int = 4096
    vip_playlist_max: int = 50
    vip_concurrent: int = 3
    vip_max_duration_min: int = 600

    # Features
    inline_enabled: bool = True
    search_enabled: bool = True
    direct_links_enabled: bool = True
    disabled_platforms: list[str] = Field(default_factory=list)
    # Playlists cost one quota unit per item (otherwise one unit per playlist).
    playlist_charge_per_item: bool = True
    # Allow links to unknown sites ("other") in group chats. Off by default: groups are an abuse vector.
    groups_allow_other_sites: bool = False
    # Queued jobs older than this are dropped (and refunded) instead of delivering stale results.
    queue_max_wait_min: int = 30

    @classmethod
    def setting_groups(cls) -> dict[str, list[str]]:
        return {
            "free": [
                "free_daily_limit",
                "free_max_height",
                "free_max_mb",
                "free_playlist_max",
                "free_concurrent",
                "free_max_duration_min",
            ],
            "vip": [
                "vip_daily_limit",
                "vip_max_height",
                "vip_max_mb",
                "vip_playlist_max",
                "vip_concurrent",
                "vip_max_duration_min",
            ],
            "growth": [
                "force_sub_enabled",
                "sponsor_enabled",
                "sponsor_text",
                "referral_enabled",
                "referral_required",
                "referral_reward_days",
            ],
            "features": [
                "maintenance",
                "groups_enabled",
                "inline_enabled",
                "search_enabled",
                "direct_links_enabled",
                "disabled_platforms",
                "playlist_charge_per_item",
                "groups_allow_other_sites",
                "queue_max_wait_min",
            ],
        }
