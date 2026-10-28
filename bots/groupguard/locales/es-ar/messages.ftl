## Group Guard — independently authored Argentine Spanish variation.
group-welcome = 🛡 ¡Gracias por añadirme! Haceme administrador con permisos para borrar mensajes, restringir miembros y fijar mensajes. Usá /settings para configurar la protección.
gg-start =
    🛡 ¡Hola, <b>{ $name }</b>! Soy <b>Group Guard</b>, el gestor de seguridad de tu grupo.
    Ofrezco verificación de nuevos miembros, protección contra mensajes masivos y CAS, bloqueos de contenido, listas de palabras prohibidas, moderación, notas, filtros, normas y bienvenidas. Agregame como administrador y consultá /settings o /help.
gg-help = 📖 Usá /help para ver las categorías y /help nombre_del_comando para buscar. Moderación: /ban /mute /kick /warn. Contenido: /save /filter /rules. Protección: /lock /blocklist /night. /settings abrí el panel privado del grupo.
gg-welcome-default = 👋 ¡Bienvenido, { "{" }mention{ "}" }, a <b>{ "{" }group{ "}" }</b>!
gg-credit = 🛡 Protegido por @{ $bot }
gg-btn-add = ➕ Añadirme a un grupo
gg-btn-commands = 📖 Comandos
gg-btn-rules = 📜 Normas
gg-btn-human = ✅ Soy una persona
gg-btn-unwarn = ↩️ Quitar advertencia (administradores)
gg-btn-locks = 🔒 Bloqueos ({ $count })
gg-btn-open-settings = ⚙️ Abrir ajustes
gg-btn-admin-tab = 🛡 Grupos
gg-captcha = 🤖 { $user }, confirmá que sos una persona en <b>{ $minutes } minutos</b> para evitar la expulsión.
gg-captcha-button = Tocá el botón de abajo 👇
gg-captcha-math = ¿Cuánto es <b>{ $a } + { $b }</b>?
gg-captcha-not-you = Este botón correspondé a otra persona.
gg-captcha-ok = ✅ ¡Bienvenido!
gg-captcha-wrong = ❌ Respuesta incorrecta. Quedan { $left } intentos.
gg-captcha-failed = ❌ Demasiadas respuestas incorrectas.
gg-captcha-passed = ✅ { $user } se ha verificado. ¡Bienvenido!
gg-cas-banned = 🚫 { $user } figura como remitente de spam en CAS y fue vetado.
gg-join-request = 👋 Para entrar en <b>{ $group }</b>, confirmá que sos una persona:
gg-join-approved = ✅ Se ha aprobado tu entrada. ¡Bienvenido!
gg-join-expired = ⌛ Esta solicitud ha caducado. Pedí entrar de nuevo.
gg-goodbye = 👋 { $user } ha salido del grupo.
gg-flood-mute = 🌊 { $user } ha enviado demasiados mensajes y fue silenciado temporalmente.
gg-flood-kick = 🌊 { $user } fue extocádo por enviar demasiados mensajes.
gg-flood-ban = 🌊 { $user } fue vetado por enviar demasiados mensajes.
gg-newbie-links = 🆕 { $user }, los nuevos miembros no pueden publicar enlaces durante las primeras { $hours } horas.
gg-spam-banned = 🧠 { $user } fue vetado por publicar spam.
gg-reason-blocklist = palabra prohibida
gg-need-right = ⛔ Necesitas el permiso de administrador «{ $right }».
gg-right-admin = administrador
gg-right-restrict = restringir miembros
gg-right-delete = borrar mensajes
gg-right-pin = fijar mensajes
gg-right-change_info = cambiar la información del grupo
gg-admins-only = ⛔ Solo administradores.
gg-need-target = 👤 Respondé a un mensaje o indicá un @usuario verificado o un ID de usuario.
gg-target-admin = 🙅 No puedo aplicar esta acción a un administrador.
gg-bot-no-rights = ⚠️ Necesito ser administrador y tener los permisos correspondientes.
gg-banned = 🔨 { $user } fue vetado. Motivo: { $reason }
gg-banned-for = 🔨 { $user } fue vetado durante { $time }. Motivo: { $reason }
gg-unbanned = ✅ Se ha retirado el veto de { $user }.
gg-kicked = 👢 { $user } fue extocádo. Motivo: { $reason }
gg-muted = 🔇 { $user } fue silenciado. Motivo: { $reason }
gg-muted-for = 🔇 { $user } fue silenciado durante { $time }. Motivo: { $reason }
gg-unmuted = 🔊 { $user } puede volver a hablar.
gg-warned = ⚠️ { $user } ha recibido una advertencia ({ $count }/{ $limit }). Motivo: { $reason }
gg-warn-limit-ban = 🔨 { $user } ha alcanzado { $limit } advertencias y fue vetado.
gg-warn-limit-mute = 🔇 { $user } ha alcanzado { $limit } advertencias y fue silenciado.
gg-warn-limit-kick = 👢 { $user } ha alcanzado { $limit } advertencias y fue extocádo.
gg-unwarned = ↩️ Se ha quitado una advertencia de { $user } ({ $count }/{ $limit }).
gg-warn-removed = ↩️ Advertencia retirada por { $admin }.
gg-warns = ⚠️ { $user } tiene { $count }/{ $limit } advertencias.
gg-warns-reset = 🧽 Se han restablecido las advertencias de { $user }.
gg-purge-reply = 🧹 Respondé al primer mensaje que querés borrar.
gg-purged = 🧹 Se han borrado { $count } mensajes.
gg-pin-reply = 📌 Respondé al mensaje que querés fijar.
gg-report-reply = 🚨 Respondé al mensaje que querés denunciar.
gg-reported = 🚨 Se ha denunciado a { $user } ante los administradores.
gg-setlog-usage = 📒 Haceme administrador de tu canal de registro y usá <code>/setlog -100…</code> con su ID.
gg-setlog-failed = ⚠️ No puedo publicar en ese destino. Agregame allí como administrador primero.
gg-setlog-done = 📒 Canal de registro conectado.
gg-setlog-off = 📒 Canal de registro desconectado.
gg-log-connected = 📒 Este chat recibe el registro de moderación de <b>{ $group }</b>.
gg-log-flood = 🌊 Mensajes masivos: { $user } → { $action }
gg-log-report = 🚨 Denuncia sobre { $user }
gg-log-spam = 🧠 Veto por spam detectado por IA: { $user }
    <blockquote>{ $text }</blockquote>
