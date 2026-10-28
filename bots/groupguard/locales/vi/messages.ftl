## Independently authored Group Guard vi content.
group-welcome = 🛡 Cảm ơn đã thêm tôi! Cấp quyền quản trị để xóa tin nhắn, hạn chế thành viên và ghim tin. Cấu hình bằng /settings.
gg-start = 🛡 Xin chào <b>{ $name }</b>! Tôi là <b>Group Guard</b>: xác minh thành viên mới, chống dồn tin và CAS, khóa nội dung, quản lý, ghi chú, bộ lọc, quy tắc và chào mừng. Thêm tôi làm quản trị viên rồi dùng /settings hoặc /help.
gg-help = 📖 /help hiển thị các mục; /help lệnh tìm lệnh. Quản lý: /ban /mute /kick /warn. Nội dung: /save /filter /rules. Bảo vệ: /lock /blocklist /night. /settings mở bảng nhóm cá nhân.
gg-welcome-default = 👋 Chào mừng { "{" }mention{ "}" } đến <b>{ "{" }group{ "}" }</b>!
gg-credit = 🛡 Được bảo vệ bởi @{ $bot }
gg-btn-add = ➕ Thêm vào nhóm
gg-btn-commands = 📖 Lệnh
gg-btn-rules = 📜 Quy tắc
gg-btn-human = ✅ Tôi là người
gg-btn-unwarn = ↩️ Xóa cảnh báo (quản trị viên)
gg-btn-locks = 🔒 Khóa nội dung · số lượng: { $count }
gg-btn-open-settings = ⚙️ Mở cài đặt
gg-btn-admin-tab = 🛡 Nhóm
gg-captcha = 🤖 Xác minh bạn là người trong thời hạn hiển thị, nếu không bạn sẽ bị loại.
    phút: { $minutes }
    thành viên: { $user }
gg-captcha-button = Nhấn nút bên dưới 👇
gg-captcha-math = <b>{ $a } + { $b }</b> bằng bao nhiêu?
gg-captcha-not-you = Nút này dành cho người khác.
gg-captcha-ok = ✅ Chào mừng!
gg-captcha-wrong = ❌ Sai đáp án. Thử lại nếu còn lượt.
    lượt còn lại: { $left }
gg-captcha-failed = ❌ Quá nhiều đáp án sai.
gg-captcha-passed = ✅ Xác minh thành công. Chào mừng!
    thành viên: { $user }
gg-cas-banned = 🚫 CAS nhận diện thành viên là người gửi rác; đã cấm.
    thành viên: { $user }
gg-join-request = 👋 Xác minh bạn là người để vào nhóm:
    nhóm: { $group }
gg-join-approved = ✅ Yêu cầu được duyệt. Chào mừng!
gg-join-expired = ⌛ Yêu cầu hết hạn. Gửi yêu cầu vào nhóm mới.
gg-goodbye = 👋 Thành viên đã rời nhóm.
    thành viên: { $user }
gg-flood-mute = 🌊 Thành viên bị hạn chế viết tạm thời vì quá nhiều tin.
    thành viên: { $user }
gg-flood-kick = 🌊 Thành viên bị loại vì quá nhiều tin.
    thành viên: { $user }
gg-flood-ban = 🌊 Thành viên bị cấm vì quá nhiều tin.
    thành viên: { $user }
gg-newbie-links = 🆕 Thành viên mới không được gửi liên kết trong các giờ đầu được chỉ định.
    giờ: { $hours }
    thành viên: { $user }
gg-spam-banned = 🧠 Thành viên bị cấm vì tin rác.
    thành viên: { $user }
gg-reason-blocklist = từ bị cấm
gg-need-right = ⛔ Cần quyền quản trị tương ứng.
    quyền: { $right }
gg-right-admin = quản trị viên
gg-right-restrict = hạn chế thành viên
gg-right-delete = xóa tin nhắn
gg-right-pin = ghim tin nhắn
gg-right-change_info = đổi thông tin nhóm
gg-admins-only = ⛔ Chỉ dành cho quản trị viên.
gg-need-target = 👤 Trả lời tin nhắn hoặc nhập ID hay @tên người dùng đã được xác minh hiện tại.
gg-target-admin = 🙅 Thao tác này không được nhắm vào quản trị viên.
gg-bot-no-rights = ⚠️ Tôi cần làm quản trị viên với quyền cần thiết.
gg-banned = 🔨 Thành viên đã bị cấm.
    lý do: { $reason }
    thành viên: { $user }
gg-banned-for = 🔨 Thành viên bị cấm trong thời hạn chỉ định.
    lý do: { $reason }
    thời gian: { $time }
    thành viên: { $user }
gg-unbanned = ✅ Đã gỡ cấm thành viên.
    thành viên: { $user }
gg-kicked = 👢 Thành viên bị loại và có thể vào lại.
    lý do: { $reason }
    thành viên: { $user }
gg-muted = 🔇 Thành viên bị hạn chế viết.
    lý do: { $reason }
    thành viên: { $user }
gg-muted-for = 🔇 Thành viên bị hạn chế viết trong thời hạn chỉ định.
    lý do: { $reason }
    thời gian: { $time }
    thành viên: { $user }
gg-unmuted = 🔊 Thành viên có thể viết lại.
    thành viên: { $user }
gg-warned = ⚠️ Cảnh báo thành viên đã được ghi.
    số lượng: { $count }
    ngưỡng: { $limit }
    lý do: { $reason }
    thành viên: { $user }
gg-warn-limit-ban = 🔨 Đạt ngưỡng cảnh báo; thành viên bị cấm.
    ngưỡng: { $limit }
    thành viên: { $user }
gg-warn-limit-mute = 🔇 Đạt ngưỡng cảnh báo; thành viên bị hạn chế viết.
    ngưỡng: { $limit }
    thành viên: { $user }
gg-warn-limit-kick = 👢 Đạt ngưỡng cảnh báo; thành viên bị loại.
    ngưỡng: { $limit }
    thành viên: { $user }
gg-unwarned = ↩️ Đã xóa một cảnh báo của thành viên.
    số lượng: { $count }
    ngưỡng: { $limit }
    thành viên: { $user }
gg-warn-removed = ↩️ Quản trị viên đã xóa cảnh báo.
    quản trị viên: { $admin }
gg-warns = ⚠️ Cảnh báo của thành viên:
    số lượng: { $count }
    ngưỡng: { $limit }
    thành viên: { $user }
gg-warns-reset = 🧽 Đã đặt lại cảnh báo của thành viên.
    thành viên: { $user }
gg-purge-reply = 🧹 Trả lời tin đầu tiên cần xóa.
gg-purged = 🧹 Tin nhắn đã được xóa.
    số lượng: { $count }
gg-pin-reply = 📌 Trả lời tin cần ghim.
gg-report-reply = 🚨 Trả lời tin cần báo cáo.
gg-reported = 🚨 Đã báo thành viên tới quản trị viên.
    thành viên: { $user }
