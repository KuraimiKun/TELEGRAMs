## Independently authored Group Guard de content.
group-welcome = 🛡 Danke fürs Hinzufügen! Gib mir Administratorrechte zum Löschen, Einschränken von Mitgliedern und Anheften von Nachrichten. Die Konfiguration öffnest du mit /settings.
gg-start = 🛡 Hallo <b>{ $name }</b>! Ich bin <b>Group Guard</b>: Prüfung neuer Mitglieder, Flut-/CAS-Schutz, Inhaltssperren, Moderation, Notizen, Filter, Regeln und Begrüßungen. Füge mich als Gruppenadministrator hinzu und nutze /settings oder /help.
gg-help = 📖 /help zeigt Bereiche; /help Befehl sucht Befehle. Moderation: /ban /mute /kick /warn. Inhalte: /save /filter /rules. Schutz: /lock /blocklist /night. /settings öffnet die persönliche Gruppenübersicht.
gg-welcome-default = 👋 Willkommen { "{" }mention{ "}" } in <b>{ "{" }group{ "}" }</b>!
gg-credit = 🛡 Geschützt durch @{ $bot }
gg-btn-add = ➕ Zu einer Gruppe hinzufügen
gg-btn-commands = 📖 Befehle
gg-btn-rules = 📜 Regeln
gg-btn-human = ✅ Ich bin ein Mensch
gg-btn-unwarn = ↩️ Verwarnung entfernen (Administratoren)
gg-btn-locks = 🔒 Inhaltssperren · Anzahl: { $count }
gg-btn-open-settings = ⚙️ Einstellungen öffnen
gg-btn-admin-tab = 🛡 Gruppen
gg-captcha = 🤖 Bestätige innerhalb der angegebenen Frist, dass du ein Mensch bist, sonst wirst du entfernt.
    Minuten: { $minutes }
    Mitglied: { $user }
gg-captcha-button = Drücke die Schaltfläche unten 👇
gg-captcha-math = Was ist <b>{ $a } + { $b }</b>?
gg-captcha-not-you = Diese Schaltfläche ist für eine andere Person.
gg-captcha-ok = ✅ Willkommen!
gg-captcha-wrong = ❌ Falsche Antwort. Weitere Versuche sind noch möglich.
    Verbleibende Versuche: { $left }
gg-captcha-failed = ❌ Zu viele falsche Antworten.
gg-captcha-passed = ✅ Prüfung bestanden. Willkommen!
    Mitglied: { $user }
gg-cas-banned = 🚫 Das Mitglied ist bei CAS als Spammer bekannt und wurde gesperrt.
    Mitglied: { $user }
gg-join-request = 👋 Bestätige, dass du ein Mensch bist, um der Gruppe beizutreten:
    Gruppe: { $group }
gg-join-approved = ✅ Beitritt genehmigt. Willkommen!
gg-join-expired = ⌛ Diese Anfrage ist abgelaufen. Stelle eine neue Beitrittsanfrage.
gg-goodbye = 👋 Das Mitglied hat die Gruppe verlassen.
    Mitglied: { $user }
gg-flood-mute = 🌊 Wegen zu vieler Nachrichten wurde das Mitglied vorübergehend stummgeschaltet.
    Mitglied: { $user }
gg-flood-kick = 🌊 Das Mitglied wurde wegen Nachrichtenflut entfernt.
    Mitglied: { $user }
gg-flood-ban = 🌊 Das Mitglied wurde wegen Nachrichtenflut gesperrt.
    Mitglied: { $user }
gg-newbie-links = 🆕 Neue Mitglieder dürfen während der angegebenen ersten Stunden keine Links senden.
    Stunden: { $hours }
    Mitglied: { $user }
gg-spam-banned = 🧠 Das Mitglied wurde wegen Spam gesperrt.
    Mitglied: { $user }
gg-reason-blocklist = gesperrtes Wort
gg-need-right = ⛔ Dafür brauchst du das passende Administratorrecht.
    Recht: { $right }
gg-right-admin = Administrator
gg-right-restrict = Mitglieder einschränken
gg-right-delete = Nachrichten löschen
gg-right-pin = Nachrichten anheften
gg-right-change_info = Gruppeninformationen ändern
gg-admins-only = ⛔ Nur für Administratoren.
gg-need-target = 👤 Antworte auf eine Nachricht oder gib einen geprüften @Benutzernamen beziehungsweise eine Benutzer-ID an.
gg-target-admin = 🙅 Diese Aktion darf keinen Administrator treffen.
gg-bot-no-rights = ⚠️ Ich brauche Administratorstatus und die passenden Berechtigungen.
gg-banned = 🔨 Das Mitglied wurde gesperrt.
    Grund: { $reason }
    Mitglied: { $user }
gg-banned-for = 🔨 Das Mitglied wurde für die angegebene Zeit gesperrt.
    Grund: { $reason }
    Zeit: { $time }
    Mitglied: { $user }
gg-unbanned = ✅ Die Sperre des Mitglieds wurde aufgehoben.
    Mitglied: { $user }
gg-kicked = 👢 Das Mitglied wurde entfernt und darf erneut beitreten.
    Grund: { $reason }
    Mitglied: { $user }
gg-muted = 🔇 Das Mitglied wurde stummgeschaltet.
    Grund: { $reason }
    Mitglied: { $user }
gg-muted-for = 🔇 Das Mitglied wurde für die angegebene Zeit stummgeschaltet.
    Grund: { $reason }
    Zeit: { $time }
    Mitglied: { $user }
gg-unmuted = 🔊 Das Mitglied darf wieder schreiben.
    Mitglied: { $user }
gg-warned = ⚠️ Das Mitglied wurde verwarnt.
    Anzahl: { $count }
    Grenze: { $limit }
    Grund: { $reason }
    Mitglied: { $user }
gg-warn-limit-ban = 🔨 Verwarnungsgrenze erreicht; das Mitglied wurde gesperrt.
    Grenze: { $limit }
    Mitglied: { $user }
gg-warn-limit-mute = 🔇 Verwarnungsgrenze erreicht; das Mitglied wurde stummgeschaltet.
    Grenze: { $limit }
    Mitglied: { $user }
gg-warn-limit-kick = 👢 Verwarnungsgrenze erreicht; das Mitglied wurde entfernt.
    Grenze: { $limit }
    Mitglied: { $user }
gg-unwarned = ↩️ Eine Verwarnung des Mitglieds wurde entfernt.
    Anzahl: { $count }
    Grenze: { $limit }
    Mitglied: { $user }
gg-warn-removed = ↩️ Eine Verwarnung wurde vom Administrator entfernt.
    Administrator: { $admin }
gg-warns = ⚠️ Verwarnungen des Mitglieds:
    Anzahl: { $count }
    Grenze: { $limit }
    Mitglied: { $user }
gg-warns-reset = 🧽 Die Verwarnungen des Mitglieds wurden zurückgesetzt.
    Mitglied: { $user }
gg-purge-reply = 🧹 Antworte auf die erste Nachricht, die gelöscht werden soll.
gg-purged = 🧹 Nachrichten wurden gelöscht.
    Anzahl: { $count }
gg-pin-reply = 📌 Antworte auf die Nachricht, die angeheftet werden soll.
gg-report-reply = 🚨 Antworte auf die Nachricht, die gemeldet werden soll.
gg-reported = 🚨 Das Mitglied wurde den Administratoren gemeldet.
    Mitglied: { $user }
