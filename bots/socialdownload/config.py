"""Bot-specific configuration loaded from SOCIALDOWNLOAD_* environment variables."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import NoDecode

from core.config import BaseBotEnv, parse_csv_strs


class SocialDownloadEnv(BaseBotEnv):
    data_dir: Path = Path("./data/socialdownload")
    worker_concurrency: int = 4
    proxies: Annotated[list[str], NoDecode] = Field(default_factory=list)
    pot_provider_url: str | None = None
    direct_link_base_url: str | None = None
    direct_link_ttl_seconds: int = 3600
    cache_ttl_days: int = 30
    # Tell admins (log channel, else admin DMs) when a newer yt-dlp is released.
    ytdlp_update_alerts: bool = True

    _v_proxies = field_validator("proxies", mode="before")(classmethod(lambda cls, v: parse_csv_strs(v)))

    @property
    def downloads_dir(self) -> Path:
        return (self.data_dir / "downloads").resolve()

    @property
    def public_dir(self) -> Path:
        return (self.data_dir / "public").resolve()

    @property
    def cookies_dir(self) -> Path:
        return (self.data_dir / "cookies").resolve()

    @property
    def proxies_file(self) -> Path:
        """Admin-managed proxies (one per line), in addition to SOCIALDOWNLOAD_PROXIES."""
        return (self.data_dir / "cookies" / "proxies.list").resolve()
