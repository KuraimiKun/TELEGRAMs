## Independently authored Group Guard zh-tw content.
group-welcome = 🛡 感謝新增！請給我刪除訊息、限制成員和置頂訊息的管理員許可權。使用 /settings 配置。
gg-start = 🛡 你好，<b>{ $name }</b>！我是 <b>Group Guard</b>：提供新成員驗證、訊息刷屏和 CAS 防護、內容限制、管理、筆記、過濾器、規則與歡迎訊息。請將我設為群管理員，然後使用 /settings 或 /help。
gg-help = 📖 /help 顯示分類；/help 命令可搜尋命令。管理：/ban /mute /kick /warn。內容：/save /filter /rules。防護：/lock /blocklist /night。/settings 開啟個人群設定面板。
gg-welcome-default = 👋 歡迎 { "{" }mention{ "}" } 加入 <b>{ "{" }group{ "}" }</b>！
gg-credit = 🛡 由 @{ $bot } 提供保護
gg-btn-add = ➕ 新增到群組
gg-btn-commands = 📖 命令
gg-btn-rules = 📜 規則
gg-btn-human = ✅ 我是真人
gg-btn-unwarn = ↩️ 移除警告（管理員）
gg-btn-locks = 🔒 內容限制 · 數量: { $count }
gg-btn-open-settings = ⚙️ 開啟設定
gg-btn-admin-tab = 🛡 群組
gg-captcha = 🤖 請在指定期限內證明你是真人，否則將被移出群組。
    分鐘: { $minutes }
    成員: { $user }
gg-captcha-button = 點選下方按鈕 👇
gg-captcha-math = <b>{ $a } + { $b }</b> 等於多少？
gg-captcha-not-you = 此按鈕屬於其他人。
gg-captcha-ok = ✅ 歡迎！
gg-captcha-wrong = ❌ 回答錯誤。還有次數時可以重試。
    剩餘嘗試: { $left }
gg-captcha-failed = ❌ 錯誤次數過多。
gg-captcha-passed = ✅ 驗證透過。歡迎！
    成員: { $user }
gg-cas-banned = 🚫 此成員被 CAS 標記為垃圾訊息傳送者，已被封鎖。
    成員: { $user }
gg-join-request = 👋 請證明你是真人以加入群組：
    群組: { $group }
gg-join-approved = ✅ 入群請求已批准。歡迎！
gg-join-expired = ⌛ 此請求已過期，請重新申請入群。
gg-goodbye = 👋 成員已離開群組。
    成員: { $user }
gg-flood-mute = 🌊 此成員因訊息過多而被臨時禁言。
    成員: { $user }
gg-flood-kick = 🌊 此成員因訊息過多而被移出群組。
    成員: { $user }
gg-flood-ban = 🌊 此成員因訊息過多而被封鎖。
    成員: { $user }
gg-newbie-links = 🆕 新成員在指定的最初幾小時內不能傳送連結。
    小時: { $hours }
    成員: { $user }
gg-spam-banned = 🧠 此成員因垃圾訊息而被封鎖。
    成員: { $user }
gg-reason-blocklist = 受限詞語
gg-need-right = ⛔ 需要相應的管理員許可權。
    許可權: { $right }
gg-right-admin = 管理員
gg-right-restrict = 限制成員
gg-right-delete = 刪除訊息
gg-right-pin = 置頂訊息
gg-right-change_info = 修改群資訊
gg-admins-only = ⛔ 僅限管理員。
gg-need-target = 👤 請回復一條訊息，或提供使用者 ID 或當前已驗證的 @使用者名稱。
gg-target-admin = 🙅 此操作不能針對管理員。
gg-bot-no-rights = ⚠️ 我需要管理員身份及相應許可權。
gg-banned = 🔨 成員已封鎖。
    原因: { $reason }
    成員: { $user }
gg-banned-for = 🔨 成員已在指定期限內封鎖。
    原因: { $reason }
    時間: { $time }
    成員: { $user }
gg-unbanned = ✅ 成員封鎖已解除。
    成員: { $user }
gg-kicked = 👢 成員已移出，可以重新加入。
    原因: { $reason }
    成員: { $user }
gg-muted = 🔇 成員已禁言。
    原因: { $reason }
    成員: { $user }
gg-muted-for = 🔇 成員已在指定期限內禁言。
    原因: { $reason }
    時間: { $time }
    成員: { $user }
gg-unmuted = 🔊 成員可以再次發言。
    成員: { $user }
gg-warned = ⚠️ 成員警告已記錄。
    數量: { $count }
    上限: { $limit }
    原因: { $reason }
    成員: { $user }
gg-warn-limit-ban = 🔨 已達到警告上限，成員已封鎖。
    上限: { $limit }
    成員: { $user }
gg-warn-limit-mute = 🔇 已達到警告上限，成員已禁言。
    上限: { $limit }
    成員: { $user }
gg-warn-limit-kick = 👢 已達到警告上限，成員已移出。
    上限: { $limit }
    成員: { $user }
gg-unwarned = ↩️ 成員的一條警告已移除。
    數量: { $count }
    上限: { $limit }
    成員: { $user }
gg-warn-removed = ↩️ 管理員已移除警告。
    管理員: { $admin }
gg-warns = ⚠️ 成員警告：
    數量: { $count }
    上限: { $limit }
    成員: { $user }
gg-warns-reset = 🧽 成員警告已清零。
    成員: { $user }
gg-purge-reply = 🧹 請回復要刪除範圍的第一條訊息。
gg-purged = 🧹 訊息已刪除。
    數量: { $count }
gg-pin-reply = 📌 請回復要置頂的訊息。
gg-report-reply = 🚨 請回復要舉報的訊息。
gg-reported = 🚨 已向管理員舉報成員。
    成員: { $user }
