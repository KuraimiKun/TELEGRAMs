# Phase 2: Publishing MVP

**Status:** Implemented; automated verification recorded below. **Original estimate:** 6–9 engineer-days. **Dependency:** Phase 1.

Implemented directly at the user's request. Live Telegram/client/server compatibility and the release canary remain Phase 0/production-readiness work. The supported MVP subset and fallbacks are described in the [operator guide](../OPERATIONS.md#publishing-boundaries-and-limits).

Goal: deliver a complete channel publishing workflow. Covers core CH-02 and CH-03, signatures from CH-14, and internal publication events from CH-11.

## Tasks

- [x] Add immutable post versions, target deliveries, and one-off schedule records using the Phase 1 operation layer.
- [x] Build the composer for text and supported basic media, caption handling, incoming Telegram entities/validated HTML, link buttons, and channel signatures.
- [x] Add preview, notification/link-preview/protection settings, primary-channel-only replies, and optional post-publication pinning. Live compatibility remains unverified; the guide records the conservative subset and fallbacks.
- [x] Implement saved drafts and per-channel sent/scheduled lists with pagination, ownership checks, and clear status labels.
- [x] Support immediate or scheduled publication to one or more authorized channels. Show the target/time summary before committing work.
- [x] Add content/media edits, rescheduling, publish-now, explicit copy-to-new-draft/share-link actions, and generation-based cancellation of stale jobs.
- [x] Separate remote deletion from detaching a management record; support deletion scheduling and reminder-only outcomes where required.
- [x] Record per-target successes, failures, remote IDs, and uncertain outcomes. Keep pin/deletion failures distinct from successful publication.
- [x] Enforce configured limits transactionally and expose usable recovery messages in both languages.

## Deliverables

- Working channel connection → compose → save/schedule → publish → edit → delete workflow.
- Reusable renderer and library services for subsequent phases.
- Focused publishing tests, migrations, localized menus, and an operator walkthrough.

## Verification and exit criteria

- [x] Preview and published content use the same renderer; automated fixtures cover supported formats, emoji, and Arabic text.
- [x] Scheduled work survives a rebuilt service context; edits/cancellation invalidate obsolete jobs and serialize with dispatch.
- [x] Multi-channel partial failures are reported without blindly resending successful or uncertain destinations.
- [x] Own/all permissions apply consistently to draft, scheduled, and published post actions.
- [x] Deletion, detach, rights loss, unsupported media, rate limits, and interrupted sends have tested outcomes.

Evidence and limitations: [Phase 2 verification](../PHASE_02_VERIFICATION.md). Runtime walkthrough: [operations guide](../OPERATIONS.md).

**Milestone: R1 publishing MVP. Cumulative estimate: 14–20 engineer-days.** Apply the relevant operational/canary checks from [Phase 7](PHASE_07_PRODUCTION_READINESS.md) before exposing this milestone to users.

Next: [Phase 3: Advanced publishing](PHASE_03_ADVANCED_PUBLISHING.md).
