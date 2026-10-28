## Group Guard — Indonesian, independently authored.
group-welcome = 🛡 Terima kasih sudah menambahkan saya! Jadikan saya admin dengan izin hapus pesan, batasi anggota dan sematkan pesan. Gunakan /settings untuk mengatur perlindungan.
gg-start =
    🛡 Halo <b>{ $name }</b>! Saya <b>Group Guard</b>, pengelola keamanan grup.
    Verifikasi anggota baru, perlindungan banjir pesan dan CAS, kunci konten, daftar blokir, moderasi, catatan, filter, aturan dan sambutan tersedia. Tambahkan saya sebagai admin grup, lalu buka /settings atau /help.
gg-help = 📖 Gunakan /help untuk panduan kategori dan /help nama_perintah untuk pencarian. Moderasi: /ban /mute /kick /warn. Konten: /save /filter /rules. Perlindungan: /lock /blocklist /night. /settings membuka panel pribadi grup.
gg-welcome-default = 👋 Selamat datang { "{" }mention{ "}" } di <b>{ "{" }group{ "}" }</b>!
gg-credit = 🛡 Dilindungi oleh @{ $bot }
gg-btn-add = ➕ Tambahkan ke grup
gg-btn-commands = 📖 Perintah
gg-btn-rules = 📜 Aturan
gg-btn-human = ✅ Saya manusia
gg-btn-unwarn = ↩️ Hapus peringatan (admin)
gg-btn-locks = 🔒 Kunci ({ $count })
gg-btn-open-settings = ⚙️ Buka pengaturan
gg-btn-admin-tab = 🛡 Grup
gg-captcha = 🤖 { $user }, buktikan bahwa Anda manusia dalam <b>{ $minutes } menit</b> agar tidak dikeluarkan.
gg-captcha-button = Tekan tombol di bawah 👇
gg-captcha-math = Berapa <b>{ $a } + { $b }</b>?
gg-captcha-not-you = Tombol ini milik pengguna lain.
gg-captcha-ok = ✅ Selamat datang!
gg-captcha-wrong = ❌ Jawaban salah. Sisa percobaan: { $left }.
gg-captcha-failed = ❌ Terlalu banyak jawaban salah.
gg-captcha-passed = ✅ { $user } sudah terverifikasi. Selamat datang!
gg-cas-banned = 🚫 { $user } tercatat sebagai pengirim spam di CAS dan diblokir.
gg-join-request = 👋 Untuk bergabung dengan <b>{ $group }</b>, buktikan bahwa Anda manusia:
gg-join-approved = ✅ Permintaan bergabung disetujui. Selamat datang!
gg-join-expired = ⌛ Permintaan ini kedaluwarsa. Ajukan permintaan baru.
gg-goodbye = 👋 { $user } meninggalkan grup.
gg-flood-mute = 🌊 { $user } mengirim pesan beruntun terlalu cepat dan dibisukan sementara.
gg-flood-kick = 🌊 { $user } dikeluarkan karena banjir pesan.
gg-flood-ban = 🌊 { $user } diblokir karena banjir pesan.
gg-newbie-links = 🆕 { $user }, anggota baru belum boleh mengirim tautan selama { $hours } jam pertama.
gg-spam-banned = 🧠 { $user } diblokir karena mengirim spam.
gg-reason-blocklist = kata yang diblokir
gg-need-right = ⛔ Anda memerlukan izin admin “{ $right }”.
gg-right-admin = administrator
gg-right-restrict = membatasi anggota
gg-right-delete = menghapus pesan
gg-right-pin = menyematkan pesan
gg-right-change_info = mengubah informasi grup
gg-admins-only = ⛔ Khusus admin.
gg-need-target = 👤 Balas pesan atau berikan @nama pengguna yang terverifikasi atau ID pengguna.
gg-target-admin = 🙅 Admin tidak boleh menjadi sasaran tindakan ini.
gg-bot-no-rights = ⚠️ Saya memerlukan status admin dan izin yang sesuai.
gg-banned = 🔨 { $user } diblokir. Alasan: { $reason }
gg-banned-for = 🔨 { $user } diblokir selama { $time }. Alasan: { $reason }
gg-unbanned = ✅ Blokir { $user } dicabut.
gg-kicked = 👢 { $user } dikeluarkan. Alasan: { $reason }
gg-muted = 🔇 { $user } dibisukan. Alasan: { $reason }
gg-muted-for = 🔇 { $user } dibisukan selama { $time }. Alasan: { $reason }
gg-unmuted = 🔊 { $user } dapat mengirim pesan kembali.
gg-warned = ⚠️ { $user } mendapat peringatan ({ $count }/{ $limit }). Alasan: { $reason }
gg-warn-limit-ban = 🔨 { $user } mencapai { $limit } peringatan dan diblokir.
gg-warn-limit-mute = 🔇 { $user } mencapai { $limit } peringatan dan dibisukan.
gg-warn-limit-kick = 👢 { $user } mencapai { $limit } peringatan dan dikeluarkan.
gg-unwarned = ↩️ Satu peringatan { $user } dihapus ({ $count }/{ $limit }).
gg-warn-removed = ↩️ Peringatan dihapus oleh { $admin }.
gg-warns = ⚠️ { $user } memiliki { $count }/{ $limit } peringatan.
gg-warns-reset = 🧽 Peringatan { $user } direset.
gg-purge-reply = 🧹 Balas pesan pertama yang ingin dihapus.
gg-purged = 🧹 { $count } pesan dihapus.
gg-pin-reply = 📌 Balas pesan yang ingin disematkan.
gg-report-reply = 🚨 Balas pesan yang ingin dilaporkan.
gg-reported = 🚨 { $user } dilaporkan kepada admin.
gg-setlog-usage = 📒 Jadikan saya admin di kanal log, lalu gunakan <code>/setlog -100…</code> dengan ID kanal.
gg-setlog-failed = ⚠️ Saya tidak dapat mengirim pesan ke tujuan itu. Tambahkan saya sebagai admin terlebih dahulu.
gg-setlog-done = 📒 Kanal log terhubung.
gg-setlog-off = 📒 Kanal log dilepas.
gg-log-connected = 📒 Percakapan ini menerima log moderasi <b>{ $group }</b>.
gg-log-flood = 🌊 Banjir pesan: { $user } → { $action }
gg-log-report = 🚨 Laporan tentang { $user }
gg-log-spam = 🧠 Pemblokiran spam oleh AI: { $user }
    <blockquote>{ $text }</blockquote>
gg-rules = 📜 <b>Aturan</b>
    { $rules }
