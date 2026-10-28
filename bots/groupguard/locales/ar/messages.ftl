## حارس المجموعات — العربية.
group-welcome =
    🛡 <b>شكراً لإضافتي!</b>

    اجعلني <b>مشرفاً</b> (حذف الرسائل، حظر الأعضاء، التثبيت) لأحمي المجموعة،
    ثم أرسل /settings لضبط التحقق ومكافحة التكرار والأقفال وغيرها.
gg-start =
    🛡 أهلاً <b>{ $name }</b>! أنا <b>حارس المجموعات</b> — أحافظ على مجموعتك نظيفة وآمنة.

    • 🤖 تحقق للأعضاء الجدد، ومنع البوتات، وقاعدة CAS لمكافحة السبام
    • 🌊 مكافحة التكرار، 🔒 أقفال (روابط، تحويلات، وسائط…)، 🚫 كلمات محظورة
    • 🔨 /ban /mute /kick /warn مع مدة، و /purge
    • 📝 ملاحظات، 🔁 ردود تلقائية، 📜 قوانين، 👋 ترحيب مخصص
    • 🌙 الوضع الليلي، 🧠 كشف السبام بالذكاء الاصطناعي، 📒 قناة سجل

    أضفني إلى مجموعتك واجعلني مشرفاً 👇
gg-help =
    📖 <b>الأوامر</b> (داخل المجموعات)

    <b>الإشراف</b> — رد على رسالة أو اكتب @المعرف / الرقم:
    /ban [10m|2h|3d] [السبب] · /unban · /kick · /mute [المدة] · /unmute
    /warn [السبب] · /unwarn · /warns · /resetwarns
    /purge (بالرد: حذف كل ما بعدها) · /del · /pin [loud] · /unpin
    /report (بالرد) — استدعاء المشرفين · /id

    <b>المحتوى</b>
    /rules · /setrules النص · /setwelcome النص · /resetwelcome
    المتغيرات: <code>{"{"}first{"}"}</code> <code>{"{"}mention{"}"}</code> <code>{"{"}group{"}"}</code> <code>{"{"}count{"}"}</code>
    /save اسم نص (أو بالرد) · #اسم · /notes · /clear اسم
    /filter كلمة نص (أو بالرد) · /filters · /stop كلمة

    <b>الحماية</b>
    /lock links forwards media … · /unlock · /locks
    /addblock كلمة، كلمة · /rmblock كلمة · /blocklist
    /night 23 7 +3 (إغلاق المجموعة ليلاً) · /night off
    /setlog -100… (قناة السجل) · /settings — لوحة الإعدادات
gg-welcome-default = 👋 أهلاً { "{" }mention{ "}" } في <b>{ "{" }group{ "}" }</b>!
gg-credit = 🛡 محمية بواسطة @{ $bot }
gg-btn-add = ➕ أضفني إلى مجموعتك
gg-btn-commands = 📖 الأوامر
gg-btn-rules = 📜 القوانين
gg-btn-human = ✅ أنا إنسان
gg-btn-unwarn = ↩️ إزالة التحذير (للمشرفين)
gg-btn-locks = 🔒 الأقفال ({ $count })
gg-btn-open-settings = ⚙️ فتح الإعدادات
gg-btn-admin-tab = 🛡 المجموعات
gg-captcha = 🤖 { $user }، أكّد أنك إنسان خلال <b>{ $minutes } دقيقة</b> وإلا ستُزال من المجموعة.
gg-captcha-button = اضغط الزر بالأسفل 👇
gg-captcha-math = كم يساوي <b>{ $a } + { $b }</b>؟
gg-captcha-not-you = هذا الزر ليس لك 🙂
gg-captcha-ok = ✅ أهلاً بك!
gg-captcha-wrong = ❌ إجابة خاطئة. تبقّت { $left } محاولات.
gg-captcha-failed = ❌ محاولات خاطئة كثيرة.
gg-captcha-passed = ✅ تم التحقق من { $user } — أهلاً بك!
gg-cas-banned = 🚫 { $user } مرسل سبام معروف (CAS) وتم حظره.
gg-join-request = 👋 للانضمام إلى <b>{ $group }</b>، أكّد أنك إنسان:
gg-join-approved = ✅ تم قبولك! أهلاً بك.
gg-join-expired = ⌛ انتهت صلاحية الطلب — أرسل طلب انضمام جديداً.
gg-goodbye = 👋 غادر { $user } المجموعة.
gg-flood-mute = 🌊 { $user } كان يكرر الرسائل وتم كتمه مؤقتاً.
gg-flood-kick = 🌊 { $user } كان يكرر الرسائل وتمت إزالته.
gg-flood-ban = 🌊 { $user } كان يكرر الرسائل وتم حظره.
gg-newbie-links = 🆕 { $user }، لا يمكن للأعضاء الجدد نشر روابط خلال أول { $hours } ساعة.
gg-spam-banned = 🧠 نشر { $user } رسائل سبام وتم حظره.
gg-reason-blocklist = كلمة محظورة
gg-need-right = ⛔ تحتاج صلاحية المشرف «{ $right }» لهذا الأمر.
gg-right-admin = مشرف
gg-right-restrict = حظر المستخدمين
gg-right-delete = حذف الرسائل
gg-right-pin = تثبيت الرسائل
gg-right-change_info = تغيير معلومات المجموعة
gg-admins-only = ⛔ للمشرفين فقط.
gg-need-target = 👤 رد على رسالة، أو اكتب @المعرف أو رقم المستخدم.
gg-target-admin = 🙅 لا يمكنني فعل ذلك مع مشرف.
gg-bot-no-rights = ⚠️ أحتاج أن أكون مشرفاً بالصلاحيات المناسبة لفعل ذلك.
gg-banned = 🔨 تم حظر { $user }. السبب: { $reason }
gg-banned-for = 🔨 تم حظر { $user } لمدة { $time }. السبب: { $reason }
gg-unbanned = ✅ أُلغي حظر { $user }.
gg-kicked = 👢 تم طرد { $user }. السبب: { $reason }
gg-muted = 🔇 تم كتم { $user }. السبب: { $reason }
gg-muted-for = 🔇 تم كتم { $user } لمدة { $time }. السبب: { $reason }
gg-unmuted = 🔊 يمكن لـ { $user } الكتابة مجدداً.
gg-warned = ⚠️ تم تحذير { $user } ({ $count }/{ $limit }). السبب: { $reason }
gg-warn-limit-ban = 🔨 وصل { $user } إلى { $limit } تحذيرات وتم حظره.
gg-warn-limit-mute = 🔇 وصل { $user } إلى { $limit } تحذيرات وتم كتمه.
gg-warn-limit-kick = 👢 وصل { $user } إلى { $limit } تحذيرات وتم طرده.
gg-unwarned = ↩️ أُزيل تحذير من { $user } ({ $count }/{ $limit }).
gg-warn-removed = ↩️ أزال { $admin } التحذير.
gg-warns = ⚠️ لدى { $user } ‏{ $count }/{ $limit } تحذيرات.
gg-warns-reset = 🧽 تم تصفير تحذيرات { $user }.
gg-purge-reply = 🧹 رد على أول رسالة تريد حذفها.
gg-purged = 🧹 حُذفت { $count } رسالة.
gg-pin-reply = 📌 رد على الرسالة التي تريد تثبيتها.
gg-report-reply = 🚨 رد على الرسالة التي تريد الإبلاغ عنها.
gg-reported = 🚨 تم إبلاغ المشرفين عن { $user }.
gg-setlog-usage = 📒 الاستخدام: أضفني مشرفاً في قناة السجل، ثم <code>/setlog -100…</code> (رقم القناة).
gg-setlog-failed = ⚠️ لا أستطيع النشر هناك. أضفني مشرفاً أولاً.
gg-setlog-done = 📒 تم ربط قناة السجل.
gg-setlog-off = 📒 تم فصل قناة السجل.
gg-log-connected = 📒 هذه المحادثة تستقبل الآن سجل الإشراف لـ <b>{ $group }</b>.
gg-log-flood = 🌊 تكرار: { $user } ← { $action }
gg-log-report = 🚨 بلاغ عن { $user }
gg-log-spam =
    🧠 حظر سبام بالذكاء الاصطناعي: { $user }
    <blockquote>{ $text }</blockquote>