gg-setlog-usage = 📒 Thêm tôi làm quản trị kênh nhật ký và dùng <code>/setlog -100…</code> với ID kênh.
gg-setlog-failed = ⚠️ Tôi không thể gửi ở đó. Thêm tôi làm quản trị viên trước.
gg-setlog-done = 📒 Đã kết nối kênh nhật ký.
gg-setlog-off = 📒 Đã ngắt kênh nhật ký.
gg-log-connected = 📒 Cuộc trò chuyện này nhận nhật ký quản lý nhóm.
    nhóm: { $group }
gg-log-flood = 🌊 Phát hiện dồn tin:
    thao tác: { $action }
    thành viên: { $user }
gg-log-report = 🚨 Báo cáo về thành viên:
    thành viên: { $user }
gg-log-spam = 🧠 Cấm do tin rác được AI phát hiện:
    văn bản: { $text }
    thành viên: { $user }
gg-rules = 📜 <b>Quy tắc</b>
    { $rules }
gg-no-rules = 📜 Chưa có quy tắc. Quản trị viên có thể dùng /setrules văn_bản.
gg-rules-saved = 📜 Đã lưu quy tắc.
gg-rules-cleared = 📜 Đã xóa quy tắc.
gg-welcome-usage = 👋 Dùng <code>/setwelcome Xin chào {"{"}mention{"}"}, chào mừng đến {"{"}group{"}"}!</code> hoặc trả lời tin nhắn.
gg-welcome-saved = 👋 Đã lưu lời chào.
gg-welcome-reset = 👋 Đã khôi phục lời chào mặc định.
gg-note-usage = 📝 <code>/save tên văn_bản</code> hoặc trả lời bằng <code>/save tên</code>.
gg-filter-usage = 🔁 <code>/filter từ câu_trả_lời</code> hoặc trả lời bằng <code>/filter từ</code>.
gg-note-saved = 📝 Đã lưu ghi chú. Đọc bằng <code>#{ $key }</code> theo quyền truy cập.
gg-filter-saved = 🔁 Tôi sẽ trả lời khi khớp “{ $key }”.
gg-notes-empty = 📝 Chưa có ghi chú.
gg-filters-empty = 🔁 Chưa có bộ lọc.
gg-notes-list = 📝 <b>Ghi chú</b>
gg-filters-list = 🔁 <b>Bộ lọc</b>
gg-item-deleted = 🗑 Đã xóa mục.
    khóa: { $key }
gg-item-missing = 🤷 Không có nội dung lưu với tên này.
gg-items-limit = 📦 Đạt giới hạn ghi chú và bộ lọc của nhóm.
gg-lock-usage = 🔒 Dùng <code>/lock links</code>. Các loại ở dưới; <code>all</code> chọn tất cả.
    loại: { $types }
gg-locked = 🔒 Nội dung bị khóa:
    loại: { $types }
gg-unlocked = 🔓 Nội dung được phép:
    loại: { $types }
gg-locks-title = 🔒 <b>Khóa nội dung</b>
gg-locks-panel = 🔒 <b>Khóa</b>: nội dung bị khóa sẽ bị xóa; quản trị viên được miễn.
gg-lock-links = liên kết
gg-lock-invites = liên kết mời
gg-lock-forwards = chuyển tiếp
gg-lock-media = media
gg-lock-stickers = nhãn dán
gg-lock-gifs = GIF
gg-lock-voice = tin thoại
gg-lock-polls = bình chọn
gg-lock-bots = bot
gg-blocklist = 🚫 <b>Từ bị cấm</b>
    từ: { $words }
gg-blocklist-empty = 🚫 Không có từ bị cấm.
gg-blocklist-usage = 🚫 <code>/addblock từ, cụm khác</code> · <code>/rmblock từ</code>
gg-blocklist-saved = 🚫 Đã cập nhật danh sách cấm.
    số lượng: { $count }
gg-night-usage = 🌙 <code>/night 23 7 +3</code> đóng từ23:00 đến07:00 UTC+3; <code>/night off</code> tắt.
gg-night-on = 🌙 Đã đặt giờ đêm cho nhóm.
    kết thúc: { $end }
    bắt đầu: { $start }
    múi giờ: { $tz }
gg-night-off = 🌙 Đã tắt chế độ đêm.
gg-night-start = 🌙 Chúc ngủ ngon! Nhóm đóng đến giờ chỉ định.
    kết thúc: { $end }
gg-night-end = ☀️ Chào buổi sáng! Nhóm mở lại.
gg-panel = ⚙️ <b>Cài đặt nhóm</b>
    Nhấn lựa chọn để đổi. Đặt giờ đêm bằng /night.
    nhóm: { $group }
    giờ đêm: { $night }
gg-panel-sent = 📬 Đã gửi cài đặt vào riêng tư.
gg-panel-start-first = 📬 Mở trò chuyện riêng với tôi trước, rồi nhấn bên dưới.
gg-credit-vip = 💎 Cần VIP để ẩn dòng bảo vệ. Dùng /vip trong riêng tư.
gg-opt-wel = 👋 Chào mừng · giá trị: { $value }
gg-opt-cln = 🧹 Xóa tin vào nhóm · giá trị: { $value }
gg-opt-bye = 👋 Tạm biệt · giá trị: { $value }
gg-opt-cap = 🤖 Xác minh · giá trị: { $value }
gg-opt-cpm = ⏱ Hạn xác minh, phút · giá trị: { $value }
gg-opt-fld = 🌊 Ngưỡng tin nhắn · giá trị: { $value }
gg-opt-fla = 🌊 Xử lý dồn tin · giá trị: { $value }
gg-opt-wrn = ⚠️ Ngưỡng cảnh báo · giá trị: { $value }
gg-opt-wra = ⚠️ Xử lý cảnh báo · giá trị: { $value }
gg-opt-act = ⏳ Hạn chế tự động, phút · giá trị: { $value }
gg-opt-cas = 🛡 Bảo vệ CAS · giá trị: { $value }
gg-opt-nwb = 🆕 Thành viên mới không liên kết, giờ · giá trị: { $value }
gg-opt-ais = 🧠 Bảo vệ tin rác bằng AI · giá trị: { $value }
gg-opt-ngt = 🌙 Chế độ đêm · giá trị: { $value }
gg-opt-crd = 🏷 Dòng bảo vệ · giá trị: { $value }
gg-opt-lang = 🌐 Ngôn ngữ · giá trị: { $value }
gg-val-button = Nút
gg-val-math = Phép tính
gg-val-off = tắt
gg-val-mute = hạn chế viết
gg-val-kick = loại
gg-val-ban = cấm
gg-adm = 🛡 <b>Group Guard: thống kê</b>
    nhóm: { $groups }
    bản ghi: { $items }
    cảnh báo: { $warns }
