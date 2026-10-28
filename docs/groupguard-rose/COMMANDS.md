# Group Guard implemented command contracts

Current stage2. This table describes actual implemented command families; later stages add their operator contracts. No live Telegram/deployed Bot API capability certification.

| Commands | Context | Caller / bot rights | Behavior/default |
|---|---|---|---|
| ban,tban,dban,sban,unban; mute,tmute,dmute,smute,unmute; kick,dkick,skick | Group | restrict_members / restrict_members; d/s also delete_messages on both | Reply, ID or verified known username; reasons256; t requires60s–365d; d requires reply; s deletes command/reply and suppresses confirmation, keeps audit/log |
| kickme | Group | current actual human member / restrict_members | Self only, no arbitrary arguments; creator/admin protected |
| warn,dwarn,swarn,rmwarn,unwarn,resetwarn,resetwarns | Group | restrict_members / restrict_members; d/s deletion union | Exact IDs, reasons, completed threshold cutoff reset; failed/uncertain history retained |
| warns; warnings | Group | Public | Live reasons/IDs/expiry versus settings; large reason lists become files |
| setwarnlimit,setwarnmode,setwarntime,warntime | Group | change_info / bot admin | Limit1–20, >= threshold; modes ban/mute/kick/tban/tmute; ages captured on issuance, off cancels pending ages |
| promote,demote | Group | promote_members / promote_members | Current permission intersection, never promotion grant; only editable demotion, no creator/bot target |
| adminlist; admincache | Group | Public; change_info refresh / bot admin | Fresh public identities, anonymous omitted; refresh invalidates old cache |
| adminerror,anonadmin | Group | change_info / bot admin | Error responses on; anonymous assumption off. On assumes only same-group ordinary rights bounded by bot and excludes owner |
| approve,unapprove; unapproveall | Group | change_info; creator clear / bot admin | Scoped reasons/identity; does not exempt manual actions |
| approval,approved | Group | Public | Status/reason; paginated files above30 entries |
| report,admin,admins,@admin; reports | Group | Public reports; change_info toggle / bot admin | Reply report; public nonanonymous admin pings; reports on |
| id,info | Group/private | Public | Available self/reply/known username/ID profile; group context ID/membership; unknown resolves to explicit failure |
| pin,permapin,unpin,unpinall | Group | pin_messages / pin_messages | Pin quiet by default, loud optional; permapin sends then pins actual new ID |
| antichannelpin,cleanlinked | Group | change_info settings / pin or delete for enforcement | Defaults off; auto-forward unpin/deletion distinct |
| del,purge,spurge,purgefrom,purgeto | Group | delete_messages / delete_messages | Reply range, cap300IDs; N selects from reply; endpoints human/chat/topic bound10min; bulk count unknown |
| setlog,unsetlog,log,nolog | Group (initial setlog also channel) | change_info in source+destination / bot admin plus channel post | Original channel receipt+forward, or numeric extension; category selection; all six default on |
| logchannel,logcategories | Group | Public | Destination and actual category status |

Configuration changes and callbacks always revalidate current authority. Both standalone and actual child contexts use the same contracts. Existing legacy defaults/aliases are preserved; no permissions inferred from factory/operator ownership.

Phase3 adds actual group content commands. Connected PM mutations remain Phase8; existing opaque content links are reads and never grant administrator authority.

| Commands | Context | Caller / bot rights | Behavior/default |
|---|---|---|---|
| rules; setrules,resetrules,privaterules,setrulesbutton,resetrulesbutton | Group; member-revalidated PM content link | Public/member reads; change_info writes / bot admin | Shared Rose/native entity rendering; private opening button; plaintext custom label; reset does not alter other settings |
| welcome,goodbye; setwelcome,setgoodbye; resetwelcome,resetgoodbye | Group | Public preview; change_info writes / bot admin | Show/on/yes/true/off/no/false/noformat; replied eight attachment types with optional command caption; reset preserves enable and verification state |
| save,get,notes,clear,privatenotes,#name | Group; member-revalidated PM link/menu | Public reads unless admin flag; change_info writes / bot admin | New single-word names only; private/noprivate controls; replied subject fillings; rich native entities and legacy HTML remain supported |
| clearall confirm; stopall confirm | Group | Actual creator / bot admin | Explicit confirmation and creator authority; cancel obsolete note cadence/jobs atomically |
| filter,stop,filters | Group | Public list/trigger; change_info writes / bot admin | Words, quoted phrases, parenthesized batch; prefix:/exact: matching; replytag/user/admin/allow_bot; slash command suggestions in actual chat scope |
| button | Group | Public | Clone helper: one quoted label and URL or #note per line; optional same; copyable markup and working scoped menu preview |
| cleanwelcome | Group | change_info / bot admin; delete_messages at cleanup | Off default; previously sent welcome IDs are scheduled for deletion five minutes after replacement, separate from service messages |