gg-rules =
    📜 <b>القوانين</b>

    { $rules }
gg-no-rules = 📜 لم تُضبط قوانين بعد. للمشرفين: /setrules القوانين
gg-rules-saved = 📜 تم حفظ القوانين.
gg-rules-cleared = 📜 تم مسح القوانين.
gg-welcome-usage = 👋 الاستخدام: <code>/setwelcome أهلاً {"{"}mention{"}"} في {"{"}group{"}"}!</code> (أو بالرد على رسالة)
gg-welcome-saved = 👋 تم حفظ رسالة الترحيب.
gg-welcome-reset = 👋 أُعيدت رسالة الترحيب للافتراضية.
gg-note-usage = 📝 الاستخدام: <code>/save اسم نص</code>، أو بالرد على رسالة بـ <code>/save اسم</code>.
gg-filter-usage = 🔁 الاستخدام: <code>/filter كلمة نص الرد</code>، أو بالرد على رسالة بـ <code>/filter كلمة</code>.
gg-note-saved = 📝 تم الحفظ — يمكن لأي عضو عرضها بـ <code>#{ $key }</code>.
gg-filter-saved = 🔁 سأرد كلما قال أحدهم «{ $key }».
gg-notes-empty = 📝 لا توجد ملاحظات بعد.
gg-filters-empty = 🔁 لا توجد ردود تلقائية بعد.
gg-notes-list = 📝 <b>الملاحظات</b>
gg-filters-list = 🔁 <b>الردود التلقائية</b>
gg-item-deleted = 🗑 تم حذف «{ $key }».
gg-item-missing = 🤷 لا يوجد شيء محفوظ بهذا الاسم.
gg-items-limit = 📦 وصلت المجموعة للحد الأقصى من الملاحظات والردود.
gg-lock-usage = 🔒 الاستخدام: <code>/lock links</code> — الأنواع: { $types } (أو <code>all</code>)
gg-locked = 🔒 تم قفل: { $types }
gg-unlocked = 🔓 تم فتح: { $types }
gg-locks-title = 🔒 <b>الأقفال</b>
gg-locks-panel = 🔒 <b>الأقفال</b> — يُحذف المحتوى المقفل (المشرفون مستثنون).
gg-lock-links = الروابط
gg-lock-invites = روابط الدعوة
gg-lock-forwards = التحويلات
gg-lock-media = الوسائط
gg-lock-stickers = الملصقات
gg-lock-gifs = الصور المتحركة
gg-lock-voice = الصوتيات
gg-lock-polls = الاستطلاعات
gg-lock-bots = البوتات
gg-blocklist = 🚫 <b>الكلمات المحظورة</b>: { $words }
gg-blocklist-empty = 🚫 لا توجد كلمات محظورة.
gg-blocklist-usage = 🚫 الاستخدام: <code>/addblock كلمة، عبارة أخرى</code> · <code>/rmblock كلمة</code>
gg-blocklist-saved = 🚫 تم تحديث القائمة ({ $count } كلمة).
gg-night-usage = 🌙 الاستخدام: <code>/night 23 7 +3</code> (من 23:00 إلى 07:00، UTC+3) · <code>/night off</code>
gg-night-on = 🌙 الوضع الليلي: تُغلق المجموعة من { $start } إلى { $end } ({ $tz }).
gg-night-off = 🌙 تم إيقاف الوضع الليلي.
gg-night-start = 🌙 تصبحون على خير! المجموعة مغلقة حتى { $end }.
gg-night-end = ☀️ صباح الخير! فُتحت المجموعة من جديد.
gg-panel =
    ⚙️ <b>الإعدادات — { $group }</b>

    اضغط أي خيار لتغييره. ساعات الوضع الليلي: { $night } (غيّرها بـ /night في المجموعة).
gg-panel-sent = 📬 أرسلت لك الإعدادات في الخاص.
gg-panel-start-first = 📬 ابدأ محادثة خاصة معي أولاً، ثم اضغط بالأسفل:
gg-credit-vip = 💎 إخفاء سطر «محمية بواسطة» ميزة VIP (/vip في الخاص).
gg-opt-wel = 👋 الترحيب: { $value }
gg-opt-cln = 🧹 حذف رسائل الانضمام: { $value }
gg-opt-bye = 👋 الوداع: { $value }
gg-opt-cap = 🤖 التحقق: { $value }
gg-opt-cpm = ⏱ مهلة التحقق: { $value } د
gg-opt-fld = 🌊 حد التكرار: { $value }
gg-opt-fla = 🌊 التكرار ← { $value }
gg-opt-wrn = ⚠️ حد التحذيرات: { $value }
gg-opt-wra = ⚠️ التحذيرات ← { $value }
gg-opt-act = ⏳ مدة الكتم/الحظر التلقائي: { $value } د
gg-opt-cas = 🛡 قاعدة CAS: { $value }
gg-opt-nwb = 🆕 منع روابط الجدد: { $value } س
gg-opt-ais = 🧠 كشف السبام الذكي: { $value }
gg-opt-ngt = 🌙 الوضع الليلي: { $value }
gg-opt-crd = 🏷 سطر الحماية: { $value }
gg-opt-lang = 🌐 اللغة: { $value }
gg-val-button = زر
gg-val-math = حساب
gg-val-off = متوقف
gg-val-mute = كتم
gg-val-kick = طرد
gg-val-ban = حظر
gg-adm =
    🛡 <b>حارس المجموعات</b>

    • المجموعات المحمية: <b>{ $groups }</b>
    • التحذيرات الصادرة: <b>{ $warns }</b>
    • الملاحظات والردود: <b>{ $items }</b>
cmd-settings = إعدادات المجموعة (داخل مجموعة)
cmd-help = الأوامر

# Phase 1A authorization, review and truthful action outcomes
gg-auth-denied = تعذر التحقق من الصلاحيات. لم يتغير شيء.
gg-target-invalid = اختر عضواً بشرياً معروفاً. تعذر التحقق من الهدف.
gg-duration-invalid = استخدم مدة صحيحة من 60s إلى 365d. الأوامر المؤقتة تتطلب مدة.
gg-reason-invalid = يجب ألا يتجاوز السبب 256 حرفاً.
gg-outcome-failed = فشل الإجراء المطلوب أو تعذر التحقق من صلاحياته.
gg-outcome-partial = اكتمل الإجراء جزئياً فقط. قد يبقى الحظر إذا فشلت استعادة الطرد.
gg-outcome-ancillary = اكتمل الإجراء الأساسي، لكن فشلت خطوة مرتبطة به.
gg-review-request = مراجعة: <b>{ $operation }</b>
    الهدف: { $target }
    التفاصيل: { $details }
    المدة بالثواني: { $duration }
    يمكن لشخص مخوّل حالياً الموافقة خلال 120 ثانية.
