## Independently authored Group Guard nl content.
group-welcome = 🛡 Bedankt voor het toevoegen! Geef me beheerdersrechten om berichten te verwijderen, leden te beperken en berichten vast te zetten. Gebruik /settings voor instellingen.
gg-start = 🛡 Hallo <b>{ $name }</b>! Ik ben <b>Group Guard</b>: verificatie van nieuwe leden, bescherming tegen berichtenstromen en CAS, inhoudsblokkades, moderatie, notities, filters, regels en begroetingen. Voeg me toe als beheerder en gebruik /settings of /help.
gg-help = 📖 /help toont onderdelen; /help commando zoekt commando's. Moderatie: /ban /mute /kick /warn. Inhoud: /save /filter /rules. Bescherming: /lock /blocklist /night. /settings opent je persoonlijke groepspaneel.
gg-welcome-default = 👋 Welkom { "{" }mention{ "}" } in <b>{ "{" }group{ "}" }</b>!
gg-credit = 🛡 Beschermd door @{ $bot }
gg-btn-add = ➕ Toevoegen aan een groep
gg-btn-commands = 📖 Commando's
gg-btn-rules = 📜 Regels
gg-btn-human = ✅ Ik ben een mens
gg-btn-unwarn = ↩️ Waarschuwing verwijderen (beheerders)
gg-btn-locks = 🔒 Inhoudsblokkades · Aantal: { $count }
gg-btn-open-settings = ⚙️ Instellingen openen
gg-btn-admin-tab = 🛡 Groepen
gg-captcha = 🤖 Bevestig binnen de aangegeven termijn dat je een mens bent, anders word je verwijderd.
    Minuten: { $minutes }
    Lid: { $user }
gg-captcha-button = Druk op de knop hieronder 👇
gg-captcha-math = Hoeveel is <b>{ $a } + { $b }</b>?
gg-captcha-not-you = Deze knop is voor iemand anders.
gg-captcha-ok = ✅ Welkom!
gg-captcha-wrong = ❌ Fout antwoord. Je kunt opnieuw proberen zolang er pogingen over zijn.
    Resterende pogingen: { $left }
gg-captcha-failed = ❌ Te veel foute antwoorden.
gg-captcha-passed = ✅ Verificatie geslaagd. Welkom!
    Lid: { $user }
gg-cas-banned = 🚫 Het lid staat bij CAS bekend als spammer en is verbannen.
    Lid: { $user }
gg-join-request = 👋 Bevestig dat je een mens bent om lid te worden:
    Groep: { $group }
gg-join-approved = ✅ Verzoek goedgekeurd. Welkom!
gg-join-expired = ⌛ Dit verzoek is verlopen. Dien een nieuw toetredingsverzoek in.
gg-goodbye = 👋 Het lid heeft de groep verlaten.
    Lid: { $user }
gg-flood-mute = 🌊 Het lid is tijdelijk gedempt wegens te veel berichten.
    Lid: { $user }
gg-flood-kick = 🌊 Het lid is verwijderd wegens te veel berichten.
    Lid: { $user }
gg-flood-ban = 🌊 Het lid is verbannen wegens te veel berichten.
    Lid: { $user }
gg-newbie-links = 🆕 Nieuwe leden mogen de aangegeven eerste uren geen links sturen.
    Uren: { $hours }
    Lid: { $user }
gg-spam-banned = 🧠 Het lid is wegens spam verbannen.
    Lid: { $user }
gg-reason-blocklist = geblokkeerd woord
gg-need-right = ⛔ Hiervoor heb je het juiste beheerdersrecht nodig.
    Recht: { $right }
gg-right-admin = beheerder
gg-right-restrict = leden beperken
gg-right-delete = berichten verwijderen
gg-right-pin = berichten vastzetten
gg-right-change_info = groepsinformatie wijzigen
gg-admins-only = ⛔ Alleen voor beheerders.
gg-need-target = 👤 Antwoord op een bericht of geef een ID of een momenteel geverifieerde @gebruikersnaam op.
gg-target-admin = 🙅 Deze actie mag geen beheerder treffen.
gg-bot-no-rights = ⚠️ Ik moet beheerder zijn met de benodigde rechten.
gg-banned = 🔨 Het lid is verbannen.
    Reden: { $reason }
    Lid: { $user }
gg-banned-for = 🔨 Het lid is voor de aangegeven tijd verbannen.
    Reden: { $reason }
    Tijd: { $time }
    Lid: { $user }
gg-unbanned = ✅ Verbanning van het lid opgeheven.
    Lid: { $user }
gg-kicked = 👢 Het lid is verwijderd en mag opnieuw toetreden.
    Reden: { $reason }
    Lid: { $user }
gg-muted = 🔇 Het lid is gedempt.
    Reden: { $reason }
    Lid: { $user }
gg-muted-for = 🔇 Het lid is voor de aangegeven tijd gedempt.
    Reden: { $reason }
    Tijd: { $time }
    Lid: { $user }
gg-unmuted = 🔊 Het lid mag weer schrijven.
    Lid: { $user }
gg-warned = ⚠️ Waarschuwing voor het lid geregistreerd.
    Aantal: { $count }
    Limiet: { $limit }
    Reden: { $reason }
    Lid: { $user }
gg-warn-limit-ban = 🔨 Waarschuwingslimiet bereikt; het lid is verbannen.
    Limiet: { $limit }
    Lid: { $user }
gg-warn-limit-mute = 🔇 Waarschuwingslimiet bereikt; het lid is gedempt.
    Limiet: { $limit }
    Lid: { $user }
gg-warn-limit-kick = 👢 Waarschuwingslimiet bereikt; het lid is verwijderd.
    Limiet: { $limit }
    Lid: { $user }
gg-unwarned = ↩️ Een waarschuwing van het lid is verwijderd.
    Aantal: { $count }
    Limiet: { $limit }
    Lid: { $user }
gg-warn-removed = ↩️ Waarschuwing door een beheerder verwijderd.
    Beheerder: { $admin }
gg-warns = ⚠️ Waarschuwingen van het lid:
    Aantal: { $count }
    Limiet: { $limit }
    Lid: { $user }
gg-warns-reset = 🧽 Waarschuwingen van het lid gewist.
    Lid: { $user }
gg-purge-reply = 🧹 Antwoord op het eerste bericht dat verwijderd moet worden.
gg-purged = 🧹 Berichten verwijderd.
    Aantal: { $count }
gg-pin-reply = 📌 Antwoord op het bericht dat vastgezet moet worden.
gg-report-reply = 🚨 Antwoord op het bericht dat gemeld moet worden.
gg-reported = 🚨 Het lid is bij de beheerders gemeld.
    Lid: { $user }
