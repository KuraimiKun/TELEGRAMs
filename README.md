# Telegram Multi-Bot Platform

Run many Telegram bots on one server — one Postgres, one Redis, one local Bot API server, one webhook
gateway — with a shared, production-grade core: users and memberships, Telegram Stars payments and VIP
plans, referrals, forced channel subscription, a full localized admin panel, broadcasts, scheduling,
metrics and backups. Each bot is a small plugin package under `bots/`.

Eight standalone bots ship with the platform, with four templates for user-created bots:

| Bot | What it does |
|---|---|
| **`socialdownload`** | Downloads videos, photos and music from TikTok, Instagram, YouTube, X, Facebook, Pinterest, Reddit, SoundCloud and 1,800+ other sites (yt-dlp + gallery-dl). Files up to 2 GB through the local Bot API, signed direct links beyond that, inline mode, search, playlists. |
| **`notes`** | Notes & reminders. A deliberately small bot that shows how to build on the SDK. |
| **`channelmanager`** | Publishing, schedules, automation, member workflows, publishing teams, locked content, campaigns, invitation gates, channel Stars plans and branded full managers. See [setup](docs/channelmanager/OPERATIONS.md), [publishing](docs/channelmanager/ADVANCED_PUBLISHING.md), [automation](docs/channelmanager/SOURCE_AUTOMATION.md), [members](docs/channelmanager/MEMBER_WORKFLOWS.md), and [growth/billing](docs/channelmanager/GROWTH_AND_BILLING.md). |
| **`anonymous`** | Anonymous inboxes, anonymous replies, personal links, story cards and inline sharing. Also a factory template. |
| **`groupguard`** | Group moderation, warnings, captcha, flood and content locks, notes, filters and night mode. Also a factory template. |
| **`factory`** | Hosts user-created anonymous inbox, feedback/contact, group manager, Channel Manager and custom command/menu bots. Owner management, broadcasts and a public gallery. |
| **`cvbot`** | Analyzes PDF, DOCX, image or text CVs; job matching, cover letters, LinkedIn copy, interview practice and shareable scores. VIP PDF exports and one-off Stars reviews. |
| **`doctools`** | Student document basket: PDF/image transformations, OCR, word counts, citations, AI summaries and shareable study quizzes. Heavy jobs run in a dedicated worker. |

`feedback` and `custombot` are factory-only templates; they use each owner's BotFather token and do
not require platform `FEEDBACK_TOKEN` or `CUSTOMBOT_TOKEN` values. New bots and templates have English
and Arabic interfaces.

## Highlights

- **Multi-tenant core**: global `users` + per-bot `bot_users`; Redis keys namespaced per bot; per-bot
  tables via a table prefix; one bot failing to start never takes the others down.
- **Money handled carefully**: invoices encode exactly what was sold and are validated at pre-checkout;
  payment + VIP grant happen in one idempotent transaction; every VIP change is written to a ledger, so
  refunds (admin-initiated or from Telegram) remove only the paid days.
- **Reliable download pipeline**: crash-safe Redis queue with leases, heartbeats, retries and dead
  letters; identical concurrent requests download once; exactly-once quota refunds; graceful shutdown
  re-queues in-flight work.
- **Admin panel** (`/admin`, en/ar/es/ru): stats, user search and lists, bans with reasons, VIP
  grant/revoke, payment history and refunds, plans, required channels, typed live settings, resumable
  broadcasts, audit log, plus tabs contributed by each bot.
- **Operations**: Alembic migrations, Docker Compose stack with healthchecks, TLS via Let's Encrypt,
  nginx rate limits and Telegram IP allowlist, HMAC-signed expiring download links, nightly backups,
  Prometheus metrics, Sentry, JSON logs with per-update / per-job context.

## Architecture