cmd-settings = Cài đặt nhóm
cmd-help = Hướng dẫn lệnh
gg-auth-denied = Không xác minh được quyền. Không có thay đổi.
gg-target-invalid = Chọn thành viên người đã biết. Không xác minh được mục tiêu.
gg-duration-invalid = Dùng thời hạn60s–365d. Lệnh tạm thời cần thời hạn.
gg-reason-invalid = Lý do tối đa256 ký tự.
gg-outcome-failed = Thao tác thất bại hoặc không được phép.
gg-outcome-partial = Thao tác chỉ hoàn thành một phần. Lệnh cấm có thể còn nếu khôi phục sau khi loại thất bại.
gg-outcome-ancillary = Thao tác chính hoàn thành nhưng bước phụ thất bại.
gg-review-request = Xem thao tác bất biến bên dưới. Người đang có quyền có thể duyệt trong120 giây. Thời hạn được ghi bằng giây.
    chi tiết: { $details }
    thời hạn: { $duration }
    thao tác: { $operation }
    đối tượng: { $target }
gg-review-approve = Duyệt thao tác này
gg-review-unavailable = Kho xác nhận không khả dụng. Gửi lệnh mới.
gg-review-expired = Xác nhận hết hạn, không hợp lệ hoặc đã dùng.
gg-review-consumed = Xác nhận đã dùng. Kiểm tra kết quả; cần lệnh mới để thử lại.
gg-duration-permanent = Vĩnh viễn / không thời hạn
gg-purge-ack = API xác nhận yêu cầu xóa. Không biết số thực sự đã xóa.
    API đã xác nhận: { $acknowledged }
    đã yêu cầu: { $requested }
gg-warning-removed = Đã xóa cảnh báo.
gg-op-ban = cấm
gg-op-mute = hạn chế viết
gg-op-kick = loại
gg-op-unban = gỡ cấm
gg-op-unmute = gỡ hạn chế viết
gg-op-warn = cảnh báo
gg-op-unwarn = xóa cảnh báo
gg-op-resetwarns = đặt lại cảnh báo
gg-op-purge = xóa dải tin
gg-op-delete = xóa tin
gg-op-pin = ghim tin
gg-op-unpin = bỏ ghim
gg-op-setlog = đặt nhật ký
gg-op-unsetlog = bỏ nhật ký
gg-op-config = đổi cài đặt
gg-op-save = lưu nội dung
gg-op-remove = bỏ nội dung
gg-op-panel = mở bảng
gg-review-details-above = Toàn bộ nội dung yêu cầu nằm ở tin ngay phía trên.
gg-warn-pending = Đã lưu cảnh báo; thao tác ngưỡng đang được xử lý.
gg-done = Hoàn thành.
gg-setting-saved = Đã lưu cài đặt.
    cài đặt: { $setting }
gg-setting-value = Giá trị cài đặt hiện tại:
    cài đặt: { $setting }
    giá trị: { $value }
gg-setting-invalid = Cài đặt không hợp lệ. Dùng on/off, chế độ hợp lệ hoặc thời hạn như10m.
gg-warning-settings = Cài đặt cảnh báo:
    thời hạn: { $duration }
    hết hạn: { $expiry }
    ngưỡng: { $limit }
    chế độ: { $mode }
gg-admin-changed = Đã hoàn thành thao tác quản trị.
    thao tác: { $action }
    thành viên: { $user }
gg-admin-list = Quản trị viên công khai:
    { $admins }
gg-approved = Đã duyệt thành viên.
    lý do: { $reason }
    thành viên: { $user }
gg-unapproved = Đã xóa các phê duyệt.
    số lượng: { $count }
gg-approval-status = Trạng thái duyệt thành viên:
    lý do: { $reason }
    trạng thái: { $status }
    thành viên: { $user }
gg-approval-list = Thành viên đã duyệt:
    { $approvals }
gg-next-page = Mục khác: { $command }
gg-range-invalid = Phạm vi không hợp lệ. Chọn ít nhất một tin và không vượt giới hạn hiển thị.
    giới hạn: { $cap }
gg-range-start = Đã lưu đầu mốc cho bạn trong chủ đề này mười phút. Trả lời tin cuối bằng /purgeto.
gg-range-missing = Chưa có đầu mốc cho bạn ở đây. Dùng /purgefrom làm câu trả lời trước.
gg-content-needed = Nhập nội dung hoặc trả lời nội dung; tối đa3500 ký tự.
gg-log-status = Cài đặt nhật ký:
    loại: { $categories }
    đích: { $destination }
gg-log-unverified = Tôi chưa có bằng chứng nhận lệnh gốc từ kênh. Gửi /setlog trong kênh trước.
gg-log-forward = Chuyển tiếp /setlog gốc này vào nhóm. Quản trị viên kết nối cần quyền đổi thông tin ở cả hai cuộc trò chuyện.
gg-info = Thông tin người dùng hoặc cuộc trò chuyện:
    ID: { $id }
    tư cách thành viên: { $membership }
    tên: { $name }
    tên người dùng: { $username }
gg-op-unpinall = bỏ mọi ghim
gg-op-permapin = ghim vĩnh viễn
gg-op-promote = bổ nhiệm quản trị
gg-op-demote = bỏ quản trị
gg-op-approve_user = phê duyệt người dùng
gg-op-unapprove = bỏ phê duyệt
gg-op-unapproveall = bỏ mọi phê duyệt
gg-unknown = Không rõ
gg-chat-id = ID cuộc trò chuyện:
    ID: { $id }
gg-on = Bật
gg-off = Tắt
gg-anon-enabled = Tin cậy quản trị viên ẩn danh đang bật ở đây. Lệnh ẩn danh của nhóm này dùng quyền bot mà không xác định người. Thao tác của chủ vẫn cần người tạo đã xác minh. /anonadmin off khôi phục kiểm tra bởi người.
gg-right-invite_users = mời người dùng
gg-right-promote_members = bổ nhiệm quản trị viên
gg-right-manage_topics = quản lý chủ đề
gg-right-creator = người tạo nhóm
gg-log-join = Thành viên đã vào.
    thành viên: { $user }
gg-log-leave = Thành viên đã rời.
    thành viên: { $user }
gg-warning-row = Bản ghi cảnh báo:
    hết hạn: { $expiry }
    ID: { $id }
    lý do: { $reason }
gg-menu-prompt = Chọn lựa chọn.
gg-content-invalid = Nội dung không hợp lệ hoặc vượt giới hạn Telegram. Kiểm tra tên, định dạng, tùy biến và nút.
gg-content-unavailable = Nội dung không khả dụng hoặc tư cách thành viên hiện tại không cho phép truy cập.
gg-btn-private-note = Mở ghi chú
gg-open-private = Mở nội dung này trong riêng tư:
gg-items-cleared = Đã xóa các mục.
    số lượng: { $count }
