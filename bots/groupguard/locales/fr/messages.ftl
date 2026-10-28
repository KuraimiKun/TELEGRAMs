## Group Guard — independently authored French.
group-welcome = 🛡 Merci de m'avoir ajouté ! Donnez-moi les droits d'administration pour supprimer les messages, restreindre les membres et épingler. Utilisez /settings pour configurer la protection.
gg-start =
    🛡 Bonjour <b>{ $name }</b> ! Je suis <b>Group Guard</b>, le gestionnaire de sécurité de votre groupe.
    Vérification des nouveaux membres, protection contre les messages massifs et CAS, restrictions de contenu, liste de blocage, modération, notes, filtres, règles et accueil sont disponibles. Ajoutez-moi comme administrateur, puis ouvrez /settings ou /help.
gg-help = 📖 /help affiche les catégories ; /help nom_commande recherche une commande. Modération : /ban /mute /kick /warn. Contenu : /save /filter /rules. Protection : /lock /blocklist /night. /settings ouvre le panneau privé du groupe.
gg-welcome-default = 👋 Bienvenue { "{" }mention{ "}" } dans <b>{ "{" }group{ "}" }</b> !
gg-credit = 🛡 Protégé par @{ $bot }
gg-btn-add = ➕ M'ajouter à un groupe
gg-btn-commands = 📖 Commandes
gg-btn-rules = 📜 Règles
gg-btn-human = ✅ Je suis une personne
gg-btn-unwarn = ↩️ Retirer l'avertissement (administrateurs)
gg-btn-locks = 🔒 Restrictions ({ $count })
gg-btn-open-settings = ⚙️ Ouvrir les paramètres
gg-btn-admin-tab = 🛡 Groupes
gg-captcha = 🤖 { $user }, confirmez que vous êtes une personne sous <b>{ $minutes } minutes</b> pour éviter l'expulsion.
gg-captcha-button = Appuyez sur le bouton ci-dessous 👇
gg-captcha-math = Combien font <b>{ $a } + { $b }</b> ?
gg-captcha-not-you = Ce bouton appartient à quelqu'un d'autre.
gg-captcha-ok = ✅ Bienvenue !
gg-captcha-wrong = ❌ Réponse incorrecte. Il reste { $left } essais.
gg-captcha-failed = ❌ Trop de réponses incorrectes.
gg-captcha-passed = ✅ { $user } a été vérifié. Bienvenue !
gg-cas-banned = 🚫 { $user } figure dans la liste de spam CAS et a été banni.
gg-join-request = 👋 Pour rejoindre <b>{ $group }</b>, confirmez que vous êtes une personne :
gg-join-approved = ✅ Votre entrée a été approuvée. Bienvenue !
gg-join-expired = ⌛ Cette demande a expiré. Demandez à rejoindre le groupe à nouveau.
gg-goodbye = 👋 { $user } a quitté le groupe.
gg-flood-mute = 🌊 { $user } a envoyé trop de messages et a été réduit au silence temporairement.
gg-flood-kick = 🌊 { $user } a été expulsé pour messages massifs.
gg-flood-ban = 🌊 { $user } a été banni pour messages massifs.
gg-newbie-links = 🆕 { $user }, les nouveaux membres ne peuvent pas publier de liens pendant les { $hours } premières heures.
gg-spam-banned = 🧠 { $user } a été banni pour publication de spam.
gg-reason-blocklist = mot interdit
gg-need-right = ⛔ Vous devez disposer du droit d'administration « { $right } ».
gg-right-admin = administrateur
gg-right-restrict = restreindre les membres
gg-right-delete = supprimer les messages
gg-right-pin = épingler les messages
gg-right-change_info = modifier les informations du groupe
gg-admins-only = ⛔ Réservé aux administrateurs.
gg-need-target = 👤 Répondez à un message ou donnez un @utilisateur vérifié ou un identifiant.
gg-target-admin = 🙅 Cette action ne peut pas viser un administrateur.
gg-bot-no-rights = ⚠️ J'ai besoin du statut d'administrateur et des droits correspondants.
gg-banned = 🔨 { $user } a été banni. Motif : { $reason }
gg-banned-for = 🔨 { $user } a été banni pendant { $time }. Motif : { $reason }
gg-unbanned = ✅ Le bannissement de { $user } a été retiré.
gg-kicked = 👢 { $user } a été expulsé. Motif : { $reason }
gg-muted = 🔇 { $user } a été réduit au silence. Motif : { $reason }
gg-muted-for = 🔇 { $user } a été réduit au silence pendant { $time }. Motif : { $reason }
gg-unmuted = 🔊 { $user } peut à nouveau parler.
gg-warned = ⚠️ { $user } a reçu un avertissement ({ $count }/{ $limit }). Motif : { $reason }
gg-warn-limit-ban = 🔨 { $user } a atteint { $limit } avertissements et a été banni.
gg-warn-limit-mute = 🔇 { $user } a atteint { $limit } avertissements et a été réduit au silence.
gg-warn-limit-kick = 👢 { $user } a atteint { $limit } avertissements et a été expulsé.
gg-unwarned = ↩️ Un avertissement de { $user } a été retiré ({ $count }/{ $limit }).
gg-warn-removed = ↩️ Avertissement retiré par { $admin }.
gg-warns = ⚠️ { $user } a { $count }/{ $limit } avertissements.
gg-warns-reset = 🧽 Les avertissements de { $user } ont été réinitialisés.
gg-purge-reply = 🧹 Répondez au premier message à supprimer.
gg-purged = 🧹 { $count } messages ont été supprimés.
gg-pin-reply = 📌 Répondez au message à épingler.
gg-report-reply = 🚨 Répondez au message à signaler.
gg-reported = 🚨 { $user } a été signalé aux administrateurs.
gg-setlog-usage = 📒 Ajoutez-moi comme administrateur du canal de journal, puis utilisez <code>/setlog -100…</code> avec son identifiant.
gg-setlog-failed = ⚠️ Je ne peux pas publier dans cette destination. Ajoutez-moi d'abord comme administrateur.
gg-setlog-done = 📒 Canal de journal connecté.
gg-setlog-off = 📒 Canal de journal déconnecté.
gg-log-connected = 📒 Cette conversation reçoit le journal de modération de <b>{ $group }</b>.
gg-log-flood = 🌊 Messages massifs : { $user } → { $action }
gg-log-report = 🚨 Signalement de { $user }
gg-log-spam = 🧠 Bannissement pour spam détecté par IA : { $user }
    <blockquote>{ $text }</blockquote>
