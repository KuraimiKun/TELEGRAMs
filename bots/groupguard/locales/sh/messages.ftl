## Independently authored Group Guard sh content.
group-welcome = 🛡 Hvala što ste me dodali! Dajte mi administratorska prava za brisanje poruka, ograničavanje članova i zakačivanje poruka. Podešavanja se otvaraju komandom /settings.
gg-start = 🛡 Zdravo <b>{ $name }</b>! Ja sam <b>Group Guard</b>: provera novih članova, zaštita od previše poruka i CAS, zabrane sadržaja, moderacija, beleške, filteri, pravila i pozdravi. Dodajte me kao administratora i koristite /settings ili /help.
gg-help = 📖 /help prikazuje oblasti; /help komanda traži komande. Moderacija: /ban /mute /kick /warn. Sadržaj: /save /filter /rules. Zaštita: /lock /blocklist /night. /settings otvara lični panel grupe.
gg-welcome-default = 👋 Dobro došli { "{" }mention{ "}" } u <b>{ "{" }group{ "}" }</b>!
gg-credit = 🛡 Zaštitu pruža @{ $bot }
gg-btn-add = ➕ Dodaj u grupu
gg-btn-commands = 📖 Komande
gg-btn-rules = 📜 Pravila
gg-btn-human = ✅ Ja sam čovek
gg-btn-unwarn = ↩️ Ukloni upozorenje (administratori)
gg-btn-locks = 🔒 Zabrane sadržaja · Broj: { $count }
gg-btn-open-settings = ⚙️ Otvori podešavanja
gg-btn-admin-tab = 🛡 Grupe
gg-captcha = 🤖 Potvrdite da ste čovek pre isteka navedenog roka, inače ćete biti uklonjeni.
    Minuti: { $minutes }
    Član: { $user }
gg-captcha-button = Pritisnite dugme ispod 👇
gg-captcha-math = Koliko je <b>{ $a } + { $b }</b>?
gg-captcha-not-you = Ovo dugme pripada drugoj osobi.
gg-captcha-ok = ✅ Dobro došli!
gg-captcha-wrong = ❌ Pogrešan odgovor. Pokušajte ponovo ako imate preostalih pokušaja.
    Preostali pokušaji: { $left }
gg-captcha-failed = ❌ Previše pogrešnih odgovora.
gg-captcha-passed = ✅ Provera uspešna. Dobro došli!
    Član: { $user }
gg-cas-banned = 🚫 CAS prepoznaje člana kao pošiljaoca spama; član je blokiran.
    Član: { $user }
gg-join-request = 👋 Potvrdite da ste čovek da biste ušli u grupu:
    Grupa: { $group }
gg-join-approved = ✅ Zahtev odobren. Dobro došli!
gg-join-expired = ⌛ Zahtev je istekao. Pošaljite novi zahtev za pristup.
gg-goodbye = 👋 Član je napustio grupu.
    Član: { $user }
gg-flood-mute = 🌊 Član je privremeno utišan zbog previše poruka.
    Član: { $user }
gg-flood-kick = 🌊 Član je uklonjen zbog previše poruka.
    Član: { $user }
gg-flood-ban = 🌊 Član je blokiran zbog previše poruka.
    Član: { $user }
gg-newbie-links = 🆕 Novi članovi ne smeju slati linkove tokom navedenih prvih sati.
    Sati: { $hours }
    Član: { $user }
gg-spam-banned = 🧠 Član je blokiran zbog spama.
    Član: { $user }
gg-reason-blocklist = zabranjena reč
gg-need-right = ⛔ Potrebno je odgovarajuće administratorsko pravo.
    Pravo: { $right }
gg-right-admin = administrator
gg-right-restrict = ograničavanje članova
gg-right-delete = brisanje poruka
gg-right-pin = zakačivanje poruka
gg-right-change_info = menjanje informacija grupe
gg-admins-only = ⛔ Samo za administratore.
gg-need-target = 👤 Odgovorite na poruku ili navedite ID ili trenutno proverenog @korisnika.
gg-target-admin = 🙅 Ova radnja ne sme pogoditi administratora.
gg-bot-no-rights = ⚠️ Moram biti administrator sa potrebnim pravima.
gg-banned = 🔨 Član je blokiran.
    Razlog: { $reason }
    Član: { $user }
gg-banned-for = 🔨 Član je blokiran na navedeni period.
    Razlog: { $reason }
    Vreme: { $time }
    Član: { $user }
gg-unbanned = ✅ Blokada člana uklonjena.
    Član: { $user }
gg-kicked = 👢 Član je uklonjen i može se vratiti.
    Razlog: { $reason }
    Član: { $user }
gg-muted = 🔇 Član je utišan.
    Razlog: { $reason }
    Član: { $user }
gg-muted-for = 🔇 Član je utišan na navedeni period.
    Razlog: { $reason }
    Vreme: { $time }
    Član: { $user }
gg-unmuted = 🔊 Član ponovo može pisati.
    Član: { $user }
gg-warned = ⚠️ Upozorenje člana zabeleženo.
    Broj: { $count }
    Limit: { $limit }
    Razlog: { $reason }
    Član: { $user }
gg-warn-limit-ban = 🔨 Dostignut prag upozorenja; član blokiran.
    Limit: { $limit }
    Član: { $user }
gg-warn-limit-mute = 🔇 Dostignut prag upozorenja; član utišan.
    Limit: { $limit }
    Član: { $user }
gg-warn-limit-kick = 👢 Dostignut prag upozorenja; član uklonjen.
    Limit: { $limit }
    Član: { $user }
gg-unwarned = ↩️ Jedno upozorenje člana uklonjeno.
    Broj: { $count }
    Limit: { $limit }
    Član: { $user }
gg-warn-removed = ↩️ Administrator je uklonio upozorenje.
    Administrator: { $admin }
gg-warns = ⚠️ Upozorenja člana:
    Broj: { $count }
    Limit: { $limit }
    Član: { $user }
gg-warns-reset = 🧽 Upozorenja člana poništena.
    Član: { $user }
gg-purge-reply = 🧹 Odgovorite na prvu poruku koju želite obrisati.
gg-purged = 🧹 Poruke obrisane.
    Broj: { $count }
gg-pin-reply = 📌 Odgovorite na poruku koju želite zakačiti.
gg-report-reply = 🚨 Odgovorite na poruku koju želite prijaviti.
gg-reported = 🚨 Član prijavljen administratorima.
    Član: { $user }
gg-setlog-usage = 📒 Dodajte me kao administratora kanala dnevnika pa koristite <code>/setlog -100…</code> sa njegovim ID-jem.
gg-setlog-failed = ⚠️ Ne mogu slati tamo. Prvo me dodajte kao administratora.
gg-setlog-done = 📒 Kanal dnevnika povezan.
gg-setlog-off = 📒 Kanal dnevnika odvojen.
gg-log-connected = 📒 Ovaj razgovor prima dnevnik moderacije grupe.
    Grupa: { $group }
