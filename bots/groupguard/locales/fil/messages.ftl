## Independently authored Group Guard fil content.
group-welcome = 🛡 Salamat sa pagdagdag! Bigyan ako ng karapatang tagapangasiwa para magbura ng mensahe, maghigpit sa kasapi at mag-pin. Iayos sa /settings.
gg-start = 🛡 Kumusta <b>{ $name }</b>! Ako ang <b>Group Guard</b>: pagpapatunay ng bagong kasapi, proteksiyon sa pagbaha ng mensahe at CAS, pagpigil sa nilalaman, pamamahala, tala, pansala, tuntunin at pagbati. Idagdag akong tagapangasiwa at gamitin ang /settings o /help.
gg-help = 📖 /help nagpapakita ng mga seksiyon; /help utos naghahanap ng utos. Pamamahala: /ban /mute /kick /warn. Nilalaman: /save /filter /rules. Proteksiyon: /lock /blocklist /night. /settings nagbubukas ng personal na panel ng grupo.
gg-welcome-default = 👋 Maligayang pagdating { "{" }mention{ "}" } sa <b>{ "{" }group{ "}" }</b>!
gg-credit = 🛡 Pinoprotektahan ni @{ $bot }
gg-btn-add = ➕ Idagdag sa grupo
gg-btn-commands = 📖 Mga utos
gg-btn-rules = 📜 Mga tuntunin
gg-btn-human = ✅ Tao ako
gg-btn-unwarn = ↩️ Alisin ang babala (tagapangasiwa)
gg-btn-locks = 🔒 Mga pagpigil sa nilalaman · bilang: { $count }
gg-btn-open-settings = ⚙️ Buksan ang mga ayos
gg-btn-admin-tab = 🛡 Mga grupo
gg-captcha = 🤖 Patunayang tao ka bago matapos ang ipinakitang panahon, kung hindi ay aalisin ka.
    mga minuto: { $minutes }
    kasapi: { $user }
gg-captcha-button = Pindutin ang buton sa ibaba 👇
gg-captcha-math = Ano ang <b>{ $a } + { $b }</b>?
gg-captcha-not-you = Para sa ibang tao ang butong ito.
gg-captcha-ok = ✅ Maligayang pagdating!
gg-captcha-wrong = ❌ Maling sagot. Subukan muli kung may natitirang pagtatangka.
    natitirang pagtatangka: { $left }
gg-captcha-failed = ❌ Napakaraming maling sagot.
gg-captcha-passed = ✅ Matagumpay ang pagpapatunay. Maligayang pagdating!
    kasapi: { $user }
gg-cas-banned = 🚫 Kilala ng CAS ang kasapi bilang nagpapadala ng spam; ipinagbawal ang pagpasok.
    kasapi: { $user }
gg-join-request = 👋 Patunayang tao ka upang sumali sa grupo:
    grupo: { $group }
gg-join-approved = ✅ Naaprubahan ang kahilingan. Maligayang pagdating!
gg-join-expired = ⌛ Nag-expire ang kahilingan. Magpadala ng bagong kahilingan sa pagsali.
gg-goodbye = 👋 Umalis ang kasapi sa grupo.
    kasapi: { $user }
gg-flood-mute = 🌊 Pansamantalang pinatahimik ang kasapi dahil sa sobrang mensahe.
    kasapi: { $user }
gg-flood-kick = 🌊 Inalis ang kasapi dahil sa sobrang mensahe.
    kasapi: { $user }
gg-flood-ban = 🌊 Ipinagbawal ang kasapi dahil sa sobrang mensahe.
    kasapi: { $user }
gg-newbie-links = 🆕 Hindi puwedeng magpadala ng link ang bagong kasapi sa ipinakitang unang mga oras.
    mga oras: { $hours }
    kasapi: { $user }
gg-spam-banned = 🧠 Ipinagbawal ang kasapi dahil sa spam.
    kasapi: { $user }
gg-reason-blocklist = ipinagbabawal na salita
gg-need-right = ⛔ Kailangan ang naaangkop na karapatang tagapangasiwa.
    karapatan: { $right }
gg-right-admin = tagapangasiwa
gg-right-restrict = paghihigpit sa kasapi
gg-right-delete = pagbura ng mensahe
gg-right-pin = pag-pin ng mensahe
gg-right-change_info = pagbago ng impormasyon ng grupo
gg-admins-only = ⛔ Para lamang sa tagapangasiwa.
gg-need-target = 👤 Tumugon sa mensahe o magbigay ng ID o kasalukuyang napatunayang @pangalan ng gumagamit.
gg-target-admin = 🙅 Hindi maaaring tamaan ng aksiyong ito ang tagapangasiwa.
gg-bot-no-rights = ⚠️ Kailangan kong maging tagapangasiwa na may kinakailangang karapatan.
gg-banned = 🔨 Ipinagbawal ang kasapi.
    dahilan: { $reason }
    kasapi: { $user }
gg-banned-for = 🔨 Ipinagbawal ang kasapi sa ipinakitang panahon.
    dahilan: { $reason }
    oras: { $time }
    kasapi: { $user }
gg-unbanned = ✅ Inalis ang pagbabawal sa kasapi.
    kasapi: { $user }
gg-kicked = 👢 Inalis ang kasapi at puwedeng sumali muli.
    dahilan: { $reason }
    kasapi: { $user }
gg-muted = 🔇 Pinatahimik ang kasapi.
    dahilan: { $reason }
    kasapi: { $user }
gg-muted-for = 🔇 Pinatahimik ang kasapi sa ipinakitang panahon.
    dahilan: { $reason }
    oras: { $time }
    kasapi: { $user }
gg-unmuted = 🔊 Puwedeng magsulat muli ang kasapi.
    kasapi: { $user }
gg-warned = ⚠️ Naitala ang babala ng kasapi.
    bilang: { $count }
    hangganan: { $limit }
    dahilan: { $reason }
    kasapi: { $user }
gg-warn-limit-ban = 🔨 Naabot ang hangganan ng babala; ipinagbawal ang kasapi.
    hangganan: { $limit }
    kasapi: { $user }
gg-warn-limit-mute = 🔇 Naabot ang hangganan ng babala; pinatahimik ang kasapi.
    hangganan: { $limit }
    kasapi: { $user }
gg-warn-limit-kick = 👢 Naabot ang hangganan ng babala; inalis ang kasapi.
    hangganan: { $limit }
    kasapi: { $user }
gg-unwarned = ↩️ Inalis ang isang babala ng kasapi.
    bilang: { $count }
    hangganan: { $limit }
    kasapi: { $user }
gg-warn-removed = ↩️ Inalis ng tagapangasiwa ang babala.
    tagapangasiwa: { $admin }
gg-warns = ⚠️ Mga babala ng kasapi:
    bilang: { $count }
    hangganan: { $limit }
    kasapi: { $user }
gg-warns-reset = 🧽 Ni-reset ang mga babala ng kasapi.
    kasapi: { $user }
gg-purge-reply = 🧹 Tumugon sa unang mensaheng buburahin.
gg-purged = 🧹 Nabura ang mga mensahe.
    bilang: { $count }
gg-pin-reply = 📌 Tumugon sa mensaheng ipa-pin.
gg-report-reply = 🚨 Tumugon sa mensaheng iuulat.
gg-reported = 🚨 Naiulat ang kasapi sa mga tagapangasiwa.
    kasapi: { $user }