gg-rules = 📜 <b>Normas</b>
    { $rules }
gg-no-rules = 📜 Todavía no hay normas. Los administradores pueden usar /setrules texto.
gg-rules-saved = 📜 Normas guardadas.
gg-rules-cleared = 📜 Normas borradas.
gg-welcome-usage = 👋 Usá <code>/setwelcome Hola {"{"}mention{"}"}, ¡bienvenido a {"{"}group{"}"}!</code> o respondé a un mensaje.
gg-welcome-saved = 👋 Bienvenida guardada.
gg-welcome-reset = 👋 Se ha restaurado la bienvenida predeterminada.
gg-note-usage = 📝 Usá <code>/save nombre texto</code> o respondé a un mensaje con <code>/save nombre</code>.
gg-filter-usage = 🔁 Usá <code>/filter palabra respuesta</code> o respondé a un mensaje con <code>/filter palabra</code>.
gg-note-saved = 📝 Nota guardada; puede consultárse con <code>#{ $key }</code> según sus permisos de acceso.
gg-filter-saved = 🔁 Respondéré cuando coincida «{ $key }».
gg-notes-empty = 📝 Todavía no hay notas.
gg-filters-empty = 🔁 Todavía no hay filtros.
gg-notes-list = 📝 <b>Notas</b>
gg-filters-list = 🔁 <b>Filtros</b>
gg-item-deleted = 🗑 Se ha borrado «{ $key }».
gg-item-missing = 🤷 No hay contenido guardado con ese nombre.
gg-items-limit = 📦 Este grupo ha alcanzado el límite de notas y filtros.
gg-lock-usage = 🔒 Usá <code>/lock links</code>. Tipos: { $types } o <code>all</code>.
gg-locked = 🔒 Bloqueado: { $types }
gg-unlocked = 🔓 Desbloqueado: { $types }
gg-locks-title = 🔒 <b>Bloqueos de contenido</b>
gg-locks-panel = 🔒 <b>Bloqueos</b>: el contenido bloqueado se borra; los administradores están exentos.
gg-blocklist = 🚫 <b>Palabras prohibidas</b>: { $words }
gg-blocklist-empty = 🚫 No hay palabras prohibidas.
gg-blocklist-usage = 🚫 <code>/addblock palabra, otra frase</code> · <code>/rmblock palabra</code>
gg-blocklist-saved = 🚫 Lista de bloqueo actualizada ({ $count } entradas).
gg-night-usage = 🌙 <code>/night 23 7 +3</code>: cierre de 23:00 a 07:00 UTC+3; <code>/night off</code> lo desactiva.
gg-night-on = 🌙 Modo nocturno: cierre de { $start } a { $end } ({ $tz }).
gg-night-off = 🌙 Modo nocturno desactivado.
gg-night-start = 🌙 ¡Buenas noches! El grupo está cerrado hasta { $end }.
gg-night-end = ☀️ ¡Buenos días! El grupo está abierto de nuevo.
gg-panel = ⚙️ <b>Ajustes — { $group }</b>
    Tocá una opción para cambiarla. Horario nocturno: { $night }; usá /night para modificarlo.
gg-panel-sent = 📬 Te envié los ajustes por privado.
gg-panel-start-first = 📬 Iniciá primero una conversación privada conmigo y tocá el botón de abajo.
gg-credit-vip = 💎 Ocultar la línea de protección requiere VIP. Usá /vip en privado.
gg-opt-wel = 👋 Bienvenida: { $value }
gg-opt-cln = 🧹 Borrar mensajes de entrada: { $value }
gg-opt-bye = 👋 Despedida: { $value }
gg-opt-cap = 🤖 Verificación: { $value }
gg-opt-cpm = ⏱ Tiempo de verificación: { $value } min
gg-opt-fld = 🌊 Límite de mensajes masivos: { $value }
gg-opt-fla = 🌊 Acción contra mensajes masivos: { $value }
gg-opt-wrn = ⚠️ Límite de advertencias: { $value }
gg-opt-wra = ⚠️ Acción por advertencias: { $value }
gg-opt-act = ⏳ Silencio/veto automático: { $value } min
gg-opt-cas = 🛡 Protección CAS: { $value }
gg-opt-nwb = 🆕 Nuevos miembros sin enlaces: { $value } h
gg-opt-ais = 🧠 Protección contra spam con IA: { $value }
gg-opt-ngt = 🌙 Modo nocturno: { $value }
gg-opt-crd = 🏷 Línea de crédito: { $value }
gg-opt-lang = 🌐 Idioma: { $value }
gg-val-button = botón
gg-val-math = cálculo
gg-val-off = desactivado
gg-val-mute = silenciar
gg-val-kick = extocár
gg-val-ban = vetar
gg-adm = 🛡 <b>Group Guard</b>
    Grupos protegidos: <b>{ $groups }</b>; advertencias: <b>{ $warns }</b>; notas y filtros: <b>{ $items }</b>.
cmd-settings = Ajustes del grupo
cmd-help = Guía de comandos
gg-auth-denied = No se ha podido verificar la autorización. No ha cambiado nada.
gg-target-invalid = Elegí un miembro humano conocido. No se ha podido verificar al destinatario.
gg-duration-invalid = Usá una duración de 60s a 365d. Los comandos temporales necesitan una duración.
gg-reason-invalid = El motivo admite como máximo 256 caractsos.
gg-outcome-failed = La acción pedída ha fallado o no se ha podido autorizar.
gg-outcome-partial = La acción solo se ha completado parcialmente. El veto puede permanecer si falla la restitución tras extocár.
gg-outcome-ancillary = La acción principal se ha completado, pero ha fallado un paso relacionado.
gg-review-request = Revisión: <b>{ $operation }</b>
    Destinatario: { $target }
    Detalles: { $details }
    Duración (segundos): { $duration }
    Una persona con permisos actuales puede aprobarla durante 120 segundos.
