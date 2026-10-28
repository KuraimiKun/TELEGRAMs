## Independently authored Group Guard pl content.
group-welcome = 🛡 Dziękuję za dodanie! Nadaj mi prawa administratora do usuwania wiadomości, ograniczania członków i przypinania wiadomości. Ustawienia otworzysz przez /settings.
gg-start = 🛡 Witaj <b>{ $name }</b>! Jestem <b>Group Guard</b>: weryfikacja nowych członków, ochrona przed zalewem wiadomości i CAS, blokady treści, moderacja, notatki, filtry, zasady i powitania. Dodaj mnie jako administratora i użyj /settings lub /help.
gg-help = 📖 /help pokazuje działy; /help polecenie wyszukuje polecenia. Moderacja: /ban /mute /kick /warn. Treści: /save /filter /rules. Ochrona: /lock /blocklist /night. /settings otwiera osobisty panel grupy.
gg-welcome-default = 👋 Witaj { "{" }mention{ "}" } w <b>{ "{" }group{ "}" }</b>!
gg-credit = 🛡 Chronione przez @{ $bot }
gg-btn-add = ➕ Dodaj do grupy
gg-btn-commands = 📖 Polecenia
gg-btn-rules = 📜 Zasady
gg-btn-human = ✅ Jestem człowiekiem
gg-btn-unwarn = ↩️ Usuń ostrzeżenie (administratorzy)
gg-btn-locks = 🔒 Blokady treści · Liczba: { $count }
gg-btn-open-settings = ⚙️ Otwórz ustawienia
gg-btn-admin-tab = 🛡 Grupy
gg-captcha = 🤖 Potwierdź w podanym terminie, że jesteś człowiekiem; inaczej zostaniesz usunięty.
    Minuty: { $minutes }
    Członek: { $user }
gg-captcha-button = Naciśnij przycisk poniżej 👇
gg-captcha-math = Ile wynosi <b>{ $a } + { $b }</b>?
gg-captcha-not-you = Ten przycisk jest dla innej osoby.
gg-captcha-ok = ✅ Witaj!
gg-captcha-wrong = ❌ Błędna odpowiedź. Możesz spróbować ponownie, jeśli zostały próby.
    Pozostałe próby: { $left }
gg-captcha-failed = ❌ Zbyt wiele błędnych odpowiedzi.
gg-captcha-passed = ✅ Weryfikacja zaliczona. Witaj!
    Członek: { $user }
gg-cas-banned = 🚫 Członek jest znany CAS jako spamer i został zbanowany.
    Członek: { $user }
gg-join-request = 👋 Potwierdź, że jesteś człowiekiem, aby dołączyć do grupy:
    Grupa: { $group }
gg-join-approved = ✅ Prośba zatwierdzona. Witaj!
gg-join-expired = ⌛ Ta prośba wygasła. Wyślij nową prośbę o dołączenie.
gg-goodbye = 👋 Członek opuścił grupę.
    Członek: { $user }
gg-flood-mute = 🌊 Członek tymczasowo wyciszony za nadmiar wiadomości.
    Członek: { $user }
gg-flood-kick = 🌊 Członek usunięty za nadmiar wiadomości.
    Członek: { $user }
gg-flood-ban = 🌊 Członek zbanowany za nadmiar wiadomości.
    Członek: { $user }
gg-newbie-links = 🆕 Nowi członkowie nie mogą wysyłać linków przez wskazane pierwsze godziny.
    Godziny: { $hours }
    Członek: { $user }
gg-spam-banned = 🧠 Członek zbanowany za spam.
    Członek: { $user }
gg-reason-blocklist = zablokowane słowo
gg-need-right = ⛔ Potrzebujesz odpowiedniego uprawnienia administratora.
    Uprawnienie: { $right }
gg-right-admin = administrator
gg-right-restrict = ograniczanie członków
gg-right-delete = usuwanie wiadomości
gg-right-pin = przypinanie wiadomości
gg-right-change_info = zmiana informacji grupy
gg-admins-only = ⛔ Tylko dla administratorów.
gg-need-target = 👤 Odpowiedz na wiadomość albo podaj ID lub obecnie zweryfikowaną @nazwę użytkownika.
gg-target-admin = 🙅 Ta akcja nie może dotyczyć administratora.
gg-bot-no-rights = ⚠️ Muszę być administratorem z wymaganymi uprawnieniami.
gg-banned = 🔨 Członek zbanowany.
    Powód: { $reason }
    Członek: { $user }
gg-banned-for = 🔨 Członek zbanowany na wskazany czas.
    Powód: { $reason }
    Czas: { $time }
    Członek: { $user }
gg-unbanned = ✅ Ban członka usunięty.
    Członek: { $user }
gg-kicked = 👢 Członek usunięty; może dołączyć ponownie.
    Powód: { $reason }
    Członek: { $user }
gg-muted = 🔇 Członek wyciszony.
    Powód: { $reason }
    Członek: { $user }
gg-muted-for = 🔇 Członek wyciszony na wskazany czas.
    Powód: { $reason }
    Czas: { $time }
    Członek: { $user }
gg-unmuted = 🔊 Członek znów może pisać.
    Członek: { $user }
gg-warned = ⚠️ Ostrzeżenie członka zapisane.
    Liczba: { $count }
    Limit: { $limit }
    Powód: { $reason }
    Członek: { $user }
gg-warn-limit-ban = 🔨 Osiągnięto limit ostrzeżeń; członek zbanowany.
    Limit: { $limit }
    Członek: { $user }
gg-warn-limit-mute = 🔇 Osiągnięto limit ostrzeżeń; członek wyciszony.
    Limit: { $limit }
    Członek: { $user }
gg-warn-limit-kick = 👢 Osiągnięto limit ostrzeżeń; członek usunięty.
    Limit: { $limit }
    Członek: { $user }
gg-unwarned = ↩️ Jedno ostrzeżenie członka usunięte.
    Liczba: { $count }
    Limit: { $limit }
    Członek: { $user }
gg-warn-removed = ↩️ Administrator usunął ostrzeżenie.
    Administrator: { $admin }
gg-warns = ⚠️ Ostrzeżenia członka:
    Liczba: { $count }
    Limit: { $limit }
    Członek: { $user }
gg-warns-reset = 🧽 Ostrzeżenia członka wyzerowane.
    Członek: { $user }
gg-purge-reply = 🧹 Odpowiedz na pierwszą wiadomość do usunięcia.
gg-purged = 🧹 Wiadomości usunięte.
    Liczba: { $count }
gg-pin-reply = 📌 Odpowiedz na wiadomość do przypięcia.
gg-report-reply = 🚨 Odpowiedz na wiadomość do zgłoszenia.
gg-reported = 🚨 Członek zgłoszony administratorom.
    Członek: { $user }
gg-setlog-usage = 📒 Dodaj mnie jako administratora kanału dziennika i użyj <code>/setlog -100…</code> z jego ID.
gg-setlog-failed = ⚠️ Nie mogę tam pisać. Najpierw dodaj mnie jako administratora.
gg-setlog-done = 📒 Kanał dziennika połączony.
gg-setlog-off = 📒 Kanał dziennika odłączony.
gg-log-connected = 📒 Ten czat otrzymuje dziennik moderacji grupy.
    Grupa: { $group }