gg-setlog-usage = 📒 將我設為日誌頻道管理員，然後使用 <code>/setlog -100…</code> 提供頻道 ID。
gg-setlog-failed = ⚠️ 我無法在該處傳送訊息，請先將我設為管理員。
gg-setlog-done = 📒 日誌頻道已連線。
gg-setlog-off = 📒 日誌頻道已斷開。
gg-log-connected = 📒 此聊天接收群組管理日誌。
    群組: { $group }
gg-log-flood = 🌊 檢測到刷屏：
    操作: { $action }
    成員: { $user }
gg-log-report = 🚨 成員舉報：
    成員: { $user }
gg-log-spam = 🧠 AI 垃圾訊息封鎖：
    文字: { $text }
    成員: { $user }
gg-rules = 📜 <b>規則</b>
    { $rules }
gg-no-rules = 📜 尚未儲存規則。管理員可以使用 /setrules 文字。
gg-rules-saved = 📜 規則已儲存。
gg-rules-cleared = 📜 規則已刪除。
gg-welcome-usage = 👋 使用 <code>/setwelcome 你好 {"{"}mention{"}"}，歡迎加入 {"{"}group{"}"}！</code>，或回覆一條訊息。
gg-welcome-saved = 👋 歡迎訊息已儲存。
gg-welcome-reset = 👋 預設歡迎訊息已恢復。
gg-note-usage = 📝 <code>/save 名稱 文字</code>，或回覆一條訊息並使用 <code>/save 名稱</code>。
gg-filter-usage = 🔁 <code>/filter 詞語 回覆</code>，或回覆一條訊息並使用 <code>/filter 詞語</code>。
gg-note-saved = 📝 筆記已儲存。按照訪問許可權使用 <code>#{ $key }</code> 獲取。
gg-filter-saved = 🔁 匹配“{ $key }”時，我會回覆。
gg-notes-empty = 📝 尚無筆記。
gg-filters-empty = 🔁 尚無過濾器。
gg-notes-list = 📝 <b>筆記</b>
gg-filters-list = 🔁 <b>過濾器</b>
gg-item-deleted = 🗑 條目已刪除。
    鍵: { $key }
gg-item-missing = 🤷 此名稱下沒有儲存內容。
gg-items-limit = 📦 此群筆記和過濾器數量已達到上限。
gg-lock-usage = 🔒 使用 <code>/lock links</code>。下方列出可用型別；<code>all</code> 選擇所有型別。
    型別: { $types }
gg-locked = 🔒 已限制內容：
    型別: { $types }
gg-unlocked = 🔓 已允許內容：
    型別: { $types }
gg-locks-title = 🔒 <b>內容限制</b>
gg-locks-panel = 🔒 <b>限制</b>：受限內容將被刪除，管理員豁免。
gg-lock-links = 連結
gg-lock-invites = 邀請連結
gg-lock-forwards = 轉發
gg-lock-media = 媒體
gg-lock-stickers = 貼紙
gg-lock-gifs = GIF
gg-lock-voice = 語音訊息
gg-lock-polls = 投票
gg-lock-bots = 機器人
gg-blocklist = 🚫 <b>受限詞語</b>
    詞語: { $words }
gg-blocklist-empty = 🚫 沒有受限詞語。
gg-blocklist-usage = 🚫 <code>/addblock 詞語, 其他短語</code> · <code>/rmblock 詞語</code>
gg-blocklist-saved = 🚫 遮蔽列表已更新。
    數量: { $count }
gg-night-usage = 🌙 <code>/night 23 7 +3</code> 在 UTC+3 的 23:00 至 07:00 關閉群組；<code>/night off</code> 停用。
gg-night-on = 🌙 群組夜間時間已設定。
    結束: { $end }
    開始: { $start }
    時區: { $tz }
gg-night-off = 🌙 夜間模式已停用。
gg-night-start = 🌙 晚安！群組將關閉至指定時間。
    結束: { $end }
gg-night-end = ☀️ 早上好！群組已重新開放。
gg-panel = ⚙️ <b>群組設定</b>
    點選選項修改。夜間時間透過 /night 設定。
    群組: { $group }
    夜間時段: { $night }
gg-panel-sent = 📬 設定已私聊傳送。
gg-panel-start-first = 📬 請先開啟與我的私聊，再點選下方按鈕。
gg-credit-vip = 💎 隱藏保護說明需要 VIP，請在私聊使用 /vip。
gg-opt-wel = 👋 歡迎訊息 · 值: { $value }
gg-opt-cln = 🧹 刪除入群訊息 · 值: { $value }
gg-opt-bye = 👋 離群訊息 · 值: { $value }
gg-opt-cap = 🤖 驗證 · 值: { $value }
gg-opt-cpm = ⏱ 驗證期限，分鐘 · 值: { $value }
gg-opt-fld = 🌊 刷屏閾值 · 值: { $value }
gg-opt-fla = 🌊 刷屏處理 · 值: { $value }
gg-opt-wrn = ⚠️ 警告上限 · 值: { $value }
gg-opt-wra = ⚠️ 警告處理 · 值: { $value }
gg-opt-act = ⏳ 自動限制，分鐘 · 值: { $value }
gg-opt-cas = 🛡 CAS 保護 · 值: { $value }
gg-opt-nwb = 🆕 新成員禁止連結，小時 · 值: { $value }
gg-opt-ais = 🧠 AI 垃圾訊息保護 · 值: { $value }
gg-opt-ngt = 🌙 夜間模式 · 值: { $value }
gg-opt-crd = 🏷 保護說明 · 值: { $value }
gg-opt-lang = 🌐 語言 · 值: { $value }
gg-val-button = 按鈕
gg-val-math = 算術題
gg-val-off = 停用
gg-val-mute = 禁言
gg-val-kick = 移出
gg-val-ban = 封鎖
gg-adm = 🛡 <b>Group Guard：統計</b>
    群組: { $groups }
    條目: { $items }
    警告: { $warns }
