## Bot Factory — English.
fac-home =
    🏭 Hi <b>{ $name }</b>! Welcome to the <b>Bot Factory</b>.

    Launch <b>your own Telegram bot</b> in one minute — no code, no server, free:
    📩 anonymous inbox · 💬 contact / support bot · 🛡 group guard · 🧩 menu & info bot

    Your bots: <b>{ $count }</b> / { $limit }
fac-btn-new = 🤖 Create a bot
fac-btn-mine = 📂 My bots ({ $count })
fac-btn-gallery = 🌟 Gallery
fac-btn-botfather = 🧑‍🔧 Open @BotFather
fac-btn-open = 🚀 Open @{ $username }
fac-btn-manage = ⚙️ Manage
fac-btn-pause = ⏸ Pause
fac-btn-resume = ▶️ Resume
fac-btn-token = 🔑 New token
fac-btn-public = 🌟 In gallery: { $state }
fac-btn-brand = 🏷 Credit line: { $state }
fac-btn-refresh = 🔄 Refresh
fac-btn-delete = 🗑 Delete
fac-btn-delete-ok = 🗑 Yes, delete the bot and all its data
fac-btn-admin-tab = 🏭 Factory
fac-choose = 🤖 <b>What should your bot do?</b>
fac-tpl-anonymous = Anonymous inbox
fac-tpl-anonymous-desc = People message you anonymously through your bot; you reply in one tap.
fac-tpl-anonymous-guide = Share your bot's link in your bio or story — people can now write to you anonymously.
fac-tpl-feedback = Contact / support bot
fac-tpl-feedback-desc = Customers write to the bot, you answer by replying. Works for a whole team in a group.
fac-tpl-feedback-guide = Open your bot and send /start. Messages from customers arrive there — reply to answer. /admin for settings.
fac-tpl-groupguard = Group guard
fac-tpl-groupguard-desc = Captcha, anti-spam, anti-flood, warnings, welcomes, notes — your own branded group manager.
fac-tpl-groupguard-guide = Add your bot to your group as admin, then send /settings in the group.
fac-tpl-custom = Menu & info bot
fac-tpl-custom-desc = Build pages, buttons, links and commands — menus, FAQs, price lists, portfolios. No code.
fac-tpl-custom-guide = Open your bot and send /build to design your pages. Changes are live instantly.
fac-steps =
    { $template } — great choice! Now:

    1. Open @BotFather and send <code>/newbot</code>
    2. Pick a name and a username ending in “bot”
    3. Copy the <b>token</b> BotFather gives you and send it here

    🔒 I delete your message right away and store the token encrypted.
fac-creating = ⏳ Setting up your bot…
fac-created =
    🎉 <b>@{ $username } is live!</b> ({ $template })

    { $guide }
fac-err-template = ⚠️ Unknown template.
fac-err-token_format = ⚠️ That doesn't look like a bot token. It looks like <code>123456789:AA…</code> — copy it from @BotFather.
fac-err-token_invalid = ⚠️ Telegram says this token is invalid or was revoked. Get a fresh one from @BotFather.
fac-err-telegram = ⚠️ Telegram didn't answer. Please try again in a moment.
fac-err-platform_bot = ⚠️ This bot already runs on this platform.
fac-err-taken = ⚠️ This bot is already connected by someone else.
fac-err-revoked = ⛔ This bot was blocked by the moderators.
fac-err-limit = 📦 You've reached your limit of { $limit } bots. Get 💎 VIP or invite friends for more slots.
fac-err-webhook = ⚠️ Telegram refused to connect the bot. Please try again later.
fac-err-token_other_bot = ⚠️ That token belongs to a different bot.
fac-mine = 📂 <b>Your bots</b> ({ $count })
fac-mine-empty = 📂 You have no bots yet. Create one in a minute!
fac-not-found = Bot not found.
fac-manage =
    🤖 <b>@{ $username }</b>
    { $template }

    • Status: { $status }
    • Users: <b>{ $users }</b>
    • Visitors who came to the factory from it: <b>{ $visits }</b>
    • Created: { $created }

    Open the bot and send /admin for its settings, stats and broadcasts.
fac-status-active = running
fac-status-paused = paused
fac-status-error = error
fac-status-revoked = blocked
fac-last-error = ⚠️ Last error: { $error }
fac-brand-vip = 💎 Removing the “Made with” line is a VIP feature.
fac-rotate = 🔑 Send the new token of @{ $username } (in @BotFather: /revoke, then copy the new token).
fac-rotated = ✅ Token updated.
fac-confirm-delete = 🗑 Delete @{ $username }? Its users, settings and content are removed for good. (The bot itself stays yours in @BotFather.)
fac-deleted = 🗑 @{ $username } was deleted.
fac-disabled = 🔧 Creating bots is temporarily unavailable. Please try again later.
fac-gallery = 🌟 <b>Gallery</b> — popular bots made here
fac-gallery-empty = No public bots yet. Make yours public from its ⚙️ Manage screen!
fac-adm = 🏭 <b>Factory</b> — bots by template and status
fac-adm-btn-search = 🔍 Find a bot
fac-adm-search = 🔍 Send a @username, bot id or owner id.
fac-adm-btn-revoke = ⛔ Revoke @{ $username }
fac-adm-confirm = ⛔ Revoke @{ $username }? It stops immediately and its token is erased.
fac-adm-revoked = ⛔ @{ $username } revoked.
vip-perks =
    ✅ Up to { $vip_bots } bots (free: { $free_bots })
    ✅ Remove the “Made with” credit line from your bots
    ✅ Priority support
vip-status-none = ⚪ Free plan: { $free_bots } bot(s).
cmd-newbot = Create a bot
cmd-mybots = Your bots
cmd-top = Gallery of bots
