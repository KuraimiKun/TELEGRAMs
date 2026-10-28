"""Error reporting (Sentry) and metrics (Prometheus) shared by every process role.

Metrics are exposed on ``/metrics`` by the gateway's HTTP server and, for the scheduler and bot processes,
by a small dedicated server on ``METRICS_PORT`` (internal network only — nginx never proxies it).
"""

from __future__ import annotations

import contextlib
from typing import Any

from prometheus_client import Counter, Gauge, Histogram, start_http_server

from core.config import PlatformConfig
from core.log import get_logger

log = get_logger(__name__)

# ------------------------------------------------------------------ platform metrics
UPDATES = Counter("tg_updates_total", "Telegram updates processed", ["bot", "type"])
UPDATE_SECONDS = Histogram(
    "tg_update_seconds", "Time to process one update", ["bot"], buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30)
)
HANDLER_ERRORS = Counter("tg_handler_errors_total", "Unhandled errors while processing updates", ["bot"])
PAYMENTS = Counter("payments_total", "Successful Telegram Stars payments", ["bot"])
PAYMENT_STARS = Counter("payment_stars_total", "Stars received", ["bot"])
REFUNDS = Counter("refunds_total", "Refunded payments", ["bot"])
BROADCAST_MESSAGES = Counter("broadcast_messages_total", "Broadcast deliveries", ["bot", "outcome"])
SCHEDULED_RUNS = Counter("scheduled_job_runs_total", "Scheduled job runs", ["bot", "job", "outcome"])

# ------------------------------------------------------------------ download bot metrics
JOBS = Counter("download_jobs_total", "Finished download jobs", ["bot", "platform", "outcome"])
JOB_SECONDS = Histogram(
    "download_job_seconds",
    "End-to-end job duration",
    ["bot", "platform"],
    buckets=(1, 2.5, 5, 10, 20, 40, 60, 120, 300, 600, 1800),
)
QUEUE_DEPTH = Gauge("download_queue_depth", "Jobs waiting or running", ["bot", "state"])
BYTES_DELIVERED = Counter("download_bytes_delivered_total", "Bytes uploaded to Telegram", ["bot"])

# ------------------------------------------------------------------ AI and factory metrics
AI_REQUESTS = Counter("ai_requests_total", "AI requests", ["provider", "bot", "outcome"])
AI_TOKENS = Counter("ai_tokens_total", "AI tokens used", ["provider", "direction"])
AI_SECONDS = Histogram("ai_request_seconds", "AI request latency", ["provider"], buckets=(1, 2.5, 5, 10, 20, 40, 60, 120))
CHILD_BOTS = Gauge("factory_child_bots_loaded", "Child bots loaded in this process")


def start_metrics_server(port: int) -> None:
    if port <= 0:
        return
    try:
        start_http_server(port)
        log.info("metrics_server_started", port=port)
    except OSError as e:  # e.g. several replicas on one host with host networking
        log.warning("metrics_server_failed", port=port, error=str(e))


def init_sentry(platform: PlatformConfig, role: str) -> None:
    """Initialise Sentry when SENTRY_DSN is set. Errors logged at ERROR level become Sentry events."""
    if not platform.sentry_dsn:
        return
    import sentry_sdk
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=platform.sentry_dsn,
        environment=platform.environment,
        release=platform.release or None,
        traces_sample_rate=0.0,
        send_default_pii=False,
        integrations=[AsyncioIntegration(), LoggingIntegration(event_level=None)],
    )
    sentry_sdk.set_tag("process", role)
    log.info("sentry_enabled", role=role)


def capture(exc: BaseException, **tags: Any) -> None:
    """Report an exception to Sentry (no-op when Sentry is not configured)."""
    with contextlib.suppress(Exception):
        import sentry_sdk

        if not sentry_sdk.get_client().is_active():
            return
        with sentry_sdk.new_scope() as scope:
            for key, value in tags.items():
                if value is not None:
                    scope.set_tag(key, str(value))
            sentry_sdk.capture_exception(exc)