gg-setlog-usage = 📒 Füge mich als Administrator im Protokollkanal hinzu und verwende <code>/setlog -100…</code> mit dessen ID.
gg-setlog-failed = ⚠️ Ich kann dort nicht senden. Füge mich zuerst als Administrator hinzu.
gg-setlog-done = 📒 Protokollkanal verbunden.
gg-setlog-off = 📒 Protokollkanal getrennt.
gg-log-connected = 📒 Dieser Chat empfängt das Moderationsprotokoll der Gruppe.
    Gruppe: { $group }
gg-log-flood = 🌊 Nachrichtenflut festgestellt:
    Aktion: { $action }
    Mitglied: { $user }
gg-log-report = 🚨 Meldung über ein Mitglied:
    Mitglied: { $user }
gg-log-spam = 🧠 Spam-Sperre durch KI:
    Text: { $text }
    Mitglied: { $user }
gg-rules = 📜 <b>Regeln</b>
    { $rules }
gg-no-rules = 📜 Noch keine Regeln gespeichert. Administratoren können /setrules Text verwenden.
gg-rules-saved = 📜 Regeln gespeichert.
gg-rules-cleared = 📜 Regeln gelöscht.
gg-welcome-usage = 👋 Nutze <code>/setwelcome Hallo {"{"}mention{"}"}, willkommen in {"{"}group{"}"}!</code> oder antworte auf eine Nachricht.
gg-welcome-saved = 👋 Begrüßung gespeichert.
gg-welcome-reset = 👋 Standardbegrüßung wiederhergestellt.
gg-note-usage = 📝 <code>/save Name Text</code> oder eine Nachricht mit <code>/save Name</code> beantworten.
gg-filter-usage = 🔁 <code>/filter Wort Antwort</code> oder eine Nachricht mit <code>/filter Wort</code> beantworten.
gg-note-saved = 📝 Notiz gespeichert. Abruf: <code>#{ $key }</code>, entsprechend den Zugriffsrechten.
gg-filter-saved = 🔁 Ich antworte bei einem Treffer auf „{ $key }“.
gg-notes-empty = 📝 Noch keine Notizen.
gg-filters-empty = 🔁 Noch keine Filter.
gg-notes-list = 📝 <b>Notizen</b>
gg-filters-list = 🔁 <b>Filter</b>
gg-item-deleted = 🗑 Eintrag gelöscht.
    Schlüssel: { $key }
gg-item-missing = 🤷 Unter diesem Namen ist nichts gespeichert.
gg-items-limit = 📦 Die Grenze für Notizen und Filter dieser Gruppe ist erreicht.
gg-lock-usage = 🔒 Nutze <code>/lock links</code>. Die verfügbaren Typen stehen unten; <code>all</code> wählt alle aus.
    Typen: { $types }
gg-locked = 🔒 Gesperrte Inhalte:
    Typen: { $types }
gg-unlocked = 🔓 Freigegebene Inhalte:
    Typen: { $types }
gg-locks-title = 🔒 <b>Inhaltssperren</b>
gg-locks-panel = 🔒 <b>Sperren</b>: gesperrte Inhalte werden gelöscht; Administratoren sind ausgenommen.
gg-lock-links = Links
gg-lock-invites = Einladungslinks
gg-lock-forwards = Weiterleitungen
gg-lock-media = Medien
gg-lock-stickers = Sticker
gg-lock-gifs = GIFs
gg-lock-voice = Sprachnachrichten
gg-lock-polls = Umfragen
gg-lock-bots = Bots
gg-blocklist = 🚫 <b>Gesperrte Wörter</b>
    Wörter: { $words }
gg-blocklist-empty = 🚫 Keine gesperrten Wörter.
gg-blocklist-usage = 🚫 <code>/addblock Wort, weitere Phrase</code> · <code>/rmblock Wort</code>
gg-blocklist-saved = 🚫 Sperrliste aktualisiert.
    Anzahl: { $count }
gg-night-usage = 🌙 <code>/night 23 7 +3</code> schließt von 23:00 bis 07:00 UTC+3; <code>/night off</code> deaktiviert.
gg-night-on = 🌙 Nachtzeiten für die Gruppe eingestellt.
    Ende: { $end }
    Beginn: { $start }
    Zeitzone: { $tz }
gg-night-off = 🌙 Nachtmodus ausgeschaltet.
gg-night-start = 🌙 Gute Nacht! Die Gruppe bleibt bis zur angegebenen Zeit geschlossen.
    Ende: { $end }
gg-night-end = ☀️ Guten Morgen! Die Gruppe ist wieder offen.
gg-panel = ⚙️ <b>Gruppeneinstellungen</b>
    Drücke eine Option zum Ändern. Nachtzeiten werden mit /night festgelegt.
    Gruppe: { $group }
    Nachtzeiten: { $night }
gg-panel-sent = 📬 Die Einstellungen wurden dir privat geschickt.
gg-panel-start-first = 📬 Starte zuerst einen privaten Chat mit mir und drücke dann unten.
gg-credit-vip = 💎 Das Ausblenden der Schutzzeile benötigt VIP. Nutze /vip im privaten Chat.
gg-opt-wel = 👋 Begrüßung · Wert: { $value }
gg-opt-cln = 🧹 Beitrittsmeldungen löschen · Wert: { $value }
gg-opt-bye = 👋 Abschied · Wert: { $value }
gg-opt-cap = 🤖 Prüfung · Wert: { $value }
gg-opt-cpm = ⏱ Prüffrist, Minuten · Wert: { $value }
gg-opt-fld = 🌊 Flutgrenze · Wert: { $value }
gg-opt-fla = 🌊 Aktion bei Nachrichtenflut · Wert: { $value }
gg-opt-wrn = ⚠️ Verwarnungsgrenze · Wert: { $value }
gg-opt-wra = ⚠️ Verwarnungsaktion · Wert: { $value }
gg-opt-act = ⏳ Automatische Einschränkung, Minuten · Wert: { $value }
gg-opt-cas = 🛡 CAS-Schutz · Wert: { $value }
gg-opt-nwb = 🆕 Neue Mitglieder ohne Links, Stunden · Wert: { $value }
gg-opt-ais = 🧠 KI-Spamschutz · Wert: { $value }
gg-opt-ngt = 🌙 Nachtmodus · Wert: { $value }
gg-opt-crd = 🏷 Schutzzeile · Wert: { $value }
gg-opt-lang = 🌐 Sprache · Wert: { $value }
gg-val-button = Schaltfläche
gg-val-math = Rechenaufgabe
gg-val-off = ausgeschaltet
gg-val-mute = stummschalten
gg-val-kick = entfernen
gg-val-ban = sperren
gg-adm = 🛡 <b>Group Guard: Statistik</b>
    Gruppen: { $groups }
    Einträge: { $items }
    Verwarnungen: { $warns }