gg-log-flood = 🌊 Wykryto zalew wiadomości:
    Akcja: { $action }
    Członek: { $user }
gg-log-report = 🚨 Zgłoszenie członka:
    Członek: { $user }
gg-log-spam = 🧠 Ban za spam wykryty przez AI:
    Tekst: { $text }
    Członek: { $user }
gg-rules = 📜 <b>Zasady</b>
    { $rules }
gg-no-rules = 📜 Brak zapisanych zasad. Administratorzy mogą użyć /setrules tekst.
gg-rules-saved = 📜 Zasady zapisane.
gg-rules-cleared = 📜 Zasady usunięte.
gg-welcome-usage = 👋 Użyj <code>/setwelcome Witaj {"{"}mention{"}"} w {"{"}group{"}"}!</code> albo odpowiedz na wiadomość.
gg-welcome-saved = 👋 Powitanie zapisane.
gg-welcome-reset = 👋 Domyślne powitanie przywrócone.
gg-note-usage = 📝 <code>/save nazwa tekst</code> lub odpowiedź na wiadomość z <code>/save nazwa</code>.
gg-filter-usage = 🔁 <code>/filter słowo odpowiedź</code> lub odpowiedź z <code>/filter słowo</code>.
gg-note-saved = 📝 Notatka zapisana. Dostęp: <code>#{ $key }</code>, zgodnie z uprawnieniami.
gg-filter-saved = 🔁 Odpowiem po dopasowaniu „{ $key }”.
gg-notes-empty = 📝 Brak notatek.
gg-filters-empty = 🔁 Brak filtrów.
gg-notes-list = 📝 <b>Notatki</b>
gg-filters-list = 🔁 <b>Filtry</b>
gg-item-deleted = 🗑 Wpis usunięty.
    Klucz: { $key }
gg-item-missing = 🤷 Nic nie zapisano pod tą nazwą.
gg-items-limit = 📦 Osiągnięto limit notatek i filtrów tej grupy.
gg-lock-usage = 🔒 Użyj <code>/lock links</code>. Dostępne typy są poniżej; <code>all</code> wybiera wszystkie.
    Typy: { $types }
gg-locked = 🔒 Zablokowane treści:
    Typy: { $types }
gg-unlocked = 🔓 Dozwolone treści:
    Typy: { $types }
gg-locks-title = 🔒 <b>Blokady treści</b>
gg-locks-panel = 🔒 <b>Blokady</b>: zablokowane treści są usuwane; administratorzy są wyłączeni.
gg-lock-links = Linki
gg-lock-invites = Linki zaproszeń
gg-lock-forwards = Przesłane wiadomości
gg-lock-media = Media
gg-lock-stickers = Naklejki
gg-lock-gifs = GIF-y
gg-lock-voice = Wiadomości głosowe
gg-lock-polls = Ankiety
gg-lock-bots = Boty
gg-blocklist = 🚫 <b>Zablokowane słowa</b>
    Słowa: { $words }
gg-blocklist-empty = 🚫 Brak zablokowanych słów.
gg-blocklist-usage = 🚫 <code>/addblock słowo, inna fraza</code> · <code>/rmblock słowo</code>
gg-blocklist-saved = 🚫 Lista blokad zaktualizowana.
    Liczba: { $count }
gg-night-usage = 🌙 <code>/night 23 7 +3</code> zamyka od 23:00 do 07:00 UTC+3; <code>/night off</code> wyłącza.
gg-night-on = 🌙 Ustawiono godziny nocne grupy.
    Koniec: { $end }
    Początek: { $start }
    Strefa czasowa: { $tz }
gg-night-off = 🌙 Tryb nocny wyłączony.
gg-night-start = 🌙 Dobranoc! Grupa pozostanie zamknięta do wskazanej godziny.
    Koniec: { $end }
gg-night-end = ☀️ Dzień dobry! Grupa znów otwarta.
gg-panel = ⚙️ <b>Ustawienia grupy</b>
    Naciśnij opcję, aby ją zmienić. Godziny nocne ustawia /night.
    Grupa: { $group }
    Godziny nocne: { $night }
gg-panel-sent = 📬 Ustawienia wysłane prywatnie.
gg-panel-start-first = 📬 Najpierw rozpocznij prywatny czat ze mną, potem naciśnij poniżej.
gg-credit-vip = 💎 Ukrycie wiersza ochrony wymaga VIP. Użyj /vip prywatnie.
gg-opt-wel = 👋 Powitania · Wartość: { $value }
gg-opt-cln = 🧹 Usuń wiadomości o dołączeniu · Wartość: { $value }
gg-opt-bye = 👋 Pożegnania · Wartość: { $value }
gg-opt-cap = 🤖 Weryfikacja · Wartość: { $value }
gg-opt-cpm = ⏱ Termin weryfikacji, minuty · Wartość: { $value }
gg-opt-fld = 🌊 Limit wiadomości · Wartość: { $value }
gg-opt-fla = 🌊 Akcja przy nadmiarze wiadomości · Wartość: { $value }
gg-opt-wrn = ⚠️ Limit ostrzeżeń · Wartość: { $value }
gg-opt-wra = ⚠️ Akcja ostrzeżeń · Wartość: { $value }
gg-opt-act = ⏳ Automatyczne ograniczenie, minuty · Wartość: { $value }
gg-opt-cas = 🛡 Ochrona CAS · Wartość: { $value }
gg-opt-nwb = 🆕 Nowi członkowie bez linków, godziny · Wartość: { $value }
gg-opt-ais = 🧠 Ochrona przed spamem AI · Wartość: { $value }
gg-opt-ngt = 🌙 Tryb nocny · Wartość: { $value }
gg-opt-crd = 🏷 Wiersz ochrony · Wartość: { $value }
gg-opt-lang = 🌐 Język · Wartość: { $value }
gg-val-button = Przycisk
gg-val-math = Obliczenie
gg-val-off = wyłączone
gg-val-mute = wycisz
gg-val-kick = usuń
gg-val-ban = zbanuj
gg-adm = 🛡 <b>Group Guard: statystyki</b>
    Grupy: { $groups }
    Wpisy: { $items }
    Ostrzeżenia: { $warns }
cmd-settings = Ustawienia grupy
cmd-help = Przewodnik po poleceniach
gg-auth-denied = Nie udało się zweryfikować uprawnień. Nic nie zmieniono.
gg-target-invalid = Wybierz znanego członka będącego człowiekiem. Nie udało się zweryfikować celu.
gg-duration-invalid = Użyj czasu od 60s do 365d. Polecenia tymczasowe wymagają czasu.
gg-reason-invalid = Powód może mieć najwyżej 256 znaków.
gg-outcome-failed = Akcja nie powiodła się lub nie została autoryzowana.
gg-outcome-partial = Akcja wykonana częściowo. Ban może pozostać, jeśli przywrócenie po usunięciu nie powiedzie się.
gg-outcome-ancillary = Główna akcja zakończona, ale dodatkowy krok nie powiódł się.
gg-review-request = Sprawdź niezmienną akcję poniżej. Osoba z aktualnymi uprawnieniami może zatwierdzić w ciągu 120 sekund. Czas podano w sekundach.
    Szczegóły: { $details }
    Czas: { $duration }
    Operacja: { $operation }
    Cel: { $target }
