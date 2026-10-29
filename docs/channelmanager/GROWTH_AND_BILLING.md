# Collaboration, growth, Stars plans and branded senders

Phase 6 adds migration `0024_chm_growth`, sixteen scoped tables and the `/team`, `/locked`, `/campaigns`, `/plans`, `/senders`, `/menus`, `/subscriber`, `/subscribe`, `/unsubscribe`, and `/forget` commands. English and Arabic menus use actor-bound callbacks. Apply migrations before running the gateway, worker or factory scheduler. No plans or prices are published by default.

## Publishing teams and adoption

Use `/team` to grant or revoke channel-local publishing access. The grantor must currently be a native owner or an administrator with both posting and promotion rights. Permissions are `create`, `edit_own`, `edit_all`, `delete_own`, `delete_all`, `schedules`, and `settings`. Enter the numeric user ID and selected permission names; review before applying. Revocation uses `USER_ID revoke`.

Virtual admins can manage permitted bot posts, drafts, targets, batches, recurrence and publishing defaults. Admission, enforcement, source automation, delegation, campaigns, sender bindings and billing retain native administrative checks. Editing manually sourced automatic posts also retains its native checks.

Authorization reads the current grant and the grantor's current native authority. Global edit/settings and delete rights cannot exceed the grantor's corresponding native rights, including after a later role change. Queued publication captures the grant generation; a changed or revoked grant fails again at the SQL dispatch fence. Failed authorization holds publication for review. An owner with native edit rights can adopt a post by ID, after which pending work stays held until explicitly published or scheduled again. Already sent and ambiguous sends are not repeated by adoption.

## Locked content

Use `/locked` to enter a public teaser, a separate private secret and ordered additional requirements (`CHAT_ID URL`, or `-`). Both the bot and operator must administer additional required chats. A lock always requires source-channel membership. Open the resulting post to preview and explicitly publish its teaser.

The public version contains an unlock link and the teaser only. The secret lives in a separate scoped record. The supported reveal is a signed private `/start` link: membership is checked in source/additional order on interaction and again before private dispatch. The result uses content protection. Secret changes invalidate pending old-version reveals; disabling a lock invalidates its links. No global message edit reveals the secret. Protected delivery does not prevent a recipient from photographing or otherwise recording content.

The private fallback is implemented and tested with recorded API calls. Newer ephemeral channel responses and real client rendering remain Phase 0/7 compatibility work. Media must have been uploaded to this sender. Source-bound callbacks, albums, pins, replies and deletion timers are excluded from private content.

## Campaign consent, snapshots and privacy

Admission captcha/continuation interactions do not subscribe users to campaigns. `/subscribe` explicitly enables campaigns for one channel and sender; `/unsubscribe` disables them. Membership requirements remain independent of consent. Fresh private starts and usable private contact establish reachability; observing a channel member alone does not.

Use `/campaigns` to enter supported text/media and create a 15-minute SQL audience snapshot. The snapshot includes only this sender's associated leads with private-interaction evidence, reachability and explicit opt-in, excluding blocked and opted-out users. The current plan caps recipient count. Preview shows the fixed count and content; **Confirm campaign send** is a separate action. Later arrivals do not enter that snapshot.

Each recipient has an outcome. Dispatch rechecks consent, block state, source, actor, generation and quota. Cancellation stops undispatched work. Recovery preserves dispatched uncertainty. **Review definite unsent recipients** prepares another confirmation using only the same snapshot's selected, failed or cancelled entries; succeeded, skipped and uncertain entries are excluded. It cannot expand into another channel or child bot. A reduced plan may hold an oversized campaign for review.

`/forget` reviews removal of the channel/sender lead and campaign recipient records, erases feedback content and its user association, and scrubs terminal private jobs. It retains an opaque opt-out marker, admission state, financial records and audit/cleanup obligations. A native RPC already dispatched can still finish; completion also scrubs opted-out private jobs. Users can explicitly opt in again with retained association or fresh source membership proof.

## Must Share invitations

In `/members`, configure **Invitation gate**, required distinct credits (0 disables), timeout and optional invitation-only timeout bypass. Invitation counts never satisfy captcha, required memberships, filters or timing/manual conditions.

The bot creates its own expiring join-request link for each request/invitation epoch. Credit comes from a distinct first qualifying observed request after captcha/required-chat checks, or a first observed join with native attribution. Qualifying requests count so that recursively required invitations do not require an already admitted referee. A click alone does not count. Native links from another creator, self-referrals, repeated invitees, wrong sources, superseded requests and stale epochs do not advance the request. There is no guarantee against coordinated accounts.

Introduction text supports `{invite_count}`, `{invite_required}`, and `{invite_url}`; entity offsets are adjusted using UTF-16-aware splices. The private check action refreshes progress. A share button contains the request's own link. Links expire at the original request deadline and are queued for revocation after completion or epoch replacement. An ambiguous link-creation RPC is not retried blindly; its requested expiry still bounds the unknown link. Change policy and explicitly adopt held requests when a fresh invitation epoch is needed.

## Channel Stars ledger

A platform administrator uses `/plans` → **Manage plan catalog** to enter an unpublished immutable version: name, tier, rank, days, Stars price and all quotas. Review before publishing. Retirement prevents new checkout; accepted checkouts retain their immutable terms. Business prices are a deployment decision. This implementation does not invent or publish prices.

A native channel operator chooses a published plan and renewal, immediate upgrade or next-period downgrade. The bot creates a server-issued quote bound to bot, channel, payer, version, amount, currency, expiry and current upgrade basis. Review its impact, then explicitly request the native Stars invoice. Telegram's payment confirmation remains a separate user action. Invoices use `XTR`, one price item and an empty provider token. [Telegram Stars payments](https://core.telegram.org/bots/payments-stars).

