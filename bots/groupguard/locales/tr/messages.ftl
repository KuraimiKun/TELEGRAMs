## Independently authored Group Guard tr content.
group-welcome = 🛡 Beni eklediğiniz için teşekkürler! Mesaj silme, üyeleri kısıtlama ve mesaj sabitleme yönetici haklarını verin. /settings ile yapılandırın.
gg-start = 🛡 Merhaba <b>{ $name }</b>! Ben <b>Group Guard</b>: yeni üye doğrulama, mesaj akını ve CAS koruması, içerik kilitleri, moderasyon, notlar, filtreler, kurallar ve karşılamalar. Beni yönetici ekleyip /settings veya /help kullanın.
gg-help = 📖 /help bölümleri gösterir; /help komut komutları arar. Moderasyon: /ban /mute /kick /warn. İçerik: /save /filter /rules. Koruma: /lock /blocklist /night. /settings kişisel grup panelini açar.
gg-welcome-default = 👋 { "{" }mention{ "}" }, <b>{ "{" }group{ "}" }</b> grubuna hoş geldiniz!
gg-credit = 🛡 @{ $bot } tarafından korunuyor
gg-btn-add = ➕ Gruba ekle
gg-btn-commands = 📖 Komutlar
gg-btn-rules = 📜 Kurallar
gg-btn-human = ✅ Ben insanım
gg-btn-unwarn = ↩️ Uyarıyı kaldır (yöneticiler)
gg-btn-locks = 🔒 İçerik kilitleri · Sayı: { $count }
gg-btn-open-settings = ⚙️ Ayarları aç
gg-btn-admin-tab = 🛡 Gruplar
gg-captcha = 🤖 Belirtilen süre içinde insan olduğunuzu doğrulayın; aksi halde çıkarılırsınız.
    Dakika: { $minutes }
    Üye: { $user }
gg-captcha-button = Aşağıdaki düğmeye basın 👇
gg-captcha-math = <b>{ $a } + { $b }</b> kaç eder?
gg-captcha-not-you = Bu düğme başka bir kişiye ait.
gg-captcha-ok = ✅ Hoş geldiniz!
gg-captcha-wrong = ❌ Yanlış yanıt. Deneme kaldıysa yeniden deneyin.
    Kalan denemeler: { $left }
gg-captcha-failed = ❌ Çok fazla yanlış yanıt.
gg-captcha-passed = ✅ Doğrulama başarılı. Hoş geldiniz!
    Üye: { $user }
gg-cas-banned = 🚫 CAS üyeyi spam göndericisi olarak tanıyor; üye yasaklandı.
    Üye: { $user }
gg-join-request = 👋 Gruba katılmak için insan olduğunuzu doğrulayın:
    Grup: { $group }
gg-join-approved = ✅ İstek onaylandı. Hoş geldiniz!
gg-join-expired = ⌛ İsteğin süresi doldu. Yeni katılma isteği gönderin.
gg-goodbye = 👋 Üye gruptan ayrıldı.
    Üye: { $user }
gg-flood-mute = 🌊 Üye çok fazla mesaj nedeniyle geçici olarak susturuldu.
    Üye: { $user }
gg-flood-kick = 🌊 Üye çok fazla mesaj nedeniyle çıkarıldı.
    Üye: { $user }
gg-flood-ban = 🌊 Üye çok fazla mesaj nedeniyle yasaklandı.
    Üye: { $user }
gg-newbie-links = 🆕 Yeni üyeler belirtilen ilk saatlerde bağlantı gönderemez.
    Saat: { $hours }
    Üye: { $user }
gg-spam-banned = 🧠 Üye spam nedeniyle yasaklandı.
    Üye: { $user }
gg-reason-blocklist = yasaklı sözcük
gg-need-right = ⛔ İlgili yönetici hakkı gerekiyor.
    Hak: { $right }
gg-right-admin = yönetici
gg-right-restrict = üyeleri kısıtlama
gg-right-delete = mesaj silme
gg-right-pin = mesaj sabitleme
gg-right-change_info = grup bilgilerini değiştirme
gg-admins-only = ⛔ Yalnızca yöneticiler.
gg-need-target = 👤 Bir mesajı yanıtlayın veya kimlik ya da güncel doğrulanmış @kullanıcı adı verin.
gg-target-admin = 🙅 Bu işlem bir yöneticiyi hedefleyemez.
gg-bot-no-rights = ⚠️ Gerekli haklara sahip yönetici olmam gerekiyor.
gg-banned = 🔨 Üye yasaklandı.
    Gerekçe: { $reason }
    Üye: { $user }
gg-banned-for = 🔨 Üye belirtilen süre için yasaklandı.
    Gerekçe: { $reason }
    Zaman: { $time }
    Üye: { $user }
gg-unbanned = ✅ Üyenin yasağı kaldırıldı.
    Üye: { $user }
gg-kicked = 👢 Üye çıkarıldı; yeniden katılabilir.
    Gerekçe: { $reason }
    Üye: { $user }
gg-muted = 🔇 Üye susturuldu.
    Gerekçe: { $reason }
    Üye: { $user }
gg-muted-for = 🔇 Üye belirtilen süre için susturuldu.
    Gerekçe: { $reason }
    Zaman: { $time }
    Üye: { $user }
gg-unmuted = 🔊 Üye yeniden yazabilir.
    Üye: { $user }
gg-warned = ⚠️ Üyenin uyarısı kaydedildi.
    Sayı: { $count }
    Sınır: { $limit }
    Gerekçe: { $reason }
    Üye: { $user }
gg-warn-limit-ban = 🔨 Uyarı sınırına ulaşıldı; üye yasaklandı.
    Sınır: { $limit }
    Üye: { $user }
gg-warn-limit-mute = 🔇 Uyarı sınırına ulaşıldı; üye susturuldu.
    Sınır: { $limit }
    Üye: { $user }
gg-warn-limit-kick = 👢 Uyarı sınırına ulaşıldı; üye çıkarıldı.
    Sınır: { $limit }
    Üye: { $user }
gg-unwarned = ↩️ Üyenin bir uyarısı kaldırıldı.
    Sayı: { $count }
    Sınır: { $limit }
    Üye: { $user }
gg-warn-removed = ↩️ Yönetici uyarıyı kaldırdı.
    Yönetici: { $admin }
gg-warns = ⚠️ Üyenin uyarıları:
    Sayı: { $count }
    Sınır: { $limit }
    Üye: { $user }
gg-warns-reset = 🧽 Üyenin uyarıları sıfırlandı.
    Üye: { $user }
gg-purge-reply = 🧹 Silinecek ilk mesajı yanıtlayın.
gg-purged = 🧹 Mesajlar silindi.
    Sayı: { $count }
gg-pin-reply = 📌 Sabitlenecek mesajı yanıtlayın.
gg-report-reply = 🚨 Bildirilecek mesajı yanıtlayın.
gg-reported = 🚨 Üye yöneticilere bildirildi.
    Üye: { $user }