gg-rules = 📜 <b>Règles</b>
    { $rules }
gg-no-rules = 📜 Aucune règle définie. Les administrateurs peuvent utiliser /setrules texte.
gg-rules-saved = 📜 Règles enregistrées.
gg-rules-cleared = 📜 Règles supprimées.
gg-welcome-usage = 👋 Utilisez <code>/setwelcome Bonjour {"{"}mention{"}"}, bienvenue dans {"{"}group{"}"} !</code> ou répondez à un message.
gg-welcome-saved = 👋 Message d'accueil enregistré.
gg-welcome-reset = 👋 Message d'accueil par défaut restauré.
gg-note-usage = 📝 Utilisez <code>/save nom texte</code> ou répondez à un message avec <code>/save nom</code>.
gg-filter-usage = 🔁 Utilisez <code>/filter mot réponse</code> ou répondez à un message avec <code>/filter mot</code>.
gg-note-saved = 📝 Note enregistrée, accessible avec <code>#{ $key }</code> selon ses droits d'accès.
gg-filter-saved = 🔁 Je répondrai lorsque « { $key } » correspondra.
gg-notes-empty = 📝 Aucune note pour le moment.
gg-filters-empty = 🔁 Aucun filtre pour le moment.
gg-notes-list = 📝 <b>Notes</b>
gg-filters-list = 🔁 <b>Filtres</b>
gg-item-deleted = 🗑 « { $key } » a été supprimé.
gg-item-missing = 🤷 Rien n'est enregistré sous ce nom.
gg-items-limit = 📦 Ce groupe a atteint la limite de notes et de filtres.
gg-lock-usage = 🔒 Utilisez <code>/lock links</code>. Types : { $types } ou <code>all</code>.
gg-locked = 🔒 Restreint : { $types }
gg-unlocked = 🔓 Autorisé : { $types }
gg-locks-title = 🔒 <b>Restrictions de contenu</b>
gg-locks-panel = 🔒 <b>Restrictions</b> : le contenu restreint est supprimé ; les administrateurs sont exemptés.
gg-blocklist = 🚫 <b>Mots interdits</b> : { $words }
gg-blocklist-empty = 🚫 Aucun mot interdit.
gg-blocklist-usage = 🚫 <code>/addblock mot, autre expression</code> · <code>/rmblock mot</code>
gg-blocklist-saved = 🚫 Liste de blocage mise à jour ({ $count } entrées).
gg-night-usage = 🌙 <code>/night 23 7 +3</code> ferme de 23 h à 7 h UTC+3 ; <code>/night off</code> désactive.
gg-night-on = 🌙 Mode nocturne : fermeture de { $start } à { $end } ({ $tz }).
gg-night-off = 🌙 Mode nocturne désactivé.
gg-night-start = 🌙 Bonne nuit ! Le groupe est fermé jusqu'à { $end }.
gg-night-end = ☀️ Bonjour ! Le groupe est à nouveau ouvert.
gg-panel = ⚙️ <b>Paramètres — { $group }</b>
    Appuyez sur une option pour la modifier. Horaires nocturnes : { $night }, modifiables avec /night.
gg-panel-sent = 📬 Les paramètres vous ont été envoyés en privé.
gg-panel-start-first = 📬 Démarrez d'abord une conversation privée avec moi, puis appuyez ci-dessous.
gg-credit-vip = 💎 Masquer la ligne de protection nécessite VIP. Utilisez /vip en privé.
gg-opt-wel = 👋 Accueil : { $value }
gg-opt-cln = 🧹 Nettoyer les entrées : { $value }
gg-opt-bye = 👋 Départ : { $value }
gg-opt-cap = 🤖 Vérification : { $value }
gg-opt-cpm = ⏱ Délai de vérification : { $value } min
gg-opt-fld = 🌊 Limite de messages massifs : { $value }
gg-opt-fla = 🌊 Action pour messages massifs : { $value }
gg-opt-wrn = ⚠️ Limite d'avertissements : { $value }
gg-opt-wra = ⚠️ Action d'avertissement : { $value }
gg-opt-act = ⏳ Silence/bannissement automatique : { $value } min
gg-opt-cas = 🛡 Protection CAS : { $value }
gg-opt-nwb = 🆕 Nouveaux membres sans liens : { $value } h
gg-opt-ais = 🧠 Protection antispam par IA : { $value }
gg-opt-ngt = 🌙 Mode nocturne : { $value }
gg-opt-crd = 🏷 Ligne de crédit : { $value }
gg-opt-lang = 🌐 Langue : { $value }
gg-val-button = bouton
gg-val-math = calcul
gg-val-off = désactivé
gg-val-mute = silence
gg-val-kick = expulsion
gg-val-ban = bannissement
gg-adm = 🛡 <b>Group Guard</b>
    Groupes protégés : <b>{ $groups }</b> ; avertissements : <b>{ $warns }</b> ; notes et filtres : <b>{ $items }</b>.
cmd-settings = Paramètres du groupe
cmd-help = Guide des commandes
gg-auth-denied = L'autorisation n'a pas pu être vérifiée. Rien n'a changé.
gg-target-invalid = Choisissez un membre humain connu. La cible n'a pas pu être vérifiée.
gg-duration-invalid = Utilisez une durée de 60s à 365d. Les commandes temporaires nécessitent une durée.
gg-reason-invalid = Le motif doit compter au plus 256 caractères.
gg-outcome-failed = L'action demandée a échoué ou n'a pas pu être autorisée.
gg-outcome-partial = L'action n'est terminée qu'en partie. Un bannissement peut rester si la restitution après expulsion échoue.
gg-outcome-ancillary = L'action principale est terminée, mais une étape associée a échoué.
gg-review-request = Révision : <b>{ $operation }</b>
    Cible : { $target }
    Détails : { $details }
    Durée (secondes) : { $duration }
    Une personne actuellement autorisée peut approuver sous 120 secondes.
