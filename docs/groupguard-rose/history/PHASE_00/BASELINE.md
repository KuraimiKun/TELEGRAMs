# Phase 0 baseline

Audit date: 2026-10-12, Asia/Jakarta. Commands ran in `/workspace/TELEGRAMBOTS`; logs contain host UTC timestamps. This run, rather than the preceding onboarding run, supplies the results below.

## Checkout and instructions

- HEAD: `e474c59784c47f4055cdc0eab7a74d111a1ff66b`; branch: `work`; latest subject: “Merge pull request #1 from KuraimiKun/claude/exciting-meitner-42p1kb”.
- Initial `git status --short`: empty. No applicable AGENTS.md, PLAN.md or REPORT_TEMPLATE.md found under `/workspace`; no `/AGENTS.md` is present. Read README.md, docs/BOT_SDK.md, docs/DESIGN_SYSTEM.md and docs/OPERATIONS.md. Reconstructed Phase 0 planning/report templates in this directory.
- Reference `d55fc44fe1a63ba5788125c1325d2a855944d5e0` is absent (`git cat-file -t` exit 128). `git fetch --no-tags origin <reference>` exit 128: `upload-pack: not our ref`. No reset, branch switch or push. Exact reference diff remains blocked. Current history includes Group Guard commit `17b71dc` and factory work `44ff18f`; these are current-checkout facts, not a comparison to the missing reference.
- Changes for this phase are exclusively `docs/groupguard-rose/` planning/report/evidence files. No production source, test suite, migration, dependency, lockfile or production configuration changed. No commit, merge, deployment or live Telegram action.

## Tools and dependencies

Python 3.12.14; aiogram 3.31.0; pytest 9.1.1; pytest-asyncio 1.4.0; Ruff 0.17.0; mypy 2.4.0; SQLAlchemy 2.1.4; asyncpg 0.32.0; redis-py 7.4.1; fakeredis 2.39.0; Alembic 1.20.0. PostgreSQL 16.15; Redis server 7.4.11. Dependencies already installed during onboarding using `python -m venv .venv` and `.venv/bin/pip install -e '.[dev]'`. No lockfile exists. `evidence/dependencies.txt` records the resolved baseline; resolution on another date may differ.

Use the existing isolated checkout; no worktree is needed. Activate `.venv` before reproducing the equivalent unprefixed commands below.

| Actual command | Exit | Result |
|---|---:|---|
| `.venv/bin/python -m core bots` | 0 | 7 contracts valid; includes factory-only templates |
| `.venv/bin/ruff check .` | 0 | All checks passed |
| `.venv/bin/mypy` | 0 | No issues in 210 source files |
| `.venv/bin/pytest -q tests/bots/groupguard tests/bots/factory tests/test_locales.py` | 0 | 32 passed, 4.80s |
| `.venv/bin/pytest -q` | 0 | 158 passed, 2 skipped, 38.01s |
| `TEST_DATABASE_URL=postgresql+asyncpg://bot@127.0.0.1:5432/gg_phase0_audit .venv/bin/pytest -q tests/integration` | 0 | 2 passed, 2.97s |
| `PYTHONPATH=/workspace/TELEGRAMBOTS .venv/bin/python /tmp/groupguard-audit/probes.py` | 0 | 10 diagnostic observations; not a pytest pass count |
| `pytest -q tests/e2e` | unrun | No tests/e2e directory; no e2e validation claimed |

The two skipped full-suite tests are `tests/integration/test_migrations.py`'s PostgreSQL-only cases when TEST_DATABASE_URL is unset. Both ran and passed in the dedicated integration invocation. No expected failures or disabled assertions. Live tests are deselected by repository addopts `-m 'not live'`; the default run is not live coverage. No failing baseline checks.

## Disposable services

Existing onboarding containers `telegram-onboarding-postgres` and `telegram-onboarding-redis` use PostgreSQL 16-alpine and Redis 7-alpine, bound only to loopback; PostgreSQL has trust authentication for development. They were reused; no production configuration was changed. Created a new disposable database with:

```bash
docker exec telegram-onboarding-postgres createdb -U bot gg_phase0_audit
TEST_DATABASE_URL=postgresql+asyncpg://bot@127.0.0.1:5432/gg_phase0_audit .venv/bin/pytest -q tests/integration
```

Integration tests drop/recreate the selected `public` schema, migrate all tables, compare model metadata, downgrade to base/re-upgrade and test PostgreSQL concurrency for core users/payments/VIP. They do **not** test Group Guard warnings/configuration races. Never point them at the `bot` development database or a real group database. No real Redis database was flushed; other tests/probes use fakeredis and in-memory SQLite. A repeat needs a fresh disposable DB or the same explicitly disposable DB; do not blindly rerun `createdb` on existing state.

## Diagnostic observations

`evidence/probes.py.txt` is an audit-only script using the existing RecordingSession, SQLite and fakeredis. Run it with the checkout on PYTHONPATH; it does not contact Telegram.

| Probe | Observed result |
|---|---|
| P01 | Message sent as the group receives `creator=True`, all six local authority flags true |
| P02 | Edited blocked-word/link message: zero DeleteMessage calls |
| P03 | `/terms casino` with casino blocked: zero deletes, core responds |
| P04 | `/start gs_<group>` as admin opens home, no settings keyboard |
| P05 | Second cached service writes welcome=false after first sets goodbye=true; persisted goodbye becomes false |
| P06 | Mocked warning-limit ban fails; warnings remaining=0; response says user was banned |
| P07 | Expiry pauses after reading state; simulated successful release deletes state; expiry resumes and kicks same user |
| P08 | Old/unrelated callback with same chat/user consumes newly issued button challenge; no message or generation binding |
| P09 | Standalone dispatcher subscriptions: callback_query, chat_join_request, chat_member, message, my_chat_member, pre_checkout_query; no edited/reaction observers |
| P10 | `parse_duration('10s')` returns None; the command parser treats invalid durations as reason text/permanent action |

These demonstrate bounded local behaviors. P07 forces a legitimate stale-read interleaving; P08 uses the permissive recording harness and does not claim arbitrary Telegram callbacks can be forged by clients. Persistent old buttons/rejoins and mode changes are the concrete threat. Further concurrency/remote API failures require acceptance tests in later phases.

## Source and capability access

Both `curl -fsSL --max-time 30 https://missrose.org/docs/` and the equivalent official Bot API request failed with exit 22; `curl -i` confirmed proxy **CONNECT 403 Forbidden** (exit 56), before any website response. An escalated retry returned the same denial. No verification was disabled, no proxy was bypassed, and no network draft was changed in Phase 0. This is a network access blocker, not evidence that either website is down, and not an automatic-approval-review rejection.

Public official local-server README was retrieved through `https://raw.githubusercontent.com/tdlib/telegram-bot-api/master/README.md` on the audit date. It documents `--local` 2000MB uploads, unlimited downloads, local file paths and flexible local webhooks, and mandatory API ID/hash. That server was **not** installed/run for this audit. Compose uses `aiogram/telegram-bot-api:latest` by default; no deployed image/version/capability is established. Installed SDK schemas/docstrings are evidence of available client methods and constraints, not current website retrieval or live API success.

Required outside input: read access to `missrose.org` and `core.telegram.org` or a complete dated documentation snapshot; available reference commit/patch for the comparison. No Telegram credentials are needed to finish the source inventory or next mocked foundation tests.