gg-setlog-usage = 📒 Idagdag akong tagapangasiwa sa channel ng talaan at gamitin ang <code>/setlog -100…</code> kasama ang ID nito.
gg-setlog-failed = ⚠️ Hindi ako makapagsulat doon. Idagdag muna akong tagapangasiwa.
gg-setlog-done = 📒 Nakakonekta ang channel ng talaan.
gg-setlog-off = 📒 Nadiskonekta ang channel ng talaan.
gg-log-connected = 📒 Tumatanggap ang usapang ito ng talaan ng pamamahala ng grupo.
    grupo: { $group }
gg-log-flood = 🌊 Natukoy ang sobrang mensahe:
    aksiyon: { $action }
    kasapi: { $user }
gg-log-report = 🚨 Ulat tungkol sa kasapi:
    kasapi: { $user }
gg-log-spam = 🧠 Pagbabawal dahil sa spam na natukoy ng AI:
    teksto: { $text }
    kasapi: { $user }
gg-rules = 📜 <b>Mga tuntunin</b>
    { $rules }
gg-no-rules = 📜 Wala pang tuntunin. Maaaring gumamit ang tagapangasiwa ng /setrules teksto.
gg-rules-saved = 📜 Nai-save ang mga tuntunin.
gg-rules-cleared = 📜 Nabura ang mga tuntunin.
gg-welcome-usage = 👋 Gamitin ang <code>/setwelcome Kumusta {"{"}mention{"}"}, maligayang pagdating sa {"{"}group{"}"}!</code> o tumugon sa mensahe.
gg-welcome-saved = 👋 Nai-save ang pagbati.
gg-welcome-reset = 👋 Naibalik ang karaniwang pagbati.
gg-note-usage = 📝 <code>/save pangalan teksto</code> o tumugon gamit ang <code>/save pangalan</code>.
gg-filter-usage = 🔁 <code>/filter salita tugon</code> o tumugon gamit ang <code>/filter salita</code>.
gg-note-saved = 📝 Nai-save ang tala. Kunin sa <code>#{ $key }</code>, ayon sa karapatan.
gg-filter-saved = 🔁 Tutugon ako kapag tumugma ang “{ $key }”.
gg-notes-empty = 📝 Wala pang tala.
gg-filters-empty = 🔁 Wala pang pansala.
gg-notes-list = 📝 <b>Mga tala</b>
gg-filters-list = 🔁 <b>Mga pansala</b>
gg-item-deleted = 🗑 Nabura ang tala.
    susi: { $key }
gg-item-missing = 🤷 Walang nilalamang naka-save sa pangalang ito.
gg-items-limit = 📦 Naabot ang hangganan ng tala at pansala ng grupo.
gg-lock-usage = 🔒 Gamitin ang <code>/lock links</code>. Mga uri sa ibaba; pinipili ng <code>all</code> ang lahat.
    mga uri: { $types }
gg-locked = 🔒 Ipinagbabawal na nilalaman:
    mga uri: { $types }
gg-unlocked = 🔓 Pinapayagang nilalaman:
    mga uri: { $types }
gg-locks-title = 🔒 <b>Mga pagpigil sa nilalaman</b>
gg-locks-panel = 🔒 <b>Mga pagpigil</b>: binubura ang ipinagbabawal na nilalaman; hindi saklaw ang tagapangasiwa.
gg-lock-links = mga link
gg-lock-invites = mga link ng imbitasyon
gg-lock-forwards = mga ipinasa
gg-lock-media = media
gg-lock-stickers = mga sticker
gg-lock-gifs = GIF
gg-lock-voice = mensaheng boses
gg-lock-polls = mga botohan
gg-lock-bots = mga bot
gg-blocklist = 🚫 <b>Mga ipinagbabawal na salita</b>
    mga salita: { $words }
gg-blocklist-empty = 🚫 Walang ipinagbabawal na salita.
gg-blocklist-usage = 🚫 <code>/addblock salita, ibang parirala</code> · <code>/rmblock salita</code>
gg-blocklist-saved = 🚫 Na-update ang listahan ng pagbabawal.
    bilang: { $count }
gg-night-usage = 🌙 <code>/night 23 7 +3</code> nagsasara mula23:00 hanggang07:00 UTC+3; <code>/night off</code> nagpapahinto.
gg-night-on = 🌙 Naitakda ang oras ng gabi ng grupo.
    wakas: { $end }
    simula: { $start }
    sona ng oras: { $tz }
gg-night-off = 🌙 Pinatay ang paraan sa gabi.
gg-night-start = 🌙 Magandang gabi! Sarado ang grupo hanggang sa ipinakitang oras.
    wakas: { $end }
gg-night-end = ☀️ Magandang umaga! Bukas muli ang grupo.
gg-panel = ⚙️ <b>Mga ayos ng grupo</b>
    Pindutin ang opsiyon para baguhin. Itakda ang oras ng gabi sa /night.
    grupo: { $group }
    oras ng gabi: { $night }
gg-panel-sent = 📬 Naipadala ang mga ayos sa pribado.
gg-panel-start-first = 📬 Buksan muna ang pribadong usapan sa akin, pagkatapos ay pindutin sa ibaba.
gg-credit-vip = 💎 Kailangan ng VIP para itago ang linyang pang-proteksiyon. Gamitin ang /vip sa pribado.
gg-opt-wel = 👋 Mga pagbati · halaga: { $value }
gg-opt-cln = 🧹 Burahin ang mensahe ng pagsali · halaga: { $value }
gg-opt-bye = 👋 Pamamaalam · halaga: { $value }
gg-opt-cap = 🤖 Pagpapatunay · halaga: { $value }
gg-opt-cpm = ⏱ Panahon ng pagpapatunay, minuto · halaga: { $value }
gg-opt-fld = 🌊 Hangganan ng mensahe · halaga: { $value }
gg-opt-fla = 🌊 Aksiyon sa sobrang mensahe · halaga: { $value }
gg-opt-wrn = ⚠️ Hangganan ng babala · halaga: { $value }
gg-opt-wra = ⚠️ Aksiyon sa babala · halaga: { $value }
gg-opt-act = ⏳ Awtomatikong paghihigpit, minuto · halaga: { $value }
gg-opt-cas = 🛡 Proteksiyon ng CAS · halaga: { $value }
gg-opt-nwb = 🆕 Bagong kasapi walang link, oras · halaga: { $value }
gg-opt-ais = 🧠 Proteksiyon sa spam ng AI · halaga: { $value }
gg-opt-ngt = 🌙 Paraan sa gabi · halaga: { $value }
gg-opt-crd = 🏷 Linya ng proteksiyon · halaga: { $value }
gg-opt-lang = 🌐 Wika · halaga: { $value }
gg-val-button = Buton
gg-val-math = Pagkuwenta
gg-val-off = nakapatay
gg-val-mute = patahimikin
gg-val-kick = alisin
gg-val-ban = ipagbawal
gg-adm = 🛡 <b>Group Guard: estadistika</b>
    mga grupo: { $groups }
    mga tala: { $items }
    mga babala: { $warns }