cmd-settings = Gruppeneinstellungen
cmd-help = Befehlsübersicht
gg-auth-denied = Die Berechtigung konnte nicht geprüft werden. Nichts wurde geändert.
gg-target-invalid = Wähle ein bekanntes menschliches Mitglied. Das Ziel konnte nicht geprüft werden.
gg-duration-invalid = Nutze eine Dauer von 60s bis 365d. Temporäre Befehle benötigen eine Dauer.
gg-reason-invalid = Der Grund darf höchstens 256 Zeichen enthalten.
gg-outcome-failed = Die Aktion ist fehlgeschlagen oder konnte nicht autorisiert werden.
gg-outcome-partial = Die Aktion ist nur teilweise abgeschlossen. Eine Sperre kann bestehen bleiben, wenn die Wiederherstellung nach dem Entfernen fehlschlägt.
gg-outcome-ancillary = Die Hauptaktion wurde abgeschlossen, aber ein zugehöriger Schritt ist fehlgeschlagen.
gg-review-request = Prüfe die unveränderliche Aktion unten. Eine aktuell berechtigte Person kann innerhalb von 120 Sekunden zustimmen. Die Dauer wird in Sekunden angegeben.
    Einzelheiten: { $details }
    Dauer: { $duration }
    Operation: { $operation }
    Ziel: { $target }
gg-review-approve = Diese Aktion genehmigen
gg-review-unavailable = Der Bestätigungsspeicher ist nicht verfügbar. Sende einen neuen Befehl.
gg-review-expired = Diese Bestätigung ist abgelaufen, ungültig oder bereits verwendet.
gg-review-consumed = Die Bestätigung wurde verwendet. Prüfe das Ergebnis; zum Wiederholen ist ein neuer Befehl nötig.
gg-duration-permanent = Dauerhaft / ohne Zeitlimit
gg-purge-ack = Die API hat Löschanfragen bestätigt. Die tatsächlich gelöschte Anzahl ist nicht bekannt.
    Von API bestätigt: { $acknowledged }
    Angefordert: { $requested }
gg-warning-removed = Verwarnung entfernt.
gg-op-ban = sperren
gg-op-mute = stummschalten
gg-op-kick = entfernen
gg-op-unban = Sperre aufheben
gg-op-unmute = Stummschaltung aufheben
gg-op-warn = verwarnen
gg-op-unwarn = Verwarnung entfernen
gg-op-resetwarns = Verwarnungen zurücksetzen
gg-op-purge = Nachrichtenbereich löschen
gg-op-delete = Nachricht löschen
gg-op-pin = Nachricht anheften
gg-op-unpin = Anheftung lösen
gg-op-setlog = Protokollziel setzen
gg-op-unsetlog = Protokollziel entfernen
gg-op-config = Einstellungen ändern
gg-op-save = Inhalt speichern
gg-op-remove = Inhalt entfernen
gg-op-panel = Übersicht öffnen
gg-review-details-above = Der vollständige angeforderte Inhalt steht direkt darüber.
gg-warn-pending = Verwarnung gespeichert; eine Grenzfallaktion wird bereits verarbeitet.
gg-done = Abgeschlossen.
gg-setting-saved = Einstellung gespeichert.
    Einstellung: { $setting }
gg-setting-value = Aktueller Einstellungswert:
    Einstellung: { $setting }
    Wert: { $value }
gg-setting-invalid = Ungültige Einstellung. Nutze on/off, einen gültigen Modus oder eine Dauer wie 10m.
gg-warning-settings = Verwarnungseinstellungen:
    Dauer: { $duration }
    Ablauf: { $expiry }
    Grenze: { $limit }
    Modus: { $mode }
gg-admin-changed = Administratoraktion abgeschlossen.
    Aktion: { $action }
    Mitglied: { $user }
gg-admin-list = Öffentliche Administratoren:
    { $admins }
gg-approved = Mitglied genehmigt.
    Grund: { $reason }
    Mitglied: { $user }
gg-unapproved = Genehmigungen entfernt.
    Anzahl: { $count }
gg-approval-status = Genehmigungsstatus des Mitglieds:
    Grund: { $reason }
    Status: { $status }
    Mitglied: { $user }
gg-approval-list = Genehmigte Mitglieder:
    { $approvals }
gg-next-page = Weitere Einträge: { $command }
gg-range-invalid = Ungültiger Bereich. Wähle zwischen einer Nachricht und der angegebenen Grenze.
    Obergrenze: { $cap }
gg-range-start = Der Start ist für dich in diesem Thema zehn Minuten gespeichert. Beantworte die letzte Nachricht mit /purgeto.
gg-range-missing = Für dich ist hier kein Start gespeichert. Nutze zuerst /purgefrom als Antwort.
gg-content-needed = Gib Inhalt an oder antworte darauf; höchstens 3500 Zeichen.
gg-log-status = Protokolleinstellungen:
    Kategorien: { $categories }
    Ziel: { $destination }
gg-log-unverified = Ich habe keinen bestätigten Empfang dieses ursprünglichen Kanalbefehls. Sende zuerst /setlog im Kanal.
gg-log-forward = Leite diesen ursprünglichen /setlog-Befehl an die Gruppe weiter. Der verbindende Administrator benötigt Änderungsrechte in beiden Chats.
gg-info = Informationen über Benutzer oder Chat:
    ID: { $id }
    Mitgliedschaft: { $membership }
    Name: { $name }
    Benutzername: { $username }
gg-op-unpinall = alle Anheftungen lösen
gg-op-permapin = dauerhaft anheften
gg-op-promote = Administrator ernennen
gg-op-demote = Administrator absetzen
gg-op-approve_user = Benutzer genehmigen
gg-op-unapprove = Genehmigung entfernen
gg-op-unapproveall = alle Genehmigungen entfernen
gg-unknown = Unbekannt
gg-chat-id = Chat-ID:
    ID: { $id }
gg-on = Ein
gg-off = Aus
gg-anon-enabled = Die Annahme anonymer Administratorrechte ist hier aktiv. Anonyme Befehle derselben Gruppe verwenden die Rechte des Bots, ohne eine Person zu identifizieren. Eigentümeraktionen benötigen weiterhin den geprüften Ersteller. /anonadmin off aktiviert wieder die menschliche Prüfung.
gg-right-invite_users = Benutzer einladen
gg-right-promote_members = Administratoren ernennen
gg-right-manage_topics = Themen verwalten
gg-right-creator = Gruppenersteller
gg-log-join = Mitglied beigetreten.
    Mitglied: { $user }
gg-log-leave = Mitglied ausgetreten.
    Mitglied: { $user }
gg-warning-row = Verwarnungseintrag:
    Ablauf: { $expiry }
    ID: { $id }
    Grund: { $reason }
gg-menu-prompt = Wähle eine Option.
gg-content-invalid = Der Inhalt ist ungültig oder überschreitet Telegram-Grenzen. Prüfe Name, Format, Modifikatoren und Schaltflächen.
gg-content-unavailable = Der Inhalt ist nicht verfügbar oder deine aktuelle Gruppenmitgliedschaft erlaubt keinen Zugriff.
gg-btn-private-note = Notiz öffnen
gg-open-private = Diesen Inhalt privat öffnen:
gg-items-cleared = Einträge gelöscht.
    Anzahl: { $count }
gg-clearall-confirm = Der Gruppenersteller bestätigt mit <code>/{ $command } confirm</code>.
gg-button-usage = Nutze <code>/button "Beschriftung" https://example.com</code>. Ergänze die Zeile <code>"Notiz" #Name same</code> für eine weitere Schaltfläche in derselben Reihe. Du erhältst Markup und eine funktionierende Vorschau.
gg-btn-accept-rules = Regeln annehmen
gg-btn-open-verification = Prüfung öffnen
gg-captcha-private = Öffne die private Aufgabe zur Bestätigung deiner Gruppenmitgliedschaft.
    Mitglied: { $user }
gg-captcha-choice = Wähle mit den Schaltflächen die passende Abbildung. Modus und Zeichenposition stehen unten.
    Modus: { $mode }
    Position: { $position }
