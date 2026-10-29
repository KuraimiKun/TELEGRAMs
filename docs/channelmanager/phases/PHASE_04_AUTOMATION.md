# Phase 4: Auto-complete and filtered forwarding

**Status:** Implemented, with automated verification. Live compatibility/canary remains a release gate. **Original estimate:** 6–9 engineer-days. **Dependency:** Phase 3.

Goal: automate manually published source-channel content. Covers CH-06, CH-13, and the shared keyword subsystem.

## Tasks

- [x] Add named auto-complete sets with explicit priority, activation state, channel ownership, and typed rule configuration.
- [x] Implement trigger/excluded words, media selectors, removable leading trigger commands, and a documented bounded keyword contract. Phase 0 live validation remains outstanding.
- [x] Add header/signature, buttons, attachments, separator stickers, vote buttons, deletion timers, and word replacement for supported message types.
- [x] Transform canonical content while preserving entities and preventing repeated prefix/suffix additions on bot-generated edit events.
- [x] Add channel/group forwarding destinations, permission checks, filters, copy/forward choices, and original-versus-transformed payload selection.
- [x] Reject routing cycles during configuration and enforce runtime provenance/hop protection.
- [x] Add album-aware collection and tested fallbacks; rebuild or omit destination-specific callbacks rather than copying invalid ones.
- [x] Implement explicit optional source-edit propagation for copies; reject attributed-forward propagation and keep automatic deletion propagation disabled.
- [x] Record independent route/edit results and integrate shared budgets, retry handling, audit, and operator diagnostics.

## Deliverables

- Auto-complete editor, bounded matcher, transformation pipeline, and forwarding-route management.
- Models/migrations and examples for original/transformed forwarding behavior.
- Loop, formatting, album, duplicate-event, and destination-failure tests.

## Verification and exit criteria

- [x] A manual source post is enriched and routed once per intended content version in automated tests.
- [x] The bot's own edits/forwards cannot create a feedback loop in the supported workflows.
- [x] Matching-set precedence and word-replacement behavior are deterministic.
- [x] Media limitations, destination rights loss, and protected-content failures are visible.
- [x] A failure in one destination does not stop reporting or successful delivery to other destinations.
- [x] Entity positions remain valid after transformations, including emoji and Arabic text.

Evidence and boundaries: [Phase 4 verification](../PHASE_04_VERIFICATION.md). Operator walkthrough and exact keyword/media/propagation contracts: [source automation](../SOURCE_AUTOMATION.md). Revision: `0022_chm_automation`.

Milestone: R2 publishing automation complete.

Next: [Phase 5: Member workflows](PHASE_05_MEMBERSHIP.md).