cmd-settings = 群組設定
cmd-help = 命令指南
gg-auth-denied = 無法驗證許可權，未作修改。
gg-target-invalid = 請選擇已知的真人成員，無法驗證此目標。
gg-duration-invalid = 請使用 60s 至 365d 的時長。臨時命令必須提供時長。
gg-reason-invalid = 原因最長 256 個字元。
gg-outcome-failed = 操作失敗或未獲授權。
gg-outcome-partial = 操作僅部分完成。如果移出後的恢復失敗，封鎖可能仍然保留。
gg-outcome-ancillary = 主要操作已完成，但附加步驟失敗。
gg-review-request = 請稽核下方不可修改的操作。當前有許可權的真人可在 120 秒內批准。時長以秒為單位。
    詳情: { $details }
    時長: { $duration }
    操作: { $operation }
    目標: { $target }
gg-review-approve = 批准此操作
gg-review-unavailable = 確認儲存不可用，請重新傳送命令。
gg-review-expired = 此確認已過期、無效或已經使用。
gg-review-consumed = 確認已使用。請檢視結果；重試需要新命令。
gg-duration-permanent = 永久／無時限
gg-purge-ack = API 已確認刪除請求。實際刪除數量未知。
    API 已確認: { $acknowledged }
    請求數量: { $requested }
gg-warning-removed = 警告已移除。
gg-op-ban = 封鎖
gg-op-mute = 禁言
gg-op-kick = 移出
gg-op-unban = 解除封鎖
gg-op-unmute = 解除禁言
gg-op-warn = 警告
gg-op-unwarn = 移除警告
gg-op-resetwarns = 清零警告
gg-op-purge = 刪除訊息範圍
gg-op-delete = 刪除訊息
gg-op-pin = 置頂訊息
gg-op-unpin = 取消置頂
gg-op-setlog = 設定日誌目標
gg-op-unsetlog = 移除日誌目標
gg-op-config = 修改設定
gg-op-save = 儲存內容
gg-op-remove = 移除內容
gg-op-panel = 開啟面板
gg-review-details-above = 請求的完整內容位於緊接上方的訊息中。
gg-warn-pending = 警告已儲存，達到閾值的操作已在處理中。
gg-done = 已完成。
gg-setting-saved = 設定已儲存。
    設定: { $setting }
gg-setting-value = 當前設定值：
    設定: { $setting }
    值: { $value }
gg-setting-invalid = 設定無效。請使用 on/off、有效模式或 10m 等時長。
gg-warning-settings = 警告設定：
    時長: { $duration }
    到期: { $expiry }
    上限: { $limit }
    模式: { $mode }
gg-admin-changed = 管理員操作已完成。
    操作: { $action }
    成員: { $user }
gg-admin-list = 公開管理員：
    { $admins }
gg-approved = 成員已獲批准。
    原因: { $reason }
    成員: { $user }
gg-unapproved = 批准記錄已移除。
    數量: { $count }
gg-approval-status = 成員批准狀態：
    原因: { $reason }
    狀態: { $status }
    成員: { $user }
gg-approval-list = 已批准成員：
    { $approvals }
gg-next-page = 更多條目：{ $command }
gg-range-invalid = 範圍無效。請至少選擇一條訊息，且不超過指定上限。
    最大數量: { $cap }
gg-range-start = 已為你在此主題儲存起點，有效十分鐘。請回復末條訊息使用 /purgeto。
gg-range-missing = 你在此處沒有儲存起點，請先回復訊息使用 /purgefrom。
gg-content-needed = 請提供內容或回覆內容，最多 3500 個字元。
gg-log-status = 日誌設定：
    類別: { $categories }
    目標: { $destination }
gg-log-unverified = 我沒有收到此頻道命令的可驗證原件。請先在頻道傳送 /setlog。
gg-log-forward = 請將此原始 /setlog 命令轉發到群組。連線者必須有兩個聊天的修改資訊許可權。
gg-info = 使用者或聊天資訊：
    ID: { $id }
    成員身份: { $membership }
    名稱: { $name }
    使用者名稱: { $username }
gg-op-unpinall = 取消所有置頂
gg-op-permapin = 永久置頂
gg-op-promote = 任命管理員
gg-op-demote = 移除管理員
gg-op-approve_user = 批准使用者
gg-op-unapprove = 移除批准
gg-op-unapproveall = 移除全部批准
gg-unknown = 未知
gg-chat-id = 聊天 ID：
    ID: { $id }
gg-on = 啟用
gg-off = 停用
gg-anon-enabled = 此處已信任匿名管理員。本群匿名命令使用機器人的許可權，但不會識別真人。所有者操作仍需要驗證當前建立者。/anonadmin off 可恢復真人稽核。
gg-right-invite_users = 邀請使用者
gg-right-promote_members = 任命管理員
gg-right-manage_topics = 管理主題
gg-right-creator = 群建立者
gg-log-join = 成員加入。
    成員: { $user }
gg-log-leave = 成員離開。
    成員: { $user }
gg-warning-row = 警告記錄：
    到期: { $expiry }
    ID: { $id }
    原因: { $reason }
gg-menu-prompt = 請選擇選項。
gg-content-invalid = 內容無效或超出 Telegram 限制。請檢查名稱、格式、修飾符和按鈕。
gg-content-unavailable = 內容不可用，或你當前的群成員身份不允許訪問。
gg-btn-private-note = 開啟筆記
gg-open-private = 私聊開啟此內容：
gg-items-cleared = 條目已清除。
    數量: { $count }
gg-clearall-confirm = 群建立者使用 <code>/{ $command } confirm</code> 確認。
gg-button-usage = 使用 <code>/button "標籤" https://example.com</code>。新增 <code>"筆記" #名稱 same</code> 可在同一行增加按鈕。你會收到標記和可用預覽。
gg-btn-accept-rules = 接受規則
gg-btn-open-verification = 開啟驗證
gg-captcha-private = 請開啟私聊驗證，以確認你的群成員身份。
    成員: { $user }
