# Phase 6: Collaboration, growth, billing, and branded bots

**Status:** Implemented and verified in the working tree on 29 October 2026. Live compatibility and release remain Phase 0/7 gates. See [verification](../PHASE_06_VERIFICATION.md) and [operations](../GROWTH_AND_BILLING.md). **Original estimate:** 8–12 engineer-days. **Dependencies:** Phases 3–5.

Goal: complete the advanced product families. Covers CH-07, CH-10, CH-16, CH-17, and CH-18, plus advanced CH-08 and CH-13. The sections below divide the phase into reviewable steps; they do not add separate estimates to the overall range.

## Step 6A: Delegation and locked content

- [x] Add channel-scoped virtual admins with create, own/all edit/delete, schedule, and optional settings permissions.
- [x] Add verified delegation/revocation and adoption of queued work whose creator loses access.
- [x] Configure locked/unlocked post versions and ordered membership requirements.
- [x] Implement the signed private-chat fallback with fresh access checks; live ephemeral-response compatibility remains Phase 0/7.
- [x] Test that an unlock never exposes the secret version through a global public-message edit.

## Step 6B: Leads, campaigns, and invitation growth

- [x] Add sender-specific, channel-associated leads with private-interaction evidence and opt-out state.
- [x] Build campaign audience/content preview, recipient snapshot, explicit send action, cancellation, and per-recipient outcomes.
- [x] Handle restart and uncertain deliveries without blind replay or cross-channel audience expansion.
- [x] Add Must Share invitation attribution, distinct invitee credit, thresholds, dynamic progress content, and optional invitation-only timeout bypass.
- [x] Prevent self-referrals, repeated credit, and stale request generations from advancing admission.

## Step 6C: Per-channel Stars plans

- [x] Add immutable plan versions, server-issued channel invoices, entitlement periods, and payment-linked grant records.
- [x] Validate payer, resource authorization, quote, amount, and currency at checkout/fulfillment; handle late and duplicate payments.
- [x] Grant channel entitlement atomically through the shared payment service and add channel-specific refund reconciliation.
- [x] Add renewals, expiry, impact previews, and non-destructive quota enforcement on downgrade; retain cleanup obligations.
- [x] Complete prorated upgrades and scheduled downgrades after the basic prepaid lifecycle passes its tests.

## Step 6D: Branded senders and native interactions

- [x] Register the selected factory template/sender role through existing encrypted-token ownership and lifecycle services.
- [x] Add verified channel-to-sender bindings, tested cross-bot media rejection with explicit upload-to-sender fallback, and routing between onboarding and native menu/feedback interactions.
- [x] Include edited-channel subscriptions, factory sweeps, sender invalidation, rotation, pause/delete, and residual cleanup reporting.
- [x] Keep control-bot billing and child namespaces aligned with the existing factory contract.
- [x] Require an explicit migration for a token already hosted elsewhere; external Modular interoperability remains separately scoped.

## Deliverables and exit criteria

- [x] Collaboration, unlock, lead/campaign, invitation, invoice/entitlement, and sender models/services have migrations and localized UI.
- [x] Cross-channel/cross-child permissions and campaign audience isolation pass.
- [x] Private reveal confidentiality, blocked-recipient handling, invitation abuse cases, and child lifecycle recovery pass.
- [x] Duplicate/wrong/late payments, refunds, expiry, and downgrade preserve a consistent channel ledger.
- [x] Each step has focused tests and operator recovery instructions.

Milestone: R4 proposed feature scope complete; final combined production verification remains in Phase 7. Reassess this phase's estimate after Phase 0 confirms branded-bot and billing scope.

Next: [Phase 7: Production readiness](PHASE_07_PRODUCTION_READINESS.md).