gg-setlog-usage = 📒 Voeg me toe als kanaalbeheerder en gebruik <code>/setlog -100…</code> met het kanaal-ID.
gg-setlog-failed = ⚠️ Ik kan daar niet schrijven. Voeg me eerst toe als beheerder.
gg-setlog-done = 📒 Logkanaal gekoppeld.
gg-setlog-off = 📒 Logkanaal losgekoppeld.
gg-log-connected = 📒 Deze chat ontvangt het moderatielog van de groep.
    Groep: { $group }
gg-log-flood = 🌊 Overmatige berichtenstroom gedetecteerd:
    Actie: { $action }
    Lid: { $user }
gg-log-report = 🚨 Melding over een lid:
    Lid: { $user }
gg-log-spam = 🧠 Verbanning wegens door AI herkende spam:
    Tekst: { $text }
    Lid: { $user }
gg-rules = 📜 <b>Regels</b>
    { $rules }
gg-no-rules = 📜 Nog geen regels. Beheerders kunnen /setrules tekst gebruiken.
gg-rules-saved = 📜 Regels opgeslagen.
gg-rules-cleared = 📜 Regels verwijderd.
gg-welcome-usage = 👋 Gebruik <code>/setwelcome Hallo {"{"}mention{"}"}, welkom in {"{"}group{"}"}!</code> of antwoord op een bericht.
gg-welcome-saved = 👋 Begroeting opgeslagen.
gg-welcome-reset = 👋 Standaardbegroeting hersteld.
gg-note-usage = 📝 <code>/save naam tekst</code> of antwoord op een bericht met <code>/save naam</code>.
gg-filter-usage = 🔁 <code>/filter woord antwoord</code> of antwoord met <code>/filter woord</code>.
gg-note-saved = 📝 Notitie opgeslagen. Ophalen: <code>#{ $key }</code>, volgens de toegangsrechten.
gg-filter-saved = 🔁 Ik antwoord bij een overeenkomst met “{ $key }”.
gg-notes-empty = 📝 Nog geen notities.
gg-filters-empty = 🔁 Nog geen filters.
gg-notes-list = 📝 <b>Notities</b>
gg-filters-list = 🔁 <b>Filters</b>
gg-item-deleted = 🗑 Item verwijderd.
    Sleutel: { $key }
gg-item-missing = 🤷 Niets onder deze naam opgeslagen.
gg-items-limit = 📦 Limiet voor notities en filters in deze groep bereikt.
gg-lock-usage = 🔒 Gebruik <code>/lock links</code>. Beschikbare typen staan hieronder; <code>all</code> selecteert alle typen.
    Typen: { $types }
gg-locked = 🔒 Geblokkeerde inhoud:
    Typen: { $types }
gg-unlocked = 🔓 Toegestane inhoud:
    Typen: { $types }
gg-locks-title = 🔒 <b>Inhoudsblokkades</b>
gg-locks-panel = 🔒 <b>Blokkades</b>: geblokkeerde inhoud wordt verwijderd; beheerders zijn uitgezonderd.
gg-lock-links = Links
gg-lock-invites = Uitnodigingslinks
gg-lock-forwards = Doorgestuurde berichten
gg-lock-media = Media
gg-lock-stickers = Stickers
gg-lock-gifs = GIFs
gg-lock-voice = Spraakberichten
gg-lock-polls = Peilingen
gg-lock-bots = Bots
gg-blocklist = 🚫 <b>Geblokkeerde woorden</b>
    Woorden: { $words }
gg-blocklist-empty = 🚫 Geen geblokkeerde woorden.
gg-blocklist-usage = 🚫 <code>/addblock woord, andere zin</code> · <code>/rmblock woord</code>
gg-blocklist-saved = 🚫 Blokkeerlijst bijgewerkt.
    Aantal: { $count }
gg-night-usage = 🌙 <code>/night 23 7 +3</code> sluit van 23:00 tot 07:00 UTC+3; <code>/night off</code> schakelt uit.
gg-night-on = 🌙 Nachturen voor de groep ingesteld.
    Einde: { $end }
    Begin: { $start }
    Tijdzone: { $tz }
gg-night-off = 🌙 Nachtmodus uitgeschakeld.
gg-night-start = 🌙 Welterusten! De groep blijft tot de aangegeven tijd gesloten.
    Einde: { $end }
gg-night-end = ☀️ Goedemorgen! De groep is weer open.
gg-panel = ⚙️ <b>Groepsinstellingen</b>
    Druk op een optie om te wijzigen. Nachturen worden ingesteld met /night.
    Groep: { $group }
    Nachturen: { $night }
gg-panel-sent = 📬 Instellingen privé verstuurd.
gg-panel-start-first = 📬 Begin eerst een privéchat met mij en druk daarna hieronder.
gg-credit-vip = 💎 De beschermingsregel verbergen vereist VIP. Gebruik /vip in een privéchat.
gg-opt-wel = 👋 Begroetingen · Waarde: { $value }
gg-opt-cln = 🧹 Toetredingsberichten verwijderen · Waarde: { $value }
gg-opt-bye = 👋 Afscheid · Waarde: { $value }
gg-opt-cap = 🤖 Verificatie · Waarde: { $value }
gg-opt-cpm = ⏱ Verificatietermijn, minuten · Waarde: { $value }
gg-opt-fld = 🌊 Berichtenlimiet · Waarde: { $value }
gg-opt-fla = 🌊 Actie bij te veel berichten · Waarde: { $value }
gg-opt-wrn = ⚠️ Waarschuwingslimiet · Waarde: { $value }
gg-opt-wra = ⚠️ Waarschuwingsactie · Waarde: { $value }
gg-opt-act = ⏳ Automatische beperking, minuten · Waarde: { $value }
gg-opt-cas = 🛡 CAS-bescherming · Waarde: { $value }
gg-opt-nwb = 🆕 Nieuwe leden zonder links, uren · Waarde: { $value }
gg-opt-ais = 🧠 AI-spambescherming · Waarde: { $value }
gg-opt-ngt = 🌙 Nachtmodus · Waarde: { $value }
gg-opt-crd = 🏷 Beschermingsregel · Waarde: { $value }
gg-opt-lang = 🌐 Taal · Waarde: { $value }
gg-val-button = Knop
gg-val-math = Rekensom
gg-val-off = uit
gg-val-mute = dempen
gg-val-kick = verwijderen
gg-val-ban = verbannen
gg-adm = 🛡 <b>Group Guard: statistieken</b>
    Groepen: { $groups }
    Items: { $items }
    Waarschuwingen: { $warns }