gg-clearall-confirm = Người tạo nhóm xác nhận bằng <code>/{ $command } confirm</code>.
gg-button-usage = Dùng <code>/button "Nhãn" https://example.com</code>. Thêm <code>"Ghi chú" #tên same</code> để có nút khác cùng hàng. Bạn nhận cú pháp và xem trước hoạt động.
gg-btn-accept-rules = Chấp nhận quy tắc
gg-btn-open-verification = Mở xác minh
gg-captcha-private = Mở xác minh riêng để xác nhận tư cách thành viên nhóm.
    thành viên: { $user }
gg-captcha-choice = Chọn ảnh tương ứng bằng các nút. Chế độ và vị trí ký tự ở dưới.
    chế độ: { $mode }
    vị trí: { $position }
gg-captcha-settings = Cài đặt xác minh:
    bật: { $enabled }
    loại: { $kick }
    chế độ: { $mode }
    gỡ: { $release }
    giây: { $seconds }
gg-captcha-dependency = Bật lời chào trước xác minh. Lưu quy tắc trước khi yêu cầu chấp nhận.
gg-val-text = Ảnh chữ
gg-val-text2 = Ảnh ký tự
gg-captcha-attempts-exhausted = Xác minh thất bại sau quá nhiều đáp án sai; đã áp dụng hạn chế dự định.
gg-captcha-admin-exempt = Bạn hiện là quản trị viên nhóm. Xác minh đã kết thúc.
gg-captcha-question-text = Chọn từ trong ảnh.
gg-captcha-question-math = Giải phép tính trong ảnh rồi chọn đáp án.
gg-captcha-question-text2 = Chọn ký tự chỉ định trong ảnh từ trái sang phải.
    vị trí: { $position }
gg-locktypes = Các khóa nội dung có sẵn:
    loại: { $types }
gg-allowlist-title = Ngoại lệ khóa nội dung
gg-allowlist-invalid = Ngoại lệ không hợp lệ. Dùng miền/đường dẫn, lời mời chính xác, @cuộc_trò_chuyện hoặc danh tính khai báo như stickerpack:tên.
gg-reason-lock = Nội dung bị khóa:
    loại: { $types }
gg-lock-applied = Đã áp dụng quy tắc khóa.
    lý do: { $reason }
    loại: { $types }
gg-reaction-failed = Không áp dụng được quy tắc phản ứng. Máy chủ Bot API này có thể không hỗ trợ xóa phản ứng.
    mã: { $code }
gg-reaction-anonymous = Số đếm ẩn danh không có ID người dùng hoặc cuộc trò chuyện gửi. API xóa cần thông tin đó; không tuyên bố đã xóa.
gg-none = Không có
gg-blocklist-title = Danh sách cấm
gg-blocklist-invalid = Điều kiện, lý do hoặc thao tác không hợp lệ. Kiểm tra dấu ngoặc kép, thoát ký tự đại diện và thời hạn cần cho chế độ tạm.
gg-blocklist-settings = Cài đặt danh sách cấm:
    xóa: { $delete }
    chế độ: { $mode }
gg-blocklist-action = Đã áp dụng quy tắc danh sách cấm cho thành viên.
    lý do: { $reason }
    thành viên: { $user }
gg-lock-album = album
gg-lock-anonchannel = người gửi ẩn danh hoặc kênh
gg-lock-audio = âm thanh
gg-lock-bot = tin từ bot
gg-lock-button = nút
gg-lock-cashtag = thẻ tiền tệ
gg-lock-checklist = danh sách kiểm
gg-lock-cjk = văn bản Trung/Nhật/Hàn
gg-lock-command = lệnh
gg-lock-comment = bình luận kênh
gg-lock-contact = liên hệ
gg-lock-cyrillic = chữ Kirin
gg-lock-document = tài liệu
gg-lock-email = email
gg-lock-emoji = emoji
gg-lock-emojicustom = emoji tùy chỉnh
gg-lock-emojigame = trò chơi emoji
gg-lock-emojionly = chỉ emoji
gg-lock-externalreply = trả lời bên ngoài
gg-lock-forward = chuyển tiếp
gg-lock-forwarduser = tin chuyển tiếp người dùng
gg-lock-forwardbot = tin chuyển tiếp bot
gg-lock-forwardchannel = tin chuyển tiếp kênh
gg-lock-forwardstory = câu chuyện chuyển tiếp
gg-lock-game = trò chơi
gg-lock-gif = GIF
gg-lock-guestbot = bot khách
gg-lock-inline = nội dung nội tuyến
gg-lock-invitelink = liên kết mời
gg-lock-botlink = liên kết bot
gg-lock-location = vị trí
gg-lock-outsidereaction = phản ứng người ngoài
gg-lock-phone = số điện thoại
gg-lock-photo = ảnh
gg-lock-poll = bình chọn
gg-lock-reaction = phản ứng
gg-lock-rtl = văn bản phải sang trái
gg-lock-spoiler = nội dung ẩn
gg-lock-sticker = nhãn dán
gg-lock-stickeranimated = nhãn dán động
gg-lock-stickerpremium = nhãn dán premium
gg-lock-text = văn bản
gg-lock-url = URL
gg-lock-video = video
gg-lock-videonote = tin video
gg-flood-status = Dồn tin: ngưỡng liên tiếp ở N; cửa sổ thời gian vượt N. Thao tác, thời hạn và dọn chuỗi ở dưới.
    xóa toàn bộ chuỗi: { $clear }
    ngưỡng liên tiếp: { $consecutive }
    số lượng: { $count }
    thời hạn: { $duration }
    chế độ: { $mode }
    giây: { $seconds }
gg-raid-status = Bảo vệ vào hàng loạt. /antiraid on bật; /antiraid off dừng. Chu kỳ, thời hạn cấm và ngưỡng tự động mỗi phút ở dưới.
    hoạt động: { $active }
    ngưỡng tự động: { $auto }
    thời hạn cấm: { $ban }
    khoảng thời gian: { $period }
    đến: { $until }
gg-raid-banned = 🛡 Thành viên bị cấm tạm trong khi bảo vệ vào hàng loạt đang hoạt động.
    thành viên: { $user }
gg-raid-declined = 🛡 Đã từ chối yêu cầu khi bảo vệ vào hàng loạt đang hoạt động.
    thành viên: { $user }
gg-silent-consent-required = Người tạo phải cho phép thao tác im lặng và cấu hình nhật ký trước khi chọn thao tác này.
gg-btn-enable-raid = Bật bảo vệ vào hàng loạt
gg-human-required = Thao tác này cần người có thể xác định.
gg-group-message-required = Dùng lệnh với tin hoặc chủ đề thật của nhóm. ID tin riêng không phải ID tin nhóm.
gg-connection-private = Dùng lệnh kết nối trong trò chuyện riêng của chúng ta.
gg-connection-disconnected = Đã ngắt. Năm nhóm gần nhất còn để kết nối lại.
gg-connection-current = Đã kết nối nhóm. Tư cách thành viên và quyền hiện tại được kiểm tra mỗi thao tác.
    nhóm: { $group }