gg-review-approve = Aprobar esta acción
gg-review-unavailable = El almacenamiento de revisiones no está disponible. Enviá un comando nuevo.
gg-review-expired = Esta revisión ha caducado, es inválida o ya se ha utilizado.
gg-review-consumed = Esta revisión ya se ha utilizado. Revisá el resultado; enviá otro comando para reintentar.
gg-duration-permanent = Permanente / sin temporizador
gg-purge-ack = Se solicitó borrar { $requested } IDs de mensaje; la API reconoció { $acknowledged }. No se conoce el número confirmádo de mensajes borrados.
gg-warning-removed = Advertencia retirada.
gg-review-details-above = El contenido pedído completo aparece justo arriba.
gg-warn-pending = Advertencia registrada; ya se está procesando una acción por el umbral.
gg-done = Completado.
gg-setting-saved = Ajuste { $setting } guardado.
gg-setting-value = { $setting }: { $value }
gg-setting-invalid = Ajuste inválido. Usá on/off, un modo válido o una duración como 10m.
gg-warning-settings = Advertencias: límite { $limit }; modo { $mode }; sanción { $duration }; caducidad { $expiry }.
gg-admin-changed = Acción { $action } completada para { $user }.
gg-admin-list = Administradores públicos:
    { $admins }
gg-approved = { $user } aprobado. Motivo: { $reason }
gg-unapproved = Se han retirado { $count } aprobaciones.
gg-approval-status = Aprobación de { $user }: { $status }. Motivo: { $reason }
gg-approval-list = Usuarios aprobados:
    { $approvals }
gg-next-page = Más entradas: { $command }
gg-range-invalid = Rango inválido. Seleccioná entre 1 y { $cap } IDs de mensaje.
gg-range-start = Inicio guardado para ti en este tema durante 10 minutos. Respondé al último mensaje con /purgeto.
gg-range-missing = No hay un inicio guardado para ti en este tema. Usá /purgefrom en el primer mensaje.
gg-content-needed = Proporciona contenido o respondé a él; máximo 3500 caractsos.
gg-log-status = Destino del registro: { $destination }. Categorías activas: { $categories }.
gg-log-unverified = No tengo una recepción verificada de ese comando original del canal. Enviá /setlog al canal primero.
gg-log-forward = Reenviá este comando /setlog original a tu grupo. El administrador que conecta ambos chats necesita cambiar información en los dos.
gg-info = Nombre: { $name }
    Usuario: { $username }
    ID: <code>{ $id }</code>
    Membresía: { $membership }