gg-log-flood = 🌊 Otkriveno previše poruka:
    Radnja: { $action }
    Član: { $user }
gg-log-report = 🚨 Prijava člana:
    Član: { $user }
gg-log-spam = 🧠 Blokada zbog spama otkrivenog AI-jem:
    Tekst: { $text }
    Član: { $user }
gg-rules = 📜 <b>Pravila</b>
    { $rules }
gg-no-rules = 📜 Pravila još nisu sačuvana. Administratori mogu koristiti /setrules tekst.
gg-rules-saved = 📜 Pravila sačuvana.
gg-rules-cleared = 📜 Pravila obrisana.
gg-welcome-usage = 👋 Koristite <code>/setwelcome Zdravo {"{"}mention{"}"}, dobro došli u {"{"}group{"}"}!</code> ili odgovorite na poruku.
gg-welcome-saved = 👋 Pozdrav sačuvan.
gg-welcome-reset = 👋 Podrazumevani pozdrav vraćen.
gg-note-usage = 📝 <code>/save ime tekst</code> ili odgovor na poruku sa <code>/save ime</code>.
gg-filter-usage = 🔁 <code>/filter reč odgovor</code> ili odgovor sa <code>/filter reč</code>.
gg-note-saved = 📝 Beleška sačuvana. Pristup: <code>#{ $key }</code>, prema pravima pristupa.
gg-filter-saved = 🔁 Odgovoriću kada se poklopi „{ $key }“.
gg-notes-empty = 📝 Još nema beležaka.
gg-filters-empty = 🔁 Još nema filtera.
gg-notes-list = 📝 <b>Beleške</b>
gg-filters-list = 🔁 <b>Filteri</b>
gg-item-deleted = 🗑 Stavka obrisana.
    Ključ: { $key }
gg-item-missing = 🤷 Ništa nije sačuvano pod ovim imenom.
gg-items-limit = 📦 Dostignut limit beležaka i filtera grupe.
gg-lock-usage = 🔒 Koristite <code>/lock links</code>. Dostupni tipovi su ispod; <code>all</code> bira sve.
    Tipovi: { $types }
gg-locked = 🔒 Zabranjeni sadržaji:
    Tipovi: { $types }
gg-unlocked = 🔓 Dozvoljeni sadržaji:
    Tipovi: { $types }
gg-locks-title = 🔒 <b>Zabrane sadržaja</b>
gg-locks-panel = 🔒 <b>Zabrane</b>: zabranjeni sadržaji se brišu; administratori su izuzeti.
gg-lock-links = Linkovi
gg-lock-invites = Linkovi poziva
gg-lock-forwards = Prosleđivanja
gg-lock-media = Mediji
gg-lock-stickers = Nalepnice
gg-lock-gifs = GIF
gg-lock-voice = Glasovne poruke
gg-lock-polls = Ankete
gg-lock-bots = Botovi
gg-blocklist = 🚫 <b>Zabranjene reči</b>
    Reči: { $words }
gg-blocklist-empty = 🚫 Nema zabranjenih reči.
gg-blocklist-usage = 🚫 <code>/addblock reč, druga fraza</code> · <code>/rmblock reč</code>
gg-blocklist-saved = 🚫 Lista zabrana ažurirana.
    Broj: { $count }
gg-night-usage = 🌙 <code>/night 23 7 +3</code> zatvara od 23:00 do 07:00 UTC+3; <code>/night off</code> isključuje.
gg-night-on = 🌙 Noćni raspored grupe podešen.
    Kraj: { $end }
    Početak: { $start }
    Vremenska zona: { $tz }
gg-night-off = 🌙 Noćni režim isključen.
gg-night-start = 🌙 Laku noć! Grupa ostaje zatvorena do navedenog vremena.
    Kraj: { $end }
gg-night-end = ☀️ Dobro jutro! Grupa je ponovo otvorena.
gg-panel = ⚙️ <b>Podešavanja grupe</b>
    Pritisnite opciju za promenu. Noćni raspored se podešava sa /night.
    Grupa: { $group }
    Noćni raspored: { $night }
gg-panel-sent = 📬 Podešavanja poslata privatno.
gg-panel-start-first = 📬 Prvo otvorite privatni razgovor sa mnom, zatim pritisnite ispod.
gg-credit-vip = 💎 Skrivanje zaštitnog reda zahteva VIP. Koristite /vip privatno.
gg-opt-wel = 👋 Dobrodošlica · Vrednost: { $value }
gg-opt-cln = 🧹 Briši poruke o pristupanju · Vrednost: { $value }
gg-opt-bye = 👋 Oproštaj · Vrednost: { $value }
gg-opt-cap = 🤖 Provera · Vrednost: { $value }
gg-opt-cpm = ⏱ Rok provere, minuti · Vrednost: { $value }
gg-opt-fld = 🌊 Limit poruka · Vrednost: { $value }
gg-opt-fla = 🌊 Radnja zbog previše poruka · Vrednost: { $value }
gg-opt-wrn = ⚠️ Prag upozorenja · Vrednost: { $value }
gg-opt-wra = ⚠️ Radnja upozorenja · Vrednost: { $value }
gg-opt-act = ⏳ Automatsko ograničenje, minuti · Vrednost: { $value }
gg-opt-cas = 🛡 CAS zaštita · Vrednost: { $value }
gg-opt-nwb = 🆕 Novi članovi bez linkova, sati · Vrednost: { $value }
gg-opt-ais = 🧠 AI zaštita od spama · Vrednost: { $value }
gg-opt-ngt = 🌙 Noćni režim · Vrednost: { $value }
gg-opt-crd = 🏷 Zaštitni red · Vrednost: { $value }
gg-opt-lang = 🌐 Jezik · Vrednost: { $value }
gg-val-button = Dugme
gg-val-math = Račun
gg-val-off = isključeno
gg-val-mute = utišaj
gg-val-kick = ukloni
gg-val-ban = blokiraj
gg-adm = 🛡 <b>Group Guard: statistika</b>
    Grupe: { $groups }
    Stavke: { $items }
    Upozorenja: { $warns }
