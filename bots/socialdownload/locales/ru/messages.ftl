## SocialDownload — Русский (Russian)

## ---------- Start / general ----------
start-welcome =
    👋 Привет, <b>{ $name }</b>!

    Я скачиваю <b>видео, фото и музыку</b> из TikTok, Instagram, YouTube, X (Twitter), Facebook, Pinterest, Reddit, Threads, SoundCloud и ещё 1800+ сайтов.

    📎 <b>Просто отправь мне ссылку!</b>
    🔎 Или введи текст для поиска в YouTube.
start-referred = 🤝 Вы присоединились по приглашению друга. Добро пожаловать!

btn-help = ❓ Помощь
btn-lang = 🌍 Язык
btn-vip = 💎 VIP
btn-profile = 👤 Профиль
btn-settings = ⚙️ Настройки
btn-add-group = ➕ Добавить в группу
btn-referral = 🎁 Бесплатный VIP
btn-back = ⬅️ Назад
btn-cancel = ✖️ Отмена
btn-close = ✖️ Закрыть

help-text =
    ❓ <b>Как пользоваться</b>

    1️⃣ Скопируйте ссылку из TikTok, Instagram, YouTube, X, Facebook, Pinterest, Reddit, SoundCloud…
    2️⃣ Отправьте её мне.
    3️⃣ Получите файл в наилучшем качестве и без водяных знаков.

    <b>Команды</b>
    /start — главное меню
    /search — поиск видео на YouTube
    /music — поиск и скачивание музыки
    /profile — статистика и ваш тариф
    /settings — качество по умолчанию, формат аудио, подписи
    /vip — тарифы VIP
    /referral — приглашайте друзей и получайте VIP бесплатно
    /lang — сменить язык
    /terms — условия использования
    /support — поддержка

    💡 <b>Подсказки</b>
    • Можно использовать в любом чате: напишите <code>@{ $bot } ссылка</code>
    • Добавьте меня в группу, и я буду скачивать ссылки участников.
    • Уже скачанные ссылки отправляются мгновенно.

terms-text =
    📜 <b>Условия использования</b>

    • Бот предназначен для загрузки общедоступного контента для личного пользования.
    • Вы несете ответственность за соблюдение авторских прав.
    • Запрещено использовать бота для распространения нелегального контента.
    • Спам и злоупотребления ведут к перманентной блокировке.
    • Покупки VIP активируются мгновенно.

support-text = 💬 Поддержка: { $contact }
support-none = 💬 Контакт поддержки пока не настроен.

lang-choose = 🌍 Выберите язык интерфейса:
lang-changed = ✅ Язык успешно изменен на русский.

## ---------- Generic states ----------
throttled = 🐢 Не так быстро! Пожалуйста, подождите пару секунд.
banned = 🚫 Вы заблокированы в этом боте.
maintenance = 🛠 Бот на техническом обслуживании. Пожалуйста, попробуйте позже.
expired-menu = ⌛ Меню устарело. Отправьте ссылку повторно.
unknown = Неизвестно
state-on = ✅ Вкл
state-off = ❌ Выкл
saved = ✅ Сохранено

## ---------- Download flow ----------
dl-analyzing = 🔎 Анализирую ссылку…
dl-choose-format =
    🎬 <b>{ $title }</b>
    👤 { $uploader }  ⏱ { $duration }

    Выберите формат:
btn-best = ⭐ Лучшее качество
btn-audio = 🎵 Аудио ({ $format })
dl-queued = ⏳ В очереди… позиция: <b>{ $position }</b>
dl-starting = ⚙️ Начинаю загрузку…
dl-downloading =
    ⬇️ <b>Загрузка…</b> { $percent }%
    { $bar }
    { $done } / { $total } • { $speed }/с • ⏱ { $eta }
dl-downloading-simple = ⬇️ <b>Загрузка…</b> { $done } • { $speed }/с
dl-processing = 🛠 Обработка…
dl-uploading = 📤 Отправка в Telegram…
dl-cancelled = ❌ Загрузка отменена.
dl-cancel-too-late = Загрузка уже завершена.
dl-direct-link =
    📦 Файл слишком большой для Telegram ({ $size }).

    🔗 Прямая ссылка на скачивание (действует { $minutes } мин):
    { $link }
dl-caption-via = 📥 через @{ $bot }
dl-limit-reached =
    🚫 Вы исчерпали дневной лимит в <b>{ $limit }</b> скачиваний.

    ⏰ Сброс через { $hours }ч { $minutes }м.
    💎 Оформите VIP для безлимитной загрузки!
dl-too-many-active = ⏳ У вас уже выполняется { $count } загрузок. Дождитесь их окончания.
dl-platform-disabled = ⚠️ Скачивание с этой платформы временно отключено.
dl-quality-locked = 🔒 Качество { $quality } доступно только для VIP. Нажмите 💎 VIP для перехода.
dl-no-url = 🤔 Отправьте ссылку для скачивания или текст для поиска на YouTube.
dl-playlist =
    📃 Плейлист: <b>{ $title }</b>
    Всего элементов: { $count }

    Ваш тариф позволяет скачать до { $max } элементов. Что скачиваем?