gg-setlog-usage = 📒 Beni günlük kanalında yönetici yapıp kanal kimliğiyle <code>/setlog -100…</code> kullanın.
gg-setlog-failed = ⚠️ Orada yazamıyorum. Önce beni yönetici ekleyin.
gg-setlog-done = 📒 Günlük kanalı bağlandı.
gg-setlog-off = 📒 Günlük kanalı ayrıldı.
gg-log-connected = 📒 Bu sohbet grubun moderasyon günlüğünü alıyor.
    Grup: { $group }
gg-log-flood = 🌊 Mesaj akını algılandı:
    İşlem: { $action }
    Üye: { $user }
gg-log-report = 🚨 Üye bildirimi:
    Üye: { $user }
gg-log-spam = 🧠 Yapay zekanın algıladığı spam yasağı:
    Metin: { $text }
    Üye: { $user }
gg-rules = 📜 <b>Kurallar</b>
    { $rules }
gg-no-rules = 📜 Henüz kural kaydedilmedi. Yöneticiler /setrules metin kullanabilir.
gg-rules-saved = 📜 Kurallar kaydedildi.
gg-rules-cleared = 📜 Kurallar silindi.
gg-welcome-usage = 👋 <code>/setwelcome Merhaba {"{"}mention{"}"}, {"{"}group{"}"} grubuna hoş geldin!</code> kullanın veya bir mesajı yanıtlayın.
gg-welcome-saved = 👋 Karşılama kaydedildi.
gg-welcome-reset = 👋 Varsayılan karşılama geri yüklendi.
gg-note-usage = 📝 <code>/save ad metin</code> veya <code>/save ad</code> ile yanıt.
gg-filter-usage = 🔁 <code>/filter sözcük yanıt</code> veya <code>/filter sözcük</code> ile yanıt.
gg-note-saved = 📝 Not kaydedildi. Haklara göre <code>#{ $key }</code> ile erişin.
gg-filter-saved = 🔁 “{ $key }” eşleştiğinde yanıtlayacağım.
gg-notes-empty = 📝 Henüz not yok.
gg-filters-empty = 🔁 Henüz filtre yok.
gg-notes-list = 📝 <b>Notlar</b>
gg-filters-list = 🔁 <b>Filtreler</b>
gg-item-deleted = 🗑 Kayıt silindi.
    Anahtar: { $key }
gg-item-missing = 🤷 Bu adda kayıtlı içerik yok.
gg-items-limit = 📦 Grubun not ve filtre sınırına ulaşıldı.
gg-lock-usage = 🔒 <code>/lock links</code> kullanın. Türler aşağıda; <code>all</code> hepsini seçer.
    Türler: { $types }
gg-locked = 🔒 Yasaklı içerik:
    Türler: { $types }
gg-unlocked = 🔓 İzinli içerik:
    Türler: { $types }
gg-locks-title = 🔒 <b>İçerik kilitleri</b>
gg-locks-panel = 🔒 <b>Kilitler</b>: yasaklı içerik silinir; yöneticiler muaftır.
gg-lock-links = Bağlantılar
gg-lock-invites = Davet bağlantıları
gg-lock-forwards = İletilen mesajlar
gg-lock-media = Medya
gg-lock-stickers = Çıkartmalar
gg-lock-gifs = GIF
gg-lock-voice = Sesli mesajlar
gg-lock-polls = Anketler
gg-lock-bots = Botlar
gg-blocklist = 🚫 <b>Yasaklı sözcükler</b>
    Sözcükler: { $words }
gg-blocklist-empty = 🚫 Yasaklı sözcük yok.
gg-blocklist-usage = 🚫 <code>/addblock sözcük, diğer ifade</code> · <code>/rmblock sözcük</code>
gg-blocklist-saved = 🚫 Yasak listesi güncellendi.
    Sayı: { $count }
gg-night-usage = 🌙 <code>/night 23 7 +3</code> UTC+3 için 23:00–07:00 kapatır; <code>/night off</code> devre dışı bırakır.
gg-night-on = 🌙 Grubun gece saatleri ayarlandı.
    Bitiş: { $end }
    Başlangıç: { $start }
    Saat dilimi: { $tz }
gg-night-off = 🌙 Gece modu kapatıldı.
gg-night-start = 🌙 İyi geceler! Grup belirtilen saate kadar kapalı.
    Bitiş: { $end }
gg-night-end = ☀️ Günaydın! Grup yeniden açık.
gg-panel = ⚙️ <b>Grup ayarları</b>
    Değiştirmek için seçeneğe basın. Gece saatleri /night ile ayarlanır.
    Grup: { $group }
    Gece saatleri: { $night }
gg-panel-sent = 📬 Ayarlar özelden gönderildi.
gg-panel-start-first = 📬 Önce benimle özel sohbet başlatın, sonra aşağıya basın.
gg-credit-vip = 💎 Koruma satırını gizlemek VIP gerektirir. Özelden /vip kullanın.
gg-opt-wel = 👋 Karşılama · Değer: { $value }
gg-opt-cln = 🧹 Katılma mesajlarını sil · Değer: { $value }
gg-opt-bye = 👋 Ayrılma · Değer: { $value }
gg-opt-cap = 🤖 Doğrulama · Değer: { $value }
gg-opt-cpm = ⏱ Doğrulama süresi, dakika · Değer: { $value }
gg-opt-fld = 🌊 Mesaj sınırı · Değer: { $value }
gg-opt-fla = 🌊 Mesaj akını işlemi · Değer: { $value }
gg-opt-wrn = ⚠️ Uyarı sınırı · Değer: { $value }
gg-opt-wra = ⚠️ Uyarı işlemi · Değer: { $value }
gg-opt-act = ⏳ Otomatik kısıtlama, dakika · Değer: { $value }
gg-opt-cas = 🛡 CAS koruması · Değer: { $value }
gg-opt-nwb = 🆕 Yeni üyeler bağlantısız, saat · Değer: { $value }
gg-opt-ais = 🧠 Yapay zeka spam koruması · Değer: { $value }
gg-opt-ngt = 🌙 Gece modu · Değer: { $value }
gg-opt-crd = 🏷 Koruma satırı · Değer: { $value }
gg-opt-lang = 🌐 Dil · Değer: { $value }
gg-val-button = Düğme
gg-val-math = Hesap
gg-val-off = kapalı
gg-val-mute = sustur
gg-val-kick = çıkar
gg-val-ban = yasakla
gg-adm = 🛡 <b>Group Guard: istatistik</b>
    Gruplar: { $groups }
    Kayıtlar: { $items }
    Uyarılar: { $warns }
