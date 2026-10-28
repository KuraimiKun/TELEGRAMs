## SocialDownload — English (source locale)
## Rules for translators:
##  - Keep every key and every { $variable } unchanged.
##  - Keep HTML tags (<b>, <i>, <code>, <a>) and emojis.
##  - Continuation lines must be indented with 4 spaces.

## ---------- Start / general ----------
start-welcome =
    👋 Hi, <b>{ $name }</b>!

    I download <b>videos, photos and music</b> from TikTok, Instagram, YouTube, X (Twitter), Facebook, Pinterest, Reddit, Threads, SoundCloud and 1800+ other sites.

    📎 <b>Just send me a link!</b>
    🔎 Or send any text to search YouTube.
start-referred = 🤝 You joined via an invitation from a friend. Welcome!

btn-help = ❓ Help
btn-lang = 🌍 Language
btn-vip = 💎 VIP
btn-profile = 👤 Profile
btn-settings = ⚙️ Settings
btn-add-group = ➕ Add to group
btn-referral = 🎁 Free VIP
btn-back = ⬅️ Back
btn-cancel = ✖️ Cancel
btn-close = ✖️ Close

help-text =
    ❓ <b>How to use</b>

    1️⃣ Copy a link from TikTok, Instagram, YouTube, X, Facebook, Pinterest, Reddit, SoundCloud…
    2️⃣ Send it to me.
    3️⃣ Get your file — no watermark, best quality.

    <b>Commands</b>
    /start — main menu
    /search — search YouTube videos
    /music — search and download music
    /profile — your stats and plan
    /settings — default quality, audio format, captions
    /vip — VIP plans
    /referral — invite friends, get free VIP
    /lang — change language
    /terms — terms of use
    /support — contact support

    💡 <b>Tips</b>
    • Use me inline in any chat: type <code>@{ $bot } link</code>
    • Add me to a group and I'll download links posted there.
    • Already downloaded links are delivered instantly.

terms-text =
    📜 <b>Terms of use</b>

    • This bot is a tool for downloading publicly available media for personal use.
    • You are responsible for respecting copyright and the terms of the platforms you download from.
    • Do not use the bot to download or distribute illegal content.
    • Abuse (spam, automation) leads to a permanent ban.
    • VIP purchases are digital goods and are delivered instantly.

support-text = 💬 Support: { $contact }
support-none = 💬 Support is not configured yet.

lang-choose = 🌍 Choose your language:
lang-changed = ✅ Language changed to English.

## ---------- Generic states ----------
throttled = 🐢 Slow down! Please wait a few seconds.
banned = 🚫 You are banned from using this bot.
maintenance = 🛠 The bot is under maintenance. Please try again a bit later.
expired-menu = ⌛ This menu has expired. Please send the link again.
unknown = Unknown
state-on = ✅ On
state-off = ❌ Off
saved = ✅ Saved

## ---------- Download flow ----------
dl-analyzing = 🔎 Analyzing link…
dl-choose-format =
    🎬 <b>{ $title }</b>
    👤 { $uploader }  ⏱ { $duration }

    Choose a format:
btn-best = ⭐ Best quality
btn-audio = 🎵 Audio ({ $format })
dl-queued = ⏳ In queue… position: <b>{ $position }</b>
dl-starting = ⚙️ Starting download…
dl-downloading =
    ⬇️ <b>Downloading…</b> { $percent }%
    { $bar }
    { $done } / { $total } • { $speed }/s • ⏱ { $eta }
dl-downloading-simple = ⬇️ <b>Downloading…</b> { $done } • { $speed }/s
dl-processing = 🛠 Processing…
dl-uploading = 📤 Uploading to Telegram…
dl-cancelled = ❌ Download cancelled.
dl-cancel-too-late = This download has already finished.
dl-direct-link =
    📦 This file is too large for Telegram ({ $size }).

    🔗 Download link (valid for { $minutes } min):
    { $link }
dl-caption-via = 📥 via @{ $bot }
dl-limit-reached =
    🚫 You've reached your daily limit of <b>{ $limit }</b> downloads.

    ⏰ Resets in { $hours }h { $minutes }m.
    💎 Get VIP for unlimited downloads!
