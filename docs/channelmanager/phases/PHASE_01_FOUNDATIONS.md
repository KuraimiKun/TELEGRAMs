# Phase 1: Platform foundations and channel authorization

**Status:** Complete: implementation and automated verification. **Estimate:** 5–7 engineer-days. **Dependency:** Phase 0.

Started directly at the user's request. Phase 0's live Telegram/client compatibility matrix remains planned; Phase 1 uses the existing SDK's channel setup and messaging primitives without advertising the advanced capabilities awaiting that validation.

Goal: establish a safe, durable module on which publishing and membership workflows can run. Covers CH-01 and the foundations for CH-11 and CH-18.

## Tasks

- [x] Register `bots/channelmanager/` with `chm_` tables, `CHANNELMANAGER_` configuration, `chm:` callbacks, fresh routers, and English/Arabic locales.
- [x] Add channel, role, inbox, operation, event, and minimal entitlement/limit models with migrations and enforced bot/channel scoping.
- [x] Implement channel connection and lifecycle menus: validate the operator, inspect bot rights, and handle removal, demotion, reconnection, and missing permissions.
- [x] Add narrow priority channel-membership routers and explicit update subscriptions. Keep channel handlers independent of an individual `BotUser` sender.
- [x] Generalize the existing Group Guard-specific durable webhook acknowledgement into an SDK capability; preserve its current behavior and defaults for other bots.
- [x] Persist relevant inbound events before acknowledgement. Deduplicate by bot/update and create domain changes plus outgoing intents transactionally.
- [x] Implement fenced operation claims, dispatch/outcome records, bounded retries, uncertain outcomes, and operator visibility.
- [x] Register the delivery worker and central scheduled sweeps; use namespaced Redis coordination and shared sender/chat rate budgets.
- [x] Add basic admin diagnostics and internal audit events. Keep platform administration separate from channel-operator permissions.

## Deliverables

- Discoverable bot skeleton with a working channel setup flow.
- Initial schema, migrations, durable ingress/outbox, worker entry point, and focused fixtures/tests.
- Documented configuration and recovery/status behavior.

Primary integration areas: the SDK module contract, dispatcher, gateway, child serving, scheduler, and the new module's authorization/ingress/outbox code. See [repository findings](../DEVELOPMENT_PLAN.md#repository-findings-and-reuse).

## Verification and exit criteria

- [x] Connecting one channel grants no access to another channel or bot namespace.
- [x] Forged callbacks, outsiders, stale menus, and revoked rights fail safely.
- [x] Duplicate updates create one logical operation; database failure prevents premature acknowledgement.
- [x] Worker crashes and lost leases preserve pending or uncertain work for inspection.
- [x] Discovery, localization, migrations, and existing bot ingress behavior pass focused regression checks.

Evidence and limitations: [Phase 1 verification](../PHASE_01_VERIFICATION.md). Runtime setup and recovery: [operations guide](../OPERATIONS.md).

Next: [Phase 2: Publishing MVP](PHASE_02_PUBLISHING_MVP.md).