gg-captcha-settings = Einstellungen der Mitgliedsprüfung:
    Aktiviert: { $enabled }
    Entfernen: { $kick }
    Modus: { $mode }
    Aufhebung: { $release }
    Sekunden: { $seconds }
gg-captcha-dependency = Aktiviere Begrüßungen vor der Prüfung. Speichere Regeln, bevor du deren Zustimmung verlangst.
gg-val-text = Textabbildung
gg-val-text2 = Zeichenabbildung
gg-captcha-attempts-exhausted = Nach zu vielen falschen Antworten ist die Prüfung fehlgeschlagen; die vorgesehene Einschränkung wurde angewendet.
gg-captcha-admin-exempt = Du bist jetzt Gruppenadministrator. Die Prüfung wurde beendet.
gg-captcha-question-text = Wähle das Wort, das in der Abbildung steht.
gg-captcha-question-math = Löse die Gleichung in der Abbildung und wähle die Antwort.
gg-captcha-question-text2 = Wähle das angegebene Zeichen in der Abbildung von links nach rechts.
    Position: { $position }
gg-locktypes = Verfügbare Inhaltssperren:
    Typen: { $types }
gg-allowlist-title = Ausnahmen von Inhaltssperren
gg-allowlist-invalid = Ungültige Ausnahme. Nutze Domain/Pfad, exakte Einladung, @Chat oder eine deklarierte Identität wie stickerpack:Name.
gg-reason-lock = Gesperrter Inhalt:
    Typen: { $types }
gg-lock-applied = Die Sperrregel wurde angewendet.
    Grund: { $reason }
    Typen: { $types }
gg-reaction-failed = Die Reaktionsregel konnte nicht angewendet werden. Dieser Bot-API-Server unterstützt möglicherweise keine Reaktionsentfernung.
    Code: { $code }
gg-reaction-anonymous = Anonyme Reaktionszahlen enthalten keine Benutzer- oder Akteurschat-ID. Die Entfernungs-API benötigt eine; eine Entfernung wird nicht behauptet.
gg-none = Keine
gg-blocklist-title = Sperrliste
gg-blocklist-invalid = Ungültiger Auslöser, Grund oder Aktion. Prüfe Anführungszeichen, Maskierung von Platzhaltern und die benötigte Dauer temporärer Modi.
gg-blocklist-settings = Einstellungen der Sperrliste:
    Löschung: { $delete }
    Modus: { $mode }
gg-blocklist-action = Die Sperrlistenregel wurde auf das Mitglied angewendet.
    Grund: { $reason }
    Mitglied: { $user }
gg-lock-album = Alben
gg-lock-anonchannel = Kanalabsender
gg-lock-audio = Audio
gg-lock-bot = Bots
gg-lock-button = Inline-Schaltflächen
gg-lock-cashtag = Währungsmarkierungen
gg-lock-checklist = Checklisten
gg-lock-cjk = Chinesischer/japanischer/koreanischer Text
gg-lock-command = Befehle
gg-lock-comment = Kommentare von Nichtmitgliedern
gg-lock-contact = Kontakte
gg-lock-cyrillic = Kyrillischer Text
gg-lock-document = Dokumente
gg-lock-email = E-Mail-Adressen
gg-lock-emoji = Emoji
gg-lock-emojicustom = Benutzerdefinierte Emoji
gg-lock-emojigame = Emoji-Spiele
gg-lock-emojionly = Nur-Emoji-Text
gg-lock-externalreply = Externe Antworten
gg-lock-forward = Weiterleitungen
gg-lock-forwarduser = Benutzerweiterleitungen
gg-lock-forwardbot = Botweiterleitungen
gg-lock-forwardchannel = Kanalweiterleitungen
gg-lock-forwardstory = Weitergeleitete Geschichten
gg-lock-game = Spiele
gg-lock-gif = GIF-Animationen
gg-lock-guestbot = Gastbots
gg-lock-inline = Inline-Bots
gg-lock-invitelink = Telegram-Einladungen
gg-lock-botlink = Botlinks
gg-lock-location = Standorte
gg-lock-outsidereaction = Reaktionen von Nichtmitgliedern
gg-lock-phone = Telefonnummern
gg-lock-photo = Fotos
gg-lock-poll = Umfragen
gg-lock-reaction = Reaktionen
gg-lock-rtl = Rechts-nach-links-Text
gg-lock-spoiler = Verdeckte Inhalte
gg-lock-sticker = Sticker
gg-lock-stickeranimated = Animierte Sticker
gg-lock-stickerpremium = Premium-Sticker
gg-lock-text = Text
gg-lock-url = URLs
gg-lock-video = Videos
gg-lock-videonote = Videonachrichten
gg-flood-status = Nachrichtenflut: Der aufeinanderfolgende Grenzwert greift bei N, das Zeitfenster bei mehr als N. Aktion, Dauer und Sequenzbereinigung stehen unten.
    Ganze Sequenz bereinigen: { $clear }
    Aufeinanderfolgende Grenze: { $consecutive }
    Anzahl: { $count }
    Dauer: { $duration }
    Modus: { $mode }
    Sekunden: { $seconds }
gg-raid-status = Schutz vor Massenbeitritten. Einschalten: /antiraid on; stoppen: /antiraid off. Zeitraum, Sperrdauer und automatische Beitrittsgrenze pro Minute stehen unten.
    Aktiv: { $active }
    Automatische Grenze: { $auto }
    Sperrdauer: { $ban }
    Zeitraum: { $period }
    Bis: { $until }
gg-raid-banned = 🛡 Das Mitglied wurde während des aktiven Angriffsschutzes vorübergehend gesperrt.
    Mitglied: { $user }
gg-raid-declined = 🛡 Die Beitrittsanfrage wurde während des aktiven Angriffsschutzes abgelehnt.
    Mitglied: { $user }
gg-silent-consent-required = Der Ersteller muss stille Aktionen erlauben und ein Protokoll konfigurieren, bevor diese Aktion gewählt wird.
gg-btn-enable-raid = Angriffsschutz aktivieren
gg-human-required = Diese Aktion erfordert einen identifizierbaren Menschen.
gg-group-message-required = Nutze diesen Befehl an einer echten Gruppennachricht oder einem Thema. Private Nachrichten-IDs bezeichnen keine Gruppennachrichten.
gg-connection-private = Nutze diesen Verbindungsbefehl in unserem privaten Chat.
gg-connection-disconnected = Getrennt. Deine letzten fünf Gruppen bleiben zum erneuten Verbinden verfügbar.
gg-connection-current = Gruppe verbunden. Mitgliedschaft und aktuelle Rechte werden für jede Aktion geprüft.
    Gruppe: { $group }
gg-connection-none = Keine aktive Verbindung. Nutze /connect GROUP_ID oder /connect @Gruppe.
gg-connection-open = Öffne deine persönliche Verbindung in unserem privaten Chat.
gg-btn-connect = Privat verbinden
gg-connection-history = Deine letzten fünf Gruppen. Wähle eine zum Verbinden; aktuelle Mitgliedschaft ist erforderlich.
gg-connection-unavailable = Verbindung nicht verfügbar. Du musst ein aktuelles menschliches Mitglied und der Bot ein Administrator dort sein.
gg-catalog-unresolved = /{ $command } steht im Katalog ohne definierte Aktion. Nutze /notes oder /flood für implementierte Funktionen.
gg-cleanup-failed = Nachrichtenbereinigung fehlgeschlagen oder nicht verfügbar; keine Löschung wird behauptet.
gg-op-lock_change = Inhaltssperren ändern
gg-op-allowlist_change = Sperrausnahmen ändern
gg-op-allowlist_clear = Sperrausnahmen löschen
gg-op-blocklist_change = Sperrliste ändern
gg-op-blocklist_clear = Sperrliste leeren
gg-op-raid_change = Angriffsschutz ändern
gg-disabled-list = Befehlspolitik: /disable NAME und /enable NAME steuern die Ausführung; /disabledel die Löschung; /disableadmin bezieht Administratoren ein.
    Befehle: { $commands }