cmd-settings = Mga ayos ng grupo
cmd-help = Gabay sa mga utos
gg-auth-denied = Hindi mapatunayan ang pahintulot. Walang binago.
gg-target-invalid = Pumili ng kilalang taong kasapi. Hindi mapatunayan ang target.
gg-duration-invalid = Gumamit ng tagal na60s–365d. Kailangan ng tagal ang pansamantalang utos.
gg-reason-invalid = Hanggang256 karakter ang dahilan.
gg-outcome-failed = Nabigo o hindi pinahintulutan ang aksiyon.
gg-outcome-partial = Bahagyang natapos ang aksiyon. Maaaring manatili ang pagbabawal kapag nabigo ang pagpapanumbalik pagkatapos alisin.
gg-outcome-ancillary = Natapos ang pangunahing aksiyon, ngunit nabigo ang dagdag na hakbang.
gg-review-request = Suriin ang hindi mababagong aksiyon sa ibaba. Maaaring aprubahan ng taong may kasalukuyang pahintulot sa loob ng120 segundo. Ang tagal ay nasa segundo.
    mga detalye: { $details }
    tagal: { $duration }
    operasyon: { $operation }
    target: { $target }
gg-review-approve = Aprubahan ang aksiyong ito
gg-review-unavailable = Hindi magagamit ang imbakan ng kumpirmasyon. Magpadala ng bagong utos.
gg-review-expired = Nag-expire, hindi balido o nagamit na ang kumpirmasyon.
gg-review-consumed = Nagamit ang kumpirmasyon. Suriin ang resulta; kailangan ng bagong utos para umulit.
gg-duration-permanent = Permanente / walang takdang panahon
gg-purge-ack = Kinumpirma ng API ang mga kahilingan sa pagbura. Hindi alam ang tunay na bilang ng nabura.
    kinilala ng API: { $acknowledged }
    hiniling: { $requested }
gg-warning-removed = Inalis ang babala.
gg-op-ban = ipagbawal
gg-op-mute = patahimikin
gg-op-kick = alisin
gg-op-unban = alisin ang pagbabawal
gg-op-unmute = alisin ang pagpatahimik
gg-op-warn = magbabala
gg-op-unwarn = alisin ang babala
gg-op-resetwarns = i-reset ang babala
gg-op-purge = burahin ang hanay ng mensahe
gg-op-delete = burahin ang mensahe
gg-op-pin = i-pin ang mensahe
gg-op-unpin = alisin ang pin
gg-op-setlog = itakda ang talaan
gg-op-unsetlog = alisin ang talaan
gg-op-config = baguhin ang mga ayos
gg-op-save = i-save ang nilalaman
gg-op-remove = alisin ang nilalaman
gg-op-panel = buksan ang panel
gg-review-details-above = Nasa mensaheng kaagad sa itaas ang buong hiniling na nilalaman.
gg-warn-pending = Nai-save ang babala; pinoproseso na ang aksiyon sa hangganan.
gg-done = Tapos na.
gg-setting-saved = Nai-save ang ayos.
    ayos: { $setting }
gg-setting-value = Kasalukuyang halaga ng ayos:
    ayos: { $setting }
    halaga: { $value }
gg-setting-invalid = Hindi balidong ayos. Gumamit ng on/off, wastong paraan o tagal gaya ng10m.
gg-warning-settings = Mga ayos ng babala:
    tagal: { $duration }
    pag-expire: { $expiry }
    hangganan: { $limit }
    paraan: { $mode }
gg-admin-changed = Natapos ang aksiyon ng tagapangasiwa.
    aksiyon: { $action }
    kasapi: { $user }
gg-admin-list = Mga pampublikong tagapangasiwa:
    { $admins }
gg-approved = Naaprubahan ang kasapi.
    dahilan: { $reason }
    kasapi: { $user }
gg-unapproved = Inalis ang mga pag-apruba.
    bilang: { $count }
gg-approval-status = Kalagayan ng pag-apruba ng kasapi:
    dahilan: { $reason }
    kalagayan: { $status }
    kasapi: { $user }
gg-approval-list = Mga aprubadong kasapi:
    { $approvals }
gg-next-page = Iba pang tala: { $command }
gg-range-invalid = Hindi balidong saklaw. Pumili ng kahit isang mensahe at huwag lumampas sa ipinakitang hangganan.
    hangganan: { $cap }
gg-range-start = Nai-save ang simula para sa iyo sa paksang ito sa loob ng sampung minuto. Tumugon sa huling mensahe gamit ang /purgeto.
gg-range-missing = Walang simula para sa iyo rito. Gamitin muna ang /purgefrom bilang tugon.
gg-content-needed = Magbigay ng nilalaman o tumugon dito; hanggang3500 karakter.
gg-log-status = Mga ayos ng talaan:
    mga kategorya: { $categories }
    destinasyon: { $destination }
gg-log-unverified = Wala akong napatunayang pagtanggap ng orihinal na utos mula sa channel. Ipadala muna ang /setlog sa channel.
gg-log-forward = Ipasa sa grupo ang orihinal na /setlog. Kailangan ng tagapangasiwang nagkokonekta ang karapatang magbago ng impormasyon sa dalawang usapan.
gg-info = Impormasyon ng gumagamit o usapan:
    ID: { $id }
    kasapian: { $membership }
    pangalan: { $name }
    pangalan ng gumagamit: { $username }
gg-op-unpinall = alisin ang lahat ng pin
gg-op-permapin = permanenteng pin
gg-op-promote = gawing tagapangasiwa
gg-op-demote = alisin sa tagapangasiwa
gg-op-approve_user = aprubahan ang gumagamit
gg-op-unapprove = alisin ang pag-apruba
gg-op-unapproveall = alisin lahat ng pag-apruba
gg-unknown = Hindi alam
gg-chat-id = ID ng usapan:
    ID: { $id }
gg-on = Nakabukas
gg-off = Nakapatay
gg-anon-enabled = Nakabukas ang pagtitiwala sa di-kilalang tagapangasiwa rito. Ginagamit ng di-kilalang utos ng grupong ito ang karapatan ng bot nang hindi kinikilala ang tao. Kailangan pa rin ng napatunayang lumikha ang aksiyon ng may-ari. Ibinabalik ng /anonadmin off ang pagsusuri ng tao.
gg-right-invite_users = pag-imbita ng gumagamit
gg-right-promote_members = pagtatalaga ng tagapangasiwa
gg-right-manage_topics = pamamahala ng paksa
gg-right-creator = lumikha ng grupo
gg-log-join = Sumali ang kasapi.
    kasapi: { $user }
gg-log-leave = Umalis ang kasapi.
    kasapi: { $user }
gg-warning-row = Tala ng babala:
    pag-expire: { $expiry }
    ID: { $id }
    dahilan: { $reason }
gg-menu-prompt = Pumili ng opsiyon.
gg-content-invalid = Hindi balido ang nilalaman o lumampas sa Telegram. Suriin ang pangalan, anyo, modifier at buton.
gg-content-unavailable = Hindi magagamit ang nilalaman o hindi pinapayagan ng kasalukuyang pagiging kasapi ang pag-access.
gg-btn-private-note = Buksan ang tala
gg-open-private = Buksan nang pribado ang nilalamang ito:
gg-items-cleared = Nabura ang mga tala.
    bilang: { $count }
