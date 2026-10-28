## Independently authored Group Guard az content.
group-welcome = 🛡 Məni əlavə etdiyiniz üçün təşəkkürlər! Mesaj silmək, üzvləri məhdudlaşdırmaq və mesaj bərkitmək üçün administrator hüquqları verin. /settings ilə qurun.
gg-start = 🛡 Salam <b>{ $name }</b>! Mən <b>Group Guard</b>: yeni üzvlərin yoxlanması, mesaj seli və CAS qorunması, məzmun kilidləri, moderasiya, qeydlər, filtrlər, qaydalar və salamlamalar. Məni administrator əlavə edib /settings və ya /help istifadə edin.
gg-help = 📖 /help bölmələri göstərir; /help əmr əmrləri axtarır. Moderasiya: /ban /mute /kick /warn. Məzmun: /save /filter /rules. Qorunma: /lock /blocklist /night. /settings şəxsi qrup panelini açır.
gg-welcome-default = 👋 { "{" }mention{ "}" }, <b>{ "{" }group{ "}" }</b> qrupuna xoş gəlmisiniz!
gg-credit = 🛡 @{ $bot } tərəfindən qorunur
gg-btn-add = ➕ Qrupa əlavə et
gg-btn-commands = 📖 Əmrlər
gg-btn-rules = 📜 Qaydalar
gg-btn-human = ✅ Mən insanam
gg-btn-unwarn = ↩️ Xəbərdarlığı sil (administratorlar)
gg-btn-locks = 🔒 Məzmun kilidləri · Say: { $count }
gg-btn-open-settings = ⚙️ Ayarları aç
gg-btn-admin-tab = 🛡 Qruplar
gg-captcha = 🤖 Göstərilən müddətdə insan olduğunuzu təsdiqləyin, əks halda çıxarılacaqsınız.
    Dəqiqə: { $minutes }
    Üzv: { $user }
gg-captcha-button = Aşağıdakı düyməni basın 👇
gg-captcha-math = <b>{ $a } + { $b }</b> neçədir?
gg-captcha-not-you = Bu düymə başqa şəxs üçündür.
gg-captcha-ok = ✅ Xoş gəlmisiniz!
gg-captcha-wrong = ❌ Yanlış cavab. Cəhd qalıbsa yenidən sınayın.
    Qalan cəhdlər: { $left }
gg-captcha-failed = ❌ Çox sayda yanlış cavab.
gg-captcha-passed = ✅ Yoxlama uğurlu. Xoş gəlmisiniz!
    Üzv: { $user }
gg-cas-banned = 🚫 CAS üzvü spam göndərən kimi tanıyır; üzv bloklanıb.
    Üzv: { $user }
gg-join-request = 👋 Qrupa qoşulmaq üçün insan olduğunuzu təsdiqləyin:
    Qrup: { $group }
gg-join-approved = ✅ Sorğu təsdiqləndi. Xoş gəlmisiniz!
gg-join-expired = ⌛ Sorğunun vaxtı bitib. Yeni qoşulma sorğusu göndərin.
gg-goodbye = 👋 Üzv qrupdan ayrıldı.
    Üzv: { $user }
gg-flood-mute = 🌊 Üzv çox mesaj göndərdiyi üçün müvəqqəti susduruldu.
    Üzv: { $user }
gg-flood-kick = 🌊 Üzv çox mesaj göndərdiyi üçün çıxarıldı.
    Üzv: { $user }
gg-flood-ban = 🌊 Üzv çox mesaj göndərdiyi üçün bloklandı.
    Üzv: { $user }
gg-newbie-links = 🆕 Yeni üzvlər göstərilən ilk saatlarda keçid göndərə bilməz.
    Saat: { $hours }
    Üzv: { $user }
gg-spam-banned = 🧠 Üzv spama görə bloklandı.
    Üzv: { $user }
gg-reason-blocklist = qadağan olunmuş söz
gg-need-right = ⛔ Müvafiq administrator hüququ lazımdır.
    Hüquq: { $right }
gg-right-admin = administrator
gg-right-restrict = üzvləri məhdudlaşdırmaq
gg-right-delete = mesajları silmək
gg-right-pin = mesajları bərkitmək
gg-right-change_info = qrup məlumatını dəyişmək
gg-admins-only = ⛔ Yalnız administratorlar.
gg-need-target = 👤 Mesaja cavab verin və ya ID və yaxud hazırda yoxlanmış @istifadəçi adı göstərin.
gg-target-admin = 🙅 Bu əməliyyat administratora tətbiq edilə bilməz.
gg-bot-no-rights = ⚠️ Lazımi hüquqları olan administrator olmalıyam.
gg-banned = 🔨 Üzv bloklandı.
    Səbəb: { $reason }
    Üzv: { $user }
gg-banned-for = 🔨 Üzv göstərilən müddətə bloklandı.
    Səbəb: { $reason }
    Vaxt: { $time }
    Üzv: { $user }
gg-unbanned = ✅ Üzvün bloku götürüldü.
    Üzv: { $user }
gg-kicked = 👢 Üzv çıxarıldı; yenidən qoşula bilər.
    Səbəb: { $reason }
    Üzv: { $user }
gg-muted = 🔇 Üzv susduruldu.
    Səbəb: { $reason }
    Üzv: { $user }
gg-muted-for = 🔇 Üzv göstərilən müddətə susduruldu.
    Səbəb: { $reason }
    Vaxt: { $time }
    Üzv: { $user }
gg-unmuted = 🔊 Üzv yenidən yaza bilər.
    Üzv: { $user }
gg-warned = ⚠️ Üzvün xəbərdarlığı qeydə alındı.
    Say: { $count }
    Hədd: { $limit }
    Səbəb: { $reason }
    Üzv: { $user }
gg-warn-limit-ban = 🔨 Xəbərdarlıq həddinə çatıldı; üzv bloklandı.
    Hədd: { $limit }
    Üzv: { $user }
gg-warn-limit-mute = 🔇 Xəbərdarlıq həddinə çatıldı; üzv susduruldu.
    Hədd: { $limit }
    Üzv: { $user }
gg-warn-limit-kick = 👢 Xəbərdarlıq həddinə çatıldı; üzv çıxarıldı.
    Hədd: { $limit }
    Üzv: { $user }
gg-unwarned = ↩️ Üzvün bir xəbərdarlığı silindi.
    Say: { $count }
    Hədd: { $limit }
    Üzv: { $user }
gg-warn-removed = ↩️ Administrator xəbərdarlığı sildi.
    Administrator: { $admin }
gg-warns = ⚠️ Üzvün xəbərdarlıqları:
    Say: { $count }
    Hədd: { $limit }
    Üzv: { $user }
gg-warns-reset = 🧽 Üzvün xəbərdarlıqları sıfırlandı.
    Üzv: { $user }
gg-purge-reply = 🧹 Silinəcək ilk mesaja cavab verin.
gg-purged = 🧹 Mesajlar silindi.
    Say: { $count }
gg-pin-reply = 📌 Bərkidiləcək mesaja cavab verin.
gg-report-reply = 🚨 Şikayət ediləcək mesaja cavab verin.
gg-reported = 🚨 Üzv administratorlara bildirildi.
    Üzv: { $user }