gg-cleanup-types = Verfügbare Bereinigungskategorien:
    Typen: { $types }
gg-cleanup-selected = Gewählte Bereinigungskategorien:
    Typen: { $types }
gg-advanced-status = Stille Automatik benötigt Zustimmung des Erstellers und ein Protokoll. Bots benötigen normale Rechte; die Prüfung von Änderungen bleibt standardmäßig aktiv. Stelle die Sichtbarkeit zwischen Bots in BotFather ein.
    Einstellung: { $setting }
    Wert: { $value }
gg-action-topic = Aktionsthema. /setactiontopic wählt das aktuelle Forumthema; das allgemeine Thema hat ID 1.
    Thema: { $topic }
gg-topic-unavailable = Ein aktuelles Forum und die passenden Verwaltungsrechte sind erforderlich.
gg-topic-id-required = Gib im verbundenen privaten Chat die Themen-ID ausdrücklich an.
gg-topic-general-delete = Das allgemeine Thema kann nicht gelöscht werden. Die Bestätigung benötigt einen identifizierbaren Menschen.
gg-topic-delete-confirm = Thema und Nachrichten löschen? Die persönliche Bestätigung ist zwei Minuten gültig.
    Thema: { $topic }
gg-btn-confirm-delete = Löschung bestätigen
gg-topic-changed = Themenaktion abgeschlossen.
    Aktion: { $action }
    Thema: { $topic }
gg-op-policy_change = Befehls-/Bereinigungsrichtlinie ändern
gg-op-topic_create = Thema erstellen
gg-op-topic_rename = Thema umbenennen
gg-op-topic_close = Thema schließen
gg-op-topic_reopen = Thema wieder öffnen
gg-op-topic_delete = Thema und Nachrichten löschen
gg-op-echo = formatierten Inhalt senden
gg-broadcast-owner = Nur der konfigurierte Operator dieses Bots oder der tatsächliche Eigentümer der Kindinstanz darf deren Gruppen anschreiben.
gg-broadcast-queued = Gruppenrundsendung eingereiht. Ziele und Ergebnisse sind pro Bot getrennt.
    ID: { $id }
gg-broadcast-busy = Eine andere Rundsendung ist aktiv oder das fünfminütige Erstellungsintervall ist noch nicht abgelaufen.
gg-broadcast-empty = Du hast keine Gruppenrundsendung in diesem Bot.
gg-broadcast-status = Status der Gruppenrundsendung:
    Abgebrochen: { $cancelled }
    Fehlgeschlagen: { $failed }
    ID: { $id }
    Eingereiht: { $queued }
    Zugestellt: { $sent }
    Status: { $status }
    Unklarer Ausgang: { $uncertain }
gg-fed-created = Föderation erstellt. Die ID gehört zum getrennten Netzwerk dieses Bots.
    ID: { $id }
    Name: { $name }
gg-fed-info = Informationen zur Föderation:
    Administratoren: { $admins }
    ID: { $id }
    Protokoll: { $log }
    Name: { $name }
    Benachrichtigungen: { $notifications }
    Eigentümer: { $owner }
    Gründe erforderlich: { $reasons }
gg-fed-list = Deine Föderationen als Eigentümer oder Administrator:
    { $rows }
gg-fed-admins = Zuerst der Eigentümer, danach die Föderationsadministratoren:
    { $rows }
gg-fed-quiet = Stille passive Erklärungen. Die Durchsetzung bleibt aktiv.
    Wert: { $value }
gg-fed-policy = Regeln für Gründe und Eigentümerbenachrichtigungen:
    Benachrichtigungen: { $notifications }
    Gründe erforderlich: { $reasons }
gg-fed-confirm-delete = Föderation, Daten und Mitgliedschaften dauerhaft löschen? Bestehende Telegram-Sperren bleiben. Persönliche Bestätigung innerhalb von fünf Minuten.
    ID: { $id }
    Name: { $name }
gg-fed-confirm-log = Das angegebene Föderationsprotokoll einrichten? Bestätige innerhalb von fünf Minuten. Deine Zielrechte und die Veröffentlichungsrechte des Bots werden erneut geprüft.
    Ziel: { $destination }
    ID: { $id }
    Name: { $name }
gg-fed-confirm-sent = Eine persönliche Bestätigung wurde an den Föderationseigentümer gesendet.
gg-fed-deleted = Föderation gelöscht. Bestehende Telegram-Sperren bleiben erhalten.
gg-fed-log-set = Ziel des Föderationsprotokolls eingestellt:
    Ziel: { $destination }
gg-fed-cancel = Abbrechen
gg-fed-cancelled = Abgebrochen.
gg-fed-saved-delivery-failed = Änderung gespeichert, aber Benachrichtigung oder Protokoll nicht zugestellt. Prüfe Ziel und Botzugriff.
gg-fed-error-authority = Diese Aktion benötigt den aktuellen Föderationseigentümer oder die passende Föderationsrolle. Telegram-Gruppenrechte vergeben keine Föderationsrechte.
gg-fed-error-private = Nutze diesen Befehl in deinem eigenen privaten Chat mit diesem Bot.
gg-fed-error-group = Nutze diesen Befehl in der tatsächlichen Gruppe. Eine private Verbindung wählt keine Föderationsgruppe.
gg-fed-error-owned = Du besitzt bereits eine Föderation in diesem Bot. Nutze /fedinfo, /renamefed oder /delfed privat.
gg-fed-error-name = Gib einen nichtleeren Namen ohne Steuerzeichen an. Namen werden auf 64 Zeichen begrenzt.
gg-fed-error-id = Gib eine gültige Föderations-UUID dieses Bots an. Rose-IDs verbinden sich nicht mit unserem getrennten Dienst.
gg-fed-error-missing = Keine Föderation in diesem Bot oder Kontext gefunden.
gg-fed-error-creator = Nur der aktuelle Telegram-Gruppenersteller darf die Gruppe einer Föderation anschließen oder entfernen.
gg-fed-error-target = Gib eine positive menschliche ID, eine Antwort an einen Menschen oder einen aktuell geprüften Namen an. Der Eigentümer kann nicht abgesetzt werden.
gg-fed-error-value = Ungültige Föderationsargumente. Nutze on/off für Richtlinien und eine gültige ID, wo benötigt.
gg-fed-error-stale = Bestätigung abgelaufen, verwendet oder Föderation, Eigentümer beziehungsweise Ziel geändert. Fordere eine neue an.
gg-fed-error-destination = Der Eigentümer braucht aktuelle Administratorrechte am Ziel, der Bot Veröffentlichungszugriff. Kanäle benötigen post_messages.
gg-fed-error-delivery = Die persönliche Bestätigung konnte nicht zugestellt oder gebunden werden. Öffne einen privaten Chat mit dem Bot und versuche es erneut.
gg-fed-event = Ereignis der Föderation:
    Ereignis: { $event }
    ID: { $id }
    Name: { $name }
    Mitglied: { $user }
