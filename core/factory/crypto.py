"""Token encryption at rest and per-bot webhook secrets, both derived from FACTORY_SECRET_KEY."""

from __future__ import annotations

import base64
import hashlib
import hmac

from cryptography.fernet import Fernet, InvalidToken

from core.config import TOKEN_RE, PlatformConfig


class FactoryNotConfigured(RuntimeError):
    def __init__(self) -> None:
        super().__init__("FACTORY_SECRET_KEY is not set: the bot factory is disabled")


def _secret(platform: PlatformConfig) -> bytes:
    if platform.factory_secret_key is None:
        raise FactoryNotConfigured()
    return platform.factory_secret_key.get_secret_value().encode()


def _fernet(platform: PlatformConfig) -> Fernet:
    key = hashlib.sha256(b"factory-token-v1:" + _secret(platform)).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_token(platform: PlatformConfig, token: str) -> str:
    return _fernet(platform).encrypt(token.encode()).decode()


def decrypt_token(platform: PlatformConfig, blob: str, *, expected_bot_id: int | None = None) -> str | None:
    """None when the blob is empty (revoked bot) or was encrypted with another key."""
    if not blob:
        return None
    try:
        token = _fernet(platform).decrypt(blob.encode()).decode()
    except (InvalidToken, UnicodeDecodeError):
        return None
    if expected_bot_id is not None and (
            not TOKEN_RE.fullmatch(token) or token.partition(":")[0] != str(expected_bot_id)):
        return None
    return token


def webhook_secret(platform: PlatformConfig, bot_id: int) -> str:
    """Secret Telegram echoes in X-Telegram-Bot-Api-Secret-Token for the child's webhook (A-Za-z0-9 only)."""
    return hmac.new(_secret(platform), f"webhook:{bot_id}".encode(), hashlib.sha256).hexdigest()[:48]


def verify_webhook(platform: PlatformConfig, bot_id: int, presented: str) -> bool:
    return hmac.compare_digest(webhook_secret(platform, bot_id), presented or "")
