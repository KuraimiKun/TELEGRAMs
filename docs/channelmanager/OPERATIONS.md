# Channel Manager: setup, publishing, and recovery

Phases 1–6 provide channel management, publishing, scheduling, automation, member workflows, publishing teams, private reveals, consented campaigns, invitation gates, channel Stars plans and branded full managers. See [advanced publishing](ADVANCED_PUBLISHING.md), [source automation](SOURCE_AUTOMATION.md), [member workflows](MEMBER_WORKFLOWS.md), and [growth/billing](GROWTH_AND_BILLING.md). Member policies start disabled; only observed requests enter the queue. Plans/prices start unpublished and require platform-administrator review.

## Configuration and startup

Create a Telegram bot through BotFather and set `CHANNELMANAGER_TOKEN` in your private environment. Add `channelmanager` to `ENABLED_BOTS`. Optionally set `CHANNELMANAGER_ADMIN_IDS` for trusted platform operators; that setting does not grant rights over Telegram channels.

Apply migrations, then run the existing gateway and scheduler plus the new worker:

```text
python -m core migrate
python -m core gateway
python -m core scheduler
python -m core run channelmanager worker
```

Run those processes separately in production. `python -m core dev` runs configured bot processes together for development. For Compose, configure the token and enabled list first, then include the optional worker:

```text
docker compose --profile channelmanager up -d --build
```

The worker healthcheck uses `python -m bots.channelmanager.health` to detect stale progress independently of its process heartbeat. Configure the staged rollout and immutable Bot API image as described in [the release runbook](RELEASE_RUNBOOK.md). No token is committed or automatically configured by this implementation.

## Operator flow

1. Start the bot privately and add it as a channel administrator with posting rights.
2. Send `/connect @channelname` or `/connect -1001234567890`. The caller must currently be the channel owner or a native administrator with posting rights.
3. Use `/channels` to open channel details, inspect missing rights, refresh the bot's rights, or disconnect management after confirmation.

