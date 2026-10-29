# Phase 3 implementation and verification

Implemented 28 October 2026 in the working tree based on repository commit `10e9b83`. This extends the [publishing MVP](PHASE_02_VERIFICATION.md). Instructions and supported subsets are in [advanced publishing](ADVANCED_PUBLISHING.md).

## Implemented scope

- Legacy/new Markdown subsets and the guide's custom HTML shorthand, converted to canonical text/entities before transport.
- Structured popup, alert, membership-aware, native copy, explicit discussion-link, share, and custom vote buttons. Shared/protected combinations and unsupported styles have bounded validation/fallbacks.
- Per-message/version single-choice votes, SQL serialization, idempotent callbacks, vote changes, closure, durable count refresh, and preserved votes/closure across ordinary content edits.
- Personal named button/channel sets, editing/deletion, native scope checks, channel default vote labels, signature/default snapshots, and composer integration.
- IANA wall-clock recurrence, anchored intervals, weekday/month-day filters, overnight windows, date bounds, explicit DST policy, next-five preview, pause/resume, missed-occurrence skipping, and creator-controlled target changes.
- Independent occurrence posts and deliveries, immutable root-version provenance, per-occurrence deletion, success-first previous-occurrence replacement, and durable replacement-planning recovery with ordered post locks.
- Multipost collection, shared/per-item/omitted buttons and votes, shared publication flags/timers, restart/remove/review/add-more, explicit cancellation, progress, and confirmed scheduling.
- Named weekly calendars, saved timezone/UTC reservations, atomic allocation, stale availability/content detection, and release of unsent slots on cancellation/rescheduling.
- Ten new tables and delivery follow-up/replacement fields in revision `0021_chm_advanced`; settings, worker integration, actor/generation-bound English/Arabic menus, and runbooks.

## Verification results

| Check | Result |
|---|---|
| Final bot/locale checks | 144 passed; 31.25 seconds |
| Complete default regression suite | 1,701 passed, 143 skipped; 632.93 seconds |
| PostgreSQL/Redis integration | 14 passed; 10.90 seconds, across all three phase integration files |
| Ruff / Mypy | Passed; Mypy checked 358 source files |

The full regression run began before the final ballot-preservation and recurring-template invalidation/fencing refinements. The focused and real-service checks above were rerun against the final code. The full suite emitted one existing PyMuPDF `fitz` deprecation warning. Temporary test services were stopped after verification.

Temporal tests cover month edges, AND filters, overnight windows, DST gaps/folds, date bounds, and occupied calendar slots. Functional/menu tests cover formatter validation, UTF-16 transformations, public callback scope, live membership, voting changes/closure/versioning, default/preset snapshots, recurrence previews and confirmation, duplicate sweeps, restarts, downtime, rights loss, shared edits/targets, batch defaults and per-item input, immediate/future/calendar plans, stale confirmations, cancellation, quota rollback, follow-up serialization, and durable replacement recovery.

Real PostgreSQL checks exercise migration upgrade/downgrade/model parity while preserving a Phase 2 sent message and cleanup status; competing calendar plans; concurrent repeated votes and closed-ballot preservation across edits; recurrence quota/duplicate sweep serialization; cleanup planning while an older occurrence is locked; and generation refresh after a previously cached read. The prior Phase 1/2 integration files additionally cover ingress/job claims, namespace constraints, scheduling quotas/restart, dispatch mutation locking, and real Redis sender budgets.

All Telegram calls use `RecordingSession`. No live bot messages, credentials, webhooks, production data, or deployment were changed. Disposable services use PostgreSQL 14.24 and Redis 6.0.16 in WSL; the Compose PostgreSQL 16/Redis 7 combination remains a canary check.

## Reproduction

```text
ruff check .
mypy
python -X utf8 -m pytest -q tests/bots/channelmanager tests/test_locales.py -p no:cacheprovider
python -X utf8 -m pytest -q -p no:cacheprovider
```

Set `TEST_CHM_ADVANCED_DATABASE_URL` to a disposable loopback `postgresql+asyncpg` database whose name starts with `channelmanager_phase3_test`. The tests downgrade/upgrade Channel Manager revisions and truncate its Channel Manager tables. The prior integration files use separate `channelmanager_phase1_test` and `channelmanager_phase2_test` databases through `TEST_CHM_DATABASE_URL` and `TEST_CHM_PUBLISH_DATABASE_URL`, plus `TEST_CHM_REDIS_URL` for isolated Redis checks.

```text
python -X utf8 -m pytest -q tests/integration/test_channelmanager_advanced.py tests/integration/test_channelmanager_publishing.py tests/integration/test_channelmanager_foundations.py -p no:cacheprovider
```

Use a fresh writable `--basetemp` on Windows if required. The harness excludes the real workspace `.env`. Applying this migration to production and dropping these tables are not part of verification; operational rollback should pause claims and retain durable records.

## Remaining release work

The implementation uses conservative subsets: single media, explicit comments URLs, standard button labels, one choice per voter/message, success-first replacement, and new-only calendar/default snapshots. Styling/custom button emoji, automatic discussion-thread mapping, rich/ephemeral layouts, native polls, and albums are not advertised as tested.

Phase 0 live compatibility and the relevant production-readiness/canary gates remain outstanding. Phase 4 adds source automation; membership, collaboration/growth/billing, branded bots, and the combined release remain later phases.