btn-pl-video = 🎬 Первые { $n } как видео
btn-pl-audio = 🎵 Первые { $n } как аудио

## ---------- Errors ----------
error-private = 🔒 Этот контент приватный или доступен только подписчикам.
error-login = 🔐 Платформа требует авторизации для этого видео. Попробуйте позже.
error-geo = 🌍 Контент недоступен в регионе сервера.
error-live = 🔴 Прямые трансляции нельзя скачать во время эфира.
error-too_large = 📦 Файл превышает лимит размера вашего тарифа. В VIP лимит до 2 ГБ.
error-too_long = ⏱ Видео слишком длинное для вашего тарифа.
error-rate_limited = 🚦 Платформа временно ограничивает запросы. Попробуйте через минуту.
error-removed = 🗑 Контент был удален или ссылка недействительна.
error-no_media = 🤷 Не удалось найти доступные медиа по этой ссылке.
error-unsupported = ❔ Эта ссылка пока не поддерживается.
error-timeout = ⌛ Время ожидания истекло. Пожалуйста, попробуйте еще раз.
error-upload = 📤 Telegram отклонил загрузку файла. Попробуйте другое качество.
error-unknown = 😕 Произошла ошибка. Пожалуйста, попробуйте позже.
error-busy = 🧯 Сервер сейчас перегружен. Попробуйте через несколько минут.
error-queue_expired = ⌛ Запрос слишком долго ждал в очереди и был отменён. Отправьте ссылку ещё раз.
not-your-menu = 🙅 Это меню принадлежит другому пользователю.

## ---------- Force subscription ----------
fsub-required = 📢 Чтобы пользоваться ботом, подпишитесь на наш канал и нажмите «Я подписался».
btn-fsub-join = ➕ Подписаться на { $title }
btn-fsub-check = ✅ Я подписался
fsub-not-yet = ❌ Вы еще не подписались на все обязательные каналы.
fsub-ok = ✅ Спасибо! Обрабатываю вашу ссылку…
fsub-ok-nolink = ✅ Спасибо! Теперь отправьте ссылку.

## ---------- Search ----------
search-searching = 🔎 Поиск…
search-results = 🔎 Результаты по запросу <b>{ $query }</b>:
search-empty = 😕 Ничего не найдено. Попробуйте другой запрос.
search-usage = 🔎 Пример: <code>/search запрос</code>
music-usage = 🎵 Пример: <code>/music название песни</code>
search-disabled = 🔎 Поиск временно отключен.

## ---------- Profile ----------
profile-text =
    👤 <b>Ваш профиль</b>

    🆔 ID: <code>{ $id }</code>
    💎 Тариф: { $plan }
    📊 Сегодня: { $used } / { $limit }
    📥 Всего скачано: { $total }
    👥 Приглашено друзей: { $refs }
    🌍 Язык: { $lang }
plan-free = Бесплатный
plan-vip = VIP ⭐ (до { $until })
limit-unlimited = Безлимит

## ---------- Settings ----------
settings-text =
    ⚙️ <b>Настройки</b>

    🎚 Качество по умолчанию: <b>{ $quality }</b>
    🎵 Формат аудио: <b>{ $audio }</b>
    📝 Подписи к файлам: <b>{ $caption }</b>
btn-set-quality = 🎚 Качество
btn-set-audio = 🎵 Формат аудио
btn-set-caption = 📝 Подписи
settings-choose-quality = 🎚 Выберите качество по умолчанию для новых ссылок:
q-auto = Авто
q-ask = Всегда спрашивать
q-best = Лучшее
q-audio = Только аудио

## ---------- VIP ----------
vip-perks =
    ✅ До { $limit } скачиваний в день
    ✅ Качество до { $height }p
    ✅ Файлы до { $size }
    ✅ Приоритетная очередь без ожидания
    ✅ { $concurrent } одновременных загрузки
    ✅ Плейлисты до { $playlist } элементов
    ✅ Без рекламы и без обязательных подписок
vip-status-active = 🟢 Ваш VIP активен до <b>{ $until }</b>.
vip-status-none = ⚪ У вас бесплатный тариф ({ $free_limit } скачиваний/день, до { $free_height }p).
vip-invoice-title = VIP подписка — { $name }
vip-invoice-desc = { $days } дн. VIP: максимальное качество, приоритет, безлимит, без рекламы.
vip-activated = 🎉 Спасибо! Ваш VIP активирован до <b>{ $until }</b>.
vip-expiring = ⏰ Ваш VIP заканчивается через { $days } дн. Продлите через /vip!
vip-expired = ⌛ Срок действия VIP истек. Вы можете продлить его в любое время через /vip.
vip-granted = 🎁 Вам начислено <b>{ $days }</b> дн. VIP! Действует до <b>{ $until }</b>.
vip-revoked = ℹ️ Ваша VIP-подписка отозвана.
vip-refunded = ↩️ Оплата возвращена, статус VIP обновлен.
vip-no-plans = Сейчас нет доступных тарифов для покупки.
vip-plan-days = { $days } дней