gg-setlog-usage = 📒 Məni jurnal kanalında administrator edib kanal ID-si ilə <code>/setlog -100…</code> işlədin.
gg-setlog-failed = ⚠️ Orada yaza bilmirəm. Əvvəl administrator əlavə edin.
gg-setlog-done = 📒 Jurnal kanalı bağlandı.
gg-setlog-off = 📒 Jurnal kanalı ayrıldı.
gg-log-connected = 📒 Bu söhbət qrupun moderasiya jurnalını alır.
    Qrup: { $group }
gg-log-flood = 🌊 Mesaj seli aşkarlandı:
    Əməliyyat: { $action }
    Üzv: { $user }
gg-log-report = 🚨 Üzv haqqında şikayət:
    Üzv: { $user }
gg-log-spam = 🧠 AI tərəfindən aşkar edilmiş spam bloku:
    Mətn: { $text }
    Üzv: { $user }
gg-rules = 📜 <b>Qaydalar</b>
    { $rules }
gg-no-rules = 📜 Qaydalar saxlanmayıb. Administratorlar /setrules mətn işlədə bilər.
gg-rules-saved = 📜 Qaydalar saxlandı.
gg-rules-cleared = 📜 Qaydalar silindi.
gg-welcome-usage = 👋 <code>/setwelcome Salam {"{"}mention{"}"}, {"{"}group{"}"} qrupuna xoş gəldiniz!</code> işlədin və ya mesaja cavab verin.
gg-welcome-saved = 👋 Salamlama saxlandı.
gg-welcome-reset = 👋 Standart salamlama bərpa edildi.
gg-note-usage = 📝 <code>/save ad mətn</code> və ya mesaja <code>/save ad</code> ilə cavab verin.
gg-filter-usage = 🔁 <code>/filter söz cavab</code> və ya <code>/filter söz</code> ilə cavab verin.
gg-note-saved = 📝 Qeyd saxlandı. İcazələrə uyğun <code>#{ $key }</code> ilə alın.
gg-filter-saved = 🔁 “{ $key }” uyğun gələndə cavab verəcəyəm.
gg-notes-empty = 📝 Hələ qeyd yoxdur.
gg-filters-empty = 🔁 Hələ filtr yoxdur.
gg-notes-list = 📝 <b>Qeydlər</b>
gg-filters-list = 🔁 <b>Filtrlər</b>
gg-item-deleted = 🗑 Yazı silindi.
    Açar: { $key }
gg-item-missing = 🤷 Bu adla məzmun yoxdur.
gg-items-limit = 📦 Qrupun qeyd və filtr həddi dolub.
gg-lock-usage = 🔒 <code>/lock links</code> işlədin. Mövcud növlər aşağıdadır; <code>all</code> hamısını seçir.
    Növlər: { $types }
gg-locked = 🔒 Qadağan məzmun:
    Növlər: { $types }
gg-unlocked = 🔓 İcazəli məzmun:
    Növlər: { $types }
gg-locks-title = 🔒 <b>Məzmun kilidləri</b>
gg-locks-panel = 🔒 <b>Kilidlər</b>: qadağan məzmun silinir; administratorlar istisnadır.
gg-lock-links = Keçidlər
gg-lock-invites = Dəvət keçidləri
gg-lock-forwards = Yönləndirmələr
gg-lock-media = Media
gg-lock-stickers = Stikerlər
gg-lock-gifs = GIF
gg-lock-voice = Səs mesajları
gg-lock-polls = Sorğular
gg-lock-bots = Botlar
gg-blocklist = 🚫 <b>Qadağan sözlər</b>
    Sözlər: { $words }
gg-blocklist-empty = 🚫 Qadağan söz yoxdur.
gg-blocklist-usage = 🚫 <code>/addblock söz, başqa ifadə</code> · <code>/rmblock söz</code>
gg-blocklist-saved = 🚫 Qadağa siyahısı yeniləndi.
    Say: { $count }
gg-night-usage = 🌙 <code>/night 23 7 +3</code> UTC+3 üzrə 23:00–07:00 bağlayır; <code>/night off</code> söndürür.
gg-night-on = 🌙 Qrupun gecə vaxtı quruldu.
    Son: { $end }
    Başlanğıc: { $start }
    Saat qurşağı: { $tz }
gg-night-off = 🌙 Gecə rejimi söndürüldü.
gg-night-start = 🌙 Gecəniz xeyrə! Qrup göstərilən vaxta qədər bağlıdır.
    Son: { $end }
gg-night-end = ☀️ Sabahınız xeyir! Qrup yenidən açıqdır.
gg-panel = ⚙️ <b>Qrup ayarları</b>
    Dəyişmək üçün seçimə basın. Gecə vaxtını /night ilə qurun.
    Qrup: { $group }
    Gecə vaxtı: { $night }
gg-panel-sent = 📬 Ayarlar şəxsi söhbətə göndərildi.
gg-panel-start-first = 📬 Əvvəl mənimlə şəxsi söhbət başladın, sonra aşağıya basın.
gg-credit-vip = 💎 Qorunma sətrini gizlətmək VIP tələb edir. Şəxsi söhbətdə /vip işlədin.
gg-opt-wel = 👋 Qarşılama · Dəyər: { $value }
gg-opt-cln = 🧹 Qoşulma mesajlarını sil · Dəyər: { $value }
gg-opt-bye = 👋 Sağollaşma · Dəyər: { $value }
gg-opt-cap = 🤖 Yoxlama · Dəyər: { $value }
gg-opt-cpm = ⏱ Yoxlama müddəti, dəqiqə · Dəyər: { $value }
gg-opt-fld = 🌊 Mesaj həddi · Dəyər: { $value }
gg-opt-fla = 🌊 Mesaj seli əməliyyatı · Dəyər: { $value }
gg-opt-wrn = ⚠️ Xəbərdarlıq həddi · Dəyər: { $value }
gg-opt-wra = ⚠️ Xəbərdarlıq əməliyyatı · Dəyər: { $value }
gg-opt-act = ⏳ Avtomatik məhdudiyyət, dəqiqə · Dəyər: { $value }
gg-opt-cas = 🛡 CAS qorunması · Dəyər: { $value }
gg-opt-nwb = 🆕 Yeni üzvlər keçidsiz, saat · Dəyər: { $value }
gg-opt-ais = 🧠 AI spam qorunması · Dəyər: { $value }
gg-opt-ngt = 🌙 Gecə rejimi · Dəyər: { $value }
gg-opt-crd = 🏷 Qorunma sətri · Dəyər: { $value }
gg-opt-lang = 🌐 Dil · Dəyər: { $value }
gg-val-button = Düymə
gg-val-math = Hesab
gg-val-off = sönülü
gg-val-mute = susdur
gg-val-kick = çıxar
gg-val-ban = blokla
gg-adm = 🛡 <b>Group Guard: statistika</b>
    Qruplar: { $groups }
    Yazılar: { $items }
    Xəbərdarlıqlar: { $warns }
cmd-settings = Qrup ayarları
cmd-help = Əmr bələdçisi
gg-auth-denied = İcazə yoxlana bilmədi. Heç nə dəyişmədi.
gg-target-invalid = Tanınan insan üzv seçin. Hədəf yoxlanmadı.
gg-duration-invalid = 60s–365d müddət istifadə edin. Müvəqqəti əmrlərə müddət lazımdır.
gg-reason-invalid = Səbəb ən çox 256 simvol ola bilər.
gg-outcome-failed = Əməliyyat uğursuz və ya icazəsizdir.
gg-outcome-partial = Əməliyyat qismən tamamlandı. Çıxarmadan sonra bərpa uğursuz olarsa blok qala bilər.
gg-outcome-ancillary = Əsas əməliyyat tamamlandı, əlavə addım uğursuz oldu.
gg-review-request = Aşağıdakı dəyişməz əməliyyatı yoxlayın. Hazırda səlahiyyətli insan 120 saniyədə təsdiqləyə bilər. Müddət saniyə ilə göstərilir.
    Təfərrüatlar: { $details }
    Müddət: { $duration }
    Əməliyyat: { $operation }
    Hədəf: { $target }