gg-review-approve = Zatwierdź tę akcję
gg-review-unavailable = Magazyn potwierdzeń niedostępny. Wyślij nowe polecenie.
gg-review-expired = Potwierdzenie wygasło, jest nieprawidłowe lub już użyte.
gg-review-consumed = Potwierdzenie użyte. Sprawdź wynik; ponowienie wymaga nowego polecenia.
gg-duration-permanent = Na stałe / bez limitu czasu
gg-purge-ack = API potwierdziło żądania usunięcia. Rzeczywista liczba usuniętych wiadomości nie jest znana.
    Potwierdzone przez API: { $acknowledged }
    Żądane: { $requested }
gg-warning-removed = Ostrzeżenie usunięte.
gg-op-ban = zbanuj
gg-op-mute = wycisz
gg-op-kick = usuń
gg-op-unban = usuń bana
gg-op-unmute = usuń wyciszenie
gg-op-warn = ostrzeż
gg-op-unwarn = usuń ostrzeżenie
gg-op-resetwarns = wyzeruj ostrzeżenia
gg-op-purge = usuń zakres wiadomości
gg-op-delete = usuń wiadomość
gg-op-pin = przypnij wiadomość
gg-op-unpin = odepnij wiadomość
gg-op-setlog = ustaw cel dziennika
gg-op-unsetlog = usuń cel dziennika
gg-op-config = zmień ustawienia
gg-op-save = zapisz treść
gg-op-remove = usuń treść
gg-op-panel = otwórz panel
gg-review-details-above = Pełna żądana treść znajduje się w wiadomości bezpośrednio powyżej.
gg-warn-pending = Ostrzeżenie zapisane; akcja progowa jest już przetwarzana.
gg-done = Zakończono.
gg-setting-saved = Ustawienie zapisane.
    Ustawienie: { $setting }
gg-setting-value = Aktualna wartość ustawienia:
    Ustawienie: { $setting }
    Wartość: { $value }
gg-setting-invalid = Nieprawidłowe ustawienie. Użyj on/off, poprawnego trybu lub czasu takiego jak 10m.
gg-warning-settings = Ustawienia ostrzeżeń:
    Czas: { $duration }
    Wygaśnięcie: { $expiry }
    Limit: { $limit }
    Tryb: { $mode }
gg-admin-changed = Akcja administracyjna zakończona.
    Akcja: { $action }
    Członek: { $user }
gg-admin-list = Jawni administratorzy:
    { $admins }
gg-approved = Członek zatwierdzony.
    Powód: { $reason }
    Członek: { $user }
gg-unapproved = Zatwierdzenia usunięte.
    Liczba: { $count }
gg-approval-status = Stan zatwierdzenia członka:
    Powód: { $reason }
    Stan: { $status }
    Członek: { $user }
gg-approval-list = Zatwierdzeni członkowie:
    { $approvals }
gg-next-page = Więcej wpisów: { $command }
gg-range-invalid = Nieprawidłowy zakres. Wybierz co najmniej jedną wiadomość i nie przekraczaj wskazanego limitu.
    Maksimum: { $cap }
gg-range-start = Początek zapisany dla ciebie w tym temacie na dziesięć minut. Odpowiedz na ostatnią wiadomość przez /purgeto.
gg-range-missing = Nie masz tu zapisanego początku. Najpierw użyj /purgefrom jako odpowiedzi.
gg-content-needed = Podaj treść albo odpowiedz na nią; maksymalnie 3500 znaków.
gg-log-status = Ustawienia dziennika:
    Kategorie: { $categories }
    Cel: { $destination }
gg-log-unverified = Nie otrzymałem zweryfikowanego oryginału tego polecenia kanału. Najpierw wyślij /setlog w kanale.
gg-log-forward = Prześlij ten oryginalny /setlog do grupy. Łączący administrator musi mieć prawa zmiany informacji w obu czatach.
gg-info = Informacje o użytkowniku lub czacie:
    ID: { $id }
    Członkostwo: { $membership }
    Nazwa: { $name }
    Nazwa użytkownika: { $username }
gg-op-unpinall = odepnij wszystkie wiadomości
gg-op-permapin = przypnij na stałe
gg-op-promote = mianuj administratora
gg-op-demote = odwołaj administratora
gg-op-approve_user = zatwierdź użytkownika
gg-op-unapprove = usuń zatwierdzenie
gg-op-unapproveall = usuń wszystkie zatwierdzenia
gg-unknown = Nieznane
gg-chat-id = ID czatu:
    ID: { $id }
gg-on = Włączone
gg-off = Wyłączone
gg-anon-enabled = Zaufanie do anonimowych administratorów jest tu włączone. Anonimowe polecenia tej grupy używają praw bota bez wskazania osoby. Akcje właściciela nadal wymagają zweryfikowanego twórcy. /anonadmin off przywraca weryfikację przez człowieka.
gg-right-invite_users = zapraszanie użytkowników
gg-right-promote_members = mianowanie administratorów
gg-right-manage_topics = zarządzanie tematami
gg-right-creator = twórca grupy
gg-log-join = Członek dołączył.
    Członek: { $user }
gg-log-leave = Członek opuścił grupę.
    Członek: { $user }
gg-warning-row = Wpis ostrzeżenia:
    Wygaśnięcie: { $expiry }
    ID: { $id }
    Powód: { $reason }
gg-menu-prompt = Wybierz opcję.
gg-content-invalid = Treść nieprawidłowa lub przekracza limity Telegrama. Sprawdź nazwę, format, modyfikatory i przyciski.
gg-content-unavailable = Treść niedostępna lub aktualne członkostwo w grupie nie daje dostępu.
gg-btn-private-note = Otwórz notatkę
gg-open-private = Otwórz tę treść prywatnie:
gg-items-cleared = Wpisy usunięte.
    Liczba: { $count }
gg-clearall-confirm = Twórca grupy potwierdza przez <code>/{ $command } confirm</code>.
gg-button-usage = Użyj <code>/button "Etykieta" https://example.com</code>. Dodaj <code>"Notatka" #nazwa same</code> dla kolejnego przycisku w tym samym wierszu. Otrzymasz znaczniki i działający podgląd.
gg-btn-accept-rules = Akceptuję zasady
gg-btn-open-verification = Otwórz weryfikację
gg-captcha-private = Otwórz prywatną weryfikację, aby potwierdzić członkostwo w grupie.
    Członek: { $user }
gg-captcha-choice = Wybierz pasujący obraz przyciskami. Tryb i pozycja znaku są podane poniżej.
    Tryb: { $mode }
    Pozycja: { $position }
