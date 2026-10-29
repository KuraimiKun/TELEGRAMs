"""Offline release preflight. It never calls Telegram or loads .env implicitly."""

import argparse
import importlib.metadata
import json
import re
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
PIN = re.compile(r"^[a-zA-Z0-9./:_-]+@sha256:[a-f0-9]{64}$")


def configuration(values):
    """Return fixed messages, never configuration values or secrets."""
    token = bool(values.get("CHANNELMANAGER_TOKEN"))
    image = values.get("TELEGRAM_BOT_API_IMAGE") or ""
    return [
        {"check": "bot_token", "status": "configured" if token else "deferred",
            "detail": "Configured; native identity still requires canary verification." if token else "Not created; live canary is deferred."},
        {"check": "bot_api_image", "status": "configured" if PIN.fullmatch(image) else "deferred",
            "detail": "Immutable digest configured; verify it in the container canary." if PIN.fullmatch(image) else "Configure a canary-verified image digest before deployment."},
        {"check": "factory_key", "status": "configured" if values.get("FACTORY_SECRET_KEY") else "deferred",
            "detail": "Retain the factory encryption key with protected backups." if values.get("FACTORY_SECRET_KEY") else "Branded bots require a persistent factory encryption key."},
    ]


def report(values=None):
    cfg = Config()
    cfg.set_main_option("script_location", str(ROOT / "core/db/migrations"))
    heads = ScriptDirectory.from_config(cfg).get_heads()
    checks = [{"check": "schema", "status": "pass" if heads == ["0024_chm_growth"] else "fail",
        "detail": "Single expected migration head." if heads == ["0024_chm_growth"] else "Review migration heads."}]
    for package in ["aiogram", "SQLAlchemy", "alembic", "redis"]:
        try:
            version = importlib.metadata.version(package)
            checks.append({"check": package, "status": "pass", "detail": version})
        except importlib.metadata.PackageNotFoundError:
            checks.append({"check": package, "status": "fail", "detail": "Dependency is missing."})
    checks.extend(configuration(values or {}))
    return {"mode": "offline", "python": sys.version.split()[0], "migration_heads": heads, "checks": checks,
        "live_canary": "deferred", "deployment_ready": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, help="Explicit optional config file; values are never printed.")
    parser.add_argument("--require-deployment", action="store_true", help="Exit nonzero until native canary evidence exists.")
    args = parser.parse_args()
    values = dotenv_values(args.env_file, interpolate=False) if args.env_file else {}
    result = report(values)
    print(json.dumps(result, indent=2))
    return 1 if args.require_deployment or any(c["status"] == "fail" for c in result["checks"]) else 0


if __name__ == "__main__":
    sys.exit(main())
