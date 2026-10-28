# Cloud coding agent prompt — Phase 1A

Implement **Phase 1A only: attributable actors, fresh permissions, safe target/duration contracts, and truthful action outcomes on existing Group Guard flows**. Stop and return the report below. Do not begin Phase 1B or later work.

## Context and authority

We are extending the existing Group Guard bot toward all publicly documented Rose behavior, in individually reviewed phases. The reviewing agent receives only your reports until the final cumulative source handoff. A report's provisional acceptance is not independent code certification.

Phase 0B is provisionally accepted. Its reported baseline ends at `96357ef45c6492e03c626581ce2ee156d2da3816`, source tree `7895f72031fd4fac13b4ff280ba04b16c8d5842c`, equivalent to reference `d55fc44fe1a63ba5788125c1325d2a855944d5e0`. Continue the cumulative cloud checkout; **do not replay the bundle or reset the repository**. Preserve existing audit/history/evidence and disclose intervening changes. Read applicable `AGENTS.md`, platform README/SDK/design/operations instructions, the Phase 0B architecture/decisions/matrix, `PHASE_00B_REVIEW.md`, `PHASE_01A_SOURCE_ADDENDUM.md`, and `REPORT_TEMPLATE.md`.

This prompt bounds and supersedes the broad Phase 1 roadmap for this turn. Names/signatures proposed in Phase 0B may be refined for correctness; report the actual public contracts. Retain stable feature IDs. Apply the review's `/kickme` source correction and S32 Phase 9/10 ownership correction, recomputing ledger counts. Neither correction authorizes those future features now.

The known supplied-baseline failure is `tests/bots/doctools/test_review.py::test_malformed_html_and_invalid_encoding_are_controlled` (Python 3.12.14 parser behavior; full suite 257 passed, one failed, three service-dependent skips). Keep it visible. Do not edit DocTools, weaken/skip/xfail that test, or alter dependencies to hide it. No additional failures are acceptable.

## 1. Shared actor and authorization contracts

Introduce the minimum reusable contracts, preferably within `bots/groupguard/contracts.py` and `authz.py`, adopting them in existing handlers/services.

- Distinguish human, anonymous group, channel, bot and unknown actors. Keep bot namespace, source chat, target chat, human ID, sender-chat ID, message ID and thread distinct. `sender_chat` takes precedence over a pseudo `from_user`; it never implies creator. Only a group sending as itself is eligible for the anonymous group review flow. Other channel/unknown senders cannot gain human authority. Bot-admin command support remains Phase 8; automated actions use an explicit internal origin instead.
- Normalize rights including change-info, delete-messages, restrict-members, pin-messages, invite-users, promote-members, manage-topics and attributable creator. Existing short aliases/cache records must remain readable without granting missing rights. Promotion/topic fields are preparation only; do not implement their new commands.
- Centralize authorization and structured denial reasons. For every existing manual domain mutation, use uncached `getChatMember` information immediately before execution for the human and relevant bot capability. API uncertainty denies; platform administration, factory ownership, cached admin lists and connection history confer no Telegram rights. Display caches may remain but must not authorize mutations or protected-target decisions.
- Express all required caller/bot rights for a compound operation as sets, or an equivalent explicit union. Do not perform an initial delete/settings/warning write and discover a missing sanction right afterward. Existing settings commands/panel changes, including lock/blocklist configuration and night settings, need change-info. Manual sanctions, undo and current warning authority need restrict-members; deletion needs delete-messages; pins need pin-messages. A sanction plus deletion needs both. Pure settings SQL writes do not need fabricated bot sanction rights. Human-admin join-request actions need invite-users; automated acceptance still requires the bot capability. Owner-only checks require the current human creator.
- Map every existing mutating command, callback and panel branch in the report, including rule/welcome/note/filter/config writes, warning removal, log destination changes, moderation and night controls. Preserve established command aliases. Do not redesign later command families, disablement or full command metadata now.
- Internal automated/scheduled operations must still check actual bot capabilities and scoped current policy. They do not obtain a fictional human creator or bypass failed capability lookup. Keep their entry points distinct from human-command authorization.
- Bind private settings panels to server-created bot/target-chat/authorized-human/message state. Verify current rights on each write. A PM message's chat is not the target group: distinguish legitimate bound PM settings from forged target IDs. Validate public callback scope and ownership as applicable; `/close` may close only an appropriate bot-created panel. Preserve current routing; fixing the `gs_` start-handler shadow belongs to 1B.
- Tighten the manual user-target resolver without breaking `/id`'s separate chat-ID behavior. Validate positive human user IDs; reject anonymous/channel pseudo-users, ambiguous or unknown usernames and protected current creator/admin targets. Resolve reply/entity/known-username/numeric forms without accidentally consuming the first reason token. Check protected targets freshly and fail safely on uncertainty. Never guess arbitrary username IDs. Document observed/cache evidence and stale username handling. Keep intentional existing automatic bot-join enforcement separate from manual target policy.

