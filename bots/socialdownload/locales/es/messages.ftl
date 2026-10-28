## SocialDownload — Español (Spanish)

## ---------- Start / general ----------
start-welcome =
    👋 ¡Hola, <b>{ $name }</b>!

    Descargo <b>videos, fotos y música</b> de TikTok, Instagram, YouTube, X (Twitter), Facebook, Pinterest, Reddit, Threads, SoundCloud y más de 1800 sitios.

    📎 <b>¡Solo envíame un enlace!</b>
    🔎 O escribe cualquier texto para buscar en YouTube.
start-referred = 🤝 Te has unido mediante la invitación de un amigo. ¡Bienvenido!

btn-help = ❓ Ayuda
btn-lang = 🌍 Idioma
btn-vip = 💎 VIP
btn-profile = 👤 Perfil
btn-settings = ⚙️ Ajustes
btn-add-group = ➕ Añadir a grupo
btn-referral = 🎁 VIP Gratis
btn-back = ⬅️ Volver
btn-cancel = ✖️ Cancelar
btn-close = ✖️ Cerrar

help-text =
    ❓ <b>Cómo usar el bot</b>

    1️⃣ Copia un enlace de TikTok, Instagram, YouTube, X, Facebook, Pinterest, SoundCloud…
    2️⃣ Envíamelo por aquí.
    3️⃣ Recibe tu archivo en la mejor calidad y sin marca de agua.

    <b>Comandos</b>
    /start — menú principal
    /search — buscar videos en YouTube
    /music — buscar y descargar música
    /profile — tus estadísticas y plan
    /settings — calidad por defecto, formato de audio, subtítulos
    /vip — planes VIP
    /referral — invita amigos y gana VIP gratis
    /lang — cambiar idioma
    /terms — términos de uso
    /support — soporte

    💡 <b>Consejos</b>
    • Puedes usarme en modo inline en cualquier chat: escribe <code>@{ $bot } enlace</code>
    • Añádeme a un grupo y descargaré los enlaces compartidos allí.
    • Los enlaces descargados anteriormente se envían al instante.

terms-text =
    📜 <b>Términos de uso</b>

    • Esta herramienta es para descargar contenido público con fines personales.
    • Eres responsable de respetar los derechos de autor de las plataformas.
    • Está prohibido descargar o compartir contenido ilícito.
    • El abuso o spam provocará la suspensión permanente.
    • Las compras VIP son bienes digitales de activación instantánea.

support-text = 💬 Soporte: { $contact }
support-none = 💬 El soporte no está configurado aún.

lang-choose = 🌍 Elige tu idioma:
lang-changed = ✅ Idioma cambiado a español correctamente.

## ---------- Generic states ----------
throttled = 🐢 ¡Más despacio! Por favor, espera unos segundos.
banned = 🚫 Has sido bloqueado de este bot.
maintenance = 🛠 El bot está en mantenimiento. Inténtalo más tarde.
expired-menu = ⌛ Este menú ha expirado. Por favor, envía el enlace de nuevo.
unknown = Desconocido
state-on = ✅ Activado
state-off = ❌ Desactivado
saved = ✅ Guardado

## ---------- Download flow ----------
dl-analyzing = 🔎 Analizando enlace…
dl-choose-format =
    🎬 <b>{ $title }</b>
    👤 { $uploader }  ⏱ { $duration }

    Elige un formato:
btn-best = ⭐ Mejor calidad
btn-audio = 🎵 Audio ({ $format })
dl-queued = ⏳ En cola… posición: <b>{ $position }</b>
dl-starting = ⚙️ Iniciando descarga…
dl-downloading =
    ⬇️ <b>Descargando…</b> { $percent }%
    { $bar }
    { $done } / { $total } • { $speed }/s • ⏱ { $eta }
dl-downloading-simple = ⬇️ <b>Descargando…</b> { $done } • { $speed }/s
dl-processing = 🛠 Procesando…
dl-uploading = 📤 Subiendo a Telegram…
dl-cancelled = ❌ Descarga cancelada.
dl-cancel-too-late = La descarga ya ha finalizado.
dl-direct-link =
    📦 El archivo supera el límite de Telegram ({ $size }).

    🔗 Enlace de descarga directa (válido por { $minutes } min):
    { $link }
dl-caption-via = 📥 vía @{ $bot }
dl-limit-reached =
    🚫 Has alcanzado tu límite diario de <b>{ $limit }</b> descargas.

    ⏰ Se reinicia en { $hours }h { $minutes }m.
    💎 ¡Obtén VIP para descargas ilimitadas!
dl-too-many-active = ⏳ Ya tienes { $count } descargas activas. Espera a que finalicen.
dl-platform-disabled = ⚠️ Las descargas de esta plataforma están desactivadas temporalmente.
dl-quality-locked = 🔒 La calidad { $quality } es exclusiva para usuarios VIP. Pulsa 💎 VIP para mejorar tu cuenta.
dl-no-url = 🤔 Envíame un enlace para descargar o texto para buscar en YouTube.
dl-playlist =
    📃 Lista de reproducción: <b>{ $title }</b>
    Elementos: { $count }

    Tu plan permite hasta { $max } elementos. ¿Qué deseas descargar?