cmd-settings = Podešavanja grupe
cmd-help = Vodič komandi
gg-auth-denied = Ovlašćenje nije moglo biti provereno. Ništa nije promenjeno.
gg-target-invalid = Izaberite poznatog člana koji je čovek. Cilj nije mogao biti proveren.
gg-duration-invalid = Koristite trajanje od 60s do 365d. Privremene komande zahtevaju trajanje.
gg-reason-invalid = Razlog sme imati najviše 256 znakova.
gg-outcome-failed = Radnja nije uspela ili nije odobrena.
gg-outcome-partial = Radnja završena delimično. Blokada može ostati ako vraćanje posle uklanjanja ne uspe.
gg-outcome-ancillary = Glavna radnja završena, ali dodatni korak nije uspeo.
gg-review-request = Proverite nepromenljivu radnju ispod. Trenutno ovlašćena osoba može odobriti u roku od 120 sekundi. Trajanje je prikazano u sekundama.
    Detalji: { $details }
    Trajanje: { $duration }
    Operacija: { $operation }
    Cilj: { $target }
gg-review-approve = Odobri ovu radnju
gg-review-unavailable = Skladište potvrda nije dostupno. Pošaljite novu komandu.
gg-review-expired = Potvrda je istekla, nevažeća ili već korišćena.
gg-review-consumed = Potvrda iskorišćena. Proverite rezultat; ponavljanje zahteva novu komandu.
gg-duration-permanent = Trajno / bez vremenskog ograničenja
gg-purge-ack = API je potvrdio zahteve brisanja. Stvarni broj obrisanih poruka nije poznat.
    API potvrdio: { $acknowledged }
    Zatraženo: { $requested }
gg-warning-removed = Upozorenje uklonjeno.
gg-op-ban = blokiraj
gg-op-mute = utišaj
gg-op-kick = ukloni
gg-op-unban = skini blokadu
gg-op-unmute = skini utišavanje
gg-op-warn = upozori
gg-op-unwarn = ukloni upozorenje
gg-op-resetwarns = poništi upozorenja
gg-op-purge = obriši raspon poruka
gg-op-delete = obriši poruku
gg-op-pin = zakači poruku
gg-op-unpin = odvoji poruku
gg-op-setlog = podesi odredište dnevnika
gg-op-unsetlog = ukloni odredište dnevnika
gg-op-config = promeni podešavanja
gg-op-save = sačuvaj sadržaj
gg-op-remove = ukloni sadržaj
gg-op-panel = otvori panel
gg-review-details-above = Puni zatraženi sadržaj je u poruci neposredno iznad.
gg-warn-pending = Upozorenje sačuvano; radnja praga se već obrađuje.
gg-done = Završeno.
gg-setting-saved = Podešavanje sačuvano.
    Podešavanje: { $setting }
gg-setting-value = Trenutna vrednost podešavanja:
    Podešavanje: { $setting }
    Vrednost: { $value }
gg-setting-invalid = Nevažeće podešavanje. Koristite on/off, važeći režim ili trajanje kao 10m.
gg-warning-settings = Podešavanja upozorenja:
    Trajanje: { $duration }
    Istek: { $expiry }
    Limit: { $limit }
    Režim: { $mode }
gg-admin-changed = Administratorska radnja završena.
    Radnja: { $action }
    Član: { $user }
gg-admin-list = Javni administratori:
    { $admins }
gg-approved = Član odobren.
    Razlog: { $reason }
    Član: { $user }
gg-unapproved = Odobrenja uklonjena.
    Broj: { $count }
gg-approval-status = Status odobrenja člana:
    Razlog: { $reason }
    Status: { $status }
    Član: { $user }
gg-approval-list = Odobreni članovi:
    { $approvals }
gg-next-page = Još stavki: { $command }
gg-range-invalid = Nevažeći raspon. Izaberite bar jednu poruku i ne pređite navedeni limit.
    Maksimum: { $cap }
gg-range-start = Početak je sačuvan za vas u ovoj temi deset minuta. Odgovorite na poslednju poruku sa /purgeto.
gg-range-missing = Ovde nema sačuvanog početka za vas. Prvo koristite /purgefrom kao odgovor.
gg-content-needed = Unesite sadržaj ili odgovorite na njega; najviše 3500 znakova.
gg-log-status = Podešavanja dnevnika:
    Kategorije: { $categories }
    Odredište: { $destination }
gg-log-unverified = Nisam primio potvrđeni original ove kanalske komande. Prvo pošaljite /setlog u kanalu.
gg-log-forward = Prosledite ovaj originalni /setlog grupi. Administrator koji povezuje mora menjati informacije u oba razgovora.
gg-info = Informacije o korisniku ili razgovoru:
    ID: { $id }
    Članstvo: { $membership }
    Ime: { $name }
    Korisničko ime: { $username }
gg-op-unpinall = odvoji sve poruke
gg-op-permapin = trajno zakači
gg-op-promote = imenuj administratora
gg-op-demote = smeni administratora
gg-op-approve_user = odobri korisnika
gg-op-unapprove = ukloni odobrenje
gg-op-unapproveall = ukloni sva odobrenja
gg-unknown = Nepoznato
gg-chat-id = ID razgovora:
    ID: { $id }
gg-on = Uključeno
gg-off = Isključeno
gg-anon-enabled = Poverenje u anonimne administratore je ovde uključeno. Anonimne komande ove grupe koriste prava bota bez identifikacije osobe. Vlasničke radnje i dalje zahtevaju proverenog osnivača. /anonadmin off vraća ljudsku proveru.
gg-right-invite_users = pozivanje korisnika
gg-right-promote_members = imenovanje administratora
gg-right-manage_topics = upravljanje temama
gg-right-creator = osnivač grupe
gg-log-join = Član pristupio.
    Član: { $user }
gg-log-leave = Član otišao.
    Član: { $user }
gg-warning-row = Zapis upozorenja:
    Istek: { $expiry }
    ID: { $id }
    Razlog: { $reason }
gg-menu-prompt = Izaberite opciju.
gg-content-invalid = Sadržaj nevažeći ili prelazi Telegram limite. Proverite ime, format, modifikatore i dugmad.
gg-content-unavailable = Sadržaj nije dostupan ili trenutno članstvo u grupi ne dozvoljava pristup.
gg-btn-private-note = Otvori belešku
gg-open-private = Otvori ovaj sadržaj privatno:
gg-items-cleared = Stavke obrisane.
    Broj: { $count }
gg-clearall-confirm = Osnivač grupe potvrđuje sa <code>/{ $command } confirm</code>.
gg-button-usage = Koristite <code>/button "Oznaka" https://example.com</code>. Dodajte <code>"Beleška" #ime same</code> za još jedno dugme u istom redu. Dobićete oznake i funkcionalni pregled.
gg-btn-accept-rules = Prihvati pravila
gg-btn-open-verification = Otvori proveru
gg-captcha-private = Otvorite privatnu proveru za potvrdu članstva u grupi.
    Član: { $user }
gg-captcha-choice = Izaberite odgovarajuću sliku dugmadima. Režim i mesto znaka su ispod.
    Režim: { $mode }
    Položaj: { $position }
