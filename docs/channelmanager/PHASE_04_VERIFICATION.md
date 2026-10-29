# Phase 4 implementation and verification

Implemented 28 October 2026 in the working tree based on repository commit `10e9b83`, extending Phases 1–3. The [operator walkthrough](SOURCE_AUTOMATION.md) defines supported behavior and limits; the [phase checklist](phases/PHASE_04_AUTOMATION.md) records scope completion.

## Implemented scope

- Named channel-scoped auto-complete sets with typed specifications, priority, activation, actor adoption, quotas, stale-menu protection, and audit events.
- Bounded Unicode keywords: trigger/exclude alternatives, whole tokens, exact quoted messages, unordered conjunctions, token wildcards, case settings, media selectors, and removable leading commands.
- Canonical transformations preserving UTF-16 entities: headers/signatures, simultaneous token replacements, structured buttons/votes, text-to-media attachments, separator stickers, and independent deletion obligations.
- SQL source/part collection, immutable original/transformed version snapshots, independent action results, managed-source post reports, and persistent output provenance.
- Channel/group routing, native copy/forward semantics, original/transformed selection, source and destination checks, protected-source enforcement, graph-cycle rejection, and runtime path/hop fences.
- Photo/video album collection, signature-only enrichment, explicit unsupported/incomplete/layout-change holds, partial-result uncertainty, and per-item copy-edit propagation.
- Optional copy edit propagation to known remote IDs, destination-scoped route history, no default edit/deletion propagation, and no automatic replay of uncertain outcomes across later source versions.
- Existing outbox budgets, leases, worker/recovery integration, generation fences, definite-failure retry, sanitized source reports, admin diagnostics/metrics, and English/Arabic menus.
- Eight new tables, scoped automation-operation constraints, and a delivery message-ID lookup index in revision `0022_chm_automation`.

## Verification results

| Check | Result |
|---|---|
| Final focused bot/locale and all four phase real-service files | 227 passed; 55.62 seconds (207 bot/locale + 20 integration checks) |
| Complete default regression suite | 1,765 passed, 150 skipped, one wall-clock test failure; 610.61 seconds. The timing test was stabilized and rechecked as described below. |
| Final check after test-clock correction | 281 passed; 134.35 seconds (74 Group Guard + 207 Channel Manager/locale checks) |
| Ruff | `ruff check .` passed |
| Mypy | Passed; 363 source files |
| Tracked-file whitespace check | `git diff --check` passed |

All Telegram API effects use `RecordingSession`. Tests exclude the workspace `.env`. No real Telegram messages, credentials, webhooks, production data, or deployment were changed. Disposable loopback services use PostgreSQL 14.24 and Redis 6.0.16 in WSL and were stopped after verification; the Compose PostgreSQL 16/Redis 7 combination remains a release canary check.

The final focused run includes the completed album acknowledgement loop guard, live protection checks for propagated copies, and recovered mirror-edit reporting. It also reruns the prior foundation, publishing, and advanced-publishing integration files.

The full run used the final Phase 4 application code. Its sole failure was the existing Group Guard test `test_local_broadcast_rate_wait_does_not_consume_api_retry_budget[child-A]`: the fixture filled a real-time one-second bucket, and the sweep could consume a different bucket after the clock advanced. The unchanged file passed all 74 tests on immediate rerun. The test now supplies a fixed module-local clock and a longer fixture-key lifetime; production Group Guard code is unchanged. Final verification of that test-only correction and Channel Manager/locale checks is recorded below. The entire ten-minute suite was not rerun after this test-only change. The suite also emitted the existing PyMuPDF `fitz` deprecation warning.

## Evidence covered

Functional tests exercise keyword boundaries/normalization, wildcard budgets and invalid syntax, Arabic/emoji entity spans, simultaneous replacements, command removal, set precedence, original/transformed group copies, attributed-forward ordering, protected messages/chats, source vote scopes, attachments/stickers/timers, and independent destination failure/retry.

Replay and edit tests cover duplicate durable receipts, bot-generated edits/copies, album signature acknowledgements, manual edits of already enriched messages, multiple later source versions with propagation disabled or prior unknown delivery, repeated album edits retaining every remote ID, destination changes, forward-to-copy mode changes, partial album forward results, 429 deferral, unavailable sender budgets, native manual-source permissions, and recovered unknown edit reports.

Menu tests cover inactive set creation, configuration input, uploaded photo/sticker references, sample previews without source jobs, operator/generation-bound activation, stale/foreign callbacks, unsupported forward-edit configuration, cancellation, route controls, and the Telegram callback size limit. Locale checks verify matching English/Arabic keys and variables.

The six new real PostgreSQL tests verify:

1. Upgrade/downgrade/model parity while preserving an earlier sent delivery, its replacement flag, and an existing operation.
2. Concurrent duplicate receipt submission, ingress claims, and source planners producing one source snapshot/action set.
3. Competing route activations serialized to reject a cycle.
4. Database rejection of cross-bot/cross-source-channel automation operation references.
5. Dispatch waiting for a source-row mutation and cancelling stale work after the committed version change.
6. Configuration invalidation and an already dispatched completion without a lock-order deadlock.

## Reproduction

```text
ruff check .
mypy
python -X utf8 -m pytest -q tests/bots/channelmanager tests/test_locales.py -p no:cacheprovider
python -X utf8 -m pytest -q -p no:cacheprovider
```

For real-service checks, set these variables to dedicated disposable loopback databases/Redis:

| Variable | Required database-name prefix |
|---|---|
| `TEST_CHM_DATABASE_URL` | `channelmanager_phase1_test` |
| `TEST_CHM_PUBLISH_DATABASE_URL` | `channelmanager_phase2_test` |
| `TEST_CHM_ADVANCED_DATABASE_URL` | `channelmanager_phase3_test` |
| `TEST_CHM_AUTOMATION_DATABASE_URL` | `channelmanager_phase4_test` |
| `TEST_CHM_REDIS_URL` | Isolated local Redis; unique test keys |

Database URLs use `postgresql+asyncpg`. Tests downgrade/upgrade Channel Manager revisions and truncate its test tables, so never point them at a shared or production database.

```text
python -X utf8 -m pytest -q tests/integration/test_channelmanager_foundations.py tests/integration/test_channelmanager_publishing.py tests/integration/test_channelmanager_advanced.py tests/integration/test_channelmanager_automation.py -p no:cacheprovider
```

Windows runs may require a fresh writable `--basetemp` and execution outside the sandbox for pytest's protected temporary directory metadata. No application environment or credentials need to change.

## Remaining release work

Phase 0 live Telegram/client compatibility and production-readiness/canary gates remain outstanding. Supported media and callbacks are explicitly bounded: photo/video album signatures, single basic media, copy-only edit propagation, native live-source attribution, omitted source-bound destination callbacks, and no automatic deletion propagation or historical replay. The system does not claim exactly-once remote delivery.

Automation snapshots retain private source content and require a deployment retention/backup policy. External permission changes can race network requests despite fresh checks. General cross-bot loop detection, arbitrary historical message adoption, membership workflows, collaboration/growth/billing, branded bots, and the combined release remain outside this phase. Operational rollback should pause claims and retain source/action/cleanup records rather than drop tables.
