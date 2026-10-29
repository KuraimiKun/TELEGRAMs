# Channel Manager research and implementation proposal

Prepared 28 October 2026 against repository commit `10e9b83`.

The proposal adds an independent `channelmanager` bot to this platform, with optional branded factory bots later. It follows the capabilities documented by Channel Help while using our own interface and existing platform services.

- [Feature analysis](FEATURE_ANALYSIS.md): documented capabilities, commercial model, uncertainties, and product conclusions.
- [Development plan](DEVELOPMENT_PLAN.md): shared architecture, repository integration, data model, and workflow contracts.
- [Phase roadmap](phases/README.md): eight ordered phases with separate task lists, dependencies, estimates, deliverables, and completion gates.
- [Setup and recovery](OPERATIONS.md): configuration, worker startup, publishing walkthrough, and failure handling.
- [Phase 1 verification](PHASE_01_VERIFICATION.md): implementation scope, automated results, and validation boundaries.
- [Phase 2 verification](PHASE_02_VERIFICATION.md): publishing scope, concurrency checks, and supported-format boundaries.
- [Advanced publishing](ADVANCED_PUBLISHING.md): formatting/buttons, votes, presets, recurring posts, multipost, and weekly calendars.
- [Phase 3 verification](PHASE_03_VERIFICATION.md): temporal, concurrency, menu, and migration evidence.
- [Source automation](SOURCE_AUTOMATION.md): auto-complete rules, bounded keywords, album handling, routing, and edit propagation.
- [Phase 4 verification](PHASE_04_VERIFICATION.md): source-event, failure, loop, migration, and concurrency evidence.
- [Member workflows](MEMBER_WORKFLOWS.md): admission gates, contact reachability, bulk release, departure enforcement, and event tools.
- [Phase 5 verification](PHASE_05_VERIFICATION.md): admission, callback, cleanup, migration, and concurrency evidence.
- [Growth and billing](GROWTH_AND_BILLING.md): publishing teams, private reveals, consented campaigns, invitation gates, channel plans, branded senders and recovery.
- [Phase 6 verification](PHASE_06_VERIFICATION.md): authorization, privacy, payment, factory and real-service evidence.
- [Phase 7 verification](PHASE_07_VERIFICATION.md): full regression, PostgreSQL 16/Redis 7, replica, load and restore evidence.
- [Release and rollback](RELEASE_RUNBOOK.md): staged gates, progress health, diagnostics, canary sequence and preserved financial/cleanup state.
- [Compatibility matrix](COMPATIBILITY_MATRIX.md): supported contracts/fallbacks and explicitly deferred native/container observations.

Recommended first release: channel connection, permission checks, a reusable post composer, drafts, immediate and scheduled publication, editing, deletion, and delivery reporting. Add automation and member onboarding in subsequent releases.

Phases 1–6 and Phase 7 offline readiness are implemented in `bots/channelmanager/`, including the full-manager factory template. Native/container canary and production rollout are deferred: the user has not created the token and explicitly skipped live verification. Production credentials and deployment remain unchanged.
