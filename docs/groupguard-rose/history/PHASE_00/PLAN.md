# Reconstructed project plan

This file replaces absent attached PLAN.md for planning only. Objective: extend bots/groupguard and its factory template to all publicly documented Rose features while preserving existing behavior/data. Phase 0 audits only; stop before implementation. Phases and acceptance gates are in DECISIONS.md; contracts/schema/compatibility in ARCHITECTURE.md; behavior evidence in FEATURE_MATRIX.csv and .md; baseline in BASELINE.md.

Source gate: read every reachable Rose functional/explanation section and related current official Bot API reference; create stable independently testable behavior IDs, including command aliases/modifiers, rights, defaults, private flows, language roster and clone annotations. No inaccessible behavior is silently excluded. Current source coverage is incomplete because network proxy denies both documentation sites.

Delivery gates for every later phase: implement authorized scope only, preserve legacy fixtures/tenant isolation, meaningful mocked+PostgreSQL/Redis checks as needed, inline self-contained report with failures/unrun checks/open questions, save complete artifacts, stop for review. No production actions implied by a planning artifact. Phase 12 requires cumulative acceptance and independent source review; earlier report claims are planning evidence, not independent certification of unseen code.