Checkout rechecks live operator/bot authority, source state, plan availability, payer, amount, currency, expiry and upgrade basis within its time budget. Successful-payment messages commit to the durable inbox before acknowledgement. A leased processor records the core zero-day payment and channel grant in one transaction, deduplicated by native charge ID. It never extends personal VIP. Late success after accepted checkout can fulfill the immutable quote; unauthorized, mismatched, unknown and stale-upgrade charges go to review instead of granting entitlement.

Renewals and downgrades append after all already paid base periods. Immediate upgrades are overlays for the current remaining period, require a higher rank and nondecreasing quotas, and charge the ceiling of the remaining seconds multiplied by the difference between the two rational Stars-per-second rates. A change to the paid basis requires a fresh quote. This is prepaid service; there is no automatic recurring charge.

Expiry and refunds recompute effective quotas. Excess future schedules are held; rule, route, delegate, lock, campaign and invitation checks use effective limits at execution. Existing content and cleanup records remain. Increased quotas do not silently replay held work. Each sweep rotates through billing scopes; native dispatch also reads payment status directly.

**Review full refund** displays the actual charge and quota impact before confirmation. The payer or platform administrator may request a full native refund. A successful refund removes that payment's unused time and rebases subsequent paid base periods, preserving their purchased duration. Refunding a base period holds dependent upgrade grants and marks their invoices for review/refund. Repeated refund receipts do not shift periods again. Consumed service is not transferred into other grants. Telegram exposes full-charge `refundStarPayment`; arbitrary partial refunds are not claimed. [Bot API refund method](https://core.telegram.org/bots/api#refundstarpayment).

The shared core refund service can also mark payments refunded; the billing sweep reconciles those changes with the channel ledger. Unknown refund results remain `refund_uncertain` until a trusted native refund receipt or operator reconciliation. Do not clear dispatch markers or automatically repeat a possibly completed refund.

## Branded full managers and subscriber interactions

Create a **Channel Manager** template in the existing factory, add it as an administrator, and run `/connect` in both the control and child bots. The owner chooses it under `/senders` and reviews the binding. Ownership, current native posting/edit authority, active template, encrypted-token epoch and plan eligibility are checked. A binding selects a full manager with its own namespace; posts, leads, menus and file IDs are not copied from the control bot.

Upload media to the selected sender. Cross-bot file IDs are rejected; automatic transfer/reuse is not implemented. This is the tested conservative media behavior. Billing stays in the control bot; a child's plan menu links back there. The control bot pauses new channel work while bound. Binding/rebinding increments both source generations and cancels obsolete undispatched work, so immediate unbinding cannot resume an old queued publication.

Rotation, pause, deletion, ownership/template changes and stale bindings stop child dispatch. Factory sweeps process only active children, at most five per run, rotating fairly. Pause/delete records residual timed-ban/invitation counts in the control channel audit. Native timed bans and generated links also have their own expiry. Parent publication stays paused after child loss/deletion until the owner explicitly unbinds and reviews held/cancelled work. Deleting one child cascades its template namespace while retaining other children and the control payment ledger.

If a Channel Manager token already has a webhook on another host, create/resume/rotation require an explicit migration card before replacing that webhook. The pending create token is encrypted and confirmation expires after five minutes. External settings are not imported. External long-polling ownership cannot be detected reliably from an empty webhook; stop the previous poller before migration. External Modular interoperability remains out of scope.

Use `/menus` to configure private subscriber text/media and native link buttons with feedback enabled. `/subscriber` routes associated users to their own sender/channel menu. Feedback is private, source-scoped and relayed once to the configured operator; its inbox offers one private reply per item. Menu access, feedback and billing routing use their respective source/ownership checks.

## Recovery

- Run the normal worker/recovery scheduler and the factory scheduler. Financial receipts continue processing during maintenance; new commercial checkout is rejected then.
- Inspect `chm_inbox` failed `billing_paid`/`billing_refund` receipts by bot/update ID and sanitized error code. Fix the cause, then requeue the same receipt with a fresh availability time and cleared expired lease. Do not manufacture a new charge. Atomic payments and grant links make a legitimate receipt replay safe.
- Inspect `chm_channel_invoices`, `chm_channel_grants`, `chm_billing_incidents`, the scoped `chm_growth_actions` and operations together. Unknown/mismatched charges appear under the payer's invoice review; administrators can investigate the same scoped ledger.
- An unapplied charge's refund is an explicit reviewed recovery action. It reserves its status before calling Telegram. An ambiguous standalone incident refund remains for operator/native reconciliation, without automatic replay.
- Use campaign outcomes and reviewed unsent preparation. Do not reset uncertain recipients to selected. If consent or quota changed, resolve it and prepare a fresh review.
- For sender loss, review `sender.stopped` audit details and residual native effects before deleting state. Rebind/rotate explicitly; do not copy file IDs or audience rows across bots.
- Back up before migration. `0024` adds direct cascading bot foreign keys to older Channel Manager tables; preflight historical orphan bot IDs. Downgrade drops Phase 6 business data and is a destructive recovery choice, not a normal operational rollback.

Native membership/permission changes and already dispatched Telegram RPCs cannot be made atomic with SQL. Automated tests cover committed-state fencing and recovery, not exactly-once remote effects. Production PostgreSQL/Redis versions, native payments/refunds, bot ownership migration and Telegram client behavior require the Phase 0/7 canary before release.