gg-unknown = Desconocido
gg-chat-id = ID del chat: <code>{ $id }</code>
gg-on = Activado
gg-off = Desactivado
gg-anon-enabled = Se ha activado la suposición de administrador anónimo en este grupo. Sus comandos usan los permisos del bot sin identificar a la persona. Las acciones del propietario siguen necesitando al creador verificado. Usá /anonadmin off para recuperar la revisión humana.
gg-right-invite_users = invitar usuarios
gg-right-promote_members = nombrar administradores
gg-right-manage_topics = gestionar temas
gg-right-creator = creador del grupo
gg-log-join = { $user } ha entrado.
gg-log-leave = { $user } ha salido.
gg-warning-row = • #{ $id }: { $reason } (caduca: { $expiry })
gg-menu-prompt = Elegí una opción.
gg-content-invalid = El contenido es inválido o supera los límites de Telegram. Revisá el nombre, formato, modificadores y botones.
gg-content-unavailable = El contenido no está disponible o tu membresía actual no permite acceder.
gg-btn-private-note = Abrir nota
gg-open-private = Abrí este contenido en privado:
gg-items-cleared = Se han borrado { $count } entradas.
gg-clearall-confirm = El creador del grupo puede confirmár con <code>/{ $command } confirm</code>.
gg-button-usage = Usá <code>/button "Etiqueta" https://example.com</code>. Agregá <code>"Nota" #nombre same</code> en otra línea para un botón en la misma fila. Recibirás el marcado y una vista previa funcional.
gg-btn-accept-rules = Aceptar normas
gg-btn-open-verification = Abrir verificación
gg-captcha-private = { $user }, abrí la prueba privada para verificar tu membresía.
gg-captcha-choice = Elegí la coincidencia de la imagen con los botones. Modo: { $mode }; posición del carácter: { $position }.
gg-captcha-settings = Verificación: { $enabled }; modo: { $mode }; extocár: { $kick }; plazo: { $seconds } segundos; fin automático del silencio: { $release }.
gg-captcha-dependency = Activa las bienvenidas antes de activar la verificación. Guarda normas antes de exigir su aceptación.
gg-val-text = Imagen de texto
gg-val-text2 = Imagen de carácter
gg-captcha-attempts-exhausted = La verificación ha fallado tras demasiadas respuestas incorrectas. Se ha aplicado la restricción correspondiente.
gg-captcha-admin-exempt = Ahora sos administrador del grupo. Esta prueba de verificación ha terminado.
gg-captcha-question-text = Elegí la palabra que aparece en la imagen.
gg-captcha-question-math = Resuelve la ecuación de la imagen y elegí su respuesta.
gg-captcha-question-text2 = Elegí el carácter { $position } de la imagen, de izquierda a derecha.
gg-locktypes = Bloqueos disponibles: <code>{ $types }</code>
gg-allowlist-title = Excepciones a los bloqueos
gg-allowlist-invalid = Excepción inválida. Usá un dominio/ruta, una invitación exacta, @chat o una identidad declarada como stickerpack:nombre.
gg-reason-lock = Contenido bloqueado: { $types }
gg-lock-applied = Política de bloqueo aplicada a { $types }. Motivo: { $reason }
gg-reaction-failed = No se pudo aplicar la restricción de reacción: { $code }. Este servidor de Bot API puede no admitir su retirada.
gg-reaction-anonymous = Una actualización de reacciones anónimas no tiene identidad de usuario ni chat actor. La API de retirada la exige; no se afirma haber retirado ninguna reacción.
gg-none = Ninguno
gg-blocklist-title = Lista de bloqueo
gg-blocklist-invalid = Activador, motivo o acción inválidos. Revisá las frases entre comillas, escapes de comodines y duración de los modos temporales.
gg-blocklist-settings = Modo de bloqueo: { $mode }; borrar mensajes coincidentes: { $delete }.
gg-blocklist-action = Política de lista de bloqueo aplicada a { $user }. Motivo: { $reason }
gg-flood-status = Mensajes masivos: límite consecutivo { $consecutive } (al llegar a N); ventana { $count } / { $seconds }s (al superar N). Acción { $mode }, { $duration }; borrar secuencia { $clear }.
gg-raid-status = Protección contra ataques { $active }; hasta { $until }. Activación { $period }; veto { $ban }; umbral automático { $auto } entradas/minuto. Activar: /antiraid on · Parar: /antiraid off
gg-raid-banned = 🛡 { $user } fue vetado temporalmente durante la protección contra ataques.
gg-raid-declined = 🛡 Se ha rechazado la entrada de { $user } durante la protección contra ataques.
gg-silent-consent-required = El creador debe permitir las acciones silenciosas con un registro configurado antes de elegir esta acción.
gg-btn-enable-raid = Activar protección contra ataques
gg-human-required = Esta operación requiere una persona identificable.
gg-group-message-required = Ejecuta el comando sobre un mensaje o tema real del grupo; los IDs privados no identifican mensajes del grupo.
gg-connection-private = Usá este comando de conexión en nuestra conversación privada.
gg-connection-disconnected = Desconectado. Tus cinco grupos recientes siguen disponibles para reconectar.
gg-connection-current = Conectado a <b>{ $group }</b>. La membresía y los permisos actuales se revisán en cada operación.
gg-connection-none = No hay conexión activa. Usá /connect GROUP_ID o /connect @grupo.
gg-connection-open = Abrí tu conexión personal en nuestra conversación privada.
gg-btn-connect = Conectar en privado
gg-connection-history = Tus cinco grupos recientes. Elegí uno para reconectar; debés seguir siendo miembro.
gg-connection-unavailable = Conexión no disponible. Debes ser miembro humano actual y este bot debe ser administrador allí.
gg-catalog-unresolved = /{ $command } aparece en el catálogo sin una acción definida. Usá /notes o /flood para las funciones implementadas.
gg-cleanup-failed = La limpieza ha fallado o no está disponible; no se afirma haber borrado nada.
gg-disabled-list = Comandos: <code>{ $commands }</code>. /disable NOMBRE y /enable NOMBRE controlan la ejecución; /disabledel controla el borrado; /disableadmin incluye a administradores.
gg-cleanup-types = Categorías de limpieza disponibles: { $types }
gg-cleanup-selected = Categorías de limpieza elegidas: { $types }
gg-advanced-status = { $setting }: { $value }. El silencio automático necesita permiso del creador y registro. Los comandos de bots requieren permisos normales y conservan la revisión de cambios por defecto. Configura la visibilidad entre bots en BotFather.
gg-action-topic = Tema de acciones: { $topic }. /setactiontopic en un tema de foro lo selecciona. El tema general/predeterminado es 1.
gg-topic-unavailable = Se requiere un grupo de foro actual y los permisos de gestión de temas correspondientes.
gg-topic-id-required = En un chat privado conectado, indicá explícitamente el ID del tema.
gg-topic-general-delete = El tema general no puede borrarse. La confirmáción requiere una persona identificable.
gg-topic-delete-confirm = ¿Borrar el tema { $topic } y sus mensajes? Confirmáción personal válida durante dos minutos.
gg-btn-confirm-delete = Confirmár borrado
gg-topic-changed = Acción { $action } completada para el tema { $topic }.
gg-broadcast-owner = Solo el operador configurado de este bot o el propietario real de la instancia hija puede emitir a sus grupos.
gg-broadcast-queued = Emisión { $id } en cola. Los destinos y resultados están aislados por bot.
gg-broadcast-busy = Hay otra emisión activa o no ha terminado el intervalo de creación de cinco minutos.
gg-broadcast-empty = No tenés una emisión a grupos en este bot.
gg-broadcast-status = Emisión { $id }: { $status }. En cola: { $queued }; enviados: { $sent }; fallidos: { $failed }; inciertos: { $uncertain }; cancelados: { $cancelled }.
gg-fed-created = Federación <b>{ $name }</b> creada. Su ID en este bot es <code>{ $id }</code>.
gg-fed-info = <b>{ $name }</b>
    ID: <code>{ $id }</code>; propietario: <code>{ $owner }</code>; administradores: { $admins }.
    Motivos obligatorios: { $reasons }; avisos al propietario: { $notifications }; registro: { $log }.
gg-fed-list = Tus federaciones como propietario o administrador:
    { $rows }
gg-fed-admins = Primero el propietario, después los administradores de la federación:
    { $rows }
