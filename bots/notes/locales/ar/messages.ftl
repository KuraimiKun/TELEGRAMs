## الملاحظات والتذكيرات — العربية.
notes-start =
    👋 أهلاً <b>{ $name }</b>!

    📝 أرسل لي أي نص وسأحفظه كملاحظة.
    ⏰ استخدم <code>/remind 10m اتصل بأمي</code> لتحصل على تذكير.
notes-help =
    ℹ️ <b>طريقة الاستخدام</b>

    • أي نص ترسله يصبح ملاحظة — يعرضها الأمر /notes.
    • <code>/remind 30m تمارين</code> أو <code>/remind 2h …</code> أو <code>/remind 1d …</code> أو <code>/remind 18:30 …</code> (بتوقيت UTC)
    • يعرض الأمر /reminders التذكيرات القادمة.
notes-btn-notes = 📝 ملاحظاتي
notes-btn-reminders = ⏰ التذكيرات
notes-btn-delete = 🗑 حذف #{ $id }
notes-btn-cancel-reminder = ✖️ إلغاء { $when }
notes-btn-admin-tab = 📝 الملاحظات
notes-saved = ✅ حُفظت كملاحظة <b>#{ $id }</b>.
notes-list-title = 📝 <b>ملاحظاتك</b> ({ $count }/{ $max })
notes-empty = لا توجد ملاحظات بعد — أرسل لي أي نص.
notes-limit-notes = 📦 وصلت إلى { $max } ملاحظة. احذف بعضها أو اشترك في 💎 VIP للمزيد.
notes-remind-usage = ⏰ الاستخدام: <code>/remind 10m نص</code> — الوحدات m/h/d، أو وقت مثل <code>18:30</code> (UTC).
notes-remind-set = ⏰ تم! سأذكّرك في <b>{ $when }</b> بتوقيت UTC.
notes-limit-reminders = ⏰ لديك بالفعل { $max } تذكيرات قادمة. اشترك في 💎 VIP للمزيد.
notes-reminders-title = ⏰ <b>التذكيرات القادمة</b> ({ $count })
notes-reminders-empty = لا يوجد شيء مجدول.
notes-reminder-fire = ⏰ <b>تذكير</b>

    { $text }
notes-adm =
    📝 <b>الملاحظات</b>

    • الملاحظات المحفوظة: <b>{ $notes }</b>
    • تذكيرات قيد الانتظار: <b>{ $pending }</b>
    • تذكيرات أُرسلت: <b>{ $sent }</b>
vip-perks =
    ✅ حتى { $notes } ملاحظة
    ✅ حتى { $reminders } تذكيراً قادماً
vip-status-none = ⚪ الخطة المجانية: { $free_notes } ملاحظة، { $free_reminders } تذكيرات.
cmd-notes = ملاحظاتك
cmd-remind = ضبط تذكير
cmd-reminders = التذكيرات القادمة
