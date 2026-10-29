# Channel Manager phase roadmap

Status: Phases 1–6 and [Phase 7 offline readiness](../PHASE_07_VERIFICATION.md) are implemented. Earlier evidence is recorded for the [foundations](../PHASE_01_VERIFICATION.md), [publishing MVP](../PHASE_02_VERIFICATION.md), [advanced publishing](../PHASE_03_VERIFICATION.md), [source automation](../PHASE_04_VERIFICATION.md), [member workflows](../PHASE_05_VERIFICATION.md), and [growth/billing](../PHASE_06_VERIFICATION.md). Native/container canary and rollout are deferred: the user explicitly skipped live work because no token exists. See the [release runbook](../RELEASE_RUNBOOK.md).

Follow the phases in order. Each phase document contains its scope, tasks, deliverables, verification, and exit criteria. The [development plan](../DEVELOPMENT_PLAN.md) defines the shared architecture and workflow contracts; the [feature analysis](../FEATURE_ANALYSIS.md) defines the CH feature IDs.

| Phase | Deliverable | Depends on | Estimate | Release milestone |
|---|---|---|---|---|
| [0: Compatibility and contracts](PHASE_00_COMPATIBILITY.md) | Tested capability matrix and agreed implementation behavior | None | 3–4 days | R1 preparation |
| [1: Platform foundations](PHASE_01_FOUNDATIONS.md) | Registered bot, channel authorization, durable processing | P0 | 5–7 days | R1 preparation |
| [2: Publishing MVP](PHASE_02_PUBLISHING_MVP.md) | Complete basic publishing workflow | P1 | 6–9 days | R1 publishing MVP |
| [3: Advanced publishing](PHASE_03_ADVANCED_PUBLISHING.md) | Recurrence, calendars, batches, advanced interactions | P2 | 6–9 days | R2 publishing automation, part 1 |
| [4: Source automation](PHASE_04_AUTOMATION.md) | Auto-complete and filtered forwarding | P3 | 6–9 days | R2 publishing automation complete |
| [5: Member workflows](PHASE_05_MEMBERSHIP.md) | Admission, welcomes, departures, channel event tools | P4 in this sequence | 8–12 days | R3 membership |
| [6: Collaboration, growth, and billing](PHASE_06_GROWTH_AND_BILLING.md) | Delegation, gated content, campaigns, plans, branded bots | P3–P5 | 8–12 days | R4 feature scope complete |
| [7: Production readiness](PHASE_07_PRODUCTION_READINESS.md) | Verified release, operational tools, canary, rollback | P0–P6 | 3–6 days | Full production release |

Estimates are engineer-days for one developer familiar with this repository, including focused tests and review. They preserve the original planning ranges: **14–20 days through the publishing MVP; 45–68 days for the complete plan**. Revise them after Phase 0. External Modular integration and major SDK/client incompatibilities are outside these ranges.

Phase 5 technically requires the Phase 1 foundations and reusable publishing components; placing it after Phase 4 is the default delivery order, not an extra architectural dependency. No parallel staffing is assumed.

## Rules for every phase

- Add migrations, English/Arabic strings, focused tests, and operator-facing failure states alongside the feature that needs them.
- Keep bot/channel isolation, permission checks, durable operation records, and shared rate budgets in every applicable path.
- Complete the phase's verification and record evidence before marking its checklist finished.
- Treat the release milestones as opportunities for a controlled canary. Apply the production-readiness gates relevant to that milestone before exposing it to users; Phase 7 is the final combined release check.
- Update this roadmap when scope, estimates, dependencies, or compatibility results change.
