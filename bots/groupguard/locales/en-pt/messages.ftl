## Group Guard — independently authored en-pt. Shared keys come from core/locales.
group-welcome =
    🛡 <b>Thanks for adding me!</b>

    Make me an <b>admin</b> (delete messages, ban users, pin) so I can protect this group,
    then send /settings to configure captcha, anti-flood, locks and more.
gg-start =
    🛡 Ahoy <b>{ $name }</b>! I be <b>Group Guard</b> — I keep groups clean and safe.

    • 🤖 Captcha for newcomers, anti-bot & CAS anti-spam database
    • 🌊 Anti-flood, 🔒 locks (links, forwards, media…), 🚫 word blocklist
    • 🔨 /ban /mute /kick /warn with durations, /purge
    • 📝 Notes, 🔁 keyword auto-replies, 📜 rules, 👋 custom welcomes
    • 🌙 Night mode, 🧠 AI spam detection, 📒 log channel

    Add me to yer group and make me admin 👇
gg-help =
    📖 <b>Commands</b> (in groups)

    <b>Moderation</b> — reply to a message or give @username / id:
    /ban [10m|2h|3d] [reason] · /unban · /kick · /mute [time] · /unmute
    /warn [reason] · /unwarn · /warns · /resetwarns
    /purge (reply: delete everything since) · /del · /pin [loud] · /unpin
    /report (reply) — call the admins · /id

    <b>Content</b>
    /rules · /setrules text · /setwelcome text · /resetwelcome
    Placeholders: <code>{"{"}first{"}"}</code> <code>{"{"}mention{"}"}</code> <code>{"{"}group{"}"}</code> <code>{"{"}count{"}"}</code>
    /save name text (or reply) · #name · /notes · /clear name
    /filter word text (or reply) · /filters · /stop word

    <b>Protection</b>
    /lock links forwards media … · /unlock · /locks
    /addblock word, word · /rmblock word · /blocklist
    /night 23 7 +3 (close the chat at night) · /night off
    /setlog -100… (log channel) · /settings — full panel
gg-welcome-default = 👋 Ahoy { "{" }mention{ "}" } to <b>{ "{" }group{ "}" }</b>!
gg-credit = 🛡 Protected by @{ $bot }
gg-btn-add = ➕ Add me to yer group
gg-btn-commands = 📖 Commands
gg-btn-rules = 📜 Rules
gg-btn-human = ✅ I be human
gg-btn-unwarn = ↩️ Remove warning (admins)
gg-btn-locks = 🔒 Locks ({ $count })
gg-btn-open-settings = ⚙️ Open settings
gg-btn-admin-tab = 🛡 Groups
gg-captcha = 🤖 { $user }, please confirm you're human within <b>{ $minutes } min</b>, or you'll be removed.
gg-captcha-button = Tap the button below 👇
gg-captcha-math = What is <b>{ $a } + { $b }</b>?
gg-captcha-not-you = This button isn't for ye 🙂
gg-captcha-ok = ✅ Ahoy!
gg-captcha-wrong = ❌ Wrong answer. { $left } tries left.
gg-captcha-failed = ❌ Too many wrong answers.
gg-captcha-passed = ✅ { $user } verified — welcome!
gg-cas-banned = 🚫 { $user } is a known spammer (CAS) and was banned.
gg-join-request = 👋 To join <b>{ $group }</b>, confirm you're human:
gg-join-approved = ✅ You're in! Ahoy.
gg-join-expired = ⌛ This request expired — please request to join again.
gg-goodbye = 👋 { $user } left the group.
gg-flood-mute = 🌊 { $user } was flooding and is muted for a while.
gg-flood-kick = 🌊 { $user } was flooding and was removed.
gg-flood-ban = 🌊 { $user } was flooding and was banned.
gg-newbie-links = 🆕 { $user }, new members can't post links for the first { $hours } h.
gg-spam-banned = 🧠 { $user } posted spam and was banned.
gg-reason-blocklist = blocked word
gg-need-right = ⛔ Ye need the admin right “{ $right }” for this.
gg-right-admin = admin
gg-right-restrict = ban users
gg-right-delete = delete messages
gg-right-pin = pin messages
gg-right-change_info = change group info
gg-admins-only = ⛔ Admins only.
gg-need-target = 👤 Reply to a message, or give a @username or user id.
gg-target-admin = 🙅 I can't do that to an admin.
gg-bot-no-rights = ⚠️ I need to be an admin with the right permissions to do that.
gg-banned = 🔨 { $user } was banned. Reason: { $reason }
gg-banned-for = 🔨 { $user } was banned for { $time }. Reason: { $reason }
gg-unbanned = ✅ { $user } was unbanned.
gg-kicked = 👢 { $user } was kicked. Reason: { $reason }
gg-muted = 🔇 { $user } was muted. Reason: { $reason }
gg-muted-for = 🔇 { $user } was muted for { $time }. Reason: { $reason }
gg-unmuted = 🔊 { $user } can talk again.
gg-warned = ⚠️ { $user } has been warned ({ $count }/{ $limit }). Reason: { $reason }
gg-warn-limit-ban = 🔨 { $user } reached { $limit } warnings and was banned.
gg-warn-limit-mute = 🔇 { $user } reached { $limit } warnings and was muted.
gg-warn-limit-kick = 👢 { $user } reached { $limit } warnings and was kicked.
gg-unwarned = ↩️ Removed a warning from { $user } ({ $count }/{ $limit }).
gg-warn-removed = ↩️ Warning removed by { $admin }.
gg-warns = ⚠️ { $user } has { $count }/{ $limit } warnings.
gg-warns-reset = 🧽 Warnings of { $user } were reset.
gg-purge-reply = 🧹 Reply to the first message ye want to delete.
gg-purged = 🧹 Deleted { $count } messages.
gg-pin-reply = 📌 Reply to the message ye want to pin.
gg-report-reply = 🚨 Reply to the message ye want to report.
gg-reported = 🚨 Reported { $user } to the admins.
gg-setlog-usage = 📒 Usage: add me to yer log channel as admin, then <code>/setlog -100…</code> (the channel id).
gg-setlog-failed = ⚠️ I can't post in that chat. Add me there as an admin first.
gg-setlog-done = 📒 Log channel connected.
gg-setlog-off = 📒 Log channel disconnected.
gg-log-connected = 📒 This chat now receives the moderation log of <b>{ $group }</b>.
gg-log-flood = 🌊 Flood: { $user } → { $action }
gg-log-report = 🚨 Report about { $user }
gg-log-spam =
    🧠 AI spam ban: { $user }
    <blockquote>{ $text }</blockquote>