gg-review-approve = Approuver cette action
gg-review-unavailable = Le stockage des révisions est indisponible. Envoyez une nouvelle commande.
gg-review-expired = Cette révision a expiré, est invalide ou a déjà été utilisée.
gg-review-consumed = Cette révision a été utilisée. Vérifiez le résultat ; envoyez une autre commande pour réessayer.
gg-duration-permanent = Permanent / sans minuterie
gg-purge-ack = Suppression demandée pour { $requested } identifiants ; l'API en a reconnu { $acknowledged }. Le nombre réellement supprimé n'est pas confirmé.
gg-warning-removed = Avertissement retiré.
gg-review-details-above = Le contenu complet demandé est affiché juste au-dessus.
gg-warn-pending = Avertissement enregistré ; une action de seuil est déjà en cours.
gg-done = Terminé.
gg-setting-saved = Paramètre { $setting } enregistré.
gg-setting-value = { $setting } : { $value }
gg-setting-invalid = Paramètre invalide. Utilisez on/off, un mode valide ou une durée comme 10m.
gg-warning-settings = Avertissements : limite { $limit } ; mode { $mode } ; sanction { $duration } ; expiration { $expiry }.
gg-admin-changed = Action { $action } terminée pour { $user }.
gg-admin-list = Administrateurs publics :
    { $admins }
gg-approved = { $user } approuvé. Motif : { $reason }
gg-unapproved = { $count } approbations retirées.
gg-approval-status = Approbation de { $user } : { $status }. Motif : { $reason }
gg-approval-list = Utilisateurs approuvés :
    { $approvals }
gg-next-page = Entrées suivantes : { $command }
gg-range-invalid = Intervalle invalide. Sélectionnez entre 1 et { $cap } identifiants de message.
gg-range-start = Le début est enregistré pour vous dans ce sujet pendant dix minutes. Répondez au dernier message avec /purgeto.
gg-range-missing = Aucun début enregistré pour vous dans ce sujet. Répondez d'abord avec /purgefrom.
gg-content-needed = Fournissez du contenu ou répondez à du contenu ; maximum 3500 caractères.
gg-log-status = Destination du journal : { $destination }. Catégories actives : { $categories }.
gg-log-unverified = Je n'ai pas de réception vérifiée pour ce message original du canal. Envoyez d'abord /setlog dans le canal.
gg-log-forward = Transférez ce message /setlog original au groupe. L'administrateur doit pouvoir modifier les informations des deux conversations.
gg-info = Nom : { $name }
    Nom d'utilisateur : { $username }
    Identifiant : <code>{ $id }</code>
    Appartenance : { $membership }
