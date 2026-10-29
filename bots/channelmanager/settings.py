"""Live quotas, bounded workers and staged rollout settings."""

from pydantic import Field

from core.sdk.module import BaseBotSettings


class ChannelManagerSettings(BaseBotSettings):
    force_sub_enabled: bool = False
    referral_enabled: bool = False
    groups_enabled: bool = False
    # Preserve existing installations; new canaries explicitly select paused/publishing before launch.
    rollout_stage: str = Field(default="commercial", pattern=r"^(paused|publishing|automation|members|commercial)$")
    max_channels_per_operator: int = Field(default=20, ge=1, le=1000)
    free_max_schedules: int = Field(default=20, ge=0, le=10000)
    max_drafts_per_operator: int = Field(default=100, ge=1, le=10000)
    schedule_lateness_grace_seconds: int = Field(default=300, ge=1, le=86400)
    worker_batch_size: int = Field(default=25, ge=1, le=100)
    max_presets_per_operator: int = Field(default=50, ge=1, le=100)
    max_recurrences_per_operator: int = Field(default=20, ge=1, le=100)
    max_batches_per_operator: int = Field(default=20, ge=1, le=100)
    max_batch_items: int = Field(default=50, ge=1, le=100)
    max_calendars_per_channel: int = Field(default=20, ge=1, le=100)
    recurrence_lateness_grace_seconds: int = Field(default=30, ge=1, le=300)
    max_auto_rules_per_channel: int = Field(default=25, ge=1, le=100)
    max_routes_per_channel: int = Field(default=25, ge=1, le=100)
    album_collection_seconds: int = Field(default=2, ge=1, le=10)

    @classmethod
    def setting_groups(cls) -> dict[str, list[str]]:
        return {
            "features": ["maintenance", "rollout_stage"],
            "limits": ["max_channels_per_operator", "free_max_schedules", "max_drafts_per_operator",
                       "schedule_lateness_grace_seconds", "worker_batch_size", "max_presets_per_operator",
                       "max_recurrences_per_operator", "max_batches_per_operator", "max_batch_items", "max_calendars_per_channel",
                       "recurrence_lateness_grace_seconds", "max_auto_rules_per_channel", "max_routes_per_channel", "album_collection_seconds"],
        }