gg-rules =
    📜 <b>Rules</b>

    { $rules }
gg-no-rules = 📜 No rules set yet. Admins: /setrules yer rules
gg-rules-saved = 📜 Rules saved.
gg-rules-cleared = 📜 Rules cleared.
gg-welcome-usage = 👋 Usage: <code>/setwelcome Hi {"{"}mention{"}"}, welcome to {"{"}group{"}"}!</code> (or reply to a message)
gg-welcome-saved = 👋 Ahoy message saved.
gg-welcome-reset = 👋 Ahoy message reset to the default.
gg-note-usage = 📝 Usage: <code>/save name text</code>, or reply to a message with <code>/save name</code>.
gg-filter-usage = 🔁 Usage: <code>/filter word reply text</code>, or reply to a message with <code>/filter word</code>.
gg-note-saved = 📝 Saved — anyone can get it with <code>#{ $key }</code>.
gg-filter-saved = 🔁 I'll reply whenever someone says “{ $key }”.
gg-notes-empty = 📝 No notes yet.
gg-filters-empty = 🔁 No filters yet.
gg-notes-list = 📝 <b>Notes</b>
gg-filters-list = 🔁 <b>Filters</b>
gg-item-deleted = 🗑 Deleted “{ $key }”.
gg-item-missing = 🤷 Nothing saved under that name.
gg-items-limit = 📦 This group has reached the maximum number of notes and filters.
gg-lock-usage = 🔒 Usage: <code>/lock links</code> — types: { $types } (or <code>all</code>)
gg-locked = 🔒 Locked: { $types }
gg-unlocked = 🔓 Unlocked: { $types }
gg-locks-title = 🔒 <b>Locks</b>
gg-locks-panel = 🔒 <b>Locks</b> — locked content is deleted (admins are exempt).
gg-lock-links = Links
gg-lock-invites = Invite links
gg-lock-forwards = Forwards
gg-lock-media = Media
gg-lock-stickers = Stickers
gg-lock-gifs = GIFs
gg-lock-voice = Voice
gg-lock-polls = Polls
gg-lock-bots = Bots
gg-blocklist = 🚫 <b>Blocked words</b>: { $words }
gg-blocklist-empty = 🚫 No blocked words.
gg-blocklist-usage = 🚫 Usage: <code>/addblock word, another phrase</code> · <code>/rmblock word</code>
gg-blocklist-saved = 🚫 Blocklist updated ({ $count } words).
gg-night-usage = 🌙 Usage: <code>/night 23 7 +3</code> (from 23:00 to 07:00, UTC+3) · <code>/night off</code>
gg-night-on = 🌙 Night mode: the chat closes from { $start } to { $end } ({ $tz }).
gg-night-off = 🌙 Night mode off.
gg-night-start = 🌙 Good night! The chat is closed until { $end }.
gg-night-end = ☀️ Good morning! The chat is open again.
gg-panel =
    ⚙️ <b>Settings — { $group }</b>

    Tap an option to change it. Night mode hours: { $night } (change with /night in the group).
gg-panel-sent = 📬 I sent ye the settings in private.
gg-panel-start-first = 📬 Start a private chat with me first, then tap below:
gg-credit-vip = 💎 Hiding the “Protected by” line is a VIP feature (/vip in private).
gg-opt-wel = 👋 Ahoy: { $value }
gg-opt-cln = 🧹 Clean joins: { $value }
gg-opt-bye = 👋 Goodbye: { $value }
gg-opt-cap = 🤖 Captcha: { $value }
gg-opt-cpm = ⏱ Captcha time: { $value } min
gg-opt-fld = 🌊 Flood limit: { $value }
gg-opt-fla = 🌊 Flood → { $value }
gg-opt-wrn = ⚠️ Warn limit: { $value }
gg-opt-wra = ⚠️ Warns → { $value }
gg-opt-act = ⏳ Auto mute/ban: { $value } min
gg-opt-cas = 🛡 CAS anti-spam: { $value }
gg-opt-nwb = 🆕 No links for newbies: { $value } h
gg-opt-ais = 🧠 AI anti-spam: { $value }
gg-opt-ngt = 🌙 Night mode: { $value }
gg-opt-crd = 🏷 Credit line: { $value }
gg-opt-lang = 🌐 Language: { $value }
gg-val-button = button
gg-val-math = math
gg-val-off = off
gg-val-mute = mute
gg-val-kick = kick
gg-val-ban = ban
gg-adm =
    🛡 <b>Group Guard</b>

    • Protected groups: <b>{ $groups }</b>
    • Warnings issued: <b>{ $warns }</b>
    • Notes & filters: <b>{ $items }</b>
