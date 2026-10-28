# Phase2 moderation and administrator tools

Starting checkpointd92405e. Local gate passed with the one named pre-existing DocTools failure; continuing automatically to its separate repair and Phase3. No reset/replay/deployment/live moderation.

Delivered ban/tban/dban/sban/unban, mute/tmute/dmute/smute/unmute, kick/dkick/skick and self-only kickme. All use the existing immutable operation/fresh rights/strict target/action contract. Delete/silent forms preflight deletion rights on both caller/bot. Silent forms remove command/reply, suppress group confirmation and retain private audit/configured logs. Kick is ban then only_if_banned unban, preserving partial evidence.

Warnings add dwarn/swarn/resetwarn plus compatible spellings, settings, all five threshold modes, age/off controls and exact record listings/files. New age is captured with locked current config; positive duration changes affect future warnings. Off cancels not-yet-expired ages without resurrecting expired history. Exact-ID removal, SQL expiry and cutoff/reset generations retain the1C contract. Failed/uncertain sanctions preserve history; silent threshold logs without confirmation. Legacy mute duration remains until explicitly selecting a warning mode.

Promote/demote require exact current promote rights, editable targets and the caller/bot permission intersection across every installed API permission. Never grant promotion/anonymous rights or edit creator/bot/noneditable admins. Public admin listings/reports omit anonymous identities. Admincache invalidates stale display data. Adminerror only changes permission responses. Explicit anonadmin defaults off; on applies only to same-group anonymous actor, bounded by bot rights and never creator authority. Owner-only clearing still identifies a real creator.

Scoped approval SQL stores user/reason/actor/date. Trusted users bypass message automation, while manual authority remains separate. Public statuses and paginated/file inventories work; creator-only clear enforced. Join/security precedence stays with owning later phases. Reports/@admin and aliases reach Group Guard rather than platform private UI. Public info/ID handle available self/reply/known username/ID and actual membership; federation profile context remains10.

Per-message tools support quiet/loud pin, actual new-message permapin, unpin/unpinall, linked-channel pin/cleanup controls, del/purge/spurge/count and human/chat/topic-bound two-step endpoints. Cap300IDs,10min endpoint state and one-use claim; requested/acknowledged IDs remain distinct from unknown confirmed deletion counts. Full Rose syntax/media joins permapin through Phase3’s shared renderer.

Logs support numeric extension and original channel setup with actual server receipt/forward origin, source/destination rights and bot post capability. Factory subscriptions now deliver channel_post as well. All six categories default enabled; real filtering is used by settings/admin/automation/reports and member logs. Leave logging stops at>=50 members, unknown count skips that log.

Migration0011 adds bot-scoped approvals, GuardRestriction.state and its bot/state/updated_at recovery index. Review found interrupted manual mute ownership could otherwise disappear before SQL commit. Intents now commit before RPC with pending/applied/uncertain state; known failure restores prior evidence, crash/unknown results preserve ownership. Real PostgreSQL proves interruption after the API mute cannot let verification clear it. This is conservative uncertainty, not exactly-once delivery.

Feature evidence: evidence/long-running/phase02/feature-evidence.csv maps every134 current-stage IDs to actual paths/tests and remaining scope. All prior818 IDs retained; added S17-C-kickme separately from its Phase8 disable row. Cumulative819 rows,808 canonical IDs, current scope128 tested subsets/6 partial (federation info, security approval precedence, other threshold boundaries). Whole-ledger counts in LEDGER_COUNTS.json. No whole-family/translation/live parity self-certification. CSV normalized to LF; historical source/archive unchanged.

Checks (exact commands, saved output):

| Command | Exit/result |
|---|---|
| .venv/bin/pytest tests/bots/groupguard tests/bots/factory tests/test_locales.py -q --tb=short | 0;384 passed on frozen production tree |
| .venv/bin/pytest -q --tb=short | 1;605 passed,32 service skips,only named baseline DocTools failure |
| .venv/bin/pytest tests/bots/groupguard/test_phase02.py -k 'admincache_report or each_warning or leave_log' -q --tb=short | 0;21 passed/183 deselected; added after full collection, covers all warning dispatch modes and actual status/cache aliases |
| .venv/bin/pytest tests/bots/groupguard/test_phase01c.py tests/bots/groupguard/test_phase02.py -q --tb=short | 0;216 passed, pre-RPC ownership core regression |
| .venv/bin/pytest tests/test_locales.py -q --tb=short | 0;20 passed |
| TEST_GG_DATABASE_URL=<gg_long_concurrency> TEST_GG_REDIS_URL=<taskRedis/2> .venv/bin/pytest tests/integration/test_groupguard_foundations.py -q --tb=short | 0;27 real PostgreSQL+Redis passes |
| TEST_DATABASE_URL=<gg_long_integration> TEST_REDIS_CLAIM_URL=<taskRedis/1> .venv/bin/pytest tests/integration/test_migrations.py tests/integration/test_groupguard_review.py -q --tb=short | 0;4 passes, fresh/legacy/roundtrip/model diff and real Redis approval |
| TEST_DATABASE_URL=<gglong> TEST_REDIS_URL=<taskRedis/0> .venv/bin/pytest tests/e2e -q --tb=short | 0;1 runtime pass |
| .venv/bin/ruff check .; .venv/bin/mypy; .venv/bin/python -m core bots; .venv/bin/python -m pip check; git diff --check | 0;252 typed source files,9 module contracts,dependencies valid |

Task-owned services only: PostgreSQL127.0.0.1:55433/role gglong, databases gg_long_integration/gg_long_concurrency/gglong; Redis127.0.0.1:56380 DB0/1/2. No shared or production data/service. Retained for later stages. Mock Telegram API records actual side effects; actual ChildRegistry710011/710012 contexts used. Group conversation fixture bypasses throttling only (tests/bots/groupguard/conftest.py); existing1B real-throttle tests and runtime e2e remain passing.

An earlier full run crossed catalog edits and reported a stale locale-snapshot failure; discarded that mixed-tree result and reran frozen production. Final frozen full run has only tests/bots/doctools/test_review.py::test_malformed_html_and_invalid_encoding_are_controlled, unchanged DID NOT RAISE CitationError. Test-only mistakes (asserting generic error wording and misplaced appended fixture lines) were corrected without relaxing production contracts. Self-kick API failure adds3 separately passing cases; no xfail/suppression/dependency hiding.

Decisions/current public contracts/defaults/rights in DECISIONS.md, API_CONTRACTS.md and COMMANDS.md. Supporting digest provenance unchanged, full archived/live Rose behavior and deployed Bot API capability remain unverified. Shared renderer/media, join/CAPTCHA/security precedence, federations,31 translations/UI and remaining families are still their assigned stages. Source/migration rollback evidence is preserved; dropping approvals during downgrade loses that new table’s data, so downgrade requires backup.

Next: separately repair the production DocTools declaration parser; then Phase3 renderer/rules/notes/filters/greetings and durable repeated notes, continuing automatically through all remaining stages.

Local checkpoint recorded; continuing according to LONG_RUNNING_MASTER_PLAN.md.
