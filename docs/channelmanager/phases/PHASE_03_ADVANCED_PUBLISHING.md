# Phase 3: Advanced publishing and calendars

**Status:** Implemented; automated evidence is recorded in [Phase 3 verification](../PHASE_03_VERIFICATION.md). **Original estimate:** 6–9 engineer-days. **Dependency:** Phase 2.

The [advanced publishing guide](../ADVANCED_PUBLISHING.md) defines supported syntax, temporal policy, and fallbacks. Live Telegram/client/server compatibility and production rollout remain Phase 0/7 work.

Goal: make frequent and repeated publishing efficient. Covers CH-04 and CH-05, plus advanced CH-02, CH-03, and CH-14.

## Tasks

- [x] Extend formatting through tested legacy/new Markdown subsets and custom shorthand parsers; translate shorthand before transport.
- [x] Add structured popup/alert, membership-aware, copy, explicit comments-link, and share buttons. Styling/custom button emoji remain disabled pending live compatibility evidence.
- [x] Add custom vote buttons, counts, vote changes/closure, and concurrency-safe per-user state, separate from native reactions. Preserve votes and closure on ordinary content edits.
- [x] Add named button/channel presets and default vote labels/signatures. Snapshot selected defaults into post versions.
- [x] Implement recurrence intervals, anchor time, weekdays/month days, overnight windows, start/end dates, pause/resume, and a next-five-occurrences preview.
- [x] Add per-occurrence deletion and success-first previous-occurrence replacement with independent deliveries and durable cleanup obligations.
- [x] Support shared recurring templates with synchronized future content and creator-controlled target changes, with live authorization across targets and stale unsent-occurrence cancellation.
- [x] Build multipost collection with shared/per-item/omitted defaults, restart-current, add/remove/review, cancellation, and batch progress.
- [x] Add named weekly calendars, atomic slot reservations, and sequential batch scheduling from now or a future start.

## Deliverables

- Advanced composer interactions and reusable presets.
- Recurrence, occurrence, batch/calendar, vote, and preset services/models with migrations.
- Automated temporal/concurrency tests and localized management menus.

## Verification and exit criteria

- [x] DST ambiguity, month edges, overnight windows, downtime policy, and duplicate sweeps produce the specified occurrences.
- [x] Two batches cannot reserve the same active calendar slot; stale previews require review.
- [x] Shared edits/target changes cannot extend an operator's permissions.
- [x] Repeated callbacks cannot inflate votes; closed ballots stay closed through ordinary content edits.
- [x] A failed/uncertain replacement send preserves the prior successful occurrence; cleanup planning survives interruption and blocked older posts.
- [x] Unsupported button/media combinations have documented fallbacks and validation.

Milestone: R2 publishing automation, part 1.

Next: [Phase 4: Source automation](PHASE_04_AUTOMATION.md).
