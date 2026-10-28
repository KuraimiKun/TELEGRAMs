# Long-running implementation checkpoint report

Save one report per stage under `docs/groupguard-rose/reports/`. Update `PROGRESS.md` and continue automatically after the local gate passes. This template supersedes the old template's per-phase wait instruction for the autonomous task.

## Identity and scope

- Stage, authorized work and delivered user behavior.
- Starting/ending commit or precise worktree manifest; pre-existing changes preserved.
- Changed production/tests/migrations/locales/docs paths and purposes; diffstat.
- Stage verdict: local gate passed, incomplete or specific external dependency.

## Feature and contract evidence

| Stable feature ID | Behavior/status | Implementation path/symbol | Concrete test/input and observed effect | Remaining difference |
| --- | --- | --- | --- | --- |

Include every current-stage ID, unfinished work and whole-ledger/per-stage status counts. Record actual public signatures/fields, rights/context mapping, config/default changes, SQL keys/indexes/migrations, Redis key/payload/TTL/claim contracts and job generations/retry/ownership as relevant. Preserve stable IDs and distinguish tested subsets from whole-feature completion.

## Executed validation

| Exact command | Sanitized prerequisites/versions | Exit | Passed/failed/skipped | Relevant output and skip/failure reason |
| --- | --- | --- | --- | --- |

Distinguish reused evidence, new runs, mocks, real disposable PostgreSQL/Redis, blocked checks and live/deployed behavior not tested. Record authorization/tenant/replay/concurrency/API-failure/restart/legacy-data/child outcomes and denied side effects. Explain test-only middleware changes. Keep baseline and new failures separate; never count a skip as a pass.

## Decisions, recovery and next task

- Sourced behavior versus deliberate compatibility/safety/product decisions.
- Migration/default/cache/queue changes, upgrade and rollback/data-loss limits.
- Unresolved source/capability/external requirements, exact blockers and unaffected work continued.
- Disposable resource cleanup and remaining assumptions.
- Next concrete stage/task and dependencies.

End intermediate checkpoints with `Local checkpoint recorded; continuing according to LONG_RUNNING_MASTER_PLAN.md.` Do not request another phase prompt.

At the final stage, instead provide the complete source handoff, identity/file hashes, final validation, full known-gap list, operator documentation and independent-review guide. End with `Cumulative project ready for final code review` only when the master plan's final conditions are met; otherwise state the precise incomplete status.