gg-unknown = Inconnu
gg-chat-id = Identifiant du chat : <code>{ $id }</code>
gg-on = Activé
gg-off = Désactivé
gg-anon-enabled = L'hypothèse d'administrateur anonyme est active ici. Les commandes anonymes du même groupe utilisent les droits du bot sans identifier de personne. Les opérations du propriétaire nécessitent toujours un créateur vérifié. /anonadmin off rétablit la révision humaine.
gg-right-invite_users = inviter des utilisateurs
gg-right-promote_members = nommer des administrateurs
gg-right-manage_topics = gérer les sujets
gg-right-creator = créateur du groupe
gg-log-join = { $user } a rejoint le groupe.
gg-log-leave = { $user } a quitté le groupe.
gg-warning-row = • #{ $id } : { $reason } (expiration : { $expiry })
gg-menu-prompt = Choisissez une option.
gg-content-invalid = Contenu invalide ou trop long pour Telegram. Vérifiez le nom, le format, les modificateurs et les boutons.
gg-content-unavailable = Ce contenu est indisponible ou votre appartenance actuelle ne permet pas l'accès.
gg-btn-private-note = Ouvrir la note
gg-open-private = Ouvrez ce contenu en privé :
gg-items-cleared = { $count } entrées supprimées.
gg-clearall-confirm = Le créateur du groupe peut confirmer avec <code>/{ $command } confirm</code>.
gg-button-usage = Utilisez <code>/button "Libellé" https://example.com</code>. Ajoutez <code>"Note" #nom same</code> sur une ligne pour un bouton sur la même rangée. Le bot renvoie le balisage et une prévisualisation fonctionnelle.
gg-btn-accept-rules = Accepter les règles
gg-btn-open-verification = Ouvrir la vérification
gg-captcha-private = { $user }, ouvrez l'épreuve privée pour vérifier votre appartenance.
gg-captcha-choice = Choisissez l'image correspondante avec les boutons. Mode : { $mode } ; position du caractère : { $position }.
gg-captcha-settings = Vérification : { $enabled } ; mode : { $mode } ; expulsion : { $kick } ; délai : { $seconds } secondes ; fin automatique du silence : { $release }.
gg-captcha-dependency = Activez l'accueil avant la vérification. Enregistrez des règles avant d'exiger leur acceptation.
gg-val-text = Image de texte
gg-val-text2 = Image de caractère
gg-captcha-attempts-exhausted = Trop de réponses incorrectes : la vérification a échoué et la restriction prévue a été appliquée.
gg-captcha-admin-exempt = Vous êtes maintenant administrateur. Cette épreuve de vérification est terminée.
gg-captcha-question-text = Choisissez le mot affiché dans l'image.
gg-captcha-question-math = Résolvez l'équation dans l'image et choisissez la réponse.
gg-captcha-question-text2 = Choisissez le caractère { $position } de l'image, de gauche à droite.
gg-locktypes = Restrictions disponibles : <code>{ $types }</code>
gg-allowlist-title = Exceptions aux restrictions
gg-allowlist-invalid = Exception invalide. Utilisez domaine/chemin, invitation exacte, @chat ou une identité déclarée comme stickerpack:nom.
gg-reason-lock = Contenu restreint : { $types }
gg-lock-applied = Politique appliquée à { $types }. Motif : { $reason }
gg-reaction-failed = L'application aux réactions a échoué : { $code }. Ce serveur Bot API ne permet peut-être pas le retrait des réactions.
gg-reaction-anonymous = Une mise à jour du nombre de réactions anonymes n'identifie ni utilisateur ni chat acteur. L'API de retrait en exige un ; aucun retrait n'est affirmé.
gg-none = Aucun
gg-blocklist-title = Liste de blocage
gg-blocklist-invalid = Déclencheur, motif ou action invalide. Vérifiez les expressions entre guillemets, échappements des jokers et durée obligatoire des modes temporaires.
gg-blocklist-settings = Mode de blocage : { $mode } ; supprimer les messages correspondants : { $delete }.
gg-blocklist-action = Politique de blocage appliquée à { $user }. Motif : { $reason }
gg-flood-status = Messages massifs : limite consécutive { $consecutive } (à N) ; fenêtre { $count } / { $seconds }s (au-delà de N). Action { $mode }, { $duration } ; séquence entière { $clear }.
gg-raid-status = Protection contre les attaques { $active } ; jusqu'à { $until }. Activation { $period } ; bannissement { $ban } ; seuil automatique { $auto } entrées/minute. Activer : /antiraid on · Arrêter : /antiraid off
gg-raid-banned = 🛡 { $user } a été banni temporairement pendant la protection contre les attaques.
gg-raid-declined = 🛡 La demande d'entrée de { $user } a été refusée pendant la protection contre les attaques.
gg-silent-consent-required = Le créateur doit autoriser les actions silencieuses avec un journal configuré avant de choisir cette action.
gg-btn-enable-raid = Activer la protection contre les attaques
gg-human-required = Cette opération nécessite une personne identifiable.
gg-group-message-required = Exécutez cette commande sur le message ou sujet réel du groupe ; un identifiant privé ne désigne pas un message du groupe.
gg-connection-private = Utilisez cette commande de connexion dans notre conversation privée.
gg-connection-disconnected = Déconnecté. Vos cinq derniers groupes restent disponibles pour vous reconnecter.
gg-connection-current = Connecté à <b>{ $group }</b>. L'appartenance et les permissions actuelles sont vérifiées pour chaque opération.
gg-connection-none = Aucune connexion active. Utilisez /connect GROUP_ID ou /connect @groupe.
gg-connection-open = Ouvrez votre connexion personnelle dans notre conversation privée.
gg-btn-connect = Connecter en privé
gg-connection-history = Vos cinq derniers groupes. Sélectionnez-en un pour vous reconnecter ; vous devez toujours en être membre.
gg-connection-unavailable = Connexion indisponible. Vous devez être un membre humain actuel et le bot doit y être administrateur.
gg-catalog-unresolved = /{ $command } figure au catalogue sans action définie. Utilisez /notes ou /flood pour les fonctions implémentées.
gg-cleanup-failed = Le nettoyage a échoué ou est indisponible ; aucune suppression n'est affirmée.
gg-disabled-list = Commandes : <code>{ $commands }</code>. /disable NOM et /enable NOM règlent l'exécution ; /disabledel le nettoyage ; /disableadmin inclut les administrateurs.
gg-cleanup-types = Catégories de nettoyage disponibles : { $types }
gg-cleanup-selected = Catégories de nettoyage choisies : { $types }
gg-advanced-status = { $setting } : { $value }. Le silence automatique nécessite le consentement du créateur et un journal. Les commandes de bots exigent les droits ordinaires, avec révision des modifications par défaut. Configurez la visibilité entre bots dans BotFather.
gg-action-topic = Sujet des actions : { $topic }. /setactiontopic dans un sujet de forum le sélectionne. Le sujet général/par défaut est 1.
gg-topic-unavailable = Un groupe de forum actuel et les droits de gestion correspondants sont nécessaires.
gg-topic-id-required = Dans un chat privé connecté, donnez explicitement l'identifiant du sujet.
gg-topic-general-delete = Le sujet général ne peut pas être supprimé. La confirmation nécessite une personne identifiable.
gg-topic-delete-confirm = Supprimer le sujet { $topic } et ses messages ? Confirmation personnelle valable deux minutes.
gg-btn-confirm-delete = Confirmer la suppression
gg-topic-changed = Action { $action } terminée pour le sujet { $topic }.
gg-broadcast-owner = Seul l'opérateur configuré de ce bot ou le véritable propriétaire de l'instance enfant peut diffuser dans ses groupes.
gg-broadcast-queued = Diffusion { $id } mise en file. Destinations et résultats sont isolés par bot.
gg-broadcast-busy = Une autre diffusion est active ou le délai de création de cinq minutes n'est pas écoulé.
gg-broadcast-empty = Vous n'avez aucune diffusion de groupe dans ce bot.
gg-broadcast-status = Diffusion { $id } : { $status }. En file : { $queued } ; envoyés : { $sent } ; échecs : { $failed } ; incertains : { $uncertain } ; annulés : { $cancelled }.
gg-fed-created = Fédération <b>{ $name }</b> créée. Son identifiant dans ce bot est <code>{ $id }</code>.
gg-fed-info = <b>{ $name }</b>
    Identifiant : <code>{ $id }</code> ; propriétaire : <code>{ $owner }</code> ; administrateurs : { $admins }.
    Motifs obligatoires : { $reasons } ; notifications du propriétaire : { $notifications } ; journal : { $log }.
gg-fed-list = Vos fédérations en tant que propriétaire ou administrateur :
    { $rows }
gg-fed-admins = Le propriétaire, puis les administrateurs de la fédération :
    { $rows }