cmd-settings = Groepsinstellingen
cmd-help = Commandogids
gg-auth-denied = Autorisatie kon niet worden geverifieerd. Niets gewijzigd.
gg-target-invalid = Kies een bekend menselijk lid. Doel kon niet worden geverifieerd.
gg-duration-invalid = Gebruik een duur van 60s tot 365d. Tijdelijke commando's vereisen een duur.
gg-reason-invalid = De reden mag maximaal 256 tekens bevatten.
gg-outcome-failed = De actie is mislukt of niet geautoriseerd.
gg-outcome-partial = De actie is gedeeltelijk uitgevoerd. Een verbanning kan blijven bestaan als herstel na verwijdering mislukt.
gg-outcome-ancillary = Hoofdactie voltooid, maar een bijbehorende stap is mislukt.
gg-review-request = Controleer de onveranderlijke actie hieronder. Een momenteel bevoegde persoon kan binnen 120 seconden goedkeuren. Duur staat in seconden.
    Details: { $details }
    Duur: { $duration }
    Bewerking: { $operation }
    Doel: { $target }
gg-review-approve = Deze actie goedkeuren
gg-review-unavailable = Bevestigingsopslag niet beschikbaar. Stuur een nieuw commando.
gg-review-expired = Deze bevestiging is verlopen, ongeldig of al gebruikt.
gg-review-consumed = Bevestiging gebruikt. Controleer het resultaat; opnieuw proberen vereist een nieuw commando.
gg-duration-permanent = Permanent / zonder tijdslimiet
gg-purge-ack = De API bevestigde verwijderingsverzoeken. Het werkelijk verwijderde aantal is onbekend.
    Door API bevestigd: { $acknowledged }
    Aangevraagd: { $requested }
gg-warning-removed = Waarschuwing verwijderd.
gg-op-ban = verbannen
gg-op-mute = dempen
gg-op-kick = verwijderen
gg-op-unban = verbanning opheffen
gg-op-unmute = demping opheffen
gg-op-warn = waarschuwen
gg-op-unwarn = waarschuwing verwijderen
gg-op-resetwarns = waarschuwingen wissen
gg-op-purge = berichtenbereik verwijderen
gg-op-delete = bericht verwijderen
gg-op-pin = bericht vastzetten
gg-op-unpin = bericht losmaken
gg-op-setlog = logbestemming instellen
gg-op-unsetlog = logbestemming verwijderen
gg-op-config = instellingen wijzigen
gg-op-save = inhoud opslaan
gg-op-remove = inhoud verwijderen
gg-op-panel = paneel openen
gg-review-details-above = De volledige gevraagde inhoud staat in het bericht direct hierboven.
gg-warn-pending = Waarschuwing opgeslagen; de actie bij de limiet wordt al verwerkt.
gg-done = Voltooid.
gg-setting-saved = Instelling opgeslagen.
    Instelling: { $setting }
gg-setting-value = Huidige instellingswaarde:
    Instelling: { $setting }
    Waarde: { $value }
gg-setting-invalid = Ongeldige instelling. Gebruik on/off, een geldige modus of een duur zoals 10m.
gg-warning-settings = Waarschuwingsinstellingen:
    Duur: { $duration }
    Vervaldatum: { $expiry }
    Limiet: { $limit }
    Modus: { $mode }
gg-admin-changed = Beheerdersactie voltooid.
    Actie: { $action }
    Lid: { $user }
gg-admin-list = Openbare beheerders:
    { $admins }
gg-approved = Lid goedgekeurd.
    Reden: { $reason }
    Lid: { $user }
gg-unapproved = Goedkeuringen verwijderd.
    Aantal: { $count }
gg-approval-status = Goedkeuringsstatus van het lid:
    Reden: { $reason }
    Status: { $status }
    Lid: { $user }
gg-approval-list = Goedgekeurde leden:
    { $approvals }
gg-next-page = Meer items: { $command }
gg-range-invalid = Ongeldig bereik. Kies minstens één bericht en blijf binnen de aangegeven limiet.
    Maximum: { $cap }
gg-range-start = Beginpunt voor jou in dit onderwerp tien minuten opgeslagen. Antwoord op het laatste bericht met /purgeto.
gg-range-missing = Hier geen beginpunt voor jou opgeslagen. Gebruik eerst /purgefrom als antwoord.
gg-content-needed = Geef inhoud op of antwoord erop; maximaal 3500 tekens.
gg-log-status = Loginstellingen:
    Categorieën: { $categories }
    Bestemming: { $destination }
gg-log-unverified = Ik heb geen geverifieerde ontvangst van dit oorspronkelijke kanaalcommando. Stuur eerst /setlog in het kanaal.
gg-log-forward = Stuur dit oorspronkelijke /setlog door naar de groep. De koppelende beheerder moet informatie in beide chats mogen wijzigen.
gg-info = Informatie over gebruiker of chat:
    ID: { $id }
    Lidmaatschap: { $membership }
    Naam: { $name }
    Gebruikersnaam: { $username }
gg-op-unpinall = alle berichten losmaken
gg-op-permapin = permanent vastzetten
gg-op-promote = beheerder aanstellen
gg-op-demote = beheerder afzetten
gg-op-approve_user = gebruiker goedkeuren
gg-op-unapprove = goedkeuring verwijderen
gg-op-unapproveall = alle goedkeuringen verwijderen
gg-unknown = Onbekend
gg-chat-id = Chat-ID:
    ID: { $id }
gg-on = Aan
gg-off = Uit
gg-anon-enabled = Vertrouwen in anonieme beheerders is hier actief. Anonieme commando's van deze groep gebruiken botrechten zonder een persoon te identificeren. Eigenaarsacties vereisen nog steeds de geverifieerde maker. /anonadmin off herstelt menselijke beoordeling.
gg-right-invite_users = gebruikers uitnodigen
gg-right-promote_members = beheerders aanstellen
gg-right-manage_topics = onderwerpen beheren
gg-right-creator = groepsmaker
gg-log-join = Lid toegetreden.
    Lid: { $user }
gg-log-leave = Lid vertrokken.
    Lid: { $user }
gg-warning-row = Waarschuwingsregistratie:
    Vervaldatum: { $expiry }
    ID: { $id }
    Reden: { $reason }
gg-menu-prompt = Kies een optie.
gg-content-invalid = Inhoud ongeldig of boven Telegram-limieten. Controleer naam, opmaak, modifiers en knoppen.
gg-content-unavailable = Inhoud niet beschikbaar of je huidige groepslidmaatschap geeft geen toegang.
gg-btn-private-note = Notitie openen
gg-open-private = Deze inhoud privé openen:
gg-items-cleared = Items verwijderd.
    Aantal: { $count }
gg-clearall-confirm = De groepsmaker bevestigt met <code>/{ $command } confirm</code>.
gg-button-usage = Gebruik <code>/button "Label" https://example.com</code>. Voeg <code>"Notitie" #naam same</code> toe voor nog een knop op dezelfde rij. Je krijgt opmaak en een werkend voorbeeld.
gg-btn-accept-rules = Regels accepteren
gg-btn-open-verification = Verificatie openen
gg-captcha-private = Open de privéverificatie om je groepslidmaatschap te bevestigen.
    Lid: { $user }