cmd-settings = Grup ayarları
cmd-help = Komut rehberi
gg-auth-denied = Yetki doğrulanamadı. Hiçbir şey değiştirilmedi.
gg-target-invalid = Bilinen bir insan üye seçin. Hedef doğrulanamadı.
gg-duration-invalid = 60s–365d süre kullanın. Geçici komutlar süre gerektirir.
gg-reason-invalid = Gerekçe en fazla 256 karakter olabilir.
gg-outcome-failed = İşlem başarısız veya yetkisiz.
gg-outcome-partial = İşlem kısmen tamamlandı. Çıkarmadan sonraki geri yükleme başarısızsa yasak kalabilir.
gg-outcome-ancillary = Ana işlem tamamlandı ancak ek bir adım başarısız oldu.
gg-review-request = Aşağıdaki değişmez işlemi inceleyin. Güncel yetkili bir insan 120 saniye içinde onaylayabilir. Süre saniye olarak gösterilir.
    Ayrıntılar: { $details }
    Süre: { $duration }
    İşlem: { $operation }
    Hedef: { $target }
gg-review-approve = Bu işlemi onayla
gg-review-unavailable = Onay deposu kullanılamıyor. Yeni komut gönderin.
gg-review-expired = Onayın süresi dolmuş, geçersiz veya kullanılmış.
gg-review-consumed = Onay kullanıldı. Sonucu kontrol edin; tekrar için yeni komut gerekir.
gg-duration-permanent = Kalıcı / süresiz
gg-purge-ack = API silme isteklerini onayladı. Gerçekte silinen sayı bilinmiyor.
    API onayı: { $acknowledged }
    İstendi: { $requested }
gg-warning-removed = Uyarı kaldırıldı.
gg-op-ban = yasakla
gg-op-mute = sustur
gg-op-kick = çıkar
gg-op-unban = yasağı kaldır
gg-op-unmute = susturmayı kaldır
gg-op-warn = uyar
gg-op-unwarn = uyarıyı kaldır
gg-op-resetwarns = uyarıları sıfırla
gg-op-purge = mesaj aralığını sil
gg-op-delete = mesajı sil
gg-op-pin = mesajı sabitle
gg-op-unpin = sabitlemeyi kaldır
gg-op-setlog = günlük hedefini ayarla
gg-op-unsetlog = günlük hedefini kaldır
gg-op-config = ayarları değiştir
gg-op-save = içeriği kaydet
gg-op-remove = içeriği kaldır
gg-op-panel = paneli aç
gg-review-details-above = İstenen içeriğin tamamı hemen yukarıdaki mesajda.
gg-warn-pending = Uyarı kaydedildi; sınır işlemi zaten işleniyor.
gg-done = Tamamlandı.
gg-setting-saved = Ayar kaydedildi.
    Ayar: { $setting }
gg-setting-value = Güncel ayar değeri:
    Ayar: { $setting }
    Değer: { $value }
gg-setting-invalid = Geçersiz ayar. on/off, geçerli mod veya 10m gibi süre kullanın.
gg-warning-settings = Uyarı ayarları:
    Süre: { $duration }
    Bitiş zamanı: { $expiry }
    Sınır: { $limit }
    Mod: { $mode }
gg-admin-changed = Yönetici işlemi tamamlandı.
    İşlem: { $action }
    Üye: { $user }
gg-admin-list = Herkese açık yöneticiler:
    { $admins }
gg-approved = Üye onaylandı.
    Gerekçe: { $reason }
    Üye: { $user }
gg-unapproved = Onaylar kaldırıldı.
    Sayı: { $count }
gg-approval-status = Üyenin onay durumu:
    Gerekçe: { $reason }
    Durum: { $status }
    Üye: { $user }
gg-approval-list = Onaylı üyeler:
    { $approvals }
gg-next-page = Diğer kayıtlar: { $command }
gg-range-invalid = Geçersiz aralık. En az bir mesaj seçin ve belirtilen sınırı aşmayın.
    Üst sınır: { $cap }
gg-range-start = Başlangıç bu konuda sizin için on dakika kaydedildi. Son mesajı /purgeto ile yanıtlayın.
gg-range-missing = Burada sizin için kayıtlı başlangıç yok. Önce yanıt olarak /purgefrom kullanın.
gg-content-needed = İçerik verin veya yanıtlayın; en fazla 3500 karakter.
gg-log-status = Günlük ayarları:
    Kategoriler: { $categories }
    Hedef: { $destination }
gg-log-unverified = Bu kanal komutunun doğrulanmış aslını almadım. Önce kanalda /setlog gönderin.
gg-log-forward = Bu özgün /setlog komutunu gruba iletin. Bağlayan yönetici her iki sohbetin bilgilerini değiştirebilmelidir.
gg-info = Kullanıcı veya sohbet bilgileri:
    Kimlik: { $id }
    Üyelik: { $membership }
    Ad: { $name }
    Kullanıcı adı: { $username }
gg-op-unpinall = tüm sabitlemeleri kaldır
gg-op-permapin = kalıcı sabitle
gg-op-promote = yönetici ata
gg-op-demote = yöneticiyi kaldır
gg-op-approve_user = kullanıcıyı onayla
gg-op-unapprove = onayı kaldır
gg-op-unapproveall = tüm onayları kaldır
gg-unknown = Bilinmiyor
gg-chat-id = Sohbet kimliği:
    Kimlik: { $id }
gg-on = Açık
gg-off = Kapalı
gg-anon-enabled = Anonim yöneticilere güven burada açık. Bu grubun anonim komutları insanı tanımlamadan bot haklarını kullanır. Sahip işlemleri yine doğrulanmış oluşturanı gerektirir. /anonadmin off insan incelemesini geri getirir.
gg-right-invite_users = kullanıcı davet etme
gg-right-promote_members = yönetici atama
gg-right-manage_topics = konuları yönetme
gg-right-creator = grubu oluşturan
gg-log-join = Üye katıldı.
    Üye: { $user }
gg-log-leave = Üye ayrıldı.
    Üye: { $user }
gg-warning-row = Uyarı kaydı:
    Bitiş zamanı: { $expiry }
    Kimlik: { $id }
    Gerekçe: { $reason }
gg-menu-prompt = Bir seçenek seçin.
gg-content-invalid = İçerik geçersiz veya Telegram sınırlarını aşıyor. Adı, biçimi, değiştiricileri ve düğmeleri kontrol edin.
gg-content-unavailable = İçerik kullanılamıyor veya güncel grup üyeliğiniz erişime izin vermiyor.
gg-btn-private-note = Notu aç
gg-open-private = Bu içeriği özelden aç:
gg-items-cleared = Kayıtlar silindi.
    Sayı: { $count }
gg-clearall-confirm = Grubu oluşturan <code>/{ $command } confirm</code> ile onaylar.
gg-button-usage = <code>/button "Etiket" https://example.com</code> kullanın. Aynı satıra ek düğme için <code>"Not" #ad same</code> ekleyin. İşaretleme ve çalışan önizleme alırsınız.
gg-btn-accept-rules = Kuralları kabul et
gg-btn-open-verification = Doğrulamayı aç
gg-captcha-private = Grup üyeliğinizi doğrulamak için özel doğrulamayı açın.
    Üye: { $user }
gg-captcha-choice = Düğmelerle eşleşen resmi seçin. Mod ve karakter konumu aşağıda.
    Mod: { $mode }
    Konum: { $position }