gg-review-approve = الموافقة على هذا الإجراء
gg-review-unavailable = تخزين المراجعة غير متاح. أرسل أمراً جديداً.
gg-review-expired = هذه المراجعة منتهية أو غير صالحة أو استُخدمت بالفعل.
gg-review-consumed = استُخدمت هذه المراجعة. تحقق من نتيجة الإجراء؛ أرسل أمراً جديداً لإعادة المحاولة.
gg-duration-permanent = دائم / بلا مؤقت
gg-purge-ack = طُلب حذف { $requested } معرّف رسالة؛ أكدت الواجهة استلام { $acknowledged }. عدد الرسائل المحذوفة فعلياً غير معروف.
gg-warning-removed = أُزيل الإنذار.
gg-op-ban = حظر
gg-op-mute = كتم
gg-op-kick = طرد
gg-op-unban = إلغاء الحظر
gg-op-unmute = إلغاء الكتم
gg-op-warn = إنذار
gg-op-unwarn = إزالة الإنذار
gg-op-resetwarns = مسح الإنذارات
gg-op-purge = حذف دفعة
gg-op-delete = حذف
gg-op-pin = تثبيت
gg-op-unpin = إلغاء التثبيت
gg-op-setlog = تعيين سجل
gg-op-unsetlog = إلغاء السجل
gg-op-config = إعدادات
gg-op-save = حفظ
gg-op-remove = إزالة
gg-op-panel = فتح لوحة الإعدادات
gg-review-details-above = يظهر المحتوى المطلوب كاملاً مباشرةً أعلاه.
gg-warn-pending = سُجّل الإنذار؛ يجري تنفيذ إجراء حد الإنذارات بالفعل.

gg-done = تم التنفيذ.

gg-setting-saved = تم حفظ الإعداد { $setting }.

gg-setting-value = { $setting }: { $value }

gg-setting-invalid = إعداد غير صالح. استخدم on/off أو وضعاً صالحاً أو مدة مثل 10m.

gg-warning-settings = الإنذارات: الحد { $limit }؛ الوضع { $mode }؛ مدة العقوبة { $duration }؛ انتهاء الإنذار { $expiry }.

gg-admin-changed = تم تنفيذ { $action } للمستخدم { $user }.

gg-admin-list = المشرفون الظاهرون:
    { $admins }

gg-approved = تم اعتماد { $user }. السبب: { $reason }

gg-unapproved = تم حذف { $count } اعتماداً.

gg-approval-status = اعتماد { $user }: { $status }. السبب: { $reason }

gg-approval-list = المستخدمون المعتمدون:
    { $approvals }

gg-next-page = المزيد: { $command }

gg-range-invalid = نطاق غير صالح. اختر من 1 إلى { $cap } معرّف رسالة.

gg-range-start = تم حفظ البداية لك في هذا الموضوع لمدة 10 دقائق. رد بـ /purgeto على الرسالة الأخيرة.

gg-range-missing = لم تُحفظ بداية لك في هذا الموضوع. رد بـ /purgefrom أولاً.

gg-content-needed = أرسل محتوى أو رد على محتوى (حتى 3500 حرف).

gg-log-status = وجهة السجل: { $destination }. الفئات المفعلة: { $categories }.

gg-log-unverified = لا يوجد إيصال موثّق لأمر القناة الأصلي. أرسل /setlog في القناة أولاً.

gg-log-forward = أعد توجيه أمر /setlog الأصلي إلى مجموعتك. يجب أن يمتلك المشرف حق تغيير المعلومات في المحادثتين.

gg-info = الاسم: { $name }
    اسم المستخدم: { $username }
    المعرّف: <code>{ $id }</code>
    العضوية: { $membership }

gg-op-unpinall = إلغاء جميع المثبتات

gg-op-permapin = إرسال وتثبيت

gg-op-promote = ترقية

gg-op-demote = تنزيل

gg-op-approve_user = اعتماد

gg-op-unapprove = إلغاء اعتماد

gg-op-unapproveall = إلغاء جميع الاعتمادات

gg-unknown = غير معروف

gg-chat-id = معرّف المحادثة: <code>{ $id }</code>

gg-on = مفعّل
gg-off = معطّل

gg-anon-enabled = تم تفعيل افتراض صلاحيات المشرف المجهول في هذه المجموعة. تستخدم الأوامر المجهولة صلاحيات البوت دون تحديد إنسان. تظل إجراءات المالك بحاجة إلى منشئ موثّق. استخدم /anonadmin off لاستعادة المراجعة البشرية.

gg-right-invite_users = دعوة المستخدمين

gg-right-promote_members = ترقية المشرفين

gg-right-manage_topics = إدارة المواضيع

gg-right-creator = منشئ المجموعة

gg-log-join = انضم { $user }.
gg-log-leave = غادر { $user }.

gg-warning-row = • #{ $id }: { $reason } (ينتهي: { $expiry })

gg-menu-prompt = اختر خياراً.
gg-content-invalid = المحتوى غير صالح أو يتجاوز حدود تيليجرام. تحقق من الاسم والتنسيق والخيارات والأزرار.
gg-content-unavailable = هذا المحتوى غير متاح أو لا تسمح عضويتك الحالية في المجموعة بالوصول إليه.
gg-btn-private-note = فتح الملاحظة
gg-open-private = افتح هذا المحتوى في المحادثة الخاصة:
gg-items-cleared = تم حذف { $count } من العناصر.
gg-clearall-confirm = يستطيع مالك المجموعة التأكيد باستخدام <code>/{ $command } confirm</code>.
gg-button-usage = الاستخدام: <code>/button "عنوان" https://example.com</code>. أضف سطرًا مثل <code>"ملاحظة" #name same</code> لإنشاء زر آخر في الصف نفسه. يعرض البوت الصيغة ومعاينة زر يعمل.
gg-btn-accept-rules = أوافق على القواعد
gg-btn-open-verification = فتح التحقق
gg-captcha-private = { $user }، افتح التحدي في المحادثة الخاصة للتحقق من عضويتك.
gg-captcha-choice = طابق الصورة باستخدام الأزرار. النمط: { $mode }؛ موضع الحرف: { $position }.
gg-captcha-settings = التحقق: { $enabled }؛ النمط: { $mode }؛ الطرد: { $kick }؛ المهلة: { $seconds } ثانية؛ فك الكتم التلقائي: { $release }.
gg-captcha-dependency = فعّل الترحيب قبل تفعيل التحقق. احفظ القواعد قبل اشتراط الموافقة عليها.
gg-val-text = صورة نصية
gg-val-text2 = صورة حروف
gg-captcha-attempts-exhausted = فشل التحقق بعد تجاوز عدد الإجابات الخاطئة المسموح به. تم تطبيق قيد الفشل.
gg-captcha-admin-exempt = أصبحت مشرفًا في المجموعة. تم إنهاء تحدي التحقق هذا.
gg-captcha-question-text = اختر الكلمة الظاهرة في الصورة.
gg-captcha-question-math = حل المعادلة الظاهرة في الصورة واختر الإجابة.
gg-captcha-question-text2 = اختر الحرف رقم { $position } من الصورة، بدءًا من اليسار إلى اليمين.
gg-locktypes = أنواع القفل المتاحة: <code>{ $types }</code>
gg-allowlist-title = استثناءات القفل
gg-allowlist-invalid = الاستثناء غير صالح. استخدم نطاقًا أو مسارًا، أو رابط دعوة محددًا، أو @chat، أو مُعرّفًا مثل stickerpack:name.
gg-reason-lock = محتوى مقفول: { $types }
gg-lock-applied = تم تطبيق سياسة القفل على { $types }. السبب: { $reason }
gg-reaction-failed = فشل تنفيذ قفل التفاعلات: { $code }. قد لا يدعم خادم واجهة البوت إزالة التفاعلات.
gg-reaction-anonymous = لا يتضمن تحديث عدد التفاعلات المجهولة مُعرّف المستخدم أو الدردشة التي أضافت التفاعل. تتطلب واجهة الإزالة أحدهما، لذلك لم يتم الادعاء بإزالة أي تفاعل.
gg-none = لا يوجد
gg-blocklist-title = قائمة الحظر
gg-blocklist-invalid = المُحفّز أو السبب أو الإجراء غير صالح. تحقق من العبارات المقتبسة وحروف البدل والمدة المطلوبة للأوضاع المؤقتة.
gg-blocklist-settings = وضع قائمة الحظر: { $mode }؛ حذف الرسائل المطابقة: { $delete }.
gg-blocklist-action = تم تطبيق سياسة قائمة الحظر على { $user }. السبب: { $reason }

