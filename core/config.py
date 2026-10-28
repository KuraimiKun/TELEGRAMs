"""Configuration.

* :class:`PlatformConfig` — shared infrastructure settings (one per deployment), read from plain env vars.
* :class:`BaseBotEnv` — per-bot settings, read from env vars prefixed with the bot slug
  (``SOCIALDOWNLOAD_TOKEN``, ``SOCIALDOWNLOAD_ADMIN_IDS`` …). Bots subclass it to add their own fields.
"""

from __future__ import annotations

import hashlib
import re
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

MB = 1024 * 1024

WEBHOOK_SECRET_RE = re.compile(r"[A-Za-z0-9_-]{1,256}")
TOKEN_RE = re.compile(r"\d{3,}:[A-Za-z0-9_-]{20,}")

CsvInts = Annotated[list[int], NoDecode]
CsvStrs = Annotated[list[str], NoDecode]


def parse_csv_ints(v: object) -> object:
    if isinstance(v, str):
        return [int(x) for x in v.replace(";", ",").split(",") if x.strip()]
    if isinstance(v, int):
        return [v]
    return v


def parse_csv_strs(v: object) -> object:
    if isinstance(v, str):
        return [x.strip() for x in v.replace(";", ",").replace("\n", ",").split(",") if x.strip()]
    return v


class PlatformConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", env_ignore_empty=True)

    # --- Bots -------------------------------------------------------------
    # Slugs of bot packages under `bots/` to load, e.g. "socialdownload,quizbot".
    enabled_bots: CsvStrs = Field(default_factory=list)
    # Users with admin rights in *every* bot plus access to the cross-bot /platform dashboard.
    super_admin_ids: CsvInts = Field(default_factory=list)

    # --- Infrastructure (shared by all bots) -------------------------------
    database_url: str = "postgresql+asyncpg://bot:bot@localhost:5432/bot"
    redis_url: str = "redis://localhost:6379/0"
    # Optional separate Redis for evictable caches (allkeys-lru). Queues/FSM/locks stay on `redis_url`
    # (noeviction) so a full cache can never drop jobs or user state. Defaults to `redis_url`.
    redis_cache_url: str | None = None

    # Local Bot API server (https://github.com/tdlib/telegram-bot-api). One server serves all bot tokens.
    telegram_api_url: str | None = None
    telegram_api_local_files: bool = True

    # Webhooks: each bot receives updates on {webhook_base_url}/webhook/{slug}. Empty -> long polling.
    webhook_base_url: str | None = None
    web_host: str = "0.0.0.0"
    web_port: int = 8080
    webhook_max_connections: int = Field(default=40, ge=1, le=100)

    # Postgres connection pool per process (gateway, scheduler and every worker each hold one).
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=5, ge=0)

    data_dir: Path = Path("./data")

    # --- Misc -------------------------------------------------------------
    default_lang: str = "en"
    log_level: str = "INFO"
    log_json: bool = False
    sentry_dsn: str | None = None
    environment: str = "production"
    release: str = ""
    # Prometheus endpoint for the scheduler and bot processes (the gateway serves /metrics on WEB_PORT).
    metrics_port: int = 9100
    daily_report_hour_utc: int = Field(default=6, ge=0, le=23)

    # HMAC secret shared with nginx `secure_link` for expiring direct-download URLs (/dl/...).
    direct_link_secret: SecretStr | None = None

    # --- AI (pluggable: Claude by default, OpenAI as an alternative) -------
    ai_provider: str = "anthropic"
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    # Main and cheap/fast model ids; empty uses the provider default.
    ai_model: str = ""
    ai_fast_model: str = ""
    # Platform-wide daily token cap across every bot (0 = unlimited).
    ai_daily_token_budget: int = Field(default=0, ge=0)
    ai_concurrency: int = Field(default=8, ge=1)

    # --- Bot factory (user-created bots) ----------------------------------
    # Encrypts child bot tokens at rest and signs their webhook secrets. Required to run a factory.
    factory_secret_key: SecretStr | None = None
    # Long-polling mode only: max user-created bots polled by one dev process.
    factory_dev_polling_max: int = Field(default=20, ge=0)

    @field_validator("ai_provider")
    @classmethod
    def _check_provider(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"anthropic", "openai"}:
            raise ValueError("AI_PROVIDER must be 'anthropic' or 'openai'")
        return v

    _v_ids = field_validator("super_admin_ids", mode="before")(classmethod(lambda cls, v: parse_csv_ints(v)))
    _v_bots = field_validator("enabled_bots", mode="before")(classmethod(lambda cls, v: parse_csv_strs(v)))

    @property
    def uses_local_api(self) -> bool:
        return bool(self.telegram_api_url)

    @property
    def max_upload_bytes(self) -> int:
        """Telegram upload ceiling: 2000 MB with a local Bot API server, 50 MB with the cloud API."""
        return 2000 * MB if self.uses_local_api else 50 * MB

    def bot_data_dir(self, slug: str) -> Path:
        """Private data directory of one bot: ``<data_dir>/<slug>``."""
        return (self.data_dir / slug).resolve()

    def is_super_admin(self, user_id: int) -> bool:
        return user_id in self.super_admin_ids


class BaseBotEnv(BaseSettings):
    """Per-bot environment. Loaded with ``env_prefix = "<SLUG>_"`` by :func:`load_bot_env`."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", env_ignore_empty=True)

    token: SecretStr
    admin_ids: CsvInts = Field(default_factory=list)
    # Telegram webhook secret (A-Z a-z 0-9 _ -). Derived from the token when empty.
    webhook_secret: str | None = None
    log_channel_id: int | None = None
    support_username: str | None = None

    _v_ids = field_validator("admin_ids", mode="before")(classmethod(lambda cls, v: parse_csv_ints(v)))

    @field_validator("webhook_secret")
    @classmethod
    def _check_secret(cls, v: str | None) -> str | None:
        if v and not WEBHOOK_SECRET_RE.fullmatch(v):
            raise ValueError("webhook_secret must be 1-256 chars of A-Z, a-z, 0-9, '_' or '-' (Telegram requirement)")
        return v or None

    @field_validator("token")
    @classmethod
    def _check_token(cls, v: SecretStr) -> SecretStr:
        if not TOKEN_RE.fullmatch(v.get_secret_value()):
            raise ValueError("token does not look like a Telegram bot token (expected '<digits>:<secret>')")
        return v

    @property
    def effective_webhook_secret(self) -> str:
        if self.webhook_secret:
            return self.webhook_secret
        return hashlib.sha256(self.token.get_secret_value().encode()).hexdigest()[:48]


class BotConfigError(RuntimeError):
    """Raised with a human-readable explanation when a bot's environment is incomplete or invalid."""


def load_bot_env[E: BaseBotEnv](model: type[E], slug: str) -> E:
    """Instantiate a bot env model reading ``<SLUG>_*`` variables, failing with an actionable message."""
    prefix = f"{slug.upper()}_"
    try:
        return model(_env_prefix=prefix)
    except ValidationError as e:
        problems = "; ".join(
            f"{prefix}{'_'.join(str(p) for p in err['loc']).upper()}: {err['msg']}" for err in e.errors()
        )
        raise BotConfigError(f"Invalid configuration for bot '{slug}': {problems}") from None


@lru_cache
def get_platform_config() -> PlatformConfig:
    return PlatformConfig()
