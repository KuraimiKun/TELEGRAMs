# Admission and member workflows

Phase 5 adds `/members` and **Member workflows** in the start/channel menus. Apply `0023_chm_members`, then run the existing gateway, worker, and recovery scheduler. New policies start disabled. This release uses the standalone sender; invitation-growth gates, paid plans, and branded senders remain Phase 6.

## Configure a channel

1. Connect the source and open `/members`. The operator needs native posting and invite-user rights.
2. Configure introduction, welcome, and goodbye content with the shared text/media validator, link/native-copy buttons, and private previews. One photo, video, animation, or document is supported; albums and source-bound callbacks are excluded. Introduction reserves 512 UTF-16 units for admission instructions.
3. Choose **Manual**, **Immediate after gates**, or **Timed** approval. Set expiry (one minute to seven days), optional delay (up to one day and shorter than expiry), captcha, and required chats.
4. Configure filters, departure actions, event logging, and service cleanup as needed. They remain inactive until the policy is enabled.
5. Review and enable. New receipts use the current policy. Editing an enabled policy holds pending requests; **Adopt current policy** explicitly resumes a held request under the new configuration. Configure multiple changes while disabled when intermediate settings should not apply to new arrivals.

Policy saves are atomic and callbacks are bound to their operator and configuration generation. Required-chat, source, linked-group, moderation, and logging permissions are validated before activation and checked again for applicable side effects. Disabling remains possible when a destination loses rights; outstanding cleanup keeps its original authorization.

## One admission state machine

Join requests enter the durable inbox before acknowledgement. Each recorded request has a channel/user generation, immutable policy snapshot, contact deadline, expiry, captcha state, manual-release flag, required-chat progress, and independent delivery records.

The admission sequence is:

1. Active namespace and policy checks.
2. Total block, observed-rate, and profile filters.
3. Initial contact and optional math captcha.
4. Required-chat checks, in configured order, stopping at the first missing membership.
5. Timed/manual approval condition.
6. Fresh native authorization, profile, required-membership, configuration, and request-generation checks.
7. Approval, followed by a reachable welcome.

A timer or bulk release never satisfies a captcha or required membership. Manual release authorizes only the manual condition; timed requests still wait for their configured instant. There is no gate-bypass override in this phase. Wrong answers consume bounded attempts (default three, maximum ten); callback receipt IDs make exact duplicate callbacks idempotent. Neither duplicate updates nor policy adoption restores used attempts. Expiry defaults to one hour.

The queue records requests observed after this code is running. It does not enumerate Telegram's historical or unseen queue. Requests seen while disabled are held for explicit adoption. Adoption preserves the existing expiry ceiling and attempts, rechecks filters, resets required-chat progress, and never turns an old uncapped attempt budget into a new one. A rejoin creates a newer generation; a same-second rejoin needs an intervening observed departure. Otherwise same-time duplicate requests are suppressed.

**Bulk release** snapshots up to 5,000 recorded request IDs into SQL with a 15-minute confirmation deadline. Confirmation rechecks the actor, policy, current head, expiry, and state for every entry. It reports selected/released/skipped totals and is idempotent. Later arrivals are excluded; held, expired, and stale entries are skipped. Released means the manual condition was released, not that Telegram already approved the member.

Explicit decline is available to an authorized operator even while automatic processing is disabled. Actual membership discovered through a native membership update is recorded as external approval; the bot cannot prevent another administrator or a public invite path from admitting somebody outside this workflow.

## Private reachability

Initial contact uses the request's `user_chat_id` only within its temporary window and before processing the request. Telegram documents a five-minute limit with additional conditions. A longer captcha/approval expiry does not extend that permission. [Join-request contact rules](https://core.telegram.org/bots/api#chatjoinrequest).

The initial message includes an expiring signed **Continue privately** link bound to bot, request, and applicant. `/start` through that link records channel-specific private interaction and continued reachability. A captcha callback records interaction evidence but does not, by itself, establish continued private-message permission. Source membership and successful bot-initiated contact never set private-start evidence.

Welcome after approval and goodbye require that recorded private start, a reachable sender, and no opt-out. Contact failures, blocked users, expired windows, and absent private starts receive bounded failed/skipped results. Uncertain messages are not automatically resent. Starting the bot after approval can deliver a previously skipped welcome once while the continuation link remains valid. Operators can copy the applicant's continuation link from the request report; another user cannot use it.

Token rotation invalidates existing signatures; current request reports generate links using the current token. The newer welcome-message permission and query-only join-request API are not used as substitutes for established contact. Query-only requests, when exposed by the installed SDK, are held with `query_id_unsupported` for compatibility review.

## Filters and required chats

| Setting | Contract |
|---|---|
| Total block | Reject before initial contact/captcha |
| Ten-second threshold | Count durable observed requests and direct joins separately in a ten-second processing window; reject excess arrivals |
| Name/username expressions | Phase 4 bounded Unicode keyword contract; any blocked expression rejects |
| Alphabet rule | Allow/block named Unicode scripts in displayed-name letters; digits, marks, punctuation, and symbols are not classified as letters |
| Language rule | Allow/block declared profile language codes; a primary code can match a regional variant |
| Missing language | Allowed unless its separate rejection toggle is enabled |
| Outcome | Decline a pending request or ban; rejected direct joins use a one-minute temporary removal for decline mode |