Repeat/repeated60s–30d schedules are bot/chat/item/generation scoped. Author must remain change_info administrator and bot administrator; private/admin notes cannot be broadcast. Global privatenotes cancels a public cadence unless noprivate explicitly overrides it. One catch-up maximum after downtime. Unknown network dispatch outcome pauses the cadence until explicitly resaving. No exact-once Telegram guarantee. Clone slash filters use real Telegram1..32 lowercase command bounds; source's fewer-than32 wording is recorded separately.

Phase4 CAPTCHA contracts execute in group and issued personal PM/request cards. Connected PM configuration remains Phase8.

| Commands | Caller / bot rights | Behavior/default |
|---|---|---|
| captcha on/off; captchamode button/text/math/text2 | change_info / bot admin | Button default; enabling requires welcomes. Off/changed settings do not waive an issued policy. Legacy mode off remains readable. Nonbutton challenges open PM with real images |
| setcaptchatext,resetcaptchatext | change_info / bot admin | Plaintext128 UTF16 label, no fillings or markup expansion; reset localized default |
| captchakick,captchakicktime | change_info / bot admin | Kick default on; canonical duration5m..1day; legacy captcha_minutes preserved until explicit override |
| captcharules | change_info / bot admin | Off default; on requires saved rules. Successful question leads to actual frozen rules card and separate owner-bound acceptance before release/approval |
| captchamutetime | change_info / bot admin | Off default; explicit60s..1day releases only this issued own mute; no human-verification memory granted by a timer |

Text mode chooses the pictured word; math chooses actual pictured equation result; text2 selects four image characters in order with SQL sequence fences. Images are real PNGs from the bundled OFL font. Three wrong answers apply a one-hour local failure ban, keeping unrelated stronger owners. Unsolved kick uses frozen policy; kick off uses24h card lifetime, then retains the own mute. Manual, CAS and federation ownership stay separate. Group approvals skip CAPTCHA/newbie automation; CAS remains a security check. Successful verification is remembered per group; voluntary leave preserves it, administrative kick resets it. Join requests use actual user_chat_id and original request.date+300s contact bound, never a fresh five-minute extension. Owned bans block automatic approval.

Phase5 provides all canonical lock tokens in the supplied roster plus historical plural aliases. Status and settings use current bot/group namespace.