gg-captcha-choice = 請用按鈕選擇匹配的圖片。模式和字元位置見下方。
    模式: { $mode }
    位置: { $position }
gg-captcha-settings = 驗證設定：
    啟用: { $enabled }
    移出: { $kick }
    模式: { $mode }
    解除: { $release }
    秒: { $seconds }
gg-captcha-dependency = 請先啟用歡迎訊息再啟用驗證。要求接受規則前，請先儲存規則。
gg-val-text = 文字圖片
gg-val-text2 = 字元圖片
gg-captcha-attempts-exhausted = 錯誤次數過多，驗證失敗，已施加規定的限制。
gg-captcha-admin-exempt = 你已成為群管理員，驗證已結束。
gg-captcha-question-text = 請選擇圖片中的詞語。
gg-captcha-question-math = 請解答圖片中的算式並選擇答案。
gg-captcha-question-text2 = 請從左向右選擇圖片中指定位置的字元。
    位置: { $position }
gg-locktypes = 可用內容限制：
    型別: { $types }
gg-allowlist-title = 內容限制例外
gg-allowlist-invalid = 例外無效。請使用域名／路徑、精確邀請、@聊天或 stickerpack:名稱 等明確身份。
gg-reason-lock = 受限內容：
    型別: { $types }
gg-lock-applied = 內容限制規則已應用。
    原因: { $reason }
    型別: { $types }
gg-reaction-failed = 無法應用回應規則。此 Bot API 伺服器可能不支援移除回應。
    程式碼: { $code }
gg-reaction-anonymous = 匿名回應統計沒有使用者 ID 或傳送者聊天 ID。移除 API 需要此資訊，因此不聲稱已移除。
gg-none = 無
gg-blocklist-title = 遮蔽列表
gg-blocklist-invalid = 觸發條件、原因或操作無效。請檢查引號、萬用字元轉義及臨時模式要求的時長。
gg-blocklist-settings = 遮蔽列表設定：
    刪除: { $delete }
    模式: { $mode }
gg-blocklist-action = 已對成員應用遮蔽列表規則。
    原因: { $reason }
    成員: { $user }
gg-lock-album = 相簿
gg-lock-anonchannel = 頻道傳送者
gg-lock-audio = 音訊
gg-lock-bot = 機器人
gg-lock-button = 內聯按鈕
gg-lock-cashtag = 貨幣標記
gg-lock-checklist = 清單
gg-lock-cjk = 中文／日文／韓文文字
gg-lock-command = 命令
gg-lock-comment = 非成員評論
gg-lock-contact = 聯絡人
gg-lock-cyrillic = 西里爾文字
gg-lock-document = 文件
gg-lock-email = 電子郵件地址
gg-lock-emoji = 表情符號
gg-lock-emojicustom = 自定義表情
gg-lock-emojigame = 表情遊戲
gg-lock-emojionly = 純表情文字
gg-lock-externalreply = 外部回覆
gg-lock-forward = 轉發
gg-lock-forwarduser = 使用者轉發
gg-lock-forwardbot = 機器人轉發
gg-lock-forwardchannel = 頻道轉發
gg-lock-forwardstory = 轉發故事
gg-lock-game = 遊戲
gg-lock-gif = GIF 動畫
gg-lock-guestbot = 訪客機器人
gg-lock-inline = 內聯機器人
gg-lock-invitelink = Telegram 邀請
gg-lock-botlink = 機器人連結
gg-lock-location = 位置
gg-lock-outsidereaction = 非成員回應
gg-lock-phone = 電話號碼
gg-lock-photo = 照片
gg-lock-poll = 投票
gg-lock-reaction = 回應
gg-lock-rtl = 從右向左文字
gg-lock-spoiler = 隱藏內容
gg-lock-sticker = 貼紙
gg-lock-stickeranimated = 動態貼紙
gg-lock-stickerpremium = 高階貼紙
gg-lock-text = 文字
gg-lock-url = URL
gg-lock-video = 影片
gg-lock-videonote = 影片訊息
gg-flood-status = 刷屏限制：連續模式在 N 條觸發，時間視窗超過 N 條觸發。操作、時長和清理範圍見下方。
    清理完整序列: { $clear }
    連續閾值: { $consecutive }
    數量: { $count }
    時長: { $duration }
    模式: { $mode }
    秒: { $seconds }
gg-raid-status = 批次入群保護。/antiraid on 啟用，/antiraid off 停止。保護期限、封鎖時長和每分鐘自動閾值見下方。
    生效: { $active }
    自動閾值: { $auto }
    封鎖時長: { $ban }
    週期: { $period }
    截止: { $until }
gg-raid-banned = 🛡 批次入群保護生效期間，成員已臨時封鎖。
    成員: { $user }
gg-raid-declined = 🛡 批次入群保護生效期間，入群請求已拒絕。
    成員: { $user }
gg-silent-consent-required = 選擇此操作前，建立者必須允許靜默操作並配置日誌。
gg-btn-enable-raid = 啟用批次入群保護
gg-human-required = 此操作需要可識別的真人。
gg-group-message-required = 請針對真實群訊息或主題使用此命令。私聊訊息 ID 不代表群訊息。
gg-connection-private = 請在我們的私聊中使用此連線命令。
gg-connection-disconnected = 已斷開。最近五個群組仍可用於重新連線。
gg-connection-current = 群組已連線。每次操作均驗證當前成員身份及許可權。
    群組: { $group }