## ---------- Referrals ----------
referral-text =
    🎁 <b>Приглашайте друзей — получайте VIP бесплатно!</b>

    За каждых <b>{ $required }</b> друзей, которые перейдут и скачают что-либо, вы получаете <b>{ $days }</b> дн. VIP.

    👥 Засчитано друзей: <b>{ $count }</b>
    🎯 До следующей награды: <b>{ $left }</b>

    🔗 Ваша персональная ссылка:
    <code>{ $link }</code>
referral-reward = 🎉 { $required } ваших друзей присоединились! Вам начислено <b>{ $days }</b> дн. VIP.
referral-disabled = 🎁 Реферальная программа временно отключена.
btn-share = 📤 Поделиться ссылкой
referral-share-text = 📥 Скачивай видео и музыку из TikTok, Instagram, YouTube без водяных знаков и в лучшем качестве!

## ---------- Groups ----------
group-welcome =
    👋 Спасибо за добавление в группу!
    Отправьте любую поддерживаемую ссылку в чат, и я её скачаю.
    Администраторы могут настроить меня через /settings.
group-settings =
    ⚙️ <b>Настройки группы</b>

    Автоскачивание ссылок: { $state }
btn-group-toggle = 🔁 Переключить автоскачивание
group-admin-only = ⛔ Это действие доступно только администраторам группы.
group-disabled = ⚠️ Работа в группах отключена.

## ---------- Inline ----------
inline-hint = Вставьте ссылку после имени бота
inline-hint-desc = TikTok, Instagram, YouTube, X…
inline-download = 📥 Скачать с { $platform }
inline-download-desc = Нажмите, чтобы скачать и отправить сюда
inline-processing = ⏳ Загрузка… пожалуйста, подождите
inline-open-bot = 🤖 Открыть бота
inline-failed = 😕 Не удалось скачать по этой ссылке.
inline-hint-message = 👉 Откройте @{ $bot } и отправьте ссылку на видео или музыку, чтобы скачать!
inline-sent = ✅ Отправлено в ваш личный чат с @{ $bot }.
cmd-search = Поиск видео на YouTube
cmd-music = Поиск и скачивание музыки

## ---------- Админка: загрузки ----------
sd-btn-admin-tab = 🧰 Загрузки
sd-adm-home =
    🧰 <b>Загрузки</b>

    ⏳ В очереди: <b>{ $high }</b> VIP · <b>{ $normal }</b> бесплатных
    ⚙️ Выполняется: <b>{ $running }</b>
    ☠️ Отброшено: <b>{ $dead }</b>
    🌐 Прокси: <b>{ $proxies }</b> · 🍪 Файлов cookies: <b>{ $cookies }</b>
sd-btn-dead = ☠️ Отброшенные
sd-btn-proxies = 🌐 Прокси
sd-btn-cookies = 🍪 Cookies
sd-btn-purge = 🧹 Очистить отброшенные
sd-adm-dead = ☠️ <b>Отброшенные задачи</b> (слишком много сбоев; квота уже возвращена)
sd-adm-proxies = 🌐 <b>Прокси</b> ({ $count }) — нажмите, чтобы удалить. ⚠️ = недавние сбои.
sd-btn-proxy-add = ➕ Добавить прокси
sd-btn-proxy-reset = ♻️ Сбросить счётчики сбоев
sd-adm-proxy-prompt = ➕ Отправьте URL прокси, например <code>socks5://user:pass@host:1080</code> или <code>http://host:3128</code>
sd-adm-proxy-invalid = ❌ Неверный URL прокси (http, https, socks5, socks5h) или он уже добавлен.
sd-adm-proxy-readonly = ℹ️ Прокси из SOCIALDOWNLOAD_PROXIES меняются только в окружении.
sd-adm-cookies = 🍪 <b>Файлы cookies</b> ({ $count }) — нажмите, чтобы удалить.

    Чтобы добавить, отправьте документ <code>cookies.txt</code> (формат Netscape) с названием платформы в подписи: { $platforms }
sd-adm-cookie-saved = ✅ Cookies для <b>{ $platform }</b> сохранены как <code>{ $name }</code>.
sd-adm-cookie-invalid = ❌ Отклонено: { $error }
sd-ytdlp-update = ⬆️ Доступна новая версия yt-dlp: <b>{ $latest }</b> (сейчас { $current }). Пересоберите образ воркера — устаревший yt-dlp главная причина сломанных загрузок.