gg-review-approve = Bu əməliyyatı təsdiqlə
gg-review-unavailable = Təsdiq anbarı əlçatan deyil. Yeni əmr göndərin.
gg-review-expired = Təsdiqin vaxtı bitib, etibarsızdır və ya işlədilib.
gg-review-consumed = Təsdiq işlədildi. Nəticəni yoxlayın; təkrar üçün yeni əmr lazımdır.
gg-duration-permanent = Daimi / vaxt həddi yoxdur
gg-purge-ack = API silmə sorğularını təsdiqlədi. Həqiqətən silinən say məlum deyil.
    API təsdiqi: { $acknowledged }
    Tələb olunub: { $requested }
gg-warning-removed = Xəbərdarlıq silindi.
gg-op-ban = blokla
gg-op-mute = susdur
gg-op-kick = çıxar
gg-op-unban = bloku götür
gg-op-unmute = susdurmanı götür
gg-op-warn = xəbərdarlıq et
gg-op-unwarn = xəbərdarlığı sil
gg-op-resetwarns = xəbərdarlıqları sıfırla
gg-op-purge = mesaj aralığını sil
gg-op-delete = mesajı sil
gg-op-pin = mesajı bərkit
gg-op-unpin = bərkitməni götür
gg-op-setlog = jurnal hədəfini qur
gg-op-unsetlog = jurnal hədəfini sil
gg-op-config = ayarları dəyiş
gg-op-save = məzmunu saxla
gg-op-remove = məzmunu sil
gg-op-panel = paneli aç
gg-review-details-above = Tam tələb olunan məzmun birbaşa yuxarıdakı mesajdadır.
gg-warn-pending = Xəbərdarlıq saxlandı; hədd əməliyyatı artıq işlənir.
gg-done = Tamamlandı.
gg-setting-saved = Ayar saxlandı.
    Ayar: { $setting }
gg-setting-value = Hazırkı ayar dəyəri:
    Ayar: { $setting }
    Dəyər: { $value }
gg-setting-invalid = Etibarsız ayar. on/off, uyğun rejim və ya 10m kimi müddət istifadə edin.
gg-warning-settings = Xəbərdarlıq ayarları:
    Müddət: { $duration }
    Vaxtın bitməsi: { $expiry }
    Hədd: { $limit }
    Rejim: { $mode }
gg-admin-changed = Administrator əməliyyatı tamamlandı.
    Əməliyyat: { $action }
    Üzv: { $user }
gg-admin-list = Açıq administratorlar:
    { $admins }
gg-approved = Üzv təsdiqləndi.
    Səbəb: { $reason }
    Üzv: { $user }
gg-unapproved = Təsdiqlər silindi.
    Say: { $count }
gg-approval-status = Üzvün təsdiq vəziyyəti:
    Səbəb: { $reason }
    Vəziyyət: { $status }
    Üzv: { $user }
gg-approval-list = Təsdiqlənmiş üzvlər:
    { $approvals }
gg-next-page = Daha çox yazı: { $command }
gg-range-invalid = Etibarsız aralıq. Ən az bir mesaj seçin və göstərilən həddi aşmayın.
    Maksimum: { $cap }
gg-range-start = Başlanğıc bu mövzuda sizin üçün on dəqiqə saxlandı. Son mesaja /purgeto ilə cavab verin.
gg-range-missing = Burada sizin üçün başlanğıc saxlanmayıb. Əvvəl cavabda /purgefrom işlədin.
gg-content-needed = Məzmun verin və ya ona cavab verin; ən çox 3500 simvol.
gg-log-status = Jurnal ayarları:
    Kateqoriyalar: { $categories }
    Hədəf: { $destination }
gg-log-unverified = Bu kanal əmrinin yoxlanmış əslini almamışam. Əvvəl kanalda /setlog göndərin.
gg-log-forward = Bu əsl /setlog əmrini qrupa yönləndirin. Bağlayan administrator hər iki söhbətdə məlumat dəyişmək hüququna sahib olmalıdır.
gg-info = İstifadəçi və ya söhbət məlumatı:
    ID: { $id }
    Üzvlük: { $membership }
    Ad: { $name }
    İstifadəçi adı: { $username }
gg-op-unpinall = bütün bərkitmələri götür
gg-op-permapin = daimi bərkit
gg-op-promote = administrator təyin et
gg-op-demote = administratoru çıxar
gg-op-approve_user = istifadəçini təsdiqlə
gg-op-unapprove = təsdiqi sil
gg-op-unapproveall = bütün təsdiqləri sil
gg-unknown = Naməlum
gg-chat-id = Söhbət ID-si:
    ID: { $id }
gg-on = Aktiv
gg-off = Sönülü
gg-anon-enabled = Anonim administratorlara etibar burada aktivdir. Bu qrupun anonim əmrləri insanı müəyyənləşdirmədən bot hüquqlarını istifadə edir. Sahib əməliyyatları yenə yoxlanmış yaradıcı tələb edir. /anonadmin off insan yoxlamasını bərpa edir.
gg-right-invite_users = istifadəçiləri dəvət etmək
gg-right-promote_members = administrator təyin etmək
gg-right-manage_topics = mövzuları idarə etmək
gg-right-creator = qrup yaradıcısı
gg-log-join = Üzv qoşuldu.
    Üzv: { $user }
gg-log-leave = Üzv ayrıldı.
    Üzv: { $user }
gg-warning-row = Xəbərdarlıq qeydi:
    Vaxtın bitməsi: { $expiry }
    ID: { $id }
    Səbəb: { $reason }
gg-menu-prompt = Seçim edin.
gg-content-invalid = Məzmun etibarsızdır və ya Telegram həddini aşır. Ad, format, dəyişdiricilər və düymələri yoxlayın.
gg-content-unavailable = Məzmun əlçatan deyil və ya hazırkı qrup üzvlüyünüz girişə icazə vermir.
gg-btn-private-note = Qeydi aç
gg-open-private = Bu məzmunu şəxsi söhbətdə aç:
gg-items-cleared = Yazılar silindi.
    Say: { $count }
gg-clearall-confirm = Qrup yaradıcısı <code>/{ $command } confirm</code> ilə təsdiqləyir.
gg-button-usage = <code>/button "Etiket" https://example.com</code> işlədin. Eyni sətirdə əlavə düymə üçün <code>"Qeyd" #ad same</code> əlavə edin. İşlək önbaxış və işarələmə alacaqsınız.
gg-btn-accept-rules = Qaydaları qəbul et
gg-btn-open-verification = Yoxlamanı aç
gg-captcha-private = Qrup üzvlüyünüzü təsdiqləmək üçün şəxsi yoxlamanı açın.
    Üzv: { $user }
gg-captcha-choice = Düymələrlə uyğun şəkli seçin. Rejim və simvol mövqeyi aşağıdadır.
    Rejim: { $mode }
    Mövqe: { $position }
gg-captcha-settings = Yoxlama ayarları:
    Aktivdir: { $enabled }
    Çıxarma: { $kick }
    Rejim: { $mode }
    Azad etmə: { $release }
    Saniyə: { $seconds }