gg-connection-none = 無有效連線。請使用 /connect GROUP_ID 或 /connect @群組。
gg-connection-open = 請在我們的私聊中開啟你的個人連線。
gg-btn-connect = 私聊連線
gg-connection-history = 最近五個群組。請選擇一個；需要當前成員身份。
gg-connection-unavailable = 連線不可用。你必須是當前真人成員，機器人必須是該群管理員。
gg-catalog-unresolved = /{ $command } 屬於未定義操作的目錄名稱。請使用 /notes 或 /flood 獲取已實現功能。
gg-cleanup-failed = 訊息清理失敗或不可用，不聲稱已刪除。
gg-op-lock_change = 修改內容限制
gg-op-allowlist_change = 修改限制例外
gg-op-allowlist_clear = 清除限制例外
gg-op-blocklist_change = 修改遮蔽列表
gg-op-blocklist_clear = 清空遮蔽列表
gg-op-raid_change = 修改批次入群保護
gg-disabled-list = 命令策略：/disable 名稱 和 /enable 名稱 控制執行，/disabledel 控制刪除，/disableadmin 將管理員納入限制。
    命令: { $commands }
gg-cleanup-types = 可用清理類別：
    型別: { $types }
gg-cleanup-selected = 已選擇清理類別：
    型別: { $types }
gg-advanced-status = 靜默自動操作需要建立者同意及日誌。機器人需要正常許可權，預設稽核變更。請在 BotFather 配置機器人之間的可見性。
    設定: { $setting }
    值: { $value }
gg-action-topic = 操作主題。/setactiontopic 選擇當前論壇主題；一般主題 ID 為 1。
    主題: { $topic }
gg-topic-unavailable = 需要當前論壇及相應管理許可權。
gg-topic-id-required = 在已連線的私聊中，請明確提供主題 ID。
gg-topic-general-delete = 不能刪除一般主題。確認需要可識別的真人。
gg-topic-delete-confirm = 刪除主題及訊息？個人確認有效兩分鐘。
    主題: { $topic }
gg-btn-confirm-delete = 確認刪除
gg-topic-changed = 主題操作已完成。
    操作: { $action }
    主題: { $topic }
gg-op-policy_change = 修改命令／清理策略
gg-op-topic_create = 建立主題
gg-op-topic_rename = 重新命名主題
gg-op-topic_close = 關閉主題
gg-op-topic_reopen = 重新開啟主題
gg-op-topic_delete = 刪除主題及訊息
gg-op-echo = 傳送格式化內容
gg-broadcast-owner = 僅此機器人配置的運營者或子例項的真實所有者可向所屬群組廣播。
gg-broadcast-queued = 群組廣播已排隊。目標及結果按機器人隔離。
    ID: { $id }
gg-broadcast-busy = 另一個廣播正在執行，或上次建立後的五分鐘間隔尚未結束。
gg-broadcast-empty = 你在此機器人中沒有群組廣播。
gg-broadcast-status = 群組廣播狀態：
    已取消: { $cancelled }
    失敗: { $failed }
    ID: { $id }
    已排隊: { $queued }
    已送達: { $sent }
    狀態: { $status }
    結果不確定: { $uncertain }
gg-fed-created = 聯盟已建立。此 ID 屬於本機器人的獨立網路。
    ID: { $id }
    名稱: { $name }
gg-fed-info = 聯盟資訊：
    管理員: { $admins }
    ID: { $id }
    日誌: { $log }
    名稱: { $name }
    通知: { $notifications }
    所有者: { $owner }
    必須提供原因: { $reasons }
gg-fed-list = 你擁有或管理的聯盟：
    { $rows }
gg-fed-admins = 先列出所有者，再列出聯盟管理員：
    { $rows }
gg-fed-quiet = 靜默被動說明。封鎖執行仍然生效。
    值: { $value }
gg-fed-policy = 封鎖原因與所有者通知策略：
    通知: { $notifications }
    必須提供原因: { $reasons }
gg-fed-confirm-delete = 永久刪除聯盟、資料及成員關係？已有 Telegram 封鎖保留。請在五分鐘內進行個人確認。
    ID: { $id }
    名稱: { $name }
gg-fed-confirm-log = 設定指定聯盟日誌？請在五分鐘內確認。會重新驗證你對目標的許可權及機器人的釋出許可權。
    目標: { $destination }
    ID: { $id }
    名稱: { $name }
gg-fed-confirm-sent = 個人確認已傳送給聯盟所有者。
gg-fed-deleted = 聯盟已刪除。已有 Telegram 封鎖保留。
gg-fed-log-set = 聯盟日誌目標已設定：
    目標: { $destination }
gg-fed-cancel = 取消
gg-fed-cancelled = 已取消。
gg-fed-saved-delivery-failed = 變更已儲存，但通知或日誌未送達。請檢查目標及機器人訪問許可權。
gg-fed-error-authority = 需要當前聯盟所有者或相應聯盟角色。Telegram 群許可權不會賦予聯盟許可權。
gg-fed-error-private = 請在你與此機器人的個人私聊中使用此命令。
gg-fed-error-group = 請在真實群組中使用此命令。私聊連線不會選擇聯盟群組。
gg-fed-error-owned = 你已在此機器人中擁有聯盟。請在私聊使用 /fedinfo、/renamefed 或 /delfed。
gg-fed-error-name = 請提供非空且無控制字元的名稱。名稱限制為 64 個字元。
gg-fed-error-id = 請提供此機器人的有效聯盟 UUID。Rose 的 ID 不會連線到我們的獨立服務。
gg-fed-error-missing = 此機器人或上下文中未找到聯盟。
gg-fed-error-creator = 只有當前 Telegram 群建立者可以將群加入聯盟或退出聯盟。
gg-fed-error-target = 請提供正數真人 ID、回覆真人的訊息或當前已驗證的使用者名稱。所有者不能被降職。
gg-fed-error-value = 聯盟引數無效。策略請使用 on/off，需要 ID 時請提供有效 ID。
gg-fed-error-stale = 確認已過期、使用過，或聯盟、所有者、目標已改變。請重新請求。
gg-fed-error-destination = 所有者必須是目標的當前管理員，機器人必須能夠釋出。頻道需要 post_messages 許可權。
gg-fed-error-delivery = 個人確認未送達或未繫結。請開啟與機器人的私聊後重試。
gg-fed-event = 聯盟事件：
    事件: { $event }
    ID: { $id }
    名稱: { $name }
    成員: { $user }