gg-no-rules = 📜 Belum ada aturan. Admin dapat memakai /setrules teks_aturan.
gg-rules-saved = 📜 Aturan disimpan.
gg-rules-cleared = 📜 Aturan dihapus.
gg-welcome-usage = 👋 Gunakan <code>/setwelcome Halo {"{"}mention{"}"}, selamat datang di {"{"}group{"}"}!</code> atau balas pesan.
gg-welcome-saved = 👋 Pesan sambutan disimpan.
gg-welcome-reset = 👋 Pesan sambutan dikembalikan ke bawaan.
gg-note-usage = 📝 Gunakan <code>/save nama teks</code> atau balas pesan dengan <code>/save nama</code>.
gg-filter-usage = 🔁 Gunakan <code>/filter kata teks_balasan</code> atau balas pesan dengan <code>/filter kata</code>.
gg-note-saved = 📝 Catatan disimpan dan dapat dibuka dengan <code>#{ $key }</code> sesuai izin aksesnya.
gg-filter-saved = 🔁 Saya akan membalas ketika “{ $key }” cocok.
gg-notes-empty = 📝 Belum ada catatan.
gg-filters-empty = 🔁 Belum ada filter.
gg-notes-list = 📝 <b>Catatan</b>
gg-filters-list = 🔁 <b>Filter</b>
gg-item-deleted = 🗑 “{ $key }” dihapus.
gg-item-missing = 🤷 Tidak ada konten tersimpan dengan nama itu.
gg-items-limit = 📦 Jumlah catatan dan filter grup ini sudah mencapai batas.
gg-lock-usage = 🔒 Gunakan <code>/lock links</code>. Jenis: { $types } atau <code>all</code>.
gg-locked = 🔒 Dikunci: { $types }
gg-unlocked = 🔓 Dibuka: { $types }
gg-locks-title = 🔒 <b>Kunci konten</b>
gg-locks-panel = 🔒 <b>Kunci konten</b> — konten yang dikunci dihapus; admin dikecualikan.
gg-blocklist = 🚫 <b>Kata diblokir</b>: { $words }
gg-blocklist-empty = 🚫 Daftar blokir kosong.
gg-blocklist-usage = 🚫 <code>/addblock kata, frasa lain</code> · <code>/rmblock kata</code>
gg-blocklist-saved = 🚫 Daftar blokir diperbarui ({ $count } entri).
gg-night-usage = 🌙 <code>/night 23 7 +3</code> menutup grup pukul 23:00–07:00 UTC+3; <code>/night off</code> menonaktifkan.
gg-night-on = 🌙 Mode malam: grup ditutup dari { $start } hingga { $end } ({ $tz }).
gg-night-off = 🌙 Mode malam dinonaktifkan.
gg-night-start = 🌙 Selamat malam! Grup ditutup hingga { $end }.
gg-night-end = ☀️ Selamat pagi! Grup dibuka kembali.
gg-panel = ⚙️ <b>Pengaturan — { $group }</b>
    Tekan pilihan untuk mengubahnya. Waktu mode malam: { $night }; ubah dengan /night.
gg-panel-sent = 📬 Pengaturan dikirim ke percakapan pribadi Anda.
gg-panel-start-first = 📬 Mulai percakapan pribadi dengan saya dahulu, lalu tekan tombol di bawah.
gg-credit-vip = 💎 Menyembunyikan tulisan perlindungan memerlukan VIP. Gunakan /vip di percakapan pribadi.
gg-opt-wel = 👋 Sambutan: { $value }
gg-opt-cln = 🧹 Hapus pesan bergabung: { $value }
gg-opt-bye = 👋 Perpisahan: { $value }
gg-opt-cap = 🤖 Verifikasi: { $value }
gg-opt-cpm = ⏱ Waktu verifikasi: { $value } menit
gg-opt-fld = 🌊 Batas banjir pesan: { $value }
gg-opt-fla = 🌊 Tindakan banjir pesan: { $value }
gg-opt-wrn = ⚠️ Batas peringatan: { $value }
gg-opt-wra = ⚠️ Tindakan peringatan: { $value }
gg-opt-act = ⏳ Bisukan/blokir otomatis: { $value } menit
gg-opt-cas = 🛡 Perlindungan CAS: { $value }
gg-opt-nwb = 🆕 Larangan tautan anggota baru: { $value } jam
gg-opt-ais = 🧠 Perlindungan spam AI: { $value }
gg-opt-ngt = 🌙 Mode malam: { $value }
gg-opt-crd = 🏷 Kredit perlindungan: { $value }
gg-opt-lang = 🌐 Bahasa: { $value }
gg-val-button = tombol
gg-val-math = hitungan
gg-val-off = nonaktif
gg-val-mute = bisukan
gg-val-kick = keluarkan
gg-val-ban = blokir
gg-adm = 🛡 <b>Group Guard</b>
    Grup dilindungi: <b>{ $groups }</b>; peringatan: <b>{ $warns }</b>; catatan dan filter: <b>{ $items }</b>.
cmd-settings = Pengaturan grup
cmd-help = Panduan perintah
gg-auth-denied = Otorisasi tidak dapat diverifikasi. Tidak ada perubahan.
gg-target-invalid = Pilih anggota manusia yang diketahui. Identitas sasaran belum terverifikasi.
gg-duration-invalid = Gunakan durasi 60s–365d. Perintah sementara wajib memiliki durasi.
gg-reason-invalid = Alasan maksimal 256 karakter.
gg-outcome-failed = Tindakan gagal atau tidak dapat diotorisasi.
gg-outcome-partial = Tindakan hanya selesai sebagian. Pemblokiran mungkin tetap berlaku jika pemulihan setelah pengeluaran gagal.
gg-outcome-ancillary = Tindakan utama selesai, tetapi langkah terkait gagal.
gg-review-request = Tinjau: <b>{ $operation }</b>
    Sasaran: { $target }
    Rincian: { $details }
    Durasi (detik): { $duration }
    Manusia dengan izin saat ini dapat menyetujui dalam 120 detik.
