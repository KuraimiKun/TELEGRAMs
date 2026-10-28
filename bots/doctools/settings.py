"""Limits editable through the bot's admin settings."""

from pydantic import Field

from core.sdk.module import BaseBotSettings


class DocToolsSettings(BaseBotSettings):
    free_max_mb: int = Field(default=20, ge=1, le=200)
    vip_max_mb: int = Field(default=100, ge=1, le=500)
    free_max_pages: int = Field(default=50, ge=1, le=1000)
    vip_max_pages: int = Field(default=300, ge=1, le=2000)
    free_ai_daily_limit: int = Field(default=3, ge=0, le=1000)
    vip_ai_daily_limit: int = Field(default=30, ge=0, le=1000)
    max_basket_files: int = Field(default=20, ge=1, le=100)
    max_active_jobs: int = Field(default=2, ge=1, le=10)

    @classmethod
    def setting_groups(cls) -> dict[str, list[str]]:
        groups = super().setting_groups()
        groups["documents"] = [
            "free_max_mb", "vip_max_mb", "free_max_pages", "vip_max_pages",
            "free_ai_daily_limit", "vip_ai_daily_limit", "max_basket_files", "max_active_jobs",
        ]
        return groups