gg-clearall-confirm = Kinukumpirma ng lumikha ng grupo sa <code>/{ $command } confirm</code>.
gg-button-usage = Gamitin ang <code>/button "Label" https://example.com</code>. Idagdag ang <code>"Tala" #pangalan same</code> para sa isa pang buton sa parehong hanay. Makakatanggap ng marka at gumaganang paunang tingin.
gg-btn-accept-rules = Tanggapin ang tuntunin
gg-btn-open-verification = Buksan ang pagpapatunay
gg-captcha-private = Buksan ang pribadong pagpapatunay upang kumpirmahin ang pagiging kasapi ng grupo.
    kasapi: { $user }
gg-captcha-choice = Piliin ang katugmang larawan gamit ang mga buton. Paraan at puwesto ng karakter sa ibaba.
    paraan: { $mode }
    posisyon: { $position }
gg-captcha-settings = Mga ayos ng pagpapatunay:
    nakabukas: { $enabled }
    pag-alis: { $kick }
    paraan: { $mode }
    pagpalaya: { $release }
    mga segundo: { $seconds }
gg-captcha-dependency = Buksan ang pagbati bago pagpapatunay. I-save ang tuntunin bago humingi ng pagtanggap.
gg-val-text = Larawan ng teksto
gg-val-text2 = Larawan ng karakter
gg-captcha-attempts-exhausted = Nabigo ang pagpapatunay matapos ang sobrang maling sagot; inilapat ang nakatakdang paghihigpit.
gg-captcha-admin-exempt = Tagapangasiwa ka na ng grupo. Natapos ang pagpapatunay.
gg-captcha-question-text = Piliin ang salitang nasa larawan.
gg-captcha-question-math = Sagutin ang kuwenta sa larawan at piliin ang sagot.
gg-captcha-question-text2 = Piliin ang ipinakitang karakter sa larawan, mula kaliwa pakanan.
    posisyon: { $position }
gg-locktypes = Mga magagamit na pagpigil sa nilalaman:
    mga uri: { $types }
gg-allowlist-title = Mga hindi saklaw ng pagpigil sa nilalaman
gg-allowlist-invalid = Hindi balidong eksepsiyon. Gumamit ng domain/path, eksaktong imbitasyon, @usapan o tiyak na pagkakakilanlan gaya ng stickerpack:pangalan.
gg-reason-lock = Ipinagbabawal na nilalaman:
    mga uri: { $types }
gg-lock-applied = Inilapat ang tuntunin ng pagpigil.
    dahilan: { $reason }
    mga uri: { $types }
gg-reaction-failed = Hindi mailapat ang tuntunin ng reaksiyon. Maaaring hindi suportado ng Bot API server na ito ang pagtanggal ng reaksiyon.
    code: { $code }
gg-reaction-anonymous = Walang ID ng gumagamit o nagpapadalang usapan ang di-kilalang bilang. Kailangan ito ng pagtanggal na API; hindi inaangking may tinanggal.
gg-none = Wala
gg-blocklist-title = Listahan ng pagbabawal
gg-blocklist-invalid = Hindi balidong trigger, dahilan o aksiyon. Suriin ang sipi, escape ng wildcard at kailangang tagal sa pansamantalang paraan.
gg-blocklist-settings = Mga ayos ng listahan ng pagbabawal:
    pagbura: { $delete }
    paraan: { $mode }
gg-blocklist-action = Inilapat ang tuntunin ng listahan ng pagbabawal sa kasapi.
    dahilan: { $reason }
    kasapi: { $user }
gg-lock-album = album
gg-lock-anonchannel = di-kilala o channel na nagpapadala
gg-lock-audio = audio
gg-lock-bot = mensaheng mula sa bot
gg-lock-button = mga buton
gg-lock-cashtag = mga tag ng salapi
gg-lock-checklist = mga checklist
gg-lock-cjk = tekstong Tsino/Hapones/Koreano
gg-lock-command = mga utos
gg-lock-comment = komento sa channel
gg-lock-contact = mga contact
gg-lock-cyrillic = mga karakter na Cyrillic
gg-lock-document = mga dokumento
gg-lock-email = email
gg-lock-emoji = emoji
gg-lock-emojicustom = pasadyang emoji
gg-lock-emojigame = mga laro ng emoji
gg-lock-emojionly = puro emoji
gg-lock-externalreply = panlabas na tugon
gg-lock-forward = mga ipinasa
gg-lock-forwarduser = ipinasang mensahe ng gumagamit
gg-lock-forwardbot = ipinasang mensahe ng bot
gg-lock-forwardchannel = ipinasang mensahe ng channel
gg-lock-forwardstory = ipinasang story
gg-lock-game = mga laro
gg-lock-gif = GIF
gg-lock-guestbot = bisitang bot
gg-lock-inline = inline na nilalaman
gg-lock-invitelink = link ng imbitasyon
gg-lock-botlink = link ng bot
gg-lock-location = mga lokasyon
gg-lock-outsidereaction = reaksiyon ng di-kasapi
gg-lock-phone = numero ng telepono
gg-lock-photo = mga larawan
gg-lock-poll = mga botohan
gg-lock-reaction = mga reaksiyon
gg-lock-rtl = tekstong kanan-pakaliwa
gg-lock-spoiler = nakatagong nilalaman
gg-lock-sticker = mga sticker
gg-lock-stickeranimated = animated na sticker
gg-lock-stickerpremium = premium na sticker
gg-lock-text = teksto
gg-lock-url = URL
gg-lock-video = mga video
gg-lock-videonote = mensaheng video
gg-flood-status = Sobrang mensahe: sunod-sunod na hangganan sa N; panahon na bintana higit N. Aksiyon, tagal at paglilinis ng hanay sa ibaba.
    burahin ang buong sunod-sunod: { $clear }
    sunod-sunod na hangganan: { $consecutive }
    bilang: { $count }
    tagal: { $duration }
    paraan: { $mode }
    mga segundo: { $seconds }
gg-raid-status = Proteksiyon sa maramihang pagsali. /antiraid on nagbubukas; /antiraid off humihinto. Panahon, tagal ng pagbabawal at awtomatikong hangganan bawat minuto sa ibaba.
    aktibo: { $active }
    awtomatikong hangganan: { $auto }
    tagal ng pagbabawal: { $ban }
    panahon: { $period }
    hanggang: { $until }
gg-raid-banned = 🛡 Pansamantalang ipinagbawal ang kasapi habang aktibo ang proteksiyon sa maramihang pagsali.
    kasapi: { $user }
gg-raid-declined = 🛡 Tinanggihan ang kahilingan habang aktibo ang proteksiyon sa maramihang pagsali.
    kasapi: { $user }
gg-silent-consent-required = Kailangang payagan ng lumikha ang tahimik na aksiyon at magtakda ng talaan bago piliin ang aksiyong ito.
gg-btn-enable-raid = Buksan ang proteksiyon sa maramihang pagsali
gg-human-required = Kailangan ng makikilalang tao ang aksiyong ito.
gg-group-message-required = Gamitin sa totoong mensahe o paksa ng grupo. Hindi ID ng grupong mensahe ang pribadong ID.
gg-connection-private = Gamitin ang utos ng koneksiyon sa pribadong usapan natin.
gg-connection-disconnected = Nadiskonekta. Nananatili ang huling limang grupo para makakonekta muli.
gg-connection-current = Nakakonekta ang grupo. Sinusuri ang pagiging kasapi at kasalukuyang karapatan sa bawat aksiyon.
    grupo: { $group }