| Commands | Caller / bot rights | Actual behavior |
|---|---|---|
| locks; locks list; locktypes | Public group read | Current configured types/policies versus complete available roster; all shortcut advertised |
| lock/unlock TYPE... [### reason] [{mode [duration]}] | change_info / bot admin | Atomic per-type delta and validated policy; default delete; kick/ban/tban/mute/tmute; explicit optional action works without reason separator |
| lockwarns on/off | change_info / bot admin | Default off; default delete policy becomes actual delete+durable warning when on; explicit per-lock primary action takes precedence |
| allowlist; rmallowlist | change_info writes/public inventory / bot admin | Domains/subdomains/boundary-safe paths, exact invites/public chat names/numeric observed targets, channel/bot/inline/forward/command identities and sticker/custom emoji packs; one entry per line |
| rmallowlistall confirm | Actual creator / bot admin | Explicit clear with fresh creator authority |

Default nothing locked. Legacy links/invites/forwards/media/stickers/gifs/polls/bots remain explicit aliases; old stored voice retains video-note behavior, new canonical voice/videonote are distinct. Existing alias callbacks toggle canonical current sets. Locks precede blocklist. Actual admins/approved users exempt; own-group anonymous administration is a collective SDK identity without a fictional human, while mutation review/anonadmin authority remains separate.

Attributable reaction/outsider events call real DeleteMessageReaction with actual user or actor_chat ID and current delete capability; outsider policies require linked discussion plus actual nonmember proof. Anonymous aggregate counts provide no actor required by removal API, so only a precise diagnostic/failed receipt is possible. No invented actor or remote-removal success. Sender-channel permanent ban uses its separate SDK method and API semantics (owner's channels in this chat); timed/mute/warn human policies cannot manufacture a user for a channel. Unsupported actor policy records a failed primary with any actual deletion retained.

Phase6: /addblocklist TRIGGER reason [{action [duration]}], /blocklist (no arguments lists; arguments add), /rmblocklist and /rmblocklistall confirm (actual creator). Quoted phrases and (a,b) multiple triggers work; legacy addblock/rmblock/unblocklist aliases preserve comma lists. change_info authority for writes. /blocklistmode nothing|warn|kick|ban|tban TIME|mute|tmute TIME; /blocklistdelete on/off independent; /setblocklistreason TEXT and /resetblocklistreason. Public listing is bounded text/file. Bulk batches fail atomically at150 entries by default, never silently truncate.

Typed prefixes stickerpack: (including <> replied actual sticker/custom emoji set), file: (filename/full pattern or .extension), forward:/inline: actual ID/username, prefix:/exact:/lookalike:, name:/username: observed profiles. One optional leading @ on username. Full-word Unicode alphanumeric/underscore boundary, NFKD casefold/accent/space normalization. ? one non-space, * zero/more non-space, ** arbitrary, backslash escapes. New pattern raw256 codepoints, source32768, at most32 wildcard tokens. Lookalike is curated Cyrillic/Greek-to-Latin local equivalence, not full Unicode visual identity. Source lookalike exact-example and username inline-prose defects use the declared prefixes.

Default nothing deletes only; deletion off retains selected sanction/warning. Entry reason wins over configured fallback then localized default. Silent per-entry swarn/skick/sban/stban/smute/stmute requires creator-enabled consent and log; never a silent default mode. Consent management completes Phase8. Removed/disabled log selects loud behavior, a failed selected audit receives visible ancillary-failure fallback. Approved/current admin users exempt. Locks win before blocklist. Join profile checks use actual ChatMemberUpdated with no fictional Message/deletion target; warning/mute can coexist with independent CAPTCHA, kick/ban suppress verification for that consumed join. Checks see joins/speaking only, never unseen profile changes.

Phase7: /flood reports independent consecutive/timer policies and exact boundaries. /setflood N|off (at N), /setfloodtimer N TIME|off (over N; seconds), /setfloodmode kick|ban|mute|tban TIME|tmute TIME with gated silent s-prefix, /clearflood on|off. Config writes change_info, actual automatic effect current bot delete/restrict union. Legacy default timer6/8s/mute60m preserved; new consecutive off. Selected normal ban/mute permanent, temporary require valid60s..365d. Counts≤50/window1s..24h local caps. Clear on removes only observed user IDs, default off removes current offending message. Admin/approved/bot/channel interleaving resets consecutive; edits/replay never recount.

/antiraid status with bound enable button; on uses configured6h, TIME override does not change default, off cancels activation without unbanning applied users. Activation caller restrict_members, bot restrict_members when enabling. /raidtime TIME and /raidactiontime TIME configure separate future active/ban policy (defaults6h/1h, local60s..30d); /autoantiraid N|off|no >N unapproved non-admin human joins under1min, cap10000 local. Activation freezes ban period; stale callback/expiry cannot reset/terminate newer generation. Existing owned bans/CAS precede raid; then observed profile/newbie/CAP. Active join requests decline with bot invite_users, issued CAP cannot approve during raid. Unknown outcomes retained, not blindly retried.

/night START END [UTC_OFFSET] and /night off restore owned snapshots immediately when appropriate. Current schedule-window/version plus permission fingerprint prevents stale restoration over later admin changes. Failed close/restore/lookup retry in bounded fair sweeps, never fabricate open defaults. Factory pause/deletion release only owned transient state and cancel activation; actual punitive bans remain. Missing API rights/identity is a recorded failure, not an invented restored group.

## Phase 8 connections and utilities

Private /connect ID|@publicgroup validates the actual group and current membership. Group /connect returns a personal PM link. /connect with no private arguments shows the last five groups; /reconnect replaces the active selection; /connection and /disconnect report or clear it. Connected members can read; changes require each feature's current group rights. /id uses the logical connected group. Commands needing actual group message IDs (purge/delete/pin, delete variants and reports) require group context. Private replies always retain their actual private source IDs.

/disabled, /disableable, /disable NAMES, /enable NAMES, /disabledel on|off, /disableadmin on|off use canonical purposes. Current admins bypass ordinary disablement until disableadmin is on. Recovery commands stay available. The published twenty-name catalog is preserved; /runs and /saved return an explicit compatibility diagnostic. /antiflood is a local read-only /flood status alias and accepts no arguments. Federation catalog execution arrives in9/10.

/cleancommand and /keepcommand all|admin|user|other operate after functional processing; /cleancommandtypes lists categories. /cleanmsg and /keepmsg all|action|filter|note select owned output removal after 300 seconds; /cleanmsgtypes lists them. Action includes announcements, warnings, echo and permapin outputs. Active verification/help/settings cards are separate; old-welcome cleanup retains its own policy. /cleanservice BOOL|all|TYPES, /nocleanservice TYPES and /cleanservicetypes support join/leave/other/photo/pin/title/videochat. Payment processing happens first; absent updates and failed deletes are never claimed as successful cleanup.

/setactiontopic uses the current forum topic; /actiontopic reports it. Welcomes use the selected topic or general by default. /newtopic NAME, /renametopic NAME, /closetopic, /reopentopic, /deletetopic use current manage_topics rights; deletion requires a personal 120-second confirmation. Connected PM uses an explicit topic ID for rename/close/reopen/delete. General deletion is rejected. Missing/deleted topic API failures remain failures, without sending to another topic.

/echo and /say render saved formatting or replied media under change_info rights. /broadcast CONTENT is restricted to configured standalone operators or the current active child's owner; /broadcast without content reports that owner's latest campaign outcomes. Destinations are this bot's active groups only. Local policy: one active campaign and one creation per owner per five minutes, batches of100, quota20 destination attempts per second. RetryAfter retries at most five attempts; unknown delivery is retained without replay. Known attachment success plus companion failure does not repeat the attachment.

/silentactions on|off is creator-only; enabling needs the configured automated log category and does not convert existing action policies. Explicit silent selections become loud when consent/log is removed or delivery fails. Manual silent variants stay independent. /bot2bot off|admin|all defaults off; bots retain exact current group rights and never creator/owner identity. Mutations require human review unless /bot2botskipreview on; review still rechecks the original bot and human. Self/reply loops, duplicate intents and more than ten commands per bot/group/minute are suppressed. Explicit allow_bot slash filters are independent opt-in. BotFather bot-to-bot visibility must be configured outside this local task; no live configuration is asserted.

## Phase 9 our federation service

/newfed NAME, /renamefed NAME and /delfed operate privately. Each human owns at most one federation per bot; names truncate to64 Unicode codepoints and creation returns a UUID. Delete uses a personal five-minute revision-bound confirmation, permanently removes federation roles/membership, cancels undispatched relevant jobs and never sends an automatic Telegram unban.

/fedinfo [ID], /fedadmins [ID [AFTER_USER]], /chatfed and /myfeds [AFTER_ID] expose this bot's local federation namespace. Group context uses its attached federation; actual PM context uses the human's owned federation or an explicit UUID. A private group connection never retargets federation commands. Public explicit private UUID reads are independent of a group's disabled command policy; group fedinfo/fedadmins honor it. Admin pages contain the owner and at most100 administrators; myfeds pages contain at most20 records with continuation syntax. Group creation/admin roles do not confer federation roles.

The owner uses /fedpromote TARGET and /feddemote TARGET; administrators use /feddemoteme ID for self-removal. The owner cannot be demoted. Positive human IDs and human replies work; group usernames require live proof, private known usernames require current verification in one of the federation's first50 actual groups, otherwise use an ID. /fedreason on|off controls required ban reasons (defaultoff local choice; enforcement10); /fednotif on|off controls owner notifications (defaulton sourced). Logs remain independent of notification-off.

/setfedlog DESTINATION in the federation context, or /setfedlog FED_ID as an actual channel post, sends the owner a personal confirmation. Current owner/destination change_info rights and bot posting rights (post_messages in channels) are rechecked. /unsetfedlog removes the destination. Missing notification/log transport is reported separately from a saved role/configuration change; absent Message receipts cannot bind confirmation authority.

Only the group's current Telegram creator can /joinfed ID or /leavefed; federation ownership is not required. /quietfed on|off requires current change_info rights and only selects passive explanation policy; enforcement10 remains independent. Rejoining changes attachment generation and cancels obsolete undispatched destination work. Legacy groups without a federation retain their previous behavior.

## Phase 10 federation policies and files

/fban TARGET [REASON] and /unfban TARGET [REASON] use the group's attached federation or the actual private caller's owned federation, even with a connection. Federation owner/admin role is independent of group administration; current roles are rechecked. /fedreason on requires nonempty reasons. Records are policy intents: observed destinations are queued, and failure/uncertainty stays visible in durable outcomes. Current Telegram administrators remain protected from automatic enforcement.

/subfed ID, /unsubfed ID are owner-only directed subscriptions; A subscribes to B means A's groups enforce B's current bans. /fedsubs lists direct targets and honors group disable policy. Self/cycles rejected; local caps32 direct/128 reachable/depth16/10,000 namespace edges. Current direct/subscribed bans take priority over generic approval/raid/newcomer/CAP. /quietfed suppresses only passive explanation, never enforcement. Active fanout produces no extra per-group notices/logs; owner notifications/federation logs remain independent.

/fedstat shows own active sources; human reply/target and TARGET FED_ID query another user or an exact reason/date/source. /fbanstat ID is an own-user reason/date form. Status pages show20 sources and a diagnostic for more; complete discovery pagination remains11. IDs/records are confined to this bot.

/fbanlist csv|minicsv|json is owner-only: full CSV id/name/username/reason/date, minicsv id/reason, JSON array with user_id/name/username/reason/date. /importfbans replies to an actual document, validates UTF-8 CSV id/reason or JSONL/NDJSON objects requiring user_id. Own JSON-array export is an explicit adapter; arrays are rejected as JSONL. Import/export share the sourced30-minute interval per federation. Local bounds2MiB/1,000 records; oversized exports reject instead of truncating. Every row and current reason policy validate before a single transaction writes bans/jobs. Identical duplicates coalesce/report; conflicts reject all. Export CSV prefixes formula-like text with apostrophe, and our CSV reader reverses that literal encoding. Imported date/ownership/admin/namespace metadata grants no trust and does not replace current actor/date.

Only actual observed messages, joins and requests create user/group observations; request observation is not membership proof. Fanout expands100 destinations/parents per job and shares a20/sec outbound quota; local waits do not consume API retries. A newer unban fences old jobs and cannot commit over an old dispatch holding the federation row. Current attachment/namespace/role/protected target/capability is rechecked. RetryAfter has bounded retries; unknown effects remain uncertain without blind replay. Passive quota/known retry queues eventual current-policy enforcement. A deleted/left federation retires only local federation provenance while keeping actual bans; fresh manual moderation remains available. Uncertain ownership is retained and cannot authorize automatic unban.

## Complete data and discovery paths

/export all or /export notes rules:current admin. /import MODULES replies to actual own v1 JSON; /reset MODULES selects defaults; current attributable creator plus delivered personal five-minute single-use/revision/digest confirmation. Sixteen families:moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Local interval five minutes. Real owned transient work safely retires; real bans/trust/roles/ownership/issued identities are not imported. No full foreign Rose schema promise.

/privacy policy, /privacy data [CURSOR], /privacy delete only the requesting human's own PM. Paginated200-row19-section own-data export, optional module convenience erasure and durable cache cleanup; minimum active security/ownership/payments/order/platform preferences/global profile retained. Read policy for limits; no blanket retention/backup/Telegram erasure promise.

/setlang CODE changes group/connected replies with fresh change-info; private /lang personal platform language. All31 native published bundles,18 family guides; /help FAMILY, /help COMMAND, /help FAMILY 2. /fedstat TARGET after:UUID continues sources; /fbanstat UUID own data. /info displays available profile plus separately bounded actual current federation source page; anonymous /id shows sender chat identity. Ordinary quietfed bot-admin changes use shared human review/explicit skip-review, with current rights and attachment generations; membership/owner work stays attributable human.