gg-fed-quiet = Explications passives silencieuses : { $value }. L'application des bannissements reste active.
gg-fed-policy = Motifs obligatoires : { $reasons } ; notifications du propriétaire : { $notifications }.
gg-fed-confirm-delete = Supprimer <b>{ $name }</b> (<code>{ $id }</code>) ? Données et appartenances seront supprimées définitivement. Les bannissements Telegram existants resteront. Confirmez sous cinq minutes.
gg-fed-confirm-log = Définir le journal de <b>{ $name }</b> (<code>{ $id }</code>) vers <code>{ $destination }</code> ? Confirmez sous cinq minutes. Vos droits à destination et ceux de publication du bot seront revérifiés.
gg-fed-confirm-sent = Une confirmation personnelle a été envoyée au propriétaire de la fédération.
gg-fed-deleted = Fédération supprimée. Les bannissements Telegram existants restent.
gg-fed-log-set = Destination du journal de fédération : <code>{ $destination }</code>.
gg-fed-cancel = Annuler
gg-fed-cancelled = Annulé.
gg-fed-saved-delivery-failed = Modification enregistrée, mais notification ou journal non livré. Vérifiez la destination et l'accès du bot.
gg-fed-error-authority = Cette action nécessite le propriétaire actuel de la fédération ou le rôle approprié. Un rôle Telegram dans un groupe ne confère pas d'autorité fédérale.
gg-fed-error-private = Utilisez cette commande dans votre propre conversation privée avec ce bot.
gg-fed-error-group = Utilisez cette commande dans le groupe réel. Une connexion privée ne sélectionne pas le groupe de fédération.
gg-fed-error-owned = Vous possédez déjà une fédération dans ce bot. Utilisez /fedinfo, /renamefed ou /delfed en privé.
gg-fed-error-name = Donnez un nom non vide sans caractères de contrôle. Les noms sont limités à 64 caractères.
gg-fed-error-id = Donnez un UUID de fédération valide de ce bot. Les identifiants Rose ne rejoignent pas ce service indépendant.
gg-fed-error-missing = Aucune fédération trouvée dans ce bot ou contexte.
gg-fed-error-creator = Seul le créateur actuel du groupe Telegram peut le faire entrer ou sortir d'une fédération.
gg-fed-error-target = Donnez un identifiant humain positif, répondez à une personne ou utilisez un nom actuellement vérifié. Le propriétaire ne peut pas être destitué.
gg-fed-error-value = Arguments de fédération invalides. Utilisez on/off pour les politiques et un identifiant valide lorsque nécessaire.
gg-fed-error-stale = Cette confirmation a expiré, a été utilisée ou l'état de la fédération, du propriétaire ou de la destination a changé. Demandez-en une nouvelle.
gg-fed-error-destination = Le propriétaire doit avoir des droits d'administration actuels à destination et le bot doit pouvoir y publier. Les canaux nécessitent post_messages.
gg-fed-error-delivery = La confirmation personnelle n'a pas pu être livrée ou liée. Ouvrez un chat privé avec le bot et réessayez.
gg-fed-event = Fédération <b>{ $name }</b> (<code>{ $id }</code>) : { $event }. Acteur : <code>{ $user }</code>.
gg-fed-event-rename = nom modifié
gg-fed-event-delete = supprimée ; les bannissements Telegram restent
gg-fed-event-promote = administrateur ajouté
gg-fed-event-demote = administrateur retiré
gg-fed-event-self-remove = administrateur démissionnaire
gg-fed-event-reason = politique des motifs modifiée
gg-fed-event-notif = politique des notifications modifiée
gg-fed-event-log = destination du journal modifiée
gg-fed-event-unlog = destination du journal retirée
gg-fed-event-ban = politique de bannissement enregistrée ; application en file
gg-fed-event-unban = politique retirée ; libération des restrictions propres en file
gg-fed-event-subscribe = abonnement ajouté ; utilisateurs observés à vérifier
gg-fed-event-unsubscribe = abonnement retiré ; les autres sources sont conservées
gg-fed-ban-details = Cible : <code>{ $user }</code>. Motif : { $reason }
gg-fed-passive = La fédération interdit { $user }. Source : <b>{ $source }</b> (<code>{ $id }</code>). Motif : { $reason }
gg-fed-enforce-failed = La fédération interdit { $user }, mais le retrait a échoué. Vérifiez les droits du bot. Source : <b>{ $source }</b> (<code>{ $id }</code>). Motif : { $reason }
gg-fed-stat = État des bannissements fédéraux pour <code>{ $user }</code> :
    { $rows }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — actif : { $status } ; dernier changement : { $date }.
gg-fed-stat-more = D'autres sources existent. Utilisez la continuation ou interrogez une fédération précise pour son motif et sa date.
gg-fed-intent-saved = Politique enregistrée pour <code>{ $user }</code> (version { $version }). Les destinations observées sont en file ; droits actuels et autres restrictions sont vérifiés avant toute action.
gg-fed-subscriptions = Abonnements directs aux bannissements des fédérations :
    { $rows }
gg-fed-imported = { $count } bannissements validés et enregistrés ; { $duplicates } doublons identiques ignorés. L'application aux destinations observées est en file.
gg-fed-event-import = bannissements validés importés ; application en file
gg-fed-error-file-format = Répondez à un CSV UTF-8 avec id/reason, à des lignes JSONL/NDJSON avec user_id ou à l'export en tableau JSON de ce bot. Une ligne invalide empêche toutes les écritures.
gg-fed-error-file-limit = Fichiers limités à 2 MiB et 1000 entrées. Fichiers absents ou trop volumineux refusés ; aucune liste n'est tronquée silencieusement.
gg-fed-error-file-duplicate = Des entrées contradictoires visent le même identifiant. Aucun bannissement importé.
gg-fed-error-file-rate = Import et export partagent un intervalle de 30 minutes par fédération. Réessayez plus tard.
gg-fed-error-reason = Les motifs sont limités à 1024 caractères sans caractères de contrôle non pris en charge.
gg-fed-error-reason_required = Cette fédération exige un motif non vide pour chaque bannissement.
gg-fed-error-cycle = Une fédération ne peut pas s'abonner à elle-même ni former un cycle dirigé.
gg-fed-error-graph_limit = Limites atteintes : 32 cibles directes, 128 fédérations accessibles, profondeur 16 ou 10 000 relations dans ce bot.
gg-data-confirm = <b>{ $operation }</b> · groupe <code>{ $group }</code>
    Modules : { $modules }
    SHA-256 du fichier : <code>{ $digest }</code>
    Confirmez sous cinq minutes. Créateur actuel et révision du groupe seront revérifiés. Seuls les modules choisis changent ; identité, confiance et bannissements actifs restent.