gg-captcha-settings = Doğrulama ayarları:
    Açık: { $enabled }
    Çıkarma: { $kick }
    Mod: { $mode }
    Serbest bırakma: { $release }
    Saniye: { $seconds }
gg-captcha-dependency = Doğrulamadan önce karşılamayı açın. Kabul zorunluluğundan önce kuralları kaydedin.
gg-val-text = Metin resmi
gg-val-text2 = Karakter resmi
gg-captcha-attempts-exhausted = Çok fazla yanlış yanıttan sonra doğrulama başarısız; öngörülen kısıtlama uygulandı.
gg-captcha-admin-exempt = Artık grup yöneticisisiniz. Doğrulama sona erdi.
gg-captcha-question-text = Resimdeki sözcüğü seçin.
gg-captcha-question-math = Resimdeki denklemi çözün ve yanıtı seçin.
gg-captcha-question-text2 = Resimde belirtilen karakteri soldan sağa seçin.
    Konum: { $position }
gg-locktypes = Kullanılabilir içerik kilitleri:
    Türler: { $types }
gg-allowlist-title = İçerik kilidi istisnaları
gg-allowlist-invalid = Geçersiz istisna. Alan adı/yol, tam davet, @sohbet veya stickerpack:ad gibi belirtilen kimlik kullanın.
gg-reason-lock = Yasaklı içerik:
    Türler: { $types }
gg-lock-applied = Kilit kuralı uygulandı.
    Gerekçe: { $reason }
    Türler: { $types }
gg-reaction-failed = Tepki kuralı uygulanamadı. Bu Bot API sunucusu tepki kaldırmayı desteklemeyebilir.
    Kod: { $code }
gg-reaction-anonymous = Anonim sayımlar kullanıcı veya gönderen sohbet kimliği vermez. Kaldırma API’si bunu gerektirir; kaldırıldığı iddia edilmez.
gg-none = Yok
gg-blocklist-title = Yasak listesi
gg-blocklist-invalid = Geçersiz tetikleyici, gerekçe veya işlem. Tırnakları, joker kaçışlarını ve geçici modların gerekli süresini kontrol edin.
gg-blocklist-settings = Yasak listesi ayarları:
    Silme: { $delete }
    Mod: { $mode }
gg-blocklist-action = Yasak listesi kuralı üyeye uygulandı.
    Gerekçe: { $reason }
    Üye: { $user }
gg-lock-album = Albümler
gg-lock-anonchannel = Kanal gönderenleri
gg-lock-audio = Ses
gg-lock-bot = Botlar
gg-lock-button = Satır içi düğmeler
gg-lock-cashtag = Para birimi etiketleri
gg-lock-checklist = Kontrol listeleri
gg-lock-cjk = Çince/Japonca/Korece metin
gg-lock-command = Komutlar
gg-lock-comment = Üye olmayan yorumları
gg-lock-contact = Kişiler
gg-lock-cyrillic = Kiril metni
gg-lock-document = Belgeler
gg-lock-email = E-posta adresleri
gg-lock-emoji = Emoji
gg-lock-emojicustom = Özel emoji
gg-lock-emojigame = Emoji oyunları
gg-lock-emojionly = Yalnız emoji
gg-lock-externalreply = Dış yanıtlar
gg-lock-forward = İletilen mesajlar
gg-lock-forwarduser = Kullanıcı iletileri
gg-lock-forwardbot = Bot iletileri
gg-lock-forwardchannel = Kanal iletileri
gg-lock-forwardstory = İletilen hikayeler
gg-lock-game = Oyunlar
gg-lock-gif = GIF animasyonları
gg-lock-guestbot = Konuk botlar
gg-lock-inline = Satır içi botlar
gg-lock-invitelink = Telegram davetleri
gg-lock-botlink = Bot bağlantıları
gg-lock-location = Konumlar
gg-lock-outsidereaction = Üye olmayan tepkileri
gg-lock-phone = Telefon numaraları
gg-lock-photo = Fotoğraflar
gg-lock-poll = Anketler
gg-lock-reaction = Tepkiler
gg-lock-rtl = Sağdan sola metin
gg-lock-spoiler = Gizli içerik
gg-lock-sticker = Çıkartmalar
gg-lock-stickeranimated = Hareketli çıkartmalar
gg-lock-stickerpremium = Premium çıkartmalar
gg-lock-text = Metin
gg-lock-url = URL
gg-lock-video = Videolar
gg-lock-videonote = Video mesajları
gg-flood-status = Mesaj akını: ardışık sınır N’de, zaman penceresi N’den fazla olduğunda işler. İşlem, süre ve sıra temizliği aşağıda.
    Tüm sırayı temizle: { $clear }
    Ardışık sınır: { $consecutive }
    Sayı: { $count }
    Süre: { $duration }
    Mod: { $mode }
    Saniye: { $seconds }
gg-raid-status = Toplu katılma koruması. /antiraid on açar; /antiraid off durdurur. Dönem, yasak süresi ve dakikalık otomatik sınır aşağıda.
    Etkin: { $active }
    Otomatik sınır: { $auto }
    Yasak süresi: { $ban }
    Dönem: { $period }
    Kadar: { $until }
gg-raid-banned = 🛡 Toplu katılma koruması etkin olduğu sırada üye geçici yasaklandı.
    Üye: { $user }
gg-raid-declined = 🛡 Toplu katılma koruması etkin olduğu sırada istek reddedildi.
    Üye: { $user }
gg-silent-consent-required = Bu işlemi seçmeden önce oluşturan sessiz işlemlere izin vermeli ve günlük ayarlamalıdır.
gg-btn-enable-raid = Toplu katılma korumasını aç
gg-human-required = Bu işlem tanımlanabilir bir insan gerektirir.
gg-group-message-required = Komutu gerçek grup mesajı veya konusunda kullanın. Özel mesaj kimliği grup mesajını göstermez.
gg-connection-private = Bu bağlantı komutunu özel sohbetimizde kullanın.
gg-connection-disconnected = Bağlantı kesildi. Son beş grup yeniden bağlanmak için kalır.
gg-connection-current = Grup bağlandı. Her işlemde üyelik ve güncel haklar denetlenir.
    Grup: { $group }
gg-connection-none = Etkin bağlantı yok. /connect GROUP_ID veya /connect @grup kullanın.
gg-connection-open = Kişisel bağlantınızı özel sohbetimizde açın.
gg-btn-connect = Özelden bağlan
gg-connection-history = Son beş grubunuz. Birini seçin; güncel üyelik gerekir.
gg-connection-unavailable = Bağlantı kullanılamıyor. Güncel insan üye olmalısınız ve bot o grupta yönetici olmalıdır.
gg-catalog-unresolved = /{ $command } katalogda tanımlı işlemi olmayan bir ad. Uygulanan işlevler için /notes veya /flood kullanın.
gg-cleanup-failed = Mesaj temizliği başarısız veya kullanılamıyor; silindiği iddia edilmez.
gg-op-lock_change = içerik kilitlerini değiştir
gg-op-allowlist_change = istisnaları değiştir
gg-op-allowlist_clear = istisnaları sil
gg-op-blocklist_change = yasak listesini değiştir
gg-op-blocklist_clear = yasak listesini boşalt
gg-op-raid_change = toplu katılma korumasını değiştir
gg-disabled-list = Komut politikası: /disable AD ve /enable AD çalıştırmayı; /disabledel silmeyi; /disableadmin yöneticileri kapsamayı yönetir.
    Komutlar: { $commands }
