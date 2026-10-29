## مصنع البوتات — العربية.
fac-home =
    🏭 أهلاً <b>{ $name }</b>! مرحباً بك في <b>مصنع البوتات</b>.

    أطلق <b>بوت تيليجرام خاصاً بك</b> خلال دقيقة — بدون برمجة، بدون خادم، مجاناً:
    📩 صندوق رسائل مجهولة · 💬 بوت تواصل ودعم · 🛡 حارس مجموعات · 🧩 بوت قوائم ومعلومات

    بوتاتك: <b>{ $count }</b> / { $limit }
fac-btn-new = 🤖 أنشئ بوتاً
fac-btn-mine = 📂 بوتاتي ({ $count })
fac-btn-gallery = 🌟 المعرض
fac-btn-botfather = 🧑‍🔧 افتح @BotFather
fac-btn-open = 🚀 افتح @{ $username }
fac-btn-manage = ⚙️ إدارة
fac-btn-pause = ⏸ إيقاف مؤقت
fac-btn-resume = ▶️ تشغيل
fac-btn-token = 🔑 توكن جديد
fac-btn-public = 🌟 في المعرض: { $state }
fac-btn-brand = 🏷 سطر الإشارة: { $state }
fac-btn-refresh = 🔄 تحديث
fac-btn-delete = 🗑 حذف
fac-btn-delete-ok = 🗑 نعم، احذف البوت وكل بياناته
fac-btn-admin-tab = 🏭 المصنع
fac-choose = 🤖 <b>ماذا تريد أن يفعل بوتك؟</b>
fac-tpl-anonymous = صندوق رسائل مجهولة
fac-tpl-anonymous-desc = يراسلك الناس دون كشف هويتهم عبر بوتك، وترد بضغطة واحدة.
fac-tpl-anonymous-guide = شارك رابط بوتك في نبذتك أو قصتك — يمكن للناس الآن مراسلتك دون كشف هويتهم.
fac-tpl-feedback = بوت تواصل ودعم
fac-tpl-feedback-desc = يراسل العملاء البوت، وترد عليهم بالرد على رسائلهم. يعمل لفريق كامل داخل مجموعة.
fac-tpl-feedback-guide = افتح بوتك وأرسل /start. تصل رسائل العملاء هناك — رد عليها للإجابة. /admin للإعدادات.
fac-tpl-groupguard = حارس مجموعات
fac-tpl-groupguard-desc = تحقق، ومكافحة سبام وتكرار، وتحذيرات، وترحيب، وملاحظات — مدير مجموعات باسمك.
fac-tpl-groupguard-guide = أضف بوتك إلى مجموعتك كمشرف، ثم أرسل /settings داخل المجموعة.
fac-tpl-custom = بوت قوائم ومعلومات
fac-tpl-custom-desc = أنشئ صفحات وأزراراً وروابط وأوامر — قوائم، أسئلة شائعة، أسعار، معرض أعمال. بدون برمجة.
fac-tpl-custom-guide = افتح بوتك وأرسل /build لتصميم صفحاتك. التغييرات تظهر فوراً.
fac-steps =
    { $template } — اختيار رائع! الآن:

    1. افتح @BotFather وأرسل <code>/newbot</code>
    2. اختر اسماً ومعرّفاً ينتهي بـ “bot”
    3. انسخ <b>التوكن</b> الذي يعطيك إياه BotFather وأرسله هنا

    🔒 أحذف رسالتك فوراً وأحفظ التوكن مشفّراً.
fac-creating = ⏳ جارٍ تجهيز بوتك…
fac-created =
    🎉 <b>@{ $username } يعمل الآن!</b> ({ $template })

    { $guide }