gg-review-approve = Setujui tindakan ini
gg-review-unavailable = Penyimpanan tinjauan tidak tersedia. Kirim perintah baru.
gg-review-expired = Tinjauan kedaluwarsa, tidak valid atau sudah digunakan.
gg-review-consumed = Tinjauan sudah digunakan. Periksa hasil tindakan; gunakan perintah baru untuk mencoba kembali.
gg-duration-permanent = Permanen / tanpa pengatur waktu
gg-purge-ack = Penghapusan diminta untuk { $requested } ID pesan; API mengakui { $acknowledged }. Jumlah pesan yang benar-benar terhapus tidak diketahui.
gg-warning-removed = Peringatan dihapus.
gg-review-details-above = Konten lengkap yang diminta ditampilkan tepat di atas.
gg-warn-pending = Peringatan dicatat; tindakan ambang batas sedang diproses.
gg-done = Selesai.
gg-setting-saved = Pengaturan { $setting } disimpan.
gg-setting-value = { $setting }: { $value }
gg-setting-invalid = Pengaturan tidak valid. Gunakan on/off, mode yang sah atau durasi seperti 10m.
gg-warning-settings = Peringatan: batas { $limit }; mode { $mode }; sanksi { $duration }; kedaluwarsa { $expiry }.
gg-admin-changed = Tindakan { $action } selesai untuk { $user }.
gg-admin-list = Admin publik:
    { $admins }
gg-approved = { $user } disetujui. Alasan: { $reason }
gg-unapproved = { $count } persetujuan dihapus.
gg-approval-status = Persetujuan { $user }: { $status }. Alasan: { $reason }
gg-approval-list = Pengguna disetujui:
    { $approvals }
gg-next-page = Entri berikutnya: { $command }
gg-range-invalid = Rentang tidak valid. Pilih 1–{ $cap } ID pesan.
gg-range-start = Titik awal disimpan untuk Anda di topik ini selama 10 menit. Balas pesan terakhir dengan /purgeto.
gg-range-missing = Belum ada titik awal di topik ini. Balas pesan awal dengan /purgefrom.
gg-content-needed = Berikan konten atau balas konten; maksimal 3500 karakter.
gg-log-status = Tujuan log: { $destination }. Kategori aktif: { $categories }.
gg-log-unverified = Tidak ada bukti penerimaan perintah kanal asli itu. Kirim /setlog di kanal terlebih dahulu.
gg-log-forward = Teruskan pesan /setlog asli ini ke grup. Admin penghubung harus memiliki izin ubah informasi di kedua percakapan.
gg-info = Nama: { $name }
    Nama pengguna: { $username }
    ID: <code>{ $id }</code>
    Keanggotaan: { $membership }
gg-unknown = Tidak diketahui
gg-chat-id = ID percakapan: <code>{ $id }</code>
gg-on = Aktif
gg-off = Nonaktif
gg-anon-enabled = Asumsi admin anonim diaktifkan untuk grup ini. Perintah anonim dari grup yang sama memakai izin bot tanpa mengenali manusianya. Tindakan khusus pemilik tetap membutuhkan pembuat terverifikasi. Gunakan /anonadmin off untuk kembali ke tinjauan manusia.
gg-right-invite_users = mengundang pengguna
gg-right-promote_members = mengangkat admin
gg-right-manage_topics = mengelola topik
gg-right-creator = pembuat grup
gg-log-join = { $user } bergabung.
gg-log-leave = { $user } keluar.
gg-warning-row = • #{ $id }: { $reason } (kedaluwarsa: { $expiry })
gg-menu-prompt = Pilih opsi.
gg-content-invalid = Konten tidak valid atau melewati batas Telegram. Periksa nama, format, pengubah dan tombol.
gg-content-unavailable = Konten tidak tersedia atau keanggotaan Anda saat ini tidak memberi akses.
gg-btn-private-note = Buka catatan
gg-open-private = Buka konten ini di percakapan pribadi:
gg-items-cleared = { $count } entri dihapus.
gg-clearall-confirm = Pembuat grup dapat mengonfirmasi dengan <code>/{ $command } confirm</code>.
gg-button-usage = Gunakan <code>/button "Label" https://example.com</code>. Tambahkan baris <code>"Catatan" #nama same</code> untuk tombol pada baris yang sama. Bot mengembalikan markup dan pratinjau yang berfungsi.
gg-btn-accept-rules = Terima aturan
gg-btn-open-verification = Buka verifikasi
gg-captcha-private = { $user }, buka tantangan pribadi untuk memverifikasi keanggotaan.
gg-captcha-choice = Cocokkan gambar dengan tombol. Mode: { $mode }; posisi karakter: { $position }.
gg-captcha-settings = Verifikasi: { $enabled }; mode: { $mode }; keluarkan: { $kick }; tenggat: { $seconds } detik; pelepasan bisu otomatis: { $release }.
gg-captcha-dependency = Aktifkan sambutan sebelum verifikasi. Simpan aturan sebelum mewajibkan persetujuan aturan.
gg-val-text = Gambar teks
gg-val-text2 = Gambar karakter
gg-captcha-attempts-exhausted = Verifikasi gagal karena terlalu banyak jawaban salah. Pembatasan kegagalan sudah diterapkan.
gg-captcha-admin-exempt = Anda kini admin grup. Tantangan verifikasi berakhir.
gg-captcha-question-text = Pilih kata yang terlihat pada gambar.
gg-captcha-question-math = Selesaikan persamaan pada gambar dan pilih jawabannya.
gg-captcha-question-text2 = Pilih karakter ke-{ $position } pada gambar, dihitung dari kiri ke kanan.
gg-locktypes = Jenis kunci tersedia: <code>{ $types }</code>
gg-allowlist-title = Pengecualian kunci
gg-allowlist-invalid = Pengecualian tidak valid. Gunakan domain/jalur, undangan persis, @grup atau identitas bertipe seperti stickerpack:nama.
gg-reason-lock = Konten dikunci: { $types }
gg-lock-applied = Kebijakan kunci { $types } diterapkan. Alasan: { $reason }
gg-reaction-failed = Penerapan kebijakan reaksi gagal: { $code }. Server Bot API ini mungkin belum mendukung penghapusan reaksi.
gg-reaction-anonymous = Pembaruan jumlah reaksi anonim tidak menyertakan identitas pengguna atau percakapan pelaku. API penghapusan memerlukannya; tidak ada klaim reaksi dihapus.
gg-none = Tidak ada
gg-blocklist-title = Daftar blokir
gg-blocklist-invalid = Pemicu, alasan atau tindakan tidak valid. Periksa frasa berpetik, escape wildcard dan durasi wajib untuk mode sementara.
gg-blocklist-settings = Mode daftar blokir: { $mode }; hapus pesan cocok: { $delete }.
gg-blocklist-action = Kebijakan daftar blokir diterapkan pada { $user }. Alasan: { $reason }
gg-flood-status = Banjir pesan: batas berturut-turut { $consecutive } (pada N); jendela { $count } / { $seconds } detik (melewati N). Tindakan { $mode }, { $duration }; seluruh rangkaian { $clear }.
gg-raid-status = Antiserbuan { $active }; hingga { $until }. Masa aktif { $period }; blokir { $ban }; ambang otomatis { $auto } anggota/menit. Mulai: /antiraid on · Hentikan: /antiraid off
gg-raid-banned = 🛡 { $user } diblokir sementara selama antiserbuan aktif.
gg-raid-declined = 🛡 Permintaan bergabung { $user } ditolak selama antiserbuan aktif.
gg-silent-consent-required = Pembuat grup harus menyetujui tindakan senyap dan mengatur log sebelum memilih tindakan ini.
gg-btn-enable-raid = Aktifkan antiserbuan
gg-human-required = Tindakan ini membutuhkan manusia yang dapat diidentifikasi.
gg-group-message-required = Jalankan perintah pada pesan atau topik grup sebenarnya; ID pesan pribadi tidak menunjuk pesan grup.
gg-connection-private = Gunakan perintah koneksi ini dalam percakapan pribadi kita.
gg-connection-disconnected = Koneksi dilepas. Lima grup terakhir tetap tersedia untuk dihubungkan kembali.
gg-connection-current = Terhubung ke <b>{ $group }</b>. Keanggotaan dan izin saat ini diperiksa untuk setiap tindakan.
gg-connection-none = Belum ada koneksi grup. Gunakan /connect GROUP_ID atau /connect @grup.
gg-connection-open = Buka koneksi pribadi Anda dalam percakapan pribadi kita.
gg-btn-connect = Hubungkan secara pribadi
gg-connection-history = Lima grup terakhir Anda. Pilih untuk terhubung kembali; keanggotaan saat ini wajib.
gg-connection-unavailable = Koneksi tidak tersedia. Anda harus menjadi anggota manusia saat ini dan bot harus admin di sana.
gg-catalog-unresolved = /{ $command } tercantum dalam katalog tanpa definisi tindakan. Gunakan /notes atau /flood untuk fitur yang sudah diterapkan.
gg-cleanup-failed = Pembersihan pesan gagal atau tidak tersedia; tidak ada klaim penghapusan.
gg-disabled-list = Perintah: <code>{ $commands }</code>. /disable NAMA dan /enable NAMA mengatur eksekusi; /disabledel mengatur penghapusan; /disableadmin mencakup admin.
gg-cleanup-types = Kategori pembersihan tersedia: { $types }
gg-cleanup-selected = Kategori pembersihan dipilih: { $types }
gg-advanced-status = { $setting }: { $value }. Tindakan otomatis senyap memerlukan persetujuan pembuat dan log. Perintah bot membutuhkan izin normal; tinjauan perubahan tetap aktif secara bawaan. Bot lain memerlukan visibilitas antarbots di BotFather.
gg-action-topic = Topik tindakan: { $topic }. Gunakan /setactiontopic di topik forum. Topik umum/bawaan adalah 1.
gg-topic-unavailable = Diperlukan grup forum saat ini dan izin kelola topik yang sesuai.
gg-topic-id-required = Dalam percakapan pribadi terhubung, berikan ID topik secara eksplisit.
gg-topic-general-delete = Topik umum tidak dapat dihapus. Konfirmasi penghapusan membutuhkan manusia yang diketahui identitasnya.
gg-topic-delete-confirm = Hapus topik { $topic } beserta pesannya? Konfirmasi bersifat pribadi dan berlaku dua menit.
gg-btn-confirm-delete = Konfirmasi penghapusan
gg-topic-changed = Tindakan topik { $action } selesai untuk { $topic }.
gg-broadcast-owner = Hanya operator bot yang dikonfigurasi atau pemilik anak pabrik sebenarnya yang dapat menyiarkan ke grup bot ini.
gg-broadcast-queued = Siaran grup { $id } diantrekan. Tujuan dan hasil pengiriman dipisahkan per bot.
gg-broadcast-busy = Siaran lain masih aktif atau jeda pembuatan lima menit belum berakhir.
gg-broadcast-empty = Anda tidak memiliki siaran grup di bot ini.
gg-broadcast-status = Siaran { $id }: { $status }. Antre: { $queued }; terkirim: { $sent }; gagal: { $failed }; tidak pasti: { $uncertain }; dibatalkan: { $cancelled }.
gg-fed-created = Federasi <b>{ $name }</b> dibuat. ID dalam bot ini: <code>{ $id }</code>.
gg-fed-info = <b>{ $name }</b>
    ID: <code>{ $id }</code>; pemilik: <code>{ $owner }</code>; admin: { $admins }.
    Alasan wajib: { $reasons }; notifikasi pemilik: { $notifications }; log: { $log }.
