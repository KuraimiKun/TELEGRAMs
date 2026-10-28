# Group Guard — autonomous implementation master plan

Prepared 12 October 2026, Asia/Jakarta. Give this entire file and its supporting handoff to the cloud coding agent.

## 1. Assignment and execution authority

Implement the complete publicly documented [Rose feature set](https://missrose.org/docs/) in the existing Group Guard bot and its factory template. Preserve Group Guard's existing behavior and platform integration, implement the features independently, and prepare the complete cumulative project for a separate final code review.

**You are authorized to execute every implementation stage in this plan in one long-running task. Continue automatically between stages after their local acceptance checks pass. Do not wait for intermediate reviewer approval or another phase prompt.** This explicitly replaces all previous instructions to implement only one phase, stop after Phase 1A, or await a per-phase review. Keep the staged structure for dependency order, testing, checkpoints and reports, not as an approval workflow.

Begin with the current repository, complete the Phase 1A evidence/guard checks below, then implement 1B, 1C and Phases 2–12. Do the implementation, tests, repairs, documentation and final packaging; do not stop at another plan or a scaffold. Use judgment for ordinary design choices and record them. If one external dependency is unavailable, record the exact gap, implement/test the locally achievable path, and continue unaffected work. Do not convert a dependency into a fictitious passing result. Stop only when implementation and final handoff are finished, or no meaningful authorized work can continue without an essential external input.

This authorization includes additive migrations, necessary shared-core integration changes, narrow fixes needed to preserve repository checks, and a separate repair of the known baseline DocTools failure. It does not include production deployment, merging/publishing, production-data manipulation, live Telegram moderation or obtaining private Rose infrastructure. Use disposable test services and mocked Telegram unless a live test is separately authorized.

## 2. Starting state: preserve and verify

The reported current cloud HEAD is `96357ef45c6492e03c626581ce2ee156d2da3816` on branch `work`. The Phase 0B source baseline tree is `7895f72031fd4fac13b4ff280ba04b16c8d5842c`, equivalent to reference `d55fc44fe1a63ba5788125c1325d2a855944d5e0`. Phase 1A implementation is reportedly present as uncommitted work: 22 production/test/locale files, 2,272 insertions and 663 deletions. **Do not reset the checkout, replay the supplied bundle, or redo Phase 0/1A from scratch.** Inspect the actual current state and disclose differences from the report.

Phase 1A reports 150 focused passes, a full suite of 371 passed/one known failure/four service-dependent skips, three separately passing integration tests and one separately passing runtime e2e. These are reported evidence, not independent certification. The feature ledger has 818 rows retaining all 812 prior IDs; ten 1A foundation rows are marked tested subsets. Wider parent features remain partial. Rows include aliases, permissions and lifecycle behavior, not just independent feature counts.

The known failure is `tests/bots/doctools/test_review.py::test_malformed_html_and_invalid_encoding_are_controlled`, line 77, `DID NOT RAISE CitationError`, with Python 3.12.14 accepting the reported malformed HTML declaration. Track it separately until a proper production-code repair and regression validation make it pass. Do not hide it with xfail, skip, weakened assertions or dependency manipulation.

Read applicable `AGENTS.md`, `README.md`, `docs/BOT_SDK.md`, `docs/DESIGN_SYSTEM.md`, `docs/OPERATIONS.md`, existing Group Guard code/tests and the cumulative audit/ledger. Preserve immutable history and prior evidence. Use scoped local commits/checkpoints if available, avoiding unrelated changes; otherwise record a working-tree path/hash manifest. HEAD alone does not identify uncommitted code. Keep durable progress in `docs/groupguard-rose/PROGRESS.md` so another cloud session can resume without repeating completed work.

## 3. Specification and uncertainty policy

Use the existing `FEATURE_MATRIX.csv/.md`, `SOURCE_COVERAGE.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `OFFLINE_SOURCE_DIGEST.md` and `PHASE_01A_SOURCE_ADDENDUM.md`. S01–S50 cover 50 documentation pages; T01 covers the [Telegram Bot API](https://core.telegram.org/bots/api). Read current official sources when reachable, including linked tables, variants and clone annotations. Keep concise paraphrases, URLs and dates rather than copying the website.

If cloud retrieval remains blocked, the supplied digest is legitimate specification input. Label it reviewer-supplied condensed evidence; do not claim full-page archival coverage, direct retrieval, live Rose equivalence or deployed API support. A framework method existing is not proof that the deployed server supports it. Inspect the installed SDK and actual available runtime/capability information, and publish required deployment capabilities without upgrading production yourself.

Keep every stable feature ID and decompose remaining broad gaps. Each functional row needs syntax, defaults, caller/bot permissions, contexts, standalone/child applicability, implementation path, positive/negative acceptance evidence and remaining deviations. Retain unresolved source details explicitly; do not silently delete rows or mark a selector/handler name as completion.

Resolve ordinary ambiguity with the best documented, compatible behavior and tests, recording assumptions separately from sourced requirements. Preserve current stored defaults on upgrades. Publish new-group defaults separately. Specific carried decisions:

- `/kickme` has a sourced self-kick purpose; implement self-only in Phase 2 and disablement in Phase 8. `runs`, `saved` and uncertain `antiflood` alias semantics need evidence or an explicit compatibility decision; do not invent a complex feature from a catalog name.
- Settings need change-info, sanctions restrict-members, deletion delete-messages, pins pin-messages, promotions promote-members, topics manage-topics. Owner-only work needs an attributable current creator. A platform/factory owner is not automatically a Telegram group administrator.
- Temporary ban/mute input uses the deliberate local range 60 seconds–365 days inclusive. General timers remain separate. Missing/unsafe timers cannot become permanent sanctions. Preserve valid one-minute sanctions and general ten-second timers.
- Warning/flood threshold ambiguities require explicit per-module boundary decisions and tests. Preserve legacy behavior for existing groups when practical; distinguish the chosen defaults for new groups. Decide approval/federation/raid/newcomer precedence explicitly, with manual moderation always retaining authorized control.
- Document parser compatibility for warntime/setwarntime and repeat/repeated; use declared typed prefixes for the inconsistent lookalike/username examples, and command-cleaning table categories rather than its conflicting example.
- S32 roles, reason policy, owner notifications and log setup belong to Phase 9; ban-list export/import and directed subscriptions belong to Phase 10.
- Unknown full Rose export schemas are not a reason to omit own-format export/import. Do not claim compatibility beyond verified external fields. Unseen runtime-help additions remain a specific gap.
- The newer `LONG_RUNNING_SOURCE_ADDENDUM.md` corrects S37: Rose documents single-word note triggers, not quoted multi-word names. Preserve any existing broader names as a legacy extension and correct the corresponding ledger claim; quoted phrases remain supported for filters/blocklists.
- Admin titles, federation transfer, global bans and cross-bot federation sharing are not mandatory sourced scope. Do not expand into these without a documented requirement.

## 4. Architecture and invariants

Extend `bots/groupguard` using the existing Python/aiogram/core SDK, PostgreSQL/SQLAlchemy/Alembic, Redis namespaces, scheduler and factory lifecycle. Avoid a replacement framework, user-account client, second dispatcher or speculative platform rewrite. Refine the proposed service boundaries based on the current Phase 1A code.

Every feature must work in standalone and actual Group Guard factory children. Scope SQL/Redis/content/media/jobs/permissions to bot identity and the relevant group/user/federation. Test two children plus standalone sharing a group. Credentials and file IDs cannot be assumed portable between bots. Preserve VIP, credits, branding, optional CAS/AI, configured limits and unrelated modules.

Separate actor identity, verified human, source/target chat, target user, message and thread. Require precise fresh rights at mutation time, including union permissions for compound actions, and fresh protected-target checks. Cached admin lists and connection history are conveniences. Anonymous verification authorizes the approving human's exact immutable action; it cannot identify the original anonymous human. Owner actions remain attributable. Validate callbacks against scoped server-side state and expiry.

Keep common argument/boolean/duration/target contracts, a command registry with aliases/context/rights/disable/cleaning metadata, a safe content renderer, typed action outcomes and consistent audit events. All mutation entry points, including PM connections and callbacks, must use the same policy. Direct and automated origins differ; automation still needs real bot capability and current policy. Never infer success from result truthiness or announce completed sanctions after a failure.

Use versioned, additive schemas only when the current feature requires them. Test fresh installs and legacy-data upgrades on disposable PostgreSQL. Preserve unrelated configuration JSON fields and old HTML/media content. Avoid destructive replacement/backfills; document rollback limits where data conversion cannot be reversed.

Build durable bounded work for expiry, cleaning, recurring content and federation fan-out. Use generations, transactional state/outbox where justified, leases, retries/backoff, cancellation and explicit terminal failure. No one-timer-per-member/child design or unbounded Redis `KEYS`. Distinguish exactly-once internal counting/claiming from uncertain external Telegram effects; reconcile uncertain effects and never blindly repeat non-idempotent mutations.

Every new feature needs localized output/help/settings and useful errors. Escape untrusted names/reasons, preserve entity offsets/Unicode, bound payloads/imports and honor Telegram text/callback limits. Logs must have scoped authorized destinations and sanitized failure evidence. Do not log tokens or unrestricted private payloads.

## 5. Stage 1A closure — inspect, preserve, repair only actual gaps

Complete missing handoff material internally, then continue automatically. Record actual signatures, dataclass/enum fields, denial/result postconditions and call-site adoption in `API_CONTRACTS.md`; record Redis review/panel/cache key patterns, schemas, TTLs and atomic claim ordering. Map all ten reported 1A IDs to exact paths/tests. Save exact real-service test commands and identify the four skips. Do not rerun everything merely to rewrite a report.

Confirm that review execution freshly protects a target promoted after review creation, rechecks current caller/bot rights, rejects changed scope/arguments/expiry, and consumes an executed-but-failed request once. Explain pure-SQL bot-status preconditions without fabricating sanction rights. Verify that the test-only throttling fixture does not create false denial evidence: assertions must reach the intended guard, with prohibited effects absent. Keep real runtime middleware coverage.

Preserve valid target/reason parsing, safe deadlines, warning retention after failed sanction, partial-kick outcomes, unknown bulk-deletion count, actual default-permission restoration and pre-closure night snapshots. Add a narrow missing guard/test only if inspection reveals a genuine gap. Checkpoint the cumulative working implementation and proceed to 1B; no report approval is required.

## 6. Stage 1B — routing, protection delivery and capability plumbing

Fix P02/P03/P04/P09 from the audit: edited blocked content escaping protection; core handlers consuming blocked content before Group Guard checks; `gs_` settings start links opening home; missing edited/reaction subscriptions.

Create one explicit Group Guard message pipeline that runs at the correct outer point for normal and edited group messages, before early core-handler consumption. Preserve private core flows, terms/support/payment functions and other bots. A blocked group command must not bypass protection through `/terms` or `/admin`; a settings/help route must still select its correct target and enforce fresh authorization.

Classify human, bot, anonymous group and sender-channel origins without blanket exemptions. Define event precedence and handoff to service/command/content handlers; keep documented locks-before-blocklists. Changes to message content must be checked on edit, but editing is not a new flood message or raid join. Introduce clear event identity/version contracts for the replay implementation in 1C.

Audit allowed updates for standalone polling/webhooks and factory polling/webhooks. Wire the events later features need, including edited messages, reactions and relevant membership/join-request events, with explicit observer/capability behavior. Full reaction lock semantics are Phase 5. Do not expose settings that falsely promise unavailable enforcement.

**Gate:** dispatcher tests reproduce and fix all four defects in standalone and actual children; normal/edited captions/entities/core-consumed content are checked; legitimate private flows, payment processing, bound settings/deep links and other bots remain functional; subscriptions are asserted for each delivery mode. Record actual SDK/deployment prerequisites and unknowns.

## 7. Stage 1C — concurrent state, replay and lifecycle foundations

Fix P05/P06/P07/P08: lost configuration edits across service instances, concurrent warning thresholds, stale CAPTCHA expiry after success and old callbacks affecting a replacement challenge. Also repair factory child job/restart/night-off transitions requiring this foundation.

Use database transactions/revision checks for field-level configuration updates and cross-worker cache consistency. Make warning records identifiable, expiry/removal idempotent and threshold action coordination safe under parallel warnings. Keep failed-action history; avoid double sanction/reset and distinguish an action intent from its external result.

Give challenges/requests generations and immutable issued policy/deadlines. Atomically coordinate answer/expiry/attempts, match the actual request/message/user, and prevent a stale job from acting on a later generation. Restriction ownership must distinguish CAPTCHA/newcomer/manual/night/federation state so one completion cannot remove another restriction.

Implement bounded delivery/replay identities so duplicate webhooks and repeated callbacks do not recount messages/joins, increment warnings twice, send repeated content or repeat action intents. Changed edits get their own content version without recounting flood. Use the minimum durable jobs/outbox/generations needed for concrete flows, with leases/recovery/cancellation for pause/unload/delete/restart. Preserve a restorable night snapshot beyond an unsafe transient TTL.

**Gate:** real PostgreSQL/Redis tests cover two writers preserving unrelated config fields, parallel threshold/removal, duplicate updates, replacement challenge versus stale answer/expiry, simultaneous answer/timeout, crash/restart, permission revocation, failed API/retry and child lifecycle. An uncertain Telegram call cannot be advertised as exactly-once delivery. Fresh and legacy-data migration checks pass.

## 8. Phase 2 — complete moderation and administrator tools

Implement all restriction families and forms: `ban/tban/dban/sban/unban`, `mute/tmute/dmute/smute/unmute`, `kick/dkick/skick`, and self-only `kickme`. Support reply, ID and known-username targets and optional reasons. Temporary forms require safe duration; delete-and-act forms require replies. Silent manual variants have their documented deletion/no-confirmation effects while retaining audit evidence. Preserve existing aliases and separate manual silence from later automated-silence gating.

Complete `warn/dwarn/swarn/rmwarn/resetwarn/warns/warnings`, warning limit/mode/time controls and compatible legacy spellings. Store exact warning identities/reasons/expiry; removal buttons remove that warning, not an unrelated latest row. Threshold/reset uses completed sanction postconditions and concurrency coordination.

Implement promote/demote, public admin listing that omits anonymous identities, adminerror, admincache and anonadmin. Promotions cannot exceed caller/bot intersection or grant promotion rights. Demotion respects editability. Optional anonymous assumption mode is off by default, explicit and documented; it applies only to the supported same-group anonymous actor and never owner-only operations. Keep verified human authorization as the default.

Complete approve/approval/approved/unapprove/unapproveall, reasons and bounded/file listings; only creator clears all. Implement reports and `@admin`, info/ID forms, precise private/group routing, log setup/categories/status/removal with actual source/destination authority, and the existing numeric log shortcut as an extension. Implement pin/permapin/unpin/unpinall, quiet/loud pinning and linked-channel pin/cleanup controls. Complete del/purge/spurge/purgefrom/purgeto, bounded counts/ranges and actor-bound two-step endpoints. Bulk acknowledgement is not a factual deletion count.

**Gate:** every command/variant has observable success, wrong-right/context/target denial and API-failure tests; all approval/default/owner boundaries are tested; warning expiry/removal is restart-safe and idempotent; anonymous identity remains private; command side effects/audit/results agree in both runtimes.

## 9. Phase 3 — shared formatting, rules, notes, filters and greetings

Implement one renderer/content model for Rose syntax, Telegram entities and legacy saved HTML/media. Support styles, quotes/expandable quotes, links, URL/same-row/note-menu buttons, all documented fillings/control modifiers and random `%%%` alternatives. Parse control tokens rather than displaying them. Keep media flags, reply identity, length/Unicode/entity handling and safe escaping consistent across previews and delivery. Provide an integrated working button-markup helper.

Complete rules set/read/reset/private delivery/custom-reset button and `{rules}` linking. Complete welcome/goodbye enablement, text/replied attachments, preview/raw/reset forms and correct joining/departing identity. Implement five-minute old-welcome cleanup using shared durable cleaning, distinct from service messages.

Complete save/get/hashtags/notes/clear/overwrite, note media, private/noprivate/admin access and correct reply/filling context. Canonical names are single words under the source correction. Preserve old broader content safely as an explicit extension. Implement genuinely scheduled repeat/repeated notes with durable cadence, permission/capability checks, change/delete cancellation, bounded catch-up and child lifecycle support.

Complete filter/stop/stopall/filters with words, quoted phrases and parenthesized multiple triggers; media payloads; prefix/exact; replytag; user/admin controls; bot opt-in and custom-clone command suggestions/descriptions. Validate command spelling against actual Telegram limits and distinguish documented clone wording. Publish/update/remove suggestions in the correct chat scope.

**Gate:** parser/render cases include malformed markup, literal escapes, nested styles, Unicode/RTL, hidden URLs, callbacks/PM unavailable and every supported attachment. Trigger collisions, privileged note access, real button navigation, legacy migration, recurring restart/updates/cancellation and previews versus delivery are tested; no placeholder helper or schedule selector.

## 10. Phase 4 — CAPTCHA and newcomer lifecycle

Implement button, text-image, math and text2 challenges, private challenge flows, custom/reset plaintext labels, rules acceptance, kick/deadline/mute-time settings and default behavior from S23. Generate actual image challenges where required. Enforce documented welcome dependencies without silently disabling existing protections.

Persist issued challenge generation/answers/attempt budget/deadline/policy; solved-member memory is group-scoped, with admin-kick reset and voluntary-leave behavior. Join requests retain the actual applicant/contact window/request status and must not be approved after expiry or failed verification. Welcome only at the appropriate completed membership transition.

Integrate CAS, AI spam and newcomer checks as optional existing controls. CAPTCHA success releases only its own verification restriction; it cannot override a manual/federation restriction or closed/night permissions. Use shared intent/deadline/ownership primitives for answer/expiry/reset/rejoin and API retry outcomes.

**Gate:** every mode's positive/negative/attempt-limit/timeout/rejoin/reset path; blocked PM, missing rights, stale generation, answer versus expiry, multiple chats/children, restart and failed/expired join requests. Image-mode selection without a functioning challenge fails the gate.

## 11. Phase 5 — full lock roster and allowlists

Implement every S22 lock token individually, not just current plural aliases. Cover text/entities/Unicode, media variants/albums, message buttons/commands, origin/forward types, sender channels, inline/guest bots, linked-discussion outsiders, reactions and outsider reactions. Use the complete roster in the digest/ledger; reconcile any new official rows. Preserve existing aliases without collapsing distinct canonical locks.

Complete status/types/listing, multi-lock changes, lockwarns and per-lock reasons/actions. Implement allowlist/rmallowlist/creator-only clear and each domain/subdomain/path, exact invite/chat reference, command, bot/channel/forward identity and sticker/custom-emoji-pack kind. Normalize safely: lookalike/suffix domains and broader neighboring paths are not accidentally allowed. Honor documented admin/approval behavior and locks-before-blocklists precedence.

Reaction/outsider handling needs real event classification, suitable subscriptions, current membership evidence and supported removal methods. Surface missing deployment capabilities with useful diagnostics; do not simulate enforcement or globally assume impossibility.

**Gate:** one positive and neighboring negative acceptance case for every canonical lock and allowlist kind; captions/hidden URLs/edits/anonymous origin/linked posts; per-lock sanctions and capability failures; reaction event paths in standalone and children. No token merely stored without enforcement.

## 12. Phase 6 — advanced blocklists

Migrate current phrases intact into typed triggers with optional actions/reasons. Complete add/remove/list/bulk-clear, quoted and multiple triggers, default/per-entry modes, deletion on/off, fallback reasons and gated silent actions. Preserve legacy add/remove aliases and explicit list-versus-add argument semantics.

Implement full-word/accent/space normalization, escaped `?`, `*`, `**` matching with bounded complexity, and every typed trigger: sticker/custom-emoji packs, filenames/extensions, forwarded/inline identity, prefix, exact, lookalike, observed name and username patterns. New profile checks happen on observable join/speaking events; do not claim unseen profile-change detection. Use the documented prefix family and record source-example typos.

**Gate:** wildcard/escape/multi-trigger/normalization boundaries, false matches and long adversarial input; attachment/origin/profile triggers; per-entry overrides, warning/deletion independence, exemptions/precedence, owner clear and migration. No unbounded regex execution or unrelated trigger deletion.

## 13. Phase 7 — antiflood, anti-raid and night completion

Implement consecutive-message and per-user time-window flood modes, independent counters/thresholds, status/limit/timer/mode controls, timed/silent sanctions and clearflood exceeded-only versus entire observed sequence. Duplicates/edits do not recount; event/message IDs remain bot/chat/user scoped. Preserve existing settings/defaults through migration and disclose chosen boundary differences.

Implement antiraid status/enable/configured-or-override-duration/off, separate active and ban periods, autoantiraid joins-per-minute and its off form. Persist activation/deadline/action policies with bounded jobs. Decide and test admin/approved/federation/newcomer precedence rather than assuming a global exemption.

Finish night scheduling/permission ownership/recovery, including settings-off restoration, process restart, child pause/unload/delete, timezone changes and failed API retry. Do not restore stale permissions over later authorized group changes or fabricate an open permission set after a failed lookup.

**Gate:** interleaved/consecutive/window edge cases, threshold equality, replay, burst joins, activation overrides/expiry/off, missing rights, overlapping restrictions and restart. Stress assertions include actual actions and bounded work, not counter values alone.

## 14. Phase 8 — connections, disabling, cleanup, topics and advanced utilities

Implement connect/disconnect/connection/reconnect and context-sensitive ID. Any current member may connect for available reads; only precise authorized humans mutate. Support PM ID/public-group username, personal group connection buttons, one active group and last-five history. Revalidate membership/rights on every protected operation; history, callbacks and another child's state are never authority.

Implement disabled/disableable/disable/enable/disabledel/disableadmin with canonical aliases and published catalog coverage. Disabled execution, optional deletion, bot/system exceptions and command cleaning are distinct. Route commands/callbacks through shared metadata so a PM, alias or panel cannot bypass policy.

Complete command cleaning (all/admin/user/other), bot-message cleaning (all/action/filter/note, five-minute delay), service cleaning (join/leave/other/photo/pin/title/videochat), and old-welcome cleanup. Run functional payment/service processing before cleanup; missing service updates are not evidence of a successful deletion.

Implement action-topic configuration/reporting and new/rename/close/reopen/delete topic commands. Shared group settings remain consistent; handle general/deleted/missing topics and precise manage-topics rights. Add appropriate scoped confirmation for destructive topic deletion.

Implement echo/say and bot-owner broadcast with bounded delivery, retries and destination isolation. A group admin cannot address all platform groups. Define standalone operator and factory-child owner authority from actual platform configuration without granting unrelated Telegram group rights.

Implement creator-only automated silentactions enablement with log requirement, explicit action selection and loud fallback when disabled/log removed. Keep manual silent variants separate. Implement bot2bot off/admin/all, default human review for bot-admin mutations, explicitly configurable skip-review without authority escalation, filter opt-in and deployment prerequisites. Bound self/reply loops and review replay; bot senders never inherit creator authority.

**Gate:** removed/demoted connected members denied; alias/PM/callback policy parity; payment-before-cleanup; delayed deletion restart; missing forum targets; wrong broadcast owner/tenant and throttled fan-out; bot review/rights/loop cases. Existing private platform functions remain correct.

## 15. Phase 9 — federation management and membership

Build our own bot-scoped federation service; it cannot join Rose's private federation network by copying an ID. Implement newfed/renamefed/delfed, one owned federation per user, PM context, documented name length behavior and safe deletion confirmation. Deleting a federation must not unban every formerly banned Telegram user. Do not add transfer/global-ban/cross-bot trust as mandatory scope.

Implement owner-controlled fedpromote/feddemote, feddemoteme, fedreason, fednotif and setfedlog/unsetfedlog with proper owner confirmation/channel authority. Add any consent behavior only when sourced. Notifications and logs are independent. Implement fedinfo/fedadmins/chatfed/myfeds and creator-only group joinfed/leavefed plus quietfed. Local group administrator, group creator, federation owner and federation admin are separate roles.

Use indexed tenant constraints, stable federation identifiers, role/membership records, configuration and audit history. Require the correct role at execution, not just a stored callback/invitation. Federation deletion, leave and child lifecycle cancel stale relevant work without leaking authority into siblings.

**Gate:** role/context matrix, one-owner limits, names/IDs, cross-bot denial, membership changes, wrong-owner callbacks, private command target selection, destination logs/notifications and retained Telegram bans after federation deletion. Legacy groups remain usable without a federation.

## 16. Phase 10 — federation bans, subscriptions and enforcement

Implement fban/unfban, reasons, fedstat/fbanstat forms, user status/date/source, fbanlist formats/rate limiting, importfbans and subfed/unsubfed/fedsubs. CSV and newline JSON imports need real validation, size limits, duplicate/error handling and documented ownership. Preserve the S32 export interval and exact format distinctions from the digest; do not silently treat JSONL as only a JSON array.

Group fban authority comes from that group's federation role; PM targets the user's owned federation even when a chat connection exists. Active enforcement fans out to observed users in attached groups without extra per-group visible/log notifications. Passive joining/speaking checks include subscribed bans and explain source unless quietfed. Store minimal observed membership, not an invented full Telegram member inventory.

Use durable bounded fan-out with per-bot capability/rate control, versioned ban intents, retry/backoff/terminal evidence and cancellation. An old queued ban must not overtake a newer unban. Subscription graph changes and multiple sources retain provenance; removing one source must not remove another source's ban or an unrelated local restriction. Explicitly document cycle/self-subscription policy and uncertain external restriction ownership; prefer a safe non-destructive outcome to an unsupported unban.

**Gate:** direct/multiple/subscribed bans, graph changes, unban provenance, newly joined groups, observed/unobserved users, correct private targeting, quiet/log distinctions, concurrent ban/unban ordering, restart, revoked rights, paused/deleted children and malformed imports. Tests verify resulting API effects and failure evidence, not just queued jobs.

## 17. Phase 11 — portability, privacy, locales and complete UI

Implement export/import/reset with schema versioning and module selection, admin export, creator-only import/reset, confirmation/replay protection and bounded files. Define a local rate policy for unspecified intervals and record it. Every portable module must round-trip; omitted modules and unknown JSON fields must not be accidentally destroyed. Validate external/media/destination references; identity, ownership, trust, issued challenges and stale jobs are not blindly restored. Provide real compatibility adapters only for verified Rose formats and label unsupported fields.

Implement PM privacy policy/data access/deletion for the requesting human, scoped per bot. Inventory actual data fields, explain active moderation/federation/security-record treatment and propagate permitted deletion through caches/queues. Use an explicit minimal-retention policy derived from actual feature needs and preserved existing behavior; document unsourced defaults/configuration instead of attributing invented time periods to Rose. No blanket erasure that removes someone else's records or silently defeats active moderation. Test access isolation and post-deletion job/cache behavior.

Complete group/connected response language selection and independently authored translation coverage for every published S07 locale. Current roster: AR, AZ, BE, BG, CKB, DE, EN-GB, EN-PT, ES, ES-AR, FA, FIL, FR, HE, ID, IT, ML-IN, MS, NL, PL, PT, PT-BR, RU, SH, TA, TR, UK, UZ, VI, ZH-CN, ZH-TW. Preserve existing locale aliases. A selector with English fallback is not translated feature parity. Check keys, placeholders, plural/select branches, RTL/scripts and rendered examples; disclose translation-quality limits separately from functional coverage.

Make every feature discoverable in help and appropriate settings/panels with pagination/search where useful, valid context/deep links, capability diagnostics and localized errors. Include onboarding, command suggestions, confirmation/cancellation and content-editor helpers. Preserve localized Group Guard help, credits/VIP and child branding. No inaccessible settings that merely save a flag.

**Gate:** every module round-trip/migration, cross-tenant/unsupported/versioned import, owner/replay/rate protection, reset with job cancellation, own-data access/deletion, real locale content/placeholder parity and complete feature-to-help/UI mapping. Full source question/feature/deviation counts are current.

## 18. Separate baseline repair and Phase 12 final validation

Repair the known DocTools failure in a separate scoped checkpoint, after inspecting its intended malformed-input contract and Python parser behavior. Make the production path reject/control the unsupported malformed case without disrupting valid HTML/encoding handling. Keep a meaningful regression test and valid-input cases; do not merely change the expected result to make the count green. This narrow repair is authorized by this master plan; broad DocTools feature work is not.

Audit the entire cumulative change as if reviewing another author's work. Inspect authorization/tenant boundaries, actor and callback models, default/migration compatibility, parsing, API outcomes, queue/retry/restart behavior, media portability, logging/privacy, locales and all shared-core changes. Reconcile every functional ledger row with actual implementation and tests. Repair findings and rerun appropriate checks; a long diff or many passing tests does not replace this review.

Execute final fresh-install and old-baseline-with-data upgrades on disposable PostgreSQL; real Redis race/restart/lifecycle tests; actual standalone plus two-child Group Guard flows; all repository mandatory checks and runtime e2e. Add representative burst/fan-out benchmarks with stated volume/environment and measured results, avoiding performance claims beyond observed evidence. Verify shutdown/cleanup, constrained payloads and bounded job/queue behavior.

Document SDK/local Bot API prerequisites, webhook/polling events, BotFather requirements, migration/backup/rollback/data-loss limits, operation/error diagnostics and deployment/canary/manual QA steps. Do not run production deployment or live group tests. Distinguish mocked Telegram evidence, real disposable services and any unverified deployment/live behavior.

Your internal audit and packaged result do not replace the separate reviewing agent's final source review. Hand over the full project so that independent review can occur after this long-running task.

## 19. Recurring validation, checkpoints and continuation

For each stage, implement a coherent slice, run meaningful focused tests, repair failures, update feature/contracts/source/decision records, save a checkpoint/report and continue. Run lint/type/contracts after substantive code changes. Run the full suite and real-service checks when shared runtime, migrations, concurrency or lifecycle change, and at the final gate. Do not repeatedly rerun unchanged passing suites solely for ceremony.

Use the established virtual environment. Typical commands (record the exact executed forms and environment):

```text
.venv/bin/python -m pip check
.venv/bin/python -m core bots
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/pytest -q tests/bots/groupguard tests/bots/factory tests/test_locales.py --tb=short
.venv/bin/pytest -q --tb=short
TEST_DATABASE_URL=<dedicated disposable PostgreSQL URL> TEST_REDIS_CLAIM_URL=<dedicated disposable Redis DB> .venv/bin/pytest -q tests/integration --tb=short
TEST_DATABASE_URL=<dedicated disposable PostgreSQL URL> TEST_REDIS_URL=<dedicated disposable Redis DB> .venv/bin/pytest -q tests/e2e --tb=short
git diff --check
```

Preflight service URLs: integration tests may drop the configured PostgreSQL schema and runtime tests empty their chosen Redis database. Provision dedicated test resources; never aim them at shared/production data. Clean up only resources created by this task. Record every skipped/blocked check with a reason and execute required categories against real disposable services before claiming final validation complete.

All permission, callback, action and lifecycle changes need observable positive/negative dispatcher/service tests in standalone and actual children. Include precise rights, demotion/revocation, protected targets, forged/stale state, duplicate/concurrent delivery, failed Telegram steps, interrupted jobs, namespace isolation and legacy data. Tests should assert required/forbidden side effects and result text, not mirror implementation details. Explain any test-only middleware bypass and preserve actual runtime coverage.

Use `LONG_RUNNING_REPORT_TEMPLATE.md`. Maintain `PROGRESS.md` with current stage, completed gate evidence, exact worktree/checkpoint, open failures/dependencies and next concrete task. On context/session limits, save state and resume from it; do not start over. Maintain a concise changelog. No intermediate report needs external approval; do not end a completed stage with 'awaiting the next prompt'.

## 20. Final deliverables and completion rules

Provide one complete cumulative handoff, not merely snippets, a patch omitting new files or an archive of the old HEAD. Package the **actual finished working tree**, including new/untracked implementation files if still uncommitted:

1. Complete source, tests, migrations, locales, needed assets/licenses, dependency/environment examples and platform configs needed to build/run the project. Exclude secrets, real `.env`, private uploads/data, virtual environments, caches and bulky test containers. Include exact revision/working-tree identity and a SHA256 file manifest.
2. Baseline-to-final diff/diffstat and scoped commit history or an equivalent file/change manifest; clearly separate baseline cherry-picks, feature work, shared-core changes and the DocTools repair.
3. Updated ledger/coverage/counts, decisions, actual public/Redis/SQL/job contracts, migration/legacy-data/rollback evidence, all saved phase reports and concise relevant test outputs.
4. `FINAL_REVIEW_HANDOFF.md`: self-contained final summary, implementation status by family, exact commands/results/skips, source provenance, security/tenant/restart evidence, deliberate differences, unresolved external requirements and precise independent-review entry points.
5. Operator/user documentation with command/context/right/default tables, settings and localization coverage, deployment prerequisites, sample configuration and reproducible disposable-service test/setup commands.

Inspect the final archive by extracting/listing and verifying its manifest; ensure it includes the current implementation and that no credential/private artifact is included. Supply the downloadable artifact/path, final identity and concise summary in your final response. Report substantive remaining gaps inline, not only behind cloud file links.

Call the result **ready for final code review** only when the local gates are met, all supplied functional requirements have implementation/test evidence or a clearly listed unresolved dependency/difference, the complete project is packaged, and no new test failure remains. The known baseline failure must be properly repaired before claiming a fully passing suite. Do not claim full Rose parity when unresolved functional/translation/capability rows remain; state exactly what is incomplete. Do not self-certify independent review or production readiness.

**Start now:** inventory and checkpoint the current Phase 1A working tree; complete its contracts/security evidence; execute 1B, 1C, 2–11, the narrow baseline repair and 12; then deliver the cumulative project. Continue through locally reviewable repairs and stages without requesting another phase prompt.