gg-connection-none = Không có kết nối hoạt động. Dùng /connect GROUP_ID hoặc /connect @nhóm.
gg-connection-open = Mở kết nối cá nhân trong trò chuyện riêng của chúng ta.
gg-btn-connect = Kết nối riêng
gg-connection-history = Năm nhóm gần nhất của bạn. Chọn một; cần tư cách thành viên hiện tại.
gg-connection-unavailable = Kết nối không khả dụng. Bạn phải là thành viên người hiện tại và bot phải là quản trị ở đó.
gg-catalog-unresolved = /{ $command } là tên danh mục chưa có thao tác xác định. Dùng /notes hoặc /flood cho tính năng đã triển khai.
gg-cleanup-failed = Dọn tin thất bại hoặc không khả dụng; không tuyên bố đã xóa.
gg-op-lock_change = đổi khóa nội dung
gg-op-allowlist_change = đổi ngoại lệ
gg-op-allowlist_clear = xóa ngoại lệ
gg-op-blocklist_change = đổi từ bị cấm
gg-op-blocklist_clear = xóa từ bị cấm
gg-op-raid_change = đổi bảo vệ vào hàng loạt
gg-disabled-list = Chính sách lệnh: /disable TÊN và /enable TÊN kiểm soát chạy; /disabledel xóa; /disableadmin áp dụng cả quản trị viên.
    lệnh: { $commands }
gg-cleanup-types = Các loại dọn có sẵn:
    loại: { $types }
gg-cleanup-selected = Các loại dọn đã chọn:
    loại: { $types }
gg-advanced-status = Tự động im lặng cần đồng ý của người tạo và nhật ký. Bot cần quyền bình thường; mặc định kiểm duyệt thay đổi bật. Cấu hình khả năng nhìn giữa bot trong BotFather.
    cài đặt: { $setting }
    giá trị: { $value }
gg-action-topic = Chủ đề thao tác. /setactiontopic chọn chủ đề diễn đàn hiện tại; chủ đề chung có ID1.
    chủ đề: { $topic }
gg-topic-unavailable = Cần diễn đàn hiện tại và quyền quản lý phù hợp.
gg-topic-id-required = Nêu rõ ID chủ đề trong trò chuyện riêng đã kết nối.
gg-topic-general-delete = Không thể xóa chủ đề chung. Xác nhận cần người có thể xác định.
gg-topic-delete-confirm = Xóa chủ đề và tin? Xác nhận cá nhân có hiệu lực hai phút.
    chủ đề: { $topic }
gg-btn-confirm-delete = Xác nhận xóa
gg-topic-changed = Đã hoàn thành thao tác chủ đề.
    thao tác: { $action }
    chủ đề: { $topic }
gg-op-policy_change = đổi chính sách lệnh/dọn
gg-op-topic_create = tạo chủ đề
gg-op-topic_rename = đổi tên chủ đề
gg-op-topic_close = đóng chủ đề
gg-op-topic_reopen = mở lại chủ đề
gg-op-topic_delete = xóa chủ đề và tin
gg-op-echo = gửi nội dung đã định dạng
gg-broadcast-owner = Chỉ người vận hành được cấu hình cho bot hoặc chủ thật của bản con mới được gửi tới các nhóm của nó.
gg-broadcast-queued = Chiến dịch nhóm đã xếp hàng. Mục tiêu và kết quả tách theo bot.
    ID: { $id }
gg-broadcast-busy = Chiến dịch khác đang chạy hoặc chưa hết năm phút từ lần tạo trước.
gg-broadcast-empty = Bạn không có chiến dịch nhóm trong bot này.
gg-broadcast-status = Trạng thái chiến dịch nhóm:
    đã hủy: { $cancelled }
    thất bại: { $failed }
    ID: { $id }
    xếp hàng: { $queued }
    đã gửi: { $sent }
    trạng thái: { $status }
    kết quả chưa chắc chắn: { $uncertain }
gg-fed-created = Đã tạo liên đoàn. ID thuộc mạng riêng của bot này.
    ID: { $id }
    tên: { $name }
gg-fed-info = Thông tin liên đoàn:
    quản trị viên: { $admins }
    ID: { $id }
    nhật ký: { $log }
    tên: { $name }
    thông báo: { $notifications }
    chủ: { $owner }
    cần lý do: { $reasons }
gg-fed-list = Các liên đoàn bạn sở hữu hoặc quản lý:
    { $rows }
gg-fed-admins = Chủ sở hữu trước, sau đó quản trị viên liên đoàn:
    { $rows }
gg-fed-quiet = Cài đặt giải thích im lặng khi vào nhóm và gửi tin. Việc thực thi vẫn hoạt động.
    giá trị: { $value }
gg-fed-policy = Chính sách lý do và thông báo cho chủ:
    thông báo: { $notifications }
    cần lý do: { $reasons }
gg-fed-confirm-delete = Xóa vĩnh viễn liên đoàn, dữ liệu và tư cách thành viên? Các lệnh cấm Telegram hiện tại vẫn còn. Xác nhận cá nhân trong năm phút.
    ID: { $id }
    tên: { $name }
gg-fed-confirm-log = Đặt nhật ký liên đoàn được nêu? Xác nhận trong năm phút. Quyền của bạn tại đích và quyền đăng của bot sẽ được kiểm tra lại.
    đích: { $destination }
    ID: { $id }
    tên: { $name }
gg-fed-confirm-sent = Đã gửi xác nhận cá nhân cho chủ liên đoàn.
gg-fed-deleted = Đã xóa liên đoàn. Các lệnh cấm Telegram hiện tại vẫn còn.
gg-fed-log-set = Đã đặt đích nhật ký liên đoàn:
    đích: { $destination }
gg-fed-cancel = Hủy
gg-fed-cancelled = Đã hủy.
gg-fed-saved-delivery-failed = Đã lưu thay đổi nhưng không gửi được thông báo hoặc nhật ký. Kiểm tra đích và quyền truy cập của bot.
gg-fed-error-authority = Cần chủ hiện tại hoặc vai trò liên đoàn phù hợp. Quyền quản trị nhóm không cấp quyền liên đoàn.
gg-fed-error-private = Dùng lệnh trong trò chuyện riêng của bạn với bot này.
gg-fed-error-group = Dùng lệnh trong nhóm thật. Kết nối riêng không chọn nhóm liên đoàn.
gg-fed-error-owned = Bạn đã sở hữu liên đoàn trong bot này. Dùng /fedinfo, /renamefed hoặc /delfed riêng.
gg-fed-error-name = Nhập tên không rỗng, không có ký tự điều khiển. Tên tối đa64 ký tự.
gg-fed-error-id = Nhập UUID liên đoàn hợp lệ trong bot này. ID Rose không kết nối dịch vụ riêng của chúng tôi.
gg-fed-error-missing = Không tìm thấy liên đoàn trong bot hay ngữ cảnh này.
gg-fed-error-creator = Chỉ người tạo nhóm Telegram hiện tại được gắn nhóm vào hoặc rời liên đoàn.
gg-fed-error-target = Nhập ID người dương, trả lời người hoặc tên vừa được xác minh. Không thể hạ vai trò chủ.
gg-fed-error-value = Tham số liên đoàn không hợp lệ. Dùng on/off cho chính sách và ID hợp lệ khi cần.
gg-fed-error-stale = Xác nhận hết hạn, đã dùng hoặc liên đoàn, chủ hay đích đã đổi. Yêu cầu xác nhận mới.
gg-fed-error-destination = Chủ phải là quản trị hiện tại tại đích và bot phải đăng được. Kênh cần post_messages.
gg-fed-error-delivery = Không gửi hoặc gắn được xác nhận cá nhân. Mở trò chuyện riêng với bot rồi thử lại.
gg-fed-event = Sự kiện liên đoàn:
    sự kiện: { $event }
    ID: { $id }
    tên: { $name }
    thành viên: { $user }