dl-too-many-active = ⏳ You already have { $count } active download(s). Please wait for them to finish.
dl-platform-disabled = ⚠️ Downloads from this platform are temporarily disabled.
dl-quality-locked = 🔒 { $quality } is available for VIP users only. Tap 💎 VIP to upgrade.
dl-no-url = 🤔 Send me a link to download, or any text to search YouTube.
dl-playlist =
    📃 Playlist: <b>{ $title }</b>
    Items: { $count }

    Your plan allows up to { $max } items. What should I download?
btn-pl-video = 🎬 First { $n } as video
btn-pl-audio = 🎵 First { $n } as audio

## ---------- Errors ----------
error-private = 🔒 This content is private or only available to followers.
error-login = 🔐 This platform requires login for this content. Please try again later.
error-geo = 🌍 This content is not available in the server's region.
error-live = 🔴 Live streams can't be downloaded. Try again after the stream ends.
error-too_large = 📦 This file is too large for your plan. 💎 VIP allows bigger files.
error-too_long = ⏱ This video is too long for your plan. 💎 VIP allows longer videos.
error-rate_limited = 🚦 The platform is limiting requests right now. Please try again in a minute.
error-removed = 🗑 This content was removed or the link is invalid.
error-no_media = 🤷 I couldn't find any downloadable media at this link.
error-unsupported = ❔ This link is not supported.
error-timeout = ⌛ The download timed out. Please try again.
error-upload = 📤 Telegram rejected the upload. Please try another quality.
error-unknown = 😕 Something went wrong. Please try again later.
error-busy = 🧯 The server is busy right now. Please try again in a few minutes.
error-queue_expired = ⌛ Your request waited too long in the queue and was cancelled. Please send the link again.
not-your-menu = 🙅 This menu belongs to someone else.

## ---------- Force subscription ----------
fsub-required = 📢 To use the bot, please join our channel(s) first, then tap «I've joined».
btn-fsub-join = ➕ Join { $title }
btn-fsub-check = ✅ I've joined
fsub-not-yet = ❌ You haven't joined all channels yet.
fsub-ok = ✅ Thank you! Processing your link…
fsub-ok-nolink = ✅ Thank you! Now send me a link.

## ---------- Search ----------
search-searching = 🔎 Searching…
search-results = 🔎 Results for <b>{ $query }</b>:
search-empty = 😕 Nothing found. Try another query.
search-usage = 🔎 Usage: <code>/search query</code>
music-usage = 🎵 Usage: <code>/music song name</code>
search-disabled = 🔎 Search is currently disabled.

## ---------- Profile ----------
profile-text =
    👤 <b>Your profile</b>

    🆔 ID: <code>{ $id }</code>
    💎 Plan: { $plan }
    📊 Today: { $used } / { $limit }
    📥 Total downloads: { $total }
    👥 Invited friends: { $refs }
    🌍 Language: { $lang }
plan-free = Free
plan-vip = VIP ⭐ (until { $until })
limit-unlimited = ∞

## ---------- Settings ----------
settings-text =
    ⚙️ <b>Settings</b>

    🎚 Default quality: <b>{ $quality }</b>
    🎵 Audio format: <b>{ $audio }</b>
    📝 Captions: <b>{ $caption }</b>
btn-set-quality = 🎚 Quality
btn-set-audio = 🎵 Audio format
btn-set-caption = 📝 Captions
settings-choose-quality = 🎚 Choose the default quality for new links:
q-auto = Auto
q-ask = Always ask
q-best = Best
q-audio = Audio only

## ---------- VIP ----------
vip-perks =
    ✅ Up to { $limit } downloads per day
    ✅ Quality up to { $height }p
    ✅ Files up to { $size }
    ✅ Priority queue — no waiting
    ✅ { $concurrent } downloads at the same time
    ✅ Playlists up to { $playlist } items
    ✅ No ads and no forced subscription
vip-status-active = 🟢 Your VIP is active until <b>{ $until }</b>.
vip-status-none = ⚪ You are on the free plan ({ $free_limit } downloads/day, up to { $free_height }p).
vip-invoice-title = VIP — { $name }
vip-invoice-desc = { $days } days of VIP: more downloads, max quality, priority queue, no ads.
vip-activated = 🎉 Thank you! Your VIP is active until <b>{ $until }</b>.
vip-expiring = ⏰ Your VIP expires in { $days } day(s). Renew now with /vip to keep your benefits!
vip-expired = ⌛ Your VIP has expired. You can renew any time with /vip.
vip-granted = 🎁 You received <b>{ $days }</b> days of VIP! Active until <b>{ $until }</b>.
vip-revoked = ℹ️ Your VIP has been removed.
vip-refunded = ↩️ Your payment was refunded and VIP was adjusted.
vip-no-plans = No plans are available right now.
vip-plan-days = { $days } days

