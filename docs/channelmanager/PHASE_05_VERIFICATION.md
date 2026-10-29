# Phase 5 implementation and verification

Implemented 29 October 2026 in the working tree based on repository commit `10e9b83`, extending Phases 1–4. See [member workflows](MEMBER_WORKFLOWS.md) for the walkthrough and exact supported contracts, and [the phase checklist](phases/PHASE_05_MEMBERSHIP.md) for scope.

## Implemented scope

- Durable observed requests, monotonic channel/user heads, policy snapshots, contact/expiry deadlines, captcha attempts, ordered required-chat progress, manual release, terminal outcomes, and rejoin invalidation.
- Immediate, delayed, and manual approval through a single state machine; persisted bulk snapshots with actor/policy/expiry checks and per-entry release/skipped totals.
- Shared canonical text/media composition, safe buttons/previews, initial introduction/captcha contact, signed owner-bound `/start` continuation, and reachable post-approval welcome/goodbye.
- Total block, ten-second observed-rate controls, bounded name/username expressions, Unicode-script rules, language policies, and explicit validation/outcomes.
- Fresh admission and native-role checks, bounded private contact, idempotent captcha receipts, independent action reports, definite-failure retry, uncertainty preservation, and shared sender/chat budgets.
- Voluntary departure detection, independent source/linked-group enforcement, durable timed unbans, protection for rejoined members and changed administrator bans, and allowlisted observed service-message cleanup.
- English/Arabic event logs and menus, retained internal audit, log-output suppression in source automation, channel-scoped private interaction evidence, worker recovery, fixed-label diagnostics/metrics, and operator documentation.
- Eight new tables, a nullable scoped operation reference, and membership request/output lookup indexes in `0023_chm_members`.

## Verification results

| Check | Result |
|---|---|
| Channel Manager/locale and all five real-service files | 272 passed; 245.52 seconds (245 bot/locale + 27 PostgreSQL/Redis checks) |
| Full default regression suite | 1,802 passed, 157 skipped, two Group Guard failures; 1,492.24 seconds. Both were fixed and verified in follow-up checks below. |
| Final failure/menu rechecks | 103 passed; 31.78 seconds (Group Guard matcher/federation file and member menus, including signed start) |
| Matcher behavior comparison | 5,000 deterministic differential cases agreed with the original implementation, including invalid-pattern outcomes |
| Ruff | `ruff check .` passed |
| Mypy | Passed; 368 source files |
| Tracked-file whitespace check | `git diff --check` passed |

The final Phase 5 application code is covered by the combined run above and the broader regression run. The final router-specific signed-start test was added afterward and passed in the 103-test recheck. All Telegram API effects use `RecordingSession`; no live bot messages, tokens, webhooks, production records, or deployment were changed. Tests exclude the workspace `.env`.

Disposable loopback services use PostgreSQL 14.24 and Redis 6.0.16 in WSL and were stopped after verification. The production Compose PostgreSQL 16/Redis 7 pairing and live Telegram/client compatibility remain canary gates.

The broader run's first failure was the existing matcher adversarial speed check (10.77 seconds against an 8-second ceiling). The matcher now rejects wildcard patterns whose mandatory literal characters are absent before entering its NFA. The unchanged Unicode/wildcard/adversarial contracts pass, and 5,000 deterministic differential cases preserve prior results and validation errors. The second failure was a Group Guard federation quota fixture crossing a one-second rate bucket; the fixture now supplies a fixed module-local clock and stable seeded key. No production federation behavior changed. The full suite began before those two corrections and was not repeated after them; their complete affected files passed in the final 103-test run. One existing PyMuPDF `fitz` deprecation warning was emitted.

## Evidence

Functional/menu checks cover initial contact before approval, no inferred private-start evidence, signed link ownership/tampering, captcha limits and duplicate receipts, timer/manual/bulk inability to bypass gates, current required membership, policy-change holds/adoption without restored attempts, observed-queue snapshots, expired contact, blocked users, old expiry versus rejoin, unknown approval without replay, profile outcomes, and one-time reachable welcomes.

Departure/cleanup checks distinguish voluntary departure from administrator/bot removal; preserve independent linked-group action through own source-enforcement events; retain timed cleanup after disabling policy; avoid removing rejoined members; preserve changed administrator bans; require `only_if_banned`; retain internal audit after external logging failure; suppress event-log output from source automation; and remove only selected service messages.

Menus are tested for operator ownership, stale activation, validated policy/required-chat input, shared content/buttons/preview, cancellation, reviewed bulk snapshots, and callback byte limits. Locale tests compare English/Arabic keys and variables.

Seven new real PostgreSQL tests cover:

1. Upgrade/downgrade/model parity while preserving an earlier source snapshot, successful route output IDs, and automation operation.
2. Duplicate durable receipts and concurrent planners producing one request/contact action.
3. Concurrent duplicate captcha callbacks consuming exactly one attempt and receipt.
4. Dispatch waiting for a committed head change and cancelling stale work.
5. Policy save and already dispatched completion without a lock-order deadlock.
6. Foreign-key rejection of cross-bot/cross-channel member operation references.
7. Concurrent confirmation releasing one SQL bulk snapshot once, with one audit event.

The combined run also executes all earlier Channel Manager integration files, including real Redis sender budgets and prior migration/concurrency contracts.

## Reproduction

```text
ruff check .
mypy
python -X utf8 -m pytest -q tests/bots/channelmanager tests/test_locales.py -p no:cacheprovider
python -X utf8 -m pytest -q -p no:cacheprovider
```

Real-service variables are `TEST_CHM_DATABASE_URL`, `TEST_CHM_PUBLISH_DATABASE_URL`, `TEST_CHM_ADVANCED_DATABASE_URL`, `TEST_CHM_AUTOMATION_DATABASE_URL`, `TEST_CHM_MEMBERS_DATABASE_URL`, and `TEST_CHM_REDIS_URL`. PostgreSQL URLs use `postgresql+asyncpg`, loopback hosts, and dedicated `channelmanager_phase1_test` through `channelmanager_phase5_test` database prefixes respectively. Tests downgrade/upgrade revisions and truncate Channel Manager tables; never use production/shared databases. Redis checks use isolated key prefixes.

```text
python -X utf8 -m pytest -q tests/integration/test_channelmanager_foundations.py tests/integration/test_channelmanager_publishing.py tests/integration/test_channelmanager_advanced.py tests/integration/test_channelmanager_automation.py tests/integration/test_channelmanager_members.py -p no:cacheprovider
```

Use a fresh writable `--basetemp` on Windows. Pytest temporary-directory metadata may require execution outside the sandbox. No credentials or application environment need to change.

## Release boundaries

This is the standalone standard join-request subset. Query-only processing, newer welcome permissions, arbitrary historical member enumeration, invitation-growth gates, campaigns, branded senders, entitlement expiry, and general erasure/retention UI remain outside Phase 5. Paid-plan lifecycle and branded bots remain Phase 6; live compatibility and the combined production release remain Phase 0/7.

Private callbacks are interaction evidence, not a claim of lasting messaging permission; signed user starts establish the supported continuation. Direct public joins cannot be pre-gated by this approval API. Generation/deadline fences cover known committed state, while native changes racing a user-addressed API request remain an external atomicity limitation. Unknown effects require reconciliation; exactly-once remote delivery is not claimed.

Requests, leads, callback receipts, and audit/action records contain private IDs/contact/profile data and need deployment retention/backup controls. Explicit disconnect/removal can interrupt cleanup. Rollback should pause claims and retain durable request/ban/action records rather than drop tables.