## 2. Anonymous operation approval

Implement the default human verification flow for **existing** authorized mutations. Do not add `/anonadmin on` or assume anonymous admin rights.

Parse and validate the requested action once into an immutable, allowlisted operation. Store a random opaque nonce under `ctx.keys()`, binding bot, target/source group, original and review message IDs, thread, normalized target, arguments/reason/duration, required rights, creation/expiry and operation identity. Use a bounded 120-second TTL. The displayed review must let the human see the intended operation; escape untrusted text. Do not serialize callable code or trust callback-supplied replacement arguments.

On button activation, authenticate the actual human from the callback, validate scope/expiry and fresh caller/bot rights, atomically claim the request once, and apply that exact operation. Recheck authorization close to execution after the claim if intervening work could stale the check. Invalid/non-admin attempts must not consume the review. Concurrent valid approvals must cause at most one action. Once execution starts, failures do not make the old button executable again; require a new command. Redis/state failures deny execution.

The authorized human approves under **their own** authority; the original anonymous human is unknowable. Any currently authorized human may approve this anonymous request. Where a flow has a known initiating human, bind it to that user. For owner-only work the reviewer must actually be creator. Do not expose reviewer identity publicly or DM an anonymous pseudo-user. Record an accurate approving actor in the existing private audit path, without asserting that the original sender was identified. Redis review state supports short-lived cross-worker verification, not a claim of durable exactly-once Telegram execution.

## 3. Strict duration and argument parsing

Provide an explicit absent/valid/invalid duration result and a shared action-argument parser. Missing/invalid `/tban` or `/tmute` duration must return usage/error and cause zero sanction/deletion/domain writes. Malformed time-shaped input on ordinary ban/mute must not become a permanent action by being mistaken for a reason. Reason-only permanent commands remain supported. Clearly define and test how a word such as `spam` differs from invalid numeric/unit input, where duration sits after each target form, and how the remaining reason is retained.

For temporary ban/mute, adopt **60 seconds–365 days inclusive** as the explicit local safety policy. This narrows existing sanction bounds deliberately; document it and reject unsafe input rather than clamping or falling back to permanent. Preserve seconds support and ordinary duration units. Keep general timer/flood-window parsing separate: a 10-second flood window remains valid. Do not rewrite stored configuration or change unrelated defaults.

Calculate a new command's deadline immediately before the API call, after approval/authorization, using integer timestamps correctly so `1m` works. Validate any existing absolute deadline with a positive margin inside Telegram's permanent-conversion boundaries. Expired/unsafe deadlines must not reach the timed sanction API. Document the practical network-delay limitation. Validate reasons against existing persistence limits and escape them for output without silent data corruption or a formatting-system rewrite.

## 4. Explicit action results throughout existing flows

Replace Boolean/ignored outcomes with typed step and aggregate results for existing punish/unmute/unban/delete/log paths. Audit **every caller**, including moderation, warning thresholds, protection, welcome/CAS/AI/CAPTCHA and jobs. Do not rely on dataclass truthiness; expose explicit completion/error information. Unknown action names must fail rather than default to ban.

- Separate primary sanction, deletions, restoration, notification and audit steps. Report API errors/RetryAfter in structured sanitized outcomes without swallowing cancellation or credentials. Failed ancillary steps cannot rewrite a successful sanction as unapplied; they also cannot be reported as wholly successful.
- A kick requires ban and successful unban. If only ban succeeds, report partial failure and the possible remaining ban; do not announce that the user was successfully kicked. Undo failure must not announce successful restoration.
- Remove the fail-open `OPEN` fallback when chat-default permission lookup fails. Unmute or night restoration must not fabricate unrestricted permissions. Night closing must have a valid restorable permission snapshot before applying closure. Use actual available permission fields; avoid granting privileges beyond current defaults. Durable night/CAPTCHA restriction ownership and recovery remain later work.
- In the existing sequential warning-threshold flow, clear warnings only after the intended sanction completes. Failed authorization/API calls retain history. If the sanction completes but logging fails, reset may proceed based on sanction completion, with the log failure reported separately. Do not claim concurrent warning correctness; transaction/generation coordination belongs to 1C.
- Update automated/manual notices and existing audit messages to match the result, including CAS/AI announcements. Preserve silent behavior and branding. Silence does not imply successful action or suppression of required failure evidence.
- Bulk deletion must expose requested/acknowledged batches and partial API failures. Keep confirmed deleted count unknown when the API provides no per-ID evidence; do not print requested IDs as a factual deleted count. Preserve existing operational caps without adding future purge variants.

This adoption authorizes only the changes required for accurate current-flow outcomes and permission safety. Existing CAPTCHA generation/expiry races, job leases and update replay defects remain explicitly open; do not silently build their lifecycle redesign here.