gg-captcha-settings = Podešavanja provere:
    Uključeno: { $enabled }
    Uklanjanje: { $kick }
    Režim: { $mode }
    Oslobađanje: { $release }
    Sekunde: { $seconds }
gg-captcha-dependency = Uključite pozdrave pre provere. Sačuvajte pravila pre zahteva za prihvatanje.
gg-val-text = Slika teksta
gg-val-text2 = Slika znakova
gg-captcha-attempts-exhausted = Provera neuspešna posle previše pogrešnih odgovora; predviđeno ograničenje primenjeno.
gg-captcha-admin-exempt = Sada ste administrator grupe. Provera završena.
gg-captcha-question-text = Izaberite reč sa slike.
gg-captcha-question-math = Rešite jednačinu sa slike i izaberite odgovor.
gg-captcha-question-text2 = Izaberite navedeni znak sa slike, sleva nadesno.
    Položaj: { $position }
gg-locktypes = Dostupne zabrane sadržaja:
    Tipovi: { $types }
gg-allowlist-title = Izuzeci od zabrana sadržaja
gg-allowlist-invalid = Nevažeći izuzetak. Koristite domen/putanju, tačan poziv, @razgovor ili navedeni identitet kao stickerpack:ime.
gg-reason-lock = Zabranjeni sadržaj:
    Tipovi: { $types }
gg-lock-applied = Pravilo zabrane primenjeno.
    Razlog: { $reason }
    Tipovi: { $types }
gg-reaction-failed = Pravilo reakcija nije moglo biti primenjeno. Ovaj Bot API server možda ne podržava uklanjanje reakcija.
    Kod: { $code }
gg-reaction-anonymous = Anonimni brojevi ne daju ID korisnika ili razgovora pošiljaoca. API uklanjanja to zahteva; uklanjanje se ne tvrdi.
gg-none = Nema
gg-blocklist-title = Lista zabrana
gg-blocklist-invalid = Nevažeći okidač, razlog ili radnja. Proverite navodnike, izbegavanje džokera i obavezno trajanje privremenih režima.
gg-blocklist-settings = Podešavanja liste zabrana:
    Brisanje: { $delete }
    Režim: { $mode }
gg-blocklist-action = Pravilo liste zabrana primenjeno na člana.
    Razlog: { $reason }
    Član: { $user }
gg-lock-album = Albumi
gg-lock-anonchannel = Kanalski pošiljaoci
gg-lock-audio = Audio
gg-lock-bot = Botovi
gg-lock-button = Dugmad u poruci
gg-lock-cashtag = Oznake valuta
gg-lock-checklist = Kontrolne liste
gg-lock-cjk = Kineski/japanski/korejski tekst
gg-lock-command = Komande
gg-lock-comment = Komentari nečlanova
gg-lock-contact = Kontakti
gg-lock-cyrillic = Ćirilični tekst
gg-lock-document = Dokumenti
gg-lock-email = Adrese e-pošte
gg-lock-emoji = Emoji
gg-lock-emojicustom = Prilagođeni emoji
gg-lock-emojigame = Emoji igre
gg-lock-emojionly = Tekst samo sa emoji
gg-lock-externalreply = Spoljni odgovori
gg-lock-forward = Prosleđivanja
gg-lock-forwarduser = Prosleđivanja korisnika
gg-lock-forwardbot = Prosleđivanja botova
gg-lock-forwardchannel = Prosleđivanja kanala
gg-lock-forwardstory = Prosleđene priče
gg-lock-game = Igre
gg-lock-gif = GIF animacije
gg-lock-guestbot = Gostujući botovi
gg-lock-inline = Inline botovi
gg-lock-invitelink = Telegram pozivi
gg-lock-botlink = Linkovi botova
gg-lock-location = Lokacije
gg-lock-outsidereaction = Reakcije nečlanova
gg-lock-phone = Telefonski brojevi
gg-lock-photo = Fotografije
gg-lock-poll = Ankete
gg-lock-reaction = Reakcije
gg-lock-rtl = Tekst zdesna nalevo
gg-lock-spoiler = Skriveni sadržaj
gg-lock-sticker = Nalepnice
gg-lock-stickeranimated = Animirane nalepnice
gg-lock-stickerpremium = Premium nalepnice
gg-lock-text = Tekst
gg-lock-url = URL
gg-lock-video = Video
gg-lock-videonote = Video poruke
gg-flood-status = Previše poruka: uzastopni prag na N; vremenski prozor iznad N. Radnja, trajanje i čišćenje niza su ispod.
    Očisti ceo niz: { $clear }
    Uzastopni prag: { $consecutive }
    Broj: { $count }
    Trajanje: { $duration }
    Režim: { $mode }
    Sekunde: { $seconds }
gg-raid-status = Zaštita od masovnog pristupanja. /antiraid on uključuje; /antiraid off zaustavlja. Period, trajanje blokade i automatski prag u minuti su ispod.
    Aktivno: { $active }
    Automatski prag: { $auto }
    Trajanje blokade: { $ban }
    Period: { $period }
    Do: { $until }
gg-raid-banned = 🛡 Član privremeno blokiran tokom aktivne zaštite od masovnog pristupanja.
    Član: { $user }
gg-raid-declined = 🛡 Zahtev odbijen tokom aktivne zaštite od masovnog pristupanja.
    Član: { $user }
gg-silent-consent-required = Osnivač mora dozvoliti tihe radnje i podesiti dnevnik pre izbora ove radnje.
gg-btn-enable-raid = Uključi zaštitu od masovnog pristupanja
gg-human-required = Ova radnja zahteva identifikovanog čoveka.
gg-group-message-required = Koristite komandu uz stvarnu grupnu poruku ili temu. ID privatne poruke nije ID grupne poruke.
gg-connection-private = Koristite ovu komandu povezivanja u našem privatnom razgovoru.
gg-connection-disconnected = Veza prekinuta. Poslednjih pet grupa ostaju za ponovno povezivanje.
gg-connection-current = Grupa povezana. Članstvo i trenutna prava proveravaju se pri svakoj radnji.
    Grupa: { $group }
