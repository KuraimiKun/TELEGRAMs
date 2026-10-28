# Group Guard: Rose feature parity implementation plan

Prepared 12 October 2026 (Asia/Jakarta). Documentation reference: [Miss Rose](https://missrose.org/docs/).
Local repository inspected at `d55fc44fe1a63ba5788125c1325d2a855944d5e0`. The cloud agent must report its own baseline; it may differ.

## Objective and working agreement

Extend the existing `bots/groupguard` module to implement the complete publicly documented Rose feature set, while preserving Group Guard's existing features and its factory template. Implement the behavior independently within this platform. Keep Rose-compatible command names and syntax alongside working Group Guard aliases wherever feasible.

The scope includes documented variants, settings, default behavior, permissions, media support, message modifiers, private-chat flows, and newer/custom-clone features described in the docs. A command handler alone is not feature parity. Features that depend on Telegram capabilities or external services must remain visible in the ledger, with evidence and an implementation or explicit unresolved dependency. Rose's hosted bot identity, private spam data, and existing federation network cannot be obtained by implementing its commands; provide equivalent services in our own bot and describe that boundary.

The cloud agent implements one authorized phase at a time and retains the cumulative repository. Its reports are the only intermediate material available to the reviewing agent. A report may be accepted provisionally to start the next phase; this does not certify unseen code. Final acceptance requires the complete source project and independent code review and testing. Do not send all future phase prompts at once. After each report, the reviewer either issues a repair prompt or the next phase prompt. Stop after each phase until that prompt arrives.

This planning handoff contains no application code changes. Local baseline tests were not run for this planning-only task; Phase 0 establishes the cloud baseline.

## Existing platform to preserve

| Area | Inspected implementation | Implication |
| --- | --- | --- |
| Runtime | Python 3.12+, aiogram 3, shared `core` SDK | Extend the module; avoid introducing a second framework or user-account client. |
| Storage | PostgreSQL/SQLAlchemy/Alembic; `gg_chats`, `gg_warns`, `gg_items` | Upgrade existing data with additive, reviewed migrations. Preserve keys and records. |
| Transient state | Redis, bot key namespaces, shared scheduler | Jobs must work after restart and across replicas. Factory children use shared sweeps. |
| Bot modes | Standalone Group Guard and factory child template | Every applicable feature must work in both, with isolated data. |
| Current features | Basic restrictions, warnings, purge, pins, reports, rules, welcomes/goodbyes, button/math CAPTCHA, join requests, CAS, newcomer checks, AI spam checks, nine locks, basic blocklist, notes/filters, private settings, night mode | Extend and repair existing behavior; preserve optional AI, CAS, night mode, credits, limits, and branding. |
| Localization/UI | Fluent, Group Guard English/Arabic, shared core locale fallbacks and UI helpers | New features need localized responses and settings, not just commands. |
| Tests | Recording Bot API, fakeredis, SQLite unit tests; PostgreSQL migrations; real-service runtime harness | Use real dispatcher flows and database/Redis integration evidence where appropriate. |

Read `README.md`, `docs/BOT_SDK.md`, `docs/DESIGN_SYSTEM.md`, and `docs/OPERATIONS.md` before coding. Inspect applicable `AGENTS.md` files in the cloud checkout.

### Concrete audit priorities from the local source

These are observations to verify against the cloud baseline, not a substitute for the full audit:

- `perms.sender_rights()` currently gives anonymous group senders `creator=True`; owner-only operations must never infer a human owner's identity this way.
- `module.py` installs protection on the group `message` observer. Audit edited messages, messages consumed by earlier core routers, sender-chat posts, and reactions as separate paths.
- `core/factory/webhooks.py` lists child update types explicitly and currently omits reaction updates. Check standalone webhook/polling and child webhook/polling delivery independently.
- Warning addition, counting, reset, and punishment use separate steps. Audit concurrent warnings and preserving state when the Telegram action fails.
- Configuration updates read/modify/write cached JSON. Audit lost updates and cache invalidation across replicas.
- CAPTCHA completion, expiry, and attempt counting need concurrency and replay checks. Join-request verification must retain the actual request state.
- Existing `/sban` does not implement every documented silent-action side effect; `/tban` and `/tmute` may accept missing durations. Existing aliases must remain usable, while explicit temporary commands reject invalid input.
- Native media references belong to a bot's credentials. Copying settings or moving content between bots must not assume Telegram file IDs are portable.

## Feature ledger and acceptance rules

Phase 0 creates `docs/groupguard-rose/FEATURE_MATRIX.csv` and a readable `FEATURE_MATRIX.md`. Use stable IDs such as `ADM-001`, `MOD-001`, `FMT-001`, `CAP-001`, `LCK-001`, `BLK-001`, `FLD-001`, `RAID-001`, `FED-001`, and `DATA-001`. Create separate rows for independently testable behaviors; do not put an entire module in one row.

Each row contains: ID, module, source URL and section, checked date, command/alias or event, syntax, documented behavior/default, caller permission, required bot permission, chat types, standalone/child applicability, existing code evidence, gap status, owning phase, dependencies, acceptance scenario, test evidence, and deviation/dependency notes. Suggested statuses: `existing-unverified`, `existing-verified`, `partial`, `missing`, `blocked-external`, `implemented-unverified`, `verified`, `not-functional`.

Rules:

1. Cover every documentation page and functional section, including tables, links, modifiers, aliases, and commercial-clone annotations. Record navigation/explanation-only sections as such. Unclear or inaccessible behavior is an open question, never quietly dropped.
2. A feature becomes `verified` only when the report maps it to implementation paths and meaningful executed tests. During report review, this means agent-reported verification until independent final review.
3. Maintain a source-section coverage map so the denominator is visible. Report total and per-phase counts and all remaining gaps every time.
4. Preserve current stored configuration and established aliases. Keep existing defaults on upgrade; publish a deliberate new-group defaults policy rather than silently switching live groups to Rose defaults.
5. Document justified safety/Telegram differences. Do not label them exact parity. Unresolved differences remain open for final review.
6. Language coverage gets its own rows, including the published Rose locale roster. A language selector with English fallback does not count as translated locale parity.

## Architecture and quality requirements for every implementation phase

- Scope SQL operations to `ctx.bot_id` and the relevant chat/federation/user. Use `ctx.keys()` for normal Redis state. Existing shared factory job indexes are allowed only with explicit bot IDs and isolation tests. Federations default to a bot's own namespace; no unrequested cross-tenant trust.
- Separate Telegram actor, authenticated human, target chat, message/thread, and resolved target identity. Treat anonymous admins, channel senders, bots, and owners as distinct actor types.
- Check the caller's precise Telegram right and the bot's capability at execution time. A platform admin or factory owner is not automatically owner/admin of a Telegram group.
- Store bounded, one-use review/challenge state server-side, bind callbacks to their bot/chat/user/message and TTL, and recheck authorization before mutation. Never trust callback IDs or private connection history as authorization.
- Use one common action model for delete/warn/kick/mute/ban, timed variants, silent variants, reason, notification, and audit output. Track failure and partial success; don't announce success after a failed API call.
- Define a deterministic event pipeline. Locks precede blocklists as documented; inventory all other precedence/exemption rules. Process an event at most once per applicable rule/action, including webhook retries and message edits. A changed edit must still be checked; duplicate delivery must not count as new flood or raid activity.
- Keep external API/AI work bounded and optional. Reuse platform networking, file, metrics, audit, and scheduler conventions. Define fail-open/fail-closed behavior by feature and document it.
- Use durable deadlines and bounded jobs for expiration, recurring notes, cleaning, and federation fan-out. Handle retries, leases, backoff, dead jobs, child unload/pause/delete, and shutdown. Avoid unbounded Redis `KEYS` scans and one timer per member/child.
- Validate all user input, formatted text, URLs, file sizes, import contents, and time bounds. Preserve Telegram entity offsets and Unicode behavior. Provide understandable localized errors and protect message length/callback limits.
- Do not make destructive data changes, use live groups, expose tokens, change unrelated bots, or deploy/merge as part of cloud implementation. Provision only disposable test services.

Tests must assert externally observable behavior and denied side effects, not merely match private helper implementations. Do not weaken/remove tests to obtain a green run. Existing failing tests need a separate baseline record and explanation.

## Phases

The order is intentional. Phase 0 may propose smaller subdivisions with clear dependencies; the reviewer decides the next prompt from its report. Later phase descriptions are a roadmap, not authorization to implement them now.

### Phase 0 — Documentation inventory, repository audit, and implementation blueprint

**Change scope:** documentation and reproducible test fixtures only if needed to establish the baseline; no production behavior changes.

Read every source below, inventory all behavior, map it to the cloud repository, and create the detailed feature ledger. Establish actual installed library/API capabilities, test coverage, migrations, routing, permission boundaries, and factory behavior. Identify commands mentioned only indirectly (for example in disabling tables) and document unresolved meanings rather than inventing them.

Create `BASELINE.md`, `ARCHITECTURE.md`, and `DECISIONS.md`. The blueprint covers services/models, permissions, command metadata, formatting, event precedence, settings schema evolution, upgrade strategy, cache consistency, durable jobs, federation namespace/trust, privacy/retention, localization roster, and capability handling. Give concrete file/interface proposals and a per-phase schema plan, without building future features.

**Gate:** all source pages accounted for; every functional row assigned; baseline test results with skips/failures visible; precise Phase 1 work and acceptance cases; unresolved external dependencies and behavior questions listed. The report includes the inventory and blueprint content needed by an agent that cannot read the cloud files.

### Phase 1 — Permissions, command contracts, event delivery, and reliable shared primitives

Build the minimum reusable foundation needed for parity. Replace inferred anonymous-owner authority with verified actor handling. Centralize permission rules, owner-only checks, target resolution, boolean/duration parsing, command aliases and usage metadata, action results, and auditable reasons. Cache admin data with invalidation; do not hide anonymous admin identity in public lists by exposing it elsewhere.

Wire protection across normal and edited group messages and required event observers, preserving core router behavior. Add correct update subscriptions in both standalone and factory modes. Establish replay handling, concurrency-safe configuration/warning changes, and persistent review state. Introduce durable job infrastructure only where the existing scheduler cannot safely support later phases.

Capability checks must compare installed aiogram types/methods and the deployed local Bot API against [Telegram's official API](https://core.telegram.org/bots/api). New reaction-removal methods and bot visibility exist in the current official API; do not rely on old blanket assumptions that these features are impossible. Record actual supported deployment requirements and bounded compatibility behavior.

**Gate:** tests deny anonymous owner escalation, stale/forged callbacks, permission changes, wrong-chat/tenant actions, and non-admin mutations; edits/replays have defined behavior; configuration/warning races and failure outcomes are tested; all unrelated bot tests affected by core changes pass.

### Phase 2 — Complete manual moderation and administrator operations

Implement the full restriction command family: normal, temporary, delete-and-act, silent, undo, and any documented self-service aliases. Add warning limit/mode/time configuration, expiring warnings, delete/silent warning variants, exact warning removal buttons, and safe resets. Complete promotion/demotion with permissions bounded by both bot and caller; admin listing, cache refresh, error-display and anonymous-admin settings.

Complete approvals and owner-only bulk clearing, reports and `@admin` triggering/settings, info/ID behavior, log setup/categories, pins/permapins/unpin-all and linked-channel options, single/number/range/silent purge. Account for command variants found in source tables even when another module owns the underlying behavior.

**Gate:** permission matrices and time boundaries; existing alias compatibility; permanent versus temporary actions; successful and failed API outcomes; idempotent warning callbacks; purge range caps and API deletion limitations; anonymous identity privacy; moderation actions and audit events agree. Do not present requested deletion count as a confirmed deleted count when Telegram only acknowledges a batch.

### Phase 3 — Formatting, rules, media notes, filters, and greetings

Build one safe content representation/renderer for existing HTML/entity content and documented Rose input syntax. Implement rich formatting, URL and same-row buttons, note-menu buttons, the button-generator equivalent, documented fillings/control modifiers, and randomized content. Keep existing saved HTML functional during schema changes.

Complete rules delivery and custom/reset rules buttons; text/media welcomes and goodbyes with formatted/raw previews, resets, cleanup behavior, and correct placeholders. Extend notes with quoted names, media, private/admin/reply controls, updating and listing. Extend filters with phrases/multiple triggers, prefix/exact/user/admin/bot controls and reply targeting. Include documented custom-clone command suggestions and repeated notes; represent their schedule requirements now and implement the recurring delivery here using the common job mechanism.

**Gate:** dispatcher tests exercise text/captions/media, escaping, Unicode, malformed formatting, button navigation/authorization, private delivery when PM is unavailable, existing content migration, random alternatives, trigger collisions, and recurring delivery after restart for standalone and children. A preview must use the same renderer as real delivery.

### Phase 4 — Full CAPTCHA and newcomer lifecycle

Implement button, text, math, and text2 challenges, including private challenge flows; custom/reset button labels; solved-member persistence and documented reset behavior; kick settings/deadlines, failure actions, rules, and mute-time settings. Join requests must use persisted, expiring verification tied to the actual request and respect the relevant permissions.

Integrate existing CAS/newcomer/AI protection without removing options. Resolve documented dependencies between greetings and CAPTCHA explicitly, retaining safe behavior for existing configurations. A CAPTCHA pass must not cancel an unrelated manual/federation restriction or override a closed/night-mode group's permissions.

**Gate:** pass/wrong-answer/attempt-limit/timeout/rejoin/kick-reset scenarios for all modes; wrong user and token replay; simultaneous answer/expiry; multi-group/child isolation; restart, missing rights, blocked PM, expired join request, and API retry paths. Image challenges must be real generated challenges, not an unused selector or placeholder asset.

### Phase 5 — All documented locks and allowlists

Implement every current lock row, including message content, entities, media variants, sender/forward origin, inline/guest bots, linked-discussion outsiders, reactions and outsider reactions. The inventory must track each lock separately and record required capabilities. Preserve current plural/composite aliases without conflating distinct canonical locks.

Complete lock status/type listing, multi-lock changes, warnings, per-lock modes/reasons, and allowlist management. Implement each documented allowlist kind, including domains/paths, exact invite/chat references, commands, origins, and sticker/custom-emoji packs. Define normalization without accepting deceptive domain suffixes or incorrectly broad exemptions.

**Gate:** positive/negative fixtures for every lock, captions/hidden links/edits/anonymous sender cases, admin and approval exemptions, per-lock actions, lock-before-blocklist precedence, precise allowlist boundaries, owner-only clearing, and reaction/event handling in both runtimes. Unsupported deployment capabilities must be surfaced truthfully and remain open until fulfilled.

### Phase 6 — Advanced blocklists

Replace the string-only model with typed triggers/actions while migrating existing phrases intact. Add quoted phrases, multiple-trigger syntax, matching normalization and documented wildcard modifiers, default/custom reasons and actions, deletion policy, silent actions, and owner-only bulk clear. Support non-text triggers: packs, custom emoji, filenames/extensions, forward origin, inline bot, and prefixes.

Implement bounded matching rather than exposing arbitrary unsafe regular expressions. Preserve the source syntax's distinctions between wildcard types, escape sequences, word matching, and normalized text. Include exact/lookalike matching and custom-clone name/username triggers evaluated when a user is observed. Use the shared action model and ledger-based precedence.

**Gate:** table-driven matching cases from independently authored examples; accented/whitespace text, boundaries, escapes, filenames and missing metadata; trigger-specific/default action selection; concurrent changes and migration; edits/retries do not double-punish; malformed input and resource limits are tested.

### Phase 7 — Antiflood and AntiRaid

Implement consecutive-message and timed-window flood settings, status, all documented actions including silent/timed variants, and deletion policies. Preserve legacy rolling-window configuration through an explicit migration. Flood state must account for Telegram message order and duplicate/backlog delivery according to a documented policy.

Add manual AntiRaid, duration and action-time settings, automatic join-rate activation, deactivation/expiration, exemptions, and integration with join requests, CAPTCHA, approvals and federation checks. Use atomic bounded counters and durable activation deadlines across replicas.

**Gate:** boundary/off settings, alternate senders, concurrent bursts, mixed captions/media, replay and restart, automatic/manual activation races, expiry, API failures, and both bot modes. Tests measure legitimate users and exempt actors as well as spam scenarios.

### Phase 8 — Connections, command disabling, cleaning, topics, echo/broadcast, and bot-to-bot

Implement private connect/disconnect/connection/reconnect, history, group-username resolution, and per-command permission revalidation. Support the documented disabled-command catalog, deletion mode, and optional admin disabling without making recovery commands inaccessible. Complete command/bot/service cleanup by categories, with durable timed deletion and the necessary status/type commands.

Implement forum management and action-topic routing, echo/say, and the documented bot-owner group broadcast behavior. Reuse appropriate platform delivery primitives but define standalone operator/factory-owner authority explicitly; a group admin does not gain access to all groups served by a shared bot. Audit group `/admin` versus private platform `/admin` routing.

Implement bot-to-bot off/admin/all, human review of bot-admin mutations, skip-review settings, permission checks, and per-filter bot opt-in. Require a deployment capability/configuration path and suppress self/reply loops. The docs require human review by default; enabling a bot to send commands must not grant it extra rights.

**Gate:** loss of admin rights after connecting, shared-group members versus settings access, wrong connection/child, category cleanup failures, forum/deleted-topic handling, authorized broadcast destinations and retries, denied bot commands, review replay/expiry, and loop prevention. All mutation paths, including callbacks, obey disabling and review rules where applicable.

### Phase 9 — Federation ownership, management, membership, and information

Implement bot-scoped federation IDs, creation/rename/delete, ownership limits, fed-admin promotion/demotion/consent and self-demotion, group owner join/leave, info/admin/member-federation queries, reason requirements, notifications/log destinations, and quiet-federation settings. Implement documented owner-versus-fed-admin authority independently of group admin authority.

Store relationships with indexed tenant constraints and meaningful auditing. Define deletion/ownership and privacy policies from the inventory. A federation ID from another bot cannot create a trust relationship accidentally.

**Gate:** full owner/group-owner/fed-admin/member permission matrix, fed-admin consent if documented, duplicate joins, deletion confirmations, invalid or cross-bot IDs, logging rights, and factory child lifecycle. Preserve documented private-command target selection without silently applying a federation command to the wrong federation.

### Phase 10 — Federation bans, subscriptions, imports, and reliable enforcement

Implement fban/unfban, reason policy, user status/reason queries, own-ban lists, documented ban import/export formats, and federation subscriptions/unsubscriptions/listing. Validate graph rules and cycles; preserve ban provenance so removing one source cannot undo another federation or a local ban.

Implement documented active enforcement for observed users plus passive checks on joining/speaking and through subscribed federations. Use minimal observed membership tracking rather than attempting to enumerate inaccessible Telegram history. Fan-out must use durable bounded jobs with cancellation/version checks, retries, rate limits, failures and restart recovery. An old queued ban must not overtake a newer unban.

**Gate:** direct/subscribed/multiple-source bans, unban provenance, graph edge changes, groups joining after bans, quiet/log behavior, failure and stale-job ordering, permission revocation, paused/deleted children, malformed CSV/JSON and tenant isolation. Tests distinguish successful fan-out from merely queuing it.

### Phase 11 — Settings portability, privacy, locale coverage, and complete management UI

Implement schema-versioned module-selective JSON settings export/import, creator-only import/reset with confirmation, validation and bounded download/import sizes. Inventory actual Rose export formats; claim compatibility only for verified fields. Validate permissions, destination IDs, media portability, and unsupported/versioned fields. Imports must not silently overwrite identity/trust/ownership or restore stale challenges/jobs; include a defined restore policy.

Implement `/privacy` with understandable bot-specific data access/deletion workflows, scopes, retention and moderation-record policy. Deleting optional personal data must not create an undocumented moderation/federation escape route. Propagate cleanup to caches/queues while explaining backup retention accurately.

Complete settings panels, searchable/paginated help and command discovery, onboarding/capability diagnostics, English/Arabic parity, and the published locale coverage recorded in Phase 0. Fill translation gaps with independently authored translations; don't advertise untranslated locales as complete. Keep child branding and payment boundaries unchanged.

**Gate:** round trips for every portable module and existing configuration, unsupported external/media fields, invalid/cross-tenant import, owner/replay checks, reset cancellation, privacy deletion/access/retention, locale keys and variables, discoverability of every feature, and no stale cache/job re-creation after reset.

### Phase 12 — Release candidate, final source review, and staging handoff

The cloud agent first closes every ledger row, runs the complete quality gates, provides operator documentation and the complete cumulative source/artifact. The reviewing agent then inspects the actual changes and tests locally against the original/cloud baseline. Any report-only acceptance is replaced by independent verification; findings generate repair work.

Run fresh-schema and old-data upgrades on disposable PostgreSQL, Redis concurrency/restart tests, and the existing full runtime harness plus Group Guard and child scenarios. Add realistic burst/fan-out benchmarks with stated data volume and hardware and no invented performance claims. Check API requests, logging/privacy, backups, configuration limits, UI examples, and failure/recovery behavior.

Publish deployment prerequisites, migration/backup/rollback steps, feature-capability requirements, staged canary/manual QA instructions, and remaining limitations. Live Telegram checks require a separate authorized test group; mock-only evidence must be labeled. No production deployment is included in these prompts.

**Final gate:** complete source reviewed; all documented functional features implemented and independently evidenced, or an explicit dependency/difference list accepted by the user; no critical authorization/isolation/data-loss findings; full mandatory checks pass with skips disclosed; upgrade/rollback and staging steps are concrete. Never call it complete solely because every command name exists.

## Verification and reporting protocol

Use [REPORT_TEMPLATE.md](REPORT_TEMPLATE.md) for every phase. Reports must be self-contained: the reviewer cannot open the cloud checkout, report files, PR, or test artifacts until final source review. File paths and commit hashes identify evidence but do not replace reporting its relevant content.

Minimum recurring commands, adjusted to the exact changed paths and environment:

```text
python -m core bots
ruff check .
mypy
pytest -q tests/bots/groupguard tests/bots/factory tests/test_locales.py
pytest -q
```

Run database-changing work against disposable PostgreSQL, including `tests/integration`, and runtime/Redis-sensitive work against disposable PostgreSQL/Redis with `tests/e2e`. Existing integration tests drop the configured PostgreSQL public schema and the runtime harness empties its chosen Redis database; never point either at shared or production services. Report the exact command, sanitized environment prerequisites, exit code, pass/fail/skip counts, and why any test was skipped. Use Linux cloud-compatible commands rather than copying Windows paths.

Phase 0 runs baseline checks where possible but does not repair unrelated failures. Later phases run the appropriate focused tests and repository checks; expand testing when shared code, migrations, concurrency or runtime behavior warrants it. Real-service tests are mandatory before final acceptance, even if the cloud environment cannot run them in an earlier phase.

Return: starting and ending commit/worktree identity, changed paths/diffstat, complete new public interfaces and schema contracts, feature IDs/evidence, executed checks, migration/default/cache/job changes, risks/deviations, all open issues and precise next-phase dependencies. No credentials or irrelevant raw logs. A skipped test is not a pass; an unexecuted assertion is not evidence.

## Documentation source coverage seed

This is the starting coverage map. Phase 0 follows all functional links/sections and expands it if the site changes. It must also identify semantic conflicts or incomplete docs instead of filling them with assumptions. Reference content with URLs, retrieval date and concise paraphrases; do not commit a copied documentation site.

| Area / provisional phase | Official source pages |
| --- | --- |
| Navigation/onboarding, 0/11 | [Introduction](https://missrose.org/docs/), [Getting started](https://missrose.org/docs/getting-started/), [Before you start](https://missrose.org/docs/basics/) |
| Parsing/info/languages, 1/2/11 | [Command Usage](https://missrose.org/docs/basics/command-usage/), [Getting Info](https://missrose.org/docs/basics/info/), [Languages](https://missrose.org/docs/basics/languages/) |
| Rules/connections, 3/8 | [Rules](https://missrose.org/docs/basics/rules/), [Connecting To Chats](https://missrose.org/docs/basics/connections/), [Connections](https://missrose.org/docs/connections/) |
| Admins/moderation, 1/2 | [Admins](https://missrose.org/docs/moderation/admins/), [Pins](https://missrose.org/docs/moderation/pins/), [Approvals](https://missrose.org/docs/moderation/approvals/), [Purges](https://missrose.org/docs/moderation/purges/), [Logging](https://missrose.org/docs/moderation/log-channels/), [Restrictions](https://missrose.org/docs/moderation/restrictions/), [Warnings](https://missrose.org/docs/moderation/warnings/), [Reports](https://missrose.org/docs/moderation/reports/) |
| Command disabling, 8 | [Command Disabling](https://missrose.org/docs/moderation/disabling/) |
| Greetings, 3/4 | [Welcomes](https://missrose.org/docs/greetings/), [Goodbyes](https://missrose.org/docs/greetings/goodbyes/), [Advanced greetings](https://missrose.org/docs/greetings/advanced/) |
| Spam/locks/CAPTCHA, 4/5 | [Anti spam overview](https://missrose.org/docs/anti-spam/), [Locks](https://missrose.org/docs/anti-spam/locks/), [CAPTCHA](https://missrose.org/docs/anti-spam/captchas/) |
| Blocklists, 6 | [Managing](https://missrose.org/docs/anti-spam/blocklists/), [Modes](https://missrose.org/docs/anti-spam/blocklists/modes/), [Advanced](https://missrose.org/docs/anti-spam/blocklists/advanced/) |
| Flood/raid, 7 | [Antiflood](https://missrose.org/docs/anti-spam/antiflood/), [AntiRaid](https://missrose.org/docs/anti-spam/antiraid/) |
| Federations, 9/10 | [Overview](https://missrose.org/docs/federations/), [Info](https://missrose.org/docs/federations/fedinfo/), [Creating](https://missrose.org/docs/federations/creating/), [Managing](https://missrose.org/docs/federations/managing/), [Joining](https://missrose.org/docs/federations/joining/), [Bans](https://missrose.org/docs/federations/fedbans/), [User commands](https://missrose.org/docs/federations/user-commands/) |
| Content, 3 | [Filters](https://missrose.org/docs/filters/), [Notes](https://missrose.org/docs/notes/), [Formatting](https://missrose.org/docs/formatting/), [Button Generator](https://missrose.org/docs/formatting/button-generator/) |
| Utilities/data/topics, 8/11 | [Echo](https://missrose.org/docs/echo/), [Exports](https://missrose.org/docs/exports/), [Privacy](https://missrose.org/docs/privacy/), [Topics](https://missrose.org/docs/topics/) |
| Cleaning, 3/8 | [Commands](https://missrose.org/docs/cleaning/clean-command/), [Bot messages](https://missrose.org/docs/cleaning/clean-message/), [Service messages](https://missrose.org/docs/cleaning/clean-service/) |
| Advanced, 1/2/8 | [Overview](https://missrose.org/docs/advanced/), [Silent Actions](https://missrose.org/docs/advanced/silent-actions/), [Bot To Bot](https://missrose.org/docs/advanced/bot-to-bot/) |

The docs currently annotate command suggestions and repeated notes as custom-clone features. Include equivalents in this plan; access to Rose's commercial hosting is not required for our independent implementation. Resolve inconsistencies between examples and command names in Phase 0 and record the chosen compatibility behavior.


## Phase 0B reconciliation — controlling bounded scope

The supplied original replaces the reconstructed current plan; reconstruction remains unchanged in history/PHASE_00. Existing audit evidence is retained. Later broad title/transfer/global/cross-bot and retention suggestions are not required sourced scope: Q09/Q06 track this. Phase 0B imports only the supplied baseline commits and audits; no implementation phase is authorized. Recommend 1A actor/precise fresh rights/strict temporary parsing/truthful results, 1B ordering/edits/sender/event subscriptions/child parity, 1C atomic transitions/deadlines/retryable jobs. ARCHITECTURE.md defines bounded proposed seams. Original roadmap phases2–12 remain owning phases, not authorization to begin. No new-group source defaults overwrite established live-group defaults.


## Phase 1A cumulative addendum

Phase 1A existing-flow authorization/outcome implementation report is reports/PHASE_01A.md. Do not begin1B without reviewer prompt. 1B remains edited delivery/core precedence/gs shadow/subscriptions;1C remains config/warnings ownership/CAPTCHA generations/jobs/replay. Federation S32 roles/reasons/notifications/logs9; banlist/import/subscriptions10. Future /kickme implementation2, disable8; no command implemented now.