Callbacks are bound to their initiating user and the channel/post configuration generation. Reopen `/channels` or `/posts` when a menu is stale. Saved native roles only identify candidate channels for listing; live Telegram checks authorize access. Phase 6 virtual publishing grants have current grantor/permission/generation checks; see [teams](GROWTH_AND_BILLING.md#publishing-teams-and-adoption).

Channel removal/demotion events are committed to `chm_inbox` before webhook acknowledgement. The worker updates channel state, audit events, and outgoing status notices together. Configuration changes cancel stale, undispatched notices/publications/edits/pins. Routine refresh preserves cleanup. Explicit disconnect can interrupt ordinary cleanup, while financial refunds and invitation revocations are retained. Inspect residual native bans/effects before disconnecting. A request already dispatched may still finish. Disconnecting keeps the bot installed and the channel intact.

## Publishing walkthrough

1. Use `/newpost`, select a connected channel, and send text or one photo, video, GIF, or document with an optional caption. The content becomes a saved SQL draft immediately; `/cancel` leaves the input flow without discarding it.
2. Open **Preview**, then add link buttons or change **Post options**. Button syntax is `Website - https://example.com`; use `&&` between buttons and new lines between rows. Send `-` to clear them.
3. Options include subscriber notifications, text link previews, content protection, a saved signature, caption position where applicable, a same-channel reply ID, pinning, and a deletion timer. Pinning and editing published messages require the bot's editing right. The operator needs the native editing right for pinning.
4. Use **Destinations** to supply up to ten connected channel IDs. Every destination is checked live. Choose **Publish now** or **Schedule / reschedule**, review the channel/time summary, and press **Confirm publication**.
5. Open `/posts` or a channel's **Posts** menu to filter drafts, queued/scheduled posts, and published posts. Each destination shows its content version, publication result, and independent edit/pin/deletion result. **Refresh** retrieves the latest report; **Open message** and **Share link** appear when a remote ID is known. Protected posts omit the share shortcut.
6. Edit the content/buttons, reschedule remaining work, publish remaining safe destinations now, or copy the post to a new draft for another publication. Successful or uncertain destinations are never automatically resent. **Retry failed edits / pins / deletions** retries definite follow-up failures without publishing the content again.
7. **Delete published messages** queues remote deletion of known sent messages and cancels remaining sends. **Stop managing this post** cancels undispatched work and retains Telegram messages. **Cancel remaining sends** leaves successful messages and their existing cleanup obligations intact.

Use `/signature -1001234567890` and then send formatted signature text (up to 250 UTF-16 units), or `-` to clear. New drafts snapshot the primary channel's signature; that saved signature is used in every destination. Existing drafts keep their snapshot. Changing a channel signature or timezone requires the operator's native editing right.

Use `/timezone -1001234567890 Asia/Jakarta` to configure an IANA timezone. Scheduling accepts `YYYY-MM-DD HH:MM` in the primary channel's timezone or an ISO timestamp with a UTC offset. Ambiguous or nonexistent daylight-saving times require an explicit offset. Confirmation shows the same instant in each destination's timezone. Existing schedules retain their saved UTC instant after a timezone change.

Deletion durations accept `30m`, `2h`, or `3d`, up to one year. The timer begins at the actual successful send timestamp. At 48 hours or later, or if delayed cleanup crosses that boundary, the worker sends a private manual-deletion reminder instead of claiming a remote deletion. This follows the ordinary Bot API deletion window. [Telegram deletion rules](https://core.telegram.org/bots/api#deletemessage).

## Publishing boundaries and limits

- The composer supports text or one photo/video/animation/document received by this bot. Native entities, HTML/Markdown subsets, structured buttons, recurrence, and calendars are available. Phase 4 source automation additionally handles photo/video albums and forwarding; native polls and album composition remain outside the composer.
- HTML accepts `b`, `strong`, `i`, `em`, `u`, `ins`, `s`, `strike`, `del`, `code`, `pre`, `blockquote`, `tg-spoiler`, and `a href`. Unsupported tags/attributes, malformed nesting, crossed entity ranges, and invalid UTF-16 boundaries are rejected before queueing.
- The renderer conservatively limits text to 4,096 and captions to 1,024 UTF-16 units including the signature. Buttons allow ten rows of at most four structured buttons plus up to six default vote labels. Media file references are scoped to the uploading bot.
- Replies require the primary channel to be the sole destination. Published media cannot be converted to text through this editor; create a new draft. Replace a media caption by sending the replacement media with its caption. Content protection, notification, pin request, reply target, and deletion timer are fixed after publication.
- Source automation adopts single manual messages it enriches into the managed post report, preserving stricter native edit/delete rights for those messages. Arbitrary historical message-ID adoption is not exposed. Open/share links to private channels still require Telegram membership. Live client/server compatibility remains part of Phase 0; automated tests mock Telegram responses.
- Default settings allow 100 drafts per operator and 20 future pending schedules per channel. Draft creation locks the bot record; future-schedule quota checks lock destination channels in order. Effective quotas come from payment-linked channel grants, with `chm_entitlements` projected for compatibility and configured free limits after expiry. See the [channel ledger](GROWTH_AND_BILLING.md#channel-stars-ledger).
- A schedule more than `schedule_lateness_grace_seconds` late (default 300 seconds) is held for review. Use the post menu to explicitly publish remaining destinations now or reschedule. The worker executes saved SQL obligations directly; the central recovery sweep reconciles leases and reports.

Post edits append immutable versions and invalidate old undispatched publish/edit jobs. Dispatch serializes with post mutation and checks current actor/bot rights. A running dispatched action temporarily blocks edits, cancellation, and detach until it resolves or its lease expires. Automatic deletion retains the authorization captured at publication even if the original actor later loses rights; the bot's current deletion rights are still checked.

## Recovery and diagnostics

Use `/admin` → Channel Manager for active channel, inbox, operation, failure, and uncertain-delivery counts plus recent sanitized error identifiers. Automation adds collecting/held source and failed/uncertain action counts. Use `/automation` → source → **Source reports** for independent route/edit/cleanup outcomes and eligible individual retries. Channel operators do not receive platform admin access.

Member diagnostics additionally show pending/held/uncertain requests and cleanup obligations. Open `/members` for the observed queue, policy review, required-chat/captcha progress, individual definite-failure retries, bulk release snapshots, and departure/log/cleanup results. Policy edits hold pending requests for explicit adoption. Bulk release never bypasses gates. Welcome/goodbye delivery requires a signed private start, and explicit disconnect can interrupt cleanup; inspect unresolved bans before abandoning management.

| State | Meaning | Operator action |
|---|---|---|
| Inbox pending | Event is committed and awaiting processing/retry | Check worker health and database availability |
| Inbox failed | Five processing attempts failed; domain writes were rolled back | Inspect sanitized code, correct the cause, and review the receipt before any manual repair |
| Operation pending | Awaiting execution, local budget, or an explicit Telegram retry delay | Keep worker/Redis running; inspect `run_at` and `error_code` |
| Operation running | Held by an owner-token lease | Allow the worker or expired-lease recovery to finish |
| Operation uncertain | A dispatched request was interrupted or delivery could not be determined | Reconcile externally before deliberately creating replacement work; automatic replay is disabled |
| Operation failed | Definite rejection, invalid payload, or exhausted API retry budget | Fix permissions/reachability/configuration before creating replacement work |
| Operation cancelled | Channel generation changed or the namespace ceased to be eligible | Open current channel details; do not reuse the old menu/job |

Expired jobs that were never dispatched return to pending, subject to the attempt budget. Expired dispatched jobs become uncertain. Stale workers cannot complete jobs after losing their lease. Redis loss defers outgoing work; durable obligations remain in PostgreSQL. Maintenance continues durable receipts and cleanup-only claims. Staged rollback stops new effects while retaining financial reconciliation and cleanup; see the [release runbook](RELEASE_RUNBOOK.md#operational-rollback).

Publication, follow-up actions, status notices, and core operator broadcasts share a namespaced sender/chat budget in Channel Manager contexts. The queue does not claim exactly-once Telegram delivery. If publication succeeded but pinning failed, the report remains published with a failed pin; use the follow-up retry button after fixing rights. Network uncertainty requires manual review. Cloning deliberately creates a new publication and can duplicate a message that was already delivered. Platform core broadcasts remain operator-only and are not channel-owner campaigns.

Completed inbox payloads are cleared. Failed receipt payloads remain available for operator investigation and should be handled as private channel/member data. Automation source parts, snapshots, and configurations also retain private content/file references independently of the inbox. The current phase does not provide a general replay UI or automated retention policy; restrict database access and apply the deployment's retention policy to these records and backups.

## Verification

Run lint/type checks and focused tests before enabling the bot. On Windows, use UTF-8 Python mode for multilingual fixtures:

```text
ruff check .
mypy
python -X utf8 -m pytest -q tests/bots/channelmanager tests/test_locales.py
```

The test harness excludes the real workspace `.env` from settings reads. It still supports explicit temporary fixture env files. Windows sandboxed runs may require a writable pytest `--basetemp` or execution outside the sandbox for pytest's protected temporary directories.

Real-service tests use `TEST_CHM_DATABASE_URL`, `TEST_CHM_PUBLISH_DATABASE_URL`, `TEST_CHM_ADVANCED_DATABASE_URL`, `TEST_CHM_AUTOMATION_DATABASE_URL`, `TEST_CHM_MEMBERS_DATABASE_URL`, `TEST_CHM_GROWTH_DATABASE_URL`, and `TEST_CHM_REDIS_URL`. Database tests require loopback PostgreSQL databases named with the `channelmanager_phase1_test` through `channelmanager_phase6_test` prefixes respectively. They upgrade/downgrade Channel Manager revisions and truncate test data, including bot namespaces in Phase 6. Use dedicated disposable databases. Redis checks remove only their own test keys.

See [Phase 7 verification](PHASE_07_VERIFICATION.md), the [compatibility matrix](COMPATIBILITY_MATRIX.md), and [the roadmap](phases/README.md) for results and remaining live work. Apply migrations through `0024_chm_growth` before starting this code. Enable the factory scheduler for branded child work. Native Telegram/client verification is deferred because the token has not been created; no production deployment was performed.