gg-fed-event-rename = 名稱已修改
gg-fed-event-delete = 已刪除；Telegram 封鎖保留
gg-fed-event-promote = 管理員已新增
gg-fed-event-demote = 管理員已移除
gg-fed-event-self-remove = 管理員已辭任
gg-fed-event-reason = 封鎖原因策略已修改
gg-fed-event-notif = 所有者通知已修改
gg-fed-event-log = 日誌目標已修改
gg-fed-event-unlog = 日誌目標已移除
gg-fed-event-ban = 封鎖策略已儲存，執行已排隊
gg-fed-event-unban = 封鎖策略已移除，自有約束解除已排隊
gg-fed-event-subscribe = 訂閱已新增，已觀察使用者的核查已排隊
gg-fed-event-unsubscribe = 訂閱已移除，其他來源保留
gg-fed-ban-details = 封鎖目標及原因：
    原因: { $reason }
    成員: { $user }
gg-fed-passive = 聯盟策略封鎖此成員。來源與原因見下方。
    ID: { $id }
    原因: { $reason }
    來源: { $source }
    成員: { $user }
gg-fed-enforce-failed = 聯盟策略封鎖此成員，但移出失敗。請檢查機器人許可權。來源與原因見下方。
    ID: { $id }
    原因: { $reason }
    來源: { $source }
    成員: { $user }
gg-fed-stat = 此成員的聯盟封鎖：
    { $rows }
    成員: { $user }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — 生效：{ $status }；變更：{ $date }。
gg-fed-stat-more = 還有更多來源。請使用繼續命令，或提供具體聯盟 ID 檢視原因與日期。
gg-fed-intent-saved = 策略已儲存，已觀察的目標已排隊。執行前會核查當前許可權及其他約束來源。
    成員: { $user }
    版本: { $version }
gg-fed-subscriptions = 聯盟封鎖的直接訂閱：
    { $rows }
gg-fed-imported = 條目已驗證並儲存，完全相同的重複項已跳過。對已觀察目標的執行已排隊。
    數量: { $count }
    完全相同的重複項: { $duplicates }
gg-fed-event-import = 已匯入驗證過的封鎖，執行已排隊
gg-fed-error-file-format = 請回復含 id/reason 的 UTF-8 CSV、含 user_id 的 JSONL/NDJSON，或本機器人的 JSON 陣列匯出。任意無效行均阻止所有寫入。
gg-fed-error-file-limit = 最多 2 MiB、1000 條。缺失或過大的檔案將拒絕；不會靜默截斷列表。
gg-fed-error-file-duplicate = 同一使用者 ID 存在衝突條目，未匯入封鎖。
gg-fed-error-file-rate = 每個聯盟的匯入與匯出共用 30 分鐘間隔，請稍後重試。
gg-fed-error-reason = 封鎖原因最長 1024 個字元，不能包含不支援的控制字元。
gg-fed-error-reason_required = 此聯盟要求每條封鎖提供非空原因。
gg-fed-error-cycle = 聯盟不能訂閱自身或形成有向迴圈。
gg-fed-error-graph_limit = 已達到上限：32 個直接目標、128 個可達聯盟、深度 16，或此機器人中 10 000 條連線。
gg-data-confirm = 請在五分鐘內確認。會重新驗證當前建立者及群版本。只修改選擇的模組；身份、信任及生效封鎖均保留。
    SHA-256: { $digest }
    群組: { $group }
    模組: { $modules }
    操作: { $operation }
gg-data-import = 匯入群模組
gg-data-reset = 重置群模組
gg-data-privacy-delete = 刪除此機器人的可選個人資料
gg-data-confirm-button = 確認此變更
gg-data-personal = 請在個人私聊中開啟確認。
gg-data-saved = 所選模組已儲存。
gg-data-error-authority = 匯入和重置需要當前可識別的群建立者，匯出需要當前管理員。
gg-data-error-format = 請回復 /export 建立的帶版本且有效的 Group Guard JSON。
gg-data-error-limit = 檔案超出大小或已配置的內容上限。
gg-data-error-version = 不支援此格式或版本，未應用變更。
gg-data-error-module = 請選擇已知模組：/export all 或 /export notes rules。匯入和重置使用相同名稱。
gg-data-error-field = 模組欄位缺失或無效，未應用設定。
gg-data-error-item = 內容、選項或重複訪問許可權無效，未儲存內容。
gg-data-error-media = 媒體必須上傳至此機器人並可透過 getFile 獲取。不支援其他機器人的檔案 ID。
gg-data-error-destination = 日誌及主題目標需要當前許可權及機器人能力。主題 ID 僅適用於同一群組。
gg-data-error-language = 請使用 /setlang 選擇已安裝的語言。
gg-data-error-stale = 確認已過期、修改或使用，請重新開始。
gg-data-error-restore = 無法安全恢復自有臨時限制。證據保留，請檢查機器人許可權。
gg-data-error-rate = 群資料操作採用本地五分鐘間隔，請稍後重試。
gg-data-error-delivery = 私聊確認未送達，請開啟與機器人的私聊後重試。
gg-data-error-saved_delivery = 設定已儲存，但命令建議未更新。請檢查機器人許可權。
gg-privacy-policy = <b>你在此 Group Guard 中的資料</b>
    /privacy data 匯出個人連線、已觀察資料、警告、批准、約束／驗證狀態、聯盟所有權／角色／封鎖及安全任務。不包含他人的私密內容、驗證答案、認證資訊和原始上傳檔案。請使用繼續命令獲取後續頁面。
    /privacy delete 移除可選連線歷史、已觀察姓名／使用者名稱、未生效的驗證以及此機器人中你已完成廣播的內容。生效警告／約束、封鎖版本、角色、所有權、訂閱、防重放記錄及不確定 API 操作保留安全與排序所需的最少標識。退出或刪除聯盟關係請使用相應明確命令。共享平臺資料及其他機器人資料不變。
    運營者單獨管理備份與審計。此命令不會刪除外部 Telegram 訊息或備份，也不承諾自動保留期限。
