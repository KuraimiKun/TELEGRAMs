# Operations runbook

Everything needed to deploy, run, observe and recover the platform on a single VPS with Docker Compose.

## 1. Services

| Service | Role | Scaling |
|---|---|---|
| `migrate` | One-shot `alembic upgrade head`; every app service waits for it | — |
| `gateway` | Receives updates for all bots, serves `/health/*` and `/metrics` | 1; CV source sessions require user routing affinity across replicas |
| `scheduler` | VIP notices, daily reports, broadcasts, bot jobs | 1+ (jobs are single-flight via Redis locks) |
| `worker-socialdownload` | Downloads | `SOCIALDOWNLOAD_WORKER_REPLICAS` × `SOCIALDOWNLOAD_WORKER_CONCURRENCY` |
| `worker-doctools` | PDF/image/OCR jobs (`doctools` Compose profile) | `--scale worker-doctools=N` × `DOCTOOLS_WORKER_CONCURRENCY` |
| `postgres` | All persistent data | — |
| `redis` | Durable state: queues, FSM, locks, quotas (`noeviction`, AOF) | — |
| `redis-cache` | Evictable caches: Telegram file_ids (`allkeys-lru`) | — |
| `telegram-bot-api` | Local Bot API server (2 GB uploads) | — |
| `pot-provider` | YouTube proof-of-origin tokens for yt-dlp | — |
| `nginx` + `certbot` | TLS, webhook forwarding, signed `/dl/` links | — |
| `backup` | Nightly `pg_dump` + bot data archive | — |

## 2. First deployment

1. DNS: point `DOMAIN` at the server. Open ports 80 and 443.
2. `cp .env.example .env` and fill in every value marked **REQUIRED**:
   `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `TELEGRAM_API_ID`/`TELEGRAM_API_HASH` (my.telegram.org),
   `DOMAIN`, `LETSENCRYPT_EMAIL`, `DIRECT_LINK_SECRET`, and each bot's `<SLUG>_TOKEN`.
   Generate secrets with `openssl rand -hex 32`.
3. Pin tested images: `TELEGRAM_BOT_API_IMAGE`, `POT_PROVIDER_IMAGE`.
4. `./deploy/init-letsencrypt.sh` (add `--staging` for a dry run). It creates writable data dirs, obtains
   the certificate and starts the stack.
5. Check: `docker compose ps` (all healthy), `curl https://$DOMAIN/health/live`, and send `/start` to
   each bot. `/admin` works for `SUPER_ADMIN_IDS` and each bot's `<SLUG>_ADMIN_IDS`.
6. Inline mode: enable inline mode **and inline feedback** for SocialDownload; enable inline mode for
   Anonymous Inbox, CVBot and Document Tools. Give Group Guard moderation permissions in groups and disable Group Privacy if
   it must inspect ordinary messages. Configure the factory secret and AI provider as described below.
7. For Document Tools, set `DOCTOOLS_TOKEN`, include `doctools` in `ENABLED_BOTS`, then start the worker
   with `docker compose --profile doctools up -d --build`. Enable the profile on later deploys too.

## 3. Routine deploys

```bash
git pull && docker compose up -d --build
```

When Document Tools is enabled, use `docker compose --profile doctools up -d --build` so its worker
is rebuilt and restarted too.

`migrate` runs before the app starts. Pending Telegram updates are kept across restarts (they are not
dropped), and messages that piled up during the restart are exempt from throttling. Workers drain for
up to 20 s on `SIGTERM`; anything still running is re-queued at the front and resumed by another worker.

### Schema changes

```bash
python -m core makemigrations -m "describe the change"   # creates core/db/migrations/versions/000N_*.py
python -m core migrate                                     # apply locally, review the file, commit it
```

A database created by the old `create_all` bootstrap is adopted automatically (stamped at `0001`).

## 4. Configuration reference

Platform-wide variables are plain names; per-bot variables are prefixed with the bot slug in upper case
(`SOCIALDOWNLOAD_TOKEN`, `NOTES_ADMIN_IDS`, …). `.env.example` documents every variable and a test keeps
it in sync with the code. Runtime behaviour (limits, force-subscribe, sponsors, referral rewards,
maintenance mode…) is edited live in `/admin → Settings` and audited.

## 5. Monitoring

