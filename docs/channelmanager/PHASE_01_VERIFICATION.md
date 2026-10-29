# Phase 1 implementation and verification

Completed 28 October 2026. Base repository commit: `10e9b83`; implementation is in the working tree.

## Implemented scope

- Standalone `channelmanager` SDK module, configuration, commands, English/Arabic menus, optional Compose worker, central recovery sweep, metrics, and diagnostics.
- Live native-channel authorization, actor/generation-bound callbacks, permission refresh, disconnect/reconnect, and ordered bot-membership snapshots.
- Seven `chm_` foundation tables with composite namespace foreign keys and revision `0019_chm_foundations`.
- Durable channel-event receipts before webhook acknowledgement, duplicate suppression, transactional domain/audit/notice creation, bounded failed receipt handling, and cleared completed payloads.
- Fenced outgoing jobs, generation invalidation, bounded API retries, local-budget deferral, uncertain delivery states, and expired-lease recovery.
- Module-level durable webhook capability replacing the Group Guard slug special case. Existing polling behavior remains unchanged.
- Shared notice/operator-broadcast rate budgets in Channel Manager contexts. Other modules retain their existing broadcast behavior.
- Test isolation from the real workspace `.env`, plus Windows timezone-data support for migration generation.

## Verification results

| Check | Result |
|---|---|
| Complete default test suite | 1,608 passed, 133 skipped; 521.13 seconds |
| Final Channel Manager and locale tests | 54 passed; includes additional shutdown, maintenance, namespace-disable, and rate-store outage cases |
| Final webhook failure/privacy checks | 2 passed after ensuring receipt errors cannot log private SQL payloads |
| Real PostgreSQL/Redis tests | 3 passed: migration upgrade/downgrade/model parity, concurrent inbox/job claims and namespace constraints, atomic sender budget |
| Ruff | Passed |
| Mypy | Passed across 347 source files |
| Explicit discovery of every package, including templates | All 10 module contracts validated |
| Compose profile/worker command, Python syntax, local documentation links, diff whitespace | Passed |

The full suite ran before the last five focused edge-case tests were added; the subsequent focused run includes those tests. The final receipt-error sanitization change was separately checked by the webhook tests. Skipped tests are the suite's conditional service/runtime checks; the three Channel Manager real-service checks were run separately with their explicit URLs. The full run reported one third-party PyMuPDF `fitz` deprecation warning.

The real-service environment used disposable loopback PostgreSQL **14.24** and Redis **6.0.16** from local Ubuntu. This verifies the exercised SQL locking/constraint and Lua budget behavior; it does not establish a production canary on the Compose PostgreSQL 16 / Redis 7 images. Those deployment checks remain in the later readiness phase.

## Reproduction

Run from the repository root with the development environment installed. On Windows, enable Python UTF-8 mode. If the execution sandbox cannot access pytest's protected temporary directories, use an allowed execution context and a fresh temporary directory under `.scratch`.

```text
python -X utf8 -m pytest -q -p no:cacheprovider
python -X utf8 -m pytest -q tests/bots/channelmanager tests/test_locales.py -p no:cacheprovider
ruff check .
mypy
```

For real-service verification, set `TEST_CHM_DATABASE_URL` to a dedicated loopback database whose name starts with `channelmanager_phase1_test`, and `TEST_CHM_REDIS_URL` to a disposable local Redis endpoint. Then run:

```text
python -X utf8 -m pytest -q tests/integration/test_channelmanager_foundations.py -p no:cacheprovider
```

The migration test intentionally downgrades and upgrades the Channel Manager revision in that test database. Redis verification deletes only its unique test namespace. The workspace `.env` is excluded from pytest settings reads; explicit temporary fixture env files remain supported.

## Boundaries and next phase

No live Telegram bot/channel, production credentials, or live deployment was changed. Phase 0's live-client compatibility matrix remains pending. Failed receipt payload retention and manual repair are described in [operations](OPERATIONS.md); this phase does not add an automatic replay UI.

Phase 2 adds the post composer, drafts/library, one-off schedules, multi-channel publication, editing, deletion, and delivery reporting. Actual publication jobs must add fresh actor/bot posting-right checks at dispatch; Phase 1 outgoing jobs are private status notices only.
