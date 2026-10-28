## Independently authored Group Guard zh-cn content.
group-welcome = 🛡 感谢添加！请给我删除消息、限制成员和置顶消息的管理员权限。使用 /settings 配置。
gg-start = 🛡 你好，<b>{ $name }</b>！我是 <b>Group Guard</b>：提供新成员验证、消息刷屏和 CAS 防护、内容限制、管理、笔记、过滤器、规则与欢迎消息。请将我设为群管理员，然后使用 /settings 或 /help。
gg-help = 📖 /help 显示分类；/help 命令可搜索命令。管理：/ban /mute /kick /warn。内容：/save /filter /rules。防护：/lock /blocklist /night。/settings 打开个人群设置面板。
gg-welcome-default = 👋 欢迎 { "{" }mention{ "}" } 加入 <b>{ "{" }group{ "}" }</b>！
gg-credit = 🛡 由 @{ $bot } 提供保护
gg-btn-add = ➕ 添加到群组
gg-btn-commands = 📖 命令
gg-btn-rules = 📜 规则
gg-btn-human = ✅ 我是真人
gg-btn-unwarn = ↩️ 移除警告（管理员）
gg-btn-locks = 🔒 内容限制 · 数量: { $count }
gg-btn-open-settings = ⚙️ 打开设置
gg-btn-admin-tab = 🛡 群组
gg-captcha = 🤖 请在指定期限内证明你是真人，否则将被移出群组。
    分钟: { $minutes }
    成员: { $user }
gg-captcha-button = 点击下方按钮 👇
gg-captcha-math = <b>{ $a } + { $b }</b> 等于多少？
gg-captcha-not-you = 此按钮属于其他人。
gg-captcha-ok = ✅ 欢迎！
gg-captcha-wrong = ❌ 回答错误。还有次数时可以重试。
    剩余尝试: { $left }
gg-captcha-failed = ❌ 错误次数过多。
gg-captcha-passed = ✅ 验证通过。欢迎！
    成员: { $user }
gg-cas-banned = 🚫 此成员被 CAS 标记为垃圾消息发送者，已被封禁。
    成员: { $user }
gg-join-request = 👋 请证明你是真人以加入群组：
    群组: { $group }
gg-join-approved = ✅ 入群请求已批准。欢迎！
gg-join-expired = ⌛ 此请求已过期，请重新申请入群。
gg-goodbye = 👋 成员已离开群组。
    成员: { $user }
gg-flood-mute = 🌊 此成员因消息过多而被临时禁言。
    成员: { $user }
gg-flood-kick = 🌊 此成员因消息过多而被移出群组。
    成员: { $user }
gg-flood-ban = 🌊 此成员因消息过多而被封禁。
    成员: { $user }
gg-newbie-links = 🆕 新成员在指定的最初几小时内不能发送链接。
    小时: { $hours }
    成员: { $user }
gg-spam-banned = 🧠 此成员因垃圾消息而被封禁。
    成员: { $user }
gg-reason-blocklist = 受限词语
gg-need-right = ⛔ 需要相应的管理员权限。
    权限: { $right }
gg-right-admin = 管理员
gg-right-restrict = 限制成员
gg-right-delete = 删除消息
gg-right-pin = 置顶消息
gg-right-change_info = 修改群信息
gg-admins-only = ⛔ 仅限管理员。
gg-need-target = 👤 请回复一条消息，或提供用户 ID 或当前已验证的 @用户名。
gg-target-admin = 🙅 此操作不能针对管理员。
gg-bot-no-rights = ⚠️ 我需要管理员身份及相应权限。
gg-banned = 🔨 成员已封禁。
    原因: { $reason }
    成员: { $user }
gg-banned-for = 🔨 成员已在指定期限内封禁。
    原因: { $reason }
    时间: { $time }
    成员: { $user }
gg-unbanned = ✅ 成员封禁已解除。
    成员: { $user }
gg-kicked = 👢 成员已移出，可以重新加入。
    原因: { $reason }
    成员: { $user }
gg-muted = 🔇 成员已禁言。
    原因: { $reason }
    成员: { $user }
gg-muted-for = 🔇 成员已在指定期限内禁言。
    原因: { $reason }
    时间: { $time }
    成员: { $user }
gg-unmuted = 🔊 成员可以再次发言。
    成员: { $user }
gg-warned = ⚠️ 成员警告已记录。
    数量: { $count }
    上限: { $limit }
    原因: { $reason }
    成员: { $user }
gg-warn-limit-ban = 🔨 已达到警告上限，成员已封禁。
    上限: { $limit }
    成员: { $user }
gg-warn-limit-mute = 🔇 已达到警告上限，成员已禁言。
    上限: { $limit }
    成员: { $user }
gg-warn-limit-kick = 👢 已达到警告上限，成员已移出。
    上限: { $limit }
    成员: { $user }
gg-unwarned = ↩️ 成员的一条警告已移除。
    数量: { $count }
    上限: { $limit }
    成员: { $user }
gg-warn-removed = ↩️ 管理员已移除警告。
    管理员: { $admin }
gg-warns = ⚠️ 成员警告：
    数量: { $count }
    上限: { $limit }
    成员: { $user }
gg-warns-reset = 🧽 成员警告已清零。
    成员: { $user }
gg-purge-reply = 🧹 请回复要删除范围的第一条消息。
gg-purged = 🧹 消息已删除。
    数量: { $count }
gg-pin-reply = 📌 请回复要置顶的消息。
gg-report-reply = 🚨 请回复要举报的消息。
gg-reported = 🚨 已向管理员举报成员。
    成员: { $user }