gg-fed-event-rename = Name geändert
gg-fed-event-delete = gelöscht; Telegram-Sperren bleiben
gg-fed-event-promote = Administrator hinzugefügt
gg-fed-event-demote = Administrator entfernt
gg-fed-event-self-remove = Administrator zurückgetreten
gg-fed-event-reason = Regel für Sperrgründe geändert
gg-fed-event-notif = Eigentümerbenachrichtigungen geändert
gg-fed-event-log = Protokollziel geändert
gg-fed-event-unlog = Protokollziel entfernt
gg-fed-event-ban = Sperrregel gespeichert; Durchsetzung eingereiht
gg-fed-event-unban = Sperrregel entfernt; Aufhebung eigener Einschränkungen eingereiht
gg-fed-event-subscribe = Abonnement hinzugefügt; beobachtete Benutzer zur Prüfung eingereiht
gg-fed-event-unsubscribe = Abonnement entfernt; andere Quellen bleiben erhalten
gg-fed-ban-details = Ziel und Grund der Sperre:
    Grund: { $reason }
    Mitglied: { $user }
gg-fed-passive = Die Föderationsregel sperrt das Mitglied. Quelle und Grund stehen unten.
    ID: { $id }
    Grund: { $reason }
    Quelle: { $source }
    Mitglied: { $user }
gg-fed-enforce-failed = Die Föderationsregel sperrt das Mitglied, aber die Entfernung ist fehlgeschlagen. Prüfe Botrechte. Quelle und Grund stehen unten.
    ID: { $id }
    Grund: { $reason }
    Quelle: { $source }
    Mitglied: { $user }
gg-fed-stat = Föderationssperren dieses Mitglieds:
    { $rows }
    Mitglied: { $user }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — aktiv: { $status }; geändert: { $date }.
gg-fed-stat-more = Weitere Quellen vorhanden. Nutze den Fortsetzungsbefehl oder eine bestimmte Föderations-ID für Grund und Datum.
gg-fed-intent-saved = Die Regel wurde gespeichert; beobachtete Ziele sind eingereiht. Vor Auswirkungen werden aktuelle Rechte und andere Einschränkungsquellen geprüft.
    Mitglied: { $user }
    Version: { $version }
gg-fed-subscriptions = Direkte Abonnements von Föderationssperren:
    { $rows }
gg-fed-imported = Einträge geprüft und gespeichert; identische Duplikate übersprungen. Die Durchsetzung an beobachteten Zielen ist eingereiht.
    Anzahl: { $count }
    Identische Duplikate: { $duplicates }
gg-fed-event-import = geprüfte Sperren importiert; Durchsetzung eingereiht
gg-fed-error-file-format = Antworte auf UTF-8-CSV mit id/reason, JSONL/NDJSON mit user_id oder den JSON-Array-Export dieses Bots. Eine ungültige Zeile verhindert alle Schreibvorgänge.
gg-fed-error-file-limit = Höchstens 2 MiB und 1000 Einträge. Fehlende oder zu große Dateien werden abgelehnt; Listen werden nie still gekürzt.
gg-fed-error-file-duplicate = Widersprüchliche Einträge für dieselbe Benutzer-ID. Keine Sperren importiert.
gg-fed-error-file-rate = Import und Export teilen ein Intervall von 30 Minuten je Föderation. Versuche es später erneut.
gg-fed-error-reason = Sperrgründe dürfen höchstens 1024 Zeichen ohne nicht unterstützte Steuerzeichen enthalten.
gg-fed-error-reason_required = Diese Föderation verlangt für jede Sperre einen nichtleeren Grund.
gg-fed-error-cycle = Eine Föderation darf sich nicht selbst abonnieren oder einen gerichteten Kreis erzeugen.
gg-fed-error-graph_limit = Abonnementgrenze erreicht: 32 direkte Ziele, 128 erreichbare Föderationen, Tiefe 16 oder 10 000 Verbindungen in diesem Bot.
gg-data-confirm = Bestätige diese Aktion innerhalb von fünf Minuten. Aktueller Ersteller und Gruppenrevision werden erneut geprüft. Nur ausgewählte Module ändern sich; Identität, Vertrauen und aktive Sperren bleiben.
    SHA-256: { $digest }
    Gruppe: { $group }
    Module: { $modules }
    Operation: { $operation }
gg-data-import = Gruppenmodule importieren
gg-data-reset = Gruppenmodule zurücksetzen
gg-data-privacy-delete = Optionale persönliche Daten dieses Bots löschen
gg-data-confirm-button = Diese Änderung bestätigen
gg-data-personal = Öffne die Bestätigung in deinem privaten Chat.
gg-data-saved = Ausgewählte Module gespeichert.
gg-data-error-authority = Import und Zurücksetzen benötigen den aktuell identifizierbaren Gruppenersteller. Export benötigt einen aktuellen Administrator.
gg-data-error-format = Antworte auf gültiges versioniertes Group-Guard-JSON, erstellt mit /export.
gg-data-error-limit = Die Datei überschreitet Größe oder konfigurierte Inhaltsgrenze.
gg-data-error-version = Schema oder Version nicht unterstützt; keine Änderungen angewendet.
gg-data-error-module = Wähle bekannte Module: /export all oder /export notes rules. Import und Zurücksetzen verwenden dieselben Namen.
gg-data-error-field = Ungültige oder fehlende Modulfelder. Keine Einstellungen angewendet.
gg-data-error-item = Inhalt, Optionen oder Wiederholungszugriff ungültig. Kein Inhalt gespeichert.
gg-data-error-media = Medien müssen an diesen Bot hochgeladen und über getFile erreichbar sein. Datei-IDs anderer Bots werden nicht unterstützt.
gg-data-error-destination = Protokoll- und Themenziele benötigen aktuelle Rechte und Botfähigkeiten. Themen-IDs gelten nur innerhalb derselben Gruppe.
gg-data-error-language = Wähle eine installierte Sprache mit /setlang.
gg-data-error-stale = Bestätigung abgelaufen, geändert oder verwendet. Beginne erneut.
gg-data-error-restore = Eigene temporäre Einschränkungen konnten nicht sicher wiederhergestellt werden. Nachweise bleiben; prüfe die Rechte des Bots.
gg-data-error-rate = Gruppendatenoperationen haben ein lokales Intervall von fünf Minuten. Versuche es später erneut.
gg-data-error-delivery = Private Bestätigung nicht zugestellt. Starte einen privaten Chat mit dem Bot und versuche es erneut.
gg-data-error-saved_delivery = Einstellungen gespeichert, aber Befehlsvorschläge nicht aktualisiert. Prüfe Botberechtigungen.
gg-privacy-policy = <b>Deine Daten in diesem Group Guard</b>
    /privacy data exportiert deine Verbindungen, beobachteten Profile, Verwarnungen, Genehmigungen, Einschränkungs-/Prüfstatus, Föderationseigentum/-rollen/-sperren und Sicherheitsaufträge. Fremde private Inhalte, Prüfantworten, Authentifizierung und Rohdateien sind ausgeschlossen. Folge dem Fortsetzungsbefehl.
    /privacy delete entfernt optionale Verbindungshistorie, beobachteten Namen/Benutzernamen, inaktive Prüfungen und abgeschlossene persönliche Kampagneninhalte dieses Bots. Aktive Verwarnungen/Einschränkungen, Sperrversionen, Rollen, Eigentum, Abonnements, Wiederholungsschutz und unklare API-Arbeit behalten minimale Sicherheits- und Ordnungskennungen. Nutze ausdrückliche Föderationsrücktritts-/Löschbefehle für diese Beziehungen. Das gemeinsame Plattformprofil und andere Bots bleiben.
    Operatoren verwalten Sicherungen und Audit getrennt. Dieser Befehl löscht keine externen Telegram-Nachrichten oder Sicherungen und verspricht keine automatische Aufbewahrungsdauer.