gg-lock-album = ألبومات
gg-lock-anonchannel = مرسلو القنوات
gg-lock-audio = صوتيات
gg-lock-bot = بوتات
gg-lock-button = أزرار مضمنة
gg-lock-cashtag = وسوم العملات
gg-lock-checklist = قوائم مهام
gg-lock-cjk = نصوص صينية ويابانية وكورية
gg-lock-command = أوامر
gg-lock-comment = تعليقات غير الأعضاء
gg-lock-contact = جهات اتصال
gg-lock-cyrillic = نصوص سيريليّة
gg-lock-document = مستندات
gg-lock-email = عناوين بريد إلكتروني
gg-lock-emoji = رموز تعبيرية
gg-lock-emojicustom = رموز تعبيرية مخصصة
gg-lock-emojigame = ألعاب الرموز التعبيرية
gg-lock-emojionly = نصوص رموز تعبيرية فقط
gg-lock-externalreply = ردود خارجية
gg-lock-forward = رسائل محولة
gg-lock-forwarduser = رسائل محولة من مستخدمين
gg-lock-forwardbot = رسائل محولة من بوتات
gg-lock-forwardchannel = رسائل محولة من قنوات
gg-lock-forwardstory = قصص محولة
gg-lock-game = ألعاب
gg-lock-gif = صور متحركة
gg-lock-guestbot = بوتات ضيوف
gg-lock-inline = بوتات مضمنة
gg-lock-invitelink = دعوات تيليجرام
gg-lock-botlink = روابط بوتات
gg-lock-location = مواقع
gg-lock-outsidereaction = تفاعلات غير الأعضاء
gg-lock-phone = أرقام هواتف
gg-lock-photo = صور
gg-lock-poll = استطلاعات
gg-lock-reaction = تفاعلات
gg-lock-rtl = نصوص من اليمين إلى اليسار
gg-lock-spoiler = محتوى مخفي
gg-lock-sticker = ملصقات
gg-lock-stickeranimated = ملصقات متحركة
gg-lock-stickerpremium = ملصقات بريميوم
gg-lock-text = نصوص
gg-lock-url = روابط
gg-lock-video = فيديوهات
gg-lock-videonote = رسائل فيديو
gg-flood-status = التكرار: الحد المتتالي { $consecutive } (عند N)؛ المؤقت { $count } / { $seconds } ث (أكثر من N). الإجراء { $mode }، { $duration }؛ حذف التسلسل كاملًا { $clear }.
gg-raid-status = مكافحة الهجوم { $active }؛ حتى { $until }. مدة التفعيل { $period }؛ الحظر { $ban }؛ الحد التلقائي { $auto } انضمامات/دقيقة. تفعيل: /antiraid on · إيقاف: /antiraid off
gg-raid-banned = 🛡 حُظر { $user } مؤقتًا أثناء تفعيل مكافحة الهجوم.
gg-raid-declined = 🛡 رُفض طلب انضمام { $user } أثناء تفعيل مكافحة الهجوم.
gg-silent-consent-required = يجب على المنشئ تفعيل الإجراءات الصامتة مع سجل قبل اختيار هذا الإجراء.
gg-btn-enable-raid = تفعيل مكافحة الهجوم
gg-human-required = تتطلب هذه العملية مستخدمًا بشريًا معلوم الهوية.
gg-group-message-required = نفّذ الأمر على الرسالة أو الموضوع الفعلي في المجموعة؛ أرقام الرسائل الخاصة لا تحدد رسائل المجموعة.
gg-connection-private = استخدم أمر الاتصال في محادثتنا الخاصة.
gg-connection-disconnected = تم قطع الاتصال. تبقى آخر خمس مجموعات متاحة لإعادة الاتصال.
gg-connection-current = متصل بـ <b>{ $group }</b>. تُفحص العضوية والصلاحيات الحالية لكل عملية.
gg-connection-none = لا يوجد اتصال نشط بمجموعة. استخدم /connect GROUP_ID أو /connect @group.
gg-connection-open = افتح اتصالك الشخصي في محادثتنا الخاصة.
gg-btn-connect = الاتصال في الخاص
gg-connection-history = آخر خمس مجموعات. اختر مجموعة لإعادة الاتصال؛ العضوية الحالية مطلوبة.
gg-connection-unavailable = الاتصال غير متاح. يجب أن تكون عضوًا بشريًا حاليًا وأن يكون البوت مشرفًا هناك.
gg-catalog-unresolved = يظهر /{ $command } في القائمة المنشورة دون تعريف للإجراء. استخدم /notes أو /flood للميزات المنفذة.
gg-cleanup-failed = تعذر تنظيف الرسالة أو لم يكن متاحًا؛ لا يُدَّعى حذفها.
gg-op-lock_change = تغيير سياسة قفل الرسائل
gg-op-allowlist_change = تغيير استثناءات الأقفال
gg-op-allowlist_clear = مسح استثناءات الأقفال
gg-op-blocklist_change = تغيير عناصر قائمة الحظر
gg-op-blocklist_clear = مسح عناصر قائمة الحظر
gg-op-raid_change = تغيير تفعيل مكافحة الهجوم
gg-disabled-list = الأوامر: <code>{ $commands }</code>. يغير /disable NAME و /enable NAME التنفيذ؛ يتحكم /disabledel في الحذف؛ يشمل /disableadmin المشرفين.
gg-cleanup-types = فئات التنظيف المتاحة: { $types }
gg-cleanup-selected = فئات التنظيف المختارة: { $types }
gg-advanced-status = { $setting }: { $value }. يتطلب الصمت التلقائي موافقة المنشئ وسجلًا. تتطلب أوامر البوت صلاحياتها المعتادة؛ تبقى مراجعة التعديلات مفعلة افتراضيًا. تحتاج البوتات المخصصة إلى إعداد التواصل بين البوتات في BotFather.
gg-action-topic = موضوع الإجراءات: { $topic }. يحدده /setactiontopic داخل موضوع المنتدى. العام/الافتراضي هو 1.
gg-topic-unavailable = يتطلب ذلك مجموعة منتدى حالية وصلاحيات إدارة المواضيع المناسبة.
gg-topic-id-required = في محادثة خاصة متصلة، أدخل رقم الموضوع صراحةً.
gg-topic-general-delete = لا يمكن حذف الموضوع العام؛ يتطلب تأكيد الحذف مستخدمًا بشريًا معلوم الهوية.
gg-topic-delete-confirm = هل تريد حذف الموضوع { $topic } ورسائله؟ هذا التأكيد شخصي وتنتهي صلاحيته خلال دقيقتين.
gg-btn-confirm-delete = تأكيد الحذف
gg-topic-changed = تم تنفيذ إجراء الموضوع { $action } للموضوع { $topic }.
gg-op-policy_change = تغيير سياسة الأوامر أو التنظيف
gg-op-topic_create = إنشاء موضوع منتدى
gg-op-topic_rename = إعادة تسمية موضوع منتدى
gg-op-topic_close = إغلاق موضوع منتدى
gg-op-topic_reopen = إعادة فتح موضوع منتدى
gg-op-topic_delete = حذف موضوع منتدى ورسائله
gg-op-echo = إرسال محتوى منسق
gg-broadcast-owner = يمكن لمشغّل هذا البوت المُعيّن أو مالك النسخة الفعلي فقط الإرسال إلى مجموعاته.
gg-broadcast-queued = أُدرج الإرسال الجماعي { $id } في الطابور. تُعزل الوجهات ونتائج التسليم لكل بوت.
gg-broadcast-busy = يوجد إرسال جماعي نشط أو لم تنقضِ فترة الإنشاء المحددة بخمس دقائق.
gg-broadcast-empty = ليس لديك بث للمجموعات في هذا البوت.
gg-broadcast-status = البث { $id }: { $status }. في الانتظار: { $queued }؛ تم التسليم: { $sent }؛ فشل: { $failed }؛ نتيجة غير مؤكدة: { $uncertain }؛ ملغى: { $cancelled }.