gg-fed-list = Federasi Anda sebagai pemilik atau admin:
    { $rows }
gg-fed-admins = Pemilik, diikuti admin federasi:
    { $rows }
gg-fed-quiet = Penjelasan pasif federasi senyap: { $value }. Penegakan tetap aktif.
gg-fed-policy = Alasan wajib: { $reasons }; notifikasi pemilik: { $notifications }.
gg-fed-confirm-delete = Hapus <b>{ $name }</b> (<code>{ $id }</code>)? Data dan keanggotaan federasi dihapus permanen. Blokir Telegram yang sudah berlaku tetap ada. Konfirmasi dalam lima menit.
gg-fed-confirm-log = Atur log <b>{ $name }</b> (<code>{ $id }</code>) ke <code>{ $destination }</code>? Konfirmasi dalam lima menit. Izin tujuan Anda dan izin kirim bot akan diperiksa lagi.
gg-fed-confirm-sent = Konfirmasi pribadi dikirim ke pemilik federasi.
gg-fed-deleted = Federasi dihapus. Blokir Telegram yang sudah berlaku tetap ada.
gg-fed-log-set = Tujuan log federasi: <code>{ $destination }</code>.
gg-fed-cancel = Batal
gg-fed-cancelled = Dibatalkan.
gg-fed-saved-delivery-failed = Perubahan federasi disimpan, tetapi notifikasi atau log gagal dikirim. Periksa tujuan dan akses bot.
gg-fed-error-authority = Tindakan memerlukan pemilik federasi saat ini atau peran federasi yang sesuai. Peran grup Telegram tidak memberi kewenangan federasi.
gg-fed-error-private = Gunakan perintah ini di percakapan pribadi Anda dengan bot ini.
gg-fed-error-group = Gunakan di grup sebenarnya. Koneksi pribadi tidak memilih grup federasi.
gg-fed-error-owned = Anda sudah memiliki federasi dalam bot ini. Gunakan /fedinfo, /renamefed atau /delfed secara pribadi.
gg-fed-error-name = Berikan nama yang tidak kosong tanpa karakter kendali. Nama dipotong hingga 64 karakter.
gg-fed-error-id = Berikan UUID federasi valid dari bot ini. ID jaringan Rose tidak dapat bergabung dengan layanan federasi terpisah ini.
gg-fed-error-missing = Tidak ditemukan federasi dalam bot atau konteks yang dipilih.
gg-fed-error-creator = Hanya pembuat grup Telegram saat ini dapat memasukkan atau mengeluarkan grup dari federasi.
gg-fed-error-target = Berikan ID manusia positif, balasan manusia atau nama pengguna yang terverifikasi saat ini. Pemilik tidak dapat diturunkan.
gg-fed-error-value = Argumen federasi tidak valid. Gunakan on/off untuk kebijakan dan ID federasi valid jika diperlukan.
gg-fed-error-stale = Konfirmasi kedaluwarsa, sudah digunakan atau keadaan federasi/pemilik/tujuan berubah. Minta konfirmasi baru.
gg-fed-error-destination = Pemilik federasi memerlukan izin admin saat ini di tujuan dan bot harus dapat mengirim di sana. Kanal memerlukan post_messages.
gg-fed-error-delivery = Konfirmasi pribadi gagal dikirim atau diikat. Buka percakapan pribadi dengan bot lalu coba lagi.
gg-fed-event = Federasi <b>{ $name }</b> (<code>{ $id }</code>): { $event }. Pelaku: <code>{ $user }</code>.
gg-fed-event-rename = nama diubah
gg-fed-event-delete = dihapus; blokir Telegram yang ada tetap berlaku
gg-fed-event-promote = admin ditambahkan
gg-fed-event-demote = admin dihapus
gg-fed-event-self-remove = admin mengundurkan diri
gg-fed-event-reason = kebijakan alasan blokir diubah
gg-fed-event-notif = kebijakan notifikasi pemilik diubah
gg-fed-event-log = tujuan log diubah
gg-fed-event-unlog = tujuan log dihapus
gg-fed-event-ban = kebijakan blokir disimpan; penegakan diantrekan
gg-fed-event-unban = kebijakan blokir dihapus; pelepasan milik bot diantrekan
gg-fed-event-subscribe = langganan blokir ditambahkan; pengguna teramati diantrekan untuk diperiksa
gg-fed-event-unsubscribe = langganan blokir dihapus; sumber lain dipertahankan
gg-fed-ban-details = Sasaran: <code>{ $user }</code>. Alasan: { $reason }
gg-fed-passive = Kebijakan federasi memblokir { $user }. Sumber: <b>{ $source }</b> (<code>{ $id }</code>). Alasan: { $reason }
gg-fed-enforce-failed = Federasi memblokir { $user }, tetapi pengeluaran gagal. Periksa izin bot. Sumber: <b>{ $source }</b> (<code>{ $id }</code>). Alasan: { $reason }
gg-fed-stat = Status blokir federasi <code>{ $user }</code>:
    { $rows }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — aktif: { $status }; perubahan terakhir: { $date }.
