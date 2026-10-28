# Cloud agent phase report

Return this report in your final response, with relevant content inline. The reviewer cannot inspect the cloud files or commits until the final cumulative source handoff. Persist a copy as `docs/groupguard-rose/reports/PHASE_XX.md`.

## Identity and verdict

- Phase number/title and authorized scope:
- Starting commit, branch and pre-existing working changes:
- Ending commit/branch, or exact uncommitted state if commits are unavailable:
- Verdict: `ready for report review`, `incomplete`, or `blocked`.
- What the bot can now do (or, for Phase 0, what was established):

## Changed artifacts

List each changed path and purpose. Include diffstat and separate production code, migrations, tests, locales and documentation. Identify unrelated/pre-existing changes without altering them.

## Feature evidence

| Feature ID | Behavior delivered or audited | Implementation path | Test/scenario and result | Remaining deviation |
| --- | --- | --- | --- | --- |

Include every ID owned by the current phase, including unfinished ones. Give representative end-user commands and observable results for implementation phases.

State whole-ledger and current-phase counts by status. List all unresolved dependencies, deviations and known failures; stable IDs and reasons matter more than a completion percentage.

For Phase 0, include the complete compact inventory grouped by module, all source page/section coverage, new/partial/existing behavior, command variants/modifiers, owning phase and open questions. A statement that the matrix exists in the repository is insufficient.

## Contracts needed for the next prompt

Include relevant public symbol names, signatures, return/error behavior, locations, actor/permission mapping, configuration field names/types/defaults, table names/keys/constraints/indexes, migration revisions and dependencies, cache/version behavior, Redis state/key schemas and job lifecycle. Summarize contracts, not entire source files. Explain which proposed contracts remain unimplemented.

For Phase 0, include the architectural blueprint, schema/upgrade plan, dependency/capability versions and exact recommended Phase 1 scope and acceptance cases.

## Executed checks

| Exact command | Environment/prerequisites (sanitized) | Exit code | Passed | Failed | Skipped | Relevant output or reason |
| --- | --- | --- | --- | --- | --- | --- |

Distinguish executed, attempted-but-blocked, and not-run checks. Include concise failure output and reasons for every skipped test category. State whether PostgreSQL/Redis and Bot API evidence came from real disposable services, mocks, or live authorized QA. Do not fabricate output or describe skipped suites as passing.

## Safety, migration, and runtime evidence

Report concrete negative/edge scenarios and their outcomes: permission denial, wrong user/chat/bot, stale or replayed callbacks/updates, concurrency, Telegram API failure, restart/deadline/retry behavior, legacy data/default preservation, and child-bot isolation. Use `not applicable` with a reason where appropriate.

Include migration/backfill results and rollback/data-loss limits. Explain cleanup of temporary resources. List any unverified assumption affecting correctness.

## Remaining work and next-phase handoff

- All unfinished current-phase items and exact blockers:
- Baseline failures versus new failures:
- Decisions/deviations and supporting source or evidence:
- Required environment/capability follow-up:
- Next phase dependencies and recommended bounded work:

End with: `Stopped after Phase XX. Awaiting the reviewer's next prompt.` Do not begin another phase from the roadmap.