gg-privacy-usage = /privacy policy · /privacy data [Fortsetzung] · /privacy delete — nur in deinem eigenen privaten Chat mit diesem Bot.
gg-privacy-private = Diese Aktion erfordert den privaten Chat der anfragenden Person. Ungültige Cursor geben keinen Zugriff auf fremde Daten.
gg-privacy-next = Nächste Datenseite: /privacy data { $cursor }
gg-privacy-deleted = Optionale persönliche Daten dieses Bots entfernt. Aktive Sicherheit, Eigentum und unklare Arbeit behalten minimale Kennungen; siehe /privacy policy.
gg-language-usage = Wähle die Gruppensprache mit /setlang. /lang privat ändert deine persönliche Plattformsprache. Die verfügbaren Codes stehen unten.
    Sprachcodes: { $codes }
gg-language-saved = Antwortsprache der Gruppe geändert.
gg-help-index = <b>Group-Guard-Befehlsübersicht</b>
    /help Bereich · /help Befehl · /help Bereich 2. Angegebene Befehle funktionieren auch über geprüftes /connect; private Antworten bleiben im tatsächlichen privaten Chat.
    Einstellungen brauchen Informationsänderung, Sanktionen Mitgliedereinschränkung, Löschung Löschrechte, Anheften Anheftrechte, Ernennungen Administratorernennung, Themen Themenverwaltung. Botrechte werden getrennt geprüft. Eigentümeraktionen brauchen den aktuellen menschlichen Ersteller. /settings öffnet deine persönliche Gruppenübersicht.
gg-help-search = <b>Passende Befehle</b>
    Suche: { $query }