gg-fed-event-rename = Đã đổi tên
gg-fed-event-delete = Đã xóa; lệnh cấm Telegram vẫn còn
gg-fed-event-promote = Đã thêm quản trị viên
gg-fed-event-demote = Đã bỏ quản trị viên
gg-fed-event-self-remove = Quản trị viên rời vai trò
gg-fed-event-reason = Đã đổi chính sách lý do
gg-fed-event-notif = Đã đổi thông báo cho chủ
gg-fed-event-log = Đã đổi đích nhật ký
gg-fed-event-unlog = Đã bỏ đích nhật ký
gg-fed-event-ban = Đã lưu chính sách cấm; thực thi xếp hàng
gg-fed-event-unban = Đã bỏ chính sách cấm; gỡ hạn chế thuộc bot đã xếp hàng
gg-fed-event-subscribe = Đã thêm đăng ký; kiểm tra người đã quan sát xếp hàng
gg-fed-event-unsubscribe = Đã bỏ đăng ký; các nguồn khác vẫn còn
gg-fed-ban-details = Đối tượng và lý do cấm:
    lý do: { $reason }
    thành viên: { $user }
gg-fed-passive = Chính sách liên đoàn cấm thành viên. Nguồn và lý do ở dưới.
    ID: { $id }
    lý do: { $reason }
    nguồn: { $source }
    thành viên: { $user }
gg-fed-enforce-failed = Chính sách liên đoàn cấm thành viên nhưng loại bỏ thất bại. Kiểm tra quyền bot. Nguồn và lý do ở dưới.
    ID: { $id }
    lý do: { $reason }
    nguồn: { $source }
    thành viên: { $user }
gg-fed-stat = Các lệnh cấm liên đoàn cho thành viên này:
    { $rows }
    thành viên: { $user }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — hoạt động: { $status }; thay đổi: { $date }.
gg-fed-stat-more = Còn nguồn khác. Dùng lệnh tiếp trang hoặc ID liên đoàn cụ thể để xem lý do và ngày.
gg-fed-intent-saved = Đã lưu chính sách; đối tượng đã quan sát được xếp hàng. Quyền hiện tại và nguồn hạn chế khác được kiểm tra trước hiệu ứng.
    thành viên: { $user }
    phiên bản: { $version }
gg-fed-subscriptions = Các đăng ký trực tiếp lệnh cấm liên đoàn:
    { $rows }
gg-fed-imported = Đã kiểm tra và lưu bản ghi; bỏ qua bản trùng giống nhau. Thực thi cho đối tượng đã quan sát xếp hàng.
    số lượng: { $count }
    bản trùng giống nhau: { $duplicates }
gg-fed-event-import = Đã nhập lệnh cấm đã kiểm tra; thực thi xếp hàng
gg-fed-error-file-format = Trả lời CSV UTF-8 có id/reason, JSONL/NDJSON có user_id hoặc mảng JSON do bot xuất. Một dòng sai chặn mọi lần ghi.
gg-fed-error-file-limit = Tối đa2 MiB và1000bản ghi. Từ chối tệp thiếu hoặc quá lớn; không âm thầm cắt danh sách.
gg-fed-error-file-duplicate = Bản ghi xung đột cho cùng ID người dùng. Không nhập lệnh cấm nào.
gg-fed-error-file-rate = Nhập và xuất dùng chung khoảng30phút cho mỗi liên đoàn. Thử lại sau.
gg-fed-error-reason = Lý do tối đa1024ký tự, không có ký tự điều khiển không hỗ trợ.
gg-fed-error-reason_required = Liên đoàn cần lý do không rỗng cho mỗi lệnh cấm.
gg-fed-error-cycle = Liên đoàn không được đăng ký chính nó hay tạo chu trình có hướng.
gg-fed-error-graph_limit = Đạt giới hạn:32đích trực tiếp,128liên đoàn có thể tới, độ sâu16 hoặc10000cạnh trong bot này.
gg-data-confirm = Xác nhận trong năm phút. Người tạo hiện tại và phiên bản nhóm được kiểm tra lại. Chỉ mô đun đã chọn thay đổi; danh tính, tin cậy và lệnh cấm hoạt động vẫn còn.
    SHA-256: { $digest }
    nhóm: { $group }
    mô đun: { $modules }
    thao tác: { $operation }