gg-fed-quiet = Explicaciones pasivas silenciosas: { $value }. La aplicación de vetos sigue activa.
gg-fed-policy = Motivos obligatorios: { $reasons }; avisos al propietario: { $notifications }.
gg-fed-confirm-delete = ¿Borrar <b>{ $name }</b> (<code>{ $id }</code>)? Los datos y afiliaciones de la federación se eliminarán permanentemente. Los vetos existentes en Telegram permanecerán. Confirmá durante los próximos cinco minutos.
gg-fed-confirm-log = ¿Establecer el registro de <b>{ $name }</b> (<code>{ $id }</code>) en <code>{ $destination }</code>? Confirmá en cinco minutos. Se volverán a comprobar tus permisos y el permiso de publicación del bot.
gg-fed-confirm-sent = Se ha enviado una confirmáción personal al propietario de la federación.
gg-fed-deleted = Federación borrada. Los vetos existentes en Telegram permanecen.
gg-fed-log-set = Destino del registro de la federación: <code>{ $destination }</code>.
gg-fed-cancel = Cancelar
gg-fed-cancelled = Cancelado.
gg-fed-saved-delivery-failed = Cambio guardado, pero ha fallado el envío de un aviso o del registro. Revisá el destino y el acceso del bot.
gg-fed-error-authority = Se requiere el propietario actual de la federación o el rol correspondiente. Los cargos en grupos de Telegram no otorgan autoridad en la federación.
gg-fed-error-private = Usá este comando en tu propia conversación privada con este bot.
gg-fed-error-group = Usá este comando en el grupo real. Una conexión privada no selecciona el grupo de la federación.
gg-fed-error-owned = Ya posees una federación en este bot. Usá /fedinfo, /renamefed o /delfed en privado.
gg-fed-error-name = Indicá un nombre no vacío sin caractsos de control. Se limitará a 64 caractsos.
gg-fed-error-id = Indicá un UUID de federación válido de este bot. Los IDs de Rose no se integran en este servicio independiente.
gg-fed-error-missing = No se ha encontrado una federación en este bot o contexto.
gg-fed-error-creator = Solo el creador actual del grupo de Telegram puede afiliarlo o retirarlo de una federación.
gg-fed-error-target = Indicá un ID humano positivo, respondé a una persona o usá un nombre verificado actualmente. No se puede destituir al propietario.
gg-fed-error-value = Argumentos de federación inválidos. Usá on/off para sus políticas y un ID válido cuando corresponda.
gg-fed-error-stale = La confirmáción ha caducado, ya se utilizó o cambió el estado de la federación, propietario o destino. Pedí otra.
gg-fed-error-destination = El propietario necesita permisos administrativos actuales en el destino y el bot debe poder publicar allí. Los canales requieren post_messages.
gg-fed-error-delivery = No se ha podido enviar o vincular la confirmáción personal. Abrí un chat privado con el bot y reintenta.
gg-fed-event = Federación <b>{ $name }</b> (<code>{ $id }</code>): { $event }. Actor: <code>{ $user }</code>.
gg-fed-event-rename = nombre cambiado
gg-fed-event-delete = borrada; los vetos de Telegram permanecen
gg-fed-event-promote = administrador añadido
gg-fed-event-demote = administrador retirado
gg-fed-event-self-remove = administrador dimitido
gg-fed-event-reason = política de motivos cambiada
gg-fed-event-notif = política de avisos al propietario cambiada
gg-fed-event-log = destino del registro cambiado
gg-fed-event-unlog = destino del registro eliminado
gg-fed-event-ban = política de veto guardada; aplicación en cola
gg-fed-event-unban = política de veto retirada; liberación de restricciones propias en cola
gg-fed-event-subscribe = suscripción a vetos añadida; usuarios observados pendientes de revisión
gg-fed-event-unsubscribe = suscripción a vetos retirada; se conservan las demás fuentes
gg-fed-ban-details = Destinatario: <code>{ $user }</code>. Motivo: { $reason }
gg-fed-passive = La política de la federación veta a { $user }. Fuente: <b>{ $source }</b> (<code>{ $id }</code>). Motivo: { $reason }
gg-fed-enforce-failed = La federación veta a { $user }, pero ha fallado la retirada. Revisá los permisos del bot. Fuente: <b>{ $source }</b> (<code>{ $id }</code>). Motivo: { $reason }
gg-fed-stat = Estado de vetos federados de <code>{ $user }</code>:
    { $rows }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — activo: { $status }; último cambio: { $date }.
gg-fed-stat-more = Hay más fuentes. Usá el comando de continuación o consultá un ID concreto para ver motivo y fecha.
gg-fed-intent-saved = Política guardada para <code>{ $user }</code> (versión { $version }). Los destinos observados están en cola; los permisos actuales y las demás restricciones se revisán antes de actuar.
gg-fed-subscriptions = Suscripciones directas a vetos de otras federaciones:
    { $rows }
gg-fed-imported = { $count } vetos validados y guardados; { $duplicates } duplicados idénticos ignorados. La aplicación en destinos observados está en cola.
gg-fed-event-import = vetos validados importados; aplicación en cola
gg-fed-error-file-format = Respondé a un CSV UTF-8 con id/reason, registros JSONL/NDJSON con user_id o un archivo exportado por este bot como matriz JSON. Una fila inválida impide toda escritura.
gg-fed-error-file-limit = Los archivos de vetos admiten 2 MiB y 1000 registros. Se rechazan archivos ausentes o excesivos; no se truncan listas en silencio.
gg-fed-error-file-duplicate = Hay registros incompatibles para el mismo ID. No se ha importado ningún veto.
gg-fed-error-file-rate = La importación y exportación comparten un intervalo de 30 minutos por federación. Reintentá más tarde.
gg-fed-error-reason = Los motivos admiten 1024 caractsos sin caractsos de control no compatibles.
gg-fed-error-reason_required = Esta federación exige un motivo no vacío para cada veto.
gg-fed-error-cycle = Una federación no puede suscribirse a sí misma ni formar un ciclo dirigido.
gg-fed-error-graph_limit = Límite de suscripciones alcanzado: 32 destinos directos, 128 federaciones alcanzables, profundidad 16 o 10 000 relaciones en este bot.
gg-data-confirm = <b>{ $operation }</b> · grupo <code>{ $group }</code>
    Módulos: { $modules }
    SHA-256 del archivo: <code>{ $digest }</code>
    Confirmá durante cinco minutos. Se comprobarán de nuevo el creador actual y la revisión del grupo. Solo cambiarán los módulos elegidos; identidad, confianza y vetos activos permanecerán.