gg-fed-created = تم إنشاء الاتحاد <b>{ $name }</b>. معرّفه في هذا البوت هو <code>{ $id }</code>.
gg-fed-info = <b>{ $name }</b>
    المعرّف: <code>{ $id }</code>
    المالك: <code>{ $owner }</code>؛ المشرفون: { $admins }.
    الأسباب مطلوبة: { $reasons }؛ إشعارات المالك: { $notifications }؛ السجل: { $log }.
gg-fed-list = اتحاداتك بصفتك مالكاً أو مشرفاً:
    { $rows }
gg-fed-admins = المالك أولاً ثم مشرفو الاتحاد:
    { $rows }
gg-fed-quiet = إخفاء توضيحات الاتحاد: { $value }. يظل تنفيذ الحظر نشطاً.
gg-fed-policy = الأسباب مطلوبة: { $reasons }؛ إشعارات المالك: { $notifications }.
gg-fed-confirm-delete = هل تريد حذف <b>{ $name }</b> (<code>{ $id }</code>)؟ ستُحذف سجلات الاتحاد وعضوياته نهائياً. سيبقى حظر المستخدمين في تيليجرام. أكّد خلال خمس دقائق.
gg-fed-confirm-log = هل تريد تعيين <code>{ $destination }</code> لسجل <b>{ $name }</b> (<code>{ $id }</code>)؟ أكّد خلال خمس دقائق. سنعيد التحقق من صلاحياتك وصلاحيات نشر البوت في الوجهة.
gg-fed-confirm-sent = أُرسل تأكيد شخصي إلى مالك الاتحاد.
gg-fed-deleted = حُذف الاتحاد. يبقى الحظر الحالي في تيليجرام.
gg-fed-log-set = وجهة سجل الاتحاد: <code>{ $destination }</code>.
gg-fed-cancel = إلغاء
gg-fed-cancelled = أُلغي الطلب.
gg-fed-saved-delivery-failed = حُفظ تغيير الاتحاد. تعذر تسليم الإشعار أو السجل؛ تحقّق من الوجهة ووصول البوت.
gg-fed-error-authority = يتطلب هذا الإجراء مالك الاتحاد الحالي أو دور الاتحاد المناسب. لا تمنح أدوار المجموعة صلاحيات داخل الاتحاد.
gg-fed-error-private = استخدم هذا الأمر في محادثتك الخاصة مع هذا البوت.
gg-fed-error-group = استخدم هذا الأمر في المجموعة الفعلية. الاتصال الخاص لا يحدد مجموعة الاتحاد.
gg-fed-error-owned = أنت تملك اتحاداً بالفعل في هذا البوت. استخدم /fedinfo أو /renamefed أو /delfed في الخاص.
gg-fed-error-name = أدخل اسماً غير فارغ بلا محارف تحكم. تُختصر الأسماء إلى 64 محرفاً.
gg-fed-error-id = أدخل معرّف UUID صالحاً لاتحاد في هذا البوت. لا يمكن استخدام معرّفات شبكة روز في خدمة اتحاداتنا المستقلة.
gg-fed-error-missing = لم يُعثر على اتحاد في هذا البوت أو السياق المحدد.
gg-fed-error-creator = منشئ المجموعة الحالي في تيليجرام وحده يمكنه الانضمام إلى اتحاد أو مغادرته.
gg-fed-error-target = أدخل معرّف إنسان موجباً أو ردّاً على إنسان أو اسم مستخدم معروفاً ومتحققاً منه حالياً. لا يمكن إزالة المالك.
gg-fed-error-value = معاملات الاتحاد غير صالحة. استخدم on/off لتغيير السياسات ومعرّف اتحاد صالحاً حيث يلزم.
gg-fed-error-stale = انتهى التأكيد أو استُخدم أو تغيرت حالة الاتحاد أو المالك أو الوجهة. اطلب تأكيداً جديداً.
gg-fed-error-destination = يحتاج مالك الاتحاد إلى صلاحيات إدارة حالية في الوجهة، ويحتاج البوت إلى النشر فيها. تتطلب القنوات صلاحية post_messages.
gg-fed-error-delivery = تعذر تسليم التأكيد الشخصي أو ربطه. افتح محادثة خاصة مع البوت وحاول مجدداً.
gg-fed-event = الاتحاد <b>{ $name }</b> (<code>{ $id }</code>): { $event }. صاحب الإجراء: <code>{ $user }</code>.
gg-fed-event-rename = تغيّر الاسم
gg-fed-event-delete = حُذف الاتحاد؛ يبقى حظر تيليجرام الحالي
gg-fed-event-promote = أُضيف مشرف
gg-fed-event-demote = أُزيل مشرف
gg-fed-event-self-remove = استقال مشرف
gg-fed-event-reason = تغيّرت سياسة أسباب الحظر
gg-fed-event-notif = تغيّرت سياسة إشعارات المالك
gg-fed-event-log = تغيّرت وجهة السجل
gg-fed-event-unlog = أُزيلت وجهة السجل
gg-fed-event-ban = حُفظت سياسة الحظر وأُدرج التنفيذ في الانتظار
gg-fed-event-unban = أُزيلت سياسة الحظر وأُدرج رفع الحظر المملوك في الانتظار
gg-fed-event-subscribe = أُضيف اشتراك الحظر وأُدرج المستخدمون المرصودون للتحقق
gg-fed-event-unsubscribe = أُزيل اشتراك الحظر وحُفظت المصادر الأخرى
gg-fed-ban-details = المستهدف: <code>{ $user }</code>. السبب: { $reason }
gg-fed-passive = تمنع سياسة الاتحاد { $user }. المصدر: <b>{ $source }</b> (<code>{ $id }</code>). السبب: { $reason }
gg-fed-enforce-failed = تمنع سياسة الاتحاد { $user } لكن الإزالة فشلت. تحقّق من صلاحيات البوت. المصدر: <b>{ $source }</b> (<code>{ $id }</code>). السبب: { $reason }
gg-fed-stat = حالة حظر الاتحادات للمستخدم <code>{ $user }</code>:
    { $rows }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — نشط: { $status }؛ آخر تغيير: { $date }.