- **Health**: `GET /health/live` (public), `GET /health/ready` (DB + Redis; internal only — nginx hides
  it). Scheduler and workers publish Redis heartbeats checked by `python -m core healthcheck <role>`.
- **Metrics** (Prometheus): gateway `:8080/metrics`; scheduler and workers `:METRICS_PORT/metrics`
  (internal network only). Key series:
  - `tg_updates_total{bot,type}`, `tg_update_seconds`, `tg_handler_errors_total{bot}`
  - `payments_total`, `payment_stars_total`, `refunds_total`
  - `download_jobs_total{bot,platform,outcome}`, `download_job_seconds`, `download_queue_depth{state}`,
    `download_bytes_delivered_total`
  - `broadcast_messages_total{outcome}`, `scheduled_job_runs_total{job,outcome}`
  - `ai_requests_total{provider,bot,outcome}`, `ai_tokens_total{provider,direction}`, `ai_request_seconds`
- **Errors**: set `SENTRY_DSN` (plus optional `ENVIRONMENT`, `RELEASE`). Unhandled update errors, failed
  jobs and failing scheduled jobs are reported with `bot`, `update_id`/`job_id` tags.
- **Logs**: JSON (`LOG_JSON=true`) with `bot`, `update_id`, `user_id` / `job_id` bound automatically.
  `docker compose logs -f gateway worker-socialdownload`.
- **Alerts worth setting**: `download_queue_depth{state="dead"}` growing, a high
  `download_jobs_total{outcome=~"failed_.*"}` ratio, `tg_handler_errors_total` rate > 0, a non-ready
  `/health/ready`, and missing heartbeats.

## 6. Backups & restore

The `backup` service writes `./backups/db-<timestamp>.dump` (custom format) and
`./backups/data-<timestamp>.tar.gz` (cookies and other small bot data) every day at
`BACKUP_HOUR_UTC`, keeping `BACKUP_RETENTION_DAYS` days. Copy `./backups` off the server (rsync / object
storage) — a backup on the same disk is not a backup.

Run a backup on demand: `docker compose exec backup /bin/sh /usr/local/bin/backup.sh`.

Restore:

```bash
docker compose --profile doctools stop gateway scheduler worker-socialdownload worker-doctools
docker compose exec -T postgres pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists \
    < backups/db-YYYYMMDDTHHMMSSZ.dump
tar -xzf backups/data-YYYYMMDDTHHMMSSZ.tar.gz -C ./data
docker compose up -d
```

When Document Tools is enabled, restart with `docker compose --profile doctools up -d`.

Redis holds queues and short-lived state only: after losing it, in-flight downloads are lost (users can
resend), caches refill on demand.

## 7. SocialDownload specifics

- **yt-dlp freshness** is the most common cause of failures. The scheduler alerts the bot's log channel
  (or admins) when a new release exists; rebuild the image to update (`docker compose build --pull`).
- **Cookies** for login-gated content: `/admin → 🧰 Downloads → Cookies`, then send a Netscape
  `cookies.txt` with the platform as caption (`youtube`, `instagram`, …). Files are validated, stored
  0600, rotated per download, and down-weighted after login failures.
- **Proxies**: `SOCIALDOWNLOAD_PROXIES` (read-only) plus a list managed in the admin tab. Failing proxies
  are picked less often.
- **Dead letters**: jobs whose worker died 3 times are refunded, reported to the user, and listed in the
  admin tab for inspection.
- **Disk**: work dirs are cleaned every 10 minutes; downloads refuse to start when free space is low.
- **Direct links** (VIP files above 2 GB) are HMAC-signed by the app and verified by nginx with
  `DIRECT_LINK_SECRET`; they expire after `SOCIALDOWNLOAD_DIRECT_LINK_TTL_SECONDS`.

## 8. Security notes

- Webhooks: per-bot secret token (validated by the gateway) + Telegram IP allowlist and rate limit in nginx.
- Downloads: URLs to private, loopback, link-local or internal Docker hosts are refused (SSRF guard,
  including every redirect hop of short links); unknown sites are ignored in groups by default.
- All user- and site-provided text is HTML-escaped before it reaches Telegram.
- Rotate a bot token: update `<SLUG>_TOKEN` and restart. The platform refuses to start if a slug's token
  suddenly belongs to a *different* bot, so two bots' data can never be mixed by accident.