gg-captcha-settings = Ustawienia weryfikacji:
    Włączone: { $enabled }
    Usunięcie: { $kick }
    Tryb: { $mode }
    Zwolnienie: { $release }
    Sekundy: { $seconds }
gg-captcha-dependency = Włącz powitania przed weryfikacją. Zapisz zasady przed wymaganiem akceptacji.
gg-val-text = Obraz z tekstem
gg-val-text2 = Obraz ze znakami
gg-captcha-attempts-exhausted = Weryfikacja nieudana po zbyt wielu błędnych odpowiedziach; zastosowano zaplanowane ograniczenie.
gg-captcha-admin-exempt = Jesteś teraz administratorem grupy. Weryfikacja zakończona.
gg-captcha-question-text = Wybierz słowo widoczne na obrazie.
gg-captcha-question-math = Rozwiąż równanie na obrazie i wybierz odpowiedź.
gg-captcha-question-text2 = Wybierz wskazany znak na obrazie, od lewej do prawej.
    Pozycja: { $position }
gg-locktypes = Dostępne blokady treści:
    Typy: { $types }
gg-allowlist-title = Wyjątki od blokad treści
gg-allowlist-invalid = Nieprawidłowy wyjątek. Użyj domeny/ścieżki, dokładnego zaproszenia, @czatu lub zadeklarowanej tożsamości jak stickerpack:nazwa.
gg-reason-lock = Zablokowana treść:
    Typy: { $types }
gg-lock-applied = Reguła blokady zastosowana.
    Powód: { $reason }
    Typy: { $types }
gg-reaction-failed = Nie udało się zastosować reguły reakcji. Ten serwer Bot API może nie obsługiwać usuwania reakcji.
    Kod: { $code }
gg-reaction-anonymous = Anonimowe liczniki nie zawierają ID użytkownika lub czatu autora. API usuwania tego wymaga; nie deklaruje się usunięcia.
gg-none = Brak
gg-blocklist-title = Lista blokad
gg-blocklist-invalid = Nieprawidłowy wyzwalacz, powód lub akcja. Sprawdź cudzysłowy, sekwencje ucieczki symboli wieloznacznych i czas wymagany dla trybów tymczasowych.
gg-blocklist-settings = Ustawienia listy blokad:
    Usuwanie: { $delete }
    Tryb: { $mode }
gg-blocklist-action = Reguła listy blokad zastosowana do członka.
    Powód: { $reason }
    Członek: { $user }
gg-lock-album = Albumy
gg-lock-anonchannel = Nadawcy kanałowi
gg-lock-audio = Audio
gg-lock-bot = Boty
gg-lock-button = Przyciski w wiadomości
gg-lock-cashtag = Oznaczenia walut
gg-lock-checklist = Listy kontrolne
gg-lock-cjk = Tekst chiński/japoński/koreański
gg-lock-command = Polecenia
gg-lock-comment = Komentarze osób spoza grupy
gg-lock-contact = Kontakty
gg-lock-cyrillic = Tekst cyrylicą
gg-lock-document = Dokumenty
gg-lock-email = Adresy email
gg-lock-emoji = Emoji
gg-lock-emojicustom = Niestandardowe emoji
gg-lock-emojigame = Gry emoji
gg-lock-emojionly = Tekst tylko z emoji
gg-lock-externalreply = Odpowiedzi zewnętrzne
gg-lock-forward = Przesłane wiadomości
gg-lock-forwarduser = Przesłane od użytkowników
gg-lock-forwardbot = Przesłane od botów
gg-lock-forwardchannel = Przesłane z kanałów
gg-lock-forwardstory = Przesłane relacje
gg-lock-game = Gry
gg-lock-gif = Animacje GIF
gg-lock-guestbot = Boty gościnne
gg-lock-inline = Boty inline
gg-lock-invitelink = Zaproszenia Telegram
gg-lock-botlink = Linki do botów
gg-lock-location = Lokalizacje
gg-lock-outsidereaction = Reakcje osób spoza grupy
gg-lock-phone = Numery telefonów
gg-lock-photo = Zdjęcia
gg-lock-poll = Ankiety
gg-lock-reaction = Reakcje
gg-lock-rtl = Tekst od prawej do lewej
gg-lock-spoiler = Ukryte treści
gg-lock-sticker = Naklejki
gg-lock-stickeranimated = Animowane naklejki
gg-lock-stickerpremium = Naklejki premium
gg-lock-text = Tekst
gg-lock-url = URL
gg-lock-video = Filmy
gg-lock-videonote = Wiadomości wideo
gg-flood-status = Zalew wiadomości: limit kolejnych działa przy N; okno czasowe powyżej N. Akcja, czas i czyszczenie sekwencji poniżej.
    Wyczyść całą sekwencję: { $clear }
    Próg kolejnych wiadomości: { $consecutive }
    Liczba: { $count }
    Czas: { $duration }
    Tryb: { $mode }
    Sekundy: { $seconds }
gg-raid-status = Ochrona przed masowym dołączaniem. /antiraid on włącza; /antiraid off zatrzymuje. Okres, czas banów i automatyczny próg na minutę poniżej.
    Aktywne: { $active }
    Automatyczny próg: { $auto }
    Czas bana: { $ban }
    Okres: { $period }
    Do: { $until }
gg-raid-banned = 🛡 Członek tymczasowo zbanowany podczas aktywnej ochrony przed masowym dołączaniem.
    Członek: { $user }
gg-raid-declined = 🛡 Prośba odrzucona podczas aktywnej ochrony przed masowym dołączaniem.
    Członek: { $user }
gg-silent-consent-required = Twórca musi zezwolić na ciche akcje i skonfigurować dziennik przed wybraniem tej akcji.
gg-btn-enable-raid = Włącz ochronę przed masowym dołączaniem
gg-human-required = Ta akcja wymaga identyfikowalnego człowieka.
gg-group-message-required = Użyj polecenia przy prawdziwej wiadomości lub temacie grupy. ID prywatnych wiadomości nie oznaczają wiadomości grupy.
gg-connection-private = Użyj tego polecenia połączenia w naszym prywatnym czacie.
gg-connection-disconnected = Odłączono. Ostatnie pięć grup pozostaje dostępnych do ponownego połączenia.
gg-connection-current = Grupa połączona. Członkostwo i aktualne prawa są sprawdzane przy każdej akcji.
    Grupa: { $group }