gg-connection-none = Nema aktivne veze. Koristite /connect GROUP_ID ili /connect @grupa.
gg-connection-open = Otvorite ličnu vezu u našem privatnom razgovoru.
gg-btn-connect = Poveži privatno
gg-connection-history = Poslednjih pet grupa. Izaberite jednu; potrebno je trenutno članstvo.
gg-connection-unavailable = Veza nije dostupna. Morate biti trenutni ljudski član, a bot administrator te grupe.
gg-catalog-unresolved = /{ $command } je ime iz kataloga bez definisane radnje. Koristite /notes ili /flood za implementirane funkcije.
gg-cleanup-failed = Čišćenje poruka nije uspelo ili nije dostupno; brisanje se ne tvrdi.
gg-op-lock_change = promeni zabrane sadržaja
gg-op-allowlist_change = promeni izuzetke
gg-op-allowlist_clear = obriši izuzetke
gg-op-blocklist_change = promeni listu zabrana
gg-op-blocklist_clear = isprazni listu zabrana
gg-op-raid_change = promeni zaštitu masovnog pristupanja
gg-disabled-list = Politika komandi: /disable IME i /enable IME upravljaju izvršavanjem; /disabledel brisanjem; /disableadmin uključuje administratore.
    Komande: { $commands }
gg-cleanup-types = Dostupne kategorije čišćenja:
    Tipovi: { $types }
gg-cleanup-selected = Izabrane kategorije čišćenja:
    Tipovi: { $types }
gg-advanced-status = Tiha automatizacija zahteva saglasnost osnivača i dnevnik. Botovi zahtevaju normalna prava; provera promena je podrazumevano uključena. Podesite vidljivost među botovima u BotFather.
    Podešavanje: { $setting }
    Vrednost: { $value }
gg-action-topic = Tema radnji. /setactiontopic bira trenutnu forumsku temu; opšta tema ima ID 1.
    Tema: { $topic }
gg-topic-unavailable = Potreban je trenutni forum i odgovarajuća prava upravljanja.
gg-topic-id-required = U povezanom privatnom razgovoru jasno navedite ID teme.
gg-topic-general-delete = Opšta tema se ne može obrisati. Potvrda zahteva identifikovanog čoveka.
gg-topic-delete-confirm = Obrisati temu i poruke? Lična potvrda važi dva minuta.
    Tema: { $topic }
gg-btn-confirm-delete = Potvrdi brisanje
gg-topic-changed = Radnja teme završena.
    Radnja: { $action }
    Tema: { $topic }
gg-op-policy_change = promeni politiku komandi/čišćenja
gg-op-topic_create = napravi temu
gg-op-topic_rename = preimenuj temu
gg-op-topic_close = zatvori temu
gg-op-topic_reopen = ponovo otvori temu
gg-op-topic_delete = obriši temu i poruke
gg-op-echo = pošalji formatirani sadržaj
gg-broadcast-owner = Samo podešeni operator ovog bota ili stvarni vlasnik potomne instance sme pisati njenim grupama.
gg-broadcast-queued = Grupna kampanja u redu. Odredišta i rezultati odvojeni po botu.
    ID: { $id }
gg-broadcast-busy = Druga kampanja je aktivna ili nije prošlo pet minuta od prethodnog kreiranja.
gg-broadcast-empty = Nemate grupnu kampanju u ovom botu.
gg-broadcast-status = Status grupne kampanje:
    Otkazano: { $cancelled }
    Neuspešno: { $failed }
    ID: { $id }
    U redu: { $queued }
    Dostavljeno: { $sent }
    Status: { $status }
    Neizvestan rezultat: { $uncertain }
gg-fed-created = Federacija kreirana. ID pripada odvojenoj mreži ovog bota.
    ID: { $id }
    Ime: { $name }
gg-fed-info = Informacije o federaciji:
    Administratori: { $admins }
    ID: { $id }
    Dnevnik: { $log }
    Ime: { $name }
    Obaveštenja: { $notifications }
    Vlasnik: { $owner }
    Obavezni razlozi: { $reasons }
gg-fed-list = Vaše federacije kao vlasnika ili administratora:
    { $rows }
gg-fed-admins = Prvo vlasnik, zatim administratori federacije:
    { $rows }
gg-fed-quiet = Tiha pasivna objašnjenja. Sprovođenje blokada ostaje aktivno.
    Vrednost: { $value }
gg-fed-policy = Politike razloga i obaveštenja vlasnika:
    Obaveštenja: { $notifications }
    Obavezni razlozi: { $reasons }
gg-fed-confirm-delete = Trajno obrisati federaciju, podatke i članstva? Postojeće Telegram blokade ostaju. Lična potvrda u roku od pet minuta.
    ID: { $id }
    Ime: { $name }
gg-fed-confirm-log = Podesiti navedeni dnevnik federacije? Potvrdite u roku od pet minuta. Vaša prava na odredištu i botovo pravo objavljivanja ponovo se proveravaju.
    Odredište: { $destination }
    ID: { $id }
    Ime: { $name }
gg-fed-confirm-sent = Lična potvrda poslata vlasniku federacije.
gg-fed-deleted = Federacija obrisana. Postojeće Telegram blokade ostaju.
gg-fed-log-set = Odredište dnevnika federacije podešeno:
    Odredište: { $destination }
gg-fed-cancel = Otkaži
gg-fed-cancelled = Otkazano.
gg-fed-saved-delivery-failed = Promena sačuvana, ali obaveštenje ili dnevnik nisu dostavljeni. Proverite odredište i pristup bota.
gg-fed-error-authority = Potreban je trenutni vlasnik federacije ili odgovarajuća uloga. Prava Telegram grupe ne daju prava federacije.
gg-fed-error-private = Koristite komandu u svom privatnom razgovoru sa ovim botom.
gg-fed-error-group = Koristite komandu u stvarnoj grupi. Privatna veza ne bira grupu federacije.
gg-fed-error-owned = Već posedujete federaciju u ovom botu. Koristite /fedinfo, /renamefed ili /delfed privatno.
gg-fed-error-name = Navedite neprazno ime bez kontrolnih znakova. Imena se ograničavaju na 64 znaka.
gg-fed-error-id = Navedite važeći UUID federacije ovog bota. Rose ID-jevi ne povezuju našu odvojenu uslugu.
gg-fed-error-missing = Nije pronađena federacija u ovom botu ili kontekstu.
gg-fed-error-creator = Samo trenutni osnivač Telegram grupe sme priključiti grupu federaciji ili je odvojiti.
gg-fed-error-target = Navedite pozitivan ljudski ID, odgovor čoveku ili trenutno provereno ime. Vlasnik ne može biti smenjen.
gg-fed-error-value = Nevažeći argumenti federacije. Koristite on/off za politike i važeći ID gde je potreban.
gg-fed-error-stale = Potvrda istekla, korišćena ili su federacija, vlasnik ili odredište promenjeni. Zatražite novu.
gg-fed-error-destination = Vlasnik mora trenutno upravljati odredištem, a bot mora moći objavljivati. Kanali zahtevaju post_messages.
gg-fed-error-delivery = Lična potvrda nije dostavljena ili vezana. Otvorite privatni razgovor sa botom i pokušajte ponovo.
gg-fed-event = Događaj federacije:
    Događaj: { $event }
    ID: { $id }
    Ime: { $name }
    Član: { $user }