gg-fed-stat-more = توجد مصادر أخرى. استعلم بمعرّف اتحاد محدد لعرض سببه وتاريخه.
gg-fed-intent-saved = حُفظت سياسة الاتحاد للمستخدم <code>{ $user }</code> بالإصدار { $version }. أُدرجت الوجهات المرصودة في الانتظار؛ تُراجع الصلاحيات الحالية ومصادر القيود الأخرى قبل التنفيذ.
gg-fed-subscriptions = اشتراكات حظر الاتحادات المباشرة:
    { $rows }
gg-fed-imported = تم التحقق من { $count } سجل حظر وحفظها؛ تم تجاهل { $duplicates } سجل مكرر مطابق. أُدرج تنفيذ الوجهات المرصودة في الانتظار.
gg-fed-event-import = استُوردت سجلات حظر متحقق منها وأُدرج التنفيذ في الانتظار
gg-fed-error-file-format = ردّ على ملف CSV بترميز UTF-8 وأعمدة id/reason، أو سجلات JSONL/NDJSON تتضمن user_id، أو مصفوفة JSON مُصدّرة من هذا البوت. تمنع الصفوف غير الصالحة جميع الكتابات.
gg-fed-error-file-limit = تقتصر ملفات الحظر على 2 ميبيبايت و1,000 سجل. تُرفض الملفات الكبيرة أو المفقودة؛ لا تُختصر القوائم بصمت.
gg-fed-error-file-duplicate = توجد سجلات متعارضة لمعرّف المستخدم نفسه. لم يُستورد أي حظر.
gg-fed-error-file-rate = يشترك تصدير قوائم الحظر واستيرادها في مهلة 30 دقيقة لكل اتحاد. حاول لاحقاً.
gg-fed-error-reason = يجب ألا يتجاوز السبب 1,024 محرفاً وألا يحتوي محارف تحكم غير مدعومة.
gg-fed-error-reason_required = يتطلب هذا الاتحاد سبباً غير فارغ لكل حظر.
gg-fed-error-cycle = لا يمكن للاتحاد الاشتراك في نفسه أو إنشاء حلقة اشتراكات موجهة.
gg-fed-error-graph_limit = تم بلوغ حدود الاشتراك: 32 هدفاً مباشراً أو 128 اتحاداً قابلاً للوصول أو عمق 16 أو 10,000 رابط في هذا البوت.
gg-data-confirm =
    <b>{ $operation }</b> · المجموعة <code>{ $group }</code>
    الوحدات: { $modules }
    بصمة الملف SHA-256: <code>{ $digest }</code>
    أكّد خلال خمس دقائق. نتحقق مجددًا من صلاحية منشئ المجموعة ومن نسخة الإعدادات. تتغير الوحدات المحددة فقط؛ الهوية والثقة والحظر النشط تبقى محفوظة.
gg-data-import = استيراد وحدات المجموعة
gg-data-reset = إعادة ضبط وحدات المجموعة
gg-data-privacy-delete = حذف البيانات الشخصية الاختيارية من هذا البوت
gg-data-confirm-button = تأكيد هذا التغيير
gg-data-personal = افتح رسالة التأكيد التي أرسلتها إلى محادثتك الخاصة.
gg-data-saved = حُفظت الوحدات المحددة.
gg-data-error-authority = الاستيراد وإعادة الضبط يتطلبان منشئ المجموعة الحالي المعروف الهوية. التصدير يتطلب مشرفًا حاليًا.
gg-data-error-format = ردّ على ملف JSON صالح بإصدار Group Guard المدعوم؛ أنشئه باستخدام /export.
gg-data-error-limit = تجاوز الملف حد الحجم أو عدد عناصر المحتوى المسموح به.
gg-data-error-version = مخطط الملف أو إصداره غير مدعوم؛ لم تُطبّق أي تغييرات.
gg-data-error-module = اختر وحدات معروفة: /export all أو /export notes rules. يستخدم الاستيراد وإعادة الضبط الأسماء نفسها.
gg-data-error-field = حقول الوحدة غير صالحة أو ناقصة؛ لم تُطبّق الإعدادات.
gg-data-error-item = المحتوى أو الخيارات أو صلاحية التكرار غير صالحة؛ لم يُحفظ المحتوى.
gg-data-error-media = يجب رفع الوسائط إلى هذا البوت وإتاحتها عبر getFile. معرّفات ملفات بوت آخر غير مدعومة.
gg-data-error-destination = وجهة السجل والموضوع تتطلب صلاحيات حالية وقدرات البوت. معرّفات المواضيع صالحة للمجموعة نفسها فقط.
gg-data-error-language = اختر لغة مثبتة باستخدام /setlang.
gg-data-error-stale = انتهى التأكيد أو تغيرت بياناته أو استُخدم بالفعل. ابدأ من جديد.
gg-data-error-restore = تعذرت استعادة القيود المؤقتة التي يملكها البوت بأمان. تبقى أدلتها محفوظة؛ تحقق من الصلاحيات قبل المحاولة.
gg-data-error-rate = توجد مهلة محلية من خمس دقائق بين عمليات بيانات المجموعة. حاول لاحقًا.
gg-data-error-delivery = تعذر إرسال التأكيد الخاص. افتح محادثة خاصة مع البوت ثم أعد المحاولة.
gg-data-error-saved_delivery = حُفظت الإعدادات لكن تعذر تحديث اقتراحات الأوامر. تحقق من صلاحيات البوت.
gg-privacy-policy =
    <b>بياناتك لدى بوت Group Guard هذا</b>
    /privacy data يصدّر اتصالاتك وملفاتك المرصودة وإنذاراتك وموافقاتك وحالات القيود والتحقق وملكيات الاتحادات وأدوارها وحظرها والعمل الأمني المعلّق. لا يتضمن محتوى الآخرين الخاص أو الإجابات أو بيانات المصادقة أو الملفات الخام. اتبع أمر المتابعة للصفحات التالية.
    /privacy delete يحذف سجل الاتصال الاختياري والاسم واسم المستخدم المرصودين والتحقق غير النشط ومحتوى الحملات الشخصية المنتهية في هذا البوت. تحتفظ الإنذارات والقيود النشطة وإصدارات الحظر والأدوار والملكية والاستحقاقات وإيصالات منع التكرار والعمل ذي النتيجة المجهولة بأقل معرّفات لازمة للأمن والترتيب. لإلغاء علاقات الاتحاد استخدم أوامر الاستقالة أو الحذف الصريحة. يبقى الملف المشترك للمنصة وبيانات البوتات الأخرى.
    يدير المشغّلون النسخ الاحتياطية والتدقيق منفصلين؛ لا يمحو هذا الأمر رسائل تيليجرام الخارجية أو النسخ الاحتياطية. لا ندّعي مدة احتفاظ تلقائية.
gg-privacy-usage = /privacy policy · /privacy data [مؤشر المتابعة] · /privacy delete — في محادثتك الخاصة مع البوت.
gg-privacy-private = يجب أن ينفذ هذا الإجراء الشخص نفسه في محادثته الخاصة. مؤشر وصول غير صالح لا يكشف بيانات الآخرين.
gg-privacy-next = الصفحة التالية: /privacy data { $cursor }
gg-privacy-deleted = حُذفت بياناتك الشخصية الاختيارية من هذا البوت. تبقى أقل معرّفات لازمة للأمن والملكية والعمل مجهول النتيجة؛ راجع /privacy policy.
gg-language-usage = اختر لغة المجموعة: /setlang { $codes }. يغيّر /lang الخاص لغة حسابك على المنصة.
gg-language-saved = تم تحديث لغة الردود في المجموعة.
gg-help-index =
    <b>دليل أوامر Group Guard</b>
    /help family · /help command · /help family 2. تعمل أوامر المجموعة المدرجة كذلك من اتصال /connect الموثّق. تبقى الردود الخاصة في المحادثة الخاصة الفعلية.
    الإعدادات تتطلب تغيير المعلومات؛ العقوبات تقييد الأعضاء؛ الحذف حذف الرسائل؛ التثبيت تثبيت الرسائل؛ الترقيات ترقية الأعضاء؛ المواضيع إدارة المواضيع. نتحقق من صلاحيات البوت منفصلًا. عمليات المالك تتطلب منشئ المجموعة الحالي المعروف الهوية. يفتح /settings لوحة مجموعتك الشخصية.
