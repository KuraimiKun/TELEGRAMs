# Reviewer-supplied Rose specification digest

Reference date: 12 October 2026 (Asia/Jakarta). Sources were read through the reviewer's web tools. This is independently written, condensed specification material, not a copied website or full archival snapshot. It accounts for the 50 documentation navigation pages below. The cloud agent may use it offline and must label its evidence `reviewer-supplied digest`, retaining each original URL; do not claim direct cloud retrieval or that unspecified details are known.

Decompose behaviors, syntax variants, permissions and defaults into stable feature rows. A module summary is not one completed feature. Where a default/edge case is not stated here, record `unspecified` and the precise question. Preserve current live-group defaults. Distinguish documented behavior from proposed platform hardening. Implementation prompts will refine remaining details before the affected phase.

## S01 — Introduction

[Source](https://missrose.org/docs/). Navigation/overview, not a separate moderation function. Use it as the page-coverage denominator, with the nested pages below.

## S02 — Getting started

[Source](https://missrose.org/docs/getting-started/). Provide an add-to-group entry point, onboarding and explanation of required Telegram administrative rights. Actual bot identity must come from our runtime. An unprivileged bot cannot promise moderation capability. The website's specific hosted username is not a dependency for our implementation.

## S03 — Before you start

[Source](https://missrose.org/docs/basics/). Orientation and username-resolution limitations. A user unknown to the bot may not be resolvable by username; preserve reply/ID alternatives and clear errors instead of guessing identity.

## S04 — Command usage

[Source](https://missrose.org/docs/basics/command-usage/). Group commands configure that group; private connections provide another access path. Boolean synonyms are on/yes/true and off/no/false. Documented common duration suffixes are m/h/d/w. Module-specific bounds still apply. Antiflood timers additionally show seconds in their own page. Existing Group Guard seconds support is a compatibility extension.

## S05 — Info

[Source](https://missrose.org/docs/basics/info/). `/id` supports self/current group, reply and known username. `/info` supports self, reply, username or ID; show available name/username/ID, group membership and current federation ban information. Unknown users get an informative failure. Negative group IDs differ from user IDs. Do not pretend the Bot API can resolve every arbitrary user username.

## S06 — Basic chat connections

[Source](https://missrose.org/docs/basics/connections/). `/connect` in a group starts a private connection; PM accepts group ID or public group username. This is an introductory description of S40's same feature, not a second connection system.

## S07 — Languages

[Source](https://missrose.org/docs/basics/languages/). `/setlang` offers selection; a language-code argument selects directly. Setting affects group/connected-chat responses. Rose documents English-only start/help; retaining our localized help is a deliberate compatible enhancement. Published roster: AR, AZ, BE, BG, CKB, DE, EN-GB, EN-PT, ES, ES-AR, FA, FIL, FR, HE, ID, IT, ML-IN, MS, NL, PL, PT, PT-BR, RU, SH, TA, TR, UK, UZ, VI, ZH-CN, ZH-TW. Inventory every locale separately; aliases and fallback do not equal complete translations. The page points to runtime help for possible newer additions, which remain unobserved.

## S08 — Rules

[Source](https://missrose.org/docs/basics/rules/). `/rules`, `/setrules`, `/resetrules`; `/privaterules` switches group delivery versus a PM-opening button. Formatting is supported. `{rules}` creates a rules button in supported content. `/setrulesbutton` and `/resetrulesbutton` customize/reset its label. Keep rules access behavior separate from settings authorization.

## S09 — Administrator permissions

[Source](https://missrose.org/docs/moderation/admins/). Settings require change-info, deletion requires delete-messages, sanctions require restrict-members, pins require pin-messages, promotion/demotion requires promote-members, topics require manage-topics. `/promote` assigns the caller/bot permission intersection excluding promotion rights; `/demote` removes appropriate bot-editable admin roles. `/adminlist` is public but omits anonymous admins. `/adminerror` controls permission-error responses; `/admincache` refreshes cached admins. Anonymous commands normally require a button to identify an admin and check their actual rights. `/anonadmin on` allows assumed admin rights, explicitly excluding owner authority; off restores verification. Owner-only actions always need attributable owner authorization.

## S10 — Pins

[Source](https://missrose.org/docs/moderation/pins/). Reply `/pin` pins without a loud notification; `/pin loud` requests notification. `/permapin` sends formatted content and pins that new message, rather than establishing a perpetual re-pin scheduler. `/unpin` removes latest or replied pin; `/unpinall` clears pins. `/antichannelpin` unpins automatically linked channel posts; `/cleanlinked` deletes those posts from the discussion group. Keep linked-channel deletion distinct from generic forwarded-message locks.

## S11 — Approvals

[Source](https://missrose.org/docs/moderation/approvals/). `/approve` accepts usual target forms and an optional reason. `/approval` checks status/reason; `/approved` lists, using a file for large lists. `/unapprove` removes a user; `/unapproveall` is group-owner-only. Approvals exempt trusted users from automated actions while leaving manual authority separate. Interactions with federation bans/newcomer/raid policies need explicit precedence decisions rather than guessed exemptions.

## S12 — Purges

[Source](https://missrose.org/docs/moderation/purges/). Reply `/del` deletes the target and command without a completion reply. Reply `/purge` deletes from the selected starting message through the command; `/purge N` selects N messages beginning at the reply. There is no non-reply purge-all shortcut. `/spurge` suppresses completion output. `/purgefrom` and `/purgeto` mark range endpoints. Respect deletion limitations; stale messages need truthful feedback. Bind two-step ranges to authorized actor/chat and impose our documented operational cap. An old claim that bots cannot see other bots is conditional and must be checked against current API support.

## S13 — Admin logs

[Source](https://missrose.org/docs/moderation/log-channels/). Documented setup: add bot as channel admin, send `/setlog` in that channel, forward the original command to the group to associate it. This is different from Group Guard's numeric destination shortcut, which should remain an additional authorized path. Multiple groups may share the channel. `/unsetlog`, `/logchannel`, `/logcategories`, `/log`, `/nolog`. Categories: settings, admin, user, automated, reports, other; all enabled by default. The documented leave-log behavior stops at 50 group members. Verify destination/source authorization and don't accept a fabricated forward as ownership proof.

## S14 — Restrictions

[Source](https://missrose.org/docs/moderation/restrictions/). Families: ban/tban/dban/sban/unban; mute/tmute/dmute/smute/unmute; kick/dkick/skick. Targets are reply, known username or ID; reasons are optional. Temporary commands require durations. Delete-and-act commands require replies. Manual silent variants remove the replied message if present, remove the command and suppress group confirmation. Logs are a separate policy; silence does not imply deleting audit evidence. Kick allows rejoin. Invalid time must never accidentally become permanent.

## S15 — Warnings

[Source](https://missrose.org/docs/moderation/warnings/). `/warnings` reports settings; `/setwarnlimit`, `/setwarnmode` choose threshold/action, including kick/ban/mute and temporary ban/mute. `/warn`, `/dwarn`, `/swarn`; delete/silent variants have their documented message effects. `/rmwarn` removes latest; removal button removes a warning; `/resetwarn` clears a user's warnings; `/warns` displays reasons. `/setwarntime` sets/off disables age-based expiry for individual warnings; example also spells `/warntime`. When threshold sanction is applied, warnings reset. Docs say both limit and going over the limit without a rigorous boundary definition: record the ambiguity; don't clear history before a failed sanction.

## S16 — Reports

[Source](https://missrose.org/docs/moderation/reports/). Reports are enabled by default and controlled with `/reports`. Reply `/report` or `@admin` reports the offending message and notifies admins through mentions. Keep current `/admin` and `/admins` aliases if useful, while ensuring group report routing does not expose the platform's private admin UI. Anonymous administrator privacy still applies.

## S17 — Disabled commands

[Source](https://missrose.org/docs/moderation/disabling/). `/disabled`, `/disableable`, `/disable`, `/enable`; none disabled by default. Disabled commands are ignored; `/disabledel` optionally deletes them. `/disableadmin` extends disabling to admins, who can restore settings. Published disableable names: adminlist, antiflood, approval, connect, fedadmins, fedinfo, fedsubs, filters, flood, id, info, kickme, locks, locktypes, notes, rules, runs, saved, warnings, warns. Some names are not otherwise defined by these pages; inventory them as unresolved aliases/behaviors, not automatically invented features.

## S18 — Welcomes

[Source](https://missrose.org/docs/greetings/). `/welcome` shows configured content, accepts boolean toggles, and supports `noformat` inspection. `/setwelcome` accepts formatted text or replied sticker/media with optional caption; `/resetwelcome` restores defaults. Use shared formatting and fillings, notably the canonical `{chatname}`. Preserve Group Guard's `{group}` and `{count}` as extensions. Welcome state, content reset and verification are separate settings.

## S19 — Goodbyes

[Source](https://missrose.org/docs/greetings/goodbyes/). `/goodbye` toggles and displays, including `noformat`; `/setgoodbye` accepts text or replied media/stickers with caption; `/resetgoodbye` resets content. Support common formatting/fillings. Capture the departing user's identity from the leave event rather than assuming a message sender is the departing user.

## S20 — Advanced greetings

[Source](https://missrose.org/docs/greetings/advanced/). Refers to service cleaning and CAPTCHA, covered separately. `/cleanwelcome` removes old welcome messages; the documented period is five minutes and is not presented as configurable. Preserve the behavior distinction between greeting messages and Telegram service messages.

## S21 — Anti-spam overview

[Source](https://missrose.org/docs/anti-spam/). Overview/navigation for locks, CAPTCHA, blocklists, flood and raids; record as non-functional coverage rather than duplicate commands.

## S22 — Locks

[Source](https://missrose.org/docs/anti-spam/locks/). `/locks`, `/locks list`, `/locktypes`, multi-type `/lock`/`/unlock`; nothing locked by default. Admins exempt; locks precede blocklists. `/lockwarns` enables warnings. Per-lock reason/action syntax uses `###` and `{mode}`; actions include kick, ban/tban, mute/tmute.

Roster: all, album, anonchannel, audio, bot, button, cashtag, checklist, cjk, command, comment, contact, cyrillic, document, email, emoji, emojicustom, emojigame, emojionly, externalreply, forward, forwarduser, forwardbot, forwardchannel, forwardstory, game, gif, guestbot, inline, invitelink, botlink, location, outsidereaction, phone, photo, poll, reaction, rtl, spoiler, sticker, stickeranimated, stickerpremium, text, url, video, videonote, voice, zalgo.

`/allowlist`, `/rmallowlist`, owner-only `/rmallowlistall`. Allowlist kinds: URL/button domain/subdomain/path; invites by exact link/chat/username; inline bots; sender channels; commands; sticker/emoji packs; forwarded identities. Pack shortcuts include `stickerpack:<>` and `emojipack:<>` from replies. `comment`/`outsidereaction` concern non-members of linked discussions. Detect Unicode/entity/media/origin/event types separately.

## S23 — CAPTCHA

[Source](https://missrose.org/docs/anti-spam/captchas/). `/captcha`, `/captchamode`; button default, text image selection, math, text2 character selection. Non-button challenges open PM. Success releases verification mute; failure temporarily bans; unsolved users stay muted or are kicked according to settings. Successful verification is remembered per group; an admin kick resets it, voluntary leave does not. Docs require welcomes enabled.

`/setcaptchatext`, `/resetcaptchatext`: plaintext label, no fillings. Join requests send PM verification, optionally rules acceptance, then approve and welcome; bot needs invite-users. `/captchakick`, `/captchakicktime`: default kick deadline five minutes, allowed five minutes to one day. `/captcharules` includes rules acceptance. `/captchamutetime` schedules automatic release or `off` disables it. Issued challenge state must remain independent of later settings edits and unrelated sanctions.

## S24 — Blocklist management

[Source](https://missrose.org/docs/anti-spam/blocklists/). `/addblocklist` accepts word, quoted phrase or parenthesized comma-separated triggers with optional shared reason; `/blocklist` lists; `/rmblocklist` removes singles/phrases/multiple entries; owner-only `/rmblocklistall` clears. Other pages use `/blocklist` as an adding alias, so support an explicit, tested argument/no-argument distinction while preserving our older aliases. Individual action modifiers can be embedded in reasons/content.

## S25 — Blocklist modes

[Source](https://missrose.org/docs/anti-spam/blocklists/modes/). `/blocklistmode` selects nothing, warn, kick, ban/tban, mute/tmute. Default nothing still deletes the message. `/blocklistdelete off` stops deletion without necessarily disabling the selected user action; on restores deletion. Temporary actions take common durations. Per-entry overrides are distinct from default mode.

## S26 — Advanced blocklists

[Source](https://missrose.org/docs/anti-spam/blocklists/advanced/). Full-word matching; normalize accents and repeated spaces. `?` matches one non-space character, `*` zero/more non-space characters, `**` arbitrary characters; backslash escapes modifiers. `/setblocklistreason`/`/resetblocklistreason` control fallback reason. Per-entry `{action}` overrides default; silent per-entry actions require S49 and cannot be the default blocklist mode.

Typed triggers: `stickerpack:` with reply/emoji extraction; `file:` names/extensions with wildcards; `forward:` and `inline:` identities; `prefix:` start-only; `exact:` entire message; `lookalike:` visually similar forms. Custom-clone `name:` and `username:` patterns apply to observed users at join/speaking; unseen profile changes cannot be detected. The lookalike example mistakenly spells exact; the username prose mistakenly discusses inline bots. Record both defects. Use declared prefixes as the proposed canonical grammar, with tests before implementation.

## S27 — Antiflood

[Source](https://missrose.org/docs/anti-spam/antiflood/). `/flood` status; `/setflood` consecutive-message limit; `/setfloodtimer` per-user count/time window, including seconds. `/setfloodmode` accepts kick, ban/tban, mute/tmute and gated silent variants. By default, delete messages beyond the limit; `/clearflood on` deletes the whole observed flood sequence, off restores exceeded-only deletion. Consecutive example describes acting after N messages while timer example says more than N; make boundary tests and source uncertainty explicit rather than reusing one threshold accidentally.

## S28 — AntiRaid

[Source](https://missrose.org/docs/anti-spam/antiraid/). During activation, new joins are temporarily banned. Default active period six hours; default ban period one hour. `/raidtime`, `/raidactiontime` configure independently. `/antiraid` shows status and an enable option; `on` uses configured period, a duration overrides it, `off` stops immediately. `/autoantiraid N` triggers when more than N users join in under one minute; off/no disables. Integrate without guessing admin/approval/federation exemption precedence.

## S29 — Federation overview

[Source](https://missrose.org/docs/federations/). Federations hold bans/reasons under their own owner and admins; groups opt in to shared enforcement. Rose does not provide global bans here. Our equivalent federation service cannot join Rose's existing private network simply by copying a fed ID. Keep existing CAS as our separate optional protection.

## S30 — Federation info

[Source](https://missrose.org/docs/federations/fedinfo/). `/fedinfo` and `/fedadmins` support current/own fed or explicit fed ID; `/chatfed` identifies the group's federation; `/myfeds` lists federations where the user has admin status. IDs are distinct from group IDs. Preserve group/PM target context in tests.

## S31 — Creating federations

[Source](https://missrose.org/docs/federations/creating/). `/newfed` and `/delfed` operate in PM; one owned federation per user; names limited to 64 characters, with documented truncation. `/renamefed` renames. Creation returns ID. Deletion removes federation data and cannot be undone; users already banned by it remain banned in Telegram. Do not automatically unban all former members on deletion. Federation transfer is not established by this page and must not be invented as a required feature.

## S32 — Managing federations

[Source](https://missrose.org/docs/federations/managing/). Owner controls `/fedpromote`, `/feddemote`; admin self-removal is `/feddemoteme ID`. `/fedreason` requires ban reasons; `/fednotif` controls owner PM notifications, enabled by default. `/setfedlog`/`/unsetfedlog` manage destination; channel setup takes fed ID and owner confirmation. Notification-off does not stop configured logs.

Owner `/fbanlist` supports csv, minicsv and json. Banlist functions are limited to once per 30 minutes. Reply `/importfbans` reads CSV with id/reason columns or JSONL/NDJSON records requiring user_id; optional names/username/reason. Do not silently treat newline JSON as an array-only format. `/subfed ID`, `/unsubfed ID`, `/fedsubs` manage directed banlist subscriptions for linked groups. Graph/provenance/job implementation requirements are our hardening choices.

## S33 — Joining federations

[Source](https://missrose.org/docs/federations/joining/). Group creator alone uses `/joinfed ID` or `/leavefed`; need not own the destination federation. Per-chat `/quietfed` controls visible explanations when federation-banned users join and are removed. It does not disable enforcement.

## S34 — Federation bans

[Source](https://missrose.org/docs/federations/fedbans/). `/fban`/`/unfban` accept usual targets/reasons. In a group, authority comes from that group's federation role, independently of local group-admin status. PM commands target the user's owned federation even if a chat connection exists. Active bans immediately enforce in fed groups where the user has been observed, without per-group visible/log notifications for that fan-out. Passive checks on joins/speaking also enforce subscribed-fed bans and explain the source unless quietfed. Track observed membership minimally; avoid inaccessible history enumeration.

## S35 — User federation commands

[Source](https://missrose.org/docs/federations/user-commands/). All users can use `/fedstat` for their own bans, reply/target forms for others, and target plus fed ID for reason/date. `/fbanstat ID` is documented for one's own reason/date. Group the overlapping forms as explicit aliases/target-resolution contracts. Do not leak data across our bot namespace.

## S36 — Filters

[Source](https://missrose.org/docs/filters/). `/filter` saves words, quoted phrases, parenthesized multiple triggers or replied media with optional content; `/stop` removes; creator-only `/stopall`; `/filters` lists. Default reply/fillings use trigger sender; `{replytag}` changes to the replied user when available. `prefix:` and `exact:` restrict start/whole-message matching. `{user}` excludes admins; `{admin}` restricts to admins; `{allow_bot}` allows bot triggers, otherwise ignored. Shared formatting applies. Custom-clone `{command}` optionally adds a description and publishes slash filters to group command suggestions; documented spelling limits are English letters/digits/underscore and fewer than 32 characters. Validate against Telegram's actual command limits and record any interpretation difference.

## S37 — Notes

[Source](https://missrose.org/docs/notes/). `/save` stores/replaces text or replied attachment; quoted names allowed. `/get`, hashtags, `/notes`, `/clear`. Notes public by default unless `{admin}`. `/privatenotes` directs users through a PM-opening button; `{private}` overrides per note, `{noprivate}` forces group delivery. Replies/fillings use the replied user when present, otherwise opener. Custom-clone repeated notes use a duration modifier; prose says `{repeated time}` while example says `{repeat time}`. Treat them as proposed compatibility aliases with dedicated tests. Use real durable scheduled delivery, not a selector stub.

## S38 — Formatting

[Source](https://missrose.org/docs/formatting/). Input supports code, italic, bold, strike, underline, spoiler, ordinary/expandable quotation and hyperlinks. URL buttons use buttonurl syntax; `:same` joins rows; `#note` targets note menus. Fillings: `{first}`, `{last}`, `{fullname}`, `{username}` with fallback, `{mention}`, `{id}`, `{chatname}`, `{rules}`. Controls: `{preview}`, `{nonotif}`, `{protect}`, `{mediaspoiler}`. Random alternatives separated by `%%%`. Do not confuse control modifiers with literal visible text. Existing Group Guard HTML remains stored/rendered as legacy HTML. Platform content protection is a Telegram flag, not a guarantee against every capture method.

## S39 — Button generator

[Source](https://missrose.org/docs/formatting/button-generator/). A helper builds button markup, including labels, links and row layout. Provide a functional equivalent integrated with our content editor/commands; we do not need to copy Rose's website or graphical assets. Note-button menus and ordinary URL buttons need distinct targets.

## S40 — Connections

[Source](https://missrose.org/docs/connections/). Any chat member may connect, but only suitably privileged admins mutate settings. PM `/connect ID/@group`; group `/connect` provides a personal connection button. One active group at a time; new connection replaces previous. `/disconnect`, `/connection`, `/id` in context. PM `/connect` without arguments lists the last five chats; `/reconnect` also supports switching. History is convenience, not an authorization grant. Revalidate membership/rights.

## S41 — Echo and broadcast

[Source](https://missrose.org/docs/echo/). `/echo` and `/say` resend formatted content. `/broadcast` sends to the bot owner's groups; it is not authority for an arbitrary group admin to address every group served by a shared bot. Define standalone operator/factory-owner authority separately from group rights and existing platform broadcasts. Preserve destination isolation and rate limits.

## S42 — Settings exports/imports/reset

[Source](https://missrose.org/docs/exports/). Admin `/export` produces JSON, optionally selected modules. Reply `/import` imports all/selected modules and is creator-only. `/reset` is creator-only with confirmation. These operations are rate limited; no exact interval is given here. Source docs do not provide the complete settings-file schema: don't claim full Rose-file compatibility without a real verified format. Module-selective own-format round trips remain mandatory.

## S43 — Privacy

[Source](https://missrose.org/docs/privacy/). PM-only `/privacy` exposes policy, access and deletion of stored personal data. It does not define our exact retention periods or every field deletion rule. Inventory those as product-policy decisions; do not present proposed 7/30/90-day policies as Rose requirements.

## S44 — Topics

[Source](https://missrose.org/docs/topics/). Settings are shared across a forum's topics. Welcomes use the default/general action topic until `/setactiontopic` in a topic changes it; `/actiontopic` reports it. `/newtopic`, `/renametopic`, `/closetopic`, `/reopentopic`, `/deletetopic`; deletion removes topic/messages. Manage-topic authorization and handling of absent/deleted/general topics are essential. Closing a topic does not stop Telegram admins posting there.

## S45 — Command cleaning

[Source](https://missrose.org/docs/cleaning/clean-command/). `/cleancommand` deletes command messages after handling, regardless of sender, while still executing authorized commands; `/keepcommand` reverses. Types all/admin/user/other; `/cleancommandtypes` lists. Other includes unrecognized/other-bot commands. This is different from locking or disabling execution. The page's example uses join/leave/pin, inconsistent with its command-type table; use documented table types and record the typo.

## S46 — Bot-message cleaning

[Source](https://missrose.org/docs/cleaning/clean-message/). `/cleanmsg` and `/keepmsg` select all or categories; `/cleanmsgtypes` lists. Categories action/filter/note. Enabled categories delete corresponding bot messages after five minutes. Keep timed cleaning distinct from immediate silent actions and Telegram service cleaning.

## S47 — Service-message cleaning

[Source](https://missrose.org/docs/cleaning/clean-service/). `/cleanservice` boolean/all or categories; `/nocleanservice` removes selected categories; `/cleanservicetypes` lists. Categories join, leave, other, photo, pin, title, videochat. Other includes payment/proximity/web-app/auto-delete changes; deleting their message must not skip functional payment processing. Telegram may omit join/leave service updates in larger groups; absence does not prove our cleaner ran. Respect undeletable service-message limits.

## S48 — Advanced overview

[Source](https://missrose.org/docs/advanced/). Explanation/navigation for silent actions and bot-to-bot. No additional standalone command set.

## S49 — Automated silent actions

[Source](https://missrose.org/docs/advanced/silent-actions/). `/silentactions on` is group-owner-only and requires a log channel. Automated sban/skick/smute/swarn support temporary durations where relevant. After enabling, affected settings must be explicitly set to silent; don't silently convert all existing automatic actions. Disabling or removing log destination makes existing silent actions loud. Inventory separately from manually typed `/sban` etc.; do not apply this automatic-mode gate to manual commands without supporting evidence.

## S50 — Bot-to-bot

[Source](https://missrose.org/docs/advanced/bot-to-bot/). `/bot2bot` modes off(default)/admin/all control which bots trigger commands. Bots still need ordinary command permissions. Bot admin mutations require human review by default; `/bot2botskipreview` toggles review bypass while retaining the bot's real rights. `{allow_bot}` is a per-filter opt-in. BotFather bot-to-bot configuration is a deployment requirement for custom bots. Defend self-trigger loops and replayed reviews. Receiving a command from another bot does not give it owner authority.

## T01 — Telegram capability notes

[Official reference](https://core.telegram.org/bots/api). Current reference includes `deleteMessageReaction` and `deleteAllMessageReactions`, `getChatAdministrators(return_bots=...)`, reaction permissions and guest/bot message support. Reaction removals require delete-message rights. Reaction updates require explicit subscriptions and admin eligibility. `getChatMember` has restricted guarantees when bot is not admin. Bulk deletion accepts up to 100 IDs and acknowledges without a per-ID deleted count; deletion age/service limitations apply. Very short/long restriction deadlines can become permanent. Join-request `user_chat_id` has a short contact window. Check actual installed SDK and deployed server; documented API availability alone does not prove deployment support. Don't hardcode a server version from a mutable image tag.

## Remaining source uncertainties and review decisions

- Unknown indirect commands: runs, saved and some antiflood alias semantics. Separate known disable-catalog membership from undefined execution behavior.
- Typos: warntime/setwarntime; repeat/repeated; lookalike example; username blocklist prose; cleancommand example. Proposed parser aliases or canonical prefixes must be stated and tested.
- Threshold boundaries and exemption precedence need module-specific decisions. Do not assert that generic approval bypasses every federation/security action.
- Complete Rose export schema and runtime-help additions are unobserved. Capabilities of the deployed local Bot API are unobserved. These remain specific gaps, not reasons to call every feature externally blocked.
- Full original-page archival coverage and live Rose behavior are not claimed by this digest. Preserve exact limits of source evidence in reports and refine affected-phase requirements before implementation.