gg-cleanup-types = Kullanılabilir temizlik kategorileri:
    Türler: { $types }
gg-cleanup-selected = Seçilen temizlik kategorileri:
    Türler: { $types }
gg-advanced-status = Sessiz otomasyon oluşturanın izni ve günlük gerektirir. Botlara normal haklar gerekir; değişiklik incelemesi varsayılan olarak açıktır. BotFather’da botlar arası görünürlüğü ayarlayın.
    Ayar: { $setting }
    Değer: { $value }
gg-action-topic = İşlem konusu. /setactiontopic güncel forum konusunu seçer; genel konunun kimliği 1’dir.
    Konu: { $topic }
gg-topic-unavailable = Güncel forum ve ilgili yönetim hakları gerekir.
gg-topic-id-required = Bağlı özel sohbette konu kimliğini açıkça verin.
gg-topic-general-delete = Genel konu silinemez. Onay tanımlanabilir bir insan gerektirir.
gg-topic-delete-confirm = Konu ve mesajlar silinsin mi? Kişisel onay iki dakika geçerlidir.
    Konu: { $topic }
gg-btn-confirm-delete = Silmeyi onayla
gg-topic-changed = Konu işlemi tamamlandı.
    İşlem: { $action }
    Konu: { $topic }
gg-op-policy_change = komut/temizlik politikasını değiştir
gg-op-topic_create = konu oluştur
gg-op-topic_rename = konuyu yeniden adlandır
gg-op-topic_close = konuyu kapat
gg-op-topic_reopen = konuyu yeniden aç
gg-op-topic_delete = konu ve mesajları sil
gg-op-echo = biçimli içerik gönder
gg-broadcast-owner = Yalnız bu botun yapılandırılmış işleticisi veya alt örneğin gerçek sahibi kendi gruplarına yayın yapabilir.
gg-broadcast-queued = Grup yayını sıraya alındı. Hedefler ve sonuçlar bot başına ayrıdır.
    Kimlik: { $id }
gg-broadcast-busy = Başka yayın etkin veya önceki oluşturmadan itibaren beş dakikalık aralık dolmadı.
gg-broadcast-empty = Bu botta grup yayınınız yok.
gg-broadcast-status = Grup yayını durumu:
    İptal edildi: { $cancelled }
    Başarısız: { $failed }
    Kimlik: { $id }
    Sırada: { $queued }
    İletildi: { $sent }
    Durum: { $status }
    Belirsiz sonuç: { $uncertain }
gg-fed-created = Federasyon oluşturuldu. Kimlik bu botun ayrı ağına aittir.
    Kimlik: { $id }
    Ad: { $name }
gg-fed-info = Federasyon bilgileri:
    Yöneticiler: { $admins }
    Kimlik: { $id }
    Günlük: { $log }
    Ad: { $name }
    Bildirimler: { $notifications }
    Sahip: { $owner }
    Gerekçe zorunlu: { $reasons }
gg-fed-list = Sahip veya yönetici olduğunuz federasyonlar:
    { $rows }
gg-fed-admins = Önce sahip, ardından federasyon yöneticileri:
    { $rows }
gg-fed-quiet = Sessiz pasif açıklamalar. Yasak uygulaması etkin kalır.
    Değer: { $value }
gg-fed-policy = Gerekçe ve sahip bildirimi politikaları:
    Bildirimler: { $notifications }
    Gerekçe zorunlu: { $reasons }
gg-fed-confirm-delete = Federasyon, veriler ve üyelikler kalıcı silinsin mi? Mevcut Telegram yasakları kalır. Beş dakika içinde kişisel onay verin.
    Kimlik: { $id }
    Ad: { $name }
gg-fed-confirm-log = Belirtilen federasyon günlüğü ayarlansın mı? Beş dakika içinde onaylayın. Hedef haklarınız ve botun yayın hakkı yeniden kontrol edilir.
    Hedef: { $destination }
    Kimlik: { $id }
    Ad: { $name }
gg-fed-confirm-sent = Kişisel onay federasyon sahibine gönderildi.
gg-fed-deleted = Federasyon silindi. Mevcut Telegram yasakları kalır.
gg-fed-log-set = Federasyon günlük hedefi ayarlandı:
    Hedef: { $destination }
gg-fed-cancel = İptal
gg-fed-cancelled = İptal edildi.
gg-fed-saved-delivery-failed = Değişiklik kaydedildi ancak bildirim veya günlük iletilmedi. Hedefi ve bot erişimini kontrol edin.
gg-fed-error-authority = Güncel federasyon sahibi veya ilgili rol gerekiyor. Telegram grup hakları federasyon hakları vermez.
gg-fed-error-private = Komutu bu botla kendi özel sohbetinizde kullanın.
gg-fed-error-group = Komutu gerçek grupta kullanın. Özel bağlantı federasyon grubunu seçmez.
gg-fed-error-owned = Bu botta zaten bir federasyonunuz var. Özelden /fedinfo, /renamefed veya /delfed kullanın.
gg-fed-error-name = Kontrol karakteri içermeyen, boş olmayan ad verin. Adlar 64 karakterle sınırlanır.
gg-fed-error-id = Bu botun geçerli federasyon UUID’sini verin. Rose kimlikleri ayrı hizmetimize bağlanmaz.
gg-fed-error-missing = Bu bot veya bağlamda federasyon bulunamadı.
gg-fed-error-creator = Yalnız güncel Telegram grubu oluşturanı grubu federasyona katabilir veya ayırabilir.
gg-fed-error-target = Pozitif insan kimliği, insana yanıt veya güncel doğrulanmış ad verin. Sahibin rütbesi düşürülemez.
gg-fed-error-value = Geçersiz federasyon argümanları. Politikalar için on/off ve gereken yerde geçerli kimlik kullanın.
gg-fed-error-stale = Onayın süresi dolmuş, kullanılmış veya federasyon, sahip ya da hedef değişmiş. Yeni onay isteyin.
gg-fed-error-destination = Sahip hedefte güncel yönetici olmalı, bot yayın yapabilmelidir. Kanallar post_messages gerektirir.
gg-fed-error-delivery = Kişisel onay iletilmedi veya bağlanmadı. Botla özel sohbet açıp yeniden deneyin.
gg-fed-event = Federasyon olayı:
    Olay: { $event }
    Kimlik: { $id }
    Ad: { $name }
    Üye: { $user }
