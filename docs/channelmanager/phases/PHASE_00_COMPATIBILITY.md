# Phase 0: Compatibility and behavior contracts

**Status:** Offline behavior contracts and compatibility matrix recorded through Phase 7. Native/client verification is deferred at the user's request because no token exists. See [matrix](../COMPATIBILITY_MATRIX.md) and [release evidence](../PHASE_07_VERIFICATION.md). **Original estimate:** 3–4 engineer-days. **Dependency:** None.

Goal: establish what the deployed Telegram stack supports and define the behavior needed by later phases. Covers the uncertainties affecting all CH features.

## Tasks

- [x] Record Python/aiogram and the identified immutable Bot API image candidate; its runtime test remains deferred.
- [x] Build the versioned capability matrix for all listed content, interaction, member and sender families.
- [x] Separate automated evidence, unsupported/untested capabilities and explicit user-visible fallbacks from native observations.
- [x] Define and test owner/native/virtual rights, own/all ceilings, revocation and adoption.
- [x] Define/test scheduling, timezone/DST, downtime and recurring replacement behavior.
- [x] Define/test keyword, precedence, vote and route edit/deletion behavior.
- [x] Record quotas, unpublished configurable prices, explicit campaign consent, full-manager branded scope and external interoperability boundary.

## Deliverables

- Versioned compatibility matrix with test environment, evidence, and fallback decisions.
- Representative channel/member/callback update fixtures.
- Behavior decisions linked from the shared [workflow contracts](../DEVELOPMENT_PLAN.md#workflow-contracts).
- Revised estimates where compatibility results change the work.

## Verification and exit criteria

- [ ] Every R1 dependency has either demonstrated support or a documented fallback suitable for the MVP.
- [x] Unverified advanced capabilities remain explicitly marked and are not advertised as implemented.
- [x] Permission, scheduling, rule, and delivery contracts have focused tests.
- [x] Missing token, container/native canary and external dependencies are recorded without credentials.

Next: [Phase 1: Platform foundations](PHASE_01_FOUNDATIONS.md).
