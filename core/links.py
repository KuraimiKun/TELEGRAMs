"""Expiring signed URLs compatible with nginx ``secure_link`` / ``secure_link_md5``.

nginx config (see deploy/nginx/templates/default.conf.template)::

    secure_link $arg_md5,$arg_expires;
    secure_link_md5 "$secure_link_expires$uri <secret>";
"""

from __future__ import annotations

import base64
import hashlib
import time
from urllib.parse import quote, unquote, urlsplit


def sign_path(path: str, secret: str, expires: int) -> str:
    digest = hashlib.md5(f"{expires}{path} {secret}".encode(), usedforsecurity=False).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def signed_url(base_url: str, filename: str, secret: str, ttl_seconds: int, now: float | None = None) -> str:
    """``https://host/dl/bot`` + ``file.mp4`` -> ``https://host/dl/bot/file.mp4?md5=...&expires=...``."""
    url = f"{base_url.rstrip('/')}/{quote(filename)}"
    expires = int((now if now is not None else time.time()) + ttl_seconds)
    # nginx `$uri` is the *decoded* path, so sign that.
    sig = sign_path(unquote(urlsplit(url).path), secret, expires)
    return f"{url}?md5={sig}&expires={expires}"