gg-fed-event-rename = ad değişti
gg-fed-event-delete = silindi; Telegram yasakları kalır
gg-fed-event-promote = yönetici eklendi
gg-fed-event-demote = yönetici kaldırıldı
gg-fed-event-self-remove = yönetici görevden ayrıldı
gg-fed-event-reason = gerekçe politikası değişti
gg-fed-event-notif = sahip bildirimleri değişti
gg-fed-event-log = günlük hedefi değişti
gg-fed-event-unlog = günlük hedefi kaldırıldı
gg-fed-event-ban = yasak politikası kaydedildi; uygulama sırada
gg-fed-event-unban = yasak politikası kaldırıldı; kendi kısıtlamalarını kaldırma sırada
gg-fed-event-subscribe = abonelik eklendi; gözlenen kullanıcı denetimi sırada
gg-fed-event-unsubscribe = abonelik kaldırıldı; diğer kaynaklar kalır
gg-fed-ban-details = Yasak hedefi ve gerekçesi:
    Gerekçe: { $reason }
    Üye: { $user }
gg-fed-passive = Federasyon politikası üyeyi yasaklıyor. Kaynak ve gerekçe aşağıda.
    Kimlik: { $id }
    Gerekçe: { $reason }
    Kaynak: { $source }
    Üye: { $user }
gg-fed-enforce-failed = Federasyon politikası üyeyi yasaklıyor ancak çıkarma başarısız. Bot haklarını kontrol edin. Kaynak ve gerekçe aşağıda.
    Kimlik: { $id }
    Gerekçe: { $reason }
    Kaynak: { $source }
    Üye: { $user }
gg-fed-stat = Bu üyenin federasyon yasakları:
    { $rows }
    Üye: { $user }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — etkin: { $status }; değişme: { $date }.
gg-fed-stat-more = Başka kaynaklar var. Gerekçe ve tarih için devam komutu veya belirli federasyon kimliği kullanın.
gg-fed-intent-saved = Politika kaydedildi; gözlenen hedefler sırada. Etkilerden önce güncel haklar ve diğer kısıtlama kaynakları kontrol edilir.
    Üye: { $user }
    Sürüm: { $version }
gg-fed-subscriptions = Federasyon yasaklarına doğrudan abonelikler:
    { $rows }
gg-fed-imported = Kayıtlar doğrulandı ve kaydedildi; aynı yinelenenler atlandı. Gözlenen hedeflere uygulama sırada.
    Sayı: { $count }
    Aynı yinelenenler: { $duplicates }
gg-fed-event-import = doğrulanmış yasaklar içe aktarıldı; uygulama sırada
gg-fed-error-file-format = id/reason içeren UTF-8 CSV, user_id içeren JSONL/NDJSON veya bu botun JSON dizisi dışa aktarımını yanıtlayın. Bir geçersiz satır tüm yazmaları durdurur.
gg-fed-error-file-limit = En fazla 2 MiB ve 1000 kayıt. Eksik veya aşırı büyük dosyalar reddedilir; listeler sessizce kesilmez.
gg-fed-error-file-duplicate = Aynı kullanıcı kimliği için çelişen kayıtlar. Yasak içe aktarılmadı.
gg-fed-error-file-rate = İçe ve dışa aktarım federasyon başına 30 dakikalık aralığı paylaşır. Daha sonra deneyin.
gg-fed-error-reason = Yasak gerekçeleri desteklenmeyen kontrol karakteri olmadan en fazla 1024 karakterdir.
gg-fed-error-reason_required = Bu federasyon her yasak için boş olmayan gerekçe ister.
gg-fed-error-cycle = Federasyon kendine abone olamaz veya yönlü döngü oluşturamaz.
gg-fed-error-graph_limit = Sınıra ulaşıldı:32 doğrudan hedef,128 erişilebilir federasyon,16 derinlik veya bu botta10 000 bağlantı.
gg-data-confirm = Beş dakika içinde onaylayın. Güncel oluşturan ve grup revizyonu yeniden denetlenir. Yalnız seçilen modüller değişir; kimlik, güven ve etkin yasaklar kalır.
    SHA-256: { $digest }
    Grup: { $group }
    Modüller: { $modules }
    İşlem: { $operation }
gg-data-import = Grup modüllerini içe aktar
gg-data-reset = Grup modüllerini sıfırla
gg-data-privacy-delete = Bu botun isteğe bağlı kişisel verilerini sil
gg-data-confirm-button = Bu değişikliği onayla
gg-data-personal = Onayı özel sohbetinizde açın.
gg-data-saved = Seçilen modüller kaydedildi.
gg-data-error-authority = İçe aktarma ve sıfırlama güncel tanımlanabilir grubu oluşturanı gerektirir. Dışa aktarma güncel yönetici gerektirir.
gg-data-error-format = /export ile oluşturulmuş geçerli, sürümlü Group Guard JSON’u yanıtlayın.
gg-data-error-limit = Dosya boyut veya yapılandırılmış içerik sınırını aşıyor.
gg-data-error-version = Şema veya sürüm desteklenmiyor; değişiklik uygulanmadı.
gg-data-error-module = Bilinen modülleri seçin:/export all veya /export notes rules. İçe aktarma ve sıfırlama aynı adları kullanır.
gg-data-error-field = Geçersiz veya eksik modül alanları. Ayarlar uygulanmadı.
gg-data-error-item = İçerik, seçenekler veya tekrar erişimi geçersiz. İçerik kaydedilmedi.
gg-data-error-media = Medya bu bota yüklenmiş ve getFile ile erişilebilir olmalıdır. Diğer botların dosya kimlikleri desteklenmez.
gg-data-error-destination = Günlük ve konu hedefleri güncel haklar ve bot yetenekleri gerektirir. Konu kimlikleri yalnız aynı grupta geçerlidir.
gg-data-error-language = /setlang ile kurulu dil seçin.
gg-data-error-stale = Onayın süresi dolmuş, değişmiş veya kullanılmış. Yeniden başlayın.
gg-data-error-restore = Kendi geçici kısıtlamaları güvenli geri yüklenemedi. Kanıtlar kalır; bot haklarını kontrol edin.
gg-data-error-rate = Grup veri işlemlerinin yerel beş dakikalık aralığı vardır. Daha sonra deneyin.
gg-data-error-delivery = Özel onay iletilmedi. Botla özel sohbet başlatıp yeniden deneyin.
gg-data-error-saved_delivery = Ayarlar kaydedildi ancak komut önerileri güncellenmedi. Bot izinlerini kontrol edin.
gg-privacy-policy = <b>Bu Group Guard’daki verileriniz</b>
    /privacy data bağlantıları, gözlenen profilleri, uyarıları, onayları, kısıtlama/doğrulama durumunu, federasyon sahipliği/rolleri/yasakları ve güvenlik işlerini dışa aktarır. Başkalarının özel içeriği, doğrulama yanıtları, kimlik doğrulama ve ham dosyalar hariçtir. Devam komutunu izleyin.
    /privacy delete isteğe bağlı bağlantı geçmişini, gözlenen ad/kullanıcı adını, etkin olmayan doğrulamaları ve bu bottaki tamamlanmış kişisel yayın içeriğinizi kaldırır. Etkin uyarı/kısıtlamalar, yasak sürümleri, roller, sahiplik, abonelikler, tekrar koruması ve belirsiz API işleri güvenlik ve sıralama için asgari kimlikleri tutar. Bu ilişkiler için açık federasyondan ayrılma/silme komutlarını kullanın. Paylaşılan platform profili ve diğer botlar kalır.
    İşleticiler yedekleri ve denetimi ayrı yönetir. Komut dış Telegram mesajlarını veya yedekleri silmez, otomatik saklama süresi vaat etmez.
