# Phase 9 federation management and membership

## Identity and scope

Started from fdc3a61 (Phase8 cef9319 plus the documentation line-ending repair). The working implementation adds local UUID federations, one owner per bot/user, distinct federation roles and creator-controlled group membership. Local gate passed; exact source/test identity is recorded in phase09/worktree.sha256 and documentation/evidence in MANIFEST.sha256. No deployment/live API or Rose private network was used. Current report date:13 October2026 UTC.

Production changes: federations.py, handlers/federations.py, additive0017 models/migration, module priority routing,37 real EN/AR strings and the optional existing-transaction namespace check. Tests:39 actual dispatcher cases across standalone/ChildRegistry710011/710012 and nine real PostgreSQL cases. All prior work and stable ledger IDs remain preserved.

## Feature and contract evidence

Every one of the33 stage IDs is retained in [feature-evidence.csv](../evidence/long-running/phase09/feature-evidence.csv);31 rows have local tested-subset evidence, required-reason/quiet enforcement remain the two explicit partials for10. The Phase8 fedinfo/fedadmins catalog rows now have actual execution/disable tests; fedsubs remains10. Whole-ledger counts are in LEDGER_COUNTS.json, and current signatures/fields/keys/jobs in API_CONTRACTS.md. No selector is described as ban enforcement.

Private create/rename/delete and protected federation management use the actual human's owned federation even with an active group connection. Public reads can use current/owned/explicit UUID, scoped to this bot. Group disabled commands govern in-group reads; explicit public PM UUID queries retain their independent federation context. Names reject blank/control input and truncate64 codepoints. Myfeds/admin roster output is bounded with explicit continuation syntax.

Owner, federation administrator, Telegram group creator/admin and platform/child owner remain separate. Owner-only promotion/demotion cannot demote the immutable owner; an administrator can resign by explicit ID. Group creator alone joins/leaves a federation, even one owned by someone else. Quiet policy needs change_info; it does not grant ban/owner roles. Mutation/role/source audit is transactional.

Delete and log setup freeze the current revision in a personal300-second token and bind the actual owner-PM Message. Wrong opener/child, expiry, cancellation, replay, renamed federation and revoked destination deny without side effects. Channel setup uses the actual channel post and current owner administration plus this bot's post_messages rights; confirmation audit preserves actual source and confirming message IDs. Forwarded proof is not used. Deletion removes local roles/membership and cancels relevant undispatched work while preserving existing Telegram bans.

Owner notification defaults on; reason requirement defaults off locally. Notification-off preserves configured logs. Current destination rights and actual Message receipts are required; transport failures remain independent of a committed role/configuration change. Bots, anonymous senders, inactive children and private owned cleanup contexts cannot obtain human federation authority.

Composite federation/group foreign keys enforce bot scope. All writes serialize at bot member0 and lock the federation row; ownership uniqueness is database-backed. Fresh child-status rechecks use the current mutation transaction, avoiding a separate SQLite shared-connection session rolling back pending writes. Existing callers keep the prior namespace behavior.

## Executed validation

| Check | Result |
| --- | --- |
| First dispatcher/locale scope |29 passed;15 failures in new fixtures |
| Corrected fixtures |40 passed;4 child persistence failures exposed |
| Production same-transaction namespace correction |24 federation cases passed |
| Expanded federation/locale acceptance |59 passed |
| New PostgreSQL ownership/parallel roles/tenant FK/generation cases |9 passed;72 unrelated deselected |
| Complete PostgreSQL/Redis foundations |81 passed |
| Fresh/legacy/model migration and real Redis review |4 passed |
| Runtime E2E |1 passed |
| Frozen Ruff/mypy |Pass;292 source files |
| Full frozen suite |1,409 passed;88 skipped;zero failures |

The 88 full-suite skips comprise81 foundation,4 migration/review and1 runtime cases, all separately passing, plus2 standalone factory-only inapplicabilities.

The first fixture failures selected the owner as a promotion target and expected optional keyboard data in the recording SDK Message receipt; the actual request carries that keyboard. Tests now use a distinct human and the actual returned Message ID plus recorded keyboard. Remaining child persistence failures were production transaction sequencing, fixed without weakening mutation/no-unban assertions. The real PostgreSQL constraints and races pass independently.

Exact commands from the repository cwd with the established .venv (evidence files preserve results):

```text
.venv/bin/pytest -q tests/bots/groupguard/test_phase09.py tests/test_locales.py --tb=short
.venv/bin/pytest -q tests/bots/groupguard/test_phase09.py --tb=short
TEST_GG_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_concurrency TEST_GG_REDIS_URL=redis://127.0.0.1:56380/2 .venv/bin/pytest -q tests/integration/test_groupguard_foundations.py -k federation --tb=short
TEST_GG_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_concurrency TEST_GG_REDIS_URL=redis://127.0.0.1:56380/2 .venv/bin/pytest -q tests/integration/test_groupguard_foundations.py --tb=short
TEST_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_integration TEST_REDIS_CLAIM_URL=redis://127.0.0.1:56380/1 .venv/bin/pytest -q tests/integration/test_migrations.py tests/integration/test_groupguard_review.py --tb=short
TEST_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gglong TEST_REDIS_URL=redis://127.0.0.1:56380/0 .venv/bin/pytest -q tests/e2e --tb=short
DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_integration .venv/bin/alembic upgrade head
DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_integration .venv/bin/alembic revision --autogenerate -m gg_federations --rev-id 0017_gg_federations
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/python -m core bots
.venv/bin/pytest -q --tb=short
git diff --check
```

Python3.12, existing aiogram, disposable PostgreSQL16/Redis7. Dedicated test databases and Redis DB numbers are asserted before reset; task-owned services remain for later phases. Fast conversation fixture bypasses wall-clock throttling as documented; runtime E2E exercises real runtime middleware. Recorded SDK effects, real services and unobserved live behavior remain distinct.

## Decisions, recovery and next task

Own UUIDs/roles are independently implemented; no global bans, transfer or cross-bot trust are invented. Private context independence, codepoint truncation, bounded roster/username verification, default policies and revision invalidation are recorded in DECISIONS.md. Additive0017 does not rewrite legacy groups; downgrade drops federation tables and loses federation data, so back up first. Existing real bans are never automatically undone by local deletion.

Next: Phase10 direct/subscribed ban versions, observed membership, durable bounded graph/fanout/current authority and provenance, real files/import validation and quiet/source enforcement. Then portability/privacy/31 authored locales/UI, final audit and actual source ZIP. Required-reason/quiet enforcement, full UI/translations and independent final review are explicitly unfinished. No external dependency prevents this local continuation.

Local checkpoint recorded; continuing according to LONG_RUNNING_MASTER_PLAN.md.
