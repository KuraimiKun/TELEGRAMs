"""Runtime settings for Notes & Reminders, editable in /admin -> Settings."""

from __future__ import annotations

from core.sdk.module import BaseBotSettings


class NotesSettings(BaseBotSettings):
    free_max_notes: int = 50
    vip_max_notes: int = 2000
    free_max_reminders: int = 5
    vip_max_reminders: int = 200

    @classmethod
    def setting_groups(cls) -> dict[str, list[str]]:
        groups = super().setting_groups()
        groups["limits"] = ["free_max_notes", "vip_max_notes", "free_max_reminders", "vip_max_reminders"]
        return groups