## ---------- Referrals ----------
referral-text =
    🎁 <b>Invite friends — get VIP for free!</b>

    For every <b>{ $required }</b> friends who join and download something, you get <b>{ $days }</b> days of VIP.

    👥 Qualified friends: <b>{ $count }</b>
    🎯 Next reward in: <b>{ $left }</b>

    🔗 Your personal link:
    <code>{ $link }</code>
referral-reward = 🎉 { $required } of your friends joined! You received <b>{ $days }</b> days of VIP.
referral-disabled = 🎁 The referral program is currently disabled.
btn-share = 📤 Share link
referral-share-text = 📥 Download videos from TikTok, Instagram, YouTube and more — free and without watermark!

## ---------- Groups ----------
group-welcome =
    👋 Thanks for adding me!
    Send any supported link in this chat and I'll download it.
    Admins can use /settings to configure me.
group-settings =
    ⚙️ <b>Group settings</b>

    Auto-download links: { $state }
btn-group-toggle = 🔁 Toggle auto-download
group-admin-only = ⛔ Only group admins can do this.
group-disabled = ⚠️ Group mode is currently disabled.

## ---------- Inline ----------
inline-hint = Paste a link after my username
inline-hint-desc = TikTok, Instagram, YouTube, X…
inline-download = 📥 Download from { $platform }
inline-download-desc = Tap to download and send here
inline-processing = ⏳ Downloading… please wait
inline-open-bot = 🤖 Open the bot
inline-failed = 😕 Failed to download this link.
inline-hint-message = 👉 Open @{ $bot } and send any video or music link to download it!
inline-sent = ✅ Sent to your private chat with @{ $bot }.
cmd-search = Search YouTube videos
cmd-music = Search and download music

## ---------- Admin: downloads ----------
sd-btn-admin-tab = 🧰 Downloads
sd-adm-home =
    🧰 <b>Downloads</b>

    ⏳ Waiting: <b>{ $high }</b> VIP · <b>{ $normal }</b> free
    ⚙️ Running: <b>{ $running }</b>
    ☠️ Dead-lettered: <b>{ $dead }</b>
    🌐 Proxies: <b>{ $proxies }</b> · 🍪 Cookie files: <b>{ $cookies }</b>
sd-btn-dead = ☠️ Dead letters
sd-btn-proxies = 🌐 Proxies
sd-btn-cookies = 🍪 Cookies
sd-btn-purge = 🧹 Purge dead letters
sd-adm-dead = ☠️ <b>Dead-lettered jobs</b> (crashed too many times; already refunded)
sd-adm-proxies = 🌐 <b>Proxies</b> ({ $count }) — tap one to remove it. ⚠️ = recent failures.
sd-btn-proxy-add = ➕ Add proxy
sd-btn-proxy-reset = ♻️ Reset failure counters
sd-adm-proxy-prompt = ➕ Send a proxy URL, e.g. <code>socks5://user:pass@host:1080</code> or <code>http://host:3128</code>
sd-adm-proxy-invalid = ❌ Not a valid proxy URL (http, https, socks5, socks5h), or it already exists.
sd-adm-proxy-readonly = ℹ️ Proxies from SOCIALDOWNLOAD_PROXIES can only be changed in the environment.
sd-adm-cookies = 🍪 <b>Cookie files</b> ({ $count }) — tap one to delete it.

    To add one, send a Netscape <code>cookies.txt</code> document with the platform as caption: { $platforms }
sd-adm-cookie-saved = ✅ Cookies for <b>{ $platform }</b> saved as <code>{ $name }</code>.
sd-adm-cookie-invalid = ❌ Rejected: { $error }
sd-ytdlp-update = ⬆️ A new yt-dlp version is available: <b>{ $latest }</b> (running { $current }). Rebuild the worker image to update — outdated yt-dlp is the #1 cause of broken downloads.
