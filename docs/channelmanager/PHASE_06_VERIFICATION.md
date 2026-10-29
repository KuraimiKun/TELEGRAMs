# Phase 6 implementation and verification

Implemented 29 October 2026 in the working tree based on repository commit `10e9b83`, extending Phases 1–5. See [the completed checklist](phases/PHASE_06_GROWTH_AND_BILLING.md) and [the growth/billing runbook](GROWTH_AND_BILLING.md) for the supported workflows and recovery contract.

## Implemented scope

- Native-verified, channel-scoped virtual publishing grants, own/all edit/delete, schedule/settings permissions, queued grant-generation fencing, revocation and reviewed post adoption.
- Separate public teasers/private secrets, ordered membership requirements, signed private starts, actionable join links, fresh receive/dispatch checks, content protection and secret-version invalidation.
- Sender/channel leads with explicit campaign opt-in independent of admission; reviewed SQL audience snapshots, per-recipient outcomes, cancellation, restricted unsent preparation, opt-out and scoped erasure.
- Request-owned expiring native invitation links, first qualifying request/first-join attribution, distinct invitee credit, dynamic UTF-16-safe progress, separate invitation timeout and durable revocation.
- Unpublished/admin-configured immutable plan versions, bound Stars quotes/invoices, fast checkout validation, durable leased financial receipts, atomic zero-day core payment/channel grants, duplicate handling and paid-period projection.
- Prorated current-period upgrade overlays, queued renewals/downgrades, expiry/impact previews, non-destructive quotas, payer/admin full refunds, native/shared refund reconciliation and dependent-upgrade review.
- Full-manager factory template, verified sender bindings, source generation invalidation, upload-to-selected-sender media policy, active-only rotating sweeps, offline pause/delete fencing and residual cleanup audit.
- Explicit foreign-webhook migration confirmation on create, resume and rotation, with encrypted pending create state; child billing redirects to the control bot.
- Localized private subscriber menus, links, scoped feedback and one-time replies. Native invoices/feedback also use payer/operator language.
- Sixteen new tables, added workflow/lease references and direct cascading bot foreign keys for older template records in `0024_chm_growth`.

## Results

| Check | Result |
|---|---|
| Combined Channel Manager, locale, factory, shared-payment and all six real-service files | **345 passed**, 203.83 seconds |
| Final Phase 6 services/menus/locales/factory and Phase 6 PostgreSQL/Redis recheck | **97 passed**, 30.92 seconds |
| Final native authority-ceiling recheck across growth, menus, billing, locales and factory | **92 passed**, 25.42 seconds |
| Ruff | `ruff check .` passed |
| Mypy | Passed; **376 source files** |
| Tracked/new-file whitespace | Checked after final documentation cleanup |

The combined run covered all existing Channel Manager phases and the affected shared services. The 97-test run followed the unlock-guidance, native localization, non-Stars review and unusable-token lifecycle changes. The final 92-test run verified additional current-native-right ceilings for delegation and sender changes; it did not repeat the real-service files after the disposable services had stopped. These runs overlap; their counts must not be added as distinct tests. The full platform suite was not repeated in Phase 6; its Phase 5 results and resolved follow-ups remain recorded in [Phase 5 verification](PHASE_05_VERIFICATION.md).

The environment used Python's local virtual environment, aiogram **3.31.0**, SQLAlchemy **2.1.6**, disposable loopback PostgreSQL **14.24** and Redis **6.0.16** in WSL. The production Compose PostgreSQL 16/Redis 7 combination remains a release check. All Telegram calls used `RecordingSession`: no live messages, charges, refunds, tokens, webhook replacements or production records were used. Tests exclude the workspace `.env`. Disposable services were stopped after verification.

## Functional evidence

Collaboration checks distinguish native promotion authority from virtual grants, enforce own/all and schedule/settings restrictions, retain source-automation native checks, reject another channel/bot's grant/media, hold publication after revocation/revision/grantor loss, and require explicit republishing after adoption.

Disclosure checks confirm the public version never contains the secret, output goes only to the requesting private user with content protection, ordered requirements are checked again at dispatch, secret edits invalidate older queued reveals, disabled/tampered links fail, missing requirements have actionable links, and unknown remote sends do not replay automatically.

Campaign checks cover private proof, explicit opt-in, exact channel and sender association, later arrivals excluded from snapshots, opt-out after preview, scoped deletion, snapshot confirmation idempotency, outcome reporting and exclusion of succeeded/ambiguous recipients from reviewed retries. Feedback ownership, one-time reply, private data erasure, optional resubscription and Arabic native output are covered.