gg-connection-none = Walang aktibong koneksiyon. Gamitin ang /connect GROUP_ID o /connect @grupo.
gg-connection-open = Buksan ang personal na koneksiyon sa pribadong usapan natin.
gg-btn-connect = Kumonekta nang pribado
gg-connection-history = Huling limang grupo mo. Pumili ng isa; kailangan ang kasalukuyang pagiging kasapi.
gg-connection-unavailable = Hindi magagamit ang koneksiyon. Kailangan kang maging kasalukuyang taong kasapi at tagapangasiwa ang bot doon.
gg-catalog-unresolved = /{ $command } ay pangalang nasa katalogo na walang tiyak na aksiyon. Gamitin ang /notes o /flood para sa naipatupad na gawa.
gg-cleanup-failed = Nabigo o hindi magagamit ang paglilinis ng mensahe; walang inaangking pagbura.
gg-op-lock_change = baguhin ang pagpigil
gg-op-allowlist_change = baguhin ang mga eksepsiyon
gg-op-allowlist_clear = burahin ang mga eksepsiyon
gg-op-blocklist_change = baguhin ang ipinagbabawal
gg-op-blocklist_clear = burahin ang ipinagbabawal
gg-op-raid_change = baguhin ang proteksiyon sa pagsali
gg-disabled-list = Patakaran ng utos: /disable PANGALAN at /enable PANGALAN sa pagpapatakbo; /disabledel sa pagbura; /disableadmin sa pagsaklaw ng tagapangasiwa.
    mga utos: { $commands }
gg-cleanup-types = Mga magagamit na kategorya ng paglilinis:
    mga uri: { $types }
gg-cleanup-selected = Mga napiling kategorya ng paglilinis:
    mga uri: { $types }
gg-advanced-status = Kailangan ng tahimik na awtomatika ang pahintulot ng lumikha at talaan. Kailangan ng bot ang normal na karapatan; karaniwang nakabukas ang pagsusuri ng pagbabago. Iayos ang pagkakita ng mga bot sa BotFather.
    ayos: { $setting }
    halaga: { $value }
gg-action-topic = Paksa ng aksiyon. /setactiontopic pumipili ng kasalukuyang paksa ng forum; ID1 ang pangkalahatang paksa.
    paksa: { $topic }
gg-topic-unavailable = Kailangan ang kasalukuyang forum at naaangkop na karapatang pamahalaan.
gg-topic-id-required = Tiyak na ibigay ang ID ng paksa sa nakakonektang pribadong usapan.
gg-topic-general-delete = Hindi mabubura ang pangkalahatang paksa. Kailangan ng kumpirmasyon ang makikilalang tao.
gg-topic-delete-confirm = Burahin ang paksa at mensahe? Balido ang personal na kumpirmasyon sa loob ng dalawang minuto.
    paksa: { $topic }
gg-btn-confirm-delete = Kumpirmahin ang pagbura
gg-topic-changed = Natapos ang aksiyon sa paksa.
    aksiyon: { $action }
    paksa: { $topic }
gg-op-policy_change = baguhin ang patakaran ng utos/paglilinis
gg-op-topic_create = gumawa ng paksa
gg-op-topic_rename = palitan ang pangalan ng paksa
gg-op-topic_close = isara ang paksa
gg-op-topic_reopen = buksan muli ang paksa
gg-op-topic_delete = burahin ang paksa at mensahe
gg-op-echo = ipadala ang naayos na nilalaman
gg-broadcast-owner = Tanging nakatakdang operator ng bot na ito o tunay na may-ari ng batang instance ang puwedeng magpadala sa mga grupo nito.
gg-broadcast-queued = Nakapila ang kampanya sa grupo. Magkahiwalay ang target at resulta bawat bot.
    ID: { $id }
gg-broadcast-busy = May ibang aktibong kampanya o hindi pa tapos ang limang minuto mula sa huling paglikha.
gg-broadcast-empty = Wala kang kampanya sa grupo sa bot na ito.
gg-broadcast-status = Kalagayan ng kampanya sa grupo:
    nakansela: { $cancelled }
    nabigo: { $failed }
    ID: { $id }
    nakapila: { $queued }
    naihatid: { $sent }
    kalagayan: { $status }
    di-tiyak na resulta: { $uncertain }
gg-fed-created = Nalikha ang pederasyon. Para sa hiwalay na network ng bot na ito ang ID.
    ID: { $id }
    pangalan: { $name }
gg-fed-info = Impormasyon ng pederasyon:
    mga tagapangasiwa: { $admins }
    ID: { $id }
    talaan: { $log }
    pangalan: { $name }
    mga abiso: { $notifications }
    may-ari: { $owner }
    kailangan ang dahilan: { $reasons }
gg-fed-list = Mga pederasyong pag-aari o pinamamahalaan mo:
    { $rows }
gg-fed-admins = May-ari muna, kasunod ang mga tagapangasiwa ng pederasyon:
    { $rows }
gg-fed-quiet = Ayos ng tahimik na paliwanag sa pagsali at mensahe. Nananatili ang pagpapatupad.
    halaga: { $value }
gg-fed-policy = Patakaran ng dahilan at abiso sa may-ari:
    mga abiso: { $notifications }
    kailangan ang dahilan: { $reasons }
gg-fed-confirm-delete = Permanente bang burahin ang pederasyon, datos at kasapian? Mananatili ang kasalukuyang pagbabawal sa Telegram. Personal na kumpirmahin sa loob ng limang minuto.
    ID: { $id }
    pangalan: { $name }
gg-fed-confirm-log = Itakda ang ipinakitang talaan ng pederasyon? Kumpirmahin sa loob ng limang minuto. Susuriing muli ang iyong karapatan at karapatan sa paglalathala ng bot sa destinasyon.
    destinasyon: { $destination }
    ID: { $id }
    pangalan: { $name }
gg-fed-confirm-sent = Naipadala ang personal na kumpirmasyon sa may-ari ng pederasyon.
gg-fed-deleted = Nabura ang pederasyon. Mananatili ang kasalukuyang pagbabawal sa Telegram.
gg-fed-log-set = Naitakda ang destinasyon ng talaan ng pederasyon:
    destinasyon: { $destination }
