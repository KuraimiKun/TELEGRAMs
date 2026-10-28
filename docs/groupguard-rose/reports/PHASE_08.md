# Phase 8 connections, command policy and utilities

## Identity and scope

Started from a51f5fe. This local checkpoint continues directly into Phases 9–12 under the controlling pasted request. Local gate passed. No deployment or live Rose/Telegram validation was performed. Source identity is recorded in phase08/worktree.sha256; documentation/evidence identity is recorded in MANIFEST.sha256.

## Feature and contract evidence

Every current-stage stable ID, local status, concrete acceptance family and remaining difference is preserved in [phase08/feature-evidence.csv](../evidence/long-running/phase08/feature-evidence.csv). Whole-ledger and scoped counts are in [LEDGER_COUNTS.json](../LEDGER_COUNTS.json); public signatures/fields and SQL/Redis/job contracts are in [API_CONTRACTS.md](../API_CONTRACTS.md).

Connected private commands carry a real group as task-local target context while preserving the original incoming Message, source chat, reply and message IDs. Current membership is checked for each command, exact feature rights for changes, and revision-fenced invalidation cannot erase a newer connection. Last-five history, opener-bound group links and sibling namespaces grant no authority. Commands requiring actual group message IDs are rejected in private context.

The canonical command catalog coordinates disablement, aliases, connected PM, reviews and bound content callbacks. Recovery controls remain available. The published twenty disableable names are present; three federation command implementations remain for Phases 9/10. `runs` and `saved` have explicit unsupported diagnostics; `antiflood` is a documented local read-only flood status alias. Catalog membership alone is not marked as execution parity.

Command and service cleanup run after functional processing. Native group payments now register the validated payer in this bot before the shared payment grant, even without an earlier private message. Failed processing preserves the recoverable message. Owned bot outputs schedule durable deletion after 300 seconds using actual returned Message receipts; Boolean responses cannot create imaginary jobs. Current categories, namespace and delete rights are checked again at dispatch. Action means announcements, warnings, echo and permapin; active verification/help/settings cards remain outside these categories, and welcome cleanup keeps its separate policy.

Forum operations use the installed SDK and actual current manage-topics rights. Deletion requires a personal, bound, expiring confirmation and cannot delete General. Missing/deleted topic errors stay visible without a fallback send. Welcomes now use the configured action topic or General. Ordinary note/filter replies keep their actual context.

Group campaigns are limited to configured standalone operators or the current active child's owner and this bot's active groups. Expansion and delivery are bounded, destination outcomes persist, and the owner can inspect them with `/broadcast`. Authority and campaign/destination state are checked after awaited rendering. Local quota waits do not consume API retry attempts. Interrupted network delivery stays uncertain without replay; known attachment delivery followed by companion throttling does not repost the attachment.

Creator-only automated silent enablement requires the configured automated log category and preserves explicit action selection. Removal of consent/log or failed log delivery triggers loud fallback. Manual silent commands remain separate. Bot-to-bot mode defaults off; current membership and rights remain mandatory. Human review freezes the original bot and operation and rechecks both actors. Skip-review grants no additional rights; bots never become creators or owners. Self/reply/duplicate/rate loop bounds are enforced.

Additional shared seams preserve essential Indic/Japanese marks during bounded matching, validate normalized expansion at save, include actual custom-emoji pack IDs and skip malformed legacy night keys. Additive migration 0016 creates connection and campaign tables; no existing group configuration is rewritten.

## Executed validation

| Gate | Observed result |
| --- | --- |
| Broad Group Guard, locale and shared-feature regression before final additions | 1,125 passed; 2 standalone factory-only skips |
| Expanded Phase 8 acceptance | 68 passed; six new fixture/assertion failures corrected |
| Corrected cases | 6 passed; 68 deselected |
| Complete PostgreSQL/Redis foundation suite | 72 passed |
| Fresh/legacy/model migrations and Redis approval | 4 passed |
| Runtime E2E | 1 passed |
| Ruff and mypy | Pass; 290 source files |
| Frozen full suite | 1,370 passed; 79 skipped; zero failures |

The 79 full-suite skips comprise 72 foundation cases, four migration/Redis cases and one runtime case, all separately passing, plus two standalone factory-only inapplicabilities.

Final documentation diff checking flagged CSV writer CRLF endings. They were normalized to LF without changing ledger fields or IDs; the check was rerun successfully.

The six new failures were two test defects in each of the three contexts: the test expected an exception class instead of the existing `retry_after` result code, and omitted two required fields of the actual SDK Restricted member DTO. Required/forbidden API effects remained unchanged. Earlier shared-warning receipt regression was repaired in production while preserving the original test assertions; debug logs remain available.

All 824 stable ledger IDs are retained. Of 123 Phase 8 rows, 117 have local tested-subset evidence and six remain explicitly partial for federation execution or unresolved catalog semantics. Complete discoverability, 31 authored locales, portability/privacy, federation enforcement and final independent source review remain later work. Recording SDK evidence is separate from real disposable PostgreSQL/Redis and runtime evidence; no live bot visibility or remote exactly-once behavior is asserted.

Exact executed commands (repository cwd, existing .venv; redirected files under phase08 evidence):

```text
.venv/bin/pytest -q tests/bots/groupguard tests/test_locales.py tests/core/test_features.py --tb=short
.venv/bin/pytest -q tests/bots/groupguard/test_phase08.py --tb=short
.venv/bin/pytest -q tests/bots/groupguard/test_phase08.py -k 'restricted_nonmember or posted_broadcast' --tb=short
TEST_GG_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_concurrency TEST_GG_REDIS_URL=redis://127.0.0.1:56380/2 .venv/bin/pytest -q tests/integration/test_groupguard_foundations.py --tb=short
TEST_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gg_long_integration TEST_REDIS_CLAIM_URL=redis://127.0.0.1:56380/1 .venv/bin/pytest -q tests/integration/test_migrations.py tests/integration/test_groupguard_review.py --tb=short
TEST_DATABASE_URL=postgresql+asyncpg://gglong@127.0.0.1:55433/gglong TEST_REDIS_URL=redis://127.0.0.1:56380/0 .venv/bin/pytest -q tests/e2e --tb=short
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/python -m pip check
.venv/bin/python -m core bots
.venv/bin/pytest -q --tb=short
git diff --check
```

The fast conversation fixture passes through the shared throttle to avoid wall-clock test delays, as in prior stages; runtime E2E retains actual runtime middleware. PostgreSQL16/Redis7 run in dedicated task-owned local containers, with explicit disposable database/Redis-DB assertions. No shared service was reset. Full-suite service skips are recorded separately from the actual service runs. Dependency check and all nine module contracts pass.

## Decisions, recovery and next task

Phase8 compatibility choices are recorded in DECISIONS.md and the command/default/context guide in COMMANDS.md. Migration0016 is additive; its downgrade drops only the new connection/campaign tables, losing those records. Back up before rollback. Namespace shutdown cancels undispatched campaign/cleanup work and marks active campaigns cancelled; uncertain remote effects remain evidence. Existing user files and prior feature checkpoints are preserved.

Task-owned PostgreSQL/Redis remain running for the authorized later stages. Next: implement the documented Phase9 UUID service, SQL role/membership constraints, owner confirmations and independent notifications/logs; then Phase10 provenance/versioned ban enforcement, Phase11 portability/privacy/locales/UI, and Phase12 audit/package. Full source/BotFather/live behavior remain external validation limits, not blockers to this local work.

Local checkpoint recorded; continuing according to LONG_RUNNING_MASTER_PLAN.md.