cmd-settings = Group settings (in a group)
cmd-help = Commands

# Phase 1A authorization, review and truthful action outcomes
gg-auth-denied = Authorization could not be verified. Nothing was changed.
gg-target-invalid = Pick ye a known human member. The target could not be verified.
gg-duration-invalid = Use a valid duration from 60s to 365d. Temporary commands require a duration.
gg-reason-invalid = The reason must be at most 256 characters.
gg-outcome-failed = The requested action failed or could not be authorized.
gg-outcome-partial = The action only partly completed. A ban may remain if the kick restoration failed.
gg-outcome-ancillary = The primary action completed, but a related step failed.
gg-review-request = Review: <b>{ $operation }</b>
    Target: { $target }
    Details: { $details }
    Duration (seconds): { $duration }
    A currently authorized human may approve within 120 seconds.
gg-review-approve = Approve this action
gg-review-unavailable = Review storage is unavailable. Submit a new command.
gg-review-expired = This review is expired, invalid or already used.
gg-review-consumed = This review was used. Check the action result; submit a new command to retry.
gg-duration-permanent = Permanent / no timer
gg-purge-ack = Deletion requested for { $requested } message IDs; API acknowledged { $acknowledged }. The confirmed deleted count is unknown.
gg-warning-removed = Warning removed.
gg-op-ban = ban
gg-op-mute = mute
gg-op-kick = kick
gg-op-unban = unban
gg-op-unmute = unmute
gg-op-warn = warn
gg-op-unwarn = unwarn
gg-op-resetwarns = resetwarns
gg-op-purge = purge
gg-op-delete = delete
gg-op-pin = pin
gg-op-unpin = unpin
gg-op-setlog = setlog
gg-op-unsetlog = unsetlog
gg-op-config = config
gg-op-save = save
gg-op-remove = remove
gg-op-panel = panel
gg-review-details-above = The full requested content is shown immediately above.
gg-warn-pending = Warning recorded; a threshold action is already being processed.

gg-done = Aye, done.

gg-setting-saved = Setting { $setting } saved.

gg-setting-value = { $setting }: { $value }

gg-setting-invalid = Invalid setting. Use on/off, a valid mode, or a duration such as 10m.

gg-warning-settings = Warnings: limit { $limit }; mode { $mode }; sanction { $duration }; warning expiry { $expiry }.

gg-admin-changed = { $action } completed for { $user }.

gg-admin-list = Public administrators:
    { $admins }

gg-approved = { $user } approved. Reason: { $reason }

gg-unapproved = Removed { $count } approvals.

gg-approval-status = Approval for { $user }: { $status }. Reason: { $reason }

gg-approval-list = Approved users:
    { $approvals }

gg-next-page = More entries: { $command }

gg-range-invalid = Invalid range. Select between 1 and { $cap } message IDs.

gg-range-start = Start saved for ye in this topic for 10 minutes. Reply /purgeto to the final message.

gg-range-missing = No start saved for ye in this topic. Reply /purgefrom first.

gg-content-needed = Supply content or reply to content (up to 3500 characters).

gg-log-status = Log destination: { $destination }. Enabled categories: { $categories }.

gg-log-unverified = I have no verified setup receipt for that original channel command. Send /setlog in the channel first.

gg-log-forward = Forward this original /setlog command to yer group. The connecting administrator must have change-info rights in both chats.

gg-info = Name: { $name }
    Username: { $username }
    ID: <code>{ $id }</code>
    Membership: { $membership }

gg-op-unpinall = unpinall

gg-op-permapin = permapin

gg-op-promote = promote

gg-op-demote = demote

gg-op-approve_user = approve_user

gg-op-unapprove = unapprove

gg-op-unapproveall = unapproveall

gg-unknown = Unknown

gg-chat-id = Chat ID: <code>{ $id }</code>

gg-on = On
gg-off = Off

gg-anon-enabled = Anonymous admin assumption enabled in this group. Same-group anonymous commands use this bot’s rights without identifying a human. Owner-only operations still require a verified creator. Use /anonadmin off to restore human review.

gg-right-invite_users = invite users

gg-right-promote_members = promote administrators

gg-right-manage_topics = manage topics

gg-right-creator = group creator

gg-log-join = { $user } joined.
gg-log-leave = { $user } left.

gg-warning-row = • #{ $id }: { $reason } (expires: { $expiry })

