# Group Guard operator and review guide

Prepared13 October2026, Asia/Jakarta. This is a review/deployment runbook, not evidence of production deployment or live Telegram testing. Public specification is the supplied dated digest/addenda, independently implemented. The full Rose export schema, unseen runtime-help additions, native-language peer review and deployed Bot API capability remain unverified.

## Configure and start

Use the repository's README, .env.example, docker-compose configuration and docs/OPERATIONS.md. Python3.12 is required. Keep real tokens/credentials outside source. The existing core CLI checks modules with `python -m core bots`; run migrations before gateway/scheduler processes. Preserve bot-ID/token/SQL-slug identity: changing a token is not a tenant migration.

Standalone configuration: `ENABLED_BOTS=groupguard`, `GROUPGUARD_TOKEN`, `GROUPGUARD_ADMIN_IDS`, database and Redis URLs. Factory additionally needs `FACTORY_TOKEN`, `FACTORY_ADMIN_IDS`, `FACTORY_SECRET_KEY` and the `groupguard` template. Store the factory encryption key securely; losing it prevents token decryption. Platform/factory ownership does not grant group Telegram administration. Child credits/VIP/features follow the existing factory integration.

Use empty `WEBHOOK_BASE_URL` for development polling or the actual HTTPS URL and secret for webhooks. Never configure a production endpoint as a test fixture. The Group Guard durable inbox commits before webhook acknowledgement; unknown or paused children are acknowledged without acquiring authority. Polling offsets and webhook acknowledgement depend on the actual application path, not merely a handler registry.

## Telegram capabilities and BotFather

Installed aiogram exposes the required methods, including reaction removal and `return_bots`; this does not certify the deployed local/cloud Bot API version. Pin and verify the production Bot API image separately. Check getMe identity, actual getChatMember guarantees, forum support, and reaction endpoints on an authorized canary before enabling those policies.

Required subscription coverage includes message, edited_message, callback_query, chat_member, my_chat_member, chat_join_request, channel_post, message_reaction and message_reaction_count. `allowed_update_types` combines dispatcher routes with module-required events for standalone polling/webhooks and children. Telegram reaction delivery also requires appropriate administrator eligibility. Configure BotFather privacy/message visibility and bot-to-bot delivery where supported; a framework field cannot make Telegram send otherwise unavailable events.

| Operation | Human authority | Bot capability |
| --- | --- | --- |
| Group settings, locks, language | Current admin with change_info | Relevant action capabilities checked separately |
| Ban/mute/kick/warning sanctions | Current restrict_members | restrict_members; protected target checked freshly |
| Deletion/purge and deleting sanction variants | delete_messages plus sanction rights when combined | Same union |
| Pins | pin_messages | pin_messages |
| Promotions | promote_members, limited to caller/bot intersection | promote_members |
| Topics | manage_topics; deletion attributable current creator confirmation | Actual forum and manage_topics |
| Join-request approval/decline | Current policy and personal issued challenge | invite_users, plus restrict_members for mute |
| Import/reset, all-item destructive reset, group federation join/leave | Attributable current group creator | Current media/destination/restore capabilities |
| Federation ownership/admin policy | Current scoped federation role; owner for ownership settings/files/graph | Relevant group enforcement/posting capabilities |
| Broadcast | Configured operator or actual factory child owner | Only this bot's active configured groups |
| Personal privacy | Actual requesting human's own PM | Current namespace; no Telegram erasure RPC |

Every protected mutation rechecks current rights. Cached admin lists, connection history, stored cards and platform owner status do not substitute. Anonymous reviews authorize the approving human's exact immutable action, not the unknown original author. Creator work requires an identifiable current creator. Eligible bot admins follow default human review unless the creator explicitly allows skip-review; they never acquire creator/federation-owner authority.

## Defaults, limits and compatibility