## 9. Troubleshooting

| Symptom | Check |
|---|---|
| Bot silent | `docker compose logs gateway` for `bot_context_failed` / `set_webhook_failed`; `getWebhookInfo` |
| `configuration_error` at start | The message names the exact `<SLUG>_*` variable that is missing/invalid |
| Downloads stuck in queue | `download_queue_depth`, worker health, `/admin → 🧰 Downloads` |
| Many `failed_login` | Upload fresh cookies for that platform |
| Many `failed_timeout` | Proxies down / platform rate limiting — add or rotate proxies |
| Broadcast not progressing | Scheduler health; broadcasts resume automatically after restarts |
| Document jobs queued but no result | Enable the `doctools` Compose profile; inspect `worker-doctools` logs and heartbeat |
| OCR executable/language error | Check `DOCTOOLS_TESSERACT_COMMAND` and `tesseract --list-langs` includes `eng` and `ara` |

## 10. Factory operations

Enable `factory` in `ENABLED_BOTS`, set `FACTORY_TOKEN` and generate a stable `FACTORY_SECRET_KEY`
(`openssl rand -hex 32`). Child tokens are Fernet-encrypted with a key derived from this secret;
child webhook secrets are derived from it too. Back up the secret securely with the database.
An ordinary database backup alone cannot recover encrypted child tokens.

Templates `anonymous`, `feedback`, `groupguard` and `custom` are discovered automatically, including
factory-only modules. Their tokens come from owners using `/newbot`; no platform token is required
for `feedback` or `custombot`. `/mybots` lets an owner inspect users, pause/resume, rotate their token,
open child admin/broadcast tools and delete a bot. Default live limits are 1 free or 10 VIP bots,
plus a slot per 3 qualifying referrals; change these in the factory's admin settings.

Production child webhooks use `/webhook/c/<bot_id>`. The existing nginx `/webhook/` location covers
them; no factory-specific location is needed. Gateway startup reasserts active child webhooks.
Local polling is bounded by `FACTORY_DEV_POLLING_MAX`; use webhooks when hosting many children.
Keep the scheduler running for child broadcasts and Group Guard's shared captcha/night sweeps.

To revoke an abusive child, open the factory's `/admin → Factory`, search its username or owner id,
choose Revoke and confirm. This removes the webhook, wipes the stored token, hides the bot from the
gallery and retains its record and reason for audit. The same Telegram bot id cannot be re-created
through `/newbot`. Owner Pause keeps its token and data; owner Delete removes the child's data.

For a child's BotFather token rotation, the owner uses `/mybots → bot → Rotate token`. The factory
checks that the new token belongs to the same bot id, replaces the encrypted token and reattaches
the webhook. Platform tokens are rotated through `<SLUG>_TOKEN` and a service restart.

### Factory encryption-key rotation

There is no automatic key-rotation CLI. Simply replacing `FACTORY_SECRET_KEY` makes existing child
tokens unreadable. Perform a coordinated maintenance operation:

1. Stop gateway, scheduler and bot workers so children and admin mutations cannot race the rotation.
2. Back up the database and old secret together; generate and securely retain the replacement secret.
3. In one database transaction, read every nonempty `ChildBot.token_enc`, decrypt with
   `core.factory.crypto.decrypt_token(old_platform_config, ...)`, and re-encrypt with
   `encrypt_token(new_platform_config, ...)`. Verify every round trip before committing. Abort the
   whole transaction if any token is unreadable; revoked rows have empty tokens and stay empty.
4. Install the new secret in `.env` and restart the app services together. Startup replaces child
   webhook secrets and fresh registries rebuild child contexts. Verify a child update and broadcast.
5. If recovery is required, restore both the database snapshot and matching old secret together.

Avoid recording plaintext tokens or keys in shell history, SQL files, logs or support tickets.

## 11. AI and CV operations

Set `AI_PROVIDER=anthropic` with `ANTHROPIC_API_KEY`, or `AI_PROVIDER=openai` with `OPENAI_API_KEY`.
The selected provider is shared by all bots in each process. Missing credentials disable AI buttons;
CV analysis needs AI, while extraction/OCR still supports local processing. Set `AI_MODEL` and
`AI_FAST_MODEL` explicitly when you need to pin model ids supported by your provider account.