gg-setlog-usage = 📒 将我设为日志频道管理员，然后使用 <code>/setlog -100…</code> 提供频道 ID。
gg-setlog-failed = ⚠️ 我无法在该处发送消息，请先将我设为管理员。
gg-setlog-done = 📒 日志频道已连接。
gg-setlog-off = 📒 日志频道已断开。
gg-log-connected = 📒 此聊天接收群组管理日志。
    群组: { $group }
gg-log-flood = 🌊 检测到刷屏：
    操作: { $action }
    成员: { $user }
gg-log-report = 🚨 成员举报：
    成员: { $user }
gg-log-spam = 🧠 AI 垃圾消息封禁：
    文本: { $text }
    成员: { $user }
gg-rules = 📜 <b>规则</b>
    { $rules }
gg-no-rules = 📜 尚未保存规则。管理员可以使用 /setrules 文本。
gg-rules-saved = 📜 规则已保存。
gg-rules-cleared = 📜 规则已删除。
gg-welcome-usage = 👋 使用 <code>/setwelcome 你好 {"{"}mention{"}"}，欢迎加入 {"{"}group{"}"}！</code>，或回复一条消息。
gg-welcome-saved = 👋 欢迎消息已保存。
gg-welcome-reset = 👋 默认欢迎消息已恢复。
gg-note-usage = 📝 <code>/save 名称 文本</code>，或回复一条消息并使用 <code>/save 名称</code>。
gg-filter-usage = 🔁 <code>/filter 词语 回复</code>，或回复一条消息并使用 <code>/filter 词语</code>。
gg-note-saved = 📝 笔记已保存。按照访问权限使用 <code>#{ $key }</code> 获取。
gg-filter-saved = 🔁 匹配“{ $key }”时，我会回复。
gg-notes-empty = 📝 尚无笔记。
gg-filters-empty = 🔁 尚无过滤器。
gg-notes-list = 📝 <b>笔记</b>
gg-filters-list = 🔁 <b>过滤器</b>
gg-item-deleted = 🗑 条目已删除。
    键: { $key }
gg-item-missing = 🤷 此名称下没有保存内容。
gg-items-limit = 📦 此群笔记和过滤器数量已达到上限。
gg-lock-usage = 🔒 使用 <code>/lock links</code>。下方列出可用类型；<code>all</code> 选择所有类型。
    类型: { $types }
gg-locked = 🔒 已限制内容：
    类型: { $types }
gg-unlocked = 🔓 已允许内容：
    类型: { $types }
gg-locks-title = 🔒 <b>内容限制</b>
gg-locks-panel = 🔒 <b>限制</b>：受限内容将被删除，管理员豁免。
gg-lock-links = 链接
gg-lock-invites = 邀请链接
gg-lock-forwards = 转发
gg-lock-media = 媒体
gg-lock-stickers = 贴纸
gg-lock-gifs = GIF
gg-lock-voice = 语音消息
gg-lock-polls = 投票
gg-lock-bots = 机器人
gg-blocklist = 🚫 <b>受限词语</b>
    词语: { $words }
gg-blocklist-empty = 🚫 没有受限词语。
gg-blocklist-usage = 🚫 <code>/addblock 词语, 其他短语</code> · <code>/rmblock 词语</code>
gg-blocklist-saved = 🚫 屏蔽列表已更新。
    数量: { $count }
gg-night-usage = 🌙 <code>/night 23 7 +3</code> 在 UTC+3 的 23:00 至 07:00 关闭群组；<code>/night off</code> 停用。
gg-night-on = 🌙 群组夜间时间已设置。
    结束: { $end }
    开始: { $start }
    时区: { $tz }
gg-night-off = 🌙 夜间模式已停用。
gg-night-start = 🌙 晚安！群组将关闭至指定时间。
    结束: { $end }
gg-night-end = ☀️ 早上好！群组已重新开放。
gg-panel = ⚙️ <b>群组设置</b>
    点击选项修改。夜间时间通过 /night 设置。
    群组: { $group }
    夜间时段: { $night }
gg-panel-sent = 📬 设置已私聊发送。
gg-panel-start-first = 📬 请先开启与我的私聊，再点击下方按钮。
gg-credit-vip = 💎 隐藏保护说明需要 VIP，请在私聊使用 /vip。
gg-opt-wel = 👋 欢迎消息 · 值: { $value }
gg-opt-cln = 🧹 删除入群消息 · 值: { $value }
gg-opt-bye = 👋 离群消息 · 值: { $value }
gg-opt-cap = 🤖 验证 · 值: { $value }
gg-opt-cpm = ⏱ 验证期限，分钟 · 值: { $value }
gg-opt-fld = 🌊 刷屏阈值 · 值: { $value }
gg-opt-fla = 🌊 刷屏处理 · 值: { $value }
gg-opt-wrn = ⚠️ 警告上限 · 值: { $value }
gg-opt-wra = ⚠️ 警告处理 · 值: { $value }
gg-opt-act = ⏳ 自动限制，分钟 · 值: { $value }
gg-opt-cas = 🛡 CAS 保护 · 值: { $value }
gg-opt-nwb = 🆕 新成员禁止链接，小时 · 值: { $value }
gg-opt-ais = 🧠 AI 垃圾消息保护 · 值: { $value }
gg-opt-ngt = 🌙 夜间模式 · 值: { $value }
gg-opt-crd = 🏷 保护说明 · 值: { $value }
gg-opt-lang = 🌐 语言 · 值: { $value }
gg-val-button = 按钮
gg-val-math = 算术题
gg-val-off = 停用
gg-val-mute = 禁言
gg-val-kick = 移出
gg-val-ban = 封禁
gg-adm = 🛡 <b>Group Guard：统计</b>
    群组: { $groups }
    条目: { $items }
    警告: { $warns }