gg-data-import = Nhập mô đun nhóm
gg-data-reset = Đặt lại mô đun nhóm
gg-data-privacy-delete = Xóa dữ liệu cá nhân tùy chọn của bot này
gg-data-confirm-button = Xác nhận thay đổi
gg-data-personal = Mở xác nhận trong trò chuyện riêng của bạn.
gg-data-saved = Đã lưu các mô đun đã chọn.
gg-data-error-authority = Nhập/đặt lại cần người tạo nhóm có thể xác định hiện tại. Xuất cần quản trị hiện tại.
gg-data-error-format = Trả lời JSON Group Guard có phiên bản hợp lệ do /export tạo.
gg-data-error-limit = Tệp vượt giới hạn kích thước hoặc nội dung đã đặt.
gg-data-error-version = Lược đồ hoặc phiên bản không hỗ trợ; không đổi gì.
gg-data-error-module = Chọn mô đun đã biết:/export all hoặc /export notes rules. Nhập/đặt lại dùng cùng tên.
gg-data-error-field = Trường mô đun sai hoặc thiếu. Chưa áp dụng cài đặt.
gg-data-error-item = Nội dung, tùy chọn hoặc quyền lặp không hợp lệ. Chưa lưu nội dung.
gg-data-error-media = Media phải được tải lên bot này và truy cập được qua getFile. Không hỗ trợ ID tệp của bot khác.
gg-data-error-destination = Đích nhật ký và chủ đề cần quyền hiện tại cùng khả năng bot. ID chủ đề chỉ hợp lệ trong cùng nhóm.
gg-data-error-language = Chọn ngôn ngữ đã cài bằng /setlang.
gg-data-error-stale = Xác nhận hết hạn, đã đổi hoặc đã dùng. Bắt đầu lại.
gg-data-error-restore = Không thể khôi phục an toàn hạn chế tạm thời thuộc bot. Giữ bằng chứng; kiểm tra quyền bot.
gg-data-error-rate = Thao tác dữ liệu nhóm dùng khoảng địa phương năm phút. Thử lại sau.
gg-data-error-delivery = Không gửi được xác nhận riêng. Mở trò chuyện riêng với bot và thử lại.
gg-data-error-saved_delivery = Đã lưu cài đặt nhưng chưa cập nhật gợi ý lệnh. Kiểm tra quyền bot.
gg-privacy-policy = <b>Dữ liệu của bạn trong Group Guard này</b>
    /privacy data xuất kết nối, hồ sơ đã quan sát, cảnh báo, phê duyệt, trạng thái hạn chế/xác minh, sở hữu/vai trò/lệnh cấm liên đoàn và công việc bảo mật. Không gồm nội dung riêng của người khác, đáp án xác minh, thông tin đăng nhập hoặc tệp tải lên thô. Dùng lệnh tiếp trang.
    /privacy delete bỏ lịch sử kết nối tùy chọn, tên/tên người dùng đã quan sát, xác minh không hoạt động và nội dung chiến dịch đã kết thúc của bạn trong bot này. Cảnh báo/hạn chế đang hoạt động, phiên bản cấm, vai trò, sở hữu, quyền dịch vụ, chống phát lại và việc API chưa chắc chắn giữ ID tối thiểu để bảo mật và thứ tự. Dùng lệnh rõ ràng để rời/xóa liên đoàn cho những liên kết đó. Hồ sơ nền tảng chung và bot khác vẫn còn.
    Người vận hành quản lý sao lưu và kiểm toán riêng. Lệnh không xóa tin Telegram bên ngoài hoặc bản sao lưu và không hứa thời hạn giữ tự động.
gg-privacy-usage = /privacy policy · /privacy data [tiếp trang] · /privacy delete — chỉ trong trò chuyện riêng của bạn với bot này.
gg-privacy-private = Cần trò chuyện riêng thật của người yêu cầu. Con trỏ sai không cấp dữ liệu người khác.
gg-privacy-next = Trang dữ liệu tiếp:/privacy data { $cursor }
gg-privacy-deleted = Đã bỏ dữ liệu cá nhân tùy chọn của bot này. Bảo mật hoạt động, sở hữu và việc chưa chắc chắn giữ ID tối thiểu; xem /privacy policy.
gg-language-usage = Chọn ngôn ngữ nhóm bằng /setlang. /lang riêng đổi ngôn ngữ nền tảng cá nhân. Mã có sẵn ở dưới.
    mã ngôn ngữ: { $codes }
gg-language-saved = Đã đổi ngôn ngữ trả lời nhóm.
gg-help-index = <b>Hướng dẫn lệnh Group Guard</b>
    /help mục · /help lệnh · /help mục 2. Lệnh được nêu cũng chạy qua /connect đã xác minh; trả lời riêng ở trong trò chuyện riêng thật.
    Cài đặt cần change_info; xử phạt cần restrict_members; xóa cần delete_messages; ghim cần pin_messages; bổ nhiệm cần promote_members; chủ đề cần manage_topics. Quyền bot được kiểm tra riêng. Thao tác chủ cần người tạo là người hiện tại. /settings mở bảng nhóm cá nhân.
gg-help-search = <b>Lệnh phù hợp</b>
    tìm kiếm: { $query }