gg-data-import = Importar módulos del grupo
gg-data-reset = Restablecer módulos del grupo
gg-data-privacy-delete = Borrar datos personales opcionales de este bot
gg-data-confirm-button = Confirmár este cambio
gg-data-personal = Abrí la confirmáción enviada a tu chat privado.
gg-data-saved = Módulos seleccionados guardados.
gg-data-error-authority = Importar o restablecer requiere al creador actual identificable del grupo. Exportar requiere un administrador actual.
gg-data-error-format = Respondé a un documento JSON válido y versionado de Group Guard; créalo con /export.
gg-data-error-limit = El archivo supera el tamaño o límite de contenido configurado.
gg-data-error-version = Esquema o versión no compatibles; no se ha aplicado ningún cambio.
gg-data-error-module = Elegí módulos conocidos: /export all o /export notes rules. Importar y restablecer usan los mismos nombres.
gg-data-error-field = Campos inválidos o ausentes; no se han aplicado ajustes.
gg-data-error-item = Contenido, opciones o acceso de repetición inválidos; no se ha guardado el contenido.
gg-data-error-media = Los medios deben subirse a este bot y estar disponibles mediante getFile. No se admiten IDs de otro bot.
gg-data-error-destination = Los registros y temas requieren autoridad actual y capacidades del bot. Los IDs de temas solo valen en su propio grupo.
gg-data-error-language = Elegí un idioma instalado con /setlang.
gg-data-error-stale = Esta confirmáción ha caducado, ha cambiado o ya se ha utilizado. Empezá de nuevo.
gg-data-error-restore = No se han podido restaurar con seguridad las restricciones temporales propias. Se conserva su evidencia; revisá los permisos antes de reintentar.
gg-data-error-rate = Las operaciones de datos del grupo tienen un intervalo local de cinco minutos. Reintentá más tarde.
gg-data-error-delivery = No se ha podido enviar la confirmáción privada. Abrí un chat privado con este bot y reintenta.
gg-data-error-saved_delivery = Ajustes guardados, pero no se han podido actualizar las sugerencias de comandos. Revisá los permisos del bot.
gg-data-error-cache_pending = Los datos opcionales de SQL se han borrado; la limpieza de caché queda en cola porque no está disponible. Los registros de seguridad activos permanecen.
gg-privacy-policy =
    <b>Tus datos en este bot Group Guard</b>
    /privacy data exporta tus conexiones, perfiles observados, advertencias, aprobaciones, estados de restricción y verificación, propiedad/roles/vetos de federaciones y trabajo de seguridad pendiente. Excluye contenido privado ajeno, respuestas de verificación, autenticación y archivos originales. Sigue el comando de continuación para ver más páginas.
    /privacy delete elimina el historial opcional de conexiones, nombres y usuarios observados, verificaciones inactivas y contenido de campañas personales terminadas en este bot. Advertencias/restricciones activas, versiones de vetos, roles, propiedad, derechos de suscripción, recibos contra repeticiones y trabajo de API incierto conservan los identificadores mínimos necesarios para seguridad y orden. Usá los comandos explícitos de dimisión o borrado de federación para esas relaciones. El perfil compartido de la plataforma y otros bots no se borran.
    Los operadores gestionan aparte las copias de seguridad y auditorías. Este comando no borra mensajes externos de Telegram ni copias de seguridad; no se promete un plazo automático de conservación.
gg-privacy-usage = /privacy policy · /privacy data [continuación] · /privacy delete — en tu propio chat privado con este bot.
gg-privacy-private = Se requiere la conversación privada de la persona pedínte. Los cursores inválidos no permiten ver datos ajenos.
gg-privacy-next = Siguiente página de datos: /privacy data { $cursor }
gg-privacy-deleted = Datos personales opcionales retirados de este bot. Seguridad activa, propiedad y trabajo incierto conservan identificadores mínimos; consultá /privacy policy.
gg-language-usage = Elegí el idioma del grupo: /setlang { $codes }. /lang en privado cambia tu idioma personal de la plataforma.
gg-language-saved = Idioma de respuesta del grupo actualizado.
gg-help-index =
    <b>Guía de comandos de Group Guard</b>
    /help categoría · /help comando · /help categoría 2. Los comandos indicádos también funcionan mediante /connect verificado; las respuestas privadas conservan el chat privado real.
    Ajustes: cambiar información; sanciones: restringir miembros; borrado: borrar mensajes; fijación: fijar mensajes; promociones: nombrar administradores; temas: gestionar temas. Los permisos del bot se verifican por separado. Las acciones del propietario necesitan al creador humano actual. /settings abrí tu panel privado del grupo.
gg-help-search = <b>Comandos coincidentes con { $query }</b>
gg-help-connected = Grupo o conexión de grupo verificada; consultá los permisos en la guía de la categoría
gg-help-group-only = Se requiere un mensaje real del grupo
gg-help-unsupported = Nombre conservado del catálogo; una acción sin fuente confirmáda devuelve una explicación
gg-help-next = Página siguiente
gg-help-previous = Página anterior
gg-help-family-title-moderation = Moderación y aprobaciones
gg-help-family-title-messages = Borrado y fijación de mensajes
gg-help-family-title-logging = Registros autorizados
gg-help-family-title-settings = Ajustes e idioma del grupo
gg-help-family-title-content = Notas, filtros, normas y saludos
gg-help-family-title-captcha = Verificación de nuevos miembros
gg-help-family-title-locks = Bloqueos de contenido y excepciones
gg-help-family-title-blocklists = Coincidencias y acciones de listas de bloqueo
gg-help-family-title-antispam = Protección contra mensajes masivos y ataques
gg-help-family-title-connections = Conexiones privadas a grupos
gg-help-family-title-identity = Información de usuario y chat
gg-help-family-title-policy = Política de comandos y bots
gg-help-family-title-cleanup = Limpieza de comandos, bots y servicios
gg-help-family-title-topics = Temas del foro
gg-help-family-title-utilities = Repetición de contenido y campañas del operador
gg-help-family-title-federations = Roles, vetos y suscripciones de federaciones
gg-help-family-title-portability = Archivos de grupo y datos personales
gg-help-family-title-discovery = Ayuda y editor de contenido
gg-help-family-moderation =
    <b>Moderación</b> · Respondé a un mensaje o indicá un ID o @usuario con prueba actual. /ban 20 motivo; /tban 20 60s motivo; /mute 20; /tmute 20 2h motivo. Las sanciones temporales admiten 60 segundos–365 días. /kickme solo te extocá a ti. Las variantes d borran la respuesta; las s limpian comando/respuesta y necesitan permiso de borrado. Los administradores actuales están protegidos.
    /setwarnlimit 3; /setwarnmode ban; /setwarntime 1d. Los grupos nuevos usan tres advertencias; los ajustes antiguos permanecen. /approve evita solo la protección común de contenido/mensajes masivos, nunca federaciones/CAS/ataques/acciones manuales. /promote requiere permisos y solo concede la intersección de derechos del bot y pedínte. El reinicio masivo requiere al creador.