gg-captcha-choice = Kies de juiste afbeelding met de knoppen. Modus en tekenpositie staan hieronder.
    Modus: { $mode }
    Positie: { $position }
gg-captcha-settings = Verificatie-instellingen:
    Actief: { $enabled }
    Verwijdering: { $kick }
    Modus: { $mode }
    Opheffing: { $release }
    Seconden: { $seconds }
gg-captcha-dependency = Activeer begroetingen vóór verificatie. Sla regels op voordat je aanvaarding vereist.
gg-val-text = Tekstafbeelding
gg-val-text2 = Tekenafbeelding
gg-captcha-attempts-exhausted = Verificatie mislukt na te veel foute antwoorden; de vastgestelde beperking is toegepast.
gg-captcha-admin-exempt = Je bent nu groepsbeheerder. Verificatie beëindigd.
gg-captcha-question-text = Kies het woord in de afbeelding.
gg-captcha-question-math = Los de vergelijking in de afbeelding op en kies het antwoord.
gg-captcha-question-text2 = Kies het aangegeven teken in de afbeelding, van links naar rechts.
    Positie: { $position }
gg-locktypes = Beschikbare inhoudsblokkades:
    Typen: { $types }
gg-allowlist-title = Uitzonderingen op inhoudsblokkades
gg-allowlist-invalid = Ongeldige uitzondering. Gebruik domein/pad, exacte uitnodiging, @chat of een opgegeven identiteit zoals stickerpack:naam.
gg-reason-lock = Geblokkeerde inhoud:
    Typen: { $types }
gg-lock-applied = Blokkaderegel toegepast.
    Reden: { $reason }
    Typen: { $types }
gg-reaction-failed = Reactieregel kon niet worden toegepast. Deze Bot API-server ondersteunt mogelijk geen reactieverwijdering.
    Code: { $code }
gg-reaction-anonymous = Anonieme tellingen bevatten geen gebruiker-ID of afzenderchat-ID. De verwijderings-API vereist dit; verwijdering wordt niet geclaimd.
gg-none = Geen
gg-blocklist-title = Blokkeerlijst
gg-blocklist-invalid = Ongeldige trigger, reden of actie. Controleer aanhalingstekens, escapes voor wildcards en vereiste duur voor tijdelijke modi.
gg-blocklist-settings = Blokkeerlijstinstellingen:
    Verwijdering: { $delete }
    Modus: { $mode }
gg-blocklist-action = Blokkeerlijstregel op het lid toegepast.
    Reden: { $reason }
    Lid: { $user }
gg-lock-album = Albums
gg-lock-anonchannel = Kanaalafzenders
gg-lock-audio = Audio
gg-lock-bot = Bots
gg-lock-button = Inlineknoppen
gg-lock-cashtag = Valutamarkeringen
gg-lock-checklist = Controlelijsten
gg-lock-cjk = Chinese/Japanse/Koreaanse tekst
gg-lock-command = Commando's
gg-lock-comment = Reacties van niet-leden
gg-lock-contact = Contacten
gg-lock-cyrillic = Cyrillische tekst
gg-lock-document = Documenten
gg-lock-email = E-mailadressen
gg-lock-emoji = Emoji
gg-lock-emojicustom = Aangepaste emoji
gg-lock-emojigame = Emojispellen
gg-lock-emojionly = Alleen emoji
gg-lock-externalreply = Externe antwoorden
gg-lock-forward = Doorgestuurde berichten
gg-lock-forwarduser = Doorgestuurd van gebruikers
gg-lock-forwardbot = Doorgestuurd van bots
gg-lock-forwardchannel = Doorgestuurd van kanalen
gg-lock-forwardstory = Doorgestuurde verhalen
gg-lock-game = Spellen
gg-lock-gif = GIF-animaties
gg-lock-guestbot = Gastbots
gg-lock-inline = Inlinebots
gg-lock-invitelink = Telegram-uitnodigingen
gg-lock-botlink = Botlinks
gg-lock-location = Locaties
gg-lock-outsidereaction = Reacties van buitenstaanders
gg-lock-phone = Telefoonnummers
gg-lock-photo = Foto's
gg-lock-poll = Peilingen
gg-lock-reaction = Reacties
gg-lock-rtl = Tekst van rechts naar links
gg-lock-spoiler = Verborgen inhoud
gg-lock-sticker = Stickers
gg-lock-stickeranimated = Geanimeerde stickers
gg-lock-stickerpremium = Premiumstickers
gg-lock-text = Tekst
gg-lock-url = URLs
gg-lock-video = Video's
gg-lock-videonote = Videoberichten
gg-flood-status = Berichtenstroom: opeenvolgende limiet bij N; tijdvenster boven N. Actie, duur en opschoning van de reeks staan hieronder.
    Hele reeks opschonen: { $clear }
    Opeenvolgende limiet: { $consecutive }
    Aantal: { $count }
    Duur: { $duration }
    Modus: { $mode }
    Seconden: { $seconds }
gg-raid-status = Bescherming tegen massale toetreding. /antiraid on activeert; /antiraid off stopt. Periode, verbanningsduur en automatische limiet per minuut staan hieronder.
    Actief: { $active }
    Automatische limiet: { $auto }
    Verbanningsduur: { $ban }
    Periode: { $period }
    Tot: { $until }
gg-raid-banned = 🛡 Lid tijdelijk verbannen tijdens actieve bescherming tegen massale toetreding.
    Lid: { $user }
gg-raid-declined = 🛡 Verzoek afgewezen tijdens actieve bescherming tegen massale toetreding.
    Lid: { $user }
gg-silent-consent-required = De maker moet stille acties toestaan en een log instellen voordat deze actie wordt gekozen.
gg-btn-enable-raid = Bescherming tegen massale toetreding activeren
gg-human-required = Deze actie vereist een identificeerbaar mens.
gg-group-message-required = Gebruik dit commando bij een echt groepsbericht of onderwerp. Privébericht-ID's verwijzen niet naar groepsberichten.
gg-connection-private = Gebruik dit koppelcommando in onze privéchat.
gg-connection-disconnected = Losgekoppeld. Je laatste vijf groepen blijven beschikbaar om opnieuw te koppelen.
gg-connection-current = Groep gekoppeld. Lidmaatschap en huidige rechten worden bij elke actie gecontroleerd.
    Groep: { $group }