gg-data-import = Importer les modules du groupe
gg-data-reset = Réinitialiser les modules du groupe
gg-data-privacy-delete = Supprimer les données personnelles facultatives de ce bot
gg-data-confirm-button = Confirmer cette modification
gg-data-personal = Ouvrez la confirmation envoyée à votre conversation privée.
gg-data-saved = Modules sélectionnés enregistrés.
gg-data-error-authority = Importation et réinitialisation nécessitent le créateur actuel identifiable du groupe. L'export nécessite un administrateur actuel.
gg-data-error-format = Répondez à un document JSON versionné valide de Group Guard ; créez-le avec /export.
gg-data-error-limit = Ce fichier dépasse la taille ou la quantité de contenu configurée.
gg-data-error-version = Schéma ou version non pris en charge ; aucune modification appliquée.
gg-data-error-module = Choisissez des modules connus : /export all ou /export notes rules. Importation et réinitialisation utilisent les mêmes noms.
gg-data-error-field = Champs invalides ou manquants ; aucun paramètre appliqué.
gg-data-error-item = Contenu, options ou accès de répétition invalides ; aucun contenu enregistré.
gg-data-error-media = Les médias doivent être envoyés à ce bot et accessibles par getFile. Les identifiants d'un autre bot ne sont pas acceptés.
gg-data-error-destination = Journaux et sujets nécessitent des droits actuels et les capacités du bot. Un identifiant de sujet ne vaut que dans son groupe.
gg-data-error-language = Choisissez une langue installée avec /setlang.
gg-data-error-stale = Confirmation expirée, modifiée ou déjà utilisée. Recommencez.
gg-data-error-restore = Les restrictions temporaires propres n'ont pas pu être restaurées en sécurité. Leur preuve reste ; vérifiez les droits du bot avant de réessayer.
gg-data-error-rate = Les opérations de données du groupe ont un intervalle local de cinq minutes. Réessayez plus tard.
gg-data-error-delivery = La confirmation privée n'a pas pu être livrée. Démarrez une conversation privée avec le bot et réessayez.
gg-data-error-saved_delivery = Paramètres enregistrés, mais suggestions de commandes non actualisées. Vérifiez les permissions du bot.
gg-data-error-cache_pending = Les données SQL facultatives ont été retirées ; le nettoyage du cache est en file car il est indisponible. Les données de sécurité actives restent.
gg-privacy-policy =
    <b>Vos données dans ce bot Group Guard</b>
    /privacy data exporte vos connexions, profils observés, avertissements, approbations, états de restriction/vérification, propriété/rôles/bannissements fédéraux et travail de sécurité en attente. Il exclut le contenu privé d'autrui, les réponses de vérification, l'authentification et les fichiers bruts. Suivez la continuation pour les pages suivantes.
    /privacy delete retire l'historique facultatif des connexions, noms/pseudonymes observés, vérifications inactives et contenu des campagnes personnelles terminées de ce bot. Les avertissements/restrictions actifs, versions de bannissement, rôles, propriété, droits d'abonnement, reçus antirépétition et travail API incertain conservent les identifiants minimaux nécessaires à la sécurité et à l'ordre. Utilisez les commandes explicites de démission ou suppression de fédération pour ces liens. Le profil partagé de la plateforme et les autres bots restent.
    Les opérateurs gèrent séparément sauvegardes et audits. Cette commande ne supprime pas les messages Telegram externes ni les sauvegardes et ne promet pas de durée automatique de conservation.
gg-privacy-usage = /privacy policy · /privacy data [continuation] · /privacy delete — dans votre propre conversation privée avec ce bot.
gg-privacy-private = Cette action nécessite la conversation privée de la personne demandeuse. Un curseur invalide ne donne pas accès aux données d'autrui.
gg-privacy-next = Page suivante : /privacy data { $cursor }
gg-privacy-deleted = Données personnelles facultatives retirées de ce bot. Sécurité active, propriété et travail incertain conservent des identifiants minimaux ; consultez /privacy policy.
gg-language-usage = Choisissez la langue du groupe : /setlang { $codes }. /lang en privé modifie votre langue personnelle sur la plateforme.
gg-language-saved = Langue de réponse du groupe actualisée.
gg-help-index =
    <b>Guide des commandes Group Guard</b>
    /help catégorie · /help commande · /help catégorie 2. Les commandes indiquées fonctionnent aussi par /connect vérifié ; les réponses privées restent dans leur véritable conversation.
    Paramètres : modifier les informations ; sanctions : restreindre les membres ; suppression : supprimer les messages ; épingles : épingler ; promotions : nommer des administrateurs ; sujets : gérer les sujets. Les droits du bot sont vérifiés séparément. Les actions du propriétaire exigent le créateur humain actuel. /settings ouvre votre panneau privé du groupe.
gg-help-search = <b>Commandes correspondant à { $query }</b>
gg-help-connected = Groupe ou connexion vérifiée ; les droits sont expliqués dans la catégorie
gg-help-group-only = Un message réel du groupe est nécessaire
gg-help-unsupported = Nom du catalogue conservé ; un comportement sans source confirmée renvoie une explication
gg-help-next = Page suivante
gg-help-previous = Page précédente
gg-help-family-title-moderation = Modération et approbations
gg-help-family-title-messages = Suppression et épinglage
gg-help-family-title-logging = Journaux autorisés
gg-help-family-title-settings = Paramètres et langue du groupe
gg-help-family-title-content = Notes, filtres, règles et salutations
gg-help-family-title-captcha = Vérification des nouveaux membres
gg-help-family-title-locks = Restrictions de contenu et exceptions
gg-help-family-title-blocklists = Correspondances et actions de blocage
gg-help-family-title-antispam = Protection contre les messages massifs et attaques
gg-help-family-title-connections = Connexions privées aux groupes
gg-help-family-title-identity = Informations utilisateur et conversation
gg-help-family-title-policy = Politique des commandes et des bots
gg-help-family-title-cleanup = Nettoyage des commandes, bots et services
gg-help-family-title-topics = Sujets de forum
gg-help-family-title-utilities = Écho de contenu et campagnes d'opérateur
gg-help-family-title-federations = Rôles, bannissements et abonnements fédéraux
gg-help-family-title-portability = Fichiers du groupe et données personnelles
gg-help-family-title-discovery = Aide et éditeur de contenu
gg-help-family-moderation =
    <b>Modération</b> · Répondez à un message ou donnez un identifiant ou @utilisateur vérifié. /ban 20 motif ; /tban 20 60s motif ; /mute 20 ; /tmute 20 2h motif. Les sanctions temporaires acceptent 60 secondes–365 jours. /kickme ne vise que vous. Les variantes d suppriment aussi la réponse ; les s nettoient commande/réponse et exigent la suppression. Les administrateurs actuels sont protégés.
    /setwarnlimit 3 ; /setwarnmode ban ; /setwarntime 1d. Nouveaux groupes : trois avertissements ; les anciens réglages restent. /approve contourne seulement la protection ordinaire de contenu/messages massifs, jamais fédération/CAS/attaque/action manuelle. /promote exige le droit correspondant et limite les droits accordés à l'intersection demandeur/bot. Les réinitialisations massives exigent le créateur.