gg-fed-cancel = Kanselahin
gg-fed-cancelled = Nakansela.
gg-fed-saved-delivery-failed = Na-save ang pagbabago ngunit hindi naihatid ang abiso o tala. Suriin ang destinasyon at akses ng bot.
gg-fed-error-authority = Kailangan ang kasalukuyang may-ari o naaangkop na tungkulin sa pederasyon. Hindi nagbibigay ng karapatan sa pederasyon ang pagiging tagapangasiwa ng grupo.
gg-fed-error-private = Gamitin ang utos sa pribadong usapan mo sa bot na ito.
gg-fed-error-group = Gamitin ang utos sa tunay na grupo. Hindi pumipili ng grupong pederasyon ang pribadong koneksiyon.
gg-fed-error-owned = May pag-aari ka nang pederasyon sa bot na ito. Gamitin ang /fedinfo, /renamefed o /delfed nang pribado.
gg-fed-error-name = Magbigay ng hindi bakanteng pangalan na walang control character. Hanggang64 na karakter ang pangalan.
gg-fed-error-id = Magbigay ng wastong UUID ng pederasyon sa bot na ito. Hindi kumokonekta sa hiwalay nating serbisyo ang Rose ID.
gg-fed-error-missing = Walang pederasyon sa bot o kontekstong ito.
gg-fed-error-creator = Tanging kasalukuyang lumikha ng grupong Telegram ang puwedeng magsali o mag-alis ng grupo sa pederasyon.
gg-fed-error-target = Magbigay ng positibong ID ng tao, tugon sa tao o kasalukuyang napatunayang pangalan. Hindi puwedeng tanggalin sa tungkulin ang may-ari.
gg-fed-error-value = Hindi wastong argumento ng pederasyon. Gamitin ang on/off sa patakaran at wastong ID kung kailangan.
gg-fed-error-stale = Nag-expire, nagamit o nagbago ang pederasyon, may-ari o destinasyon ng kumpirmasyon. Humiling ng bago.
gg-fed-error-destination = Kailangang kasalukuyang tagapangasiwa ang may-ari sa destinasyon at makapaglathala ang bot. Kailangan ng channel ang post_messages.
gg-fed-error-delivery = Hindi naihatid o naitali ang personal na kumpirmasyon. Buksan ang pribadong usapan sa bot at subukan muli.
gg-fed-event = Pangyayari sa pederasyon:
    pangyayari: { $event }
    ID: { $id }
    pangalan: { $name }
    kasapi: { $user }
gg-fed-event-rename = Nabago ang pangalan
gg-fed-event-delete = Nabura; nananatili ang pagbabawal sa Telegram
gg-fed-event-promote = Nadagdag ang tagapangasiwa
gg-fed-event-demote = Naalis ang tagapangasiwa
gg-fed-event-self-remove = Umalis sa tungkulin ang tagapangasiwa
gg-fed-event-reason = Nabago ang patakaran ng dahilan
gg-fed-event-notif = Nabago ang abiso sa may-ari
gg-fed-event-log = Nabago ang destinasyon ng talaan
gg-fed-event-unlog = Naalis ang destinasyon ng talaan
gg-fed-event-ban = Na-save ang patakaran ng pagbabawal; nakapila ang pagpapatupad
gg-fed-event-unban = Naalis ang patakaran ng pagbabawal; nakapila ang pag-alis ng paghihigpit na pag-aari ng bot
gg-fed-event-subscribe = Nadagdag ang suskripsiyon; nakapila ang pagsuri ng nakitang gumagamit
gg-fed-event-unsubscribe = Naalis ang suskripsiyon; nananatili ang ibang pinagmulan
gg-fed-ban-details = Target at dahilan ng pagbabawal:
    dahilan: { $reason }
    kasapi: { $user }
gg-fed-passive = Ipinagbabawal ng patakaran ng pederasyon ang kasapi. Nasa ibaba ang pinagmulan at dahilan.
    ID: { $id }
    dahilan: { $reason }
    pinagmulan: { $source }
    kasapi: { $user }
gg-fed-enforce-failed = Ipinagbabawal ng patakaran ng pederasyon ang kasapi ngunit nabigo ang pag-alis. Suriin ang karapatan ng bot. Nasa ibaba ang pinagmulan at dahilan.
    ID: { $id }
    dahilan: { $reason }
    pinagmulan: { $source }
    kasapi: { $user }
gg-fed-stat = Mga pagbabawal ng pederasyon para sa kasaping ito:
    { $rows }
    kasapi: { $user }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — aktibo: { $status }; pagbabago: { $date }.
gg-fed-stat-more = May iba pang pinagmulan. Gamitin ang utos na pagpapatuloy o tiyak na ID ng pederasyon para sa dahilan at petsa.
gg-fed-intent-saved = Na-save ang patakaran; nakapila ang mga nakitang target. Sinusuri ang kasalukuyang karapatan at ibang pinagmulan ng paghihigpit bago ang epekto.
    kasapi: { $user }
    bersiyon: { $version }
gg-fed-subscriptions = Mga tuwirang suskripsiyon sa pagbabawal ng pederasyon:
    { $rows }
gg-fed-imported = Nasuri at na-save ang mga tala; nilaktawan ang magkaparehong dobleng tala. Nakapila ang pagpapatupad sa nakitang target.
    bilang: { $count }
    magkaparehong dobleng tala: { $duplicates }
gg-fed-event-import = Na-import ang nasuring pagbabawal; nakapila ang pagpapatupad
gg-fed-error-file-format = Tumugon sa UTF-8 CSV na may id/reason, JSONL/NDJSON na may user_id o JSON array na na-export ng bot. Pinipigil ng maling linya ang lahat ng pagsulat.
gg-fed-error-file-limit = Hanggang2 MiB at1000tala. Tinatanggihan ang kulang o malaking file; hindi tahimik na pinuputol ang listahan.
gg-fed-error-file-duplicate = Magkasalungat ang tala para sa iisang ID ng gumagamit. Walang pagbabawal na na-import.
gg-fed-error-file-rate = Iisang30minutong pagitan ang import at export bawat pederasyon. Subukan mamaya.
gg-fed-error-reason = Hanggang1024karakter ang dahilan, walang di-suportadong control character.
gg-fed-error-reason_required = Kailangan ng pederasyon ang hindi bakanteng dahilan sa bawat pagbabawal.
gg-fed-error-cycle = Hindi puwedeng magsuskripsiyon ang pederasyon sa sarili o gumawa ng paikot na ugnayan.
gg-fed-error-graph_limit = Naabot ang hangganan:32tuwirang target,128naaabot na pederasyon, lalim16 o10000ugnayan sa bot na ito.
gg-data-confirm = Kumpirmahin sa loob ng limang minuto. Susuriing muli ang kasalukuyang lumikha at bersiyon ng grupo. Mga napiling modulo lang ang mababago; nananatili ang identidad, tiwala at aktibong pagbabawal.
    SHA-256: { $digest }
    grupo: { $group }
    mga modulo: { $modules }
    operasyon: { $operation }