gg-connection-none = Brak aktywnego połączenia. Użyj /connect GROUP_ID lub /connect @grupa.
gg-connection-open = Otwórz osobiste połączenie w naszym prywatnym czacie.
gg-btn-connect = Połącz prywatnie
gg-connection-history = Ostatnie pięć grup. Wybierz jedną; wymagane aktualne członkostwo.
gg-connection-unavailable = Połączenie niedostępne. Musisz być aktualnym członkiem będącym człowiekiem, a bot administratorem grupy.
gg-catalog-unresolved = /{ $command } występuje w katalogu bez zdefiniowanej akcji. Użyj /notes lub /flood dla zaimplementowanych funkcji.
gg-cleanup-failed = Czyszczenie wiadomości nieudane lub niedostępne; nie deklaruje się usunięcia.
gg-op-lock_change = zmień blokady treści
gg-op-allowlist_change = zmień wyjątki
gg-op-allowlist_clear = usuń wyjątki
gg-op-blocklist_change = zmień listę blokad
gg-op-blocklist_clear = wyczyść listę blokad
gg-op-raid_change = zmień ochronę masowych wejść
gg-disabled-list = Polityka poleceń: /disable NAZWA i /enable NAZWA sterują wykonaniem; /disabledel usuwaniem; /disableadmin obejmuje administratorów.
    Polecenia: { $commands }
gg-cleanup-types = Dostępne kategorie czyszczenia:
    Typy: { $types }
gg-cleanup-selected = Wybrane kategorie czyszczenia:
    Typy: { $types }
gg-advanced-status = Cicha automatyzacja wymaga zgody twórcy i dziennika. Boty potrzebują zwykłych praw; kontrola zmian domyślnie włączona. Ustaw widoczność między botami w BotFather.
    Ustawienie: { $setting }
    Wartość: { $value }
gg-action-topic = Temat akcji. /setactiontopic wybiera bieżący temat forum; ogólny temat ma ID 1.
    Temat: { $topic }
gg-topic-unavailable = Wymagane aktualne forum i odpowiednie prawa zarządzania.
gg-topic-id-required = W połączonym czacie prywatnym podaj ID tematu jawnie.
gg-topic-general-delete = Ogólnego tematu nie można usunąć. Potwierdzenie wymaga identyfikowalnego człowieka.
gg-topic-delete-confirm = Usunąć temat i wiadomości? Osobiste potwierdzenie ważne dwie minuty.
    Temat: { $topic }
gg-btn-confirm-delete = Potwierdź usunięcie
gg-topic-changed = Akcja tematu zakończona.
    Akcja: { $action }
    Temat: { $topic }
gg-op-policy_change = zmień politykę poleceń/czyszczenia
gg-op-topic_create = utwórz temat
gg-op-topic_rename = zmień nazwę tematu
gg-op-topic_close = zamknij temat
gg-op-topic_reopen = otwórz ponownie temat
gg-op-topic_delete = usuń temat i wiadomości
gg-op-echo = wyślij sformatowaną treść
gg-broadcast-owner = Tylko skonfigurowany operator bota lub rzeczywisty właściciel instancji potomnej może rozsyłać wiadomości do jej grup.
gg-broadcast-queued = Kampania grupowa w kolejce. Cele i wyniki oddzielone według bota.
    ID: { $id }
gg-broadcast-busy = Inna kampania trwa lub nie upłynęło pięć minut od poprzedniego utworzenia.
gg-broadcast-empty = Nie masz kampanii grupowej w tym bocie.
gg-broadcast-status = Stan kampanii grupowej:
    Anulowane: { $cancelled }
    Nieudane: { $failed }
    ID: { $id }
    W kolejce: { $queued }
    Dostarczone: { $sent }
    Stan: { $status }
    Wynik niepewny: { $uncertain }
gg-fed-created = Federacja utworzona. ID należy do oddzielnej sieci tego bota.
    ID: { $id }
    Nazwa: { $name }
gg-fed-info = Informacje o federacji:
    Administratorzy: { $admins }
    ID: { $id }
    Dziennik: { $log }
    Nazwa: { $name }
    Powiadomienia: { $notifications }
    Właściciel: { $owner }
    Powody wymagane: { $reasons }
gg-fed-list = Twoje federacje jako właściciel lub administrator:
    { $rows }
gg-fed-admins = Najpierw właściciel, potem administratorzy federacji:
    { $rows }
gg-fed-quiet = Ciche wyjaśnienia pasywne. Egzekwowanie nadal aktywne.
    Wartość: { $value }
gg-fed-policy = Zasady powodów i powiadomień właściciela:
    Powiadomienia: { $notifications }
    Powody wymagane: { $reasons }
gg-fed-confirm-delete = Trwale usunąć federację, dane i członkostwa? Istniejące bany Telegrama pozostaną. Osobiste potwierdzenie w ciągu pięciu minut.
    ID: { $id }
    Nazwa: { $name }
gg-fed-confirm-log = Ustawić wskazany dziennik federacji? Potwierdź w ciągu pięciu minut. Twoje prawa celu i prawa publikowania bota zostaną sprawdzone ponownie.
    Cel: { $destination }
    ID: { $id }
    Nazwa: { $name }
gg-fed-confirm-sent = Osobiste potwierdzenie wysłane właścicielowi federacji.
gg-fed-deleted = Federacja usunięta. Istniejące bany Telegrama pozostają.
gg-fed-log-set = Cel dziennika federacji ustawiony:
    Cel: { $destination }
gg-fed-cancel = Anuluj
gg-fed-cancelled = Anulowano.
gg-fed-saved-delivery-failed = Zmiana zapisana, ale powiadomienie lub dziennik nie dotarły. Sprawdź cel i dostęp bota.
gg-fed-error-authority = Wymagany aktualny właściciel federacji lub odpowiednia rola. Prawa grupy Telegram nie nadają praw federacji.
gg-fed-error-private = Użyj tego polecenia we własnym prywatnym czacie z tym botem.
gg-fed-error-group = Użyj polecenia w rzeczywistej grupie. Połączenie prywatne nie wybiera grupy federacji.
gg-fed-error-owned = Masz już federację w tym bocie. Użyj /fedinfo, /renamefed lub /delfed prywatnie.
gg-fed-error-name = Podaj niepustą nazwę bez znaków sterujących. Nazwy są ograniczane do 64 znaków.
gg-fed-error-id = Podaj poprawną UUID federacji tego bota. ID Rose nie łączą z naszą oddzielną usługą.
gg-fed-error-missing = Nie znaleziono federacji w tym bocie lub kontekście.
gg-fed-error-creator = Tylko aktualny twórca grupy Telegram może dołączyć grupę do federacji lub ją odłączyć.
gg-fed-error-target = Podaj dodatnie ID człowieka, odpowiedź do człowieka lub aktualnie zweryfikowaną nazwę. Właściciela nie można odwołać.
gg-fed-error-value = Nieprawidłowe argumenty federacji. Użyj on/off dla zasad i poprawnego ID tam, gdzie wymagane.
gg-fed-error-stale = Potwierdzenie wygasło, zostało użyte albo federacja, właściciel lub cel zmienili się. Poproś o nowe.
gg-fed-error-destination = Właściciel potrzebuje aktualnych praw administratora celu, bot dostępu do publikowania. Kanały wymagają post_messages.
gg-fed-error-delivery = Osobiste potwierdzenie nie dotarło lub nie zostało powiązane. Otwórz prywatny czat z botem i spróbuj ponownie.
gg-fed-event = Zdarzenie federacji:
    Zdarzenie: { $event }
    ID: { $id }
    Nazwa: { $name }
    Członek: { $user }