gg-help-family-messages =
    <b>Mensajes</b> · /del necesita una respuesta real del grupo. /purge comienza allí; /purgefrom y /purgeto fijan extremos. Se aplican límites configurados y reglas de Telegram; la confirmáción por lote no es un recuento exacto de borrado.
    /pin [loud], /permapin, /unpin y /unpinall necesitan permiso de fijar. Retirar todas las fijaciones requiere al creador. /antichannelpin y /cleanlinked controlan mensajes automáticos del canal vinculado.
gg-help-family-logging =
    <b>Registros</b> · /setlog -100… necesita administración actual en el destino y permiso de publicación del bot. Una configuración reenviada debe correspondér al original realmente recibido. /logcategories muestra settings/admin/user/automated/reports/other; /log y /nolog seleccionan categorías. Un fallo de registro no afirma que una acción haya terminado.
gg-help-family-settings =
    <b>Ajustes</b> · /settings abrí un panel personal con caducidad y revisá cambiar información. /setlang code guarda el idioma del grupo; /lang privado guarda el personal. /night 23 7 +3 cierra el grupo por la noche; /night off restaura solo la copia de permisos propia que siga coincidiendo. Los cambios externos prevalecen.
gg-help-family-content =
    <b>Editor</b> · /save palabra texto o respondé a medios; /get palabra, #palabra y /notes consultán notas. Las notas usan una palabra; los nombres antiguos más amplios se conservan. /filter "frase" texto, /filterprefix y /filterexact elegín coincidencias. /stop elimina un activador; /clearall y /stopall necesitan confirmáción del creador.
    El marcado Rose admite negrita/cursiva/subrayado/tachado/código, enlaces, citas y alternativas aleatorias %%%. Campos: { "{" }first{ "}" }, { "{" }last{ "}" }, { "{" }fullname{ "}" }, { "{" }username{ "}" }, { "{" }mention{ "}" }, { "{" }id{ "}" }, { "{" }chatname{ "}" }, { "{" }count{ "}" }. /button crea botones URL/nota/normas con vista previa. Controles: preview/nonotif/protect/mediaspoiler; notas: admin/private/noprivate/repeat; filtros: user/allow_bot/replytag/command. /save palabra Hola { "{" }repeat 5m{ "}" } programa solo contenido público con permiso actual del autor. Normas, saludos y contenido privado comparten el mismo renderizador; los IDs de medios pertenecen al bot.
gg-help-family-captcha =
    <b>Verificación</b> · /captcha on/off; /captchamode off/button/math/text/text2; /setcaptchatext; /captcharules on; /captchakick on/off; /captchakicktime y /captchamutetime admiten plazos limitados. Las pruebas emitidas conservan su generación/plazo. Solicitudes de entrada: invite-users; silencios de miembros: restrict-members. Las respuestas son personales y de un uso. Los vetos federados se revisán antes de aprobaciones/verificación.
gg-help-family-locks =
    <b>Bloqueos</b> · /lock links [acción], /unlock tipo; /locktypes muestra tipos reales, /locks el estado. /lockwarns controla advertencias. /allowlist admite dominio/ruta, invitación exacta, @chat o stickerpack:/forward:/inline:/channel:/chat:/bot:/command:. Se rechazan patrones inválidos. Las excepciones solo afectan al bloqueo coincidente; el silencio automático exige consentimiento del creador y registro autorizado.
gg-help-family-blocklists =
    <b>Lista de bloqueo</b> · /addblocklist "frase" admite texto/prefijo/exacto e identidades declaradas con motivo/acción opcional. /rmblocklist elimina claves exactas. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute define la acción; los modos temporales necesitan duración. /blocklistdelete controla el borrado por separado. Los comodines están limitados; se rechazan patrones inválidos y excesos de entradas.
gg-help-family-antispam =
    <b>Mensajes masivos y ataques</b> · /setflood número para consecutivos; /setfloodtimer número duración para la ventana; /setfloodmode para sanción/duración; /clearflood para borrar. Se conservan los valores antiguos. /flood y /antiflood muestran la política; su relación es una compatibilidad local.
    /antiraid on/off/duration, /raidtime, /raidactiontime y /autoantiraid guardan un plazo y una sanción independiente para recién llegados. Precede a aprobación/verificación; la caducidad está vinculada a generación y resiste reinicios.
gg-help-family-connections =
    <b>Conexiones</b> · Usá /connect groupID o el enlace personal. Se revisá tu membresía y la del bot; toda modificación exige derechos actuales exactos. /connection muestra la selección; /disconnect la elimina; /connect muestra historial con continuación. Una conexión no concede propiedad de federación ni autoridad de operador.
gg-help-family-identity =
    <b>Información</b> · /id muestra IDs reales de usuario/chat/origen; /info consultá el destinatario actual. Respuestas y @usuarios necesitan prueba vigente y acotada. Un mensaje anónimo no identifica a la persona original; no se inventa un ID humano.
gg-help-family-policy =
    <b>Política</b> · /disable comando, /enable comando, /disabled y /disableable cubren nombres y alias. /disableadmin decide la exención administrativa; /disabledel el borrado de comandos desactivados. La recuperación sigue disponible. /bot2bot off/admin/all verifica membresía real; las modificaciones requieren normalmente revisión humana, /bot2botskipreview es del creador. /silentactions exige su consentimiento y registro autorizado. runs/saved sin acción documentada dan una explicación.
gg-help-family-cleanup =
    <b>Limpieza</b> · /cleancommand admin/user/other y /keepcommand seleccionan comandos. /cleanmsg action/filter/note y /keepmsg seleccionan solo mensajes realmente enviados por este bot; recibos y tareas de cinco minutos evitan IDs inventados. /cleanservice y /nocleanservice seleccionan join/leave/other/photo/pin/title/videochat. Primero se realiza el trabajo funcional y el procesamiento de pagos válidos.
gg-help-family-topics =
    <b>Temas</b> · /newtopic nombre, /renametopic nombre, /closetopic y /reopentopic usan el tema real actual. /deletetopic exige confirmáción del creador; /setactiontopic guarda un destino del mismo grupo. Se necesita foro de Telegram y manage-topics. Los fallos de entrega en temas ausentes o no compatibles se comunican como tales.