gg-captcha-dependency = Yoxlamadan əvvəl salamlamaları aktiv edin. Qəbul tələbindən əvvəl qaydaları saxlayın.
gg-val-text = Mətn şəkli
gg-val-text2 = Simvol şəkli
gg-captcha-attempts-exhausted = Çox yanlış cavabdan sonra yoxlama uğursuz oldu; nəzərdə tutulan məhdudiyyət tətbiq edildi.
gg-captcha-admin-exempt = İndi qrup administratorusunuz. Yoxlama bitdi.
gg-captcha-question-text = Şəkildəki sözü seçin.
gg-captcha-question-math = Şəkildəki tənliyi həll edib cavabı seçin.
gg-captcha-question-text2 = Şəkildə soldan sağa göstərilən simvolu seçin.
    Mövqe: { $position }
gg-locktypes = Mövcud məzmun kilidləri:
    Növlər: { $types }
gg-allowlist-title = Məzmun kilidi istisnaları
gg-allowlist-invalid = Etibarsız istisna. Domen/yol, dəqiq dəvət, @söhbət və ya stickerpack:ad kimi açıq kimlik istifadə edin.
gg-reason-lock = Qadağan məzmun:
    Növlər: { $types }
gg-lock-applied = Kilid qaydası tətbiq edildi.
    Səbəb: { $reason }
    Növlər: { $types }
gg-reaction-failed = Reaksiya qaydası tətbiq olunmadı. Bu Bot API serveri reaksiyaların silinməsini dəstəkləməyə bilər.
    Kod: { $code }
gg-reaction-anonymous = Anonim saylar istifadəçi və ya göndərən söhbət ID-si vermir. Silmə API-si bunu tələb edir; silmə iddia edilmir.
gg-none = Yoxdur
gg-blocklist-title = Qadağa siyahısı
gg-blocklist-invalid = Tətikləyici, səbəb və ya əməliyyat etibarsızdır. Dırnaqları, şablon simvollarının qaçışını və müvəqqəti rejimin müddətini yoxlayın.
gg-blocklist-settings = Qadağa siyahısı ayarları:
    Silmə: { $delete }
    Rejim: { $mode }
gg-blocklist-action = Qadağa siyahısı qaydası üzvə tətbiq edildi.
    Səbəb: { $reason }
    Üzv: { $user }
gg-lock-album = Albomlar
gg-lock-anonchannel = Kanal göndərənləri
gg-lock-audio = Audio
gg-lock-bot = Botlar
gg-lock-button = Daxili düymələr
gg-lock-cashtag = Valyuta nişanları
gg-lock-checklist = Yoxlama siyahıları
gg-lock-cjk = Çin/Yapon/Koreya mətni
gg-lock-command = Əmrlər
gg-lock-comment = Üzv olmayan şərhləri
gg-lock-contact = Kontaktlar
gg-lock-cyrillic = Kiril mətni
gg-lock-document = Sənədlər
gg-lock-email = E-poçt ünvanları
gg-lock-emoji = Emoji
gg-lock-emojicustom = Xüsusi emoji
gg-lock-emojigame = Emoji oyunları
gg-lock-emojionly = Yalnız emoji mətni
gg-lock-externalreply = Xarici cavablar
gg-lock-forward = Yönləndirmələr
gg-lock-forwarduser = İstifadəçi yönləndirmələri
gg-lock-forwardbot = Bot yönləndirmələri
gg-lock-forwardchannel = Kanal yönləndirmələri
gg-lock-forwardstory = Yönləndirilmiş hekayələr
gg-lock-game = Oyunlar
gg-lock-gif = GIF animasiyaları
gg-lock-guestbot = Qonaq botlar
gg-lock-inline = Daxili botlar
gg-lock-invitelink = Telegram dəvətləri
gg-lock-botlink = Bot keçidləri
gg-lock-location = Məkanlar
gg-lock-outsidereaction = Üzv olmayan reaksiyaları
gg-lock-phone = Telefon nömrələri
gg-lock-photo = Şəkillər
gg-lock-poll = Sorğular
gg-lock-reaction = Reaksiyalar
gg-lock-rtl = Sağdan sola mətn
gg-lock-spoiler = Gizli məzmun
gg-lock-sticker = Stikerlər
gg-lock-stickeranimated = Animasiyalı stikerlər
gg-lock-stickerpremium = Premium stikerlər
gg-lock-text = Mətn
gg-lock-url = URL
gg-lock-video = Videolar
gg-lock-videonote = Video mesajlar
gg-flood-status = Mesaj seli: ardıcıl hədd N-də, vaxt pəncərəsi N-dən çox olduqda işləyir. Əməliyyat, müddət və sıra təmizliyi aşağıdadır.
    Tam sıra təmizliyi: { $clear }
    Ardıcıl hədd: { $consecutive }
    Say: { $count }
    Müddət: { $duration }
    Rejim: { $mode }
    Saniyə: { $seconds }
gg-raid-status = Kütləvi qoşulma qorunması. /antiraid on aktiv edir; /antiraid off dayandırır. Dövr, blok müddəti və dəqiqəlik avtomatik hədd aşağıdadır.
    Aktiv: { $active }
    Avtomatik hədd: { $auto }
    Blok müddəti: { $ban }
    Dövr: { $period }
    Qədər: { $until }
gg-raid-banned = 🛡 Aktiv kütləvi qoşulma qorunması zamanı üzv müvəqqəti bloklandı.
    Üzv: { $user }
gg-raid-declined = 🛡 Aktiv kütləvi qoşulma qorunması zamanı sorğu rədd edildi.
    Üzv: { $user }
gg-silent-consent-required = Bu əməliyyatı seçməzdən əvvəl yaradıcı səssiz əməliyyatlara icazə verib jurnal qurmalıdır.
gg-btn-enable-raid = Kütləvi qoşulma qorunmasını aktiv et
gg-human-required = Bu əməliyyat müəyyənləşdirilən insan tələb edir.
gg-group-message-required = Əmri real qrup mesajı və ya mövzusunda istifadə edin. Şəxsi mesaj ID-si qrup mesajını göstərmir.
gg-connection-private = Bu bağlanma əmrini şəxsi söhbətimizdə işlədin.
gg-connection-disconnected = Ayrıldı. Son beş qrup yenidən bağlanmaq üçün qalır.
gg-connection-current = Qrup bağlandı. Hər əməliyyatda üzvlük və hazırkı hüquqlar yoxlanır.
    Qrup: { $group }
gg-connection-none = Aktiv bağlantı yoxdur. /connect GROUP_ID və ya /connect @qrup işlədin.
gg-connection-open = Şəxsi bağlantınızı şəxsi söhbətimizdə açın.
gg-btn-connect = Şəxsi bağlan
gg-connection-history = Son beş qrupunuz. Birini seçin; hazırkı üzvlük lazımdır.
gg-connection-unavailable = Bağlantı əlçatan deyil. Hazırkı insan üzv və bot həmin qrupda administrator olmalıdır.
gg-catalog-unresolved = /{ $command } kataloqda müəyyən əməliyyatsızdır. Hazır funksiyalar üçün /notes və ya /flood işlədin.
gg-cleanup-failed = Mesaj təmizliyi uğursuz və ya əlçatan deyil; silmə iddia edilmir.
gg-op-lock_change = məzmun kilidlərini dəyiş
gg-op-allowlist_change = istisnaları dəyiş
gg-op-allowlist_clear = istisnaları sil
gg-op-blocklist_change = qadağa siyahısını dəyiş
gg-op-blocklist_clear = qadağa siyahısını təmizlə
gg-op-raid_change = kütləvi qoşulma qorunmasını dəyiş
gg-disabled-list = Əmr siyasəti: /disable AD və /enable AD icranı; /disabledel silməni; /disableadmin administratorları əhatə etməni idarə edir.
    Əmrlər: { $commands }