gg-fed-event-rename = ime promenjeno
gg-fed-event-delete = obrisana; Telegram blokade ostaju
gg-fed-event-promote = administrator dodat
gg-fed-event-demote = administrator uklonjen
gg-fed-event-self-remove = administrator odstupio
gg-fed-event-reason = politika razloga promenjena
gg-fed-event-notif = obaveštenja vlasnika promenjena
gg-fed-event-log = odredište dnevnika promenjeno
gg-fed-event-unlog = odredište dnevnika uklonjeno
gg-fed-event-ban = pravilo blokade sačuvano; sprovođenje u redu
gg-fed-event-unban = pravilo blokade uklonjeno; skidanje sopstvenih ograničenja u redu
gg-fed-event-subscribe = pretplata dodata; provera opaženih korisnika u redu
gg-fed-event-unsubscribe = pretplata uklonjena; drugi izvori ostaju
gg-fed-ban-details = Cilj i razlog blokade:
    Razlog: { $reason }
    Član: { $user }
gg-fed-passive = Pravilo federacije blokira člana. Izvor i razlog su ispod.
    ID: { $id }
    Razlog: { $reason }
    Izvor: { $source }
    Član: { $user }
gg-fed-enforce-failed = Pravilo federacije blokira člana, ali uklanjanje nije uspelo. Proverite prava bota. Izvor i razlog su ispod.
    ID: { $id }
    Razlog: { $reason }
    Izvor: { $source }
    Član: { $user }
gg-fed-stat = Federacijske blokade ovog člana:
    { $rows }
    Član: { $user }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — aktivno: { $status }; promena: { $date }.
gg-fed-stat-more = Postoje dodatni izvori. Koristite komandu za nastavak ili konkretni ID federacije za razlog i datum.
gg-fed-intent-saved = Pravilo sačuvano; opaženi ciljevi u redu. Trenutna prava i drugi izvori ograničenja proveravaju se pre efekata.
    Član: { $user }
    Verzija: { $version }
gg-fed-subscriptions = Direktne pretplate na federacijske blokade:
    { $rows }
gg-fed-imported = Stavke proverene i sačuvane; isti duplikati preskočeni. Sprovođenje kod opaženih ciljeva u redu.
    Broj: { $count }
    Isti duplikati: { $duplicates }
gg-fed-event-import = proverene blokade uvezene; sprovođenje u redu
gg-fed-error-file-format = Odgovorite na UTF-8 CSV sa id/reason, JSONL/NDJSON sa user_id ili JSON niz izvezen ovim botom. Nevažeći red sprečava sve upise.
gg-fed-error-file-limit = Najviše 2 MiB i 1000 stavki. Nedostajući ili preveliki fajlovi se odbijaju; liste se ne skraćuju tiho.
gg-fed-error-file-duplicate = Suprotstavljene stavke za isti ID korisnika. Nema uvezenih blokada.
gg-fed-error-file-rate = Uvoz i izvoz dele period od 30 minuta po federaciji. Pokušajte kasnije.
gg-fed-error-reason = Razlozi blokada imaju najviše 1024 znaka bez nepodržanih kontrolnih znakova.
gg-fed-error-reason_required = Ova federacija zahteva neprazan razlog za svaku blokadu.
gg-fed-error-cycle = Federacija ne sme pretplatiti samu sebe niti stvoriti usmereni ciklus.
gg-fed-error-graph_limit = Limit dostignut: 32 direktna odredišta, 128 dostižnih federacija, dubina 16 ili 10 000 veza ovog bota.
gg-data-confirm = Potvrdite u roku od pet minuta. Trenutni osnivač i revizija grupe ponovo se proveravaju. Menjaju se samo izabrani moduli; identitet, poverenje i aktivne blokade ostaju.
    SHA-256: { $digest }
    Grupa: { $group }
    Moduli: { $modules }
    Operacija: { $operation }
gg-data-import = Uvezi module grupe
gg-data-reset = Resetuj module grupe
gg-data-privacy-delete = Obriši neobavezne lične podatke ovog bota
gg-data-confirm-button = Potvrdi ovu promenu
gg-data-personal = Otvorite potvrdu u privatnom razgovoru.
gg-data-saved = Izabrani moduli sačuvani.
gg-data-error-authority = Uvoz i resetovanje zahtevaju trenutnog identifikovanog osnivača grupe. Izvoz zahteva trenutnog administratora.
gg-data-error-format = Odgovorite na važeći verzionisani Group Guard JSON napravljen sa /export.
gg-data-error-limit = Fajl prelazi limit veličine ili podešenog sadržaja.
gg-data-error-version = Šema ili verzija nisu podržane; ništa nije promenjeno.
gg-data-error-module = Izaberite poznate module: /export all ili /export notes rules. Uvoz i resetovanje koriste ista imena.
gg-data-error-field = Nevažeća ili nedostajuća polja modula. Podešavanja nisu primenjena.
gg-data-error-item = Sadržaj, opcije ili pristup ponavljanju nevažeći. Sadržaj nije sačuvan.
gg-data-error-media = Mediji moraju biti poslati ovom botu i dostupni preko getFile. ID-jevi fajlova drugih botova nisu podržani.
gg-data-error-destination = Odredišta dnevnika i tema zahtevaju trenutna prava i mogućnosti bota. ID-jevi tema važe samo u istoj grupi.
gg-data-error-language = Izaberite instalirani jezik sa /setlang.
gg-data-error-stale = Potvrda istekla, promenjena ili iskorišćena. Počnite ponovo.
gg-data-error-restore = Sopstvena privremena ograničenja nisu mogla bezbedno biti vraćena. Dokazi ostaju; proverite prava bota.
gg-data-error-rate = Operacije grupnih podataka imaju lokalni razmak od pet minuta. Pokušajte kasnije.
gg-data-error-delivery = Privatna potvrda nije dostavljena. Otvorite privatni razgovor sa botom i pokušajte ponovo.
gg-data-error-saved_delivery = Podešavanja sačuvana, ali predlozi komandi nisu ažurirani. Proverite prava bota.
gg-privacy-policy = <b>Vaši podaci u ovom Group Guardu</b>
    /privacy data izvozi veze, opažene profile, upozorenja, odobrenja, status ograničenja/provera, vlasništvo/uloge/blokade federacije i bezbednosne zadatke. Tuđi privatni sadržaj, odgovori provera, autentifikacija i sirovi fajlovi nisu uključeni. Pratite komandu za nastavak.
    /privacy delete uklanja neobaveznu istoriju veza, opaženo ime/korisničko ime, neaktivne provere i sadržaj vaših završenih kampanja ovog bota. Aktivna upozorenja/ograničenja, verzije blokada, uloge, vlasništvo, pretplate, zaštita od ponavljanja i neizvesni API zadaci zadržavaju minimalne identifikatore bezbednosti i redosleda. Koristite izričite komande izlaska/brisanja federacije za te odnose. Zajednički profil platforme i drugi botovi ostaju.
    Operatori odvojeno upravljaju rezervnim kopijama i revizijom. Komanda ne briše spoljne Telegram poruke ili rezervne kopije i ne obećava automatski rok čuvanja.