Invitation checks cover native creator/link attribution, qualifying request gates, separate consent, one credit per invitee, self/repeat/wrong-source rejection, stale request epochs, timeout inability to bypass captcha, protected admission after campaign opt-out, progress placeholders/Unicode entities and retained revocation obligations.

Commercial checks cover unpublished/unauthorized catalog changes, wrong payer/amount/currency, expired/retired quotes, accepted-checkout late success, duplicate checkout reservation/payment, charge reuse against another invoice, stale upgrade basis, prorated upgrade coverage, next-period downgrade, full refunds and idempotent rebasing, upgrade dependency review, unrelated paid/VIP preservation, shared core refund projection, quota holds and actual-amount refund previews. Financial receipts are committed before acknowledgement, grant only under the current lease and process during maintenance. Ambiguous refund RPCs remain uncertain without replay. Non-XTR charges receive support guidance rather than a native Stars refund button.

Sender checks cover owner/template/status/token-epoch binding, parent pause, direct cross-bot media rejection, immediate unbind not replaying old publication, fair active-only factory sweeps, explicit foreign-host migration before webhook mutation, explicit resume migration, and SQL binding invalidation even when the token cannot be decrypted.

## PostgreSQL and Redis evidence

The seven Phase 6 real-service checks verify:

1. Migration downgrade/upgrade while preserving admission requests, an active timed ban and its operation, followed by model/schema parity.
2. Concurrent duplicate payment fulfillment creates one grant; parallel renewals allocate consecutive nonoverlapping periods.
3. Revocation committed between native authorization and the final SQL dispatch fence prevents publication.
4. Concurrent invitee credit records/increments once.
5. Child deletion cascades its namespace while retaining a sibling and the control channel's paid ledger and paused state.
6. Foreign keys reject an operation pointing to another channel's growth action.
7. Real Redis shares the sender/chat budget across operation families.

The combined run also executed all 27 earlier PostgreSQL/Redis checks. Older migration seeds now use only columns actually present in the selected old revision, preserving their original data assertions rather than accidentally inserting a later model default.

## Reproduction

```text
python -m ruff check .
python -m mypy
python -X utf8 -m pytest -q tests/bots/channelmanager tests/test_locales.py tests/bots/factory tests/core/test_subscriptions_payments.py -p no:cacheprovider
```

Use fresh writable Windows `--basetemp` directories. Pytest temporary metadata may require execution outside the sandbox. No deployment environment needs to change.

For real services, set `TEST_CHM_DATABASE_URL`, `TEST_CHM_PUBLISH_DATABASE_URL`, `TEST_CHM_ADVANCED_DATABASE_URL`, `TEST_CHM_AUTOMATION_DATABASE_URL`, `TEST_CHM_MEMBERS_DATABASE_URL`, `TEST_CHM_GROWTH_DATABASE_URL`, and `TEST_CHM_REDIS_URL` in the test process. The six PostgreSQL URLs must use `postgresql+asyncpg`, loopback hosts and disposable `channelmanager_phase1_test` through `channelmanager_phase6_test` prefixes respectively. Tests perform downgrade/upgrade and truncation; Phase 6 truncates bot namespaces in its isolated database. Redis verification uses loopback port 56388 and only its test budget keys.

```text
python -X utf8 -m pytest -q tests/integration/test_channelmanager_foundations.py tests/integration/test_channelmanager_publishing.py tests/integration/test_channelmanager_advanced.py tests/integration/test_channelmanager_automation.py tests/integration/test_channelmanager_members.py tests/integration/test_channelmanager_growth.py -p no:cacheprovider
```

## Release boundaries

Phase 6 completes the selected R4 product families with explicit fallbacks. Personal reveals use signed private delivery; ephemeral client behavior is not claimed. Media is uploaded to the chosen sender; cross-bot transfer/reuse is not claimed. Branded children are full managers with separate data; external Modular interoperability and external long-poller discovery remain outside scope. Campaigns do not enumerate Telegram's entire member list, and invitation credit cannot prove that different accounts represent different people.

Plan prices remain unpublished until an administrator configures and reviews them. Refunds are full native charge refunds, not arbitrary partial Stars refunds. Existing operator/VIP billing is not substituted for channel entitlement.

Committed-state fencing does not make native permission changes or Telegram RPCs atomic with SQL. Unknown effects need reconciliation and may require operator intervention. Production-version tests, full combined platform regression, real Telegram rendering, canary payments/refunds, capacity, backup/restore and controlled rollout remain [Phase 7](phases/PHASE_07_PRODUCTION_READINESS.md) and Phase 0 live compatibility gates. Production credentials/configuration and deployment were not changed.