gg-cleanup-types = Mövcud təmizlik kateqoriyaları:
    Növlər: { $types }
gg-cleanup-selected = Seçilmiş təmizlik kateqoriyaları:
    Növlər: { $types }
gg-advanced-status = Səssiz avtomatika yaradıcı razılığı və jurnal tələb edir. Botlara normal hüquqlar lazımdır; dəyişiklik yoxlaması standartda aktivdir. BotFather-də botlararası görünüşü qurun.
    Ayar: { $setting }
    Dəyər: { $value }
gg-action-topic = Əməliyyat mövzusu. /setactiontopic hazırkı forum mövzusunu seçir; ümumi mövzu ID-si 1-dir.
    Mövzu: { $topic }
gg-topic-unavailable = Hazırkı forum və uyğun idarəetmə hüquqları lazımdır.
gg-topic-id-required = Bağlı şəxsi söhbətdə mövzu ID-sini açıq göstərin.
gg-topic-general-delete = Ümumi mövzu silinmir. Təsdiq müəyyənləşdirilən insan tələb edir.
gg-topic-delete-confirm = Mövzu və mesajları silək? Şəxsi təsdiq iki dəqiqə qüvvədədir.
    Mövzu: { $topic }
gg-btn-confirm-delete = Silməni təsdiqlə
gg-topic-changed = Mövzu əməliyyatı tamamlandı.
    Əməliyyat: { $action }
    Mövzu: { $topic }
gg-op-policy_change = əmr/təmizlik siyasətini dəyiş
gg-op-topic_create = mövzu yarat
gg-op-topic_rename = mövzu adını dəyiş
gg-op-topic_close = mövzunu bağla
gg-op-topic_reopen = mövzunu yenidən aç
gg-op-topic_delete = mövzu və mesajları sil
gg-op-echo = formatlı məzmun göndər
gg-broadcast-owner = Yalnız bu botun təyin olunmuş operatoru və ya uşaq instansının real sahibi onun qruplarına yaza bilər.
gg-broadcast-queued = Qrup yayımı növbəyə qoyuldu. Hədəflər və nəticələr bot üzrə ayrıdır.
    ID: { $id }
gg-broadcast-busy = Başqa yayım aktivdir və ya əvvəlki yaradılmadan beş dəqiqə keçməyib.
gg-broadcast-empty = Bu botda qrup yayımınız yoxdur.
gg-broadcast-status = Qrup yayımının vəziyyəti:
    Ləğv edilib: { $cancelled }
    Uğursuz: { $failed }
    ID: { $id }
    Növbədə: { $queued }
    Çatdırılıb: { $sent }
    Vəziyyət: { $status }
    Qeyri-müəyyən nəticə: { $uncertain }
gg-fed-created = Federasiya yaradıldı. ID bu botun ayrı şəbəkəsinə aiddir.
    ID: { $id }
    Ad: { $name }
gg-fed-info = Federasiya məlumatı:
    Administratorlar: { $admins }
    ID: { $id }
    Jurnal: { $log }
    Ad: { $name }
    Bildirişlər: { $notifications }
    Sahib: { $owner }
    Səbəblər tələb olunur: { $reasons }
gg-fed-list = Sahib və ya administrator olduğunuz federasiyalar:
    { $rows }
gg-fed-admins = Əvvəl sahib, sonra federasiya administratorları:
    { $rows }
gg-fed-quiet = Səssiz passiv izahlar. Blokların icrası aktiv qalır.
    Dəyər: { $value }
gg-fed-policy = Səbəb və sahib bildirişi siyasəti:
    Bildirişlər: { $notifications }
    Səbəblər tələb olunur: { $reasons }
gg-fed-confirm-delete = Federasiya, məlumat və üzvlüklər daimi silinsin? Mövcud Telegram blokları qalır. Beş dəqiqədə şəxsi təsdiq verin.
    ID: { $id }
    Ad: { $name }
gg-fed-confirm-log = Göstərilən federasiya jurnalı qurulsun? Beş dəqiqədə təsdiqləyin. Hədəf hüquqlarınız və botun yayımlama hüququ yenidən yoxlanacaq.
    Hədəf: { $destination }
    ID: { $id }
    Ad: { $name }
gg-fed-confirm-sent = Şəxsi təsdiq federasiya sahibinə göndərildi.
gg-fed-deleted = Federasiya silindi. Mövcud Telegram blokları qalır.
gg-fed-log-set = Federasiya jurnalının hədəfi quruldu:
    Hədəf: { $destination }
gg-fed-cancel = Ləğv et
gg-fed-cancelled = Ləğv edildi.
gg-fed-saved-delivery-failed = Dəyişiklik saxlandı, bildiriş və ya jurnal çatdırılmadı. Hədəf və bot girişini yoxlayın.
gg-fed-error-authority = Hazırkı federasiya sahibi və ya uyğun rol lazımdır. Telegram qrup hüquqları federasiya hüququ vermir.
gg-fed-error-private = Əmri bu botla öz şəxsi söhbətinizdə işlədin.
gg-fed-error-group = Əmri real qrupda işlədin. Şəxsi bağlantı federasiya qrupunu seçmir.
gg-fed-error-owned = Bu botda artıq federasiyanız var. Şəxsi /fedinfo, /renamefed və ya /delfed işlədin.
gg-fed-error-name = Nəzarət simvolu olmayan, boş olmayan ad verin. Adlar 64 simvola qədər kəsilir.
gg-fed-error-id = Bu botun etibarlı federasiya UUID-sini verin. Rose ID-ləri ayrıca xidmətimizə bağlanmır.
gg-fed-error-missing = Bu bot və ya kontekstdə federasiya tapılmadı.
gg-fed-error-creator = Yalnız hazırkı Telegram qrup yaradıcısı qrupu federasiyaya qoşa və ayıra bilər.
gg-fed-error-target = Müsbət insan ID-si, insana cavab və ya hazırda yoxlanmış ad verin. Sahib vəzifədən çıxarıla bilməz.
gg-fed-error-value = Etibarsız federasiya arqumentləri. Siyasət üçün on/off və tələb olunan yerdə etibarlı ID işlədin.
gg-fed-error-stale = Təsdiqin vaxtı bitib, işlədilib və ya federasiya, sahib, hədəf dəyişib. Yeni təsdiq istəyin.
gg-fed-error-destination = Sahib hədəfdə hazırkı administrator, bot yayımlama imkanlı olmalıdır. Kanallar post_messages tələb edir.
gg-fed-error-delivery = Şəxsi təsdiq çatdırılmadı və ya bağlanmadı. Botla şəxsi söhbət açıb yenidən sınayın.
gg-fed-event = Federasiya hadisəsi:
    Hadisə: { $event }
    ID: { $id }
    Ad: { $name }
    Üzv: { $user }