gg-fed-stat-more = Ada sumber lain. Gunakan perintah lanjutan atau ID federasi tertentu untuk alasan dan tanggalnya.
gg-fed-intent-saved = Kebijakan federasi untuk <code>{ $user }</code> disimpan (versi { $version }). Tujuan teramati diantrekan; izin terkini dan sumber pembatasan lain diperiksa sebelum tindakan.
gg-fed-subscriptions = Langganan langsung blokir federasi:
    { $rows }
gg-fed-imported = { $count } catatan blokir divalidasi dan disimpan; { $duplicates } duplikat identik diabaikan. Penegakan tujuan teramati diantrekan.
gg-fed-event-import = catatan blokir tervalidasi diimpor; penegakan diantrekan
gg-fed-error-file-format = Balas CSV UTF-8 dengan kolom id/reason, JSONL/NDJSON dengan user_id, atau ekspor larik JSON bot ini. Baris tidak valid membatalkan semua penulisan.
gg-fed-error-file-limit = Berkas blokir maksimal 2 MiB dan 1.000 catatan. Berkas terlalu besar atau hilang ditolak; daftar tidak dipotong diam-diam.
gg-fed-error-file-duplicate = Ada catatan bertentangan untuk ID pengguna yang sama. Tidak ada blokir diimpor.
gg-fed-error-file-rate = Ekspor dan impor blokir berbagi jeda 30 menit per federasi. Coba nanti.
gg-fed-error-reason = Alasan blokir maksimal 1.024 karakter tanpa karakter kendali yang tidak didukung.
gg-fed-error-reason_required = Federasi ini mewajibkan alasan tidak kosong untuk setiap blokir.
gg-fed-error-cycle = Federasi tidak boleh berlangganan dirinya sendiri atau membentuk siklus berarah.
gg-fed-error-graph_limit = Batas langganan tercapai: 32 tujuan langsung, 128 federasi terjangkau, kedalaman 16 atau 10.000 relasi dalam bot ini.
gg-data-confirm = <b>{ $operation }</b> · grup <code>{ $group }</code>
    Modul: { $modules }
    SHA-256 berkas: <code>{ $digest }</code>
    Konfirmasi dalam lima menit. Izin pembuat dan revisi grup diperiksa lagi. Hanya modul terpilih berubah; identitas, kepercayaan dan blokir aktif tetap ada.