fac-err-template = ⚠️ قالب غير معروف.
fac-err-token_format = ⚠️ هذا لا يبدو توكن بوت. شكله مثل <code>123456789:AA…</code> — انسخه من @BotFather.
fac-err-token_invalid = ⚠️ تيليجرام يقول إن التوكن غير صالح أو أُلغي. احصل على توكن جديد من @BotFather.
fac-err-telegram = ⚠️ لم يرد تيليجرام. حاول بعد لحظات.
fac-err-platform_bot = ⚠️ هذا البوت يعمل بالفعل على هذه المنصة.
fac-err-taken = ⚠️ هذا البوت مربوط بالفعل بواسطة شخص آخر.
fac-err-revoked = ⛔ حُظر هذا البوت من قِبل المشرفين.
fac-err-limit = 📦 وصلت إلى حدك وهو { $limit } بوت. اشترك في 💎 VIP أو ادعُ أصدقاءك لمزيد من الخانات.
fac-err-webhook = ⚠️ رفض تيليجرام ربط البوت. حاول لاحقاً.
fac-err-token_other_bot = ⚠️ هذا التوكن يخص بوتاً آخر.
fac-mine = 📂 <b>بوتاتك</b> ({ $count })
fac-mine-empty = 📂 ليس لديك بوتات بعد. أنشئ واحداً خلال دقيقة!
fac-not-found = البوت غير موجود.
fac-manage =
    🤖 <b>@{ $username }</b>
    { $template }

    • الحالة: { $status }
    • المستخدمون: <b>{ $users }</b>
    • زوار جاؤوا للمصنع من خلاله: <b>{ $visits }</b>
    • تاريخ الإنشاء: { $created }

    افتح البوت وأرسل /admin لإعداداته وإحصائياته والبث.
fac-status-active = يعمل
fac-status-paused = متوقف مؤقتاً
fac-status-error = خطأ
fac-status-revoked = محظور
fac-last-error = ⚠️ آخر خطأ: { $error }
fac-brand-vip = 💎 إزالة سطر «صُنع بواسطة» ميزة VIP.
fac-rotate = 🔑 أرسل التوكن الجديد لـ @{ $username } (في @BotFather: ‏/revoke ثم انسخ التوكن الجديد).
fac-rotated = ✅ تم تحديث التوكن.
fac-confirm-delete = 🗑 حذف @{ $username }؟ سيُحذف مستخدموه وإعداداته ومحتواه نهائياً. (يبقى البوت ملكك في @BotFather.)
fac-deleted = 🗑 تم حذف @{ $username }.
fac-disabled = 🔧 إنشاء البوتات غير متاح مؤقتاً. حاول لاحقاً.
fac-gallery = 🌟 <b>المعرض</b> — أشهر البوتات المصنوعة هنا
fac-gallery-empty = لا توجد بوتات عامة بعد. اجعل بوتك عاماً من شاشة ⚙️ الإدارة!
fac-adm = 🏭 <b>المصنع</b> — البوتات حسب القالب والحالة
fac-adm-btn-search = 🔍 ابحث عن بوت
fac-adm-search = 🔍 أرسل @المعرف أو رقم البوت أو رقم المالك.
fac-adm-btn-revoke = ⛔ حظر @{ $username }
fac-adm-confirm = ⛔ حظر @{ $username }؟ سيتوقف فوراً ويُمسح توكنه.
fac-adm-revoked = ⛔ تم حظر @{ $username }.
vip-perks =
    ✅ حتى { $vip_bots } بوتات (المجاني: { $free_bots })
    ✅ إزالة سطر «صُنع بواسطة» من بوتاتك
    ✅ دعم بأولوية
vip-status-none = ⚪ الخطة المجانية: { $free_bots } بوت.
cmd-newbot = أنشئ بوتاً
cmd-mybots = بوتاتك
cmd-top = معرض البوتات
fac-tpl-channelmanager = مدير القنوات
fac-tpl-channelmanager-desc = نشر المحتوى وإدارة الانضمام والمحتوى الخاص والحملات الاختيارية للقنوات.
fac-tpl-channelmanager-guide = أضف البوت مسؤولًا في القناة واستخدم /connect. اربطه عبر /senders في البوت الرئيسي. ارفع الوسائط إلى هذا البوت؛ تظل الفوترة في البوت الرئيسي.
fac-migration-confirm = لهذا التوكن رابط استقبال على استضافة أخرى. سيؤدي النقل إلى استبدال الرابط وإيقاف إرسال التحديثات إلى الخدمة السابقة. لن تُستورد الإعدادات أو المحتوى الخارجي. أكد فقط إذا كنت تتحكم في البوت وتريد نقله إلى هنا.
fac-btn-migrate = تأكيد النقل إلى هذه المنصة
fac-err-migration_required = يلزم تأكيد صريح لنقل هذا التوكن.