gg-fed-event-rename = ad dəyişdi
gg-fed-event-delete = silindi; Telegram blokları qalır
gg-fed-event-promote = administrator əlavə edildi
gg-fed-event-demote = administrator çıxarıldı
gg-fed-event-self-remove = administrator istefa verdi
gg-fed-event-reason = səbəb siyasəti dəyişdi
gg-fed-event-notif = sahib bildirişləri dəyişdi
gg-fed-event-log = jurnal hədəfi dəyişdi
gg-fed-event-unlog = jurnal hədəfi silindi
gg-fed-event-ban = blok siyasəti saxlandı; icra növbədədir
gg-fed-event-unban = blok siyasəti silindi; öz məhdudiyyətlərini götürmə növbədədir
gg-fed-event-subscribe = abunə əlavə edildi; müşahidə edilmiş istifadəçi yoxlaması növbədədir
gg-fed-event-unsubscribe = abunə silindi; digər mənbələr qalır
gg-fed-ban-details = Blok hədəfi və səbəbi:
    Səbəb: { $reason }
    Üzv: { $user }
gg-fed-passive = Federasiya siyasəti üzvü bloklayır. Mənbə və səbəb aşağıdadır.
    ID: { $id }
    Səbəb: { $reason }
    Mənbə: { $source }
    Üzv: { $user }
gg-fed-enforce-failed = Federasiya siyasəti üzvü bloklayır, çıxarma uğursuz oldu. Bot hüquqlarını yoxlayın. Mənbə və səbəb aşağıdadır.
    ID: { $id }
    Səbəb: { $reason }
    Mənbə: { $source }
    Üzv: { $user }
gg-fed-stat = Bu üzvün federasiya blokları:
    { $rows }
    Üzv: { $user }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — aktiv: { $status }; dəyişmə: { $date }.
gg-fed-stat-more = Başqa mənbələr var. Səbəb və tarix üçün davam əmrini və ya konkret federasiya ID-sini işlədin.
gg-fed-intent-saved = Siyasət saxlandı; müşahidə edilmiş hədəflər növbədədir. Təsirdən əvvəl hazırkı hüquqlar və digər məhdudiyyət mənbələri yoxlanır.
    Üzv: { $user }
    Versiya: { $version }
gg-fed-subscriptions = Federasiya bloklarının birbaşa abunələri:
    { $rows }
gg-fed-imported = Yazılar yoxlanıb saxlandı; eyni dublikatlar buraxıldı. Müşahidə edilmiş hədəflərin icrası növbədədir.
    Say: { $count }
    Eyni dublikatlar: { $duplicates }
gg-fed-event-import = yoxlanmış bloklar idxal edildi; icra növbədədir
gg-fed-error-file-format = id/reason ilə UTF-8 CSV, user_id ilə JSONL/NDJSON və ya bu botun JSON massiv ixracına cavab verin. Bir etibarsız sətir bütün yazmanı dayandırır.
gg-fed-error-file-limit = Ən çox 2 MiB və 1000 yazı. Yox və ya böyük fayllar rədd edilir; siyahılar səssiz kəsilmir.
gg-fed-error-file-duplicate = Eyni istifadəçi ID-si üçün ziddiyyətli yazılar. Blok idxal edilmədi.
gg-fed-error-file-rate = İdxal və ixrac hər federasiyada ortaq 30 dəqiqəlik aralıq istifadə edir. Sonra sınayın.
gg-fed-error-reason = Blok səbəbi ən çox 1024 simvol, dəstəklənməyən nəzarət simvolları olmadan ola bilər.
gg-fed-error-reason_required = Bu federasiya hər blok üçün boş olmayan səbəb tələb edir.
gg-fed-error-cycle = Federasiya özünə abunə ola və yönlü dövrə yarada bilməz.
gg-fed-error-graph_limit = Hədd dolub: 32 birbaşa hədəf, 128 çatıla bilən federasiya, dərinlik 16 və ya bu botda 10 000 əlaqə.
gg-data-confirm = Beş dəqiqədə təsdiqləyin. Hazırkı yaradıcı və qrup versiyası yenidən yoxlanır. Yalnız seçilən modullar dəyişir; kimlik, etibar və aktiv bloklar qalır.
    SHA-256: { $digest }
    Qrup: { $group }
    Modullar: { $modules }
    Əməliyyat: { $operation }
gg-data-import = Qrup modullarını idxal et
gg-data-reset = Qrup modullarını sıfırla
gg-data-privacy-delete = Bu botun könüllü şəxsi məlumatını sil
gg-data-confirm-button = Bu dəyişikliyi təsdiqlə
gg-data-personal = Təsdiqi şəxsi söhbətinizdə açın.
gg-data-saved = Seçilmiş modullar saxlandı.
gg-data-error-authority = İdxal və sıfırlama hazırkı müəyyənləşdirilən qrup yaradıcısını tələb edir. İxrac hazırkı administrator tələb edir.
gg-data-error-format = /export ilə yaradılmış versiyalı, etibarlı Group Guard JSON-na cavab verin.
gg-data-error-limit = Fayl ölçü və ya qurulmuş məzmun həddini aşır.
gg-data-error-version = Sxem və ya versiya dəstəklənmir; dəyişiklik tətbiq edilmədi.
gg-data-error-module = Tanınan modul seçin: /export all və ya /export notes rules. İdxal və sıfırlama eyni adları istifadə edir.
gg-data-error-field = Modul sahələri etibarsız və ya çatışmır. Ayarlar tətbiq edilmədi.
gg-data-error-item = Məzmun, seçimlər və ya təkrar giriş etibarsızdır. Məzmun saxlanmadı.
gg-data-error-media = Media bu bota yüklənib getFile ilə alınmalıdır. Başqa botların fayl ID-ləri dəstəklənmir.
gg-data-error-destination = Jurnal və mövzu hədəfləri hazırkı hüquq və bot imkanlarını tələb edir. Mövzu ID-si yalnız eyni qrupda işləyir.
gg-data-error-language = /setlang ilə quraşdırılmış dil seçin.
gg-data-error-stale = Təsdiqin vaxtı bitib, dəyişib və ya işlədilib. Yenidən başlayın.
gg-data-error-restore = Öz müvəqqəti məhdudiyyətləri təhlükəsiz bərpa olunmadı. Sübut qalır; bot hüquqlarını yoxlayın.
gg-data-error-rate = Qrup məlumat əməliyyatları yerli beş dəqiqə aralıqlıdır. Sonra sınayın.
gg-data-error-delivery = Şəxsi təsdiq çatdırılmadı. Botla şəxsi söhbət başladıb yenidən sınayın.
gg-data-error-saved_delivery = Ayarlar saxlandı, əmr təklifləri yenilənmədi. Bot hüquqlarını yoxlayın.
gg-privacy-policy = <b>Bu Group Guard-dakı məlumatınız</b>
    /privacy data bağlantılarınızı, müşahidə edilmiş profilləri, xəbərdarlıqları, təsdiqləri, məhdudiyyət/yoxlama vəziyyətini, federasiya sahibliyi/rolları/bloklarını və təhlükəsizlik işlərini ixrac edir. Başqasının şəxsi məzmunu, yoxlama cavabları, autentifikasiya və xam fayllar daxil deyil. Davam əmrini izləyin.
    /privacy delete könüllü bağlantı tarixçəsini, müşahidə edilmiş adı/istifadəçi adını, qeyri-aktiv yoxlamaları və bu botda bitmiş şəxsi yayım məzmununu silir. Aktiv xəbərdarlıq/məhdudiyyət, blok versiyaları, rollar, sahiblik, abunələr, təkrar qorunması və qeyri-müəyyən API işi təhlükəsizlik və ardıcıllıq üçün minimal kimlikləri saxlayır. Bu əlaqələr üçün açıq federasiyadan çıxma/silmə əmrlərini istifadə edin. Ortaq platforma profili və digər botlar qalır.
    Operatorlar ehtiyat nüsxə və auditi ayrıca idarə edir. Əmr xarici Telegram mesajlarını və ehtiyat nüsxələri silmir, avtomatik saxlama müddəti vəd etmir.