gg-privacy-usage = /privacy policy · /privacy data [繼續遊標] · /privacy delete — 僅限你與此機器人的個人私聊。
gg-privacy-private = 此操作需要請求人的個人私聊。無效遊標不會提供他人資料訪問許可權。
gg-privacy-next = 下一頁資料：/privacy data { $cursor }
gg-privacy-deleted = 此機器人的可選個人資料已移除。生效安全、所有權及不確定操作保留最少標識，詳見 /privacy policy。
gg-language-usage = 請用 /setlang 選擇群語言。私聊 /lang 修改個人平臺語言。可用程式碼見下方。
    語言程式碼: { $codes }
gg-language-saved = 群回覆語言已修改。
gg-help-index = <b>Group Guard 命令指南</b>
    /help 分類 · /help 命令 · /help 分類 2。標明的命令也可透過已驗證的 /connect 使用；私聊回覆保留在真實私聊中。
    設定需要修改資訊許可權，制裁需要限制成員許可權，刪除需要刪除許可權，置頂需要置頂許可權，任命需要提升管理員許可權，主題需要管理主題許可權。機器人許可權單獨核查。所有者操作需要當前真人建立者。/settings 開啟個人群設定面板。
gg-help-search = <b>匹配的命令</b>
    搜尋: { $query }