cmd-settings = 群组设置
cmd-help = 命令指南
gg-auth-denied = 无法验证权限，未作修改。
gg-target-invalid = 请选择已知的真人成员，无法验证此目标。
gg-duration-invalid = 请使用 60s 至 365d 的时长。临时命令必须提供时长。
gg-reason-invalid = 原因最长 256 个字符。
gg-outcome-failed = 操作失败或未获授权。
gg-outcome-partial = 操作仅部分完成。如果移出后的恢复失败，封禁可能仍然保留。
gg-outcome-ancillary = 主要操作已完成，但附加步骤失败。
gg-review-request = 请审核下方不可修改的操作。当前有权限的真人可在 120 秒内批准。时长以秒为单位。
    详情: { $details }
    时长: { $duration }
    操作: { $operation }
    目标: { $target }
gg-review-approve = 批准此操作
gg-review-unavailable = 确认存储不可用，请重新发送命令。
gg-review-expired = 此确认已过期、无效或已经使用。
gg-review-consumed = 确认已使用。请查看结果；重试需要新命令。
gg-duration-permanent = 永久／无时限
gg-purge-ack = API 已确认删除请求。实际删除数量未知。
    API 已确认: { $acknowledged }
    请求数量: { $requested }
gg-warning-removed = 警告已移除。
gg-op-ban = 封禁
gg-op-mute = 禁言
gg-op-kick = 移出
gg-op-unban = 解除封禁
gg-op-unmute = 解除禁言
gg-op-warn = 警告
gg-op-unwarn = 移除警告
gg-op-resetwarns = 清零警告
gg-op-purge = 删除消息范围
gg-op-delete = 删除消息
gg-op-pin = 置顶消息
gg-op-unpin = 取消置顶
gg-op-setlog = 设置日志目标
gg-op-unsetlog = 移除日志目标
gg-op-config = 修改设置
gg-op-save = 保存内容
gg-op-remove = 移除内容
gg-op-panel = 打开面板
gg-review-details-above = 请求的完整内容位于紧接上方的消息中。
gg-warn-pending = 警告已保存，达到阈值的操作已在处理中。
gg-done = 已完成。
gg-setting-saved = 设置已保存。
    设置: { $setting }
gg-setting-value = 当前设置值：
    设置: { $setting }
    值: { $value }
gg-setting-invalid = 设置无效。请使用 on/off、有效模式或 10m 等时长。
gg-warning-settings = 警告设置：
    时长: { $duration }
    到期: { $expiry }
    上限: { $limit }
    模式: { $mode }
gg-admin-changed = 管理员操作已完成。
    操作: { $action }
    成员: { $user }
gg-admin-list = 公开管理员：
    { $admins }
gg-approved = 成员已获批准。
    原因: { $reason }
    成员: { $user }
gg-unapproved = 批准记录已移除。
    数量: { $count }
gg-approval-status = 成员批准状态：
    原因: { $reason }
    状态: { $status }
    成员: { $user }
gg-approval-list = 已批准成员：
    { $approvals }
gg-next-page = 更多条目：{ $command }
gg-range-invalid = 范围无效。请至少选择一条消息，且不超过指定上限。
    最大数量: { $cap }
gg-range-start = 已为你在此话题保存起点，有效十分钟。请回复末条消息使用 /purgeto。
gg-range-missing = 你在此处没有保存起点，请先回复消息使用 /purgefrom。
gg-content-needed = 请提供内容或回复内容，最多 3500 个字符。
gg-log-status = 日志设置：
    类别: { $categories }
    目标: { $destination }
gg-log-unverified = 我没有收到此频道命令的可验证原件。请先在频道发送 /setlog。
gg-log-forward = 请将此原始 /setlog 命令转发到群组。连接者必须有两个聊天的修改信息权限。
gg-info = 用户或聊天信息：
    ID: { $id }
    成员身份: { $membership }
    名称: { $name }
    用户名: { $username }
gg-op-unpinall = 取消所有置顶
gg-op-permapin = 永久置顶
gg-op-promote = 任命管理员
gg-op-demote = 移除管理员
gg-op-approve_user = 批准用户
gg-op-unapprove = 移除批准
gg-op-unapproveall = 移除全部批准
gg-unknown = 未知
gg-chat-id = 聊天 ID：
    ID: { $id }
gg-on = 启用
gg-off = 停用
gg-anon-enabled = 此处已信任匿名管理员。本群匿名命令使用机器人的权限，但不会识别真人。所有者操作仍需要验证当前创建者。/anonadmin off 可恢复真人审核。
gg-right-invite_users = 邀请用户
gg-right-promote_members = 任命管理员
gg-right-manage_topics = 管理话题
gg-right-creator = 群创建者
gg-log-join = 成员加入。
    成员: { $user }
gg-log-leave = 成员离开。
    成员: { $user }
gg-warning-row = 警告记录：
    到期: { $expiry }
    ID: { $id }
    原因: { $reason }
gg-menu-prompt = 请选择选项。
gg-content-invalid = 内容无效或超出 Telegram 限制。请检查名称、格式、修饰符和按钮。
gg-content-unavailable = 内容不可用，或你当前的群成员身份不允许访问。
gg-btn-private-note = 打开笔记
gg-open-private = 私聊打开此内容：
gg-items-cleared = 条目已清除。
    数量: { $count }
gg-clearall-confirm = 群创建者使用 <code>/{ $command } confirm</code> 确认。
gg-button-usage = 使用 <code>/button "标签" https://example.com</code>。添加 <code>"笔记" #名称 same</code> 可在同一行增加按钮。你会收到标记和可用预览。
gg-btn-accept-rules = 接受规则
gg-btn-open-verification = 打开验证
gg-captcha-private = 请打开私聊验证，以确认你的群成员身份。
    成员: { $user }