gg-help-search = <b>الأوامر المطابقة لـ { $query }</b>
gg-help-connected = في المجموعة أو الاتصال الموثّق؛ راجع دليل الفئة للصلاحيات
gg-help-group-only = يتطلب رسالة فعلية في المجموعة
gg-help-unsupported = الاسم محفوظ من الفهرس؛ معناه غير موثّق ويعرض توضيحًا
gg-help-next = الصفحة التالية
gg-help-previous = الصفحة السابقة
gg-help-family-title-moderation = الإشراف والموافقات
gg-help-family-title-messages = حذف الرسائل وتثبيتها
gg-help-family-title-logging = السجلات المصرح بها
gg-help-family-title-settings = إعدادات المجموعة واللغة
gg-help-family-title-content = الملاحظات والمرشحات والقواعد والترحيب
gg-help-family-title-captcha = التحقق من الأعضاء الجدد
gg-help-family-title-locks = أقفال المحتوى واستثناءاته
gg-help-family-title-blocklists = مطابقة قائمة المنع وإجراءاتها
gg-help-family-title-antispam = حماية التدفق والغارات
gg-help-family-title-connections = اتصال خاص بالمجموعات
gg-help-family-title-identity = معلومات المستخدم والمحادثة
gg-help-family-title-policy = سياسة الأوامر والبوتات
gg-help-family-title-cleanup = تنظيف الأوامر ورسائل البوت والخدمة
gg-help-family-title-topics = مواضيع المنتدى
gg-help-family-title-utilities = إعادة المحتوى وحملات المشغّل
gg-help-family-title-federations = أدوار الاتحادات وحظرها واشتراكاتها
gg-help-family-title-portability = ملفات المجموعة وبياناتك الخاصة
gg-help-family-title-discovery = المساعدة ومحرر المحتوى
gg-help-family-moderation =
    <b>الإشراف</b> · ردّ على رسالة أو أدخل رقم المستخدم أو @اسمًا موثّقًا حاليًا.
    /ban 20 سبب · /tban 20 60s سبب · /mute 20 · /tmute 20 2h سبب. مدة العقوبة المؤقتة من 60 ثانية إلى 365 يومًا. /kickme يطردك أنت فقط. صيغ d تحذف رسالة الرد أيضًا؛ صيغ s تنظف رسالة الأمر والرد وتتطلب صلاحية الحذف. المشرفون الحاليون محميون.
    /setwarnlimit 3 · /setwarnmode ban · /setwarntime 1d. حد المجموعة الجديدة ثلاثة إنذارات؛ تبقى إعدادات المجموعات القديمة. /approve يعفي من الحماية العادية للتدفق والمحتوى ولا يعفي من الاتحاد أو CAS أو الغارات أو الإجراءات اليدوية. /promote يتطلب صلاحية الترقية ولا يمنح حقوقًا أكثر مما يملك المستدعي والبوت. إعادة الضبط الجماعية تتطلب المنشئ المعروف.
gg-help-family-messages =
    <b>الرسائل</b> · /del يتطلب ردًا على رسالة فعلية في المجموعة. يبدأ /purge منها؛ يحفظ /purgefrom و/purgeto حدود النطاق. الحذف محدود بالإعدادات وقواعد تيليجرام؛ إقرار الطلب الدفعي ليس عددًا مؤكّدًا للرسائل المحذوفة.
    /pin [loud] و/permapin و/unpin و/unpinall تحتاج صلاحية التثبيت؛ الإلغاء الجماعي يحتاج المنشئ. يتحكم /antichannelpin و/cleanlinked بالرسائل التلقائية من القناة المرتبطة.
gg-help-family-logging =
    <b>السجلات</b> · /setlog -100… يحتاج صلاحيات إشراف حالية في الوجهة وقدرة البوت على النشر. يجب أن يأتي الإعداد المحوّل من رسالة إعداد قناة تلقاها البوت فعلًا. /logcategories يعرض settings/admin/user/automated/reports/other؛ يحدد /log و/nolog الفئات. يبقى الفشل ظاهرًا ولا يعني اكتمال الإجراء.
gg-help-family-settings =
    <b>الإعدادات</b> · /settings يفتح لوحة شخصية مؤقتة ويتحقق من صلاحية تغيير المعلومات. يحفظ /setlang code لغة المجموعة بينما يحفظ /lang الخاص لغة حسابك. /night 23 7 +3 يغلق المحادثة ليلًا؛ /night off يستعيد فقط لقطة الصلاحيات التي يملكها البوت إذا كانت مطابقة. تغييرات المشرفين الخارجية لها الأولوية.
gg-help-family-content =
    <b>محرر المحتوى</b> · /save word نص أو ردّ على نص/وسائط؛ /get word و#word و/notes لقراءة الملاحظات. اسم الملاحظة كلمة واحدة؛ الأسماء القديمة الأوسع امتداد محفوظ. /filter "عبارة مقتبسة" نص و/filterprefix و/filterexact تحدد المطابقة. /stop يحذف المشغّل؛ /clearall و/stopall يحتاجان تأكيد المنشئ.
    يدعم تنسيق Rose الخط العريض والمائل والمسطّر والمشطوب والشيفرة والروابط والاقتباسات والبدائل العشوائية %%%. حقول التعبئة: { "{" }first{ "}" } و{ "{" }last{ "}" } و{ "{" }fullname{ "}" } و{ "{" }username{ "}" } و{ "{" }mention{ "}" } و{ "{" }id{ "}" } و{ "{" }chatname{ "}" } و{ "{" }count{ "}" }. استخدم /button لإنشاء أزرار روابط وملاحظات وقواعد مع معاينة فعلية. الخيارات preview/nonotif/protect/mediaspoiler؛ وللملاحظات admin/private/noprivate/repeat؛ وللمرشحات user/allow_bot/replytag/command. /save word مرحبًا { "{" }repeat 5m{ "}" } يكرر المحتوى العام فقط مع صلاحية المؤلف الحالية. تشترك القواعد والترحيب والوداع والملاحظات الخاصة في العارض نفسه؛ معرّفات الوسائط تخص هذا البوت.
gg-help-family-captcha =
    <b>التحقق</b> · /captcha on/off؛ /captchamode off/button/math/text/text2؛ /setcaptchatext للنص؛ /captcharules on؛ /captchakick on/off؛ /captchakicktime و/captchamutetime للأوقات المحدودة. تحتفظ التحديات المرسلة بجيلها وموعدها. التحقق من طلب الانضمام يحتاج دعوة الأعضاء؛ كتم العضو يحتاج تقييدهم. الإجابات شخصية وتُقبل مرة واحدة. حظر الاتحاد يسبق الموافقة والتحقق.