gg-menu-prompt = Pick ye an option.
gg-content-invalid = Content is invalid or exceeds Telegram's limits. Check the name, formatting, modifiers and buttons.
gg-content-unavailable = This content is unavailable or yer current group membership does not allow access.
gg-btn-private-note = Open note
gg-open-private = Open this content in private:
gg-items-cleared = Cleared { $count } entries.
gg-clearall-confirm = The group creator can confirm with <code>/{ $command } confirm</code>.
gg-button-usage = Usage: <code>/button "Label" https://example.com</code>. Add a line <code>"Note" #name same</code> for another button in the same row. The bot returns markup and a working preview.
gg-btn-accept-rules = Accept rules
gg-btn-open-verification = Open verification
gg-captcha-private = { $user }, open the private challenge to verify yer membership.
gg-captcha-choice = Match the image using the buttons. Mode: { $mode }; character position: { $position }.
gg-captcha-settings = CAPTCHA: { $enabled }; mode: { $mode }; kick: { $kick }; deadline: { $seconds } seconds; automatic mute release: { $release }.
gg-captcha-dependency = Enable welcomes before enabling CAPTCHA. Save rules before requiring rules acceptance.
gg-val-text = Text image
gg-val-text2 = Character image
gg-captcha-attempts-exhausted = Verification failed after too many incorrect answers. The failure restriction has been applied.
gg-captcha-admin-exempt = Ye are now a group administrator. This verification challenge has ended.
gg-captcha-question-text = Pick ye the word shown in the image.
gg-captcha-question-math = Solve the equation in the image and choose its answer.
gg-captcha-question-text2 = Pick ye character { $position } from the image, reading from left to right.
gg-locktypes = Available locks: <code>{ $types }</code>
gg-allowlist-title = Lock exceptions
gg-allowlist-invalid = Invalid exception. Use a domain/path, exact invite, @chat, or a typed identity such as stickerpack:name.
gg-reason-lock = Locked content: { $types }
gg-lock-applied = Applied the lock policy for { $types }. Reason: { $reason }
gg-reaction-failed = Reaction enforcement failed: { $code }. This Bot API server may not support reaction removal.
gg-reaction-anonymous = An anonymous reaction count update has no user or actor-chat identity. The available removal API requires one; no reaction removal was claimed.
gg-none = None
gg-blocklist-title = Blocklist
gg-blocklist-invalid = Invalid trigger, reason or action. Check quoted phrases, wildcard escapes and the required duration for temporary modes.
gg-blocklist-settings = Blocklist mode: { $mode }; delete matched messages: { $delete }.
gg-blocklist-action = Applied the blocklist policy to { $user }. Reason: { $reason }

gg-lock-album = Albums
gg-lock-anonchannel = Channel senders
gg-lock-audio = Audio
gg-lock-bot = Bots
gg-lock-button = Inline buttons
gg-lock-cashtag = Currency tags
gg-lock-checklist = Checklists
gg-lock-cjk = Chinese/Japanese/Korean text
gg-lock-command = Commands
gg-lock-comment = Nonmember comments
gg-lock-contact = Contacts
gg-lock-cyrillic = Cyrillic text
gg-lock-document = Documents
gg-lock-email = Email addresses
gg-lock-emoji = Emoji
gg-lock-emojicustom = Custom emoji
gg-lock-emojigame = Emoji games
gg-lock-emojionly = Emoji-only text
gg-lock-externalreply = External replies
gg-lock-forward = Forwards
gg-lock-forwarduser = User forwards
gg-lock-forwardbot = Bot forwards
gg-lock-forwardchannel = Channel forwards
gg-lock-forwardstory = Forwarded stories
gg-lock-game = Games
gg-lock-gif = GIF animations
gg-lock-guestbot = Guest bots
gg-lock-inline = Inline bots
gg-lock-invitelink = Telegram invitations
gg-lock-botlink = Bot links
gg-lock-location = Locations
gg-lock-outsidereaction = Nonmember reactions
gg-lock-phone = Phone numbers
gg-lock-photo = Photos
gg-lock-poll = Polls
gg-lock-reaction = Reactions
gg-lock-rtl = Right-to-left text
gg-lock-spoiler = Spoilers
gg-lock-sticker = Stickers
gg-lock-stickeranimated = Moving stickers
gg-lock-stickerpremium = Premium stickers
gg-lock-text = Text
gg-lock-url = URLs
gg-lock-video = Videos
gg-lock-videonote = Video notes
gg-flood-status = Flood: consecutive limit { $consecutive } (at N); timer { $count } / { $seconds }s (over N). Action { $mode }, { $duration }; whole sequence { $clear }.
gg-raid-status = Anti-raid { $active }; until { $until }. Activation { $period }; ban { $ban }; automatic threshold { $auto } joins/minute. Enable: /antiraid on · Stop: /antiraid off
gg-raid-banned = 🛡 { $user } was temporarily banned during active anti-raid.
gg-raid-declined = 🛡 Join request from { $user } was declined during active anti-raid.
gg-silent-consent-required = A creator must enable silent actions with a configured log before selecting this action.
gg-btn-enable-raid = Enable anti-raid
gg-human-required = This operation requires an identifiable human.
gg-group-message-required = Run this command on the actual group message or topic; private message IDs cannot identify group messages.
gg-connection-private = Use this connection command in our private chat.
gg-connection-disconnected = Disconnected. Yer last five groups remain available for reconnecting.
gg-connection-current = Connected to <b>{ $group }</b>. Current membership and permissions are checked for each operation.
gg-connection-none = No active group connection. Use /connect GROUP_ID or /connect @group.
gg-connection-open = Open yer personal connection in our private chat.
gg-btn-connect = Connect privately
gg-connection-history = Yer last five groups. Select one to reconnect; current membership is required.
gg-connection-unavailable = Connection unavailable. Ye must be a current human member and this bot must be an administrator there.
gg-catalog-unresolved = /{ $command } appears in the published catalog without a defined action. Use /notes or /flood for the implemented features.
gg-cleanup-failed = Message cleanup failed or is unavailable; no deletion was claimed.
gg-op-lock_change = change message lock policy
gg-op-allowlist_change = change lock exceptions
gg-op-allowlist_clear = clear lock exceptions
gg-op-blocklist_change = change blocklist entries
gg-op-blocklist_clear = clear blocklist entries
gg-op-raid_change = change anti-raid activation
gg-disabled-list = Commands: <code>{ $commands }</code>. /disable NAME and /enable NAME change execution; /disabledel controls deletion; /disableadmin includes administrators.
gg-cleanup-types = Available cleanup categories: { $types }
gg-cleanup-selected = Selected cleanup categories: { $types }
gg-advanced-status = { $setting }: { $value }. Automated silence needs creator consent and a log. Bot commands need their ordinary rights; default mutation review remains active. Custom bots need bot-to-bot visibility configured in BotFather.
gg-action-topic = Action topic: { $topic }. /setactiontopic in a forum topic selects it. General/default is 1.
gg-topic-unavailable = A current forum group and the matching topic-management permissions are required.
gg-topic-id-required = In a connected private chat, provide the topic ID explicitly.
gg-topic-general-delete = The general topic cannot be deleted; deletion confirmation requires an identifiable human.
gg-topic-delete-confirm = Delete topic { $topic } and its messages? This confirmation is personal and expires in two minutes.
gg-btn-confirm-delete = Aye, confirm deletion
gg-topic-changed = Topic action { $action } completed for { $topic }.
gg-op-policy_change = change command or cleanup policy
gg-op-topic_create = create a forum topic
gg-op-topic_rename = rename a forum topic
gg-op-topic_close = close a forum topic
gg-op-topic_reopen = reopen a forum topic
gg-op-topic_delete = delete a forum topic and its messages
gg-op-echo = send formatted content
gg-broadcast-owner = Only this bot's configured operator or the actual factory-child owner can broadcast to its groups.
gg-broadcast-queued = Group broadcast { $id } is queued. Destinations and delivery outcomes are isolated per bot.
gg-broadcast-busy = Another group broadcast is active or the five-minute creation interval has not elapsed.
gg-broadcast-empty = Ye have no group broadcast in this bot.
gg-broadcast-status = Broadcast { $id }: { $status }. Queued: { $queued }; delivered: { $sent }; failed: { $failed }; uncertain: { $uncertain }; cancelled: { $cancelled }.