btn-pl-video = 🎬 Primeros { $n } como video
btn-pl-audio = 🎵 Primeros { $n } como audio

## ---------- Errors ----------
error-private = 🔒 Este contenido es privado o exclusivo para seguidores.
error-login = 🔐 La plataforma requiere inicio de sesión para este contenido.
error-geo = 🌍 Este contenido no está disponible en la región del servidor.
error-live = 🔴 Las transmisiones en vivo no pueden descargarse mientras se emiten.
error-too_large = 📦 Este archivo supera el tamaño permitido en tu plan. Con 💎 VIP puedes descargar hasta 2 GB.
error-too_long = ⏱ La duración supera el límite de tu plan.
error-rate_limited = 🚦 La plataforma ha limitado temporalmente las peticiones. Prueba en un minuto.
error-removed = 🗑 El contenido fue eliminado o el enlace no es válido.
error-no_media = 🤷 No se encontró ningún medio descargable en este enlace.
error-unsupported = ❔ Este enlace no es compatible.
error-timeout = ⌛ Se agotó el tiempo de espera. Por favor, inténtalo de nuevo.
error-upload = 📤 Telegram rechazó la subida. Prueba con otra resolución.
error-unknown = 😕 Ha ocurrido un error. Por favor, inténtalo más tarde.
error-busy = 🧯 El servidor está ocupado. Inténtalo de nuevo en unos minutos.
error-queue_expired = ⌛ Tu solicitud esperó demasiado en la cola y se canceló. Envía el enlace de nuevo.
not-your-menu = 🙅 Este menú pertenece a otra persona.

## ---------- Force subscription ----------
fsub-required = 📢 Para usar el bot, únete a nuestros canales y luego presiona «Ya me he unido».
btn-fsub-join = ➕ Unirme a { $title }
btn-fsub-check = ✅ Ya me he unido
fsub-not-yet = ❌ Aún no te has unido a todos los canales requeridos.
fsub-ok = ✅ ¡Gracias! Procesando tu enlace…
fsub-ok-nolink = ✅ ¡Gracias! Ahora envíame un enlace.

## ---------- Search ----------
search-searching = 🔎 Buscando…
search-results = 🔎 Resultados para <b>{ $query }</b>:
search-empty = 😕 No se encontraron resultados. Prueba con otras palabras.
search-usage = 🔎 Uso: <code>/search consulta</code>
music-usage = 🎵 Uso: <code>/music título de canción</code>
search-disabled = 🔎 La búsqueda está desactivada actualmente.

## ---------- Profile ----------
profile-text =
    👤 <b>Tu perfil</b>

    🆔 ID: <code>{ $id }</code>
    💎 Plan: { $plan }
    📊 Hoy: { $used } / { $limit }
    📥 Descargas totales: { $total }
    👥 Amigos invitados: { $refs }
    🌍 Idioma: { $lang }
plan-free = Gratuito
plan-vip = VIP ⭐ (hasta { $until })
limit-unlimited = Ilimitado

## ---------- Settings ----------
settings-text =
    ⚙️ <b>Ajustes</b>

    🎚 Calidad predeterminada: <b>{ $quality }</b>
    🎵 Formato de audio: <b>{ $audio }</b>
    📝 Subtítulos/Texto: <b>{ $caption }</b>
btn-set-quality = 🎚 Calidad
btn-set-audio = 🎵 Formato de audio
btn-set-caption = 📝 Subtítulos
settings-choose-quality = 🎚 Elige la calidad predeterminada para enlaces nuevos:
q-auto = Automática
q-ask = Preguntar siempre
q-best = La mejor
q-audio = Solo audio

## ---------- VIP ----------
vip-perks =
    ✅ Hasta { $limit } descargas al día
    ✅ Calidad hasta { $height }p
    ✅ Archivos de hasta { $size }
    ✅ Cola prioritaria sin esperas
    ✅ { $concurrent } descargas simultáneas
    ✅ Listas de reproducción de hasta { $playlist } elementos
    ✅ Sin anuncios ni canales obligatorios
vip-status-active = 🟢 Tu VIP está activo hasta el <b>{ $until }</b>.
vip-status-none = ⚪ Estás en el plan gratuito ({ $free_limit } descargas/día, hasta { $free_height }p).
vip-invoice-title = Suscripción VIP — { $name }
vip-invoice-desc = { $days } días VIP: calidad máxima, prioridad, descargas ilimitadas y sin publicidad.
vip-activated = 🎉 ¡Gracias! Tu suscripción VIP está activa hasta el <b>{ $until }</b>.
vip-expiring = ⏰ Tu VIP caduca en { $days } día(s). ¡Renueva con /vip para mantener tus ventajas!
vip-expired = ⌛ Tu suscripción VIP ha caducado. Puedes renovar cuando quieras con /vip.
vip-granted = 🎁 ¡Has recibido <b>{ $days }</b> días VIP de regalo! Válido hasta el <b>{ $until }</b>.
vip-revoked = ℹ️ Tu suscripción VIP ha sido retirada.
vip-refunded = ↩️ Tu pago fue reembolsado y se ajustó el estado VIP.
vip-no-plans = No hay planes disponibles en este momento.
vip-plan-days = { $days } días

