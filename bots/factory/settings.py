"""Bot Factory runtime settings (editable in /admin → Settings)."""

from __future__ import annotations

from core.sdk.module import BaseBotSettings


class FactorySettings(BaseBotSettings):
    free_bots: int = 1
    vip_bots: int = 10
    # Every N invited friends who use the factory unlock one extra bot slot.
    referrals_per_slot: int = 3
    gallery_enabled: bool = True

    @classmethod
    def setting_groups(cls) -> dict[str, list[str]]:
        groups = super().setting_groups()
        groups["factory"] = ["free_bots", "vip_bots", "referrals_per_slot", "gallery_enabled"]
        return groups