gg-privacy-usage = /privacy policy · /privacy data [nastavak] · /privacy delete — samo u svom privatnom razgovoru sa ovim botom.
gg-privacy-private = Potreban je privatni razgovor čoveka koji traži podatke. Nevažeći kursori ne daju pristup tuđim podacima.
gg-privacy-next = Sledeća stranica podataka: /privacy data { $cursor }
gg-privacy-deleted = Neobavezni lični podaci ovog bota uklonjeni. Aktivna bezbednost, vlasništvo i neizvesni poslovi zadržavaju minimalne identifikatore; vidite /privacy policy.
gg-language-usage = Izaberite jezik grupe sa /setlang. /lang privatno menja lični jezik platforme. Dostupni kodovi su ispod.
    Kodovi jezika: { $codes }
gg-language-saved = Jezik grupnih odgovora promenjen.
gg-help-index = <b>Vodič komandi Group Guard</b>
    /help oblast · /help komanda · /help oblast 2. Navedene komande rade i preko proverenog /connect; privatni odgovori ostaju u stvarnom privatnom razgovoru.
    Podešavanja zahtevaju menjanje informacija; kazne ograničavanje članova; brisanje prava brisanja; zakačivanje prava zakačivanja; imenovanja prava postavljanja administratora; teme prava upravljanja temama. Prava bota proveravaju se posebno. Vlasničke radnje zahtevaju trenutnog ljudskog osnivača. /settings otvara lični panel grupe.
gg-help-search = <b>Odgovarajuće komande</b>
    Pretraga: { $query }