gg-fed-created = Created federation <b>{ $name }</b>. This bot's federation ID is <code>{ $id }</code>.
gg-fed-info = <b>{ $name }</b>
    ID: <code>{ $id }</code>
    Owner: <code>{ $owner }</code>; administrators: { $admins }.
    Required reasons: { $reasons }; owner notifications: { $notifications }; log: { $log }.
gg-fed-list = Yer federations (owner or administrator):
    { $rows }
gg-fed-admins = Owner first, then federation administrators:
    { $rows }
gg-fed-quiet = Quiet federation explanations: { $value }. Enforcement remains active.
gg-fed-policy = Required reasons: { $reasons }; owner notifications: { $notifications }.
gg-fed-confirm-delete = Delete <b>{ $name }</b> (<code>{ $id }</code>)? Federation records and memberships will be removed permanently. Existing Telegram bans will remain. Aye, confirm within five minutes.
gg-fed-confirm-log = Set the log for <b>{ $name }</b> (<code>{ $id }</code>) to <code>{ $destination }</code>? Aye, confirm within five minutes. Yer destination rights and this bot's posting rights will be checked again.
gg-fed-confirm-sent = A personal confirmation was sent to the federation owner.
gg-fed-deleted = Federation deleted. Existing Telegram bans remain.
gg-fed-log-set = Federation log destination: <code>{ $destination }</code>.
gg-fed-cancel = Belay
gg-fed-cancelled = Belayled.
gg-fed-saved-delivery-failed = Federation change saved. Notification or log delivery failed; check the destination and bot access.
gg-fed-error-authority = This action requires the current federation owner or the appropriate federation role. Telegram group roles do not grant federation authority.
gg-fed-error-private = Use this command in yer own private conversation with this bot.
gg-fed-error-group = Use this command in the actual group. A private connection does not select a federation group.
gg-fed-error-owned = Ye already own a federation in this bot. Use /fedinfo, /renamefed or /delfed privately.
gg-fed-error-name = Provide a nonempty name without control characters. Names are truncated to 64 characters.
gg-fed-error-id = Provide a valid federation UUID from this bot. Rose network IDs cannot join our separate federation service.
gg-fed-error-missing = No federation was found in this bot or in the selected context.
gg-fed-error-creator = Only the group's current Telegram creator can join or leave a federation.
gg-fed-error-target = Provide a positive human ID, a human reply, or a currently verified known username. The owner cannot be demoted.
gg-fed-error-value = Invalid federation arguments. Use on/off for policy changes and a valid federation ID where required.
gg-fed-error-stale = This confirmation is expired, already used, or its federation/owner/destination state changed. Request a new confirmation.
gg-fed-error-destination = The federation owner needs current administration rights in the destination, and this bot needs posting access there. Channels require post_messages.
gg-fed-error-delivery = The personal confirmation could not be delivered or bound. Open a private chat with this bot and retry.
gg-fed-event = Federation <b>{ $name }</b> (<code>{ $id }</code>): { $event }. Actor: <code>{ $user }</code>.
gg-fed-event-rename = name changed
gg-fed-event-delete = deleted; existing Telegram bans remain
gg-fed-event-promote = administrator added
gg-fed-event-demote = administrator removed
gg-fed-event-self-remove = administrator resigned
gg-fed-event-reason = ban reason policy changed
gg-fed-event-notif = owner notification policy changed
gg-fed-event-log = log destination changed
gg-fed-event-unlog = log destination removed
gg-fed-event-ban = ban policy saved; enforcement queued
gg-fed-event-unban = ban policy removed; owned release queued
gg-fed-event-subscribe = ban subscription added; observed users queued for checking
gg-fed-event-unsubscribe = ban subscription removed; remaining sources preserved
gg-fed-ban-details = Target: <code>{ $user }</code>. Reason: { $reason }
gg-fed-passive = Federation policy blocks { $user }. Source: <b>{ $source }</b> (<code>{ $id }</code>). Reason: { $reason }
gg-fed-enforce-failed = Federation policy blocks { $user }, but removal failed. Check this bot's rights. Source: <b>{ $source }</b> (<code>{ $id }</code>). Reason: { $reason }
gg-fed-stat = Federation ban status for <code>{ $user }</code>:
    { $rows }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — active: { $status }; last change: { $date }.