Current defaults come from ChatConfig/GuardSettings and are tested separately from legacy stored JSON. New group:welcome on, goodbye off, clean_welcome off, service cleaning on, CAPTCHA button/on/five minutes, CAS on, newcomer links24hours, AI spam off; flood6messages/8seconds/mute, consecutive threshold off, warning threshold3/ban, legacy automatic duration60minutes, raid manual period6hours/newcomer ban1hour/automatic threshold off, night off23–07UTC, empty locks/blocklist, blocklist action nothing with deletion on, bot2bot off, skip-review off, automated silent actions off, language platform default. Existing fields/default choices are preserved on upgrade; unknown JSON is retained. Confirm exact current fields in `chatconfig.py` rather than treating Rose defaults as ours.

Temporary sanctions accept60seconds–365days. General timers are separate. Missing/malformed unsafe temporary durations never become permanent sanctions. Flood/warning threshold boundaries and local precedence are recorded in DECISIONS.md. Current federation bans precede ordinary approvals/CAPTCHA/raid; actual admins remain protected. Manual authorized moderation retains control.

Help: `/help`, `/help FAMILY`, `/help COMMAND`, `/help FAMILY 2`. Eighteen families cover actual implemented commands, contexts, permissions, aliases and local defaults. Registry names `runs`/`saved` have an explicit unsupported explanation; `/antiflood` is a deliberate read-only flood alias. S37 new notes require one word; broader old names remain a readable/importable legacy extension. Quoted phrases remain supported for filters/blocklists. The full syntax/context/right mapping is in COMMANDS.md and FEATURE_MATRIX.csv; owning tests and source uncertainty accompany each stable row.

Files:own `groupguard.modules` version1,16 selectable families,2MiB/1000file records plus configured item/content caps; creator import/reset with personal five-minute single-use/revision/digest confirmation; local five-minute group interval. Unselected modules/unknown destination JSON stay. Media file IDs are bot-bound; getFile proof is required. Foreign-group topic IDs are rejected. Issued challenge IDs, trust/roles/entitlements/federation ownership/live work are excluded. Selected repeats/CAP/night/raid generations are retired safely; real punitive bans stay. Full Rose export compatibility is not claimed.

Federation files:CSV/full or minicsv, true JSONL/NDJSON, and explicit own JSON-array adapter.2MiB/1000records, sourced shared30-minute per-federation import/export interval; validate all records before writes. Own bounded subscription graph:32direct/128reachable/depth16/10000edges, no cycles/self-subscription. Fanout producer/destination pages100, pending destination limit5000, shared20/sec outbound quota. These are local caps. Observations come from real events and do not enumerate all Telegram members.

Locale coverage:all31 published471-message bundles, plus default English.25 full159-message native shared-platform overrides; remaining languages use complete native core or legitimate same-language regional bases. Region/script aliases preserve older fallback behavior. Native guide/error/button/placeholder bounds are tested; no native-language reviewer has certified quality. Group `/setlang` and personal `/lang` remain distinct.

## Diagnostics and recovery

A saved policy or queued job is not an already completed Telegram effect. Inspect typed primary/partial/ancillary outcomes, scoped audit metadata, durable job status/error_code/generation/lease and current namespace. Redis outage may deny a mutation or defer cleanup; SQL privacy deletion reports cache_pending honestly. Runtime logs must not contain real tokens, raw import files, CAPTCHA answers or unrestricted private content.

`pending/running/completed/failed/cancelled/uncertain` are distinct. Known RetryAfter/transport handling has bounded retry/backoff; local quota deferral does not consume the external RPC retry budget. An uncertain non-idempotent RPC is retained and never blindly repeated. Internal dedupe/count/claim guarantees do not promise exactly-once remote Telegram effects. Newer federation unban/graph/attachment generations fence older work. Multiple current owners/sources preserve remaining restrictions; unowned external restrictions are not automatically released.

Night restoration compares the actual current permissions with this bot's recorded closed snapshot; another admin's change wins. CAPTCHA release retains other sanctions and transferred night holds. Selected resets fail without discarding issued work when safe restoration is unavailable. Pausing children fences cached runtime/queued mutations first, allows only narrowly owned cleanup, records residual failure, and keeps required privacy cleanup available. Revoked credentials may prevent restoration; diagnose ownership/capability rather than manufacturing open defaults.

## Data, backup and rollback