Profile language and name scripts are configurable literal profile rules, not identity or trust assessments. Invalid allowlists, durations, media, and callback types fail validation before activation.

Required chats are ordered negative chat IDs with Telegram join URLs. The bot must administer them to verify membership reliably. Owners, administrators, members, and restricted users whose `is_member` is true pass. Source self-dependency and duplicate required IDs are rejected. A missing membership or API failure never counts as success. All memberships are read again immediately before approval; displayed progress is not permanent authorization.

Direct joins without an observed pending request cannot be subjected to pre-approval captcha/delay by this API. They are logged and evaluated by enabled post-join filters. Post-approval welcomes are tied to recorded requests rather than inferred from an arbitrary public join.

## Departures and cleanup

Departure bans default off. Only a present-to-absent transition performed by the departing user and ending in `left` is voluntary. Administrative removals and the bot's own enforcement are recorded separately and do not trigger goodbye/another departure ban.

An enabled departure ban can be permanent or timed (one minute to 365 days). Linked-group action requires the source's actual linked supergroup and current restriction rights for the operator and bot. Source and linked-group results are independent. Own source-enforcement updates do not cancel the matching linked-group action; a newer join/request generation does cancel stale enforcement.

Timed bans save the native deadline at whole-second precision. Confirmation creates a durable unban operation. It survives ordinary policy edits/disabling and worker restart. Cleanup verifies the saved owned ban and current ban deadline, uses `only_if_banned=True`, and never removes a rejoined member. A changed administrator ban is preserved and reported for review. The API documents why unconditional unban is unsafe for current members. [Safe unban behavior](https://core.telegram.org/bots/api#unbanchatmember).

Late ban dispatch with less than 30 seconds left is cancelled instead of accidentally creating a permanent ban. Dispatched uncertainty is retained for review; native timed expiry still applies. Explicit channel disconnect or bot removal can prevent cleanup and must be reviewed through action reports before abandoning management.

Service cleanup is an explicit allowlist: title/photo changes, removed chat photo, pinned-message notifications, and supported video-chat service messages. It operates only on messages actually observed in the source channel, checks deletion rights, and reports API rejection or an expired deletion window. Ordinary posts and unselected/unsupported service types are not removed. Configuration rejects unsupported selector names.

## Logs, diagnostics, and recovery

External logs require a connected secondary channel and live posting rights. Choose English/Arabic and an event subset: request, approved, declined, expired, joined, left, removed, banned, unbanned, filter rejection, contact failure, or cleanup failure. Logs contain source/user IDs and outcome codes; the internal SQL audit survives external logging failure. Logged bot outputs are excluded from source automation, including in-flight output acknowledgements.

`/members` provides the observed queue and recent action results. Request reports show status, attempts, requirement progress, expiry, sanitized errors, and eligible individual retries. Admin diagnostics and fixed-label metrics include pending/held/uncertain requests and cleanup obligations.

| State | Action |
|---|---|
| Pending | Check worker, contact opportunity, captcha, requirements, delay, and manual release |
| Held | Review configuration/compatibility and explicitly adopt if eligible |
| Approved / declined / expired | Terminal result; duplicates cannot reset the request |
| Superseded | A newer request replaced this generation; old undispatched jobs are invalidated |
| Uncertain | Reconcile externally; automatic approval/decline/message replay is disabled |
| Failed action | Correct rights/reachability/configuration and use a safe retry under the current request/policy |
| Skipped cleanup | Inspect whether the user already rejoined/unbanned or an administrator changed the ban |

Sender/chat budgets are shared with publishing, forwarding, status messages, and broadcasts. Two of three wall-clock second buckets prioritize short-lived contact/admission work; the remaining bucket claims oldest work first. This reserves ordinary queue progress without promising exact dispatch deadlines. Redis loss defers sends. Maintenance preserves observations while pausing planning/dispatch, and lease recovery fences stale owners.

Generation checks protect known committed state; Telegram's user-addressed approve/decline and unban methods do not provide an atomic comparison against our SQL generation/deadline. A native change racing the final check/request remains an external API limitation. The bot does not claim exactly-once effects or control over other administrators.

Requests retain minimal profile/contact/gate data; leads retain channel/sender interaction evidence; callbacks retain receipt IDs; logs/audit/actions retain IDs and outcomes. Raw completed inbox payloads are cleared, but these records remain. Restrict access and apply deployment retention/backup rules. There is no general lead-erasure/retention UI or campaign audience builder in Phase 5.

See [Phase 5 verification](PHASE_05_VERIFICATION.md) for evidence. Live Telegram compatibility, production canary, and the newer welcome/query-only APIs remain Phase 0/7 release gates.