gg-fed-stat-more = More sources exist. Query a specific federation ID for its reason/date.
gg-fed-intent-saved = Federation policy saved for <code>{ $user }</code> (version { $version }). Observed destinations are queued; current rights and other restriction sources are checked before effects.
gg-fed-subscriptions = Direct federation ban subscriptions:
    { $rows }
gg-fed-imported = Validated and saved { $count } ban records; ignored { $duplicates } identical duplicates. Observed destination enforcement is queued.
gg-fed-event-import = validated ban records imported; enforcement queued
gg-fed-error-file-format = Reply to a UTF-8 CSV with id/reason columns, JSONL/NDJSON records with user_id, or this bot's JSON-array export. Invalid rows prevent all writes.
gg-fed-error-file-limit = Ban files are limited to 2 MiB and 1,000 records. Oversized or missing files are rejected; lists are never silently truncated.
gg-fed-error-file-duplicate = Conflicting records for the same user ID were found. No bans were imported.
gg-fed-error-file-rate = Ban-list export and import share a 30-minute interval per federation. Retry later.
gg-fed-error-reason = Ban reasons must be at most 1,024 characters without unsupported control characters.
gg-fed-error-reason_required = This federation requires a nonempty reason for every ban.
gg-fed-error-cycle = A federation cannot subscribe to itself or create a directed subscription cycle.
gg-fed-error-graph_limit = Subscription limits reached: 32 direct targets, 128 reachable federations, depth 16, or 10,000 edges in this bot.
gg-data-confirm =
    <b>{ $operation }</b> · group <code>{ $group }</code>
    Modules: { $modules }
    File SHA-256: <code>{ $digest }</code>
    Aye, confirm within five minutes. Current creator rights and group revision are checked again. Only selected modules change; identity, trust and active bans stay.
gg-data-import = Import group modules
gg-data-reset = Reset group modules
gg-data-privacy-delete = Delete optional personal data in this bot
gg-data-confirm-button = Aye, confirm this change
gg-data-personal = Open the confirmation sent to yer private chat.
gg-data-saved = Selected modules saved.
gg-data-error-authority = Only a current attributable group creator can import or reset. Export requires a current admin.
gg-data-error-format = Reply to a valid Group Guard versioned JSON document; use /export to create one.
gg-data-error-limit = This file exceeds the size or configured content limit.
gg-data-error-version = This schema/version is unsupported; no changes were applied.
gg-data-error-module = Pick ye known modules: /export all, or /export notes rules. Import/reset use the same module names.
gg-data-error-field = Invalid or missing module fields; no settings were applied.
gg-data-error-item = Invalid content, options or repetition access; no content was saved.
gg-data-error-media = Media must be uploaded to this bot and accessible with getFile. Cross-bot file IDs are unsupported.
gg-data-error-destination = Log/topic references need current authority and bot capabilities. Topic IDs can only stay in the same group.
gg-data-error-language = Select an installed language with /setlang.
gg-data-error-stale = This confirmation expired, changed or was already used. Start again.
gg-data-error-restore = Owned temporary restrictions could not be safely restored. Their evidence remains; retry after checking bot rights.
gg-data-error-rate = Group data operations have a local five-minute interval. Try later.
gg-data-error-delivery = Private confirmation delivery failed. Start a private chat with this bot, then retry.
gg-data-error-saved_delivery = Settings were saved, but command suggestions could not be updated. Check bot permissions.
gg-privacy-policy =
    <b>Yer data in this Group Guard bot</b>
    /privacy data exports yer own connections, observed profiles, warnings, approvals, restriction and verification status, federation ownership/roles/bans and queued security work. It excludes other people's private content, answers, authentication and raw uploads. Follow the continuation command for more pages.
    /privacy delete removes this bot's optional connection history, observed name/username, inactive verification and terminal personal campaign content. Active warnings, restrictions, ban versions, roles, ownership, entitlements, minimal replay receipts and uncertain API work retain identifiers required for security and ordering. Use the explicit federation resignation/deletion commands for those relationships. The shared platform profile and other bots' records stay.
    Operators manage backups and audit storage separately; this command cannot erase external Telegram messages or backups. No automatic retention period is claimed.