gg-captcha-choice = 请用按钮选择匹配的图片。模式和字符位置见下方。
    模式: { $mode }
    位置: { $position }
gg-captcha-settings = 验证设置：
    启用: { $enabled }
    移出: { $kick }
    模式: { $mode }
    解除: { $release }
    秒: { $seconds }
gg-captcha-dependency = 请先启用欢迎消息再启用验证。要求接受规则前，请先保存规则。
gg-val-text = 文字图片
gg-val-text2 = 字符图片
gg-captcha-attempts-exhausted = 错误次数过多，验证失败，已施加规定的限制。
gg-captcha-admin-exempt = 你已成为群管理员，验证已结束。
gg-captcha-question-text = 请选择图片中的词语。
gg-captcha-question-math = 请解答图片中的算式并选择答案。
gg-captcha-question-text2 = 请从左向右选择图片中指定位置的字符。
    位置: { $position }
gg-locktypes = 可用内容限制：
    类型: { $types }
gg-allowlist-title = 内容限制例外
gg-allowlist-invalid = 例外无效。请使用域名／路径、精确邀请、@聊天或 stickerpack:名称 等明确身份。
gg-reason-lock = 受限内容：
    类型: { $types }
gg-lock-applied = 内容限制规则已应用。
    原因: { $reason }
    类型: { $types }
gg-reaction-failed = 无法应用回应规则。此 Bot API 服务器可能不支持移除回应。
    代码: { $code }
gg-reaction-anonymous = 匿名回应统计没有用户 ID 或发送者聊天 ID。移除 API 需要此信息，因此不声称已移除。
gg-none = 无
gg-blocklist-title = 屏蔽列表
gg-blocklist-invalid = 触发条件、原因或操作无效。请检查引号、通配符转义及临时模式要求的时长。
gg-blocklist-settings = 屏蔽列表设置：
    删除: { $delete }
    模式: { $mode }
gg-blocklist-action = 已对成员应用屏蔽列表规则。
    原因: { $reason }
    成员: { $user }
gg-lock-album = 相册
gg-lock-anonchannel = 频道发送者
gg-lock-audio = 音频
gg-lock-bot = 机器人
gg-lock-button = 内联按钮
gg-lock-cashtag = 货币标记
gg-lock-checklist = 清单
gg-lock-cjk = 中文／日文／韩文文本
gg-lock-command = 命令
gg-lock-comment = 非成员评论
gg-lock-contact = 联系人
gg-lock-cyrillic = 西里尔文字
gg-lock-document = 文档
gg-lock-email = 电子邮件地址
gg-lock-emoji = 表情符号
gg-lock-emojicustom = 自定义表情
gg-lock-emojigame = 表情游戏
gg-lock-emojionly = 纯表情文本
gg-lock-externalreply = 外部回复
gg-lock-forward = 转发
gg-lock-forwarduser = 用户转发
gg-lock-forwardbot = 机器人转发
gg-lock-forwardchannel = 频道转发
gg-lock-forwardstory = 转发故事
gg-lock-game = 游戏
gg-lock-gif = GIF 动画
gg-lock-guestbot = 访客机器人
gg-lock-inline = 内联机器人
gg-lock-invitelink = Telegram 邀请
gg-lock-botlink = 机器人链接
gg-lock-location = 位置
gg-lock-outsidereaction = 非成员回应
gg-lock-phone = 电话号码
gg-lock-photo = 照片
gg-lock-poll = 投票
gg-lock-reaction = 回应
gg-lock-rtl = 从右向左文字
gg-lock-spoiler = 隐藏内容
gg-lock-sticker = 贴纸
gg-lock-stickeranimated = 动态贴纸
gg-lock-stickerpremium = 高级贴纸
gg-lock-text = 文本
gg-lock-url = URL
gg-lock-video = 视频
gg-lock-videonote = 视频消息
gg-flood-status = 刷屏限制：连续模式在 N 条触发，时间窗口超过 N 条触发。操作、时长和清理范围见下方。
    清理完整序列: { $clear }
    连续阈值: { $consecutive }
    数量: { $count }
    时长: { $duration }
    模式: { $mode }
    秒: { $seconds }
gg-raid-status = 批量入群保护。/antiraid on 启用，/antiraid off 停止。保护期限、封禁时长和每分钟自动阈值见下方。
    生效: { $active }
    自动阈值: { $auto }
    封禁时长: { $ban }
    周期: { $period }
    截止: { $until }
gg-raid-banned = 🛡 批量入群保护生效期间，成员已临时封禁。
    成员: { $user }
gg-raid-declined = 🛡 批量入群保护生效期间，入群请求已拒绝。
    成员: { $user }
gg-silent-consent-required = 选择此操作前，创建者必须允许静默操作并配置日志。
gg-btn-enable-raid = 启用批量入群保护
gg-human-required = 此操作需要可识别的真人。
gg-group-message-required = 请针对真实群消息或话题使用此命令。私聊消息 ID 不代表群消息。
gg-connection-private = 请在我们的私聊中使用此连接命令。
gg-connection-disconnected = 已断开。最近五个群组仍可用于重新连接。
gg-connection-current = 群组已连接。每次操作均验证当前成员身份及权限。
    群组: { $group }
