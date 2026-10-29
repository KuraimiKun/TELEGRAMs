# Phase 5: Member onboarding, departure, and channel events

**Status:** Implemented with automated verification; live compatibility/canary remains a release gate. **Original estimate:** 8–12 engineer-days. **Dependency:** Phase 4 in the default sequence; technically Phase 1 plus reusable publishing components.

Goal: manage admission through one durable workflow and handle subsequent channel events. Covers CH-08, CH-09, CH-11, CH-12, and CH-15. Invitation growth and branded senders follow in Phase 6.

## Tasks

- [x] Persist observed join requests with request generations, contact deadlines, gate state, and final outcomes.
- [x] Configure welcome content through the reusable composer; attempt contact promptly and provide signed start links for continued interaction.
- [x] Implement immediate, timed, manual, and bulk approval over the persisted observed queue.
- [x] Add mathematical captcha, introductory content, bounded attempts, expiration, and safe callback ownership checks.
- [x] Add ordered required-chat checks using channel-scoped configuration and fresh eligibility checks before admission.
- [x] Add total block, join-rate, name/username, alphabet, and language filters with defined outcomes and configuration errors.
- [x] Orchestrate all enabled gates in one state machine; one timer must not bypass another unmet condition.
- [x] Add reachable private goodbye delivery and optional voluntary-departure bans, including linked-group action and durable timed unbans.
- [x] Add configurable external event logging with language/event selectors and an independently retained internal audit trail.
- [x] Add allowlisted service-message cleanup and visible unsupported/failure outcomes.
- [x] Record enough sender/channel interaction evidence for Phase 6 leads without treating join events alone as private-chat interaction.

## Deliverables

- Join-request/challenge/required-chat models and workflow services.
- Welcome, approval, filters, goodbye, event-log, and cleanup menus in English/Arabic.
- Expiry/recovery sweeps, operational counters, and admission/departure test scenarios.

## Verification and exit criteria

- [x] Repeated or reordered recorded updates cannot bypass gates or reset a completed request.
- [x] Expiry for an older request cannot reject a newer committed rejoin generation; the native API race boundary is documented.
- [x] Unreachable/blocked users and expired contact opportunities produce bounded, understandable outcomes.
- [x] Bulk approval reports stale/skipped requests and processes only the recorded queue.
- [x] Voluntary departure, administrator removal, and our own enforcement remain distinguishable without event loops.
- [x] Timed unban/cleanup obligations survive restart and ordinary policy changes; paid entitlement lifecycle remains Phase 6.

Walkthrough and limits: [member workflows](../MEMBER_WORKFLOWS.md). Schema: `0023_chm_members`. Evidence: [Phase 5 verification](../PHASE_05_VERIFICATION.md).

Milestone: R3 membership complete for the standalone sender.

Next: [Phase 6: Collaboration, growth, and billing](PHASE_06_GROWTH_AND_BILLING.md).