gg-privacy-usage = /privacy policy · /privacy data [davam] · /privacy delete — yalnız bu botla öz şəxsi söhbətinizdə.
gg-privacy-private = Əməliyyat tələb edən insanın şəxsi söhbəti lazımdır. Etibarsız kursor başqasının məlumatına giriş vermir.
gg-privacy-next = Növbəti məlumat səhifəsi: /privacy data { $cursor }
gg-privacy-deleted = Bu botun könüllü şəxsi məlumatı silindi. Aktiv təhlükəsizlik, sahiblik və qeyri-müəyyən işlər minimal kimlik saxlayır; /privacy policy baxın.
gg-language-usage = Qrup dilini /setlang ilə seçin. Şəxsi /lang platforma dilinizi dəyişir. Mövcud kodlar aşağıdadır.
    Dil kodları: { $codes }
gg-language-saved = Qrup cavablarının dili dəyişdi.
gg-help-index = <b>Group Guard əmr bələdçisi</b>
    /help bölmə · /help əmr · /help bölmə 2. Göstərilən əmrlər yoxlanmış /connect ilə də işləyir; şəxsi cavablar real şəxsi söhbətdə qalır.
    Ayarlar məlumat dəyişmə; cəzalar üzv məhdudlaşdırma; silmə silmə hüququ; bərkitmə bərkitmə hüququ; təyinat administrator təyin etmə; mövzular mövzu idarəsi tələb edir. Bot hüquqları ayrıca yoxlanır. Sahib əməliyyatları hazırkı insan yaradıcını tələb edir. /settings şəxsi qrup panelini açır.
gg-help-search = <b>Uyğun əmrlər</b>
    Axtarış: { $query }