```
Telegram ──HTTPS──▶ nginx ──/webhook/<slug>──▶ gateway ──▶ one aiogram Dispatcher per bot
                      │                                     │
                      └── /dl/<bot>/<file>?md5=&expires=     ├─ core routers (admin, VIP, lang, referral…)
                          (signed direct links)             └─ bot routers  (bots/<slug>/handlers)

scheduler ── VIP notices, daily reports, broadcasts, bot jobs (exactly-once across replicas)
<slug> workers ── bot background processes (e.g. socialdownload downloads)

shared: PostgreSQL · Redis (durable: queues/state) · Redis (LRU: caches) · local Bot API server
```

Details: [docs/BOT_SDK.md](docs/BOT_SDK.md) (writing bots), [docs/OPERATIONS.md](docs/OPERATIONS.md)
(deploying and running), [docs/DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md) (UI conventions).

## Quick start (local development)

Requirements: Python 3.12+, PostgreSQL, Redis, FFmpeg.

For document extraction and share cards, install the dependencies from `pyproject.toml`. Tesseract
with `eng` and `ara` language data provides OCR when AI is unavailable; the Docker image includes it
and Noto fonts. Configure `AI_PROVIDER` and its API key for CV analysis and other AI actions. Enable
the factory with a persistent `FACTORY_SECRET_KEY`.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # set SOCIALDOWNLOAD_TOKEN (from @BotFather) and SUPER_ADMIN_IDS
# for local runs also set: DATABASE_URL, REDIS_URL; leave WEBHOOK_BASE_URL empty (long polling)
# select bots with ENABLED_BOTS=socialdownload,notes,anonymous,groupguard,factory,cvbot,doctools

python -m core migrate          # create / upgrade the schema
python -m core bots             # validate every bot module
python -m core dev              # gateway + scheduler + all bot processes in one process
```

## CLI

| Command | Purpose |
|---|---|
| `python -m core gateway [--bots a,b]` | Serve updates (webhooks when `WEBHOOK_BASE_URL` is set, else polling) plus `/health/*` and `/metrics` |
| `python -m core scheduler` | VIP notices, daily reports, broadcasts and bot scheduled jobs |
| `python -m core run <slug> <process>` | A bot background process, e.g. `run socialdownload worker` |
| `python -m core run doctools worker` | PDF/image/OCR jobs from the document tools queue |
| `python -m core dev` | Everything above in one process (development) |
| `python -m core migrate` / `makemigrations -m "…"` / `db-current` | Alembic migrations |
| `python -m core bots` | Discover and validate bot modules |
| `python -m core new-bot <slug> --title "…"` | Scaffold a new bot (with a smoke test) |
| `python -m core healthcheck <role>` | Container healthcheck for scheduler / workers |

## Production

```bash
cp .env.example .env    # fill in every value marked REQUIRED
./deploy/init-letsencrypt.sh   # first time only: TLS certificate, then starts the whole stack
docker compose up -d --build   # later deploys (migrations run automatically first)
```

For Document Tools deployments, use `docker compose --profile doctools up -d --build` to include its worker.

See [docs/OPERATIONS.md](docs/OPERATIONS.md) for the full runbook: configuration, scaling workers,
backups and restore, monitoring, cookies and proxies, troubleshooting.

## Quality checks

```bash
ruff check .            # lint
mypy                    # types
pytest -q               # update pipeline, payments, factory, bots, queue/worker and i18n parity
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/scratch pytest tests/integration
# Optional runtime flow tests (Postgres role needs CREATE DATABASE; Redis 7+ DB must be empty):
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/scratch TEST_REDIS_URL=redis://localhost:6379/15 pytest tests/e2e
pre-commit install      # optional: run the same checks on every commit
```

The runtime harness creates its own PostgreSQL database, uses a mock HTTP Bot API and scripted AI,
exercises all new bots through webhooks and the document worker, then verifies clean shutdown. On
POSIX it sends SIGTERM; Windows asks the child to raise SIGTERM through its test launcher. Use
disposable services: the selected Redis database is emptied after the run.