gg-connection-none = Geen actieve koppeling. Gebruik /connect GROUP_ID of /connect @groep.
gg-connection-open = Open je persoonlijke koppeling in onze privéchat.
gg-btn-connect = Privé koppelen
gg-connection-history = Je laatste vijf groepen. Kies er een; huidig lidmaatschap vereist.
gg-connection-unavailable = Koppeling niet beschikbaar. Je moet een huidig menselijk lid zijn en de bot een beheerder daar.
gg-catalog-unresolved = /{ $command } staat in de catalogus zonder gedefinieerde actie. Gebruik /notes of /flood voor geïmplementeerde functies.
gg-cleanup-failed = Berichtenopschoning mislukt of niet beschikbaar; geen verwijdering geclaimd.
gg-op-lock_change = inhoudsblokkades wijzigen
gg-op-allowlist_change = uitzonderingen wijzigen
gg-op-allowlist_clear = uitzonderingen verwijderen
gg-op-blocklist_change = blokkeerlijst wijzigen
gg-op-blocklist_clear = blokkeerlijst leegmaken
gg-op-raid_change = bescherming tegen massale toetreding wijzigen
gg-disabled-list = Commandobeleid: /disable NAAM en /enable NAAM beheren uitvoering; /disabledel verwijdering; /disableadmin neemt beheerders mee.
    Commando's: { $commands }
gg-cleanup-types = Beschikbare opschooncategorieën:
    Typen: { $types }
gg-cleanup-selected = Gekozen opschooncategorieën:
    Typen: { $types }
gg-advanced-status = Stille automatisering vereist toestemming van de maker en een log. Bots vereisen normale rechten; beoordeling van wijzigingen is standaard actief. Stel botzichtbaarheid in bij BotFather.
    Instelling: { $setting }
    Waarde: { $value }
gg-action-topic = Actieonderwerp. /setactiontopic kiest het huidige forumonderwerp; het algemene onderwerp heeft ID 1.
    Onderwerp: { $topic }
gg-topic-unavailable = Een huidig forum en passende beheerrechten zijn vereist.
gg-topic-id-required = Geef in een gekoppelde privéchat het onderwerp-ID expliciet op.
gg-topic-general-delete = Het algemene onderwerp kan niet worden verwijderd. Bevestiging vereist een identificeerbaar mens.
gg-topic-delete-confirm = Onderwerp en berichten verwijderen? Persoonlijke bevestiging twee minuten geldig.
    Onderwerp: { $topic }
gg-btn-confirm-delete = Verwijdering bevestigen
gg-topic-changed = Onderwerpactie voltooid.
    Actie: { $action }
    Onderwerp: { $topic }
gg-op-policy_change = commando-/opschoonbeleid wijzigen
gg-op-topic_create = onderwerp aanmaken
gg-op-topic_rename = onderwerp hernoemen
gg-op-topic_close = onderwerp sluiten
gg-op-topic_reopen = onderwerp heropenen
gg-op-topic_delete = onderwerp en berichten verwijderen
gg-op-echo = opgemaakte inhoud versturen
gg-broadcast-owner = Alleen de ingestelde operator van deze bot of de echte eigenaar van de kindinstantie mag de eigen groepen aanschrijven.
gg-broadcast-queued = Groepscampagne in de wachtrij. Bestemmingen en resultaten gescheiden per bot.
    ID: { $id }
gg-broadcast-busy = Andere campagne actief of de periode van vijf minuten sinds vorige aanmaak is nog niet verstreken.
gg-broadcast-empty = Je hebt geen groepscampagne in deze bot.
gg-broadcast-status = Status van groepscampagne:
    Geannuleerd: { $cancelled }
    Mislukt: { $failed }
    ID: { $id }
    In wachtrij: { $queued }
    Geleverd: { $sent }
    Status: { $status }
    Onzeker resultaat: { $uncertain }
gg-fed-created = Federatie aangemaakt. Het ID behoort tot het aparte netwerk van deze bot.
    ID: { $id }
    Naam: { $name }
gg-fed-info = Federatie-informatie:
    Beheerders: { $admins }
    ID: { $id }
    Log: { $log }
    Naam: { $name }
    Meldingen: { $notifications }
    Eigenaar: { $owner }
    Redenen vereist: { $reasons }
gg-fed-list = Je federaties als eigenaar of beheerder:
    { $rows }
gg-fed-admins = Eerst de eigenaar, daarna federatiebeheerders:
    { $rows }
gg-fed-quiet = Stille passieve toelichtingen. Handhaving blijft actief.
    Waarde: { $value }
gg-fed-policy = Beleid voor redenen en eigenaarsmeldingen:
    Meldingen: { $notifications }
    Redenen vereist: { $reasons }
gg-fed-confirm-delete = Federatie, gegevens en lidmaatschappen definitief verwijderen? Bestaande Telegram-verbanningen blijven. Persoonlijke bevestiging binnen vijf minuten.
    ID: { $id }
    Naam: { $name }
gg-fed-confirm-log = De aangegeven federatielog instellen? Bevestig binnen vijf minuten. Je rechten op de bestemming en publicatierechten van de bot worden opnieuw gecontroleerd.
    Bestemming: { $destination }
    ID: { $id }
    Naam: { $name }
gg-fed-confirm-sent = Persoonlijke bevestiging naar de federatie-eigenaar verstuurd.
gg-fed-deleted = Federatie verwijderd. Bestaande Telegram-verbanningen blijven.
gg-fed-log-set = Bestemming van federatielog ingesteld:
    Bestemming: { $destination }
gg-fed-cancel = Annuleren
gg-fed-cancelled = Geannuleerd.
gg-fed-saved-delivery-failed = Wijziging opgeslagen, maar melding of log niet geleverd. Controleer bestemming en bottoegang.
gg-fed-error-authority = Huidige federatie-eigenaar of passend federatierol vereist. Telegram-groepsrechten geven geen federatierechten.
gg-fed-error-private = Gebruik dit commando in je eigen privéchat met deze bot.
gg-fed-error-group = Gebruik dit commando in de echte groep. Een privékoppeling kiest geen federatiegroep.
gg-fed-error-owned = Je bezit al een federatie in deze bot. Gebruik /fedinfo, /renamefed of /delfed privé.
gg-fed-error-name = Geef een niet-lege naam zonder besturingstekens op. Namen worden beperkt tot 64 tekens.
gg-fed-error-id = Geef een geldige federatie-UUID van deze bot op. Rose-ID's verbinden niet met onze aparte dienst.
gg-fed-error-missing = Geen federatie in deze bot of context gevonden.
gg-fed-error-creator = Alleen de huidige Telegram-groepsmaker mag de groep bij een federatie aansluiten of eruit halen.
gg-fed-error-target = Geef een positief menselijk ID, antwoord aan een mens of momenteel geverifieerde naam op. De eigenaar kan niet worden afgezet.
gg-fed-error-value = Ongeldige federatieargumenten. Gebruik on/off voor beleid en een geldig ID waar vereist.
gg-fed-error-stale = Bevestiging verlopen, gebruikt of federatie, eigenaar of bestemming gewijzigd. Vraag een nieuwe aan.
gg-fed-error-destination = Eigenaar vereist huidig bestemmingsbeheer; bot vereist publicatietoegang. Kanalen vereisen post_messages.
gg-fed-error-delivery = Persoonlijke bevestiging niet geleverd of niet gebonden. Open een privéchat met de bot en probeer opnieuw.
gg-fed-event = Federatiegebeurtenis:
    Gebeurtenis: { $event }
    ID: { $id }
    Naam: { $name }
    Lid: { $user }