gg-privacy-usage = /privacy policy · /privacy data [continuation] · /privacy delete — in yer private chat with this bot.
gg-privacy-private = This action requires the requesting human's private chat. Invalid access cursors cannot expose other users' data.
gg-privacy-next = Next data page: /privacy data { $cursor }
gg-privacy-deleted = Optional personal data removed from this bot. Active security, ownership and uncertain work retain minimal identifiers; see /privacy policy.
gg-language-usage = Pick ye a group language: /setlang { $codes }. Private /lang changes yer personal platform language.
gg-language-saved = Group response language updated.
gg-help-index =
    <b>Group Guard command guide</b>
    /help family · /help command · /help family 2. Group commands also work through yer verified /connect selection when listed. Private replies keep the actual private peer.
    Settings need change-info; sanctions restrict-members; deletion delete-messages; pins pin-messages; promotions promote-members; topics manage-topics. Bot rights are checked separately. Owner actions need the current attributable human creator. /settings opens yer personal group panel.
gg-help-search = <b>Commands matching { $query }</b>
gg-help-connected = Group or verified connected group; see family guide for rights
gg-help-group-only = Actual group message required
gg-help-unsupported = Catalog spelling retained; behavior has no confirmed source and returns a diagnostic
gg-help-next = Next page
gg-help-previous = Previous page
gg-help-family-title-moderation = Moderation and approvals
gg-help-family-title-messages = Message deletion and pins
gg-help-family-title-logging = Authorized logs
gg-help-family-title-settings = Group settings and language
gg-help-family-title-content = Notes, filters, rules and greetings
gg-help-family-title-captcha = Newcomer verification
gg-help-family-title-locks = Content locks and exceptions
gg-help-family-title-blocklists = Blocklist matching and actions
gg-help-family-title-antispam = Flood and raid protection
gg-help-family-title-connections = Private group connections
gg-help-family-title-identity = User and chat information
gg-help-family-title-policy = Command and bot policy
gg-help-family-title-cleanup = Command, bot and service cleanup
gg-help-family-title-topics = Forum topics
gg-help-family-title-utilities = Echo and operator campaigns
gg-help-family-title-federations = Federation roles, bans and subscriptions
gg-help-family-title-portability = Group files and own private data
gg-help-family-title-discovery = Help and content editor
gg-help-family-moderation =
    <b>Moderation</b> · Reply or supply a numeric ID / currently verified @username.
    /ban 20 reason · /tban 20 60s reason · /mute 20 · /tmute 20 2h reason; temporary sanctions accept 60 seconds–365 days. /kickme acts only on yourself. d variants also delete the replied message; s variants clean command/reply messages and need delete rights too. Current admins are protected.
    /setwarnlimit 3 · /setwarnmode ban · /setwarntime 1d. New groups use three warnings; existing defaults stay on upgrade. /approve bypasses ordinary automatic flood/content protection, never federation/CAS/raid or manual action. /promote needs promote rights and intersects caller/bot privileges; creator-only bulk reset and attributable owner checks stay separate.
gg-help-family-messages =
    <b>Messages</b> · /del requires an actual replied group message. /purge starts at that reply; /purgefrom and /purgeto freeze endpoints. Deletion is bounded by the configured limit and Telegram's deletion rules; batch acknowledgement is not an exact deleted count.
    /pin [loud], /permapin, /unpin, /unpinall require pin rights; bulk unpin needs the creator. /antichannelpin and /cleanlinked control automatic linked-channel messages.
gg-help-family-logging =
    <b>Logs</b> · /setlog -100… requires current destination admin authority and this bot's posting capability. Forwarded setup must come from an actual received channel setup message. /logcategories lists settings/admin/user/automated/reports/other; /log and /nolog select categories. Failures remain visible and cannot imply a completed action.
gg-help-family-settings =
    <b>Settings</b> · /settings opens a personal, expiring panel with current change-info checks. /setlang code stores the group language; private /lang stores yer personal language. /night 23 7 +3 closes chat overnight; /night off restores only the bot's owned, matching permission snapshot. External permission changes win.
gg-help-family-content =
    <b>Content editor</b> · /save word text or reply to text/media; /get word, #word and /notes read saved notes. Note triggers are single words; old broader names remain a legacy extension. /filter "quoted phrase" text, /filterprefix and /filterexact select matching. /stop removes a trigger; /clearall and /stopall require creator confirmation.
    Rose markup supports bold/italic/underline/strike/code, links, quotes and random %%% alternatives. Fillings: { "{" }first{ "}" }, { "{" }last{ "}" }, { "{" }fullname{ "}" }, { "{" }username{ "}" }, { "{" }mention{ "}" }, { "{" }id{ "}" }, { "{" }chatname{ "}" }, { "{" }count{ "}" }. Use /button for working URL/note/rules button markup. Controls include preview/nonotif/protect/mediaspoiler; notes support admin/private/noprivate/repeat, filters user/allow_bot/replytag/command. /save word Hello { "{" }repeat 5m{ "}" } schedules only public content with current author authority. /rules, private rules/notes, welcome/goodbye and reset commands share the renderer; media IDs belong to this bot.
gg-help-family-captcha =
    <b>Verification</b> · /captcha on/off; /captchamode off/button/math/text/text2; /setcaptchatext custom prompt; /captcharules on; /captchakick on/off; /captchakicktime and /captchamutetime set bounded timers. Existing challenges keep their issued generation/deadline. Join-request verification needs invite-users; member mutes need restrict-members. Issued answers are personal and single claim. Federation bans precede approval and captcha.