gg-privacy-usage = /privacy policy · /privacy data [devam] · /privacy delete — yalnız bu botla kendi özel sohbetinizde.
gg-privacy-private = İsteyen insanın özel sohbeti gereklidir. Geçersiz imleçler başkalarının verilerine erişim vermez.
gg-privacy-next = Sonraki veri sayfası:/privacy data { $cursor }
gg-privacy-deleted = Bu botun isteğe bağlı kişisel verileri kaldırıldı. Etkin güvenlik, sahiplik ve belirsiz işler asgari kimlikleri tutar; /privacy policy’ye bakın.
gg-language-usage = Grup dilini /setlang ile seçin. Özel /lang kişisel platform dilinizi değiştirir. Kullanılabilir kodlar aşağıda.
    Dil kodları: { $codes }
gg-language-saved = Grup yanıt dili değişti.
gg-help-index = <b>Group Guard komut rehberi</b>
    /help bölüm · /help komut · /help bölüm 2. Belirtilen komutlar doğrulanmış /connect ile de çalışır; özel yanıtlar gerçek özel sohbette kalır.
    Ayarlar bilgi değiştirme; cezalar üye kısıtlama; silme silme hakkı; sabitleme sabitleme hakkı; atamalar yönetici atama; konular konu yönetimi gerektirir. Bot hakları ayrı denetlenir. Sahip işlemleri güncel insan oluşturanı gerektirir. /settings kişisel grup panelini açar.
gg-help-search = <b>Eşleşen komutlar</b>
    Arama: { $query }
