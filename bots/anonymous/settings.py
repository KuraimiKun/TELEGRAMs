"""Runtime settings of the anonymous inbox (editable in /admin → Settings)."""

from __future__ import annotations

from core.sdk.module import BaseBotSettings


class AnonSettings(BaseBotSettings):
    # Messages a user may *send* per day.
    free_daily_messages: int = 20
    vip_daily_messages: int = 300
    allow_media: bool = True
    # Screen messages with the fast AI model and refuse abusive ones (needs an AI provider).
    ai_filter: bool = False
    # VIP "💡 Hint" about an anonymous sender's writing style (AI when available, metadata otherwise).
    hints_enabled: bool = True
    daily_prompt_enabled: bool = True
    daily_prompt_hour_utc: int = 17

    @classmethod
    def setting_groups(cls) -> dict[str, list[str]]:
        groups = super().setting_groups()
        groups["inbox"] = [
            "free_daily_messages",
            "vip_daily_messages",
            "allow_media",
            "ai_filter",
            "hints_enabled",
            "daily_prompt_enabled",
            "daily_prompt_hour_utc",
        ]
        return groups