`AI_DAILY_TOKEN_BUDGET` counts input plus output tokens across bots per UTC day in durable Redis;
`0` is unlimited. The example config sets 2,000,000. Restart app services after changing this
environment setting. The client checks spent tokens before each call and rechecks queued requests
when they acquire a process concurrency slot. Completed calls are accounted before releasing that
slot; calls already in flight can still pass the threshold together. Set a conservative budget and
provider-side spending limits when
you require a firm monetary cap. `AI_CONCURRENCY` bounds simultaneous AI calls per process, not
across the deployment. Adding workers increases the possible concurrent calls.

Watch budget outcomes in `ai_requests_total`, usage in `ai_tokens_total`, and latency in
`ai_request_seconds`; a budget exhaustion message is expected once the daily cap is reached. The
client's `tokens_today()` and `user_tokens_today(bot, user_id)` expose the Redis counters. Redis
resets at the UTC date boundary; do not clear quota/budget keys as a routine fix.

Enable `cvbot` and set `CVBOT_TOKEN`. CVs can be PDF, DOCX, image or pasted text. The initial live
limits are 1 free analysis/day, 10 MB, 12 pages and 40,000 extracted characters; VIP removes the
daily analysis limit and enables classic/modern PDF exports. `/pro` buys one detailed analysis for
25 Stars by default, validated through core payments; configure the price and limits in `/admin`.

CV files use temporary storage; extracted text stays in process memory for up to 15 minutes. Only
analysis summaries are stored in `cv_reports`. `/forget` deletes a user's reports and current
session. Backups therefore contain summaries, so apply your normal backup retention policy when
handling deletion requests. OCR fallback requires Tesseract with `eng` and `ara` language data;
the runtime Docker image installs these packages plus Noto fonts for Arabic share cards.

Keep one gateway when CVBot is enabled, or route each user's CV updates to the same gateway.
Follow-up tools need the source text held in that process; a gateway restart clears these sessions
and users must resend their CVs.

## 12. Document tools operations

Users upload PDF or image files into a 10-minute basket, select an action and receive the resulting
document. Supported actions include merge, split/extract ranges, compress, rotate, page numbers,
watermark, password lock/unlock, PDF-to-images, images-to-PDF and scan enhancement. `/count` and
`/cite` also work in groups; inline `cite <DOI>` shares a citation. OCR produces text or DOCX.
AI summaries and quiz polls use the configured provider and a separate per-user daily quota.

Run at least one `python -m core run doctools worker` process alongside the gateway. Compose provides
`worker-doctools` behind the `doctools` profile so installations without this bot do not start an
unconfigured worker. Scale with
`docker compose --profile doctools up -d --scale worker-doctools=2`; each replica opens its own
database pool and handles `DOCTOOLS_WORKER_CONCURRENCY` jobs. The worker uses a Redis queue with
leased jobs and retry/requeue after failures; use durable `REDIS_URL`, never the LRU cache Redis.

`DOCTOOLS_JOB_TIMEOUT_SECONDS` caps heavy jobs, `DOCTOOLS_OCR_TIMEOUT_SECONDS` caps each OCR process,
and `DOCTOOLS_TESSERACT_COMMAND` selects the executable. Basket size/page limits and free/VIP caps
are typed live admin settings. Downloads and outputs use worker-local temporary directories that
are cleaned on completion; job inputs reference Telegram files in Redis, so workers need the shared
read-only `bot_api_data` mount when local Bot API paths are enabled. No shared output volume is needed.
The database stores job counters/metadata rather than original document bytes. Redis baskets and
jobs temporarily retain file references, pasted text, operation passwords and cached AI results.
Baskets expire after ten minutes; jobs are deleted when finished and have a six-hour TTL renewed
while leased. Restrict Redis access and protect its AOF/backups as private user data. After a hard process
crash, leftover scratch directories are removed once older than the job timeout plus 300 seconds
(10 minutes with the default timeout).

Before an upgrade or backup restore, stop document workers with the gateway and scheduler. Inspect
the worker's `doctools-worker` heartbeat and logs when queue depth grows. After Redis data loss,
users may need to resend baskets/jobs, just as with SocialDownload. Keep OCR language data and Noto
fonts in the runtime image; Python dependency installation alone does not supply them.
