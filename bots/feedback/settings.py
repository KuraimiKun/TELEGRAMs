"""Feedback bot settings — the owner edits them in /admin → Settings."""

from __future__ import annotations

from core.sdk.module import BaseBotSettings


class FeedbackSettings(BaseBotSettings):
    greeting: str = ""  # shown on /start; empty = default text
    away: bool = False
    away_text: str = ""  # auto-reply while away; empty = default text
    show_profile: bool = True  # include the sender's name/@username in the inbox header
    # Where messages arrive: the owner's private chat (0) or a group set with /setinbox.
    inbox_chat_id: int = 0

    @classmethod
    def setting_groups(cls) -> dict[str, list[str]]:
        return {
            "inbox": ["greeting", "away", "away_text", "show_profile", "inbox_chat_id"],
            "features": ["maintenance"],
        }