gg-fed-event-rename = nazwa zmieniona
gg-fed-event-delete = usunięta; bany Telegrama pozostają
gg-fed-event-promote = administrator dodany
gg-fed-event-demote = administrator usunięty
gg-fed-event-self-remove = administrator zrezygnował
gg-fed-event-reason = zasada powodów banów zmieniona
gg-fed-event-notif = powiadomienia właściciela zmienione
gg-fed-event-log = cel dziennika zmieniony
gg-fed-event-unlog = cel dziennika usunięty
gg-fed-event-ban = zasada bana zapisana; egzekwowanie w kolejce
gg-fed-event-unban = zasada bana usunięta; zdjęcie własnych ograniczeń w kolejce
gg-fed-event-subscribe = subskrypcja dodana; sprawdzanie zaobserwowanych użytkowników w kolejce
gg-fed-event-unsubscribe = subskrypcja usunięta; inne źródła pozostają
gg-fed-ban-details = Cel i powód bana:
    Powód: { $reason }
    Członek: { $user }
gg-fed-passive = Zasada federacji banuje członka. Źródło i powód poniżej.
    ID: { $id }
    Powód: { $reason }
    Źródło: { $source }
    Członek: { $user }
gg-fed-enforce-failed = Zasada federacji banuje członka, ale usunięcie nie powiodło się. Sprawdź prawa bota. Źródło i powód poniżej.
    ID: { $id }
    Powód: { $reason }
    Źródło: { $source }
    Członek: { $user }
gg-fed-stat = Bany federacji tego członka:
    { $rows }
    Członek: { $user }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — aktywny: { $status }; zmiana: { $date }.
gg-fed-stat-more = Dostępne kolejne źródła. Użyj polecenia kontynuacji lub konkretnego ID federacji dla powodu i daty.
gg-fed-intent-saved = Zasada zapisana; zaobserwowane cele w kolejce. Aktualne prawa i inne źródła ograniczeń zostaną sprawdzone przed skutkami.
    Członek: { $user }
    Wersja: { $version }
gg-fed-subscriptions = Bezpośrednie subskrypcje banów federacji:
    { $rows }
gg-fed-imported = Wpisy sprawdzone i zapisane; identyczne duplikaty pominięte. Egzekwowanie wobec zaobserwowanych celów w kolejce.
    Liczba: { $count }
    Identyczne duplikaty: { $duplicates }
gg-fed-event-import = zweryfikowane bany zaimportowane; egzekwowanie w kolejce
gg-fed-error-file-format = Odpowiedz na CSV UTF-8 z id/reason, JSONL/NDJSON z user_id lub eksport tablicy JSON tego bota. Nieprawidłowy wiersz blokuje wszystkie zapisy.
gg-fed-error-file-limit = Maksymalnie 2 MiB i 1000 wpisów. Brakujące lub zbyt duże pliki odrzucane; listy nigdy nie są po cichu ucinane.
gg-fed-error-file-duplicate = Sprzeczne wpisy dla tego samego ID użytkownika. Nie zaimportowano banów.
gg-fed-error-file-rate = Import i eksport dzielą odstęp 30 minut na federację. Spróbuj później.
gg-fed-error-reason = Powody banów: najwyżej 1024 znaki bez nieobsługiwanych znaków sterujących.
gg-fed-error-reason_required = Ta federacja wymaga niepustego powodu każdego bana.
gg-fed-error-cycle = Federacja nie może subskrybować siebie ani tworzyć skierowanego cyklu.
gg-fed-error-graph_limit = Limit osiągnięty: 32 bezpośrednie cele, 128 osiągalnych federacji, głębokość 16 lub 10 000 połączeń tego bota.
gg-data-confirm = Potwierdź w ciągu pięciu minut. Aktualny twórca i rewizja grupy zostaną sprawdzeni ponownie. Zmieniają się tylko wybrane moduły; tożsamość, zaufanie i aktywne bany pozostają.
    SHA-256: { $digest }
    Grupa: { $group }
    Moduły: { $modules }
    Operacja: { $operation }
gg-data-import = Importuj moduły grupy
gg-data-reset = Przywróć moduły grupy
gg-data-privacy-delete = Usuń opcjonalne dane osobiste tego bota
gg-data-confirm-button = Potwierdź tę zmianę
gg-data-personal = Otwórz potwierdzenie w prywatnym czacie.
gg-data-saved = Wybrane moduły zapisane.
gg-data-error-authority = Import i reset wymagają aktualnego identyfikowalnego twórcy grupy. Eksport wymaga aktualnego administratora.
gg-data-error-format = Odpowiedz na poprawny wersjonowany JSON Group Guard utworzony przez /export.
gg-data-error-limit = Plik przekracza limit rozmiaru lub skonfigurowanej treści.
gg-data-error-version = Schemat lub wersja nieobsługiwane; brak zmian.
gg-data-error-module = Wybierz znane moduły: /export all lub /export notes rules. Import i reset używają tych samych nazw.
gg-data-error-field = Nieprawidłowe lub brakujące pola modułów. Nie zastosowano ustawień.
gg-data-error-item = Treść, opcje lub dostęp do powtarzania nieprawidłowe. Nie zapisano treści.
gg-data-error-media = Media muszą być przesłane temu botowi i dostępne przez getFile. ID plików innych botów nie są obsługiwane.
gg-data-error-destination = Cele dziennika i tematów wymagają aktualnych praw i możliwości bota. ID tematów obowiązują tylko w tej samej grupie.
gg-data-error-language = Wybierz zainstalowany język przez /setlang.
gg-data-error-stale = Potwierdzenie wygasło, zmieniono je lub użyto. Zacznij ponownie.
gg-data-error-restore = Nie udało się bezpiecznie przywrócić własnych tymczasowych ograniczeń. Dowody pozostają; sprawdź prawa bota.
gg-data-error-rate = Operacje danych grupy mają lokalny odstęp pięciu minut. Spróbuj później.
gg-data-error-delivery = Prywatne potwierdzenie nie dotarło. Rozpocznij prywatny czat z botem i spróbuj ponownie.
gg-data-error-saved_delivery = Ustawienia zapisane, ale sugestie poleceń nie zostały odświeżone. Sprawdź prawa bota.
gg-privacy-policy = <b>Twoje dane w tym Group Guard</b>
    /privacy data eksportuje połączenia, zaobserwowane profile, ostrzeżenia, zatwierdzenia, status ograniczeń i weryfikacji, własność, role i bany federacji oraz zadania bezpieczeństwa. Nie zawiera cudzych prywatnych treści, odpowiedzi weryfikacji, uwierzytelniania i surowych plików. Użyj polecenia kontynuacji.
    /privacy delete usuwa opcjonalną historię połączeń, zaobserwowane imię i nazwę użytkownika, nieaktywne weryfikacje i treść zakończonych własnych kampanii tego bota. Aktywne ostrzeżenia i ograniczenia, wersje banów, role, własność, subskrypcje, ochrona przed powtórzeniem i niepewne operacje API zachowują minimalne identyfikatory bezpieczeństwa i kolejności. Dla tych relacji użyj jawnych poleceń rezygnacji lub usuwania federacji. Wspólny profil platformy i inne boty pozostają.
    Operatorzy osobno zarządzają kopiami zapasowymi i audytem. Polecenie nie usuwa zewnętrznych wiadomości Telegrama ani kopii zapasowych i nie obiecuje automatycznego okresu przechowywania.