gg-help-family-locks =
    <b>Locks</b> · /lock links [action] and /unlock type; /locktypes lists actual canonical categories, /locks shows current state. /lockwarns controls warnings. /allowlist accepts a domain/path, exact invitation, @chat or declared stickerpack:/forward:/inline:/channel:/chat:/bot:/command: identities; malformed patterns are rejected. Exceptions apply to matching lock content, never all protection. Silent automation requires creator consent and an authorized automated log.
gg-help-family-blocklists =
    <b>Blocklists</b> · /addblocklist "quoted phrase" supports text/prefix/exact and declared identity entries with optional reasons/actions; /rmblocklist removes only exact selected keys. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute selects action; temporary modes require a duration. /blocklistdelete controls deletion independently. Wildcard matching is bounded; malformed patterns are rejected. Configured entry limits apply.
gg-help-family-antispam =
    <b>Flood and raid</b> · /setflood count controls consecutive flooding; /setfloodtimer count duration controls a timed window. /setfloodmode selects bounded sanction duration; /clearflood selects deletion. Legacy window defaults remain on upgrade. /flood and /antiflood show policy; their compatibility mapping is local.
    /antiraid on/off/duration, /raidtime, /raidactiontime and /autoantiraid configure a durable deadline and distinct entrant sanction. Raid precedes approvals/captcha; expiry is generation scoped and restart safe.
gg-help-family-connections =
    <b>Connections</b> · In private use /connect groupID or the personal group link. Current bot membership and yer membership are rechecked; mutations still need fresh exact rights. /connection shows yer selection, /disconnect removes it, /connect lists recent groups with continuation. Connected groups never confer federation ownership or platform operator authority.
gg-help-family-identity =
    <b>Information</b> · /id reads actual user/chat/source IDs, /info reads the current selected target. Reply and @username resolution need current scoped proof. Anonymous group posts do not identify their human author; no invented human ID is shown.
gg-help-family-policy =
    <b>Command policy</b> · /disable command, /enable command, /disabled and /disableable list canonical commands and aliases. /disableadmin controls admin bypass; /disabledel optionally deletes disabled commands. Recovery commands stay usable. /bot2bot off/admin/all checks actual bot membership; mutations normally require a human review, /bot2botskipreview is creator-only. /silentactions needs creator consent and an authorized automated log. Unknown runs/saved semantics stay explicit diagnostics.
gg-help-family-cleanup =
    <b>Cleanup</b> · /cleancommand admin/user/other and /keepcommand select command categories. /cleanmsg action/filter/note and /keepmsg select only this bot's actually delivered messages; receipts and five-minute jobs prevent guessed message deletion. /cleanservice and /nocleanservice select join/leave/other/photo/pin/title/videochat. Functional processing and valid payment handling happen before cleanup.
gg-help-family-topics =
    <b>Topics</b> · /newtopic name, /renametopic name, /closetopic and /reopentopic act on the current actual forum thread. /deletetopic requires creator confirmation; /setactiontopic stores a same-group destination. Telegram forum and manage-topics capability are required. Unsupported/deleted topic delivery returns its real failure.
gg-help-family-utilities =
    <b>Utilities</b> · /echo or /say renders inline/replied text/media through the shared bounded content renderer. /broadcast is restricted to this bot's configured platform operator or actual child owner and targets only this bot's configured groups. Durable per-destination outcomes preserve partial/uncertain deliveries; status/cancel do not repeat successful attachments.
gg-help-family-federations =
    <b>Federations</b> · /newfed name creates yer bot-scoped UUID. Private commands use yer owned federation independently of connections; explicit UUID reads do not confer roles. /fedpromote and /feddemote change federation admins; /feddemoteme resigns. /joinfed UUID and /leavefed need the current group creator. Deleting a federation does not silently unban real group bans.
    /fban userID reason and /unfban userID require current fed owner/admin; /fedreason, /fednotif and /setfedlog are owner settings. /quietfed suppresses passive notices only. /subfed UUID subscribes this federation to that one's bans, directed and cycle bounded. /fedstat [userID] and /fbanstat UUID show sources/status. /fbanlist csv/minicsv/json is owner-only with a 30-minute shared interval; /importfbans replies to bounded CSV or actual line-delimited JSON, with explicit own JSON-array support. Only actual observed users can be actively reconciled; no full member inventory is claimed.
gg-help-family-portability =
    <b>Group files and privacy</b> · /export all or selected module names requires current admin; /import and /reset require the attributable current creator and a personal five-minute, single-use confirmation. Local five-minute group interval; versioned own JSON, 2MiB maximum and configured content limits. Modules: moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Omitted modules survive. Trust, live challenges/jobs, entitlements, roles and active bans are never imported.
    /privacy policy/data/delete works only in yer own private peer, with own-data continuation and minimal active security retention. This is not a verified Rose full-export adapter.
gg-help-family-discovery =
    <b>Discovery</b> · /help lists families; /help command searches actual commands and aliases; /help family 2 continues. /button is the content markup helper. Each guide states context, rights, defaults and deployment limits. /settings opens the current group's personal panel.
gg-data-error-cache_pending = Yer optional database data be removed; cache clearing be queued until the cache returns. Active security records stay.