gg-data-import = Impor modul grup
gg-data-reset = Reset modul grup
gg-data-privacy-delete = Hapus data pribadi opsional dalam bot ini
gg-data-confirm-button = Konfirmasi perubahan ini
gg-data-personal = Buka konfirmasi yang dikirim ke percakapan pribadi Anda.
gg-data-saved = Modul terpilih disimpan.
gg-data-error-authority = Impor dan reset memerlukan pembuat grup saat ini yang dapat diidentifikasi. Ekspor memerlukan admin saat ini.
gg-data-error-format = Balas dokumen JSON Group Guard berversi yang valid; buat dengan /export.
gg-data-error-limit = Berkas melebihi batas ukuran atau jumlah konten yang dikonfigurasi.
gg-data-error-version = Skema atau versi ini tidak didukung; tidak ada perubahan diterapkan.
gg-data-error-module = Pilih modul dikenal: /export all atau /export notes rules. Impor/reset memakai nama yang sama.
gg-data-error-field = Kolom modul tidak valid atau tidak lengkap; pengaturan tidak diterapkan.
gg-data-error-item = Konten, opsi atau akses pengulangan tidak valid; konten tidak disimpan.
gg-data-error-media = Media harus diunggah ke bot ini dan tersedia melalui getFile. ID berkas lintas bot tidak didukung.
gg-data-error-destination = Tujuan log/topik membutuhkan izin terkini dan kemampuan bot. ID topik hanya berlaku dalam grup yang sama.
gg-data-error-language = Pilih bahasa yang terpasang dengan /setlang.
gg-data-error-stale = Konfirmasi kedaluwarsa, berubah atau sudah digunakan. Mulai lagi.
gg-data-error-restore = Pembatasan sementara milik bot tidak dapat dipulihkan dengan aman. Buktinya tetap tersimpan; periksa izin bot sebelum mencoba lagi.
gg-data-error-rate = Operasi data grup memiliki jeda lokal lima menit. Coba nanti.
gg-data-error-delivery = Pengiriman konfirmasi pribadi gagal. Mulai percakapan pribadi dengan bot ini lalu coba lagi.
gg-data-error-saved_delivery = Pengaturan disimpan, tetapi saran perintah gagal diperbarui. Periksa izin bot.
gg-privacy-policy =
    <b>Data Anda dalam bot Group Guard ini</b>
    /privacy data mengekspor koneksi, profil teramati, peringatan, persetujuan, status pembatasan dan verifikasi, kepemilikan/peran/blokir federasi serta pekerjaan keamanan Anda. Konten pribadi orang lain, jawaban verifikasi, autentikasi dan unggahan mentah tidak disertakan. Ikuti perintah lanjutan untuk halaman berikutnya.
    /privacy delete menghapus riwayat koneksi opsional, nama/nama pengguna teramati, verifikasi tidak aktif dan konten kampanye pribadi yang selesai dalam bot ini. Peringatan/pembatasan aktif, versi blokir, peran, kepemilikan, hak berlangganan, bukti antiduplikasi dan pekerjaan API tak pasti mempertahankan pengenal minimum untuk keamanan dan urutan. Gunakan perintah pengunduran diri/penghapusan federasi secara eksplisit. Profil platform bersama dan data bot lain tetap ada.
    Operator mengelola cadangan dan audit secara terpisah. Perintah ini tidak menghapus pesan Telegram eksternal atau cadangan dan tidak mengklaim masa penyimpanan otomatis.
gg-privacy-usage = /privacy policy · /privacy data [lanjutan] · /privacy delete — hanya dalam percakapan pribadi Anda dengan bot ini.
gg-privacy-private = Tindakan ini memerlukan manusia peminta dalam percakapan pribadinya sendiri. Kursor tidak valid tidak dapat membuka data pengguna lain.
gg-privacy-next = Halaman data berikutnya: /privacy data { $cursor }
gg-privacy-deleted = Data pribadi opsional di bot ini dihapus. Keamanan aktif, kepemilikan dan pekerjaan tak pasti mempertahankan pengenal minimum; lihat /privacy policy.
gg-language-usage = Pilih bahasa grup: /setlang { $codes }. /lang dalam percakapan pribadi mengubah bahasa pribadi platform.
gg-language-saved = Bahasa balasan grup diperbarui.
gg-help-index =
    <b>Panduan perintah Group Guard</b>
    /help kategori · /help perintah · /help kategori 2. Perintah yang ditandai juga bekerja melalui /connect terverifikasi; balasan pribadi tetap memakai percakapan pribadi sebenarnya.
    Pengaturan memerlukan ubah informasi; sanksi batasi anggota; penghapusan hapus pesan; sematan sematkan pesan; promosi angkat admin; topik kelola topik. Izin bot diperiksa terpisah. Tindakan pemilik memerlukan pembuat manusia saat ini. /settings membuka panel pribadi grup.
gg-help-search = <b>Perintah yang cocok dengan { $query }</b>
gg-help-connected = Grup atau koneksi grup terverifikasi; izin dijelaskan dalam panduan kategori
gg-help-group-only = Memerlukan pesan grup sebenarnya
gg-help-unsupported = Nama katalog dipertahankan; perilaku tanpa sumber terkonfirmasi memberi penjelasan
gg-help-next = Halaman berikutnya
gg-help-previous = Halaman sebelumnya
gg-help-family-title-moderation = Moderasi dan persetujuan
gg-help-family-title-messages = Hapus dan sematkan pesan
gg-help-family-title-logging = Log berizin
gg-help-family-title-settings = Pengaturan dan bahasa grup
gg-help-family-title-content = Catatan, filter, aturan dan sambutan
gg-help-family-title-captcha = Verifikasi anggota baru
gg-help-family-title-locks = Kunci konten dan pengecualian
gg-help-family-title-blocklists = Pencocokan dan tindakan daftar blokir
gg-help-family-title-antispam = Perlindungan banjir pesan dan serbuan
gg-help-family-title-connections = Koneksi grup pribadi
gg-help-family-title-identity = Informasi pengguna dan percakapan
gg-help-family-title-policy = Kebijakan perintah dan bot
gg-help-family-title-cleanup = Pembersihan perintah, bot dan layanan
gg-help-family-title-topics = Topik forum
gg-help-family-title-utilities = Gema konten dan kampanye operator
gg-help-family-title-federations = Peran, blokir dan langganan federasi
gg-help-family-title-portability = Berkas grup dan data pribadi
gg-help-family-title-discovery = Bantuan dan editor konten
gg-help-family-moderation =
    <b>Moderasi</b> · Balas pesan, beri ID angka atau @nama pengguna dengan bukti terkini. /ban 20 alasan; /tban 20 60s alasan; /mute 20; /tmute 20 2h alasan. Sanksi sementara menerima 60 detik–365 hari. /kickme hanya mengeluarkan diri sendiri. Varian d juga menghapus balasan; varian s membersihkan pesan perintah/balasan dan perlu izin hapus. Admin aktif dilindungi.
    /setwarnlimit 3; /setwarnmode ban; /setwarntime 1d. Grup baru memakai tiga peringatan; bawaan grup lama dipertahankan. /approve hanya melewati perlindungan konten/banjir pesan biasa, bukan federasi/CAS/serbuan/tindakan manual. /promote membutuhkan izin promosi dan irisan izin pemanggil/bot; reset massal membutuhkan pembuat.
gg-help-family-messages =
    <b>Pesan</b> · /del memerlukan balasan pesan grup sebenarnya. /purge mulai dari balasan; /purgefrom dan /purgeto membekukan titik awal/akhir. Batas konfigurasi dan aturan Telegram berlaku; pengakuan batch bukan jumlah terhapus yang pasti.
    /pin [loud], /permapin, /unpin dan /unpinall memerlukan izin sematkan. Pelepasan massal membutuhkan pembuat. /antichannelpin dan /cleanlinked mengatur pesan otomatis kanal tertaut.
