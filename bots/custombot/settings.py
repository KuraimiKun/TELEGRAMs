"""Custom bot settings (owner edits them in /admin → Settings)."""

from __future__ import annotations

from core.sdk.module import BaseBotSettings


class CustomSettings(BaseBotSettings):
    default_reply: str = ""  # answer to any unrecognised message; empty = see below
    show_menu_on_unknown: bool = True  # with no default reply, show the home page again

    @classmethod
    def setting_groups(cls) -> dict[str, list[str]]:
        return {"bot": ["default_reply", "show_menu_on_unknown"], "features": ["maintenance"]}