gg-fed-event-rename = naam gewijzigd
gg-fed-event-delete = verwijderd; Telegram-verbanningen blijven
gg-fed-event-promote = beheerder toegevoegd
gg-fed-event-demote = beheerder verwijderd
gg-fed-event-self-remove = beheerder teruggetreden
gg-fed-event-reason = redenbeleid gewijzigd
gg-fed-event-notif = eigenaarsmeldingen gewijzigd
gg-fed-event-log = logbestemming gewijzigd
gg-fed-event-unlog = logbestemming verwijderd
gg-fed-event-ban = verbanningsbeleid opgeslagen; handhaving in wachtrij
gg-fed-event-unban = verbanningsbeleid verwijderd; opheffing van eigen beperkingen in wachtrij
gg-fed-event-subscribe = abonnement toegevoegd; controle van waargenomen gebruikers in wachtrij
gg-fed-event-unsubscribe = abonnement verwijderd; andere bronnen blijven
gg-fed-ban-details = Doel en reden van verbanning:
    Reden: { $reason }
    Lid: { $user }
gg-fed-passive = Het federatiebeleid verbant het lid. Bron en reden hieronder.
    ID: { $id }
    Reden: { $reason }
    Bron: { $source }
    Lid: { $user }
gg-fed-enforce-failed = Het federatiebeleid verbant het lid, maar verwijderen mislukte. Controleer botrechten. Bron en reden hieronder.
    ID: { $id }
    Reden: { $reason }
    Bron: { $source }
    Lid: { $user }
gg-fed-stat = Federatieverbanningen van dit lid:
    { $rows }
    Lid: { $user }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — actief: { $status }; gewijzigd: { $date }.
gg-fed-stat-more = Meer bronnen beschikbaar. Gebruik het vervolgcommando of een specifiek federatie-ID voor reden en datum.
gg-fed-intent-saved = Beleid opgeslagen; waargenomen doelen in wachtrij. Huidige rechten en andere beperkingsbronnen worden vóór effecten gecontroleerd.
    Lid: { $user }
    Versie: { $version }
gg-fed-subscriptions = Directe abonnementen op federatieverbanningen:
    { $rows }
gg-fed-imported = Items geverifieerd en opgeslagen; identieke duplicaten overgeslagen. Handhaving bij waargenomen doelen in wachtrij.
    Aantal: { $count }
    Identieke duplicaten: { $duplicates }
gg-fed-event-import = geverifieerde verbanningen geïmporteerd; handhaving in wachtrij
gg-fed-error-file-format = Antwoord op UTF-8-CSV met id/reason, JSONL/NDJSON met user_id of de JSON-arrayexport van deze bot. Eén ongeldige rij voorkomt alle schrijfacties.
gg-fed-error-file-limit = Maximaal 2 MiB en 1000 items. Ontbrekende of te grote bestanden geweigerd; lijsten nooit stil afgekapt.
gg-fed-error-file-duplicate = Tegenstrijdige items voor hetzelfde gebruiker-ID. Geen verbanningen geïmporteerd.
gg-fed-error-file-rate = Import en export delen een interval van 30 minuten per federatie. Probeer later opnieuw.
gg-fed-error-reason = Verbanningsredenen maximaal 1024 tekens zonder niet-ondersteunde besturingstekens.
gg-fed-error-reason_required = Deze federatie vereist een niet-lege reden voor elke verbanning.
gg-fed-error-cycle = Een federatie mag zichzelf niet abonneren of een gerichte cyclus maken.
gg-fed-error-graph_limit = Limiet bereikt: 32 directe bestemmingen, 128 bereikbare federaties, diepte 16 of 10 000 verbindingen in deze bot.
gg-data-confirm = Bevestig binnen vijf minuten. Huidige maker en groepsrevisie worden opnieuw gecontroleerd. Alleen geselecteerde modules wijzigen; identiteit, vertrouwen en actieve verbanningen blijven.
    SHA-256: { $digest }
    Groep: { $group }
    Modules: { $modules }
    Bewerking: { $operation }
gg-data-import = Groepsmodules importeren
gg-data-reset = Groepsmodules herstellen
gg-data-privacy-delete = Optionele persoonsgegevens van deze bot verwijderen
gg-data-confirm-button = Deze wijziging bevestigen
gg-data-personal = Open de bevestiging in je privéchat.
gg-data-saved = Geselecteerde modules opgeslagen.
gg-data-error-authority = Import en herstel vereisen de huidige identificeerbare groepsmaker. Export vereist een huidige beheerder.
gg-data-error-format = Antwoord op geldige Group Guard-JSON met versie, aangemaakt met /export.
gg-data-error-limit = Bestand overschrijdt de ingestelde grootte- of inhoudslimiet.
gg-data-error-version = Schema of versie niet ondersteund; geen wijzigingen toegepast.
gg-data-error-module = Kies bekende modules: /export all of /export notes rules. Import en herstel gebruiken dezelfde namen.
gg-data-error-field = Ongeldige of ontbrekende modulevelden. Geen instellingen toegepast.
gg-data-error-item = Inhoud, opties of herhaaltoegang ongeldig. Geen inhoud opgeslagen.
gg-data-error-media = Media moeten naar deze bot zijn geüpload en via getFile bereikbaar zijn. Bestand-ID's van andere bots worden niet ondersteund.
gg-data-error-destination = Log- en onderwerpsbestemmingen vereisen huidige rechten en botmogelijkheden. Onderwerp-ID's gelden alleen binnen dezelfde groep.
gg-data-error-language = Kies een geïnstalleerde taal met /setlang.
gg-data-error-stale = Bevestiging verlopen, gewijzigd of gebruikt. Begin opnieuw.
gg-data-error-restore = Eigen tijdelijke beperkingen konden niet veilig worden hersteld. Bewijs blijft; controleer botrechten.
gg-data-error-rate = Groepsgegevensbewerkingen hebben een lokaal interval van vijf minuten. Probeer later opnieuw.
gg-data-error-delivery = Privébevestiging niet geleverd. Start een privéchat met de bot en probeer opnieuw.
gg-data-error-saved_delivery = Instellingen opgeslagen, maar commandosuggesties niet bijgewerkt. Controleer botrechten.
gg-privacy-policy = <b>Je gegevens in deze Group Guard</b>
    /privacy data exporteert koppelingen, waargenomen profielen, waarschuwingen, goedkeuringen, beperkings-/verificatiestatus, federatie-eigendom/-rollen/-verbanningen en veiligheidstaken. Privé-inhoud van anderen, verificatieantwoorden, authenticatie en ruwe bestanden ontbreken. Volg het vervolgcommando.
    /privacy delete verwijdert optionele koppelgeschiedenis, waargenomen naam/gebruikersnaam, inactieve verificaties en inhoud van je afgeronde campagnes in deze bot. Actieve waarschuwingen/beperkingen, verbanningsversies, rollen, eigendom, abonnementen, herhalingsbescherming en onzekere API-taken bewaren minimale veiligheids- en ordeningsidentiteiten. Gebruik expliciete federatie-uittredings-/verwijdercommando's voor die relaties. Gedeeld platformprofiel en andere bots blijven.
    Operators beheren back-ups en audits afzonderlijk. Dit commando verwijdert geen externe Telegram-berichten of back-ups en belooft geen automatische bewaartermijn.