gg-help-connected = Grup veya doğrulanmış bağlantı; haklar bölümde
gg-help-group-only = Gerçek grup mesajı gerekir
gg-help-unsupported = Katalog adı korundu; tanımsız davranış açıklama döndürür
gg-help-next = Sonraki sayfa
gg-help-previous = Önceki sayfa
gg-help-family-title-moderation = Moderasyon ve onaylar
gg-help-family-title-messages = Mesaj silme ve sabitleme
gg-help-family-title-logging = Yetkili günlükler
gg-help-family-title-settings = Grup ayarları ve dil
gg-help-family-title-content = Notlar, filtreler, kurallar ve karşılamalar
gg-help-family-title-captcha = Yeni üye doğrulama
gg-help-family-title-locks = İçerik kilitleri ve istisnalar
gg-help-family-title-blocklists = Yasak listesi eşleşmeleri ve işlemler
gg-help-family-title-antispam = Mesaj akını ve toplu katılma koruması
gg-help-family-title-connections = Özel grup bağlantıları
gg-help-family-title-identity = Kullanıcı ve sohbet bilgileri
gg-help-family-title-policy = Komut ve bot politikası
gg-help-family-title-cleanup = Komut, bot ve hizmet temizliği
gg-help-family-title-topics = Forum konuları
gg-help-family-title-utilities = İçerik gönderme ve işletici yayınları
gg-help-family-title-federations = Federasyon rolleri, yasakları ve abonelikleri
gg-help-family-title-portability = Grup dosyaları ve kişisel veriler
gg-help-family-title-discovery = Yardım ve içerik düzenleyici
gg-help-family-moderation = <b>Moderasyon</b> · Yanıt, sayısal kimlik veya doğrulanmış @kullanıcı. /ban 20 gerekçe; /tban 20 60s gerekçe; /mute 20; /tmute 20 2h gerekçe. Geçici süre:60 saniye–365 gün. /kickme yalnız sizi çıkarır. d biçimleri yanıtlanan mesajı; s biçimleri komut/yanıtı siler ve silme hakkı ister. Yöneticiler korunur. /setwarnlimit 3; /setwarnmode ban; /setwarntime 1d. Yeni gruplar üç uyarı; eski ayarlar kalır. /approve yalnız normal içerik/akın korumasını atlar; federasyon/CAS/toplu katılma/elle işlem muafiyeti vermez. /promote isteyen ve botun ortak haklarını aşmaz. Toplu sıfırlama oluşturanı gerektirir.
gg-help-family-messages = <b>Mesajlar</b> · /del gerçek grup yanıtı ister. /purge oradan başlar; /purgefrom ve /purgeto sınırları kaydeder. Yapılandırılmış sınırlar ve Telegram kuralları geçerlidir; toplu onay kesin silme sayısı değildir. /pin [loud], /permapin, /unpin, /unpinall sabitleme hakkı ister; hepsini kaldırmak oluşturanı gerektirir. /antichannelpin ve /cleanlinked bağlı kanalın otomatik mesajlarını yönetir.
gg-help-family-logging = <b>Günlükler</b> · /setlog -100… güncel hedef yöneticiliği ve bot yayın hakkı ister. İletilen kurulum gerçekten alınmış asılla eşleşmelidir. /logcategories:settings/admin/user/automated/reports/other; /log ve /nolog kategorileri seçer. Teslim hataları görünür kalır ve işlem başarısını kanıtlamaz.
gg-help-family-settings = <b>Ayarlar</b> · /settings süreli kişisel panel açıp güncel bilgi değiştirme hakkını denetler. /setlang kod grup dilini; özel /lang kişisel dili kaydeder. /night 23 7 +3 gece kapatır; /night off yalnız kendi hâlâ eşleşen izin durumunu geri yükler. Dış değişiklikler önceliklidir.
gg-help-family-content = <b>Düzenleyici</b> · /save sözcük metin veya medyaya yanıt; /get sözcük, #sözcük, /notes notları okur. Yeni not adları tek sözcük; eski geniş adlar kalır. /filter "ifade" metin, /filterprefix, /filterexact eşleşmeyi seçer; /stop anahtarı kaldırır. /clearall ve /stopall oluşturan onayı ister. Rose biçimi:kalın/italik/altı çizili/üstü çizili/kod, bağlantı, alıntı ve rastgele %%% seçenekler. Alanlar:{ "{" }first{ "}" }, { "{" }last{ "}" }, { "{" }fullname{ "}" }, { "{" }username{ "}" }, { "{" }mention{ "}" }, { "{" }id{ "}" }, { "{" }chatname{ "}" }, { "{" }count{ "}" }. /button URL/not/kural düğmeleri oluşturur. Genel seçenekler preview/nonotif/protect/mediaspoiler; notlar admin/private/noprivate/repeat; filtreler user/allow_bot/replytag/command. /save sözcük Merhaba { "{" }repeat 5m{ "}" } yalnız herkese açık içeriği yazarın güncel haklarıyla zamanlar. Kurallar, karşılamalar ve özel içerik ortak gösterimi kullanır. Medya kimlikleri bota aittir.
gg-help-family-captcha = <b>Doğrulama</b> · /captcha on/off; /captchamode off/button/math/text/text2; /setcaptchatext; /captcharules on; /captchakick on/off; /captchakicktime ve /captchamutetime sınırlı süreler ayarlar. Verilen sorular nesil/süreyi tutar. İstekler invite-users; susturma restrict-members ister. Yanıtlar kişisel ve tek kullanımlıdır. Federasyon yasakları onay/CAPTCHA’dan öncedir.
gg-help-family-locks = <b>Kilitler</b> · /lock links [işlem], /unlock tür; /locktypes gerçek türleri, /locks durumu gösterir. /lockwarns uyarıları yönetir. /allowlist:alan adı/yol, tam davet, @sohbet veya stickerpack:/forward:/inline:/channel:/chat:/bot:/command:. Geçersiz kalıplar reddedilir. İstisnalar yalnız eşleşen içerik içindir; sessiz otomasyon oluşturan ve yetkili günlük ister.
gg-help-family-blocklists = <b>Yasak listesi</b> · /addblocklist "ifade" metin/önek/tam eşleşme ve belirtilen kimlikleri isteğe bağlı gerekçe/işlemle destekler. /rmblocklist tam seçilen anahtarları kaldırır. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute işlem seçer; geçici mod süre ister. /blocklistdelete silmeyi ayrı yönetir. Joker karmaşıklığı sınırlıdır; geçersiz kayıt ve aşım reddedilir.
gg-help-family-antispam = <b>Akın ve toplu katılma</b> · /setflood sayı ardışık mesaj sınırını; /setfloodtimer sayı süre zaman penceresini; /setfloodmode ceza/süreyi; /clearflood sıra temizliğini ayarlar. Eski ayarlar kalır. /flood ve /antiflood politikayı gösterir; takma ad yerel uyumluluk kararıdır. /antiraid on/off/duration, /raidtime, /raidactiontime, /autoantiraid dönem ve yeni katılanın ayrı cezasını tutar. Onay/CAPTCHA’dan önceliklidir; nesle bağlı bitiş yeniden başlatmaya dayanır.
gg-help-family-connections = <b>Bağlantılar</b> · /connect groupID veya kişisel bağlantı. Sizin ve botun üyeliği denetlenir; değişiklikler yine kesin güncel hakları ister. /connection seçimi gösterir; /disconnect kaldırır; /connect devamlı geçmişi gösterir. Bağlantı federasyon sahipliği veya işletici hakkı vermez.
gg-help-family-identity = <b>Bilgiler</b> · /id gerçek kullanıcı/sohbet/kaynak kimliklerini; /info güncel hedefi gösterir. Yanıtlar ve @adlar bu botun güncel kanıtını ister. Anonim grup mesajı insanı tanımlamaz; insan kimliği uydurulmaz.
gg-help-family-policy = <b>Politikalar</b> · /disable komut, /enable komut, /disabled, /disableable kanonik adları ve takma adları kullanır. /disableadmin yönetici istisnasını; /disabledel silmeyi yönetir. Kurtarma komutları erişilebilir kalır. /bot2bot off/admin/all gerçek üyeliği denetler; değişiklikler varsayılan olarak insan incelemesi ister. /bot2botskipreview yalnız oluşturan. /silentactions onay ve yetkili günlük ister. Tanımsız runs/saved açıklama döndürür.
gg-help-family-cleanup = <b>Temizlik</b> · /cleancommand admin/user/other ve /keepcommand komutları seçer. /cleanmsg action/filter/note ve /keepmsg yalnız bu botun gerçekten gönderdiği mesajlar içindir; alındılar ve beş dakikalık işler kimlik tahminini önler. /cleanservice ve /nocleanservice:join/leave/other/photo/pin/title/videochat. İşlevsel işlem ve geçerli ödemeler temizlikten öncedir.
gg-help-family-topics = <b>Konular</b> · /newtopic ad, /renametopic ad, /closetopic, /reopentopic gerçek güncel konuda çalışır. /deletetopic oluşturan onayı ister; /setactiontopic aynı grup hedefini seçer. Telegram forumu ve manage-topics gerekir. Eksik/desteklenmeyen konular gerçek hata verir.
gg-help-family-utilities = <b>Araçlar</b> · /echo ve /say doğrudan veya yanıtlanan içeriği ortak sınırlı gösterimle gönderir. /broadcast yalnız yapılandırılmış işletici veya gerçek alt sahip içindir; yalnız bu botun yapılandırılmış gruplarını kapsar. Hedef sonuçları kısmi/belirsiz teslimi tutar; durum ve iptal başarılı ekleri tekrarlamaz.
gg-help-family-federations = <b>Federasyonlar</b> · /newfed ad bu botta UUID oluşturur. Özel komutlar bağlantılardan bağımsız kendi federasyonunuzu kullanır; UUID okumak rol vermez. /fedpromote ve /feddemote yöneticileri yönetir; /feddemoteme görevden ayrılır. /joinfed UUID ve /leavefed güncel grubu oluşturanı ister. Silme Telegram yasaklarını kaldırmaz. /fban userID gerekçe ve /unfban userID federasyon sahibi/yöneticisi; /fedreason, /fednotif, /setfedlog sahip ister. /quietfed yalnız pasif açıklamaları gizler. /subfed UUID yönlü, sınırlı ve döngüsüzdür. /fedstat [userID], /fbanstat UUID kaynak/durumu gösterir. /fbanlist csv/minicsv/json yalnız sahip içindir, ortak 30 dakikalık aralık vardır; /importfbans sınırlı CSV veya gerçek satırlı JSON’u yanıtlar ve kendi JSON dizisini açıkça destekler. Yalnız gözlenen kullanıcılar denetlenir; tam üye envanteri iddia edilmez.
gg-help-family-portability = <b>Dosyalar ve gizlilik</b> · /export all veya modüller yönetici ister; /import ve /reset güncel insan oluşturanı kişisel, tek kullanımlık beş dakikalık onayla ister. Yerel beş dakikalık aralık; kendi sürümlü JSON’u, en fazla 2MiB ve yapılandırılmış içerik sınırları. Modüller:moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Seçilmeyen modüller kalır. Güven, verilen doğrulama/işler, abonelikler, roller ve etkin yasaklar içe aktarılmaz. /privacy policy/data/delete yalnız kendi özel sohbetinizde sayfalar ve asgari güvenlik saklamasıyla çalışır. Tam Rose dışa aktarımı için doğrulanmış bağdaştırıcı yok.
gg-help-family-discovery = <b>Yardım</b> · /help bölümleri gösterir; /help komut ad/takma ad arar; /help bölüm 2 devam eder. /button düğme işaretlemesine yardım eder. Rehber bağlamı, hakları, varsayılanları ve sınırları açıklar. /settings kişisel grup panelini açar.
gg-data-error-cache_pending = İsteğe bağlı SQL verileri kaldırıldı. Kullanılamayan önbelleğin temizliği sırada; etkin güvenlik kayıtları kalır.