## ---------- Referrals ----------
referral-text =
    🎁 <b>Invita amigos — ¡consigue VIP gratis!</b>

    Por cada <b>{ $required }</b> amigos que se unan y descarguen un archivo, obtienes <b>{ $days }</b> días VIP.

    👥 Amigos válidos: <b>{ $count }</b>
    🎯 Próxima recompensa en: <b>{ $left }</b>

    🔗 Tu enlace de invitación personal:
    <code>{ $link }</code>
referral-reward = 🎉 ¡Se han unido { $required } amigos! Has recibido <b>{ $days }</b> días VIP gratis.
referral-disabled = 🎁 El programa de referidos está desactivado actualmente.
btn-share = 📤 Compartir enlace
referral-share-text = 📥 ¡Descarga videos y música de TikTok, Instagram, YouTube y más sin marca de agua y en máxima calidad!

## ---------- Groups ----------
group-welcome =
    👋 ¡Gracias por añadirme al grupo!
    Envía cualquier enlace compatible y lo descargaré aquí.
    Los administradores pueden configurarme con /settings.
group-settings =
    ⚙️ <b>Ajustes del grupo</b>

    Descarga automática de enlaces: { $state }
btn-group-toggle = 🔁 Alternar descarga automática
group-admin-only = ⛔ Esta acción solo está permitida a los administradores del grupo.
group-disabled = ⚠️ El modo de grupos está desactivado temporalmente.

## ---------- Inline ----------
inline-hint = Pega un enlace tras el nombre del bot
inline-hint-desc = TikTok, Instagram, YouTube, X…
inline-download = 📥 Descargar de { $platform }
inline-download-desc = Pulsa para descargar y enviar aquí
inline-processing = ⏳ Descargando… espera un momento
inline-open-bot = 🤖 Abrir el bot
inline-failed = 😕 No se pudo descargar este enlace.
inline-hint-message = 👉 ¡Abre @{ $bot } y envía cualquier enlace de vídeo o música para descargarlo!
inline-sent = ✅ Enviado a tu chat privado con @{ $bot }.
cmd-search = Buscar vídeos en YouTube
cmd-music = Buscar y descargar música

## ---------- Admin: descargas ----------
sd-btn-admin-tab = 🧰 Descargas
sd-adm-home =
    🧰 <b>Descargas</b>

    ⏳ En espera: <b>{ $high }</b> VIP · <b>{ $normal }</b> gratis
    ⚙️ En curso: <b>{ $running }</b>
    ☠️ Descartadas: <b>{ $dead }</b>
    🌐 Proxies: <b>{ $proxies }</b> · 🍪 Archivos de cookies: <b>{ $cookies }</b>
sd-btn-dead = ☠️ Descartadas
sd-btn-proxies = 🌐 Proxies
sd-btn-cookies = 🍪 Cookies
sd-btn-purge = 🧹 Vaciar descartadas
sd-adm-dead = ☠️ <b>Tareas descartadas</b> (fallaron demasiadas veces; ya reembolsadas)
sd-adm-proxies = 🌐 <b>Proxies</b> ({ $count }) — pulsa uno para quitarlo. ⚠️ = fallos recientes.
sd-btn-proxy-add = ➕ Añadir proxy
sd-btn-proxy-reset = ♻️ Reiniciar contadores de fallos
sd-adm-proxy-prompt = ➕ Envía una URL de proxy, p. ej. <code>socks5://user:pass@host:1080</code> o <code>http://host:3128</code>
sd-adm-proxy-invalid = ❌ URL de proxy no válida (http, https, socks5, socks5h) o ya existe.
sd-adm-proxy-readonly = ℹ️ Los proxies de SOCIALDOWNLOAD_PROXIES solo se cambian en el entorno.
sd-adm-cookies = 🍪 <b>Archivos de cookies</b> ({ $count }) — pulsa uno para borrarlo.

    Para añadir uno, envía un documento <code>cookies.txt</code> (formato Netscape) con la plataforma como pie: { $platforms }
sd-adm-cookie-saved = ✅ Cookies de <b>{ $platform }</b> guardadas como <code>{ $name }</code>.
sd-adm-cookie-invalid = ❌ Rechazado: { $error }
sd-ytdlp-update = ⬆️ Hay una nueva versión de yt-dlp: <b>{ $latest }</b> (en uso { $current }). Reconstruye la imagen del worker para actualizar: un yt-dlp antiguo es la causa n.º 1 de descargas rotas.