gg-help-family-locks =
    <b>الأقفال</b> · /lock links [إجراء] و/unlock type؛ /locktypes للأنواع الفعلية و/locks للحالة. يتحكم /lockwarns بالإنذارات. /allowlist يقبل نطاقًا ومسارًا أو دعوة مطابقة تمامًا أو @محادثة أو هويات stickerpack:/forward:/inline:/channel:/chat:/bot:/command: المعلنة؛ تُرفض الأنماط غير الصالحة. الاستثناء للمحتوى المطابق للقفل فقط، وليس لجميع الحماية. الإجراءات الصامتة تحتاج موافقة المنشئ وسجلًا تلقائيًا مصرحًا به.
gg-help-family-blocklists =
    <b>قائمة المنع</b> · /addblocklist "عبارة مقتبسة" يقبل مشغّلات نصية وبادئة ومطابقة تامة وأنواع الهوية المعلنة مع أسباب وإجراءات اختيارية؛ يحذف /rmblocklist المفاتيح المختارة بالضبط. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute يحدد الإجراء؛ الأنماط المؤقتة تحتاج مدة. يحدد /blocklistdelete حذف الرسالة مستقلًا. المطابقة محدودة وآمنة وتُطبّق حدود عدد العناصر.
gg-help-family-antispam =
    <b>التدفق والغارات</b> · /setflood count للتدفق المتتابع؛ /setfloodtimer count duration للنافذة الزمنية. /setfloodmode للإجراء ومدته المحدودة؛ /clearflood لحذف السلسلة. تبقى إعدادات النوافذ القديمة. يعرض /flood و/antiflood السياسة؛ علاقة الاسمين توافق محلي.
    /antiraid on/off/duration و/raidtime و/raidactiontime و/autoantiraid تضبط موعدًا دائمًا وعقوبة منفصلة للوافدين. الغارة تسبق الموافقة والتحقق؛ انتهاء المدة مرتبط بالجيل وآمن بعد إعادة التشغيل.
gg-help-family-connections =
    <b>الاتصالات</b> · في الخاص استخدم /connect groupID أو رابطك الشخصي. نتحقق من عضويتك وعضوية البوت حاليًا؛ تبقى التغييرات مرتبطة بالصلاحيات الدقيقة الحالية. يعرض /connection اختيارك، يزيله /disconnect، ويعرض /connect المجموعات الأخيرة مع المتابعة. اتصال المجموعة لا يمنح ملكية اتحاد أو صلاحية مشغّل المنصة.
gg-help-family-identity =
    <b>المعلومات</b> · /id يعرض معرّفات المستخدم والمحادثة والمصدر الفعلية؛ /info يعرض الهدف الحالي. حلّ الرد و@اسم المستخدم يحتاج دليلًا حاليًا ضمن النطاق. المنشور المجهول لا يكشف صاحبه البشري؛ لا نختلق معرّفًا له.
gg-help-family-policy =
    <b>سياسة الأوامر</b> · /disable command و/enable command و/disabled و/disableable للأوامر والأسماء البديلة. يتحكم /disableadmin بإعفاء المشرفين؛ /disabledel بحذف الأوامر المعطلة. تبقى أوامر الاسترداد متاحة. /bot2bot off/admin/all يتحقق من عضوية البوت الفعلية؛ تحتاج التغييرات عادة مراجعة بشرية، و/bot2botskipreview للمنشئ فقط. /silentactions يحتاج موافقة المنشئ وسجلًا تلقائيًا مصرحًا. يبقى معنى runs/saved غير الموثّق توضيحًا صريحًا.
gg-help-family-cleanup =
    <b>التنظيف</b> · /cleancommand admin/user/other و/keepcommand يحددان فئات الأوامر. /cleanmsg action/filter/note و/keepmsg يحددان رسائل هذا البوت المرسلة فعلًا؛ تمنع الإيصالات ومهام الخمس دقائق حذف معرّفات مُخمّنة. /cleanservice و/nocleanservice للفئات join/leave/other/photo/pin/title/videochat. يُنفّذ العمل الوظيفي والتحقق من الدفع قبل التنظيف.
gg-help-family-topics =
    <b>المواضيع</b> · /newtopic اسم و/renametopic اسم و/closetopic و/reopentopic تعمل على الموضوع الفعلي الحالي. /deletetopic يحتاج تأكيد المنشئ؛ يحفظ /setactiontopic وجهة داخل المجموعة نفسها. المنتدى وصلاحية إدارة المواضيع مطلوبان. فشل التسليم لموضوع محذوف أو غير مدعوم يظهر بنتيجته الحقيقية.
gg-help-family-utilities =
    <b>الأدوات</b> · /echo أو /say يعرض النص والوسائط الداخلية أو المردود عليها بالعارض المشترك المحدود. /broadcast لمشغّل هذا البوت المحدد أو مالك النسخة الفرعية الفعلي، ويستهدف مجموعاته المحددة فقط. تحفظ النتائج الدائمة لكل وجهة التسليم الجزئي والمجهول؛ الحالة والإلغاء لا يكرران المرفقات الناجحة.
gg-help-family-federations =
    <b>الاتحادات</b> · /newfed اسم ينشئ UUID ضمن هذا البوت. الخاص يختار اتحادك المملوك مستقلًا عن الاتصالات؛ قراءة UUID صريح لا تمنح دورًا. /fedpromote و/feddemote للمشرفين؛ /feddemoteme للاستقالة. /joinfed UUID و/leavefed يحتاجان منشئ المجموعة الحالي. حذف الاتحاد لا يرفع حظر تيليجرام تلقائيًا.
    /fban userID سبب و/unfban userID لمالك الاتحاد أو مشرفه؛ /fedreason و/fednotif و/setfedlog إعدادات المالك. /quietfed يخفي الشرح السلبي فقط. /subfed UUID اشتراك موجّه ومحدود بلا دورات. /fedstat [userID] و/fbanstat UUID يعرضان مصادر الحظر والحالة. /fbanlist csv/minicsv/json للمالك وبمهلة مشتركة 30 دقيقة؛ /importfbans يرد على CSV محدود أو JSON حقيقي منفصل بالأسطر مع دعم صيغة مصفوفة البوت الصريح. يعاد فحص المستخدمين المرصودين فعليًا فقط؛ لا ندّعي قائمة كاملة لأعضاء المجموعة.
gg-help-family-portability =
    <b>ملفات المجموعة والخصوصية</b> · /export all أو أسماء الوحدات يحتاج مشرفًا حاليًا؛ /import و/reset يحتاجان المنشئ البشري الحالي وتأكيدًا شخصيًا صالحًا خمس دقائق ولمرة واحدة. مهلة محلية خمس دقائق للمجموعة؛ JSON بإصدار البوت وحجم أقصى 2MiB وحدود المحتوى المضبوطة. الوحدات: moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. تبقى الوحدات غير المحددة. لا تُستورد الثقة أو التحديات والمهام الحية أو الاستحقاقات أو الأدوار أو الحظر النشط.
    /privacy policy/data/delete يعمل في محادثتك الخاصة فقط مع متابعة بياناتك والاحتفاظ الأمني الأدنى. ليس هذا محوّلًا موثّقًا لتصدير Rose الكامل.
gg-help-family-discovery =
    <b>المساعدة</b> · /help يعرض الفئات؛ /help command يبحث في الأوامر وأسمائها البديلة؛ /help family 2 يتابع الصفحات. /button مساعد لتنسيق الأزرار. يوضح كل دليل السياق والصلاحيات والإعدادات الافتراضية وحدود التشغيل. يفتح /settings لوحة المجموعة الشخصية.
gg-data-error-cache_pending = حُذفت البيانات الاختيارية من قاعدة البيانات؛ تنظيف الذاكرة المؤقتة في قائمة الانتظار لتعذر الوصول إليها. تبقى السجلات الأمنية النشطة.
