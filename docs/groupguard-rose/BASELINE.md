# Phase 0B refreshed baseline

Reference date:2026-10-12 Asia/Jakarta. Starting branch `work`, HEAD `e474c59784c47f4055cdc0eab7a74d111a1ff66b`; only pre-existing untracked `docs/groupguard-rose/`. Its20 artifacts preserved byte-for-byte in history/PHASE_00 and `/workspace/groupguard-phase00-original.tar.gz`, SHA256 `0d525c269a96c9235379c07b0fecdef9cb81bddd38844519628bdc4346575d3b`.

Verified supplied bundle SHA256 `61869c1cae2bc35ae3aa1cc8080fdbe8656ddaf22c6c69a8b7ae3503f74768cb`, all six manifest member hashes, and `git bundle verify` exit0. Prerequisite `44ff18f39d2fbbc8583eb5e0ddbd013ffd20f83f` has the same tracked starting tree `dde227cef0228c7d0104543aa3374cb7c996e41b`. Fetched with `git fetch /tmp/groupguard-phase00b-handoff/CLOUD_BASELINE.bundle HEAD`; requested commits were not already ancestors. Ordinary `git cherry-pick -x` in order succeeded without conflict:

- `17f563460d2d74ac7d0be70989c94c663e91d9d9` → `cf3afa3067e4e2769762e0c64a944b86de9439a5`.
- `d55fc44fe1a63ba5788125c1325d2a855944d5e0` → `96357ef45c6492e03c626581ce2ee156d2da3816`.

Ending/reference tree `7895f72031fd4fac13b4ff280ba04b16c8d5842c`; `git diff --exit-code d55fc44fe1a63ba5788125c1325d2a855944d5e0 HEAD` exit0, empty. No additional tracked edits. Import diffstat65 paths,5998 insertions,44 deletions. Author retained; new cherry-pick hashes differ from supplied hashes and retain provenance. Audit revisions remain untracked, uncommitted. No other user changes discarded.

Refreshed source includes CV/doctools, shared throttle_exempt/payment/AI/file/UI changes, GroupGuard flood message-ID member, `0008_cvbot -> 0009_doctools` and existing `tests/e2e`. Dependency requirements unchanged; retained editable `.venv`, pipcheck0; full installed versions saved. Python3.12.14, aiogram3.31.0, SQLAlchemy2.1.4, asyncpg0.32.0, Alembic1.20.0, redis-py7.4.1, fakeredis2.39.0, pytest9.1.1/pytest-asyncio1.4.0, ruff0.17.0, mypy2.4.0, PyMuPDF1.28.2, pypdf6.20.0.

| Exact command (repository cwd) | Exit | Pass / fail / skip | Evidence |
| --- | --- | --- | --- |
| .venv/bin/python -m pip check | 0 | n/a | No broken requirements; editable dependencies unchanged by baseline |
| .venv/bin/python -m core bots | 0 | 9 contracts valid | 7 standalone modules +2 template-only; GroupGuard is a template |
| .venv/bin/ruff check . | 0 | n/a | All checks passed |
| .venv/bin/mypy | 0 | 242 source files | No issues |
| .venv/bin/pytest -q tests/bots/groupguard tests/bots/factory tests/test_locales.py | 0 | 36 / 0 / 0 | 2.99s |
| .venv/bin/pytest -q | 1 | 257 / 1 / 3 | 33.91s; doctools malformed HTML expectation fails |
| TEST_DATABASE_URL=postgresql+asyncpg://bot@127.0.0.1:55432/gg_phase00b_integration .venv/bin/pytest -q tests/integration | 0 | 2 / 0 / 0 | 2.14s; disposable PostgreSQL |
| TEST_DATABASE_URL=postgresql+asyncpg://bot@127.0.0.1:55432/bot TEST_REDIS_URL=redis://127.0.0.1:56379/0 .venv/bin/pytest -q tests/e2e | 0 | 1 / 0 / 0 | 23.75s; disposable PG/Redis, local mock Bot API/scripted AI |
| .venv/bin/pytest -q tests/bots/doctools/test_review.py::test_malformed_html_and_invalid_encoding_are_controlled | 1 | 0 / 1 / 0 | Isolated reproducible baseline failure;0.24s |
| PYTHONPATH=/workspace/TELEGRAMBOTS .venv/bin/python docs/groupguard-rose/history/PHASE_00/evidence/probes.py.txt | 0 | 10 diagnostic observations | Script completion0 does not mean feature acceptance passed |

The full default suite skips the two integration tests because TEST_DATABASE_URL is absent and one e2e test because TEST_DATABASE_URL/TEST_REDIS_URL are absent. They were executed separately and passed; their passes do not remove the full-suite failure. Repository pytest excludes live tests by default (`-m 'not live'`); no live Telegram/web QA was requested or run.

Failure: `tests/bots/doctools/test_review.py:77`, `Failed: DID NOT RAISE CitationError` for `page_reference(b"<![bogus]><title>Study</title>", ...)`. Python3.12.14 stdlib HTMLParser accepts that declaration; `bots/doctools/citations.py` returns title Study, and its exception handler is never entered. Isolated rerun reproduces. This supplied baseline test/code mismatch is unchanged; the original checkout had no doctools test. No audit fix applied.

Disposable services were new Docker containers `groupguard-phase00b-postgres` (postgres:16-alpine, actual PostgreSQL16.15, loopback55432, test-only trust rolebot) and `groupguard-phase00b-redis` (redis:7-alpine, actual7.4.11, loopback56379). Dedicated integration database created on that server. Integration drops its selected public schema; e2e uses a unique created database and refuses nonempty RedisDB0. Both suites ran against these new services, not shared/production onboarding services. E2e migrated actual schema, exercised gateway/scheduler/worker/childfeedback plus GroupGuard CAPTCHA/flood and other bot flows, and validated shutdown. Its Telegram/AI were local mocks; no secrets/.env/live groups used. PG e2e database was removed and RedisDB0 size was0 afterward. Both test containers stopped successfully; unrelated services untouched. Stopped containers retain only disposable test data and are available for later explicit reuse/removal.

Installed SDK introspection confirms reaction-removal methods, sender-chat ban/unban, getChatAdministrators return_bots, can_react_to_messages and guest_message. No deployed server API version/capability was contacted or certified. Zero repeated blocked documentation requests in Phase0B.