gg-help-connected = 群組或已驗證連線；所需許可權見分類
gg-help-group-only = 需要真實群訊息
gg-help-unsupported = 保留目錄名稱；未定義的行為返回說明
gg-help-next = 下一頁
gg-help-previous = 上一頁
gg-help-family-title-moderation = 管理與批准
gg-help-family-title-messages = 刪除和置頂訊息
gg-help-family-title-logging = 授權日誌
gg-help-family-title-settings = 群設定和語言
gg-help-family-title-content = 筆記、過濾器、規則和歡迎訊息
gg-help-family-title-captcha = 新成員驗證
gg-help-family-title-locks = 內容限制與例外
gg-help-family-title-blocklists = 遮蔽列表匹配與操作
gg-help-family-title-antispam = 刷屏與批次入群保護
gg-help-family-title-connections = 私聊群連線
gg-help-family-title-identity = 使用者和聊天資訊
gg-help-family-title-policy = 命令與機器人策略
gg-help-family-title-cleanup = 命令、機器人和服務訊息清理
gg-help-family-title-topics = 論壇主題
gg-help-family-title-utilities = 內容傳送與運營者廣播
gg-help-family-title-federations = 聯盟角色、封鎖和訂閱
gg-help-family-title-portability = 群檔案與個人資料
gg-help-family-title-discovery = 幫助與內容編輯器
gg-help-family-moderation = <b>管理</b> · 回覆、數字 ID 或已驗證的 @使用者。/ban 20 原因；/tban 20 60s 原因；/mute 20；/tmute 20 2h 原因。臨時制裁：60 秒至 365 天。/kickme 僅移出自己。d 變體刪除回覆的訊息；s 變體刪除命令／回覆並需要刪除許可權。管理員受保護。/setwarnlimit 3；/setwarnmode ban；/setwarntime 1d。新群預設三條警告，舊設定保留。/approve 僅豁免普通內容／刷屏保護，不豁免聯盟／CAS／批次入群／手動操作。/promote 不超過請求人與機器人的共同許可權。批次重置需要建立者。
gg-help-family-messages = <b>訊息</b> · /del 需要真實群內回覆。/purge 從該訊息開始；/purgefrom 和 /purgeto 儲存邊界。受配置上限與 Telegram 規則限制；批次確認不代表精確刪除數量。/pin [loud]、/permapin、/unpin、/unpinall 需要置頂許可權，全部取消置頂需要建立者。/antichannelpin 和 /cleanlinked 控制關聯頻道自動訊息。
gg-help-family-logging = <b>日誌</b> · /setlog -100… 需要目標當前管理許可權及機器人釋出許可權。轉發配置必須對應實際收到的原始命令。/logcategories：settings/admin/user/automated/reports/other；/log 和 /nolog 選擇類別。日誌傳送失敗仍有記錄，不能據此聲稱操作成功。
gg-help-family-settings = <b>設定</b> · /settings 開啟個人有效期面板，核查當前修改資訊許可權。/setlang 程式碼 儲存群語言；私聊 /lang 儲存個人語言。/night 23 7 +3 夜間關閉群組；/night off 僅恢復仍然匹配的機器人自有許可權快照，尊重外部變更。
gg-help-family-content = <b>編輯器</b> · /save 單詞 文字 或回覆媒體；/get 單詞、#單詞、/notes 讀取筆記。新筆記名為單個詞，舊有更寬名稱保留。/filter "短語" 文字、/filterprefix、/filterexact 選擇匹配模式；/stop 刪除指定鍵。/clearall 和 /stopall 需要建立者確認。Rose 格式支援粗體／斜體／下劃線／刪除線／程式碼、連結、引用與 %%% 隨機備選。欄位：{ "{" }first{ "}" }、{ "{" }last{ "}" }、{ "{" }fullname{ "}" }、{ "{" }username{ "}" }、{ "{" }mention{ "}" }、{ "{" }id{ "}" }、{ "{" }chatname{ "}" }、{ "{" }count{ "}" }。/button 建立 URL／筆記／規則按鈕。通用選項 preview/nonotif/protect/mediaspoiler；筆記 admin/private/noprivate/repeat；過濾器 user/allow_bot/replytag/command。/save 單詞 你好 { "{" }repeat 5m{ "}" } 只定期傳送公開內容，並核查作者當前許可權。規則、歡迎和私密內容使用相同渲染器。媒體 ID 屬於機器人。
gg-help-family-captcha = <b>驗證</b> · /captcha on/off；/captchamode off/button/math/text/text2；/setcaptchatext；/captcharules on；/captchakick on/off；/captchakicktime 和 /captchamutetime 設定有界期限。已發挑戰保留代次和截止時間。入群請求需要 invite-users，禁言需要 restrict-members。答案個人繫結且一次有效。聯盟封鎖優先於批准／CAPTCHA。
gg-help-family-locks = <b>內容限制</b> · /lock links [操作]、/unlock 型別；/locktypes 顯示真實型別，/locks 顯示狀態。/lockwarns 控制警告。/allowlist 支援域名／路徑、精確邀請、@聊天或 stickerpack:/forward:/inline:/channel:/chat:/bot:/command:。無效模式拒絕。例外僅適用於匹配內容；靜默自動操作需要建立者同意與授權日誌。
gg-help-family-blocklists = <b>遮蔽列表</b> · /addblocklist "短語" 支援文字／字首／精確匹配和明確身份，可附原因／操作。/rmblocklist 精確移除選擇的鍵。/blocklistmode nothing/warn/kick/ban/tban/mute/tmute 指定操作，臨時模式必須提供時長。/blocklistdelete 單獨控制刪除。萬用字元複雜度有限，無效條目及超限均拒絕。
gg-help-family-antispam = <b>刷屏與批次入群</b> · /setflood 數量 設定連續閾值；/setfloodtimer 數量 時長 設定時間視窗；/setfloodmode 設定制裁／時長；/clearflood 設定序列清理。舊設定保留。/flood 和 /antiflood 顯示策略，別名屬於本地相容選擇。/antiraid on/off/duration、/raidtime、/raidactiontime、/autoantiraid 儲存保護期限與獨立新成員制裁。優先於批准／CAPTCHA，按代次到期並可恢復重啟前狀態。
gg-help-family-connections = <b>連線</b> · /connect groupID 或個人連線。核查你與機器人的成員身份，變更仍需要精確當前許可權。/connection 顯示選中群；/disconnect 移除；/connect 顯示可繼續檢視的歷史。連線不授予聯盟所有權或運營者許可權。
gg-help-family-identity = <b>資訊</b> · /id 顯示真實使用者／聊天／來源 ID；/info 顯示當前目標。回覆與 @使用者名稱需要此機器人作用域內的當前證據。匿名群訊息不能識別真人，不會虛構真人 ID。
gg-help-family-policy = <b>策略</b> · /disable 命令、/enable 命令、/disabled、/disableable 使用規範名及別名。/disableadmin 控制管理員例外，/disabledel 控制刪除。恢復命令始終可用。/bot2bot off/admin/all 核查真實成員身份，預設變更需真人稽核。/bot2botskipreview 僅限建立者。/silentactions 需要同意與授權日誌。未定義的 runs/saved 返回說明。
gg-help-family-cleanup = <b>清理</b> · /cleancommand admin/user/other 與 /keepcommand 選擇命令類別。/cleanmsg action/filter/note 與 /keepmsg 僅針對本機器人實際傳送的訊息，傳送憑證與五分鐘任務避免猜測 ID。/cleanservice 與 /nocleanservice：join/leave/other/photo/pin/title/videochat。先進行功能處理與有效付款處理，再清理。
gg-help-family-topics = <b>主題</b> · /newtopic 名稱、/renametopic 名稱、/closetopic、/reopentopic 操作真實當前主題。/deletetopic 需要建立者確認；/setactiontopic 選擇同群目標。需要 Telegram 論壇及 manage-topics 許可權。缺失／不支援的主題報告真實錯誤。
gg-help-family-utilities = <b>工具</b> · /echo 與 /say 透過共享有界渲染器傳送直接或回覆內容。/broadcast 僅限配置運營者或實際子例項所有者，僅覆蓋此機器人配置的群組。各目標保留部分／不確定投遞結果，查詢狀態與取消不會重複成功附件。
gg-help-family-federations = <b>聯盟</b> · /newfed 名稱 在此機器人建立 UUID。私聊命令使用自己的聯盟，與群連線無關；讀取 UUID 不授予角色。/fedpromote、/feddemote 管理管理員；/feddemoteme 辭任。/joinfed UUID 和 /leavefed 需要當前群建立者。刪除不自動解除 Telegram 封鎖。/fban userID 原因 和 /unfban userID 需要聯盟所有者／管理員；/fedreason、/fednotif、/setfedlog 需要所有者。/quietfed 僅隱藏被動說明。/subfed UUID 有向、有界且無環。/fedstat [userID]、/fbanstat UUID 顯示來源／狀態。/fbanlist csv/minicsv/json 僅限所有者並採用共同 30 分鐘間隔；/importfbans 回覆有界 CSV 或真正逐行 JSON，並明確支援自身 JSON 陣列。只核查實際觀察的使用者，不聲稱有完整成員清單。
gg-help-family-portability = <b>檔案與隱私</b> · /export all 或模組 需要管理員；/import 與 /reset 需要當前真人建立者，並進行個人一次性五分鐘確認。本地五分鐘間隔；自身帶版本 JSON，最多 2MiB，遵守配置內容上限。模組：moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions。未選擇模組保留。不匯入信任、已發挑戰／任務、訂閱、角色或生效封鎖。/privacy policy/data/delete 僅在個人私聊使用，支援分頁且保留最少安全資訊。沒有經過驗證的完整 Rose 匯出介面卡。
gg-help-family-discovery = <b>幫助</b> · /help 顯示分類；/help 命令 搜尋名稱／別名；/help 分類 2 繼續。/button 幫助編輯按鈕標記。每份指南說明上下文、許可權、預設行為及上限。/settings 開啟個人群設定面板。
gg-data-error-cache_pending = 可選 SQL 資料已移除。快取不可用，其清理已排隊；生效安全記錄保留。