gg-help-family-messages =
    <b>Messages</b> · /del exige une véritable réponse du groupe. /purge commence là ; /purgefrom et /purgeto figent les extrémités. Limites configurées et règles Telegram s'appliquent ; un accusé par lot n'est pas un nombre exact de suppressions.
    /pin [loud], /permapin, /unpin et /unpinall exigent le droit d'épingler. Tout désépingler exige le créateur. /antichannelpin et /cleanlinked contrôlent les messages automatiques du canal lié.
gg-help-family-logging =
    <b>Journaux</b> · /setlog -100… nécessite l'administration actuelle à destination et la publication du bot. Une configuration transférée doit provenir de l'original réellement reçu. /logcategories affiche settings/admin/user/automated/reports/other ; /log et /nolog sélectionnent. Un échec de journal reste visible sans affirmer l'achèvement de l'action.
gg-help-family-settings =
    <b>Paramètres</b> · /settings ouvre un panneau personnel expirant avec vérification de modifier les informations. /setlang code enregistre la langue du groupe ; /lang privé la langue personnelle. /night 23 7 +3 ferme la nuit ; /night off ne restaure que la copie de permissions propre qui correspond toujours. Les modifications externes priment.
gg-help-family-content =
    <b>Éditeur</b> · /save mot texte ou répondez à un média ; /get mot, #mot et /notes consultent les notes. Déclencheurs de notes : un mot ; les anciens noms plus larges restent. /filter "expression" texte, /filterprefix et /filterexact choisissent la correspondance. /stop retire un déclencheur ; /clearall et /stopall exigent confirmation du créateur.
    Rose accepte gras/italique/souligné/barré/code, liens, citations et alternatives aléatoires %%%. Champs : { "{" }first{ "}" }, { "{" }last{ "}" }, { "{" }fullname{ "}" }, { "{" }username{ "}" }, { "{" }mention{ "}" }, { "{" }id{ "}" }, { "{" }chatname{ "}" }, { "{" }count{ "}" }. /button crée des boutons URL/note/règles avec aperçu. Contrôles : preview/nonotif/protect/mediaspoiler ; notes : admin/private/noprivate/repeat ; filtres : user/allow_bot/replytag/command. /save mot Bonjour { "{" }repeat 5m{ "}" } ne programme que du contenu public avec droits actuels de l'auteur. Règles, accueil/départ et contenu privé partagent le rendu ; les identifiants médias sont liés au bot.
gg-help-family-captcha =
    <b>Vérification</b> · /captcha on/off ; /captchamode off/button/math/text/text2 ; /setcaptchatext ; /captcharules on ; /captchakick on/off ; /captchakicktime et /captchamutetime utilisent des délais bornés. Les épreuves émises gardent génération/délai. Demandes d'entrée : invite-users ; silence des membres : restrict-members. Réponses personnelles à usage unique. Les bannissements fédéraux précèdent approbation/vérification.
gg-help-family-locks =
    <b>Restrictions</b> · /lock links [action], /unlock type ; /locktypes affiche les types réels, /locks l'état. /lockwarns règle les avertissements. /allowlist accepte domaine/chemin, invitation exacte, @chat ou stickerpack:/forward:/inline:/channel:/chat:/bot:/command:. Les motifs invalides sont refusés. Une exception ne concerne que le contenu correspondant ; le silence automatique nécessite consentement du créateur et journal autorisé.
gg-help-family-blocklists =
    <b>Blocage</b> · /addblocklist "expression" accepte texte/préfixe/exact et identités déclarées, avec motif/action facultatifs. /rmblocklist retire des clés exactes. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute définit l'action ; les modes temporaires exigent une durée. /blocklistdelete règle la suppression séparément. Jokers bornés ; motifs invalides et limites dépassées sont refusés.
gg-help-family-antispam =
    <b>Messages massifs et attaques</b> · /setflood nombre pour les consécutifs ; /setfloodtimer nombre durée pour la fenêtre ; /setfloodmode pour sanction/durée ; /clearflood pour supprimer. Les anciens réglages restent. /flood et /antiflood affichent la politique ; leur alias est une compatibilité locale.
    /antiraid on/off/duration, /raidtime, /raidactiontime et /autoantiraid enregistrent un délai et une sanction distincte pour nouveaux entrants. Priorité sur approbation/vérification ; expiration liée à génération et sûre après redémarrage.
gg-help-family-connections =
    <b>Connexions</b> · /connect groupID ou lien personnel. Votre appartenance et celle du bot sont revérifiées ; toute modification exige les droits actuels exacts. /connection affiche la sélection ; /disconnect la retire ; /connect affiche l'historique avec continuation. Aucune connexion ne donne propriété fédérale ou autorité d'opérateur.
gg-help-family-identity =
    <b>Informations</b> · /id donne les identifiants réels utilisateur/chat/origine ; /info consulte la cible actuelle. Réponses et @utilisateurs exigent une preuve actuelle dans le bon périmètre. Un message anonyme n'identifie pas son humain d'origine ; aucun identifiant humain n'est inventé.
gg-help-family-policy =
    <b>Politique</b> · /disable commande, /enable commande, /disabled et /disableable couvrent noms et alias. /disableadmin règle l'exemption administrative ; /disabledel la suppression. Les commandes de récupération restent disponibles. /bot2bot off/admin/all vérifie l'appartenance réelle ; une modification exige normalement une révision humaine, /bot2botskipreview est réservé au créateur. /silentactions exige consentement et journal autorisé. runs/saved sans définition documentée renvoient une explication.
gg-help-family-cleanup =
    <b>Nettoyage</b> · /cleancommand admin/user/other et /keepcommand choisissent les commandes. /cleanmsg action/filter/note et /keepmsg ne ciblent que les messages réellement envoyés par ce bot ; reçus et tâches de cinq minutes empêchent les identifiants devinés. /cleanservice et /nocleanservice sélectionnent join/leave/other/photo/pin/title/videochat. Traitement fonctionnel et paiements valides précèdent le nettoyage.
gg-help-family-topics =
    <b>Sujets</b> · /newtopic nom, /renametopic nom, /closetopic et /reopentopic utilisent le sujet réel actuel. /deletetopic exige confirmation du créateur ; /setactiontopic choisit une destination du même groupe. Forum Telegram et manage-topics requis. Les échecs de livraison sur sujet absent/non pris en charge sont signalés tels quels.