gg-data-import = I-import ang modulo ng grupo
gg-data-reset = I-reset ang modulo ng grupo
gg-data-privacy-delete = Burahin ang opsiyonal na personal na datos ng bot na ito
gg-data-confirm-button = Kumpirmahin ang pagbabago
gg-data-personal = Buksan ang kumpirmasyon sa sarili mong pribadong usapan.
gg-data-saved = Na-save ang mga napiling modulo.
gg-data-error-authority = Kailangan ng kasalukuyang makikilalang lumikha ng grupo sa import/reset. Kailangan ng kasalukuyang tagapangasiwa sa export.
gg-data-error-format = Tumugon sa wastong may-bersiyong Group Guard JSON na ginawa ng /export.
gg-data-error-limit = Lampas sa itinakdang hangganan ng laki o nilalaman ang file.
gg-data-error-version = Hindi suportado ang schema o bersiyon; walang pagbabago.
gg-data-error-module = Pumili ng kilalang modulo:/export all o /export notes rules. Parehong pangalan ang gamit sa import/reset.
gg-data-error-field = Mali o kulang ang field ng modulo. Hindi nailapat ang mga ayos.
gg-data-error-item = Mali ang nilalaman, opsiyon o akses sa pag-ulit. Walang nilalamang na-save.
gg-data-error-media = Kailangang na-upload sa bot na ito at maabot sa getFile ang media. Hindi suportado ang file ID ng ibang bot.
gg-data-error-destination = Kailangan ng talaan at paksa ang kasalukuyang karapatan at kakayahan ng bot. Sa parehong grupo lang balido ang ID ng paksa.
gg-data-error-language = Pumili ng naka-install na wika sa /setlang.
gg-data-error-stale = Nag-expire, nagbago o nagamit ang kumpirmasyon. Magsimula muli.
gg-data-error-restore = Hindi ligtas maibalik ang pansamantalang paghihigpit na pag-aari ng bot. Nananatili ang ebidensiya; suriin ang karapatan ng bot.
gg-data-error-rate = Limang minuto ang lokal na pagitan ng operasyong datos ng grupo. Subukan mamaya.
gg-data-error-delivery = Hindi naihatid ang pribadong kumpirmasyon. Buksan ang pribadong usapan sa bot at subukan muli.
gg-data-error-saved_delivery = Na-save ang mga ayos ngunit hindi na-update ang mungkahing utos. Suriin ang karapatan ng bot.
gg-privacy-policy = <b>Datos mo sa Group Guard na ito</b>
    /privacy data nag-e-export ng koneksiyon, nakitang profile, babala, pag-apruba, kalagayan ng paghihigpit/pagpapatunay, pag-aari/tungkulin/pagbabawal sa pederasyon at trabaho ng seguridad. Hindi kasama ang pribadong nilalaman ng iba, sagot sa pagpapatunay, kredensiyal at hilaw na upload. Gamitin ang utos na pagpapatuloy.
    /privacy delete nag-aalis ng opsiyonal na kasaysayan ng koneksiyon, nakitang pangalan/pangalan ng gumagamit, di-aktibong pagpapatunay at nilalaman ng natapos mong kampanya sa bot na ito. Aktibong babala/paghihigpit, bersiyon ng pagbabawal, tungkulin, pag-aari, karapatan sa serbisyo, paghadlang sa replay at di-tiyak na API trabaho ay may minimal na ID para sa seguridad at pagkakasunod. Gamitin ang tahasang utos sa pag-alis/pagbura ng pederasyon para sa mga ugnayang iyon. Nananatili ang pinagsasaluhang profile ng plataporma at ibang bot.
    Hiwalay na pinamamahalaan ng operator ang backup at audit. Hindi binubura ng utos ang panlabas na mensaheng Telegram o backup, at walang ipinapangakong awtomatikong panahon ng pagtago.
gg-privacy-usage = /privacy policy · /privacy data [pagpapatuloy] · /privacy delete — sa sarili mong pribadong usapan sa bot na ito lamang.
gg-privacy-private = Kailangan ang tunay na pribadong usapan ng humihiling na tao. Hindi nagbibigay ng datos ng iba ang maling cursor.
gg-privacy-next = Susunod na pahina:/privacy data { $cursor }
gg-privacy-deleted = Naalis ang opsiyonal na personal na datos ng bot na ito. Minimal na ID ang itinatago ng aktibong seguridad, pag-aari at di-tiyak na trabaho; tingnan ang /privacy policy.
gg-language-usage = Pumili ng wikang panggrupo sa /setlang. Ang /lang nang pribado ay nagpapalit ng personal na wika sa plataporma. Nasa ibaba ang magagamit na code.
    mga code ng wika: { $codes }
gg-language-saved = Nabago ang wika ng sagot sa grupo.
gg-help-index = <b>Gabay sa utos ng Group Guard</b>
    /help pamilya · /help utos · /help pamilya 2. Puwede rin sa napatunayang /connect ang ipinakitang utos; nananatili sa tunay na pribadong usapan ang pribadong sagot.
    Kailangan ng ayos ang change_info; parusa ang restrict_members; pagbura ang delete_messages; pag-pin ang pin_messages; promosyon ang promote_members; paksa ang manage_topics. Hiwalay na sinusuri ang karapatan ng bot. Kailangan ng kasalukuyang taong lumikha sa gawain ng may-ari. Binubuksan ng /settings ang personal na panel ng grupo.
gg-help-search = <b>Mga katugmang utos</b>
    paghahanap: { $query }