gg-help-family-logging =
    <b>Log</b> · /setlog -100… membutuhkan admin tujuan saat ini dan izin kirim bot. Penyiapan lewat terusan harus cocok dengan pesan asli yang benar-benar diterima bot. /logcategories menampilkan settings/admin/user/automated/reports/other; /log dan /nolog memilih kategori. Kegagalan pengiriman tetap terlihat dan tidak berarti tindakan selesai.
gg-help-family-settings =
    <b>Pengaturan</b> · /settings membuka panel pribadi kedaluwarsa dengan pemeriksaan izin ubah informasi. /setlang code menyimpan bahasa grup; /lang pribadi menyimpan bahasa personal. /night 23 7 +3 menutup grup semalaman; /night off memulihkan hanya cuplikan izin milik bot yang masih cocok. Perubahan izin eksternal menang.
gg-help-family-content =
    <b>Editor konten</b> · /save kata teks atau balas media; /get kata, #kata dan /notes membaca catatan. Pemicu catatan satu kata; nama lama yang lebih luas tetap dipertahankan. /filter "frasa berpetik" teks, /filterprefix dan /filterexact memilih pencocokan. /stop menghapus pemicu; /clearall dan /stopall membutuhkan konfirmasi pembuat.
    Markup Rose mendukung tebal/miring/garis bawah/coret/kode, tautan, kutipan dan pilihan acak %%%. Isian: { "{" }first{ "}" }, { "{" }last{ "}" }, { "{" }fullname{ "}" }, { "{" }username{ "}" }, { "{" }mention{ "}" }, { "{" }id{ "}" }, { "{" }chatname{ "}" }, { "{" }count{ "}" }. /button membuat markup tombol URL/catatan/aturan dengan pratinjau. Kontrol preview/nonotif/protect/mediaspoiler; catatan admin/private/noprivate/repeat; filter user/allow_bot/replytag/command. /save kata Halo { "{" }repeat 5m{ "}" } hanya menjadwalkan konten publik dengan izin penulis terkini. Aturan/sambutan/perpisahan dan konten pribadi memakai renderer sama; ID media terikat bot.
gg-help-family-captcha =
    <b>Verifikasi</b> · /captcha on/off; /captchamode off/button/math/text/text2; /setcaptchatext; /captcharules on; /captchakick on/off; /captchakicktime dan /captchamutetime memakai waktu terbatas. Tantangan yang diterbitkan mempertahankan generasi/tenggatnya. Permintaan bergabung perlu invite-users; pembisuan anggota perlu restrict-members. Jawaban bersifat pribadi dan sekali pakai. Blokir federasi diperiksa sebelum persetujuan dan verifikasi.
gg-help-family-locks =
    <b>Kunci</b> · /lock links [tindakan], /unlock jenis; /locktypes menampilkan jenis sebenarnya dan /locks status. /lockwarns mengatur peringatan. /allowlist menerima domain/jalur, undangan persis, @grup atau identitas stickerpack:/forward:/inline:/channel:/chat:/bot:/command:. Pola buruk ditolak. Pengecualian hanya berlaku untuk konten kunci yang cocok; tindakan senyap membutuhkan persetujuan pembuat dan log otomatis berizin.
gg-help-family-blocklists =
    <b>Daftar blokir</b> · /addblocklist "frasa" menerima teks/bawalan/persis serta jenis identitas yang dinyatakan, dengan alasan/tindakan opsional. /rmblocklist menghapus kunci terpilih secara tepat. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute menentukan tindakan; mode sementara wajib memakai durasi. /blocklistdelete mengatur hapus pesan terpisah. Wildcard dibatasi; pola buruk dan jumlah di atas batas ditolak.
gg-help-family-antispam =
    <b>Banjir pesan dan serbuan</b> · /setflood jumlah untuk pesan berturut-turut; /setfloodtimer jumlah durasi untuk jendela waktu; /setfloodmode untuk sanksi/durasi dan /clearflood untuk penghapusan. Bawaan lama tetap ada. /flood dan /antiflood menampilkan kebijakan; aliasnya adalah keputusan kompatibilitas lokal.
    /antiraid on/off/duration, /raidtime, /raidactiontime dan /autoantiraid mengatur tenggat tersimpan dan sanksi pendatang terpisah. Serbuan mendahului persetujuan/verifikasi; kedaluwarsa terikat generasi dan aman setelah mulai ulang.
gg-help-family-connections =
    <b>Koneksi</b> · Gunakan /connect groupID atau tautan pribadi. Keanggotaan Anda/bot diperiksa kembali; perubahan tetap membutuhkan izin tepat terkini. /connection menampilkan pilihan; /disconnect melepas; /connect menampilkan riwayat dengan lanjutan. Koneksi tidak memberi kepemilikan federasi atau kewenangan operator platform.
gg-help-family-identity =
    <b>Informasi</b> · /id menampilkan ID pengguna/percakapan/sumber sebenarnya; /info untuk sasaran saat ini. Balasan dan @nama pengguna membutuhkan bukti terkini dalam cakupan. Pesan grup anonim tidak mengenali manusia asal; ID manusia tidak direkayasa.
gg-help-family-policy =
    <b>Kebijakan</b> · /disable perintah, /enable perintah, /disabled dan /disableable mencakup nama kanonis dan alias. /disableadmin mengatur pengecualian admin; /disabledel penghapusan perintah nonaktif. Perintah pemulihan tetap tersedia. /bot2bot off/admin/all memeriksa keanggotaan bot; perubahan biasanya perlu tinjauan manusia, /bot2botskipreview khusus pembuat. /silentactions perlu persetujuan pembuat dan log otomatis berizin. runs/saved tanpa definisi sumber memberi penjelasan.
gg-help-family-cleanup =
    <b>Pembersihan</b> · /cleancommand admin/user/other dan /keepcommand memilih perintah. /cleanmsg action/filter/note dan /keepmsg memilih hanya pesan bot ini yang benar-benar terkirim; bukti penerimaan dan tugas lima menit mencegah tebak ID. /cleanservice dan /nocleanservice memilih join/leave/other/photo/pin/title/videochat. Pemrosesan fungsional dan pembayaran valid berlangsung sebelum pembersihan.
gg-help-family-topics =
    <b>Topik</b> · /newtopic nama, /renametopic nama, /closetopic dan /reopentopic memakai utas forum sebenarnya. /deletetopic memerlukan konfirmasi pembuat; /setactiontopic menyimpan tujuan dalam grup yang sama. Forum Telegram dan manage-topics wajib. Kegagalan kirim pada topik hilang/tidak didukung dilaporkan apa adanya.
