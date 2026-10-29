# Phase 2 implementation and verification

Implemented 28 October 2026 in the working tree based on repository commit `10e9b83`. This extends the [Phase 1 foundations](PHASE_01_VERIFICATION.md).

## Implemented scope

- Canonical text/single-media renderer shared by previews, publication, and edits. Native Telegram entities, UTF-16 validation, a restricted HTML parser, URL button rows, signature snapshots, caption placement, notifications, protection, and same-primary-channel replies.
- English/Arabic private composer, saved drafts, personal/channel libraries with filters and pagination, target selection, timezone-aware one-off scheduling, and actor/post-generation-bound publication confirmation.
- Immutable content versions, one delivery per post/channel, post schedules, and channel styles, added by revision `0020_chm_publishing`. Composite foreign keys bind an operation to its bot/channel/delivery.
- Immediate publication, reschedule/publish-now, mixed sent/pending edits, basic media replacement, explicit copy-to-new-draft, and open/share links.
- Independent durable publish/edit/pin/delete/reminder operations, transactionally committed target reports, definite-failure follow-up retries, and no blind replay of successful or uncertain publications.
- Remote deletion versus detach, cleanup timed from actual send time, reminders outside the ordinary deletion window, and explicit disconnect/detach cancellation. Routine channel refreshes retain cleanup obligations.
- Live own/all actor checks and bot rights, ordered schedule quota locks, duplicate-confirmation fencing, post/dispatch serialization, expired-lease recovery, shared sender budgets, and recovery that cannot be starved by older future schedules.
- Late schedules held for explicit review, IANA timezone conversion, daylight-saving ambiguity rejection, localized recovery messages, and an [operator walkthrough](OPERATIONS.md#publishing-walkthrough).

## Verification results

| Check | Result |
|---|---|
| Final focused bot and locale checks | 97 passed; 24.39 seconds |
| Complete default repository suite | 1,653 passed, 138 skipped; 601.69 seconds |
| Real PostgreSQL/Redis checks | 8 passed; 9.16 seconds, across Phase 1 and Phase 2 integration files |
| Ruff / Mypy | Passed; Mypy checked 351 source files |

The full regression run preceded the final disconnect-during-send guard. The final focused and real-service checks were rerun against that guard. The full suite emitted one existing PyMuPDF `fitz` deprecation warning.

The five publishing PostgreSQL checks cover upgrade/downgrade with preserved Phase 1 channel/notice records and model parity; concurrent quota/duplicate confirmation enforcement; dispatch waiting for a post mutation; cross-bot/cross-channel delivery constraints and target uniqueness; and scheduled publication after rebuilding the service context. Phase 1 contributes its three migration/claim/inbox/rate-budget checks.

The functional tests cover preview/send equality; four media kinds; malformed HTML, URLs, and surrogate boundaries; partial versus uncertain publication; late schedules; immutable edits and cancellation; separate pin/deletion results; safe failed follow-up retries; cleanup after actor revocation/channel refresh; own/all permissions; stale confirmations; album rejection; timezone conversion; API retry/rate-store failures; and interrupted dispatch recovery. A disconnect during a dispatched publication cannot recreate pin/deletion work after the send completes; disconnected channels cannot execute new edits. API calls use `RecordingSession`; no Telegram messages are sent.

The real-service tests used temporary local PostgreSQL 14.24 and Redis 6.0.16 in WSL. The repository's Compose targets PostgreSQL 16 and Redis 7. Those deployment versions, production transport, Telegram clients, and an actual local Bot API server still need the release canary.

## Reproduction

```text
ruff check .
mypy
python -X utf8 -m pytest -q tests/bots/channelmanager tests/test_locales.py -p no:cacheprovider
python -X utf8 -m pytest -q -p no:cacheprovider
```

Set `TEST_CHM_PUBLISH_DATABASE_URL` to a dedicated loopback `postgresql+asyncpg` database whose name starts with `channelmanager_phase2_test`. The tests downgrade/upgrade its Channel Manager migrations and truncate Channel Manager tables. `TEST_CHM_DATABASE_URL` separately requires the `channelmanager_phase1_test` prefix; `TEST_CHM_REDIS_URL` selects the isolated Redis endpoint.

```text
python -X utf8 -m pytest -q tests/integration/test_channelmanager_publishing.py tests/integration/test_channelmanager_foundations.py -p no:cacheprovider
```

Windows runs may need a fresh writable `--basetemp` and execution outside the sandbox for pytest's protected temporary directories. The test harness excludes the real workspace `.env` and retains support for explicit fixture env files.

## Supported boundaries and release status

Supported content is text or one same-bot photo/video/animation/document. Albums, polls, advanced buttons, recurrence, calendars, batches, forwarding automation, manual-message adoption, virtual roles, campaigns, paid billing, and branded senders remain later-phase work. Published media-to-text conversion uses a new draft. Publication-only flags are fixed once sent. Replies are restricted to the primary channel as sole target; the primary signature snapshot is shared by selected destinations.

Telegram does not provide a transaction shared with SQL. A request interrupted after dispatch becomes uncertain and is not automatically replayed. The worker treats Telegram's explicit “message is not modified” edit response as successful confirmation that the desired content/markup is already current. [Official Bot API server error mapping](https://github.com/tdlib/telegram-bot-api/blob/master/telegram-bot-api/Client.cpp).

No production credentials, real `.env`, live database, webhooks, or deployment were changed. Phase 0 live compatibility validation and the relevant [production-readiness/canary gates](phases/PHASE_07_PRODUCTION_READINESS.md) remain outstanding before exposing R1 to users. Phase 3 is the next development phase.