gg-privacy-usage = /privacy policy · /privacy data [vervolg] · /privacy delete — alleen in je eigen privéchat met deze bot.
gg-privacy-private = Deze actie vereist de privéchat van de aanvragende persoon. Ongeldige cursors geven geen toegang tot gegevens van anderen.
gg-privacy-next = Volgende gegevenspagina: /privacy data { $cursor }
gg-privacy-deleted = Optionele persoonsgegevens van deze bot verwijderd. Actieve veiligheid, eigendom en onzekere taken bewaren minimale identiteiten; zie /privacy policy.
gg-language-usage = Kies de groepstaal met /setlang. /lang privé wijzigt je persoonlijke platformtaal. Beschikbare codes hieronder.
    Taalcodes: { $codes }
gg-language-saved = Taal van groepsantwoorden gewijzigd.
gg-help-index = <b>Group Guard-commandogids</b>
    /help onderdeel · /help commando · /help onderdeel 2. Vermelde commando's werken ook via geverifieerde /connect; privéantwoorden blijven in de echte privéchat.
    Instellingen vereisen informatie wijzigen; sancties leden beperken; verwijderingen verwijderrechten; vastzetten vastzetrechten; benoemingen beheerders aanstellen; onderwerpen onderwerpbeheer. Botrechten apart geverifieerd. Eigenaarsacties vereisen de huidige menselijke maker. /settings opent je persoonlijke groepspaneel.
gg-help-search = <b>Overeenkomende commando's</b>
    Zoekopdracht: { $query }
