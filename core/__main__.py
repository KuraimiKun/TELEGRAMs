"""Main CLI entrypoint for the Telegram Bots Platform.

Usage:
    python -m core gateway [--bots <slugs>]
    python -m core scheduler [--bots <slugs>]
    python -m core run <slug> <process_name>
    python -m core dev [--bots <slugs>]
    python -m core bots
    python -m core migrate [--revision <rev>]
    python -m core makemigrations -m "<message>"
    python -m core db-current
    python -m core healthcheck <role>
    python -m core new-bot <slug> [--title <title>]
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import sys

from core.config import BotConfigError, get_platform_config
from core.log import get_logger, setup_logging

log = get_logger("cli")


def cmd_bots() -> None:
    from core.sdk.registry import discover

    try:
        modules = discover(platform=get_platform_config(), include_templates=True)
    except Exception as e:
        print(f"\nError discovering bots: {e}\n", file=sys.stderr)
        sys.exit(1)
    print(f"\nDiscovered {len(modules)} bot module(s):")
    for m in modules:
        print(f"  • {m.slug:18} | Title: {m.title:20} | Table prefix: {m.table_prefix}")
        print(f"    Features: {', '.join(sorted(m.features))}")
        if m.factory_template:
            kind = "standalone + factory template" if m.standalone else "factory template only"
            print(f"    Factory: '{m.factory_template}' ({kind})")
        procs = list(m.processes().keys())
        if procs:
            print(f"    Processes: {', '.join(procs)}")
        jobs = [j.name for j in m.scheduled_jobs()]
        if jobs:
            print(f"    Scheduled jobs: {', '.join(jobs)}")
    print("\nAll bot module contracts validated successfully.\n")


async def cmd_dev(slugs: list[str] | None) -> None:
    """Gateway + scheduler + every bot process in ONE process sharing one set of connections."""
    from core.runtime.app import run_role
    from core.runtime.gateway import serve_gateway
    from core.runtime.process import serve_processes
    from core.runtime.scheduler import serve_scheduler

    async def role(contexts, stop) -> None:
        log.info("starting_dev_mode", bots=[c.slug for c in contexts])
        await asyncio.gather(
            serve_gateway(contexts, stop),
            serve_scheduler(contexts, stop),
            serve_processes(contexts, stop),
        )

    await run_role(role, slugs, role_name="dev")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "healthcheck":
        import time
        from pathlib import Path

        hb_path = Path(f"/tmp/hb-{sys.argv[2]}")
        with contextlib.suppress(Exception):
            if hb_path.exists() and time.time() - float(hb_path.read_text(encoding="utf-8").strip()) < 60:
                sys.exit(0)

    config = get_platform_config()
    setup_logging(level=config.log_level, json=config.log_json)

    parser = argparse.ArgumentParser(description="Multi-Bot Platform CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_ in (
        ("gateway", "Run update gateway (webhook or polling)"),
        ("scheduler", "Run central background scheduler"),
        ("dev", "Run gateway, scheduler and all bot processes in one process (local dev)"),
    ):
        p = sub.add_parser(name, help=help_)
        p.add_argument("--bots", help="Comma-separated list of bot slugs", default=None)

    p_run = sub.add_parser("run", help="Run a named background process for a bot")
    p_run.add_argument("slug", help="Bot slug")
    p_run.add_argument("process", help="Process name (e.g. worker)")

    p_mig = sub.add_parser("migrate", help="Apply database migrations (alembic upgrade)")
    p_mig.add_argument("--revision", default="head")

    p_mk = sub.add_parser("makemigrations", help="Autogenerate a new migration from model changes")
    p_mk.add_argument("-m", "--message", required=True)

    sub.add_parser("db-current", help="Show the current database revision")

    p_hc = sub.add_parser("healthcheck", help="Exit 0 if this container's role heartbeat is fresh")
    p_hc.add_argument("role", help="gateway | scheduler | <slug>-<process>")
    sub.add_parser("bots", help="List and validate discovered bots")

    p_new = sub.add_parser("new-bot", help="Generate a new bot module skeleton")
    p_new.add_argument("slug", help="Slug for the new bot (e.g. quizbot)")
    p_new.add_argument("--title", help="Display title for the bot", default=None)

    args = parser.parse_args()
    slugs = [s.strip() for s in args.bots.split(",") if s.strip()] if getattr(args, "bots", None) else None

    try:
        if args.command == "gateway":
            from core.runtime.gateway import run_gateway

            asyncio.run(run_gateway(slugs=slugs))
        elif args.command == "scheduler":
            from core.runtime.scheduler import run_scheduler

            asyncio.run(run_scheduler(slugs=slugs))
        elif args.command == "run":
            from core.runtime.process import run_process

            asyncio.run(run_process(args.slug, args.process))
        elif args.command == "dev":
            asyncio.run(cmd_dev(slugs))
        elif args.command == "migrate":
            from core.db.migrate import upgrade

            upgrade(revision=args.revision)
        elif args.command == "makemigrations":
            from core.db.migrate import make_migration

            make_migration(args.message)
        elif args.command == "db-current":
            from core.db.migrate import current

            current()
        elif args.command == "healthcheck":
            from core.runtime.app import check_heartbeat

            sys.exit(0 if asyncio.run(check_heartbeat(args.role)) else 1)
        elif args.command == "bots":
            cmd_bots()
        elif args.command == "new-bot":
            from core.scaffold.generator import create_bot_skeleton

            create_bot_skeleton(args.slug, args.title)
    except BotConfigError as e:
        log.error("configuration_error", error=str(e))
        sys.exit(2)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        main()
