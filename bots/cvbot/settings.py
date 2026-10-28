from pydantic import Field

from core.sdk.module import BaseBotSettings


class CVSettings(BaseBotSettings):
    groups_enabled: bool = False
    free_analyses_per_day: int = Field(default=1, ge=1, le=20)
    max_file_mb: int = Field(default=10, ge=1, le=50)
    max_pages: int = Field(default=12, ge=1, le=50)
    max_text_chars: int = Field(default=40000, ge=1000, le=100000)
    pro_review_stars: int = Field(default=25, ge=1, le=10000)

    @classmethod
    def setting_groups(cls) -> dict[str, list[str]]:
        return {
            **super().setting_groups(),
            "cv": ["free_analyses_per_day", "max_file_mb", "max_pages", "max_text_chars", "pro_review_stars"],
        }