gg-help-connected = Groep of geverifieerde koppeling; rechten bij onderdeel
gg-help-group-only = Een echt groepsbericht is vereist
gg-help-unsupported = Catalogusnaam behouden; ongedefinieerd gedrag geeft uitleg
gg-help-next = Volgende pagina
gg-help-previous = Vorige pagina
gg-help-family-title-moderation = Moderatie en goedkeuringen
gg-help-family-title-messages = Berichten verwijderen en vastzetten
gg-help-family-title-logging = Geautoriseerde logs
gg-help-family-title-settings = Groepsinstellingen en taal
gg-help-family-title-content = Notities, filters, regels en begroetingen
gg-help-family-title-captcha = Verificatie van nieuwe leden
gg-help-family-title-locks = Inhoudsblokkades en uitzonderingen
gg-help-family-title-blocklists = Blokkeerlijstovereenkomsten en acties
gg-help-family-title-antispam = Bescherming tegen berichtenstromen en massale toetreding
gg-help-family-title-connections = Privékoppelingen met groepen
gg-help-family-title-identity = Gebruikers- en chatinformatie
gg-help-family-title-policy = Commando- en botbeleid
gg-help-family-title-cleanup = Opschoning van commando's, bots en diensten
gg-help-family-title-topics = Forumonderwerpen
gg-help-family-title-utilities = Inhoud versturen en operatorcampagnes
gg-help-family-title-federations = Federatierollen, verbanningen en abonnementen
gg-help-family-title-portability = Groepsbestanden en persoonsgegevens
gg-help-family-title-discovery = Hulp en inhoudseditor
gg-help-family-moderation = <b>Moderatie</b> · Antwoord, numeriek ID of geverifieerde @gebruiker. /ban 20 reden; /tban 20 60s reden; /mute 20; /tmute 20 2h reden. Duur 60 seconden–365 dagen. /kickme verwijdert alleen jou. d-varianten verwijderen beantwoord bericht; s-varianten commando/antwoord en vereisen verwijderrechten. Beheerders beschermd. /setwarnlimit 3; /setwarnmode ban; /setwarntime 1d. Nieuwe groepen drie waarschuwingen; oude instellingen blijven. /approve omzeilt alleen gewone inhouds-/berichtenbescherming, nooit federatie/CAS/massale toetreding/handmatige acties. /promote geeft maximaal de gedeelde rechten van aanvrager en bot. Globaal herstel alleen maker.
gg-help-family-messages = <b>Berichten</b> · /del vereist echte groepsreactie. /purge begint daar; /purgefrom en /purgeto bewaren grenzen. Ingestelde limieten en Telegram-regels gelden; batchbevestiging bewijst geen exact verwijderd aantal. /pin [loud], /permapin, /unpin, /unpinall vereisen vastzetrechten; alles losmaken alleen maker. /antichannelpin en /cleanlinked beheren automatische gekoppelde kanaalberichten.
gg-help-family-logging = <b>Logs</b> · /setlog -100… vereist huidig bestemmingsbeheer en botpublicatie. Doorgestuurde instelling moet een echt ontvangen origineel hebben. /logcategories: settings/admin/user/automated/reports/other; /log en /nolog kiezen categorieën. Leveringsfouten blijven zichtbaar en bewijzen geen actiesucces.
gg-help-family-settings = <b>Instellingen</b> · /settings opent persoonlijk tijdelijk paneel met actuele informatie-wijzigrechten. /setlang code bewaart groepstaal; /lang privé persoonlijke taal. /night 23 7 +3 sluit 's nachts; /night off herstelt alleen eigen nog overeenkomende permissies. Externe wijzigingen hebben voorrang.
gg-help-family-content = <b>Editor</b> · /save woord tekst of antwoord op media; /get woord, #woord, /notes lezen notities. Nieuwe notitienamen één woord; oude ruimere namen blijven. /filter "zin" tekst, /filterprefix, /filterexact kiezen matches; /stop verwijdert sleutel. /clearall en /stopall vereisen makerbevestiging. Rose-opmaak: vet/cursief/onderstreept/doorgestreept/code, links, citaten en willekeurige %%% alternatieven. Velden: { "{" }first{ "}" }, { "{" }last{ "}" }, { "{" }fullname{ "}" }, { "{" }username{ "}" }, { "{" }mention{ "}" }, { "{" }id{ "}" }, { "{" }chatname{ "}" }, { "{" }count{ "}" }. /button maakt URL-/notitie-/regelknoppen. Algemene opties preview/nonotif/protect/mediaspoiler; notities admin/private/noprivate/repeat; filters user/allow_bot/replytag/command. /save woord Hallo { "{" }repeat 5m{ "}" } plant alleen openbare inhoud met actuele auteursrechten. Regels, begroetingen en privé-inhoud delen renderer. Media-ID's behoren tot bot.
gg-help-family-captcha = <b>Verificatie</b> · /captcha on/off; /captchamode off/button/math/text/text2; /setcaptchatext; /captcharules on; /captchakick on/off; /captchakicktime en /captchamutetime stellen begrensde termijnen. Uitgegeven uitdagingen houden generatie/termijn. Verzoeken vereisen invite-users; dempen restrict-members. Persoonlijke eenmalige antwoorden. Federatieverbanningen vóór goedkeuring/CAPTCHA.
gg-help-family-locks = <b>Blokkades</b> · /lock links [actie], /unlock type; /locktypes toont echte typen, /locks status. /lockwarns beheert waarschuwingen. /allowlist: domein/pad, exacte uitnodiging, @chat of stickerpack:/forward:/inline:/channel:/chat:/bot:/command:. Ongeldige patronen geweigerd. Uitzonderingen alleen voor overeenkomende inhoud; stille automatisering vereist maker en geautoriseerde log.
gg-help-family-blocklists = <b>Blokkeerlijst</b> · /addblocklist "zin" ondersteunt tekst/prefix/exact en opgegeven identiteiten met optionele reden/actie. /rmblocklist verwijdert exact gekozen sleutels. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute kiest actie; tijdelijk vereist duur. /blocklistdelete regelt verwijdering apart. Wildcardpatronen begrensd; ongeldige items en overschrijdingen geweigerd.
gg-help-family-antispam = <b>Berichten en massale toetreding</b> · /setflood aantal voor opeenvolgende berichten; /setfloodtimer aantal duur voor tijdvenster; /setfloodmode sanctie/duur; /clearflood reeks opschonen. Oude instellingen blijven. /flood en /antiflood tonen beleid; alias lokale compatibiliteitskeuze. /antiraid on/off/duration, /raidtime, /raidactiontime, /autoantiraid bewaren termijn en aparte sanctie voor toetreders. Voorrang op goedkeuring/CAPTCHA; generatiegebonden verval overleeft herstart.
gg-help-family-connections = <b>Koppelingen</b> · /connect groupID of persoonlijke link. Lidmaatschap van jou en bot wordt gecontroleerd; wijzigen vereist nog steeds exacte actuele rechten. /connection toont keuze, /disconnect verwijdert die, /connect toont geschiedenis met vervolg. Koppeling geeft geen federatie-eigendom of operatorrechten.
gg-help-family-identity = <b>Informatie</b> · /id toont echte gebruiker-/chat-/bron-ID's; /info huidige doel. Antwoorden en @namen vereisen actuele botgebonden bewijzen. Anonieme groepsberichten identificeren geen persoon; geen menselijk ID verzonnen.
gg-help-family-policy = <b>Beleid</b> · /disable commando, /enable commando, /disabled, /disableable gebruiken canonieke namen en aliases. /disableadmin beheert beheerdersuitzonderingen; /disabledel verwijderen. Herstelcommando's blijven bereikbaar. /bot2bot off/admin/all verifieert echt lidmaatschap; wijzigingen standaard menselijk beoordeeld. /bot2botskipreview alleen maker. /silentactions vereist toestemming en geautoriseerde log. Ongedefinieerde runs/saved geven uitleg.
gg-help-family-cleanup = <b>Opschoning</b> · /cleancommand admin/user/other en /keepcommand kiezen commando's. /cleanmsg action/filter/note en /keepmsg alleen echt door deze bot verzonden berichten; ontvangstbewijzen en vijfminutentaken voorkomen geraden ID's. /cleanservice en /nocleanservice: join/leave/other/photo/pin/title/videochat. Functionele verwerking en geldige betalingen vóór opschoning.
gg-help-family-topics = <b>Onderwerpen</b> · /newtopic naam, /renametopic naam, /closetopic, /reopentopic gebruiken echt huidig onderwerp. /deletetopic vereist makerbevestiging; /setactiontopic kiest bestemming in dezelfde groep. Telegram-forum en manage-topics vereist. Ontbrekende/niet-ondersteunde onderwerpen geven echte foutmelding.
gg-help-family-utilities = <b>Hulpmiddelen</b> · /echo en /say sturen directe/beantwoorde inhoud via gemeenschappelijke begrensde renderer. /broadcast alleen ingestelde operator of echte kindeigenaar; alleen ingestelde groepen van deze bot. Resultaten per bestemming bewaren gedeeltelijke/onzekere levering; status en annulering herhalen geen geslaagde bijlagen.
gg-help-family-federations = <b>Federaties</b> · /newfed naam maakt UUID in deze bot. Privécommando's gebruiken eigen federatie ongeacht koppelingen; UUID lezen geeft geen rol. /fedpromote en /feddemote beheren beheerders, /feddemoteme treedt terug. /joinfed UUID en /leavefed vereisen huidige groepsmaker. Verwijderen heft Telegram-verbanningen niet op. /fban userID reden en /unfban userID vereisen federatie-eigenaar/-beheerder; /fedreason, /fednotif, /setfedlog eigenaar. /quietfed verbergt alleen passieve meldingen. /subfed UUID gericht, begrensd, cyclusvrij. /fedstat [userID], /fbanstat UUID tonen bronnen/status. /fbanlist csv/minicsv/json alleen eigenaar met gedeeld 30-minuteninterval; /importfbans antwoord op begrensde CSV of echt JSON per regel, eigen JSON-array expliciet ondersteund. Alleen waargenomen gebruikers geverifieerd, geen volledige ledeninventaris geclaimd.
gg-help-family-portability = <b>Bestanden en privacy</b> · /export all of modules vereist beheerder; /import en /reset huidige menselijke maker met persoonlijke eenmalige vijfminutenbevestiging. Lokaal vijfminuteninterval; eigen JSON met versie, maximaal 2MiB en ingestelde inhoudslimieten. Modules: moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Niet gekozen modules blijven. Vertrouwen, uitgegeven uitdagingen/taken, abonnementen, rollen en actieve verbanningen nooit geïmporteerd. /privacy policy/data/delete alleen eigen privéchat met pagina's en minimale veiligheidsbewaring. Geen geverifieerde adapter voor volledige Rose-export.
gg-help-family-discovery = <b>Hulp</b> · /help toont onderdelen; /help commando zoekt namen/aliases; /help onderdeel 2 vervolgt. /button helpt met knopopmaak. Elke gids beschrijft context, rechten, standaardwaarden en limieten. /settings opent je persoonlijke groepspaneel.
gg-data-error-cache_pending = Optionele SQL-gegevens verwijderd. Opschoning van de onbeschikbare cache staat in de wachtrij; actieve veiligheidsgegevens blijven.