gg-privacy-usage = /privacy policy · /privacy data [kontynuacja] · /privacy delete — tylko we własnym prywatnym czacie z tym botem.
gg-privacy-private = Wymagany prywatny czat osoby wnioskującej. Nieprawidłowe kursory nie dają dostępu do cudzych danych.
gg-privacy-next = Następna strona danych: /privacy data { $cursor }
gg-privacy-deleted = Opcjonalne dane osobiste tego bota usunięte. Aktywne bezpieczeństwo, własność i niepewne zadania zachowują minimalne identyfikatory; patrz /privacy policy.
gg-language-usage = Wybierz język grupy przez /setlang. /lang prywatnie zmienia osobisty język platformy. Dostępne kody poniżej.
    Kody języka: { $codes }
gg-language-saved = Język odpowiedzi grupy zmieniony.
gg-help-index = <b>Przewodnik poleceń Group Guard</b>
    /help dział · /help polecenie · /help dział 2. Wskazane polecenia działają też przez sprawdzone /connect; prywatne odpowiedzi pozostają w prawdziwym prywatnym czacie.
    Ustawienia wymagają zmiany informacji; sankcje ograniczania członków; usuwanie praw usuwania; przypinanie praw przypinania; mianowanie praw promowania; tematy praw zarządzania tematami. Prawa bota sprawdzane osobno. Akcje właściciela wymagają aktualnego twórcy będącego człowiekiem. /settings otwiera osobisty panel grupy.
gg-help-search = <b>Pasujące polecenia</b>
    Wyszukiwanie: { $query }