gg-help-connected = Nhóm hoặc kết nối đã xác minh; quyền theo phạm vi
gg-help-group-only = Cần tin nhắn nhóm thật
gg-help-unsupported = Tên danh mục được giữ; hành vi chưa xác định trả lời giải thích
gg-help-next = Trang tiếp
gg-help-previous = Trang trước
gg-help-family-title-moderation = Quản lý và phê duyệt
gg-help-family-title-messages = Xóa và ghim tin
gg-help-family-title-logging = Nhật ký được phép
gg-help-family-title-settings = Cài đặt và ngôn ngữ nhóm
gg-help-family-title-content = Ghi chú, bộ lọc, quy tắc và chào mừng
gg-help-family-title-captcha = Xác minh người mới
gg-help-family-title-locks = Khóa nội dung và ngoại lệ
gg-help-family-title-blocklists = Đối sánh và nội dung bị cấm
gg-help-family-title-antispam = Chống dồn tin và vào hàng loạt
gg-help-family-title-connections = Kết nối riêng tới nhóm
gg-help-family-title-identity = Thông tin người dùng và trò chuyện
gg-help-family-title-policy = Chính sách lệnh và bot
gg-help-family-title-cleanup = Dọn lệnh, bot và dịch vụ
gg-help-family-title-topics = Chủ đề diễn đàn
gg-help-family-title-utilities = Gửi nội dung và chiến dịch vận hành
gg-help-family-title-federations = Vai trò, cấm và đăng ký liên đoàn
gg-help-family-title-portability = Tệp nhóm và dữ liệu cá nhân
gg-help-family-title-discovery = Trợ giúp và biên tập nội dung
gg-help-family-moderation = Trả lời, ID hoặc @tên đã xác minh. /ban 20 lý do, /tban 20 60s lý do, /mute 20, /tmute 20 2h lý do; tạm thời60s–365d. /kickme chỉ bản thân. Biến thể d xóa tin trả lời; s xóa lệnh/tin trả lời và cần delete. Quản trị được bảo vệ. /setwarnlimit 3, /setwarnmode ban, /setwarntime 1d; nhóm mới ba cảnh báo, giữ cài đặt cũ. /approve chỉ cho nội dung/dồn tin thông thường, không fed/CAS/raid/thủ công. /promote giới hạn quyền chung. Đặt lại tất cả cần người tạo.
gg-help-family-messages = /del cần trả lời thật trong nhóm. /purge bắt đầu ở đó; /purgefrom và /purgeto đặt ranh giới. Giới hạn và quy tắc Telegram áp dụng; xác nhận lô không là số xóa chính xác. /pin [loud], /permapin, /unpin, /unpinall cần pin; unpinall cần người tạo. /antichannelpin và /cleanlinked cho tin tự động từ kênh liên kết.
gg-help-family-logging = /setlog -100… cần quản trị hiện tại tại đích và quyền đăng bot. Thiết lập chuyển tiếp phải khớp nguồn thật đã nhận. /logcategories:settings/admin/user/automated/reports/other; /log và /nolog chọn loại. Hiển thị lỗi gửi; nhật ký không chứng minh thao tác thành công.
gg-help-family-settings = /settings bảng cá nhân có hạn; kiểm tra change_info mới. /setlang mã ngôn ngữ nhóm; /lang riêng ngôn ngữ cá nhân. /night 23 7 +3 đóng ban đêm; /night off chỉ khôi phục trạng thái thuộc bot còn khớp. Thay đổi bên ngoài ưu tiên.
gg-help-family-content = /save từ văn bản hoặc trả lời media; /get từ, #từ, /notes. Tên mới một từ; giữ tên cũ rộng. /filter "cụm từ" văn bản, /filterprefix, /filterexact; /stop khóa cụ thể. /clearall và /stopall xác nhận người tạo. Định dạng Rose, liên kết, trích dẫn và ngẫu nhiên %%%. Trường:{ "{" }first{ "}" }, { "{" }last{ "}" }, { "{" }fullname{ "}" }, { "{" }username{ "}" }, { "{" }mention{ "}" }, { "{" }id{ "}" }, { "{" }chatname{ "}" }, { "{" }count{ "}" }. /button URL/ghi chú/quy tắc. Tùy chọn:preview/nonotif/protect/mediaspoiler; ghi chú admin/private/noprivate/repeat; bộ lọc user/allow_bot/replytag/command. /save từ chào { "{" }repeat 5m{ "}" } chỉ nội dung công khai và quyền tác giả hiện tại. Media thuộc bot.
gg-help-family-captcha = /captcha on/off, /captchamode off/button/math/text/text2, /setcaptchatext, /captcharules on, /captchakick on/off; /captchakicktime và /captchamutetime có giới hạn. Thử thách đã phát giữ thế hệ/hạn. Yêu cầu vào cần invite-users, hạn chế cần restrict-members. Đáp án cá nhân, một lần. Cấm liên đoàn ưu tiên.
gg-help-family-locks = /lock links [thao tác], /unlock loại; /locktypes loại thật, /locks trạng thái. /lockwarns cảnh báo. /allowlist miền/đường dẫn, lời mời chính xác, @chat hoặc stickerpack:/forward:/inline:/channel:/chat:/bot:/command:. Từ chối mẫu sai. Ngoại lệ chỉ nội dung khớp; tự động im lặng cần người tạo và nhật ký được phép.
gg-help-family-blocklists = /addblocklist "cụm từ" văn bản/prefix/exact và danh tính rõ ràng với lý do/thao tác tùy chọn. /rmblocklist khóa đã chọn chính xác. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute; tạm thời cần thời hạn. /blocklistdelete riêng. Độ phức tạp mẫu có giới hạn; từ chối bản ghi sai/quá mức.
gg-help-family-antispam = /setflood số liên tiếp; /setfloodtimer số thời gian cửa sổ; /setfloodmode xử phạt/thời hạn; /clearflood dọn chuỗi. Giữ cài đặt cũ. /flood và /antiflood chính sách; bí danh quyết định địa phương. /antiraid on/off/duration, /raidtime, /raidactiontime, /autoantiraid tách thời gian và xử phạt. Ưu tiên phê duyệt/CAPTCHA; hết hạn theo thế hệ sống qua khởi động lại.
gg-help-family-connections = /connect groupID hoặc liên kết cá nhân; kiểm tra tư cách thành viên bạn và bot. Thay đổi vẫn cần quyền cụ thể mới kiểm tra. /connection lựa chọn, /disconnect bỏ, /connect lịch sử và tiếp trang. Kết nối không cấp quyền chủ liên đoàn hay người vận hành.
gg-help-family-identity = /id ID người/trò chuyện/nguồn thật; /info đối tượng hiện tại. Trả lời và @tên cần bằng chứng hiện tại của bot này. Tin nhóm ẩn danh không xác định người; không tạo ID người giả.
gg-help-family-policy = /disable lệnh, /enable lệnh, /disabled, /disableable tên chuẩn và bí danh. /disableadmin ngoại lệ quản trị; /disabledel xóa. Lệnh khôi phục vẫn dùng được. /bot2bot off/admin/all tư cách thành viên thật; mặc định người kiểm duyệt thay đổi. /bot2botskipreview chỉ người tạo. /silentactions đồng ý và nhật ký được phép. runs/saved chưa xác định giải thích.
gg-help-family-cleanup = /cleancommand admin/user/other và /keepcommand chọn lệnh. /cleanmsg action/filter/note và /keepmsg chỉ tin thật do bot này gửi; biên nhận và việc5phút, không đoán ID. /cleanservice và /nocleanservice:join/leave/other/photo/pin/title/videochat. Xử lý dịch vụ và thanh toán hợp lệ trước dọn.
gg-help-family-topics = /newtopic tên, /renametopic tên, /closetopic, /reopentopic chủ đề hiện tại thật. /deletetopic xác nhận người tạo; /setactiontopic cùng nhóm. Cần diễn đàn và manage-topics. Lỗi thật cho chủ đề thiếu hoặc không hỗ trợ.
gg-help-family-utilities = /echo và /say nội dung trực tiếp hay trả lời qua bộ hiển thị có giới hạn. /broadcast chỉ người vận hành được cấu hình hoặc chủ bản con thật, nhóm được cấu hình của bot này. Kết quả giữ gửi một phần/chưa chắc; trạng thái/hủy không gửi lại phần thành công.
gg-help-family-federations = /newfed tên UUID riêng. Riêng chọn fed bạn sở hữu bất kể kết nối; đọc UUID không cấp vai trò. /fedpromote và /feddemote vai trò; /feddemoteme bản thân. /joinfed UUID và /leavefed người tạo hiện tại. Xóa không gỡ cấm Telegram. /fban userID lý do, /unfban userID chủ/quản trị fed; /fedreason, /fednotif, /setfedlog chủ. /quietfed chỉ giải thích. /subfed UUID có hướng, giới hạn, không chu trình. /fedstat [userID], /fbanstat UUID nguồn/trạng thái. /fbanlist csv/minicsv/json chủ, chung30phút; /importfbans CSV giới hạn hoặc JSONL thật và mảng JSON riêng. Chỉ người đã quan sát, không danh mục thành viên đầy đủ.
gg-help-family-portability = /export all hoặc mô đun quản trị; /import và /reset người tạo hiện tại là người, xác nhận cá nhân một lần5phút. Khoảng địa phương5phút; JSON riêng có phiên bản tối đa2MiB và giới hạn nội dung. Mô đun:moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Giữ phần không chọn. Không nhập tin cậy, thử thách/việc đã phát, quyền dịch vụ, vai trò hay cấm hoạt động. /privacy policy/data/delete PM riêng, có trang và giữ bảo mật tối thiểu. Không bộ chuyển đổi xuất Rose đầy đủ đã xác minh.
gg-help-family-discovery = /help các mục; /help lệnh tên/bí danh; /help mục 2 tiếp trang. /button hỗ trợ mã nút. Hướng dẫn có ngữ cảnh, quyền, mặc định và giới hạn. /settings bảng nhóm cá nhân.
gg-data-error-cache_pending = Đã bỏ dữ liệu SQL tùy chọn. Dọn bộ nhớ đệm không khả dụng đã xếp hàng; dữ liệu bảo mật hoạt động vẫn còn.