gg-help-connected = Gruppe oder geprüfte Verbindung; Rechte stehen im Bereich
gg-help-group-only = Eine echte Gruppennachricht ist nötig
gg-help-unsupported = Katalogname erhalten; nicht belegtes Verhalten gibt eine Erklärung zurück
gg-help-next = Nächste Seite
gg-help-previous = Vorherige Seite
gg-help-family-title-moderation = Moderation und Genehmigungen
gg-help-family-title-messages = Nachrichten löschen und anheften
gg-help-family-title-logging = Autorisierte Protokolle
gg-help-family-title-settings = Gruppeneinstellungen und Sprache
gg-help-family-title-content = Notizen, Filter, Regeln und Begrüßungen
gg-help-family-title-captcha = Prüfung neuer Mitglieder
gg-help-family-title-locks = Inhaltssperren und Ausnahmen
gg-help-family-title-blocklists = Sperrlistentreffer und Aktionen
gg-help-family-title-antispam = Schutz vor Nachrichtenflut und Angriffen
gg-help-family-title-connections = Private Gruppenverbindungen
gg-help-family-title-identity = Benutzer- und Chatinformationen
gg-help-family-title-policy = Befehls- und Botrichtlinien
gg-help-family-title-cleanup = Bereinigung von Befehlen, Bots und Diensten
gg-help-family-title-topics = Forumthemen
gg-help-family-title-utilities = Inhaltsversand und Operatorkampagnen
gg-help-family-title-federations = Föderationsrollen, Sperren und Abonnements
gg-help-family-title-portability = Gruppendateien und persönliche Daten
gg-help-family-title-discovery = Hilfe und Inhaltseditor
gg-help-family-moderation = <b>Moderation</b> · Antwort, Zahlen-ID oder aktuell geprüfter @Benutzer. /ban 20 Grund; /tban 20 60s Grund; /mute 20; /tmute 20 2h Grund. Temporäre Sanktionen: 60 Sekunden–365 Tage. /kickme entfernt nur dich. d-Varianten löschen die beantwortete Nachricht, s-Varianten Befehl/Antwort und benötigen Löschrechte. Administratoren sind geschützt. /setwarnlimit 3; /setwarnmode ban; /setwarntime 1d. Neue Gruppen nutzen drei Verwarnungen; alte Einstellungen bleiben. /approve umgeht nur normalen Inhalts-/Flutschutz, niemals Föderation/CAS/Angriff/manuelle Aktionen. /promote gewährt höchstens die gemeinsamen Rechte von Anfragendem und Bot. Massenzurücksetzen braucht den Ersteller.
gg-help-family-messages = <b>Nachrichten</b> · /del braucht eine echte Gruppenantwort. /purge beginnt dort; /purgefrom und /purgeto speichern Grenzen. Konfigurierte Grenzen und Telegram-Regeln gelten; eine Batchbestätigung ist keine genaue Löschanzahl. /pin [loud], /permapin, /unpin und /unpinall brauchen Anheftrechte; alles lösen braucht den Ersteller. /antichannelpin und /cleanlinked steuern automatische Nachrichten des verknüpften Kanals.
gg-help-family-logging = <b>Protokolle</b> · /setlog -100… braucht aktuelle Zieladministration und Veröffentlichungsrechte des Bots. Weitergeleitete Einrichtung muss einem tatsächlich empfangenen Original entsprechen. /logcategories: settings/admin/user/automated/reports/other; /log und /nolog wählen Kategorien. Lieferfehler bleiben sichtbar und beweisen keinen Aktionserfolg.
gg-help-family-settings = <b>Einstellungen</b> · /settings öffnet eine persönliche ablaufende Übersicht mit aktueller Prüfung der Informationsänderung. /setlang code speichert die Gruppensprache; private /lang die persönliche Sprache. /night 23 7 +3 schließt über Nacht; /night off stellt nur den eigenen weiterhin passenden Berechtigungsstand wieder her. Externe Änderungen haben Vorrang.
gg-help-family-content = <b>Editor</b> · /save Wort Text oder Antwort auf Medien; /get Wort, #Wort, /notes lesen Notizen. Notiznamen sind einzelne Wörter; alte breitere Namen bleiben. /filter "Phrase" Text, /filterprefix und /filterexact bestimmen Treffer; /stop löscht den Schlüssel. /clearall und /stopall bestätigt der Ersteller. Rose unterstützt fett/kursiv/unterstrichen/durchgestrichen/Code, Links, Zitate und zufällige %%% Alternativen. Felder: { "{" }first{ "}" }, { "{" }last{ "}" }, { "{" }fullname{ "}" }, { "{" }username{ "}" }, { "{" }mention{ "}" }, { "{" }id{ "}" }, { "{" }chatname{ "}" }, { "{" }count{ "}" }. /button erzeugt funktionierende URL-/Notiz-/Regelschaltflächen. Allgemeine Optionen preview/nonotif/protect/mediaspoiler; Notizen admin/private/noprivate/repeat; Filter user/allow_bot/replytag/command. /save Wort Hallo { "{" }repeat 5m{ "}" } plant nur öffentliche Inhalte mit aktuellen Autorenrechten. Regeln, Grüße und private Inhalte teilen denselben Renderer. Medien-IDs gehören zum Bot.
gg-help-family-captcha = <b>Prüfung</b> · /captcha on/off; /captchamode off/button/math/text/text2; /setcaptchatext; /captcharules on; /captchakick on/off; /captchakicktime und /captchamutetime setzen begrenzte Fristen. Ausgegebene Aufgaben behalten Generation/Frist. Anfragen brauchen invite-users, Mitgliedsstille restrict-members. Antworten sind persönlich und einmalig. Föderationssperren gehen Genehmigung/CAPTCHA vor.
gg-help-family-locks = <b>Inhaltssperren</b> · /lock links [Aktion], /unlock Typ; /locktypes zeigt reale Typen, /locks den Zustand. /lockwarns steuert Verwarnungen. /allowlist: Domain/Pfad, exakte Einladung, @Chat oder stickerpack:/forward:/inline:/channel:/chat:/bot:/command:. Ungültige Muster werden abgelehnt. Ausnahmen gelten nur für passende Sperrinhalte; stille Automatik braucht Erstellerzustimmung und autorisiertes Protokoll.
gg-help-family-blocklists = <b>Sperrliste</b> · /addblocklist "Phrase" unterstützt Text/Präfix/exakt und deklarierte Identitäten mit optionalem Grund/Aktion. /rmblocklist entfernt exakt ausgewählte Schlüssel. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute setzt die Aktion; temporäre Modi brauchen Dauer. /blocklistdelete steuert Löschen getrennt. Platzhaltermuster sind begrenzt; ungültige Einträge und Überschreitungen werden abgelehnt.
gg-help-family-antispam = <b>Flut und Angriffe</b> · /setflood Anzahl für aufeinanderfolgende Nachrichten; /setfloodtimer Anzahl Dauer für Zeitfenster; /setfloodmode für Sanktion/Dauer; /clearflood zum Löschen der Sequenz. Alte Einstellungen bleiben. /flood und /antiflood zeigen die Richtlinie; deren Alias ist eine lokale Kompatibilitätsentscheidung. /antiraid on/off/duration, /raidtime, /raidactiontime, /autoantiraid speichern Frist und getrennte Sanktion für Neueintritte. Vorrang vor Genehmigung/CAPTCHA; Ablauf ist generationsgebunden und neustartsicher.
gg-help-family-connections = <b>Verbindungen</b> · /connect groupID oder persönlicher Link. Deine Mitgliedschaft und die des Bots werden geprüft; Änderungen brauchen weiterhin genaue aktuelle Rechte. /connection zeigt die Auswahl, /disconnect entfernt sie, /connect zeigt Verlauf mit Fortsetzung. Verbindung verleiht weder Föderationseigentum noch Operatorrechte.
gg-help-family-identity = <b>Informationen</b> · /id zeigt echte Benutzer-/Chat-/Quell-IDs, /info das aktuelle Ziel. Antworten und @Namen brauchen aktuelle scoped Nachweise. Eine anonyme Gruppennachricht identifiziert keinen Menschen; es wird keine menschliche ID erfunden.
gg-help-family-policy = <b>Richtlinien</b> · /disable Befehl, /enable Befehl, /disabled, /disableable nutzen kanonische Namen und Aliasnamen. /disableadmin steuert Administratorausnahmen, /disabledel das Löschen. Wiederherstellungsbefehle bleiben erreichbar. /bot2bot off/admin/all prüft echte Mitgliedschaft; Änderungen benötigen normalerweise menschliche Prüfung. /bot2botskipreview ist nur für den Ersteller. /silentactions benötigt Zustimmung und autorisiertes Protokoll. Unbelegte runs/saved geben eine Erklärung.
gg-help-family-cleanup = <b>Bereinigung</b> · /cleancommand admin/user/other und /keepcommand wählen Befehle. /cleanmsg action/filter/note und /keepmsg wählen nur tatsächlich von diesem Bot gesendete Nachrichten; Belege und Fünfminutenaufträge verhindern geratene IDs. /cleanservice und /nocleanservice: join/leave/other/photo/pin/title/videochat. Funktionale Verarbeitung und gültige Zahlungen erfolgen vor Bereinigung.
gg-help-family-topics = <b>Themen</b> · /newtopic Name, /renametopic Name, /closetopic, /reopentopic arbeiten im aktuellen echten Thema. /deletetopic benötigt Erstellerbestätigung; /setactiontopic wählt ein Ziel derselben Gruppe. Telegram-Forum und manage-topics erforderlich. Fehler bei fehlendem/nicht unterstütztem Thema werden ehrlich gemeldet.
gg-help-family-utilities = <b>Werkzeuge</b> · /echo und /say senden direkte oder beantwortete Inhalte durch den gemeinsamen begrenzten Renderer. /broadcast ist dem konfigurierten Operator oder tatsächlichen Kindeigentümer vorbehalten und erreicht nur konfigurierte Gruppen dieses Bots. Ergebnisse je Ziel erhalten teilweise/unklare Lieferungen; Status und Abbruch wiederholen keine erfolgreichen Anhänge.
gg-help-family-federations = <b>Föderationen</b> · /newfed Name erzeugt eine UUID in diesem Bot. Private Befehle nutzen deine eigene Föderation unabhängig von Gruppenverbindungen; UUID-Lesen verleiht keine Rolle. /fedpromote und /feddemote verwalten Administratoren, /feddemoteme tritt zurück. /joinfed UUID und /leavefed brauchen den aktuellen Gruppenersteller. Löschung hebt Telegram-Sperren nicht automatisch auf. /fban userID Grund und /unfban userID brauchen Föderationseigentümer/-admin; /fedreason, /fednotif, /setfedlog den Eigentümer. /quietfed versteckt nur passive Hinweise. /subfed UUID ist gerichtet, begrenzt und kreisfrei. /fedstat [userID], /fbanstat UUID zeigen Quellen/Status. /fbanlist csv/minicsv/json ist eigentümergebunden mit gemeinsamem 30-Minuten-Intervall; /importfbans beantwortet begrenztes CSV oder echtes zeilenweises JSON und unterstützt ausdrücklich das eigene JSON-Array. Nur tatsächlich beobachtete Benutzer werden geprüft, keine vollständige Mitgliederliste behauptet.
gg-help-family-portability = <b>Dateien und Datenschutz</b> · /export all oder Module braucht Administratorrechte; /import und /reset den aktuellen menschlichen Ersteller mit persönlicher fünfminütiger Einmalbestätigung. Lokales Fünfminutenintervall; eigenes versioniertes JSON, höchstens 2MiB und konfigurierte Inhaltsgrenzen. Module: moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Nicht gewählte Module bleiben. Vertrauen, ausgegebene Prüfungen/Aufträge, Abonnements, Rollen und aktive Sperren werden nie importiert. /privacy policy/data/delete funktioniert nur im eigenen privaten Chat mit Datenseiten und minimaler Sicherheitsaufbewahrung. Kein geprüfter Adapter für vollständigen Rose-Export.
gg-help-family-discovery = <b>Hilfe</b> · /help zeigt Bereiche, /help Befehl sucht Namen/Aliasnamen, /help Bereich 2 setzt fort. /button hilft beim Schaltflächenmarkup. Jede Anleitung beschreibt Kontext, Rechte, Vorgaben und Grenzen. /settings öffnet die persönliche Gruppenübersicht.
gg-data-error-cache_pending = Optionale SQL-Daten wurden entfernt. Die Bereinigung des nicht verfügbaren Caches ist eingereiht; aktive Sicherheitsdaten bleiben.