Migrations0009baseline→0010–0018 are additive and are exercised on fresh PostgreSQL and a real old-baseline seed with legacy HTML/media/unknown JSON/warnings. No Phase11 migration is required. Before any production upgrade, back up PostgreSQL and verify a restoration rehearsal, preserve factory encryption keys and runtime configuration, inventory Redis state and queued/uncertain jobs, and retain a compatible previous application/image.

Alembic downgrade tests prove disposable schema reversibility, not lossless production rollback. Downgrading removes new tables/columns and their data; older code cannot interpret new options/generations. A database restore can reintroduce already-sent intents. Stop/fence producers and workers, reconcile uncertain remote effects and pending jobs, then follow the backup restoration plan; do not blindly replay restored work. Redis loss invalidates ephemeral personal cards and can lose convenience counters; SQL durable state still governs owning challenges/jobs/ordering. Backups/log archives have separate operator retention and deletion procedures.

Privacy `/privacy policy|data|delete` requires the requesting human's own PM. Inventory includes19 own-data sections with200-row typed keyset pages/2MiB. Tokens, payment charge IDs, raw uploads, challenge answers and others' private content are excluded. Delete optional Group Guard convenience data/terminal owned content, clear exact owned cache/token state and enqueue durable recovery before SQL commit. Preserve minimal active moderation, versions/order/replay, roles/ownership/entitlements/payments, uncertain work, platform preferences and shared global User. Preserve the existing newcomer timestamp to its policy expiry. No universal invented retention duration or Telegram/backup erasure is promised.

## Reproduce disposable local checks

Use the existing isolated checkout and `.venv`; do not create worktrees unless requested. Only disposable loopback PostgreSQL16/Redis7 are authorized for these schema-drop/flush fixtures. `tools/start-groupguard-test-services.sh` creates/starts only `gg-long-postgres`/`gg-long-redis`, validates SELECT1/PONG, and is repeatable. Test-only trust authentication is bound to127.0.0.1 and is not a production configuration.

```sh
bash tools/start-groupguard-test-services.sh
.venv/bin/python -m pip check
.venv/bin/python -m core bots
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/pytest -q --tb=short
TEST_GG_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_concurrency TEST_GG_REDIS_URL=redis://127.0.0.1:56380/2 .venv/bin/pytest -q tests/integration/test_groupguard_foundations.py --tb=short
TEST_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_integration TEST_REDIS_CLAIM_URL=redis://127.0.0.1:56380/1 .venv/bin/pytest -q tests/integration/test_migrations.py tests/integration/test_groupguard_review.py --tb=short
TEST_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gglong TEST_REDIS_URL=redis://127.0.0.1:56380/0 .venv/bin/pytest -q tests/e2e --tb=short
```

Fast Group Guard conversation fixtures deliberately bypass throttling so denial tests reach the intended authorization guard. Separate runtime/middleware tests retain real maintenance/ban/throttle/invoice/lifecycle behavior. Recording Telegram SDK effects are not live moderation. Required PostgreSQL/Redis/migration/runtime categories run separately; report default-suite service skips separately from passes. Live-site tests remain excluded by repository policy; optional actual CAS/AI services are unverified.

## Authorized deployment rehearsal and manual QA

No deployment or live group test was run here. On a separately authorized canary, verify token/namespace and deployed API prerequisites, private start/settings deep links, all required event subscriptions, current admin/creator union rights, expired/forged/replayed personal cards, one standalone and two children in the same test group, and group versus personal language. Exercise rich content/Unicode/media/private links, edits before core routes, reaction identities/unsupported aggregate diagnostics, real flood/raid/CAP/night outcomes, bot-to-bot review visibility and sender loops, log consent/posting failures, and privacy/import/reset safety.

Restart gateway/scheduler with pending deadlines/repeats/fanout/uncertain outcomes; confirm stale generations are denied and actual effects are not duplicated. Pause/delete/revoke a canary child and inspect narrowly owned restoration/residuals/sibling isolation. Test backups and rollback with retained remote-effect reconciliation. Observe queue growth, API quotas, database pool usage, lease expiry, delivery errors and privacy cache deferral before expanding traffic. Measured local fixture workloads in the final report do not establish production throughput or independent security certification.