gg-connection-none = 无有效连接。请使用 /connect GROUP_ID 或 /connect @群组。
gg-connection-open = 请在我们的私聊中打开你的个人连接。
gg-btn-connect = 私聊连接
gg-connection-history = 最近五个群组。请选择一个；需要当前成员身份。
gg-connection-unavailable = 连接不可用。你必须是当前真人成员，机器人必须是该群管理员。
gg-catalog-unresolved = /{ $command } 属于未定义操作的目录名称。请使用 /notes 或 /flood 获取已实现功能。
gg-cleanup-failed = 消息清理失败或不可用，不声称已删除。
gg-op-lock_change = 修改内容限制
gg-op-allowlist_change = 修改限制例外
gg-op-allowlist_clear = 清除限制例外
gg-op-blocklist_change = 修改屏蔽列表
gg-op-blocklist_clear = 清空屏蔽列表
gg-op-raid_change = 修改批量入群保护
gg-disabled-list = 命令策略：/disable 名称 和 /enable 名称 控制执行，/disabledel 控制删除，/disableadmin 将管理员纳入限制。
    命令: { $commands }
gg-cleanup-types = 可用清理类别：
    类型: { $types }
gg-cleanup-selected = 已选择清理类别：
    类型: { $types }
gg-advanced-status = 静默自动操作需要创建者同意及日志。机器人需要正常权限，默认审核变更。请在 BotFather 配置机器人之间的可见性。
    设置: { $setting }
    值: { $value }
gg-action-topic = 操作话题。/setactiontopic 选择当前论坛话题；常规话题 ID 为 1。
    话题: { $topic }
gg-topic-unavailable = 需要当前论坛及相应管理权限。
gg-topic-id-required = 在已连接的私聊中，请明确提供话题 ID。
gg-topic-general-delete = 不能删除常规话题。确认需要可识别的真人。
gg-topic-delete-confirm = 删除话题及消息？个人确认有效两分钟。
    话题: { $topic }
gg-btn-confirm-delete = 确认删除
gg-topic-changed = 话题操作已完成。
    操作: { $action }
    话题: { $topic }
gg-op-policy_change = 修改命令／清理策略
gg-op-topic_create = 创建话题
gg-op-topic_rename = 重命名话题
gg-op-topic_close = 关闭话题
gg-op-topic_reopen = 重新开启话题
gg-op-topic_delete = 删除话题及消息
gg-op-echo = 发送格式化内容
gg-broadcast-owner = 仅此机器人配置的运营者或子实例的真实所有者可向所属群组广播。
gg-broadcast-queued = 群组广播已排队。目标及结果按机器人隔离。
    ID: { $id }
gg-broadcast-busy = 另一个广播正在运行，或上次创建后的五分钟间隔尚未结束。
gg-broadcast-empty = 你在此机器人中没有群组广播。
gg-broadcast-status = 群组广播状态：
    已取消: { $cancelled }
    失败: { $failed }
    ID: { $id }
    已排队: { $queued }
    已送达: { $sent }
    状态: { $status }
    结果不确定: { $uncertain }
gg-fed-created = 联盟已创建。此 ID 属于本机器人的独立网络。
    ID: { $id }
    名称: { $name }
gg-fed-info = 联盟信息：
    管理员: { $admins }
    ID: { $id }
    日志: { $log }
    名称: { $name }
    通知: { $notifications }
    所有者: { $owner }
    必须提供原因: { $reasons }
gg-fed-list = 你拥有或管理的联盟：
    { $rows }
gg-fed-admins = 先列出所有者，再列出联盟管理员：
    { $rows }
gg-fed-quiet = 静默被动说明。封禁执行仍然生效。
    值: { $value }
gg-fed-policy = 封禁原因与所有者通知策略：
    通知: { $notifications }
    必须提供原因: { $reasons }
gg-fed-confirm-delete = 永久删除联盟、数据及成员关系？已有 Telegram 封禁保留。请在五分钟内进行个人确认。
    ID: { $id }
    名称: { $name }
gg-fed-confirm-log = 设置指定联盟日志？请在五分钟内确认。会重新验证你对目标的权限及机器人的发布权限。
    目标: { $destination }
    ID: { $id }
    名称: { $name }
gg-fed-confirm-sent = 个人确认已发送给联盟所有者。
gg-fed-deleted = 联盟已删除。已有 Telegram 封禁保留。
gg-fed-log-set = 联盟日志目标已设置：
    目标: { $destination }
gg-fed-cancel = 取消
gg-fed-cancelled = 已取消。
gg-fed-saved-delivery-failed = 变更已保存，但通知或日志未送达。请检查目标及机器人访问权限。
gg-fed-error-authority = 需要当前联盟所有者或相应联盟角色。Telegram 群权限不会赋予联盟权限。
gg-fed-error-private = 请在你与此机器人的个人私聊中使用此命令。
gg-fed-error-group = 请在真实群组中使用此命令。私聊连接不会选择联盟群组。
gg-fed-error-owned = 你已在此机器人中拥有联盟。请在私聊使用 /fedinfo、/renamefed 或 /delfed。
gg-fed-error-name = 请提供非空且无控制字符的名称。名称限制为 64 个字符。
gg-fed-error-id = 请提供此机器人的有效联盟 UUID。Rose 的 ID 不会连接到我们的独立服务。
gg-fed-error-missing = 此机器人或上下文中未找到联盟。
gg-fed-error-creator = 只有当前 Telegram 群创建者可以将群加入联盟或退出联盟。
gg-fed-error-target = 请提供正数真人 ID、回复真人的消息或当前已验证的用户名。所有者不能被降职。
gg-fed-error-value = 联盟参数无效。策略请使用 on/off，需要 ID 时请提供有效 ID。
gg-fed-error-stale = 确认已过期、使用过，或联盟、所有者、目标已改变。请重新请求。
gg-fed-error-destination = 所有者必须是目标的当前管理员，机器人必须能够发布。频道需要 post_messages 权限。
gg-fed-error-delivery = 个人确认未送达或未绑定。请开启与机器人的私聊后重试。
gg-fed-event = 联盟事件：
    事件: { $event }
    ID: { $id }
    名称: { $name }
    成员: { $user }
