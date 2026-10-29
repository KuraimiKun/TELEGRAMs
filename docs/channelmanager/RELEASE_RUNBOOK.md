# Channel Manager release, canary and rollback

## Current release state

Offline readiness is verified. The user explicitly skipped live Telegram verification because the bot token has not been created. No production deployment, real charges/refunds, or webhook migration was performed. The full native/client canary remains a release gate, with the exact [compatibility matrix](COMPATIBILITY_MATRIX.md) and [verification evidence](PHASE_07_VERIFICATION.md) recorded separately.

Run the offline check without reading a private environment file:

```text
python -m bots.channelmanager.preflight
```

An explicit `--env-file PATH` checks presence/pinning without printing values. This command performs no Telegram calls, connects to no database, never implicitly loads `.env`, and never grants production approval. `--require-deployment` exits nonzero while native approval is outside this offline tool. Do not interpret an ordinary offline exit code of zero as permission to deploy.

## Deployment preparation

1. Create the bot in BotFather, retain its token privately, and configure `CHANNELMANAGER_TOKEN`, `CHANNELMANAGER_ADMIN_IDS` and `ENABLED_BOTS` when live verification is authorized. Preserve any existing enabled bots.
2. Select and run the local Bot API container in an isolated canary. The inspected candidate is `aiogram/telegram-bot-api@sha256:5d568e2ff798ccda6a727feb5d1c7f8ef79d71f6ee51aae7dc6f9e748b5e703e` (tag 10.3). Its registry metadata was inspected; its container/native behavior was not tested here. Set `TELEGRAM_BOT_API_IMAGE` to the canary-verified immutable digest. Compose has no `latest` fallback.
3. Back up the database, protected factory encryption key and required application data. Apply migrations through `0024_chm_growth` using the normal one-shot migration service. Do not run Channel Manager processes against an older schema.
4. Start the normal gateway and scheduler plus `worker-channelmanager` through the optional Compose profile. Before connecting canary channels, select the restricted rollout stage below in `/admin` settings. Existing defaults remain `commercial` for compatibility; this is not an instruction to launch every feature together.
5. Confirm gateway `/health/ready`, worker progress health, scheduler health and the queue/financial diagnostics before introducing traffic. The factory scheduler is required for children.

```text
docker compose --profile channelmanager config --quiet
docker compose --profile channelmanager up -d --build
```

The first command resolves real service env files when used in deployment; keep its output private and prefer `--quiet`. Offline validation used synthetic values with `--no-env-resolution`, and started no container.

The worker healthcheck is `python -m bots.channelmanager.health`. It reads the last successful progress pulse, rejects missing/corrupt/future/stale timestamps and uses a 90-second age ceiling. A separately alive role heartbeat cannot mask a stuck delivery loop. Each delivery attempt has a 60-second outer deadline; its durable 90-second operation lease and dispatch marker determine recovery after interruption.

## Staged rollout

`rollout_stage` is a validated bot setting. The stages are cumulative:

| Stage | New effects allowed |
|---|---|
| `paused` | Required cleanup/refunds and financial receipt processing continue; new business effects stop |
| `publishing` | Draft publication, scheduling, edits, buttons/votes and recurrence |
| `automation` | Publishing plus source auto-complete and routing |
| `members` | Prior stages plus configured admission/member effects |
| `commercial` | Prior stages plus collaboration/private growth, campaigns, new invoices and branded bindings |

Dispatch reads stage/maintenance from SQL, including the applicable control bot for a bound child source. Another control bot's stage does not pause an unrelated source. New invoice checkout is disabled outside the commercial stage. Already charged receipts and authorized refunds are still reconciled. Cleanup kinds are not disabled by stage or maintenance; explicit channel disconnection/rights loss can still make a native cleanup impossible.

Policies/rules and plan publication keep their own enablement controls. A stage does not automatically enable a saved admission policy or publish a price. For a branded full manager, advance both the control and child contexts deliberately. Held/cancelled work requires review; never reset uncertain effects just to move a canary forward.

Advance only after this native sequence has a recorded pass:

1. **Private publishing canary:** English/Arabic text and supported media, preview/send equivalence, buttons/votes, timezones and one scheduled post, editing, pin failure separation, deletion and removal of bot rights. Verify duplicate delivery/restart behavior without deliberately repeating unknown sends.
2. **Automation:** one observed manual post and a supported album, filtered route, edit propagation, loop suppression, disable/review recovery and external log behavior.
3. **Members:** standard join request, temporary contact, signed private continuation, captcha failure/success, ordered required chats, manual/timer inability to bypass gates, observed rejoin and one bounded cleanup. Do not test destructive moderation on unrelated users.
4. **Commercial growth:** one locked teaser/private reveal, missing membership links, sender-specific file upload, explicit campaign opt-in/opt-out and a small fixed audience. Confirm no secret appears in a global edit and no outsider enters a campaign.
5. **Financial/factory:** an administrator configures an unpublished test price, reviews/publishes it, then the payer explicitly approves a native Stars purchase. Verify the linked channel grant, duplicate receipt, payer-approved full refund and ledger reconciliation. Bind one owned test child, rotate/pause/rebind it, inspect residual cleanup, and verify a sibling/control ledger is retained. No test payment amount or webhook migration is pre-approved by this document.

Record bot/client/server versions, source IDs, native message/charge references in the protected operator record, timings, actual results and the reviewer. Do not put credentials into repository evidence. Native visual/payment checks were skipped in this execution and must not be marked passed from automated fixtures.

## Operational diagnostics and capacity

`/admin` → Channel Manager shows queue failures/uncertainty, failed inbox receipts, member state, growth failures, payments/refunds requiring review, paused control senders, cleanup backlog and oldest operation/inbox age. Owner workflows remain under `/posts`, `/automation`, `/members`, `/campaigns`, `/plans`, `/senders` and `/menus`.

Metrics include `channelmanager_work`, `channelmanager_queue_lag_seconds` and `channelmanager_operation_seconds`. Labels contain only fixed state/queue values and a standalone/template metric name, not channel/user IDs. Factory gauges aggregate all template children in SQL; a last processed child must not overwrite fleet totals. Paused/revoked children remain visible in retained-work aggregates. Example rules are in [channelmanager-alerts.yml](../../deploy/channelmanager-alerts.yml); review/suppress planned-pause lag alerts deliberately.

The representative recorded-transport campaign used 300 distinct recipients, a real 25/s shared Redis sender budget, PostgreSQL 16 and concurrent interactive drafts. It produced no duplicates; measured figures are in the verification record. This is an offline database/rate-budget baseline, not Telegram network capacity or a production latency guarantee. Start canaries small, investigate due lag above 120 seconds for five minutes, and keep interactive requests responsive before increasing worker concurrency.

## Operational rollback

1. Set `rollout_stage=paused` for the affected standalone/control/child scope. Keep the receipt-compatible gateway, schema and worker available. Uncached final dispatch checks prevent stale cached stages from authorizing new effects.
2. Inspect running/dispatched jobs and allow bounded calls to settle or leases to expire. Recovery returns undispatched work to pending subject to its attempt budget; dispatched uncertainty is not replayed. Review cancelled/held work before any later stage advance.
3. Keep financial receipts, full refunds, known-message deletions, owned unbans and invitation revocations processing. Maintenance also permits cleanup-only claims. If connectivity or bot rights prevent cleanup, retain its records and report the native residuals.
4. Preserve all payment/grant/audit data and the factory encryption key. Reverting to older application code is allowed only if it can still ingest/reconcile the current financial receipts and schema. A pre-billing gateway can acknowledge and lose a later payment receipt; do not use that as a rollback target.
5. Restore service under the restricted stage, resolve the incident, then explicitly review and advance again. Roll back using gates and compatible code, not an Alembic downgrade or deletion of template data.

Normal rollback does not restore an older database snapshot. Disaster recovery from a backup requires all writers/cutover coordination and reconciliation of payments or Telegram effects newer than the snapshot; restoring a database cannot undo a remote charge/message. Keep ingress failing/retrying rather than acknowledging uncommitted financial receipts during cutover.

## Backup/restore verification and reproduction

The existing `deploy/backup.sh` produced a custom-format PostgreSQL dump from the disposable Phase 7 database. It was restored into a separate fresh database. Payment amounts/status/zero-day linkage, channel grants/invoices, audit counts, operation IDs/dedupe/state, pending cleanup and migration revision matched. No original database was overwritten. Factory keys and real media were not part of this synthetic data exercise; include them in protected production recovery procedures.

The committed development harness is intentionally restricted to fixed loopback `channelmanager_phase7_test` and `channelmanager_phase7_restore_test` databases. It truncates its own source test database, uses only `RecordingSession`, and needs development dependencies:

```text
python -m tests.integration.chm_release_harness
```

Run `deploy/backup.sh` against that disposable source, create a separate restore database and use matching PostgreSQL 16 `pg_restore --exit-on-error --no-owner`. Then:

```text
python -m tests.integration.chm_release_harness --verify-restore
```

All earlier real-service suites and `tests/integration/test_channelmanager_readiness.py` remain independently runnable with their dedicated URL/key guards. See the verification record for exact suites, versions, results and remaining deferred gates.