gg-help-family-utilities =
    <b>Outils</b> · /echo ou /say rend texte/médias directs ou répondus avec le rendu commun borné. /broadcast est réservé à l'opérateur configuré ou propriétaire réel de l'instance enfant et à ses groupes configurés. Les résultats par destination conservent les livraisons partielles/incertaines ; consulter ou annuler ne renvoie pas les pièces jointes réussies.
gg-help-family-federations =
    <b>Fédérations</b> · /newfed nom crée un UUID propre à ce bot. Les commandes privées utilisent votre fédération possédée sans dépendre des connexions ; lire un UUID n'accorde aucun rôle. /fedpromote et /feddemote gèrent les administrateurs ; /feddemoteme démissionne. /joinfed UUID et /leavefed exigent le créateur actuel du groupe. Supprimer une fédération ne retire pas automatiquement les bannissements Telegram.
    /fban userID motif et /unfban userID nécessitent propriétaire/admin fédéral. /fedreason, /fednotif et /setfedlog appartiennent au propriétaire. /quietfed masque seulement les notices passives. /subfed UUID est dirigé, borné et sans cycle. /fedstat [userID] et /fbanstat UUID donnent état/sources. /fbanlist csv/minicsv/json est réservé au propriétaire avec intervalle partagé de 30 minutes ; /importfbans répond à un CSV ou JSON par lignes borné, avec prise en charge explicite du tableau JSON propre. Seuls les utilisateurs réellement observés sont réconciliés, pas un inventaire complet des membres.
gg-help-family-portability =
    <b>Fichiers et confidentialité</b> · /export all ou modules choisis exige un administrateur ; /import et /reset le créateur humain actuel avec confirmation personnelle de cinq minutes à usage unique. Intervalle local de cinq minutes ; JSON propre versionné, maximum 2MiB et limites configurées. Modules : moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Les modules omis restent. Confiance, épreuves/tâches émises, abonnements, rôles et bannissements actifs ne sont jamais importés.
    /privacy policy/data/delete fonctionne uniquement dans votre propre conversation privée, avec pagination et rétention minimale de sécurité. Ce n'est pas un adaptateur vérifié du format complet Rose.
gg-help-family-discovery =
    <b>Aide</b> · /help affiche les catégories ; /help commande recherche noms/alias ; /help catégorie 2 poursuit. /button aide au balisage des boutons. Chaque guide explique contexte, droits, valeurs et limites. /settings ouvre le panneau personnel du groupe.
gg-lock-album = Albums
gg-lock-anonchannel = Expéditeurs de canaux
gg-lock-audio = Audio
gg-lock-bot = Bots
gg-lock-button = Boutons intégrés
gg-lock-cashtag = Étiquettes monétaires
gg-lock-checklist = Listes de contrôle
gg-lock-cjk = Texte chinois/japonais/coréen
gg-lock-command = Commandes
gg-lock-comment = Commentaires de non-membres
gg-lock-contact = Contacts
gg-lock-cyrillic = Texte cyrillique
gg-lock-document = Documents
gg-lock-email = Adresses électroniques
gg-lock-emoji = Emoji
gg-lock-emojicustom = Emoji personnalisés
gg-lock-emojigame = Jeux emoji
gg-lock-emojionly = Texte uniquement emoji
gg-lock-externalreply = Réponses externes
gg-lock-forward = Transferts
gg-lock-forwarduser = Transferts de personnes
gg-lock-forwardbot = Transferts de bots
gg-lock-forwardchannel = Transferts de canaux
gg-lock-forwardstory = Stories transférées
gg-lock-game = Jeux
gg-lock-gif = Animations GIF
gg-lock-guestbot = Bots invités
gg-lock-inline = Bots intégrés
gg-lock-invitelink = Invitations Telegram
gg-lock-botlink = Liens de bots
gg-lock-location = Positions
gg-lock-outsidereaction = Réactions de non-membres
gg-lock-phone = Numéros de téléphone
gg-lock-photo = Photos
gg-lock-poll = Sondages
gg-lock-reaction = Réactions
gg-lock-rtl = Texte de droite à gauche
gg-lock-spoiler = Contenu masqué
gg-lock-sticker = Autocollants
gg-lock-stickeranimated = Autocollants animés
gg-lock-stickerpremium = Autocollants premium
gg-lock-text = Texte
gg-lock-url = URL
gg-lock-video = Vidéos
gg-lock-videonote = Notes vidéo
gg-lock-links = Liens
gg-lock-invites = Liens d’invitation
gg-lock-forwards = Transferts
gg-lock-media = Médias
gg-lock-stickers = Autocollants
gg-lock-gifs = GIF
gg-lock-voice = Messages vocaux
gg-lock-polls = Sondages
gg-lock-bots = Bots
gg-op-ban = bannir
gg-op-mute = réduire au silence
gg-op-kick = expulser
gg-op-unban = retirer le bannissement
gg-op-unmute = retirer le silence
gg-op-warn = avertir
gg-op-unwarn = retirer un avertissement
gg-op-resetwarns = réinitialiser les avertissements
gg-op-purge = supprimer une plage de messages
gg-op-delete = supprimer un message
gg-op-pin = épingler
gg-op-unpin = désépingler
gg-op-setlog = définir le journal
gg-op-unsetlog = retirer le journal
gg-op-config = modifier les paramètres
gg-op-save = enregistrer le contenu
gg-op-remove = supprimer le contenu
gg-op-panel = ouvrir le panneau
gg-op-unpinall = tout désépingler
gg-op-permapin = épingler durablement
gg-op-promote = nommer administrateur
gg-op-demote = destituer administrateur
gg-op-approve_user = approuver un utilisateur
gg-op-unapprove = retirer une approbation
gg-op-unapproveall = retirer toutes les approbations
gg-op-lock_change = modifier les restrictions
gg-op-allowlist_change = modifier les exceptions
gg-op-allowlist_clear = retirer les exceptions
gg-op-blocklist_change = modifier la liste de blocage
gg-op-blocklist_clear = vider la liste de blocage
gg-op-raid_change = modifier la protection contre les attaques
gg-op-policy_change = modifier la politique de commandes/nettoyage
gg-op-topic_create = créer un sujet
gg-op-topic_rename = renommer un sujet
gg-op-topic_close = fermer un sujet
gg-op-topic_reopen = rouvrir un sujet
gg-op-topic_delete = supprimer un sujet et ses messages
gg-op-echo = envoyer du contenu formaté
