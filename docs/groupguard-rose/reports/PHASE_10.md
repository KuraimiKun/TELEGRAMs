# Phase 10 federation bans, subscriptions and enforcement

## Identity and scope

Starting completed gate57823e1. Client autosave593c6c3 recorded an intermediate13-file slice during implementation; it is preserved separately from the completed gate. Current report:13 October2026 Asia/Jakarta. Local gate passed. Source/test identity is recorded in phase10/worktree.sha256; documentation/evidence identity in MANIFEST.sha256. No deployment, production-data operation, live moderation or Rose private network was used.

Delivered: current role/context fban/unfban intents, directed bounded subscriptions, actual observed destination enforcement with durable versions/provenance, strong passive checks and quiet explanations, public status forms, actual owner document exports and bounded CSV/JSONL/NDJSON/own JSON import. New migration0018 adds only federation ban/sub/observation tables and separate graph generation. Existing approvals, manual restrictions, optional CAS, platform/child ownership and unrelated modules remain distinct.

## Feature and contract evidence

All26 stable stage IDs and their local tested-subset status appear in [feature-evidence.csv](../evidence/long-running/phase10/feature-evidence.csv). All824 IDs remain. Previous reason/quiet selectors, federation-before-newcomer priority and fedsubs catalog execution now have concrete enforcement tests. Public signatures/fields/SQL/Redis/job contracts are in API_CONTRACTS.md; current whole-ledger counts in LEDGER_COUNTS.json. Full discoverability, status pagination and31 actual locales remain11.

Source role tests use actual dispatchers: federation owner/admin can save the attached federation's policy independently of local Telegram administration; a local creator without federation role cannot. Private commands target the actual human's owned federation despite a connection. Required-reason validation rejects before writes. Actual current Telegram administrators are exempt from automatic removal.

Ban records retain inactive monotonically increasing versions. Root and destination outboxes commit with policy and capture source/attachment generations. Workers rederive current graph/roles/namespace/target/capability, lock federation rows in sorted order before attachment and hold the intent fence through API. A delayed recording RPC proves that a newer unban cannot commit over the old ban dispatch. Deadlock-prone attachment/federation reverse ordering was corrected before the frozen gate.

Direct/subscribed/multiple-source tests assert resulting SDK bans and local ownership, not only queue creation. Removing one source preserves another; unrelated manual bans remain. Existing external bans cannot become invented ownership; unknown RPC/ownership remains uncertain without blind retry or automatic unban. Federation deletion/leave retires local provenance without undoing real bans; fresh ordinary manual unban can act when no independent restriction remains. Generic rejoin does not turn inactive uncertain federation data into a new ban.

Only actual messages, joins and requests create minimal observations. Requests do not assert membership. Fanout/reconciliation uses bounded keysets and reverse graph dedupe; no member inventory or inaccessible history is fabricated. Cycles/self/cross-bot edges reject; graph policy has a separate generation so ordinary name/config changes do not cancel valid work. Local destination quota waits stay outside API retry count. Passive current-version receipts serialize identical events and queue known rate/retry deferral. Active fanout is silent per group; independent root owner PM/log describes policy changes.

Passive speaking/join/request checks precede generic approval, raid and CAPTCHA. Quiet suppresses visible explanations while leaving enforcement active. An already-issued verification cannot approve after a federation ban and declines its pending request. Current namespace/protected target/capability and paused lifecycle remain mandatory; source/outcome diagnostics reflect actual failure.

Owner-only files require actual received document/getFile/download and real sent document receipt. Whole UTF-8 format/ID/reason/size/duplicate validation precedes transaction writes. True newline JSON differs from the explicit own JSON-array adapter; CSV and minicsv preserve their distinct columns. More than1,000 records or2MiB rejects instead of truncating. Spreadsheet-active CSV text is emitted as a reversible literal. Deep malformed JSON is controlled. The shared30-minute per-federation interval does not get consumed by invalid input. Audit retains checksum/count without unrestricted upload content or imported ownership trust.

## Executed validation