gg-help-connected = Grupa ili proverena veza; prava u oblasti
gg-help-group-only = Potrebna je stvarna grupna poruka
gg-help-unsupported = Ime kataloga zadržano; nedefinisano ponašanje daje objašnjenje
gg-help-next = Sledeća stranica
gg-help-previous = Prethodna stranica
gg-help-family-title-moderation = Moderacija i odobrenja
gg-help-family-title-messages = Brisanje i zakačivanje poruka
gg-help-family-title-logging = Ovlašćeni dnevnici
gg-help-family-title-settings = Podešavanja i jezik grupe
gg-help-family-title-content = Beleške, filteri, pravila i pozdravi
gg-help-family-title-captcha = Provera novih članova
gg-help-family-title-locks = Zabrane sadržaja i izuzeci
gg-help-family-title-blocklists = Poklapanje liste zabrana i radnje
gg-help-family-title-antispam = Zaštita od previše poruka i masovnog pristupanja
gg-help-family-title-connections = Privatne veze sa grupama
gg-help-family-title-identity = Informacije o korisnicima i razgovorima
gg-help-family-title-policy = Politika komandi i botova
gg-help-family-title-cleanup = Čišćenje komandi, botova i usluga
gg-help-family-title-topics = Forumske teme
gg-help-family-title-utilities = Slanje sadržaja i kampanje operatora
gg-help-family-title-federations = Uloge, blokade i pretplate federacije
gg-help-family-title-portability = Grupni fajlovi i lični podaci
gg-help-family-title-discovery = Pomoć i uređivač sadržaja
gg-help-family-moderation = <b>Moderacija</b> · Odgovor, brojčani ID ili provereni @korisnik. /ban 20 razlog; /tban 20 60s razlog; /mute 20; /tmute 20 2h razlog. Trajanje: 60 sekundi–365 dana. /kickme uklanja samo vas. Varijante d brišu odgovorenu poruku; s brišu komandu/odgovor i zahtevaju brisanje. Administratori zaštićeni. /setwarnlimit 3; /setwarnmode ban; /setwarntime 1d. Nove grupe tri upozorenja; stara podešavanja ostaju. /approve izuzima samo običnu zaštitu sadržaja/poruka, ne federaciju/CAS/masovni pristup/ručne radnje. /promote ne prelazi zajednička prava podnosioca i bota. Masovni reset zahteva osnivača.
gg-help-family-messages = <b>Poruke</b> · /del zahteva stvarni odgovor u grupi. /purge počinje tu; /purgefrom i /purgeto čuvaju granice. Važe podešeni limiti i Telegram pravila; potvrda grupe zahteva nije tačan broj brisanja. /pin [loud], /permapin, /unpin, /unpinall zahtevaju zakačivanje; uklanjanje svih zahteva osnivača. /antichannelpin i /cleanlinked upravljaju automatskim porukama povezanog kanala.
gg-help-family-logging = <b>Dnevnici</b> · /setlog -100… zahteva trenutno upravljanje odredištem i objavljivanje bota. Prosleđeno podešavanje mora odgovarati zaista primljenom originalu. /logcategories: settings/admin/user/automated/reports/other; /log i /nolog biraju kategorije. Greške dostave ostaju vidljive i ne dokazuju uspeh radnje.
gg-help-family-settings = <b>Podešavanja</b> · /settings otvara lični panel sa rokom i trenutnom proverom menjanja informacija. /setlang kod čuva jezik grupe; /lang privatno lični jezik. /night 23 7 +3 zatvara noću; /night off vraća samo sopstveno još odgovarajuće stanje prava. Spoljne promene imaju prednost.
gg-help-family-content = <b>Uređivač</b> · /save reč tekst ili odgovor na medije; /get reč, #reč, /notes čitaju beleške. Nova imena jedna reč; stara šira imena ostaju. /filter "fraza" tekst, /filterprefix, /filterexact biraju poklapanje; /stop uklanja ključ. /clearall i /stopall zahtevaju potvrdu osnivača. Rose format: podebljano/kurziv/podvučeno/precrtano/kod, linkovi, citati i nasumične %%% alternative. Polja: { "{" }first{ "}" }, { "{" }last{ "}" }, { "{" }fullname{ "}" }, { "{" }username{ "}" }, { "{" }mention{ "}" }, { "{" }id{ "}" }, { "{" }chatname{ "}" }, { "{" }count{ "}" }. /button pravi URL/beleška/pravila dugmad. Opšte opcije preview/nonotif/protect/mediaspoiler; beleške admin/private/noprivate/repeat; filteri user/allow_bot/replytag/command. /save reč Zdravo { "{" }repeat 5m{ "}" } zakazuje samo javni sadržaj sa trenutnim pravima autora. Pravila, pozdravi i privatni sadržaj dele prikaz. ID-jevi medija pripadaju botu.
gg-help-family-captcha = <b>Provera</b> · /captcha on/off; /captchamode off/button/math/text/text2; /setcaptchatext; /captcharules on; /captchakick on/off; /captchakicktime i /captchamutetime postavljaju ograničene rokove. Izdate provere zadržavaju generaciju/rok. Zahtevi traže invite-users; utišavanje restrict-members. Odgovori lični i jednokratni. Federacijske blokade pre odobrenja/CAPTCHA.
gg-help-family-locks = <b>Zabrane</b> · /lock links [radnja], /unlock tip; /locktypes prikazuje stvarne tipove, /locks stanje. /lockwarns upravlja upozorenjima. /allowlist: domen/putanja, tačan poziv, @razgovor ili stickerpack:/forward:/inline:/channel:/chat:/bot:/command:. Nevažeći obrasci odbijeni. Izuzeci samo za odgovarajući sadržaj; tiha automatizacija zahteva osnivača i ovlašćeni dnevnik.
gg-help-family-blocklists = <b>Lista zabrana</b> · /addblocklist "fraza" podržava tekst/prefiks/tačno poklapanje i navedene identitete sa opcionim razlogom/radnjom. /rmblocklist uklanja tačno izabrane ključeve. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute bira radnju; privremeni režimi zahtevaju trajanje. /blocklistdelete odvojeno upravlja brisanjem. Džoker obrasci ograničeni; nevažeće stavke i prekoračenja odbijeni.
gg-help-family-antispam = <b>Poruke i masovni pristup</b> · /setflood broj za uzastopne poruke; /setfloodtimer broj trajanje za vremenski prozor; /setfloodmode kazna/trajanje; /clearflood čišćenje niza. Stara podešavanja ostaju. /flood i /antiflood prikazuju politiku; alias je lokalna odluka kompatibilnosti. /antiraid on/off/duration, /raidtime, /raidactiontime, /autoantiraid čuvaju rok i odvojenu kaznu za novopridošle. Prednost nad odobrenjem/CAPTCHA; generacijski istek otporan na restart.
gg-help-family-connections = <b>Veze</b> · /connect groupID ili lični link. Proverava se vaše i botovo članstvo; promene i dalje zahtevaju precizna trenutna prava. /connection pokazuje izbor, /disconnect uklanja, /connect pokazuje istoriju sa nastavkom. Veza ne daje vlasništvo federacije ili prava operatora.
gg-help-family-identity = <b>Informacije</b> · /id pokazuje stvarne ID-jeve korisnika/razgovora/izvora; /info trenutni cilj. Odgovori i @imena zahtevaju trenutne dokaze ovog bota. Anonimne grupne poruke ne identifikuju čoveka; ne izmišlja se ljudski ID.
gg-help-family-policy = <b>Politike</b> · /disable komanda, /enable komanda, /disabled, /disableable koriste kanonska imena i aliase. /disableadmin kontroliše izuzetke administratora; /disabledel brisanje. Komande oporavka ostaju dostupne. /bot2bot off/admin/all proverava stvarno članstvo; promene podrazumevano pregleda čovek. /bot2botskipreview samo osnivač. /silentactions zahteva saglasnost i ovlašćeni dnevnik. Nedefinisani runs/saved daju objašnjenje.
gg-help-family-cleanup = <b>Čišćenje</b> · /cleancommand admin/user/other i /keepcommand biraju komande. /cleanmsg action/filter/note i /keepmsg samo poruke stvarno poslate ovim botom; potvrde i zadaci posle pet minuta sprečavaju pogađanje ID-ja. /cleanservice i /nocleanservice: join/leave/other/photo/pin/title/videochat. Funkcionalna obrada i važeća plaćanja pre čišćenja.
gg-help-family-topics = <b>Teme</b> · /newtopic ime, /renametopic ime, /closetopic, /reopentopic rade u stvarnoj trenutnoj temi. /deletetopic zahteva potvrdu osnivača; /setactiontopic bira odredište iste grupe. Telegram forum i manage-topics potrebni. Nedostajuće/nepodržane teme daju stvarne greške.
gg-help-family-utilities = <b>Alati</b> · /echo i /say šalju direktni ili odgovoreni sadržaj kroz zajednički ograničeni prikaz. /broadcast samo podešeni operator ili stvarni vlasnik potomka; samo podešene grupe ovog bota. Rezultati po odredištu čuvaju delimične/neizvesne dostave; status i otkazivanje ne ponavljaju uspešne priloge.
gg-help-family-federations = <b>Federacije</b> · /newfed ime pravi UUID u ovom botu. Privatne komande koriste vašu federaciju bez obzira na veze; čitanje UUID-ja ne daje ulogu. /fedpromote i /feddemote upravljaju administratorima, /feddemoteme odstupa. /joinfed UUID i /leavefed zahtevaju trenutnog osnivača grupe. Brisanje ne skida Telegram blokade. /fban userID razlog i /unfban userID zahtevaju vlasnika/administratora federacije; /fedreason, /fednotif, /setfedlog vlasnika. /quietfed krije samo pasivna objašnjenja. /subfed UUID usmeren, ograničen, bez ciklusa. /fedstat [userID], /fbanstat UUID pokazuju izvore/status. /fbanlist csv/minicsv/json samo vlasnik sa zajedničkim razmakom 30 minuta; /importfbans odgovara na ograničeni CSV ili pravi JSON po redu i izričito podržava svoj JSON niz. Proveravaju se samo opaženi korisnici; ne tvrdi se potpun spisak članova.
gg-help-family-portability = <b>Fajlovi i privatnost</b> · /export all ili moduli zahteva administratora; /import i /reset trenutnog ljudskog osnivača sa ličnom jednokratnom potvrdom pet minuta. Lokalni razmak pet minuta; sopstveni verzionisani JSON, najviše 2MiB i podešeni limiti. Moduli: moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Neizabrani moduli ostaju. Poverenje, izdate provere/zadaci, pretplate, uloge i aktivne blokade nikad se ne uvoze. /privacy policy/data/delete samo sopstveni privatni razgovor sa stranicama i minimalnim bezbednosnim čuvanjem. Nema proverenog adaptera punog Rose izvoza.
gg-help-family-discovery = <b>Pomoć</b> · /help pokazuje oblasti; /help komanda traži imena/aliase; /help oblast 2 nastavlja. /button pomaže sa oznakama dugmadi. Svaki vodič opisuje kontekst, prava, podrazumevane vrednosti i limite. /settings otvara lični panel grupe.
gg-data-error-cache_pending = Neobavezni SQL podaci uklonjeni. Čišćenje nedostupnog keša je u redu; aktivni bezbednosni podaci ostaju.