gg-fed-event-rename = 名称已修改
gg-fed-event-delete = 已删除；Telegram 封禁保留
gg-fed-event-promote = 管理员已添加
gg-fed-event-demote = 管理员已移除
gg-fed-event-self-remove = 管理员已辞任
gg-fed-event-reason = 封禁原因策略已修改
gg-fed-event-notif = 所有者通知已修改
gg-fed-event-log = 日志目标已修改
gg-fed-event-unlog = 日志目标已移除
gg-fed-event-ban = 封禁策略已保存，执行已排队
gg-fed-event-unban = 封禁策略已移除，自有约束解除已排队
gg-fed-event-subscribe = 订阅已添加，已观察用户的核查已排队
gg-fed-event-unsubscribe = 订阅已移除，其他来源保留
gg-fed-ban-details = 封禁目标及原因：
    原因: { $reason }
    成员: { $user }
gg-fed-passive = 联盟策略封禁此成员。来源与原因见下方。
    ID: { $id }
    原因: { $reason }
    来源: { $source }
    成员: { $user }
gg-fed-enforce-failed = 联盟策略封禁此成员，但移出失败。请检查机器人权限。来源与原因见下方。
    ID: { $id }
    原因: { $reason }
    来源: { $source }
    成员: { $user }
gg-fed-stat = 此成员的联盟封禁：
    { $rows }
    成员: { $user }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — 生效：{ $status }；变更：{ $date }。
gg-fed-stat-more = 还有更多来源。请使用继续命令，或提供具体联盟 ID 查看原因与日期。
gg-fed-intent-saved = 策略已保存，已观察的目标已排队。执行前会核查当前权限及其他约束来源。
    成员: { $user }
    版本: { $version }
gg-fed-subscriptions = 联盟封禁的直接订阅：
    { $rows }
gg-fed-imported = 条目已验证并保存，完全相同的重复项已跳过。对已观察目标的执行已排队。
    数量: { $count }
    完全相同的重复项: { $duplicates }
gg-fed-event-import = 已导入验证过的封禁，执行已排队
gg-fed-error-file-format = 请回复含 id/reason 的 UTF-8 CSV、含 user_id 的 JSONL/NDJSON，或本机器人的 JSON 数组导出。任意无效行均阻止所有写入。
gg-fed-error-file-limit = 最多 2 MiB、1000 条。缺失或过大的文件将拒绝；不会静默截断列表。
gg-fed-error-file-duplicate = 同一用户 ID 存在冲突条目，未导入封禁。
gg-fed-error-file-rate = 每个联盟的导入与导出共用 30 分钟间隔，请稍后重试。
gg-fed-error-reason = 封禁原因最长 1024 个字符，不能包含不支持的控制字符。
gg-fed-error-reason_required = 此联盟要求每条封禁提供非空原因。
gg-fed-error-cycle = 联盟不能订阅自身或形成有向循环。
gg-fed-error-graph_limit = 已达到上限：32 个直接目标、128 个可达联盟、深度 16，或此机器人中 10 000 条连接。
gg-data-confirm = 请在五分钟内确认。会重新验证当前创建者及群版本。只修改选择的模块；身份、信任及生效封禁均保留。
    SHA-256: { $digest }
    群组: { $group }
    模块: { $modules }
    操作: { $operation }
gg-data-import = 导入群模块
gg-data-reset = 重置群模块
gg-data-privacy-delete = 删除此机器人的可选个人数据
gg-data-confirm-button = 确认此变更
gg-data-personal = 请在个人私聊中打开确认。
gg-data-saved = 所选模块已保存。
gg-data-error-authority = 导入和重置需要当前可识别的群创建者，导出需要当前管理员。
gg-data-error-format = 请回复 /export 创建的带版本且有效的 Group Guard JSON。
gg-data-error-limit = 文件超出大小或已配置的内容上限。
gg-data-error-version = 不支持此格式或版本，未应用变更。
gg-data-error-module = 请选择已知模块：/export all 或 /export notes rules。导入和重置使用相同名称。
gg-data-error-field = 模块字段缺失或无效，未应用设置。
gg-data-error-item = 内容、选项或重复访问权限无效，未保存内容。
gg-data-error-media = 媒体必须上传至此机器人并可通过 getFile 获取。不支持其他机器人的文件 ID。
gg-data-error-destination = 日志及话题目标需要当前权限及机器人能力。话题 ID 仅适用于同一群组。
gg-data-error-language = 请使用 /setlang 选择已安装的语言。
gg-data-error-stale = 确认已过期、修改或使用，请重新开始。
gg-data-error-restore = 无法安全恢复自有临时限制。证据保留，请检查机器人权限。
gg-data-error-rate = 群数据操作采用本地五分钟间隔，请稍后重试。
gg-data-error-delivery = 私聊确认未送达，请开启与机器人的私聊后重试。
gg-data-error-saved_delivery = 设置已保存，但命令建议未更新。请检查机器人权限。
gg-privacy-policy = <b>你在此 Group Guard 中的数据</b>
    /privacy data 导出个人连接、已观察资料、警告、批准、约束／验证状态、联盟所有权／角色／封禁及安全任务。不包含他人的私密内容、验证答案、认证信息和原始上传文件。请使用继续命令获取后续页面。
    /privacy delete 移除可选连接历史、已观察姓名／用户名、未生效的验证以及此机器人中你已完成广播的内容。生效警告／约束、封禁版本、角色、所有权、订阅、防重放记录及不确定 API 操作保留安全与排序所需的最少标识。退出或删除联盟关系请使用相应明确命令。共享平台资料及其他机器人数据不变。
    运营者单独管理备份与审计。此命令不会删除外部 Telegram 消息或备份，也不承诺自动保留期限。