## 5. Scope, compatibility and tests

Preserve standalone/factory child behavior, bot/chat namespaces, SQL keys, existing configuration/defaults, English/Arabic UI, legacy aliases, optional CAS/AI behavior, credits/VIP/branding and unrelated modules. Localize new errors/review/result messages and verify placeholder values. Use existing infrastructure, not a second bot framework.

No SQL migration/new persistent table is authorized for 1A. Short-lived review/panel bindings and their atomic claims are in scope; general config/warning races and durable jobs belong to 1C. No new Rose command families, federation schema, reaction implementation, update subscriptions, core-router precedence change, settings deep-link routing fix or broad dependency upgrades. If a required repair genuinely needs one of these, complete unaffected work and explain the exact dependency; do not mark the gate complete.

Add meaningful dispatcher/service tests covering at least:

1. Anonymous/pseudo-user/channel/bot/factory-owner escalation denial; owner-only rejection for an ordinary admin; a real creator's attributable authorization.
2. Unrelated caller right, missing bot right, demotion/revocation after cache or panel creation, lookup failure, and compound rights missing: zero domain mutations and no prohibited Telegram calls.
3. Bound PM/group callbacks: wrong human where required, wrong chat/bot/thread/message, forged target IDs, unbound panels and current-right checks.
4. Anonymous review approval by a suitably privileged human; insufficient-right attempts; expiry, altered arguments, wrong scope, duplicate/concurrent clicks and Redis failure. Only one concurrent approval reaches the sanction. An executed-but-failed review cannot replay.
5. Reply/entity/known username/ID target forms; stale/unknown username, negative user ID, protected targets, reason-only permanent input, and faithful reason preservation.
6. Missing/malformed/negative/zero/overflow/unsafe durations cause no mutations; accepted `1m`, representative units, safe upper bound; existing absolute deadline rejection; 10-second non-sanction timer still valid.
7. Failed sanction preserves warnings; completed sanction plus failed log has distinct evidence; kick's second-step failure is partial; failed unmute/default lookup cannot grant `OPEN`; night cannot close without a snapshot; unknown action never bans.
8. False success prevention in direct and automated flows; bulk deletion acknowledged counts remain unknown; silent side effects retain truthful private evidence.
9. The same tests in standalone and at least two factory child namespaces sharing a group: no review/panel/target-cache/state access across bots. Exercise the actual Group Guard child path; the old child-feedback e2e alone is insufficient.

Update recording Telegram fixtures to provide explicit current membership/capabilities and failure transitions. Do not weaken authorization to accommodate old fixtures. Use real Redis for a targeted atomic-claim concurrency check if fakeredis cannot faithfully exercise the chosen operation. Existing mocked Telegram tests must distinguish read-only permission lookups from domain-changing API calls.

Run dependency health, `python -m core bots`, Ruff, mypy, focused Group Guard/factory/locales tests, the full default suite, disposable PostgreSQL integration and the existing disposable PostgreSQL/Redis runtime e2e. Use the project's established `.venv` commands; disclose exact commands, versions, exits/counts/skips. The full suite may retain **only the named baseline DocTools failure**. Do not use production credentials/data, deploy, merge or perform live Telegram moderation. Report blocked checks honestly; clean up disposable resources.

## 6. Inline report required for review

Persist `docs/groupguard-rose/reports/PHASE_01A.md` and return its relevant content inline. A statement that files exist, a commit hash or test total alone is insufficient. Use `REPORT_TEMPLATE.md`, including:

- Starting/ending commit and dirty state, every changed file/purpose, diffstat, authorized scope and verdict.
- Stable IDs repaired/tested; whole-ledger and current-scope status counts; partial parent rows and all deferred/open defects. Add small foundation rows if needed rather than marking entire later features verified.
- **Actual implemented** actor/right/auth/target/duration/result symbols, signatures, errors and postconditions; full existing mutation-to-rights mapping; API call-site adoption list; configuration/default/schema changes (expected none).
- Redis key/payload/TTL/atomic-claim/panel contracts and reviewer attribution/privacy semantics. State the limit of one-use approval versus Telegram delivery guarantees.
- A compact acceptance table for the nine groups above, with concrete test names, actors/inputs, observed denied/applied/partial outcome, mutation/API evidence and result. Include standalone/child isolation evidence.
- Exact checks and concise failure output; distinguish mocks from disposable services and service-dependent skips. Identify the named baseline failure separately from any new failure.
- English/Arabic message examples, preserved aliases/defaults, deliberate sanction-range difference, residual permission/network/race assumptions, and contracts needed for 1B/1C.
- Report-claimed readiness only if the full authorized 1A gate is met. Otherwise identify unfinished items without beginning another phase.

End with: `Stopped after Phase 1A. Awaiting the reviewer's next prompt.`