gg-help-connected = Grupa lub sprawdzone połączenie; prawa w dziale
gg-help-group-only = Wymagana rzeczywista wiadomość grupy
gg-help-unsupported = Nazwa katalogu zachowana; niezdefiniowane działanie zwraca wyjaśnienie
gg-help-next = Następna strona
gg-help-previous = Poprzednia strona
gg-help-family-title-moderation = Moderacja i zatwierdzenia
gg-help-family-title-messages = Usuwanie i przypinanie wiadomości
gg-help-family-title-logging = Autoryzowane dzienniki
gg-help-family-title-settings = Ustawienia i język grupy
gg-help-family-title-content = Notatki, filtry, zasady i powitania
gg-help-family-title-captcha = Weryfikacja nowych członków
gg-help-family-title-locks = Blokady treści i wyjątki
gg-help-family-title-blocklists = Dopasowania i akcje listy blokad
gg-help-family-title-antispam = Ochrona przed zalewem i masowym dołączaniem
gg-help-family-title-connections = Prywatne połączenia z grupami
gg-help-family-title-identity = Informacje o użytkownikach i czatach
gg-help-family-title-policy = Polityka poleceń i botów
gg-help-family-title-cleanup = Czyszczenie poleceń, botów i usług
gg-help-family-title-topics = Tematy forum
gg-help-family-title-utilities = Wysyłanie treści i kampanie operatora
gg-help-family-title-federations = Role, bany i subskrypcje federacji
gg-help-family-title-portability = Pliki grupy i dane osobiste
gg-help-family-title-discovery = Pomoc i edytor treści
gg-help-family-moderation = <b>Moderacja</b> · Odpowiedź, liczbowe ID lub sprawdzony @użytkownik. /ban 20 powód; /tban 20 60s powód; /mute 20; /tmute 20 2h powód. Czas: 60 sekund–365 dni. /kickme usuwa tylko ciebie. Warianty d usuwają wiadomość odpowiedzi; s polecenie/odpowiedź i wymagają usuwania. Administratorzy chronieni. /setwarnlimit 3; /setwarnmode ban; /setwarntime 1d. Nowe grupy: trzy ostrzeżenia; stare ustawienia zachowane. /approve pomija tylko zwykłą ochronę treści/zalewu, nigdy federację/CAS/masowe dołączanie/ręczne akcje. /promote nie przekracza wspólnych praw wnioskującego i bota. Masowe wyzerowanie wymaga twórcy.
gg-help-family-messages = <b>Wiadomości</b> · /del wymaga prawdziwej odpowiedzi w grupie. /purge zaczyna tam; /purgefrom i /purgeto zapisują granice. Obowiązują skonfigurowane limity i reguły Telegrama; potwierdzenie partii nie dowodzi dokładnej liczby usunięć. /pin [loud], /permapin, /unpin, /unpinall wymagają przypinania; usunięcie wszystkich przypięć wymaga twórcy. /antichannelpin i /cleanlinked sterują automatycznymi wiadomościami powiązanego kanału.
gg-help-family-logging = <b>Dzienniki</b> · /setlog -100… wymaga aktualnego zarządzania celem i publikowania bota. Przekazana konfiguracja musi odpowiadać faktycznie odebranemu oryginałowi. /logcategories: settings/admin/user/automated/reports/other; /log i /nolog wybierają kategorie. Błędy dostarczenia pozostają widoczne i nie dowodzą sukcesu akcji.
gg-help-family-settings = <b>Ustawienia</b> · /settings otwiera osobisty wygasający panel z aktualnym sprawdzeniem prawa zmiany informacji. /setlang kod zapisuje język grupy; /lang prywatnie osobisty język. /night 23 7 +3 zamyka nocą; /night off przywraca wyłącznie własny nadal zgodny stan uprawnień. Zewnętrzne zmiany mają pierwszeństwo.
gg-help-family-content = <b>Edytor</b> · /save słowo tekst lub odpowiedź na media; /get słowo, #słowo, /notes odczytują notatki. Nowe nazwy jedno słowo; dawne szersze nazwy zachowane. /filter "fraza" tekst, /filterprefix, /filterexact wybierają dopasowanie; /stop usuwa klucz. /clearall i /stopall wymagają potwierdzenia twórcy. Format Rose: pogrubienie/kursywa/podkreślenie/przekreślenie/kod, linki, cytaty i losowe alternatywy %%%. Pola: { "{" }first{ "}" }, { "{" }last{ "}" }, { "{" }fullname{ "}" }, { "{" }username{ "}" }, { "{" }mention{ "}" }, { "{" }id{ "}" }, { "{" }chatname{ "}" }, { "{" }count{ "}" }. /button tworzy przyciski URL/notatki/zasad. Ogólne opcje preview/nonotif/protect/mediaspoiler; notatki admin/private/noprivate/repeat; filtry user/allow_bot/replytag/command. /save słowo Witaj { "{" }repeat 5m{ "}" } planuje tylko publiczne treści z aktualnymi prawami autora. Zasady, powitania i prywatne treści używają tego samego renderera. ID mediów należą do bota.
gg-help-family-captcha = <b>Weryfikacja</b> · /captcha on/off; /captchamode off/button/math/text/text2; /setcaptchatext; /captcharules on; /captchakick on/off; /captchakicktime i /captchamutetime ustawiają ograniczone terminy. Wydane wyzwania zachowują generację/termin. Prośby wymagają invite-users; wyciszanie restrict-members. Odpowiedzi osobiste, jednorazowe. Bany federacji przed zatwierdzeniem/CAPTCHA.
gg-help-family-locks = <b>Blokady</b> · /lock links [akcja], /unlock typ; /locktypes pokazuje rzeczywiste typy, /locks stan. /lockwarns steruje ostrzeżeniami. /allowlist: domena/ścieżka, dokładne zaproszenie, @czat lub stickerpack:/forward:/inline:/channel:/chat:/bot:/command:. Nieprawidłowe wzorce odrzucane. Wyjątki tylko dla pasującej treści; cicha automatyzacja wymaga twórcy i autoryzowanego dziennika.
gg-help-family-blocklists = <b>Lista blokad</b> · /addblocklist "fraza" obsługuje tekst/prefiks/dokładne dopasowanie i zadeklarowane tożsamości z opcjonalnym powodem/akcją. /rmblocklist usuwa dokładnie wybrane klucze. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute ustawia akcję; tryby tymczasowe wymagają czasu. /blocklistdelete osobno steruje usuwaniem. Wzorce wieloznaczne ograniczone; błędne wpisy i przekroczenia odrzucane.
gg-help-family-antispam = <b>Zalew i masowe dołączanie</b> · /setflood liczba dla kolejnych wiadomości; /setfloodtimer liczba czas dla okna; /setfloodmode sankcja/czas; /clearflood czyści sekwencję. Stare ustawienia zachowane. /flood i /antiflood pokazują politykę; alias jest lokalną decyzją zgodności. /antiraid on/off/duration, /raidtime, /raidactiontime, /autoantiraid zapisują termin i oddzielną sankcję nowych wejść. Pierwszeństwo przed zatwierdzeniem/CAPTCHA; wygaśnięcie generacyjne odporne na restart.
gg-help-family-connections = <b>Połączenia</b> · /connect groupID lub osobisty link. Sprawdzane członkostwo twoje i bota; zmiany nadal wymagają dokładnych aktualnych praw. /connection pokazuje wybór, /disconnect usuwa go, /connect pokazuje historię z kontynuacją. Połączenie nie daje własności federacji ani praw operatora.
gg-help-family-identity = <b>Informacje</b> · /id pokazuje rzeczywiste ID użytkownika/czatu/źródła; /info aktualny cel. Odpowiedzi i @nazwy wymagają aktualnych dowodów tego bota. Anonimowa wiadomość grupy nie wskazuje osoby; nie tworzy się fikcyjnego ID człowieka.
gg-help-family-policy = <b>Polityka</b> · /disable polecenie, /enable polecenie, /disabled, /disableable używają nazw kanonicznych i aliasów. /disableadmin steruje wyjątkami administratorów; /disabledel usuwaniem. Polecenia przywracania pozostają dostępne. /bot2bot off/admin/all sprawdza prawdziwe członkostwo; zmiany domyślnie zatwierdza człowiek. /bot2botskipreview tylko twórca. /silentactions wymaga zgody i autoryzowanego dziennika. Niezdefiniowane runs/saved zwracają wyjaśnienie.
gg-help-family-cleanup = <b>Czyszczenie</b> · /cleancommand admin/user/other i /keepcommand wybierają polecenia. /cleanmsg action/filter/note i /keepmsg tylko wiadomości rzeczywiście wysłane przez bota; pokwitowania i zadania po pięciu minutach zapobiegają zgadywaniu ID. /cleanservice i /nocleanservice: join/leave/other/photo/pin/title/videochat. Przetwarzanie funkcjonalne i prawidłowe płatności przed czyszczeniem.
gg-help-family-topics = <b>Tematy</b> · /newtopic nazwa, /renametopic nazwa, /closetopic, /reopentopic działają w aktualnym prawdziwym temacie. /deletetopic wymaga potwierdzenia twórcy; /setactiontopic wybiera cel tej samej grupy. Wymagane forum Telegram i manage-topics. Brakujące/nieobsługiwane tematy zwracają prawdziwe błędy.
gg-help-family-utilities = <b>Narzędzia</b> · /echo i /say wysyłają bezpośrednią lub cytowaną treść przez wspólny ograniczony renderer. /broadcast tylko skonfigurowany operator lub rzeczywisty właściciel instancji potomnej; wyłącznie skonfigurowane grupy tego bota. Wyniki celów zachowują częściowe/niepewne dostarczenie; status i anulowanie nie powtarzają udanych załączników.
gg-help-family-federations = <b>Federacje</b> · /newfed nazwa tworzy UUID tego bota. Polecenia prywatne używają własnej federacji niezależnie od połączeń; odczyt UUID nie nadaje roli. /fedpromote i /feddemote zarządzają administratorami, /feddemoteme rezygnuje. /joinfed UUID i /leavefed wymagają aktualnego twórcy grupy. Usunięcie nie zdejmuje banów Telegrama. /fban userID powód i /unfban userID wymagają właściciela/administratora federacji; /fedreason, /fednotif, /setfedlog właściciela. /quietfed ukrywa tylko wyjaśnienia pasywne. /subfed UUID jest skierowane, ograniczone i bez cykli. /fedstat [userID], /fbanstat UUID pokazują źródła/stan. /fbanlist csv/minicsv/json tylko właściciel ze wspólnym odstępem 30 minut; /importfbans odpowiada na ograniczone CSV lub prawdziwy JSON wierszami i jawnie obsługuje własną tablicę JSON. Sprawdzani tylko zaobserwowani użytkownicy; bez twierdzenia o pełnej liście członków.
gg-help-family-portability = <b>Pliki i prywatność</b> · /export all lub moduły wymaga administratora; /import i /reset aktualnego twórcy będącego człowiekiem z osobistym jednorazowym potwierdzeniem pięciu minut. Lokalny odstęp pięciu minut; własny wersjonowany JSON, najwyżej 2MiB i skonfigurowane limity. Moduły: moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Pominięte moduły zachowane. Zaufanie, wydane wyzwania/zadania, subskrypcje, role i aktywne bany nigdy nie są importowane. /privacy policy/data/delete tylko własny prywatny czat z paginacją i minimalnym przechowywaniem bezpieczeństwa. Brak zweryfikowanego adaptera pełnego eksportu Rose.
gg-help-family-discovery = <b>Pomoc</b> · /help pokazuje działy; /help polecenie wyszukuje nazwy/aliasy; /help dział 2 kontynuuje. /button pomaga ze znacznikami. Każdy przewodnik opisuje kontekst, prawa, ustawienia domyślne i limity. /settings otwiera osobisty panel grupy.
gg-data-error-cache_pending = Opcjonalne dane SQL usunięte. Czyszczenie niedostępnej pamięci podręcznej w kolejce; aktywne dane bezpieczeństwa pozostają.