gg-privacy-usage = /privacy policy · /privacy data [继续游标] · /privacy delete — 仅限你与此机器人的个人私聊。
gg-privacy-private = 此操作需要请求人的个人私聊。无效游标不会提供他人数据访问权限。
gg-privacy-next = 下一页数据：/privacy data { $cursor }
gg-privacy-deleted = 此机器人的可选个人数据已移除。生效安全、所有权及不确定操作保留最少标识，详见 /privacy policy。
gg-language-usage = 请用 /setlang 选择群语言。私聊 /lang 修改个人平台语言。可用代码见下方。
    语言代码: { $codes }
gg-language-saved = 群回复语言已修改。
gg-help-index = <b>Group Guard 命令指南</b>
    /help 分类 · /help 命令 · /help 分类 2。标明的命令也可通过已验证的 /connect 使用；私聊回复保留在真实私聊中。
    设置需要修改信息权限，制裁需要限制成员权限，删除需要删除权限，置顶需要置顶权限，任命需要提升管理员权限，话题需要管理话题权限。机器人权限单独核查。所有者操作需要当前真人创建者。/settings 打开个人群设置面板。
gg-help-search = <b>匹配的命令</b>
    搜索: { $query }
gg-help-connected = 群组或已验证连接；所需权限见分类
gg-help-group-only = 需要真实群消息
gg-help-unsupported = 保留目录名称；未定义的行为返回说明
gg-help-next = 下一页
gg-help-previous = 上一页
gg-help-family-title-moderation = 管理与批准
gg-help-family-title-messages = 删除和置顶消息
gg-help-family-title-logging = 授权日志
gg-help-family-title-settings = 群设置和语言
gg-help-family-title-content = 笔记、过滤器、规则和欢迎消息
gg-help-family-title-captcha = 新成员验证
gg-help-family-title-locks = 内容限制与例外
gg-help-family-title-blocklists = 屏蔽列表匹配与操作
gg-help-family-title-antispam = 刷屏与批量入群保护
gg-help-family-title-connections = 私聊群连接
gg-help-family-title-identity = 用户和聊天信息
gg-help-family-title-policy = 命令与机器人策略
gg-help-family-title-cleanup = 命令、机器人和服务消息清理
gg-help-family-title-topics = 论坛话题
gg-help-family-title-utilities = 内容发送与运营者广播
gg-help-family-title-federations = 联盟角色、封禁和订阅
gg-help-family-title-portability = 群文件与个人数据
gg-help-family-title-discovery = 帮助与内容编辑器
gg-help-family-moderation = <b>管理</b> · 回复、数字 ID 或已验证的 @用户。/ban 20 原因；/tban 20 60s 原因；/mute 20；/tmute 20 2h 原因。临时制裁：60 秒至 365 天。/kickme 仅移出自己。d 变体删除回复的消息；s 变体删除命令／回复并需要删除权限。管理员受保护。/setwarnlimit 3；/setwarnmode ban；/setwarntime 1d。新群默认三条警告，旧设置保留。/approve 仅豁免普通内容／刷屏保护，不豁免联盟／CAS／批量入群／手动操作。/promote 不超过请求人与机器人的共同权限。批量重置需要创建者。
gg-help-family-messages = <b>消息</b> · /del 需要真实群内回复。/purge 从该消息开始；/purgefrom 和 /purgeto 保存边界。受配置上限与 Telegram 规则限制；批次确认不代表精确删除数量。/pin [loud]、/permapin、/unpin、/unpinall 需要置顶权限，全部取消置顶需要创建者。/antichannelpin 和 /cleanlinked 控制关联频道自动消息。
gg-help-family-logging = <b>日志</b> · /setlog -100… 需要目标当前管理权限及机器人发布权限。转发配置必须对应实际收到的原始命令。/logcategories：settings/admin/user/automated/reports/other；/log 和 /nolog 选择类别。日志发送失败仍有记录，不能据此声称操作成功。
gg-help-family-settings = <b>设置</b> · /settings 打开个人有效期面板，核查当前修改信息权限。/setlang 代码 保存群语言；私聊 /lang 保存个人语言。/night 23 7 +3 夜间关闭群组；/night off 仅恢复仍然匹配的机器人自有权限快照，尊重外部变更。
gg-help-family-content = <b>编辑器</b> · /save 单词 文本 或回复媒体；/get 单词、#单词、/notes 读取笔记。新笔记名为单个词，旧有更宽名称保留。/filter "短语" 文本、/filterprefix、/filterexact 选择匹配模式；/stop 删除指定键。/clearall 和 /stopall 需要创建者确认。Rose 格式支持粗体／斜体／下划线／删除线／代码、链接、引用与 %%% 随机备选。字段：{ "{" }first{ "}" }、{ "{" }last{ "}" }、{ "{" }fullname{ "}" }、{ "{" }username{ "}" }、{ "{" }mention{ "}" }、{ "{" }id{ "}" }、{ "{" }chatname{ "}" }、{ "{" }count{ "}" }。/button 创建 URL／笔记／规则按钮。通用选项 preview/nonotif/protect/mediaspoiler；笔记 admin/private/noprivate/repeat；过滤器 user/allow_bot/replytag/command。/save 单词 你好 { "{" }repeat 5m{ "}" } 只定期发送公开内容，并核查作者当前权限。规则、欢迎和私密内容使用相同渲染器。媒体 ID 属于机器人。
gg-help-family-captcha = <b>验证</b> · /captcha on/off；/captchamode off/button/math/text/text2；/setcaptchatext；/captcharules on；/captchakick on/off；/captchakicktime 和 /captchamutetime 设置有界期限。已发挑战保留代次和截止时间。入群请求需要 invite-users，禁言需要 restrict-members。答案个人绑定且一次有效。联盟封禁优先于批准／CAPTCHA。
gg-help-family-locks = <b>内容限制</b> · /lock links [操作]、/unlock 类型；/locktypes 显示真实类型，/locks 显示状态。/lockwarns 控制警告。/allowlist 支持域名／路径、精确邀请、@聊天或 stickerpack:/forward:/inline:/channel:/chat:/bot:/command:。无效模式拒绝。例外仅适用于匹配内容；静默自动操作需要创建者同意与授权日志。
gg-help-family-blocklists = <b>屏蔽列表</b> · /addblocklist "短语" 支持文本／前缀／精确匹配和明确身份，可附原因／操作。/rmblocklist 精确移除选择的键。/blocklistmode nothing/warn/kick/ban/tban/mute/tmute 指定操作，临时模式必须提供时长。/blocklistdelete 单独控制删除。通配符复杂度有限，无效条目及超限均拒绝。
gg-help-family-antispam = <b>刷屏与批量入群</b> · /setflood 数量 设置连续阈值；/setfloodtimer 数量 时长 设置时间窗口；/setfloodmode 设置制裁／时长；/clearflood 设置序列清理。旧设置保留。/flood 和 /antiflood 显示策略，别名属于本地兼容选择。/antiraid on/off/duration、/raidtime、/raidactiontime、/autoantiraid 保存保护期限与独立新成员制裁。优先于批准／CAPTCHA，按代次到期并可恢复重启前状态。
gg-help-family-connections = <b>连接</b> · /connect groupID 或个人连接。核查你与机器人的成员身份，变更仍需要精确当前权限。/connection 显示选中群；/disconnect 移除；/connect 显示可继续查看的历史。连接不授予联盟所有权或运营者权限。
gg-help-family-identity = <b>信息</b> · /id 显示真实用户／聊天／来源 ID；/info 显示当前目标。回复与 @用户名需要此机器人作用域内的当前证据。匿名群消息不能识别真人，不会虚构真人 ID。
gg-help-family-policy = <b>策略</b> · /disable 命令、/enable 命令、/disabled、/disableable 使用规范名及别名。/disableadmin 控制管理员例外，/disabledel 控制删除。恢复命令始终可用。/bot2bot off/admin/all 核查真实成员身份，默认变更需真人审核。/bot2botskipreview 仅限创建者。/silentactions 需要同意与授权日志。未定义的 runs/saved 返回说明。
gg-help-family-cleanup = <b>清理</b> · /cleancommand admin/user/other 与 /keepcommand 选择命令类别。/cleanmsg action/filter/note 与 /keepmsg 仅针对本机器人实际发送的消息，发送凭证与五分钟任务避免猜测 ID。/cleanservice 与 /nocleanservice：join/leave/other/photo/pin/title/videochat。先进行功能处理与有效付款处理，再清理。
gg-help-family-topics = <b>话题</b> · /newtopic 名称、/renametopic 名称、/closetopic、/reopentopic 操作真实当前话题。/deletetopic 需要创建者确认；/setactiontopic 选择同群目标。需要 Telegram 论坛及 manage-topics 权限。缺失／不支持的话题报告真实错误。
gg-help-family-utilities = <b>工具</b> · /echo 与 /say 通过共享有界渲染器发送直接或回复内容。/broadcast 仅限配置运营者或实际子实例所有者，仅覆盖此机器人配置的群组。各目标保留部分／不确定投递结果，查询状态与取消不会重复成功附件。
gg-help-family-federations = <b>联盟</b> · /newfed 名称 在此机器人创建 UUID。私聊命令使用自己的联盟，与群连接无关；读取 UUID 不授予角色。/fedpromote、/feddemote 管理管理员；/feddemoteme 辞任。/joinfed UUID 和 /leavefed 需要当前群创建者。删除不自动解除 Telegram 封禁。/fban userID 原因 和 /unfban userID 需要联盟所有者／管理员；/fedreason、/fednotif、/setfedlog 需要所有者。/quietfed 仅隐藏被动说明。/subfed UUID 有向、有界且无环。/fedstat [userID]、/fbanstat UUID 显示来源／状态。/fbanlist csv/minicsv/json 仅限所有者并采用共同 30 分钟间隔；/importfbans 回复有界 CSV 或真正逐行 JSON，并明确支持自身 JSON 数组。只核查实际观察的用户，不声称有完整成员清单。
gg-help-family-portability = <b>文件与隐私</b> · /export all 或模块 需要管理员；/import 与 /reset 需要当前真人创建者，并进行个人一次性五分钟确认。本地五分钟间隔；自身带版本 JSON，最多 2MiB，遵守配置内容上限。模块：moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions。未选择模块保留。不导入信任、已发挑战／任务、订阅、角色或生效封禁。/privacy policy/data/delete 仅在个人私聊使用，支持分页且保留最少安全信息。没有经过验证的完整 Rose 导出适配器。
gg-help-family-discovery = <b>帮助</b> · /help 显示分类；/help 命令 搜索名称／别名；/help 分类 2 继续。/button 帮助编辑按钮标记。每份指南说明上下文、权限、默认行为及上限。/settings 打开个人群设置面板。
gg-data-error-cache_pending = 可选 SQL 数据已移除。缓存不可用，其清理已排队；生效安全记录保留。
