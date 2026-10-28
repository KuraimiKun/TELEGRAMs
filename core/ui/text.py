"""Text formatting and presentation utilities for the platform design system."""

from __future__ import annotations

import html
from typing import Any

from core.config import MB


def esc(value: Any) -> str:
    """HTML-escape untrusted text (user names, media titles, admin input) before embedding it in a message."""
    if value is None:
        return ""
    return html.escape(str(value), quote=False)


def title(emoji: str, text: str) -> str:
    """Format a consistent section header, e.g. '📊 <b>Analytics</b>'."""
    return f"{emoji} <b>{text}</b>"


def kv(label: str, value: Any) -> str:
    """Format a consistent key-value bullet line, e.g. '• Total Users: <b>1,234</b>'."""
    return f"• {label}: <b>{value}</b>"


def progress_bar(percent: int, length: int = 10) -> str:
    """Render a visual progress bar (e.g. ▰▰▰▰▰▱▱▱▱▱)."""
    percent = max(0, min(100, percent))
    filled = round(length * percent / 100)
    return "▰" * filled + "▱" * (length - filled)


def human_size(bytes_val: int) -> str:
    """Format bytes into human readable KB / MB / GB."""
    if bytes_val >= 1024 * MB:
        return f"{bytes_val / (1024 * MB):.1f} GB"
    if bytes_val >= MB:
        return f"{bytes_val / MB:.1f} MB"
    return f"{bytes_val / 1024:.0f} KB"


def human_speed(bytes_per_s: float) -> str:
    """Format transfer speed into KB/s or MB/s."""
    if bytes_per_s >= MB:
        return f"{bytes_per_s / MB:.1f} MB/s"
    return f"{bytes_per_s / 1024:.0f} KB/s"


def human_duration(seconds: int) -> str:
    """Format seconds into MM:SS or HH:MM:SS."""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
