# Phase 7: Production readiness and rollout

**Status:** Offline readiness implemented and verified on 29 October 2026. The user explicitly deferred the live canary because no bot token exists. Container/native client verification and production rollout remain deferred, not passed. See [evidence](../PHASE_07_VERIFICATION.md), [release/rollback runbook](../RELEASE_RUNBOOK.md), and [compatibility matrix](../COMPATIBILITY_MATRIX.md). **Original estimate:** 3–6 engineer-days. **Dependencies:** Phases 0–6.

Goal: verify the combined product, make failures manageable, and release it in controlled steps. This phase consolidates evidence; earlier phases must already include focused tests and any checks needed for their canaries.

## Tasks

- [x] Complete and link automated evidence in the shared verification matrix; native visual/client rows remain explicitly deferred.
- [x] Run PostgreSQL 16 migration/constraint/locking and Redis 7 lease/replica tests, including standalone/child recorded webhook flows.
- [x] Verify crash/dispatch/lost-lease/rate/rights/partial/stale recovery, including bounded stuck calls and cleanup during maintenance.
- [ ] Validate visual flows with private test channels and the tested Telegram clients, including Arabic content and personal-reveal fallbacks.
- [x] Measure offline campaign load, concurrent interactive drafts, duplicate count and queue lag using real PostgreSQL/Redis. Native-network capacity remains a canary measurement.
- [x] Finish worker/profile, progress health, rollout gates, explicit image configuration, diagnostics, alerts and deployment instructions.
- [ ] Run the selected immutable Bot API image in its container/native canary; registry metadata alone is not runtime evidence.
- [x] Provide scoped operator views/runbooks for failed/uncertain work, admissions, cleanup, payment/refund and sender failures, with bounded fleet metrics.
- [x] Exercise a custom-format backup/restore into a separate database and gated rollback while preserving ledger/audit/cleanup state.
- [ ] Roll out through internal channels, a small publishing canary, automation, membership, then billing/branded senders using feature flags.

## Verification commands

After installing development dependencies, run discovery, lint, type checks, focused tests, locale checks, and the full suite as listed in the shared plan. Run integration/runtime suites against disposable services using [the SDK guide](../../BOT_SDK.md) and [operations guide](../../OPERATIONS.md). Record the actual commands, environment, and results; do not mark a check passed merely because it is listed.

## Deliverables

- Versioned release evidence and resolved compatibility/support matrix.
- Deployment, monitoring, recovery, and rollback runbooks.
- Canary results and documented remaining product limitations.

## Exit criteria

- [x] No unresolved critical failure remains in the automated scope; native/container acceptance remains deferred.
- [x] Existing bots pass the full default regression suite and remain independently configured.
- [x] Operators have scoped views and recovery procedures that preserve uncertain effects.
- [x] Gated rollback stops new effects and retains financial receipts, cleanup and durable records in automated verification.
- [ ] Canary behavior and measured capacity meet the recorded release criteria.

**Milestone: offline readiness complete; production release awaits the deferred native/container canary and explicit rollout. Original total planning range: 45–68 engineer-days.**

Return to the [phase roadmap](README.md).