gg-help-connected = Qrup və ya yoxlanmış bağlantı; hüquqlar bölmədədir
gg-help-group-only = Real qrup mesajı lazımdır
gg-help-unsupported = Kataloq adı saxlanıb; müəyyənləşməmiş davranış izah qaytarır
gg-help-next = Növbəti səhifə
gg-help-previous = Əvvəlki səhifə
gg-help-family-title-moderation = Moderasiya və təsdiqlər
gg-help-family-title-messages = Mesaj silmə və bərkitmə
gg-help-family-title-logging = Səlahiyyətli jurnallar
gg-help-family-title-settings = Qrup ayarları və dil
gg-help-family-title-content = Qeydlər, filtrlər, qaydalar və salamlamalar
gg-help-family-title-captcha = Yeni üzv yoxlaması
gg-help-family-title-locks = Məzmun kilidləri və istisnalar
gg-help-family-title-blocklists = Qadağa uyğunluğu və əməliyyatlar
gg-help-family-title-antispam = Mesaj seli və kütləvi qoşulma qorunması
gg-help-family-title-connections = Şəxsi qrup bağlantıları
gg-help-family-title-identity = İstifadəçi və söhbət məlumatı
gg-help-family-title-policy = Əmr və bot siyasəti
gg-help-family-title-cleanup = Əmr, bot və xidmət təmizliyi
gg-help-family-title-topics = Forum mövzuları
gg-help-family-title-utilities = Məzmun göndərmə və operator yayımı
gg-help-family-title-federations = Federasiya rolları, blokları və abunələri
gg-help-family-title-portability = Qrup faylları və şəxsi məlumat
gg-help-family-title-discovery = Yardım və məzmun redaktoru
gg-help-family-moderation = <b>Moderasiya</b> · Cavab, rəqəm ID-si və ya yoxlanmış @istifadəçi. /ban 20 səbəb; /tban 20 60s səbəb; /mute 20; /tmute 20 2h səbəb. Müvəqqəti müddət 60 saniyə–365 gün. /kickme yalnız sizi çıxarır. d variantı cavab mesajını, s variantı əmr/cavabı silir və silmə hüququ tələb edir. Administratorlar qorunur. /setwarnlimit 3; /setwarnmode ban; /setwarntime 1d. Yeni qrup üç xəbərdarlıqla başlayır, köhnə ayarlar qalır. /approve yalnız adi məzmun/sel qorunmasını keçir, federasiya/CAS/kütləvi giriş/manual əməliyyatı keçmir. /promote tələb edən və botun ortaq hüquqlarını aşmır. Toplu sıfırlama yaradıcı tələb edir.
gg-help-family-messages = <b>Mesajlar</b> · /del real qrup cavabı tələb edir. /purge həmin mesajdan başlayır; /purgefrom və /purgeto sərhədləri saxlayır. Qurulmuş hədlər və Telegram qaydaları tətbiq edilir; toplu təsdiq dəqiq silmə sayı deyil. /pin [loud], /permapin, /unpin, /unpinall bərkitmə hüququ tələb edir; hamısını götürmək yaradıcıya aiddir. /antichannelpin və /cleanlinked bağlı kanalın avtomatik mesajlarını idarə edir.
gg-help-family-logging = <b>Jurnallar</b> · /setlog -100… hədəfin hazırkı idarəçisi və botun yayımlama hüququ tələb edir. Yönləndirilmiş qurulum real alınmış əsllə uyğun olmalıdır. /logcategories: settings/admin/user/automated/reports/other; /log və /nolog kateqoriyanı seçir. Çatdırılma xətaları görünür və əməliyyatın uğurunu sübut etmir.
gg-help-family-settings = <b>Ayarlar</b> · /settings şəxsi, vaxtı bitən panel açır və hazırkı məlumat dəyişmə hüququnu yoxlayır. /setlang kod qrup dilini; şəxsi /lang öz dilinizi saxlayır. /night 23 7 +3 gecə bağlayır; /night off yalnız öz hələ uyğun hüquq vəziyyətini bərpa edir. Xarici dəyişikliklər üstünlük daşıyır.
gg-help-family-content = <b>Redaktor</b> · /save söz mətn və ya mediaya cavab; /get söz, #söz, /notes qeydləri oxuyur. Yeni qeyd adı tək sözdür; köhnə geniş adlar qalır. /filter "ifadə" mətn, /filterprefix, /filterexact uyğunluğu seçir; /stop açarı silir. /clearall və /stopall yaradıcı təsdiqi tələb edir. Rose formatı: qalın/kursiv/alt xətt/üst xətt/kod, keçid, sitat, təsadüfi %%% alternativlər. Sahələr: { "{" }first{ "}" }, { "{" }last{ "}" }, { "{" }fullname{ "}" }, { "{" }username{ "}" }, { "{" }mention{ "}" }, { "{" }id{ "}" }, { "{" }chatname{ "}" }, { "{" }count{ "}" }. /button URL/qeyd/qayda düymələri yaradır. Ümumi seçimlər preview/nonotif/protect/mediaspoiler; qeydlər admin/private/noprivate/repeat; filtrlər user/allow_bot/replytag/command. /save söz Salam { "{" }repeat 5m{ "}" } yalnız açıq məzmunu müəllifin hazırkı hüquqları ilə planlayır. Qaydalar, salamlamalar və şəxsi məzmun ortaq göstərmə istifadə edir. Media ID-ləri bota aiddir.
gg-help-family-captcha = <b>Yoxlama</b> · /captcha on/off; /captchamode off/button/math/text/text2; /setcaptchatext; /captcharules on; /captchakick on/off; /captchakicktime və /captchamutetime məhdud müddət qurur. Verilmiş yoxlama nəsil və vaxtı saxlayır. Sorğular invite-users, susdurma restrict-members tələb edir. Cavablar şəxsidir və bir dəfə işləyir. Federasiya blokları təsdiq/CAPTCHA-dan əvvəldir.
gg-help-family-locks = <b>Kilidlər</b> · /lock links [əməliyyat], /unlock növ; /locktypes real növləri, /locks vəziyyəti göstərir. /lockwarns xəbərdarlığı idarə edir. /allowlist: domen/yol, dəqiq dəvət, @söhbət və ya stickerpack:/forward:/inline:/channel:/chat:/bot:/command:. Etibarsız şablon rədd edilir. İstisna yalnız uyğun məzmuna aiddir; səssiz avtomatika yaradıcı və səlahiyyətli jurnal tələb edir.
gg-help-family-blocklists = <b>Qadağa siyahısı</b> · /addblocklist "ifadə" mətn/prefiks/dəqiq uyğunluq və müəyyən kimliyi, könüllü səbəb/əməliyyatı dəstəkləyir. /rmblocklist dəqiq seçilən açarları silir. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute əməliyyatı seçir; müvəqqəti rejim müddət tələb edir. /blocklistdelete silməni ayrı idarə edir. Şablon mürəkkəbliyi məhduddur; etibarsız yazı və hədd aşımı rədd edilir.
gg-help-family-antispam = <b>Sel və kütləvi giriş</b> · /setflood say ardıcıl mesajları; /setfloodtimer say müddət vaxt pəncərəsini; /setfloodmode cəza/müddəti; /clearflood sıra təmizliyini qurur. Köhnə ayarlar qalır. /flood və /antiflood siyasəti göstərir; alias yerli uyğunluq qərarıdır. /antiraid on/off/duration, /raidtime, /raidactiontime, /autoantiraid müddət və yeni girişin ayrı cəzasını saxlayır. Təsdiq/CAPTCHA-dan üstündür; nəsilli vaxt bitməsi yenidən başlamaya davamlıdır.
gg-help-family-connections = <b>Bağlantılar</b> · /connect groupID və ya şəxsi keçid. Sizin və botun üzvlüyü yoxlanır; dəyişiklik yenə dəqiq hazırkı hüquq tələb edir. /connection seçimi göstərir, /disconnect silir, /connect davamlı tarixçəni göstərir. Bağlantı federasiya sahibliyi və ya operator hüququ vermir.
gg-help-family-identity = <b>Məlumat</b> · /id real istifadəçi/söhbət/mənbə ID-lərini; /info hazırkı hədəfi göstərir. Cavablar və @adlar bu botun hazırkı sübutunu tələb edir. Anonim qrup mesajı insanı tanıtmır; insan ID-si uydurulmur.
gg-help-family-policy = <b>Siyasət</b> · /disable əmr, /enable əmr, /disabled, /disableable əsas ad və alias istifadə edir. /disableadmin administrator istisnasını; /disabledel silməni idarə edir. Bərpa əmrləri əlçatan qalır. /bot2bot off/admin/all real üzvlüyü yoxlayır; dəyişiklik standartda insan yoxlaması tələb edir. /bot2botskipreview yalnız yaradıcı. /silentactions razılıq və səlahiyyətli jurnal tələb edir. Müəyyənləşməmiş runs/saved izah qaytarır.
gg-help-family-cleanup = <b>Təmizlik</b> · /cleancommand admin/user/other və /keepcommand əmrləri seçir. /cleanmsg action/filter/note və /keepmsg yalnız bu botun real göndərdiyi mesajlar üçündür; qəbz və beş dəqiqəlik işlər ID təxminini əngəlləyir. /cleanservice və /nocleanservice: join/leave/other/photo/pin/title/videochat. Funksional emal və etibarlı ödəniş təmizlikdən əvvəldir.
gg-help-family-topics = <b>Mövzular</b> · /newtopic ad, /renametopic ad, /closetopic, /reopentopic real hazırkı mövzuda işləyir. /deletetopic yaradıcı təsdiqi tələb edir; /setactiontopic eyni qrup hədəfini seçir. Telegram forumu və manage-topics lazımdır. Çatışmayan/dəstəklənməyən mövzu real xəta verir.
gg-help-family-utilities = <b>Alətlər</b> · /echo və /say birbaşa/cavab məzmununu ortaq məhdud göstərmə ilə göndərir. /broadcast yalnız təyin olunmuş operator və ya real uşaq sahibinə aiddir; yalnız bu botun qurulmuş qruplarını əhatə edir. Hədəf nəticələri qismən/qeyri-müəyyən çatdırılmanı saxlayır; vəziyyət və ləğv uğurlu əlavələri təkrarlamır.
gg-help-family-federations = <b>Federasiyalar</b> · /newfed ad bu botda UUID yaradır. Şəxsi əmrlər bağlantıdan asılı olmayaraq öz federasiyanızı istifadə edir; UUID oxumaq rol vermir. /fedpromote və /feddemote administratorları idarə edir; /feddemoteme istefa verir. /joinfed UUID və /leavefed hazırkı qrup yaradıcısını tələb edir. Silmə Telegram bloklarını götürmür. /fban userID səbəb və /unfban userID federasiya sahibi/admini; /fedreason, /fednotif, /setfedlog sahib tələb edir. /quietfed yalnız passiv izahı gizlədir. /subfed UUID yönlü, məhdud və dövrəsizdir. /fedstat [userID], /fbanstat UUID mənbə/vəziyyəti göstərir. /fbanlist csv/minicsv/json sahibə aiddir, ortaq 30 dəqiqə aralıqlıdır; /importfbans məhdud CSV və ya real sətir-sətir JSON-a cavabdır, öz JSON massivini də açıq dəstəkləyir. Yalnız müşahidə edilmiş istifadəçi yoxlanır, tam üzv siyahısı iddia edilmir.
gg-help-family-portability = <b>Fayllar və məxfilik</b> · /export all və ya modullar administrator tələb edir; /import və /reset hazırkı insan yaradıcıdan şəxsi, birdəfəlik beş dəqiqə təsdiqi alır. Yerli beş dəqiqə aralığı; öz versiyalı JSON, ən çox 2MiB və qurulmuş məzmun həddi. Modullar: moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Seçilməyən modullar qalır. Etibar, verilmiş yoxlama/işlər, abunələr, rollar və aktiv bloklar idxal olunmur. /privacy policy/data/delete yalnız öz şəxsi söhbətində səhifələmə və minimal təhlükəsizlik saxlaması ilə işləyir. Tam Rose ixracına yoxlanmış uyğunlaşdırıcı yoxdur.
gg-help-family-discovery = <b>Yardım</b> · /help bölmələri; /help əmr ad/alias axtarışını; /help bölmə 2 davamı göstərir. /button düymə işarələməsinə kömək edir. Bələdçi kontekst, hüquq, standartlar və həddi izah edir. /settings şəxsi qrup panelini açır.
gg-data-error-cache_pending = Könüllü SQL məlumatı silindi. Əlçatmaz keş təmizliyi növbədədir; aktiv təhlükəsizlik qeydləri qalır.