gg-help-family-utilities =
    <b>Herramientas</b> · /echo o /say presenta texto/medios directos o respondidos con el renderizador común limitado. /broadcast solo correspondé al operador configurado o propietario real de la instancia hija y a sus grupos configurados. Los resultados por destino conservan entregas parciales/inciertas; consultár o cancelar no repite adjuntos enviados.
gg-help-family-federations =
    <b>Federaciones</b> · /newfed nombre crea un UUID de este bot. En privado se usá tu federación propia sin conexión de grupo; consultár un UUID no concede rol. /fedpromote y /feddemote gestionan administradores; /feddemoteme dimite. /joinfed UUID y /leavefed requieren al creador actual del grupo. Borrar la federación no retira vetos de Telegram automáticamente.
    /fban userID motivo y /unfban userID requieren propietario/admin federado. /fedreason, /fednotif y /setfedlog son del propietario. /quietfed oculta solo avisos pasivos. /subfed UUID es dirigido, limitado y sin ciclos. /fedstat [userID] y /fbanstat UUID muestran estado/fuentes. /fbanlist csv/minicsv/json es del propietario, con intervalo compartido de 30 minutos; /importfbans respondé a CSV o JSON por líneas limitado y admite expresamente la matriz JSON de este bot. Solo se revisan usuarios observados realmente; no se afirma tener todo el censo de miembros.
gg-help-family-portability =
    <b>Archivos y privacidad</b> · /export all o módulos elegidos necesita administrador; /import y /reset al creador humano actual con confirmáción personal de cinco minutos y un uso. Intervalo local de grupo de cinco minutos; JSON propio versionado, máximo 2MiB y límites de contenido configurados. Módulos: moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Los omitidos permanecen. Nunca se importan confianza, pruebas/tareas emitidas, suscripciones, roles o vetos activos.
    /privacy policy/data/delete funciona solo en tu propio chat privado, con continuación y retención mínima de seguridad. No es un adaptador verificado del formato completo de Rose.
gg-help-family-discovery =
    <b>Ayuda</b> · /help muestra categorías; /help comando busca nombres/alias; /help categoría 2 continúa. /button ayuda a crear botones. Cada guía explica contexto, permisos, valores y limitaciones. /settings abrí el panel personal del grupo.
gg-lock-album = Álbumes
gg-lock-anonchannel = Remitentes de canales
gg-lock-audio = Audio
gg-lock-bot = Bots
gg-lock-button = Botones integrados
gg-lock-cashtag = Etiquetas de monedas
gg-lock-checklist = Listas de comprobación
gg-lock-cjk = Texto chino/japonés/coreano
gg-lock-command = Comandos
gg-lock-comment = Comentarios de no miembros
gg-lock-contact = Contactos
gg-lock-cyrillic = Texto cirílico
gg-lock-document = Documentos
gg-lock-email = Direcciones de correo
gg-lock-emoji = Emoji
gg-lock-emojicustom = Emoji personalizados
gg-lock-emojigame = Juegos de emoji
gg-lock-emojionly = Texto solo de emoji
gg-lock-externalreply = Respuestas externas
gg-lock-forward = Reenvíos
gg-lock-forwarduser = Reenvíos de usuarios
gg-lock-forwardbot = Reenvíos de bots
gg-lock-forwardchannel = Reenvíos de canales
gg-lock-forwardstory = Historias reenviadas
gg-lock-game = Juegos
gg-lock-gif = Animaciones GIF
gg-lock-guestbot = Bots invitados
gg-lock-inline = Bots integrados
gg-lock-invitelink = Invitaciones de Telegram
gg-lock-botlink = Enlaces a bots
gg-lock-location = Ubicaciones
gg-lock-outsidereaction = Reacciones de no miembros
gg-lock-phone = Números de teléfono
gg-lock-photo = Fotos
gg-lock-poll = Encuestas
gg-lock-reaction = Reacciones
gg-lock-rtl = Texto de derecha a izquierda
gg-lock-spoiler = Contenido oculto
gg-lock-sticker = Stickers
gg-lock-stickeranimated = Stickers animadas
gg-lock-stickerpremium = Stickers premium
gg-lock-text = Texto
gg-lock-url = URL
gg-lock-video = Videos
gg-lock-videonote = Notas de video
gg-lock-links = Enlaces
gg-lock-invites = Enlaces de invitación
gg-lock-forwards = Reenvíos
gg-lock-media = Medios
gg-lock-stickers = Stickers
gg-lock-gifs = GIF
gg-lock-voice = Mensajes de voz
gg-lock-polls = Encuestas
gg-lock-bots = Bots
gg-op-ban = vetar
gg-op-mute = silenciar
gg-op-kick = extocár
gg-op-unban = retirar veto
gg-op-unmute = retirar silencio
gg-op-warn = advertir
gg-op-unwarn = retirar advertencia
gg-op-resetwarns = restablecer advertencias
gg-op-purge = borrar rango de mensajes
gg-op-delete = borrar mensaje
gg-op-pin = fijar mensaje
gg-op-unpin = retirar fijación
gg-op-setlog = establecer registro
gg-op-unsetlog = retirar registro
gg-op-config = cambiar ajustes
gg-op-save = guardar contenido
gg-op-remove = borrar contenido
gg-op-panel = abrir panel
gg-op-unpinall = retirar todas las fijaciones
gg-op-permapin = fijar permanentemente
gg-op-promote = nombrar administrador
gg-op-demote = destituir administrador
gg-op-approve_user = aprobar usuario
gg-op-unapprove = retirar aprobación
gg-op-unapproveall = retirar todas las aprobaciones
gg-op-lock_change = cambiar política de bloqueos
gg-op-allowlist_change = cambiar excepciones
gg-op-allowlist_clear = borrar excepciones
gg-op-blocklist_change = cambiar lista de bloqueo
gg-op-blocklist_clear = borrar lista de bloqueo
gg-op-raid_change = cambiar protección contra ataques
gg-op-policy_change = cambiar política de comandos o limpieza
gg-op-topic_create = crear tema
gg-op-topic_rename = renombrar tema
gg-op-topic_close = cerrar tema
gg-op-topic_reopen = reabrir tema
gg-op-topic_delete = borrar tema y mensajes
gg-op-echo = enviar contenido formateado
