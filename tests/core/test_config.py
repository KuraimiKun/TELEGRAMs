"""The documented environment variables must be the ones the code actually reads."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from core.config import BotConfigError, PlatformConfig, load_bot_env
from core.links import sign_path, signed_url
from core.sdk.registry import discover

ROOT = Path(__file__).resolve().parents[2]
TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


def _documented_vars() -> set[str]:
    text = (ROOT / ".env.example").read_text()
    return {m.group(1) for m in re.finditer(r"^#?\s*([A-Z][A-Z0-9_]+)=", text, re.M)}


def test_env_example_documents_real_settings():
    documented = _documented_vars()
    platform_fields = {name.upper() for name in PlatformConfig.model_fields}
    bot_fields = {
        f"{module.slug.upper()}_{name.upper()}" for module in discover() for name in module.env_model.model_fields
    }

    compose_only = {
        "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "REDIS_PASSWORD", "TELEGRAM_API_ID",
        "TELEGRAM_API_HASH", "TELEGRAM_BOT_API_IMAGE", "POT_PROVIDER_IMAGE", "DOMAIN", "LETSENCRYPT_EMAIL",
        "BACKUP_RETENTION_DAYS", "BACKUP_HOUR_UTC", "SOCIALDOWNLOAD_WORKER_REPLICAS",
    }  # fmt: skip
    unknown = documented - platform_fields - bot_fields - compose_only
    assert not unknown, f".env.example documents variables nothing reads: {sorted(unknown)}"
    assert "SOCIALDOWNLOAD_TOKEN" in documented
    assert "SUPER_ADMIN_IDS" in documented


def test_bot_env_reads_prefixed_token(monkeypatch):
    monkeypatch.setenv("SOCIALDOWNLOAD_TOKEN", TOKEN)
    monkeypatch.setenv("SOCIALDOWNLOAD_LOG_CHANNEL_ID", "")  # empty values are ignored, not parse errors
    env = load_bot_env(discover(["socialdownload"])[0].env_model, "socialdownload")
    assert env.token.get_secret_value() == TOKEN
    assert env.log_channel_id is None


def test_bot_env_errors_are_actionable(monkeypatch):
    monkeypatch.delenv("SOCIALDOWNLOAD_TOKEN", raising=False)
    monkeypatch.setenv("SOCIALDOWNLOAD_WEBHOOK_SECRET", "has spaces!")
    with pytest.raises(BotConfigError) as exc:
        load_bot_env(discover(["socialdownload"])[0].env_model, "socialdownload")
    assert "SOCIALDOWNLOAD_WEBHOOK_SECRET" in str(exc.value)


def test_signed_url_matches_nginx_secure_link_formula():
    url = signed_url("https://h.example/dl/sd/", "a b.mp4", "s3cr3t", 60, now=1000)
    assert url.startswith("https://h.example/dl/sd/a%20b.mp4?md5=")
    assert url.endswith("&expires=1060")
    sig = url.split("md5=")[1].split("&")[0]
    assert sig == sign_path("/dl/sd/a b.mp4", "s3cr3t", 1060)
    assert "=" not in sig and "+" not in sig and "/" not in sig