gg-help-connected = Grupo o napatunayang koneksiyon; karapatan ayon sa saklaw
gg-help-group-only = Kailangan ang tunay na mensahe sa grupo
gg-help-unsupported = Napanatiling pangalan sa katalogo; paliwanag ang ibinabalik ng di-tiyak na gawain
gg-help-next = Susunod na pahina
gg-help-previous = Nakaraang pahina
gg-help-family-title-moderation = Pamamahala at pag-apruba
gg-help-family-title-messages = Pagbura at pag-pin ng mensahe
gg-help-family-title-logging = Awtorisadong talaan
gg-help-family-title-settings = Mga ayos at wika ng grupo
gg-help-family-title-content = Tala, pansala, tuntunin at pagbati
gg-help-family-title-captcha = Pagpapatunay ng bagong kasapi
gg-help-family-title-locks = Pagpigil at mga eksepsiyon
gg-help-family-title-blocklists = Pagtutugma at ipinagbabawal na nilalaman
gg-help-family-title-antispam = Proteksiyon sa pagbaha at maramihang pagsali
gg-help-family-title-connections = Pribadong koneksiyon sa grupo
gg-help-family-title-identity = Impormasyon ng gumagamit at usapan
gg-help-family-title-policy = Patakaran ng utos at bot
gg-help-family-title-cleanup = Paglilinis ng utos, bot at serbisyo
gg-help-family-title-topics = Mga paksa ng forum
gg-help-family-title-utilities = Pagpapadala at kampanya ng operator
gg-help-family-title-federations = Tungkulin, pagbabawal at suskripsiyon
gg-help-family-title-portability = File ng grupo at sariling datos
gg-help-family-title-discovery = Tulong at editor ng nilalaman
gg-help-family-moderation = Tumugon, magbigay ng ID o napatunayang @pangalan. /ban 20 dahilan, /tban 20 60s dahilan, /mute 20, /tmute 20 2h dahilan; pansamantala60s–365d. /kickme sarili lang. d variants bumubura ng tugon; s bumubura ng utos/tugon at kailangan ang delete. Protektado ang tagapangasiwa. /setwarnlimit 3, /setwarnmode ban, /setwarntime 1d; tatlong babala sa bagong grupo, nananatili ang lumang ayos. /approve para lang sa karaniwang nilalaman/pagbaha, hindi fed/CAS/raid/manu-mano. /promote limitado sa magkasanib na karapatan. Creator ang reset-all.
gg-help-family-messages = /del kailangan ang tunay na tugon sa grupo. /purge nagsisimula roon; /purgefrom at /purgeto mga hangganan. Naaangkop ang limitasyon at tuntunin ng Telegram; hindi eksaktong bilang ng pagbura ang pagkilala sa batch. /pin [loud], /permapin, /unpin, /unpinall kailangan ang pin; creator sa unpinall. /antichannelpin at /cleanlinked para sa awtomatikong mensahe ng nakakonektang channel.
gg-help-family-logging = /setlog -100… kailangan ang kasalukuyang pagiging admin sa destinasyon at paglalathala ng bot. Kailangang tumugma sa tunay na natanggap na pinagmulan ang forwarded setup. /logcategories:settings/admin/user/automated/reports/other; /log at /nolog pagpili. Nakikita ang kabiguan ng paghahatid; hindi patunay ng matagumpay na aksiyon ang tala.
gg-help-family-settings = /settings personal na panel na nag-e-expire; sariwang change_info. /setlang code wika ng grupo; /lang nang pribado sariling wika. /night 23 7 +3 pagsara sa gabi; /night off nagbabalik lang ng pag-aari ng bot na kasalukuyang tumutugma. Mas nauuna ang panlabas na pagbabago.
gg-help-family-content = /save salita teksto o tugon sa media; /get salita, #salita, /notes. Iisang salita ang bagong pangalan; nananatili ang lumang malawak na pangalan. /filter "parirala" teksto, /filterprefix, /filterexact; /stop tiyak na susi. Creator confirmation sa /clearall at /stopall. Rose formatting, link, quote at random %%%. Fields:{ "{" }first{ "}" }, { "{" }last{ "}" }, { "{" }fullname{ "}" }, { "{" }username{ "}" }, { "{" }mention{ "}" }, { "{" }id{ "}" }, { "{" }chatname{ "}" }, { "{" }count{ "}" }. /button URL/tala/tuntunin. Mga opsiyon:preview/nonotif/protect/mediaspoiler; tala admin/private/noprivate/repeat; pansala user/allow_bot/replytag/command. /save salita kumusta { "{" }repeat 5m{ "}" } para lang sa pampublikong nilalaman at sariwang karapatan ng may-akda. Media para sa sariling bot.
gg-help-family-captcha = /captcha on/off, /captchamode off/button/math/text/text2, /setcaptchatext, /captcharules on, /captchakick on/off; /captchakicktime at /captchamutetime bounded. May generation/deadline ang issued challenge. Join request kailangan invite-users, mute restrict-members. Personal at single-use ang sagot. Mas nauuna ang pagbabawal ng pederasyon.
gg-help-family-locks = /lock links [aksiyon], /unlock uri; /locktypes tunay na uri, /locks kalagayan. /lockwarns babala. /allowlist domain/path, eksaktong invite, @chat o stickerpack:/forward:/inline:/channel:/chat:/bot:/command:. Mali ay tinatanggihan. Sa katugmang nilalaman lang ang eksepsiyon; creator at awtorisadong log para sa tahimik na awtomatika.
gg-help-family-blocklists = /addblocklist "parirala" teksto/prefix/exact at tahasang identidad na may opsiyonal na dahilan/aksiyon. /rmblocklist tiyak na piniling susi. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute; tagal sa pansamantala. Hiwalay ang /blocklistdelete. May limitasyon ang hirap ng pattern; tinatanggihan ang mali o sobrang tala.
gg-help-family-antispam = /setflood bilang sunod-sunod; /setfloodtimer bilang tagal panahon; /setfloodmode parusa/tagal; /clearflood paglilinis. Nananatili ang lumang ayos. /flood at /antiflood patakaran; alias isang lokal na pasiya. /antiraid on/off/duration, /raidtime, /raidactiontime, /autoantiraid magkahiwalay na panahon at parusa. Mas nauuna sa approval/CAPTCHA; generation-based expiry nabubuhay sa restart.
gg-help-family-connections = /connect groupID o personal na link; sinusuri ang kasapian mo at ng bot. Tiyak na sariwang karapatan pa rin ang pagbabago. /connection pagpili, /disconnect pag-alis, /connect kasaysayan at pagpapatuloy. Walang fed-owner o operator authority mula sa koneksiyon.
gg-help-family-identity = /id tunay na ID ng gumagamit/usapan/pinagmulan; /info kasalukuyang target. Tugon at @pangalan kailangan ang kasalukuyang ebidensiya ng sariling bot. Hindi nakikilala ang tao sa anonymous group message; walang inimbentong taong ID.
gg-help-family-policy = /disable utos, /enable utos, /disabled, /disableable canonical at alias. /disableadmin eksepsiyon ng admin; /disabledel pagbura. Magagamit pa rin ang recovery. /bot2bot off/admin/all tunay na kasapian; default human review sa pagbabago. Creator lang /bot2botskipreview. /silentactions consent at authorized log. Di-tiyak na runs/saved may paliwanag.
gg-help-family-cleanup = /cleancommand admin/user/other at /keepcommand pagpili ng utos. /cleanmsg action/filter/note at /keepmsg sa tunay na naipadala ng sariling bot lang; resibo at5mintrabaho, hindi hinuhulaang ID. /cleanservice at /nocleanservice:join/leave/other/photo/pin/title/videochat. Nauuna ang wastong serbisyong gawain at bayad sa pagbura.
gg-help-family-topics = /newtopic pangalan, /renametopic pangalan, /closetopic, /reopentopic tunay na kasalukuyang paksa. Creator confirmation sa /deletetopic; /setactiontopic parehong grupo. Kailangan forum at manage-topics. Totoong error sa kulang o di-suportadong paksa.
gg-help-family-utilities = /echo at /say direktang nilalaman o tugon sa bounded renderer. /broadcast configured operator o tunay na child-owner lang, sariling configured group lang. Mga resulta may partial/uncertain delivery; status/cancel hindi nag-uulit ng matagumpay na naihatid.
gg-help-family-federations = /newfed pangalan sariling UUID. Sa pribado pag-aari mong fed anuman ang koneksiyon; UUID read hindi role. /fedpromote at /feddemote tungkulin; /feddemoteme sarili. /joinfed UUID at /leavefed kasalukuyang creator. Hindi nag-aalis ng Telegram bans ang deletion. /fban userID dahilan, /unfban userID may-ari/fed-admin; /fedreason, /fednotif, /setfedlog may-ari. /quietfed paliwanag lang. /subfed UUID bounded directed, walang cycle. /fedstat [userID], /fbanstat UUID source/status. /fbanlist csv/minicsv/json may-ari30minsharedinterval; /importfbans bounded CSV o tunay na JSONL at sariling JSON array. Nakitang gumagamit lang, walang buong member inventory.
gg-help-family-portability = /export all o modulo admin; /import at /reset kasalukuyang taong creator at single-use personal confirmation5min. Lokal na pagitan5min; sariling may-bersiyong JSON hanggang2MiB at content caps. Modulo:moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Nananatili ang di-pinili. Hindi ini-import ang tiwala, issued challenge/jobs, entitlements, roles o aktibong bans. /privacy policy/data/delete sariling PM, may pahina at minimal security retention. Walang verified full Rose export adapter.
gg-help-family-discovery = /help mga pamilya; /help utos pangalan/alias; /help pamilya 2 pagpapatuloy. /button tumutulong sa markup ng buton. Mga gabay may konteksto, karapatan, default at hangganan. /settings personal na panel ng grupo.
gg-data-error-cache_pending = Naalis ang opsiyonal na datos sa SQL. Nakapila ang paglilinis ng di-maabot na cache; nananatili ang aktibong datos ng seguridad.
