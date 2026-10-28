"""Bot-wide runtime settings of Group Guard (per-group options live in each group's settings panel)."""

from __future__ import annotations

from core.sdk.module import BaseBotSettings


class GuardSettings(BaseBotSettings):
    cas_url: str = "https://api.cas.chat/check"
    max_purge: int = 300
    max_blocklist: int = 150
    max_items: int = 150  # notes + filters per group

    @classmethod
    def setting_groups(cls) -> dict[str, list[str]]:
        groups = super().setting_groups()
        groups["guard"] = ["cas_url", "max_purge", "max_blocklist", "max_items"]
        return groups