gg-help-family-utilities =
    <b>Alat</b> · /echo atau /say merender teks/media langsung atau balasan dengan renderer bersama yang terbatas. /broadcast hanya untuk operator bot yang dikonfigurasi atau pemilik anak pabrik sebenarnya; tujuan hanya grup bot ini yang dikonfigurasi. Hasil per tujuan mempertahankan pengiriman parsial/tak pasti; status/batal tidak mengulang lampiran sukses.
gg-help-family-federations =
    <b>Federasi</b> · /newfed nama membuat UUID dalam bot ini. Perintah pribadi memilih federasi milik Anda tanpa bergantung koneksi; pembacaan UUID tidak memberi peran. /fedpromote dan /feddemote mengatur admin; /feddemoteme mengundurkan diri. /joinfed UUID dan /leavefed perlu pembuat grup saat ini. Hapus federasi tidak otomatis mencabut blokir Telegram.
    /fban userID alasan dan /unfban userID perlu pemilik/admin federasi. /fedreason, /fednotif, /setfedlog khusus pemilik. /quietfed hanya menyembunyikan pemberitahuan pasif. /subfed UUID berarah, terbatas dan tanpa siklus. /fedstat [userID], /fbanstat UUID menampilkan status/sumber. /fbanlist csv/minicsv/json khusus pemilik dengan jeda bersama 30 menit; /importfbans membalas CSV atau JSON per baris terbatas serta mendukung larik JSON ekspor sendiri. Rekonsiliasi hanya pengguna yang benar-benar teramati, bukan inventaris seluruh anggota.
gg-help-family-portability =
    <b>Berkas grup dan privasi</b> · /export all atau nama modul membutuhkan admin; /import dan /reset membutuhkan pembuat manusia saat ini dengan konfirmasi pribadi lima menit sekali pakai. Jeda grup lokal lima menit; JSON berversi sendiri maksimal 2MiB dan batas konten konfigurasi. Modul: moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Modul yang tidak dipilih tetap ada. Kepercayaan, tantangan/tugas aktif, hak langganan, peran dan blokir aktif tidak diimpor.
    /privacy policy/data/delete hanya di percakapan pribadi sendiri, dengan lanjutan data dan retensi keamanan minimum. Ini bukan adaptor ekspor lengkap Rose yang terverifikasi.
gg-help-family-discovery =
    <b>Bantuan</b> · /help menampilkan kategori; /help perintah mencari nama/alias; /help kategori 2 melanjutkan. /button membantu markup tombol. Panduan menjelaskan konteks, izin, bawaan dan batas penyebaran. /settings membuka panel pribadi grup.
gg-lock-album = Album
gg-lock-anonchannel = Pengirim kanal
gg-lock-audio = Audio
gg-lock-bot = Bot
gg-lock-button = Tombol sebaris
gg-lock-cashtag = Tag mata uang
gg-lock-checklist = Daftar periksa
gg-lock-cjk = Teks Tionghoa/Jepang/Korea
gg-lock-command = Perintah
gg-lock-comment = Komentar nonanggota
gg-lock-contact = Kontak
gg-lock-cyrillic = Teks Kiril
gg-lock-document = Dokumen
gg-lock-email = Alamat surel
gg-lock-emoji = Emoji
gg-lock-emojicustom = Emoji khusus
gg-lock-emojigame = Permainan emoji
gg-lock-emojionly = Hanya emoji
gg-lock-externalreply = Balasan eksternal
gg-lock-forward = Pesan terusan
gg-lock-forwarduser = Terusan pengguna
gg-lock-forwardbot = Terusan bot
gg-lock-forwardchannel = Terusan kanal
gg-lock-forwardstory = Cerita terusan
gg-lock-game = Permainan
gg-lock-gif = Animasi GIF
gg-lock-guestbot = Bot tamu
gg-lock-inline = Bot sebaris
gg-lock-invitelink = Undangan Telegram
gg-lock-botlink = Tautan bot
gg-lock-location = Lokasi
gg-lock-outsidereaction = Reaksi nonanggota
gg-lock-phone = Nomor telepon
gg-lock-photo = Foto
gg-lock-poll = Jajak pendapat
gg-lock-reaction = Reaksi
gg-lock-rtl = Teks kanan ke kiri
gg-lock-spoiler = Konten tersembunyi
gg-lock-sticker = Stiker
gg-lock-stickeranimated = Stiker bergerak
gg-lock-stickerpremium = Stiker premium
gg-lock-text = Teks
gg-lock-url = URL
gg-lock-video = Video
gg-lock-videonote = Pesan video
gg-lock-links = Tautan
gg-lock-invites = Tautan undangan
gg-lock-forwards = Terusan
gg-lock-media = Media
gg-lock-stickers = Stiker
gg-lock-gifs = GIF
gg-lock-voice = Pesan suara
gg-lock-polls = Jajak pendapat
gg-lock-bots = Bot
gg-op-ban = blokir
gg-op-mute = bisukan
gg-op-kick = keluarkan
gg-op-unban = cabut blokir
gg-op-unmute = cabut pembisuan
gg-op-warn = beri peringatan
gg-op-unwarn = hapus satu peringatan
gg-op-resetwarns = reset peringatan
gg-op-purge = bersihkan rentang pesan
gg-op-delete = hapus pesan
gg-op-pin = sematkan pesan
gg-op-unpin = lepas sematan
gg-op-setlog = atur tujuan log
gg-op-unsetlog = lepas tujuan log
gg-op-config = ubah pengaturan
gg-op-save = simpan konten
gg-op-remove = hapus konten
gg-op-panel = buka panel
gg-op-unpinall = lepas semua sematan
gg-op-permapin = sematkan permanen
gg-op-promote = angkat administrator
gg-op-demote = turunkan administrator
gg-op-approve_user = setujui pengguna
gg-op-unapprove = cabut persetujuan
gg-op-unapproveall = cabut seluruh persetujuan
gg-op-lock_change = ubah kebijakan kunci
gg-op-allowlist_change = ubah pengecualian kunci
gg-op-allowlist_clear = hapus seluruh pengecualian kunci
gg-op-blocklist_change = ubah entri daftar blokir
gg-op-blocklist_clear = hapus seluruh daftar blokir
gg-op-raid_change = ubah aktivasi antiserbuan
gg-op-policy_change = ubah kebijakan perintah atau pembersihan
gg-op-topic_create = buat topik forum
gg-op-topic_rename = ubah nama topik
gg-op-topic_close = tutup topik
gg-op-topic_reopen = buka ulang topik
gg-op-topic_delete = hapus topik dan pesannya
gg-op-echo = kirim konten berformat
gg-data-error-cache_pending = Data SQL opsional dihapus; penghapusan cache diantrekan karena cache tidak tersedia. Catatan keamanan aktif tetap ada.