| Check | Observed result |
| --- | --- |
| First core effect acceptance |9 passed |
| Core, Phase9 and locale scope |68 passed |
| Initial hooks plus Phase9/4/7 and locales |201 passed;1 standalone factory-only skip |
| Expanded acceptance before corrections |41 passed;3 new fixture argument failures |
| Corrected passive/unknown cases |6 passed |
| Complete then-current new Phase10 scope |36 passed |
| Current Phase10/9/locale scope before final additions |95 passed |
| Additional status/issued verification/quota/file limits |9 passed;3 wrong fixture/helper calls corrected |
| Corrected actual dispatcher request verification |3 passed |
| Inactive uncertainty/known retry/issued CAP proof |9 passed |
| Final Phase10 plus locale scope |74 passed |
| New real PostgreSQL ordering/graph/import/passive races |9 passed;81 unrelated deselected |
| All real PostgreSQL/Redis foundations |90 passed |
| Fresh/legacy/model migrations and Redis review |4 passed |
| Runtime E2E |1 passed |
| Frozen Ruff/mypy |Pass;297 source files |
| Full frozen suite |1,463 passed;97 skipped;zero failures |

The97 full-suite skips comprise90 foundation cases,4 migration/review and1 runtime, all separately passing, plus2 standalone factory-only inapplicabilities.

New failures were test fixture usage: omitted reason/by arguments when installing an approval, then incorrectly calling a join fixture as a request challenge constructor. The corrected test feeds a real request through the dispatcher, captures its actual returned card, introduces a new federation policy, and asserts no approve/restrict plus an actual decline. No production assertions were weakened. Original debug outputs are preserved separately from whitespace-clean saved evidence.

Exact commands from the repository cwd and established .venv:

```text
.venv/bin/pytest -q tests/bots/groupguard/test_phase10.py tests/test_locales.py --tb=short
.venv/bin/pytest -q tests/bots/groupguard/test_phase10.py tests/bots/groupguard/test_phase09.py tests/bots/groupguard/test_phase04.py tests/bots/groupguard/test_phase07.py tests/test_locales.py --tb=short
TEST_GG_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_concurrency TEST_GG_REDIS_URL=redis://127.0.0.1:56380/2 .venv/bin/pytest -q tests/integration/test_groupguard_foundations.py -k 'ban_unban_cannot or parallel_cycles or concurrent_passive' --tb=short
TEST_GG_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_concurrency TEST_GG_REDIS_URL=redis://127.0.0.1:56380/2 .venv/bin/pytest -q tests/integration/test_groupguard_foundations.py --tb=short
TEST_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_integration TEST_REDIS_CLAIM_URL=redis://127.0.0.1:56380/1 .venv/bin/pytest -q tests/integration/test_migrations.py tests/integration/test_groupguard_review.py --tb=short
TEST_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gglong TEST_REDIS_URL=redis://127.0.0.1:56380/0 .venv/bin/pytest -q tests/e2e --tb=short
DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_integration .venv/bin/alembic upgrade head
DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_integration .venv/bin/alembic revision --autogenerate -m gg_fed_enforcement --rev-id 0018_gg_fed_enforcement
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/python -m core bots
.venv/bin/pytest -q --tb=short
git diff --check
```

Python3.12/existing aiogram, task-owned disposable PostgreSQL16/Redis7 with URL/DB preflight assertions. The recording SDK tracks actual fake-server membership transitions, making ban/unban effects observable. Real database/Redis cases are separate from mocked Telegram and runtime E2E. Fast conversation fixture throttle bypass is documented; runtime preserves real middleware. No live behavior or exactly-once remote guarantee is asserted.

## Decisions, recovery and next task

Local caps32 direct subscriptions/128 reachable/depth16/10,000 namespace edges,2MiB/1,000 file records,100-page work,5,000 pending destination jobs and shared20/sec quota are explicit in DECISIONS.md. The30-minute ban-file interval comes from the supplied digest. Ownership/unknown outcomes remain conservative; inactive tombstones preserve local ordering. Operator visibility and current role/context mapping are documented in COMMANDS.md.

Migration0018 is additive and legacy groups work without a federation; downgrade loses the new ban/sub/observation data and graph generation. Back up before rollback and retire local fed provenance without automatic remote unban if rolling back this feature. Source/live server/BotFather behavior remains unobserved. Task-owned services remain for11/12; no shared resource reset.

Next: Phase11 own portable modules, creator import/reset with scoped replay/rate/media/destination checks, actual bot-scoped privacy inventory/deletion,31 authored locale content and complete UI/discovery. Then Phase12 audit, measured service/burst checks and complete actual finished worktree ZIP. Status pagination/public bot/anonymous read acceptance and full UI/locales are recorded as later completion, not claimed by catalog presence.

Local checkpoint recorded; continuing according to LONG_RUNNING_MASTER_PLAN.md.
