## Independently authored Group Guard pt-br content.
group-welcome = 🛡 Obrigado por me adicionar! Dê-me direitos de administrador para apagar mensagens, restringir membros e fixar mensagens. Configure com /settings.
gg-start = 🛡 Olá <b>{ $name }</b>! Sou o <b>Group Guard</b>: verifico novos membros, protejo contra mensagens excessivas e CAS, modero conteúdos e ofereço notas, filtros, regras e saudações. Adicione-me como administrador e use /settings ou /help.
gg-help = 📖 /help mostra seções; /help comando procura comandos. Moderação: /ban /mute /kick /warn. Conteúdo: /save /filter /rules. Proteção: /lock /blocklist /night. /settings abra o painel pessoal do grupo.
gg-welcome-default = 👋 Bem-vindo { "{" }mention{ "}" } a <b>{ "{" }group{ "}" }</b>!
gg-credit = 🛡 Protegido por @{ $bot }
gg-btn-add = ➕ Adicionar a um grupo
gg-btn-commands = 📖 Comandos
gg-btn-rules = 📜 Regras
gg-btn-human = ✅ Sou uma pessoa
gg-btn-unwarn = ↩️ Remover aviso (administradores)
gg-btn-locks = 🔒 Bloqueios · Quantidade: { $count }
gg-btn-open-settings = ⚙️ Abrir configurações
gg-btn-admin-tab = 🛡 Grupos
gg-captcha = 🤖 Confirme que você é uma pessoa dentro do prazo indicado; caso contrário, você será removido.
    Minutos: { $minutes }
    Membro: { $user }
gg-captcha-button = Toque no botão abaixo 👇
gg-captcha-math = Quanto é <b>{ $a } + { $b }</b>?
gg-captcha-not-you = Este botão pertence a outra pessoa.
gg-captcha-ok = ✅ Bem-vindo!
gg-captcha-wrong = ❌ Resposta incorreta. Você pode tentar novamente enquanto houver tentativas.
    Tentativas restantes: { $left }
gg-captcha-failed = ❌ Demasiadas respostas incorretas.
gg-captcha-passed = ✅ Verificação concluída. Bem-vindo!
    Membro: { $user }
gg-cas-banned = 🚫 Membro conhecido pelo CAS como autor de spam; foi banido.
    Membro: { $user }
gg-join-request = 👋 Confirme que você é uma pessoa para entrar no grupo:
    Grupo: { $group }
gg-join-approved = ✅ Entrada aprovada. Bem-vindo!
gg-join-expired = ⌛ Pedido expirado. Envie um novo pedido de entrada.
gg-goodbye = 👋 O membro saiu do grupo.
    Membro: { $user }
gg-flood-mute = 🌊 Membro silenciado temporariamente por excesso de mensagens.
    Membro: { $user }
gg-flood-kick = 🌊 Membro removido por excesso de mensagens.
    Membro: { $user }
gg-flood-ban = 🌊 Membro banido por excesso de mensagens.
    Membro: { $user }
gg-newbie-links = 🆕 Novos membros não podem enviar links durante as primeiras horas indicadas.
    Horas: { $hours }
    Membro: { $user }
gg-spam-banned = 🧠 Membro banido por spam.
    Membro: { $user }
gg-reason-blocklist = palavra bloqueada
gg-need-right = ⛔ Você precisa do direito de administrador correspondente.
    Direito: { $right }
gg-right-admin = administrador
gg-right-restrict = restringir membros
gg-right-delete = apagar mensagens
gg-right-pin = fixar mensagens
gg-right-change_info = alterar informações do grupo
gg-admins-only = ⛔ Apenas administradores.
gg-need-target = 👤 Responda a uma mensagem ou informe um ID ou @nome de usuário atualmente verificado.
gg-target-admin = 🙅 Esta ação não pode afetar um administrador.
gg-bot-no-rights = ⚠️ Preciso de ser administrador com as permissões necessárias.
gg-banned = 🔨 Membro banido.
    Motivo: { $reason }
    Membro: { $user }
gg-banned-for = 🔨 Membro banido pelo período indicado.
    Motivo: { $reason }
    Tempo: { $time }
    Membro: { $user }
gg-unbanned = ✅ Banimento do membro removido.
    Membro: { $user }
gg-kicked = 👢 Membro removido; pode voltar a entrar.
    Motivo: { $reason }
    Membro: { $user }
gg-muted = 🔇 Membro silenciado.
    Motivo: { $reason }
    Membro: { $user }
gg-muted-for = 🔇 Membro silenciado pelo período indicado.
    Motivo: { $reason }
    Tempo: { $time }
    Membro: { $user }
gg-unmuted = 🔊 O membro pode voltar a escrever.
    Membro: { $user }
gg-warned = ⚠️ Aviso registado para o membro.
    Quantidade: { $count }
    Limite: { $limit }
    Motivo: { $reason }
    Membro: { $user }
gg-warn-limit-ban = 🔨 Limite de avisos atingido; membro banido.
    Limite: { $limit }
    Membro: { $user }
gg-warn-limit-mute = 🔇 Limite de avisos atingido; membro silenciado.
    Limite: { $limit }
    Membro: { $user }
gg-warn-limit-kick = 👢 Limite de avisos atingido; membro removido.
    Limite: { $limit }
    Membro: { $user }
gg-unwarned = ↩️ Um aviso do membro foi removido.
    Quantidade: { $count }
    Limite: { $limit }
    Membro: { $user }
gg-warn-removed = ↩️ Aviso removido pelo administrador.
    Administrador: { $admin }
gg-warns = ⚠️ Avisos do membro:
    Quantidade: { $count }
    Limite: { $limit }
    Membro: { $user }
gg-warns-reset = 🧽 Avisos do membro repostos a zero.
    Membro: { $user }
gg-purge-reply = 🧹 Responda à primeira mensagem a apagar.
gg-purged = 🧹 Mensagens apagadas.
    Quantidade: { $count }
gg-pin-reply = 📌 Responda à mensagem a fixar.
gg-report-reply = 🚨 Responda à mensagem a denunciar.
gg-reported = 🚨 Membro denunciado aos administradores.
    Membro: { $user }
gg-setlog-usage = 📒 Adicione-me como administrador no canal de registro e use <code>/setlog -100…</code> com o respetivo ID.
gg-setlog-failed = ⚠️ Não posso enviar aí. Adicione-me primeiro como administrador.
gg-setlog-done = 📒 Canal de registro ligado.
gg-setlog-off = 📒 Canal de registro desligado.
gg-log-connected = 📒 Esta conversa recebe o registro de moderação do grupo.
    Grupo: { $group }
gg-log-flood = 🌊 Excesso de mensagens detectado:
    Ação: { $action }
    Membro: { $user }
gg-log-report = 🚨 Denúncia de membro:
    Membro: { $user }
gg-log-spam = 🧠 Banimento por spam identificado pela IA:
    Texto: { $text }
    Membro: { $user }
gg-rules = 📜 <b>Regras</b>
    { $rules }
gg-no-rules = 📜 Ainda não há regras. Os administradores podem usar /setrules texto.
gg-rules-saved = 📜 Regras salvas.
gg-rules-cleared = 📜 Regras apagadas.
gg-welcome-usage = 👋 Use <code>/setwelcome Olá {"{"}mention{"}"}, bem-vindo a {"{"}group{"}"}!</code> ou responda a uma mensagem.
gg-welcome-saved = 👋 Saudação salva.
gg-welcome-reset = 👋 Saudação padrão reposta.
gg-note-usage = 📝 <code>/save nome texto</code> ou responda a uma mensagem com <code>/save nome</code>.
gg-filter-usage = 🔁 <code>/filter palavra resposta</code> ou responda com <code>/filter palavra</code>.
gg-note-saved = 📝 Nota salva. Acesso: <code>#{ $key }</code>, conforme as permissões.
gg-filter-saved = 🔁 Responderei quando encontrar «{ $key }».
gg-notes-empty = 📝 Ainda não há notas.
gg-filters-empty = 🔁 Ainda não há filtros.
gg-notes-list = 📝 <b>Notas</b>
gg-filters-list = 🔁 <b>Filtros</b>
gg-item-deleted = 🗑 Entrada apagada.
    Chave: { $key }
gg-item-missing = 🤷 Nada salvo com esse nome.
gg-items-limit = 📦 Limite de notas e filtros deste grupo atingido.
gg-lock-usage = 🔒 Use <code>/lock links</code>. Tipos disponíveis abaixo; <code>all</code> seleciona todos.
    Tipos: { $types }
gg-locked = 🔒 Conteúdos bloqueados:
    Tipos: { $types }
gg-unlocked = 🔓 Conteúdos permitidos:
    Tipos: { $types }
gg-locks-title = 🔒 <b>Bloqueios de conteúdo</b>
gg-locks-panel = 🔒 <b>Bloqueios</b>: os conteúdos bloqueados são apagados; administradores isentos.
gg-lock-links = Links
gg-lock-invites = Links de convite
gg-lock-forwards = Encaminhamentos
gg-lock-media = Multimédia
gg-lock-stickers = Figurinhas
gg-lock-gifs = GIFs
gg-lock-voice = Mensagens de voz
gg-lock-polls = Enquetes
gg-lock-bots = Bots
gg-blocklist = 🚫 <b>Palavras bloqueadas</b>
    Palavras: { $words }
gg-blocklist-empty = 🚫 Nenhuma palavra bloqueada.
gg-blocklist-usage = 🚫 <code>/addblock palavra, outra expressão</code> · <code>/rmblock palavra</code>
gg-blocklist-saved = 🚫 Lista de bloqueio atualizada.
    Quantidade: { $count }
gg-night-usage = 🌙 <code>/night 23 7 +3</code> fecha das 23:00 às 07:00 UTC+3; <code>/night off</code> desativa.
gg-night-on = 🌙 Horário noturno do grupo definido.
    Fim: { $end }
    Início: { $start }
    Fuso horário: { $tz }
gg-night-off = 🌙 Modo noturno desativado.
gg-night-start = 🌙 Boa noite! O grupo fica fechado até à hora indicada.
    Fim: { $end }
gg-night-end = ☀️ Bom dia! O grupo está novamente aberto.
gg-panel = ⚙️ <b>Configurações do grupo</b>
    Toque numa opção para alterar. Define o horário noturno com /night.
    Grupo: { $group }
    Horário noturno: { $night }
gg-panel-sent = 📬 Configurações enviadas em privado.
gg-panel-start-first = 📬 Inicie primeiro uma conversa privada comigo e depois toque abaixo.
gg-credit-vip = 💎 Ocultar a linha de proteção requer VIP. Use /vip em privado.
gg-opt-wel = 👋 Boas-vindas · Valor: { $value }
gg-opt-cln = 🧹 Apagar mensagens de entrada · Valor: { $value }
gg-opt-bye = 👋 Despedida · Valor: { $value }
gg-opt-cap = 🤖 Verificação · Valor: { $value }
gg-opt-cpm = ⏱ Prazo de verificação, minutos · Valor: { $value }
gg-opt-fld = 🌊 Limite de mensagens · Valor: { $value }
gg-opt-fla = 🌊 Ação por excesso de mensagens · Valor: { $value }
gg-opt-wrn = ⚠️ Limite de avisos · Valor: { $value }
gg-opt-wra = ⚠️ Ação dos avisos · Valor: { $value }
gg-opt-act = ⏳ Restrição automática, minutos · Valor: { $value }
gg-opt-cas = 🛡 Proteção CAS · Valor: { $value }
gg-opt-nwb = 🆕 Novos membros sem links, horas · Valor: { $value }
gg-opt-ais = 🧠 Proteção de spam por IA · Valor: { $value }
gg-opt-ngt = 🌙 Modo noturno · Valor: { $value }
gg-opt-crd = 🏷 Linha de proteção · Valor: { $value }
gg-opt-lang = 🌐 Idioma · Valor: { $value }
gg-val-button = Botão
gg-val-math = Cálculo
gg-val-off = desativado
gg-val-mute = silenciar
gg-val-kick = remover
gg-val-ban = banir
gg-adm = 🛡 <b>Group Guard: estatísticas</b>
    Grupos: { $groups }
    Entradas: { $items }
    Avisos: { $warns }
cmd-settings = Configurações do grupo
cmd-help = Guia de comandos
gg-auth-denied = Não foi possível verificar a autorização. Nada foi alterado.
gg-target-invalid = Escolha um membro humano conhecido. Não foi possível verificar o alvo.
gg-duration-invalid = Use uma duração entre 60s e 365d. Comandos temporários exigem duração.
gg-reason-invalid = O motivo pode ter no máximo 256 caracteres.
gg-outcome-failed = A ação falhou ou não foi autorizada.
gg-outcome-partial = Ação concluída parcialmente. Pode permanecer um banimento se a reposição após remoção falhar.
gg-outcome-ancillary = A ação principal terminou, mas um passo associado falhou.
gg-review-request = Revise a ação imutável abaixo. Uma pessoa atualmente autorizada pode aprovar dentro de 120 segundos. A duração é apresentada em segundos.
    Detalhes: { $details }
    Duração: { $duration }
    Operação: { $operation }
    Alvo: { $target }
gg-review-approve = Aprovar esta ação
gg-review-unavailable = Armazenamento de confirmação indisponível. Envie um novo comando.
gg-review-expired = Confirmação expirada, inválida ou já usada.
gg-review-consumed = Confirmação usada. Verifique o resultado; para repetir é necessário novo comando.
gg-duration-permanent = Permanente / sem limite de tempo
gg-purge-ack = A API confirmou os pedidos de eliminação. A quantidade efetivamente apagada é desconhecida.
    Confirmado pela API: { $acknowledged }
    Pedidos: { $requested }
gg-warning-removed = Aviso removido.
gg-op-ban = banir
gg-op-mute = silenciar
gg-op-kick = remover
gg-op-unban = remover banimento
gg-op-unmute = remover silêncio
gg-op-warn = avisar
gg-op-unwarn = remover aviso
gg-op-resetwarns = repor avisos a zero
gg-op-purge = apagar intervalo de mensagens
gg-op-delete = apagar mensagem
gg-op-pin = fixar mensagem
gg-op-unpin = desafixar mensagem
gg-op-setlog = definir destino do registro
gg-op-unsetlog = remover destino do registro
gg-op-config = alterar configurações
gg-op-save = salvar conteúdo
gg-op-remove = remover conteúdo
gg-op-panel = abrir painel
gg-review-details-above = O conteúdo completo pedido está na mensagem imediatamente acima.
gg-warn-pending = Aviso salvo; a ação do limite já está em processamento.
gg-done = Concluído.
gg-setting-saved = Configuração salva.
    Configuração: { $setting }
gg-setting-value = Valor atual da configuração:
    Configuração: { $setting }
    Valor: { $value }
gg-setting-invalid = Configuração inválida. Use on/off, um modo válido ou uma duração como 10m.
gg-warning-settings = Configurações dos avisos:
    Duração: { $duration }
    Expiração: { $expiry }
    Limite: { $limit }
    Modo: { $mode }
gg-admin-changed = Ação administrativa concluída.
    Ação: { $action }
    Membro: { $user }
gg-admin-list = Administradores públicos:
    { $admins }
gg-approved = Membro aprovado.
    Motivo: { $reason }
    Membro: { $user }
gg-unapproved = Aprovações removidas.
    Quantidade: { $count }
gg-approval-status = Estado de aprovação do membro:
    Motivo: { $reason }
    Status: { $status }
    Membro: { $user }
gg-approval-list = Membros aprovados:
    { $approvals }
gg-next-page = Mais entradas: { $command }
gg-range-invalid = Intervalo inválido. Escolha pelo menos uma mensagem e não ultrapasses o limite indicado.
    Limite máximo: { $cap }
gg-range-start = Início salvo para você neste tópico durante dez minutos. Responda à última mensagem com /purgeto.
gg-range-missing = Nenhum início salvo aqui para você. Use primeiro /purgefrom como resposta.
gg-content-needed = Forneça conteúdo ou responda a ele; máximo 3500 caracteres.
gg-log-status = Configurações do registro:
    Categorias: { $categories }
    Destino: { $destination }
gg-log-unverified = Não tenho receção verificada deste comando original do canal. Envie primeiro /setlog no canal.
gg-log-forward = Encaminhe este /setlog original para o grupo. O administrador que liga precisa de direitos de alteração de informações nas duas conversas.
gg-info = Informações do usuário ou conversa:
    ID: { $id }
    Participação: { $membership }
    Nome: { $name }
    Nome de usuário: { $username }
gg-op-unpinall = desafixar todas
gg-op-permapin = fixar permanentemente
gg-op-promote = nomear administrador
gg-op-demote = destituir administrador
gg-op-approve_user = aprovar usuário
gg-op-unapprove = remover aprovação
gg-op-unapproveall = remover todas as aprovações
gg-unknown = Desconhecido
gg-chat-id = ID da conversa:
    ID: { $id }
gg-on = Ativo
gg-off = Inativo
gg-anon-enabled = A confiança em administradores anônimos está ativa aqui. Comandos anônimos deste grupo usam os direitos do bot sem identificar uma pessoa. Ações de proprietário ainda requerem o criador verificado. /anonadmin off volta a ativar revisão humana.
gg-right-invite_users = convidar usuários
gg-right-promote_members = nomear administradores
gg-right-manage_topics = gerir tópicos
gg-right-creator = criador do grupo
gg-log-join = Membro entrou.
    Membro: { $user }
gg-log-leave = Membro saiu.
    Membro: { $user }
gg-warning-row = Registro de aviso:
    Expiração: { $expiry }
    ID: { $id }
    Motivo: { $reason }
gg-menu-prompt = Escolha uma opção.
gg-content-invalid = Conteúdo inválido ou acima dos limites Telegram. Verifique nome, formato, modificadores e botões.
gg-content-unavailable = Conteúdo indisponível ou a sua participação atual no grupo não permite acesso.
gg-btn-private-note = Abrir nota
gg-open-private = Abrir este conteúdo em privado:
gg-items-cleared = Entradas apagadas.
    Quantidade: { $count }
gg-clearall-confirm = O criador do grupo confirme com <code>/{ $command } confirm</code>.
gg-button-usage = Use <code>/button "Rótulo" https://example.com</code>. Acrescente <code>"Nota" #nome same</code> para outro botão na mesma linha. Você recebe marcação e pré-visualização funcional.
gg-btn-accept-rules = Aceitar regras
gg-btn-open-verification = Abrir verificação
gg-captcha-private = Abra a verificação privada para confirmar a sua participação no grupo.
    Membro: { $user }
gg-captcha-choice = Escolha a imagem correspondente nos botões. Modo e posição do caractere indicados abaixo.
    Modo: { $mode }
    Posição: { $position }
gg-captcha-settings = Configurações da verificação:
    Ativo: { $enabled }
    Remoção: { $kick }
    Modo: { $mode }
    Liberação: { $release }
    Segundos: { $seconds }
gg-captcha-dependency = Ativa boas-vindas antes da verificação. Salve regras antes de exigir a sua aceitação.
gg-val-text = Imagem com texto
gg-val-text2 = Imagem com caracteres
gg-captcha-attempts-exhausted = Verificação falhou após demasiadas respostas erradas; a restrição prevista foi aplicada.
gg-captcha-admin-exempt = Agora você é administrador do grupo. Verificação encerrada.
gg-captcha-question-text = Escolha a palavra apresentada na imagem.
gg-captcha-question-math = Resolve a equação na imagem e escolha a resposta.
gg-captcha-question-text2 = Escolha o caractere indicado na imagem, da esquerda para a direita.
    Posição: { $position }
gg-locktypes = Bloqueios disponíveis:
    Tipos: { $types }
gg-allowlist-title = Exceções aos bloqueios de conteúdo
gg-allowlist-invalid = Exceção inválida. Use domínio/caminho, convite exato, @conversa ou identidade declarada como stickerpack:nome.
gg-reason-lock = Conteúdo bloqueado:
    Tipos: { $types }
gg-lock-applied = Regra de bloqueio aplicada.
    Motivo: { $reason }
    Tipos: { $types }
gg-reaction-failed = Não foi possível aplicar a regra de reações. Este servidor Bot API pode não suportar remoção de reações.
    Código: { $code }
gg-reaction-anonymous = Contagens anônimas não fornecem ID de usuário ou conversa autora. A API de remoção exige um; não se declara qualquer remoção.
gg-none = Nenhum
gg-blocklist-title = Lista de bloqueio
gg-blocklist-invalid = Expressão, motivo ou ação inválidos. Verifique aspas, escapes dos curingas e duração exigida para modos temporários.
gg-blocklist-settings = Configurações da lista de bloqueio:
    Eliminação: { $delete }
    Modo: { $mode }
gg-blocklist-action = Regra da lista de bloqueio aplicada ao membro.
    Motivo: { $reason }
    Membro: { $user }
gg-lock-album = Álbuns
gg-lock-anonchannel = Remetentes de canal
gg-lock-audio = Áudio
gg-lock-bot = Bots
gg-lock-button = Botões em linha
gg-lock-cashtag = Marcas de moeda
gg-lock-checklist = Listas de verificação
gg-lock-cjk = Texto chinês/japonês/coreano
gg-lock-command = Comandos
gg-lock-comment = Comentários de não membros
gg-lock-contact = Contatos
gg-lock-cyrillic = Texto cirílico
gg-lock-document = Documentos
gg-lock-email = Endereços de correio eletrónico
gg-lock-emoji = Emoji
gg-lock-emojicustom = Emoji personalizados
gg-lock-emojigame = Jogos emoji
gg-lock-emojionly = Texto só com emoji
gg-lock-externalreply = Respostas externas
gg-lock-forward = Encaminhamentos
gg-lock-forwarduser = Encaminhamentos de usuários
gg-lock-forwardbot = Encaminhamentos de bots
gg-lock-forwardchannel = Encaminhamentos de canais
gg-lock-forwardstory = Histórias encaminhadas
gg-lock-game = Jogos
gg-lock-gif = Animações GIF
gg-lock-guestbot = Bots convidados
gg-lock-inline = Bots em linha
gg-lock-invitelink = Convites Telegram
gg-lock-botlink = Links para bots
gg-lock-location = Localizações
gg-lock-outsidereaction = Reações de não membros
gg-lock-phone = Números de telefone
gg-lock-photo = Fotografias
gg-lock-poll = Enquetes
gg-lock-reaction = Reações
gg-lock-rtl = Texto da direita para a esquerda
gg-lock-spoiler = Conteúdo oculto
gg-lock-sticker = Figurinhas
gg-lock-stickeranimated = Figurinhas animados
gg-lock-stickerpremium = Figurinhas premium
gg-lock-text = Texto
gg-lock-url = URLs
gg-lock-video = Vídeos
gg-lock-videonote = Mensagens de vídeo
gg-flood-status = Mensagens excessivas: limite consecutivo em N; janela temporal acima de N. Ação, duração e limpeza de sequência indicadas abaixo.
    Limpar toda a sequência: { $clear }
    Limite consecutivo: { $consecutive }
    Quantidade: { $count }
    Duração: { $duration }
    Modo: { $mode }
    Segundos: { $seconds }
gg-raid-status = Proteção de entradas em massa. /antiraid on ativa; /antiraid off para. Período, duração de banimento e limite automático por minuto indicados abaixo.
    Ativo: { $active }
    Limite automático: { $auto }
    Duração de banimento: { $ban }
    Período: { $period }
    Até: { $until }
gg-raid-banned = 🛡 Membro banido temporariamente durante a proteção ativa de entradas em massa.
    Membro: { $user }
gg-raid-declined = 🛡 Pedido recusado durante a proteção ativa de entradas em massa.
    Membro: { $user }
gg-silent-consent-required = O criador deve autorizar ações silenciosas e configurar um registro antes de escolher esta ação.
gg-btn-enable-raid = Ativar proteção de entradas em massa
gg-human-required = Esta ação exige uma pessoa identificável.
gg-group-message-required = Use este comando numa mensagem ou tópico real do grupo. IDs de mensagens privadas não identificam mensagens do grupo.
gg-connection-private = Use este comando de conexão na nossa conversa privada.
gg-connection-disconnected = Desligado. Os seus últimos cinco grupos continuam disponíveis para voltar a ligar.
gg-connection-current = Grupo ligado. Participação e direitos atuais verificados em cada ação.
    Grupo: { $group }
gg-connection-none = Nenhuma conexão ativa. Use /connect GROUP_ID ou /connect @grupo.
gg-connection-open = Abra a sua conexão pessoal na nossa conversa privada.
gg-btn-connect = Ligar em privado
gg-connection-history = Os seus últimos cinco grupos. Escolha um; é necessário seres membro atual.
gg-connection-unavailable = Conexão indisponível. Você precisa ser membro humano atual e o bot administrador desse grupo.
gg-catalog-unresolved = /{ $command } consta do catálogo sem ação definida. Use /notes ou /flood para funções implementadas.
gg-cleanup-failed = Limpeza de mensagens falhou ou está indisponível; não se afirma eliminação.
gg-op-lock_change = alterar bloqueios
gg-op-allowlist_change = alterar exceções
gg-op-allowlist_clear = apagar exceções
gg-op-blocklist_change = alterar lista de bloqueio
gg-op-blocklist_clear = esvaziar lista de bloqueio
gg-op-raid_change = alterar proteção de entradas em massa
gg-disabled-list = Política de comandos: /disable NOME e /enable NOME controlam execução; /disabledel eliminação; /disableadmin inclui administradores.
    Comandos: { $commands }
gg-cleanup-types = Categorias de limpeza disponíveis:
    Tipos: { $types }
gg-cleanup-selected = Categorias de limpeza selecionadas:
    Tipos: { $types }
gg-advanced-status = Automação silenciosa exige consentimento do criador e registro. Bots precisam dos direitos normais; revisão das alterações ativa por padrão. Configure visibilidade entre bots no BotFather.
    Configuração: { $setting }
    Valor: { $value }
gg-action-topic = Tópico das ações. /setactiontopic escolha o tópico atual do fórum; tópico geral tem ID 1.
    Tópico: { $topic }
gg-topic-unavailable = É necessário um fórum atual e os direitos adequados de gestão.
gg-topic-id-required = Na conversa privada ligada, informe explicitamente o ID do tópico.
gg-topic-general-delete = O tópico geral não pode ser apagado. A confirmação requer pessoa identificável.
gg-topic-delete-confirm = Apagar tópico e mensagens? Confirmação pessoal válida por dois minutos.
    Tópico: { $topic }
gg-btn-confirm-delete = Confirmar eliminação
gg-topic-changed = Ação do tópico concluída.
    Ação: { $action }
    Tópico: { $topic }
gg-op-policy_change = alterar política de comandos/limpeza
gg-op-topic_create = criar tópico
gg-op-topic_rename = renomear tópico
gg-op-topic_close = fechar tópico
gg-op-topic_reopen = reabrir tópico
gg-op-topic_delete = apagar tópico e mensagens
gg-op-echo = enviar conteúdo formatado
gg-broadcast-owner = Apenas o operador configurado deste bot ou o proprietário real da instância filha pode enviar campanhas aos seus grupos.
gg-broadcast-queued = Campanha de grupos na fila. Destinos e resultados separados por bot.
    ID: { $id }
gg-broadcast-busy = Outra campanha ativa ou o intervalo de cinco minutos desde a criação anterior ainda não terminou.
gg-broadcast-empty = Você não tem campanha de grupos neste bot.
gg-broadcast-status = Estado da campanha de grupos:
    Cancelados: { $cancelled }
    Falhados: { $failed }
    ID: { $id }
    Na fila: { $queued }
    Entregues: { $sent }
    Status: { $status }
    Resultado incerto: { $uncertain }
gg-fed-created = Federação criada. O ID pertence à rede separada deste bot.
    ID: { $id }
    Nome: { $name }
gg-fed-info = Informações da federação:
    Administradores: { $admins }
    ID: { $id }
    Registro: { $log }
    Nome: { $name }
    Notificações: { $notifications }
    Proprietário: { $owner }
    Motivos obrigatórios: { $reasons }
gg-fed-list = As suas federações como proprietário ou administrador:
    { $rows }
gg-fed-admins = Primeiro o proprietário, depois os administradores da federação:
    { $rows }
gg-fed-quiet = Explicações passivas silenciosas. A aplicação dos bloqueios continua ativa.
    Valor: { $value }
gg-fed-policy = Políticas de motivos e notificações ao proprietário:
    Notificações: { $notifications }
    Motivos obrigatórios: { $reasons }
gg-fed-confirm-delete = Apagar definitivamente federação, dados e participações? Banimentos Telegram existentes permanecem. Confirmação pessoal dentro de cinco minutos.
    ID: { $id }
    Nome: { $name }
gg-fed-confirm-log = Definir o registro de federação indicado? Confirme dentro de cinco minutos. Os seus direitos no destino e a capacidade de publicação do bot serão novamente verificados.
    Destino: { $destination }
    ID: { $id }
    Nome: { $name }
gg-fed-confirm-sent = Confirmação pessoal enviada ao proprietário da federação.
gg-fed-deleted = Federação apagada. Banimentos Telegram existentes permanecem.
gg-fed-log-set = Destino do registro da federação definido:
    Destino: { $destination }
gg-fed-cancel = Cancelar
gg-fed-cancelled = Cancelado.
gg-fed-saved-delivery-failed = Alteração salva, mas notificação ou registro não entregues. Verifique destino e acesso do bot.
gg-fed-error-authority = É necessário proprietário atual da federação ou o papel adequado. Direitos de grupo Telegram não atribuem direitos de federação.
gg-fed-error-private = Use este comando na sua própria conversa privada com este bot.
gg-fed-error-group = Use o comando no grupo real. Uma conexão privada não escolha o grupo da federação.
gg-fed-error-owned = Já és proprietário de uma federação neste bot. Use /fedinfo, /renamefed ou /delfed em privado.
gg-fed-error-name = Informe um nome não vazio sem caracteres de controlo. Os nomes são limitados a 64 caracteres.
gg-fed-error-id = Informe uma UUID válida de federação deste bot. IDs Rose não ligam ao nosso serviço separado.
gg-fed-error-missing = Nenhuma federação encontrada neste bot ou contexto.
gg-fed-error-creator = Apenas o criador atual do grupo Telegram pode aderir a uma federação ou sair dela.
gg-fed-error-target = Informe um ID humano positivo, uma resposta a uma pessoa ou nome atualmente verificado. O proprietário não pode ser destituído.
gg-fed-error-value = Argumentos de federação inválidos. Use on/off nas políticas e ID válido quando exigido.
gg-fed-error-stale = Confirmação expirada, usada ou federação, proprietário ou destino alterados. Peça uma nova.
gg-fed-error-destination = O proprietário precisa de administração atual do destino e o bot de acesso a publicação. Canais exigem post_messages.
gg-fed-error-delivery = Confirmação pessoal não entregue ou não associada. Abra conversa privada com o bot e tente novamente.
gg-fed-event = Evento da federação:
    Evento: { $event }
    ID: { $id }
    Nome: { $name }
    Membro: { $user }
gg-fed-event-rename = nome alterado
gg-fed-event-delete = apagada; banimentos Telegram mantidos
gg-fed-event-promote = administrador adicionado
gg-fed-event-demote = administrador removido
gg-fed-event-self-remove = administrador demitiu-se
gg-fed-event-reason = política de motivos alterada
gg-fed-event-notif = notificações do proprietário alteradas
gg-fed-event-log = destino do registro alterado
gg-fed-event-unlog = destino do registro removido
gg-fed-event-ban = política de banimento salva; aplicação na fila
gg-fed-event-unban = política de banimento removida; libertação de restrições próprias na fila
gg-fed-event-subscribe = assinatura adicionada; verificação dos usuários observados na fila
gg-fed-event-unsubscribe = assinatura removida; outras fontes mantidas
gg-fed-ban-details = Alvo e motivo do banimento:
    Motivo: { $reason }
    Membro: { $user }
gg-fed-passive = A política da federação bane o membro. Fonte e motivo abaixo.
    ID: { $id }
    Motivo: { $reason }
    Fonte: { $source }
    Membro: { $user }
gg-fed-enforce-failed = A política da federação bane o membro, mas a remoção falhou. Verifique direitos do bot. Fonte e motivo abaixo.
    ID: { $id }
    Motivo: { $reason }
    Fonte: { $source }
    Membro: { $user }
gg-fed-stat = Banimentos de federação deste membro:
    { $rows }
    Membro: { $user }
gg-fed-stat-line = { $name } (<code>{ $id }</code>) — ativo: { $status }; alterado: { $date }.
gg-fed-stat-more = Há mais fontes. Use o comando de continuação ou ID de federação específico para motivo e data.
gg-fed-intent-saved = Política salva; alvos observados na fila. Direitos atuais e outras fontes de restrição serão verificados antes dos efeitos.
    Membro: { $user }
    Versão: { $version }
gg-fed-subscriptions = Assinaturas diretas de banimentos de federação:
    { $rows }
gg-fed-imported = Entradas verificadas e salvas; duplicados idênticos ignorados. Aplicação aos alvos observados na fila.
    Quantidade: { $count }
    Duplicados idênticos: { $duplicates }
gg-fed-event-import = banimentos verificados importados; aplicação na fila
gg-fed-error-file-format = Responda a CSV UTF-8 com id/reason, JSONL/NDJSON com user_id ou exportação de matriz JSON deste bot. Uma linha inválida impede todas as escritas.
gg-fed-error-file-limit = Máximo 2 MiB e 1000 entradas. Arquivos ausentes ou demasiado grandes recusados; listas nunca truncadas silenciosamente.
gg-fed-error-file-duplicate = Entradas em conflito para o mesmo ID de usuário. Nenhum banimento importado.
gg-fed-error-file-rate = Importação e exportação partilham um intervalo de 30 minutos por federação. Tente mais tarde.
gg-fed-error-reason = Motivos de banimento: máximo 1024 caracteres sem caracteres de controlo não suportados.
gg-fed-error-reason_required = Esta federação exige motivo não vazio para cada banimento.
gg-fed-error-cycle = Uma federação não pode subscrever-se a si própria nem criar ciclo dirigido.
gg-fed-error-graph_limit = Limite atingido: 32 destinos diretos, 128 federações alcançáveis, profundidade 16 ou 10 000 links neste bot.
gg-data-confirm = Confirme dentro de cinco minutos. Criador atual e revisão do grupo serão novamente verificados. Só mudam os módulos escolhidos; identidade, confiança e banimentos ativos mantidos.
    SHA-256: { $digest }
    Grupo: { $group }
    Módulos: { $modules }
    Operação: { $operation }
gg-data-import = Importar módulos do grupo
gg-data-reset = Repor módulos do grupo
gg-data-privacy-delete = Apagar dados pessoais opcionais deste bot
gg-data-confirm-button = Confirmar esta alteração
gg-data-personal = Abra a confirmação na sua conversa privada.
gg-data-saved = Módulos escolhidos salvos.
gg-data-error-authority = Importar e repor requerem o criador atual identificável do grupo. Exportar requer administrador atual.
gg-data-error-format = Responda a JSON Group Guard válido e versionado, criado com /export.
gg-data-error-limit = O arquivo ultrapassa o limite de tamanho ou conteúdo configurado.
gg-data-error-version = Esquema ou versão não suportados; nenhuma alteração aplicada.
gg-data-error-module = Escolha módulos conhecidos: /export all ou /export notes rules. Importar e repor usam os mesmos nomes.
gg-data-error-field = Campos de módulo inválidos ou em falta. Nenhuma configuração aplicada.
gg-data-error-item = Conteúdo, opções ou acesso à repetição inválidos. Nenhum conteúdo salvo.
gg-data-error-media = Os arquivos devem ser enviados para este bot e acessíveis por getFile. IDs de arquivos de outros bots não são suportados.
gg-data-error-destination = Destinos de registro e tópicos requerem direitos atuais e capacidades do bot. IDs de tópicos só valem no mesmo grupo.
gg-data-error-language = Escolha um idioma instalado com /setlang.
gg-data-error-stale = Confirmação expirada, alterada ou usada. Começa novamente.
gg-data-error-restore = Não foi possível repor com segurança as restrições temporárias próprias. Provas mantidas; verifique direitos do bot.
gg-data-error-rate = Operações de dados do grupo têm intervalo local de cinco minutos. Tente mais tarde.
gg-data-error-delivery = Confirmação privada não entregue. Inicie conversa privada com o bot e tente novamente.
gg-data-error-saved_delivery = Configurações salvas, mas sugestões de comandos não atualizadas. Verifique permissões do bot.
gg-privacy-policy = <b>Os seus dados neste Group Guard</b>
    /privacy data exporta links, perfis observados, avisos, aprovações, estado de restrições e verificações, propriedade, papéis e banimentos de federação e trabalhos de segurança. Exclui conteúdo privado alheio, respostas de verificação, autenticação e arquivos em bruto. Siga o comando de continuação.
    /privacy delete remove histórico opcional de links, nome e nome de usuário observados, verificações inativas e conteúdo das suas campanhas terminadas neste bot. Avisos e restrições ativos, versões de banimentos, papéis, propriedade, assinaturas, proteção de repetição e chamadas API incertas mantêm identificadores mínimos de segurança e ordenação. Use comandos explícitos de saída/eliminação da federação para essas relações. Perfil partilhado da plataforma e outros bots mantidos.
    Operadores gerem cópias de segurança e auditoria separadamente. Este comando não apaga mensagens Telegram externas nem cópias de segurança e não promete prazo automático de retenção.
gg-privacy-usage = /privacy policy · /privacy data [continuação] · /privacy delete — apenas na sua própria conversa privada com este bot.
gg-privacy-private = Esta ação exige a conversa privada da pessoa requerente. Cursores inválidos não dão acesso a dados alheios.
gg-privacy-next = Próxima página: /privacy data { $cursor }
gg-privacy-deleted = Dados pessoais opcionais deste bot removidos. Segurança ativa, propriedade e trabalhos incertos mantêm identificadores mínimos; consulte /privacy policy.
gg-language-usage = Escolha o idioma do grupo com /setlang. /lang em privado altera o seu idioma pessoal da plataforma. Códigos disponíveis abaixo.
    Códigos de idioma: { $codes }
gg-language-saved = Idioma das respostas do grupo alterado.
gg-help-index = <b>Guia de comandos Group Guard</b>
    /help seção · /help comando · /help seção 2. Comandos indicados também funcionam com /connect verificado; respostas privadas ficam na conversa privada real.
    Configurações requerem alteração de informações, sanções restrição de membros, eliminação direitos de apagar, fixação direitos de fixar, nomeações promoção de administradores e tópicos gestão de tópicos. Direitos do bot verificados separadamente. Ações de proprietário requerem o criador humano atual. /settings abra o painel pessoal do grupo.
gg-help-search = <b>Comandos correspondentes</b>
    Pesquisa: { $query }
gg-help-connected = Grupo ou conexão verificada; direitos na seção
gg-help-group-only = É necessária uma mensagem real do grupo
gg-help-unsupported = Nome de catálogo mantido; comportamento não documentado devolve explicação
gg-help-next = Página seguinte
gg-help-previous = Página anterior
gg-help-family-title-moderation = Moderação e aprovações
gg-help-family-title-messages = Apagar e fixar mensagens
gg-help-family-title-logging = Registos autorizados
gg-help-family-title-settings = Configurações e idioma do grupo
gg-help-family-title-content = Notas, filtros, regras e saudações
gg-help-family-title-captcha = Verificação de novos membros
gg-help-family-title-locks = Bloqueios de conteúdo e exceções
gg-help-family-title-blocklists = Correspondências e ações da lista de bloqueio
gg-help-family-title-antispam = Proteção de mensagens excessivas e entradas em massa
gg-help-family-title-connections = Links privadas a grupos
gg-help-family-title-identity = Informações de usuários e conversas
gg-help-family-title-policy = Políticas de comandos e bots
gg-help-family-title-cleanup = Limpeza de comandos, bots e serviços
gg-help-family-title-topics = Tópicos do fórum
gg-help-family-title-utilities = Envio de conteúdo e campanhas do operador
gg-help-family-title-federations = Papéis, banimentos e assinaturas de federação
gg-help-family-title-portability = Arquivos de grupo e dados pessoais
gg-help-family-title-discovery = Ajuda e editor de conteúdo
gg-help-family-moderation = <b>Moderação</b> · Resposta, ID numérico ou @usuário verificado. /ban 20 motivo; /tban 20 60s motivo; /mute 20; /tmute 20 2h motivo. Duração: 60 segundos–365 dias. /kickme remove apenas o requerente. Variantes d apagam a mensagem respondida; s apagam comando/resposta e requerem eliminação. Administradores protegidos. /setwarnlimit 3; /setwarnmode ban; /setwarntime 1d. Novos grupos: três avisos; configurações antigas mantidas. /approve isenta apenas de proteção normal de conteúdo/mensagens, nunca federação/CAS/entradas em massa/ações manuais. /promote não ultrapassa direitos comuns do requerente e bot. Reposição global só pelo criador.
gg-help-family-messages = <b>Mensagens</b> · /del exige resposta real no grupo. /purge começa aí; /purgefrom e /purgeto guardam limites. Aplicam-se limites configurados e regras Telegram; confirmação em lote não prova quantidade exata apagada. /pin [loud], /permapin, /unpin e /unpinall exigem fixação; remover todas só pelo criador. /antichannelpin e /cleanlinked controlam mensagens automáticas do canal ligado.
gg-help-family-logging = <b>Registos</b> · /setlog -100… exige administração atual do destino e publicação pelo bot. Configuração encaminhada só corresponde a original realmente recebido. /logcategories: settings/admin/user/automated/reports/other; /log e /nolog escolhem categorias. Falhas de entrega mantêm-se visíveis e não provam sucesso da ação.
gg-help-family-settings = <b>Configurações</b> · /settings abra painel pessoal com expiração e verificação atual de alteração de informações. /setlang código salva idioma do grupo; /lang em privado o idioma pessoal. /night 23 7 +3 fecha à noite; /night off repõe apenas o estado de permissões próprio ainda correspondente. Alterações externas têm prioridade.
gg-help-family-content = <b>Editor</b> · /save palavra texto ou resposta a arquivo; /get palavra, #palavra, /notes leem notas. Nomes novos: uma palavra; nomes antigos mais amplos mantidos. /filter "expressão" texto, /filterprefix e /filterexact escolhem correspondência; /stop remove chave. /clearall e /stopall precisam de confirmação do criador. Formato Rose: negrito/itálico/sublinhado/riscado/código, links, citações e alternativas aleatórias %%%. Campos: { "{" }first{ "}" }, { "{" }last{ "}" }, { "{" }fullname{ "}" }, { "{" }username{ "}" }, { "{" }mention{ "}" }, { "{" }id{ "}" }, { "{" }chatname{ "}" }, { "{" }count{ "}" }. /button cria botões URL/nota/regras. Opções gerais preview/nonotif/protect/mediaspoiler; notas admin/private/noprivate/repeat; filtros user/allow_bot/replytag/command. /save palavra Olá { "{" }repeat 5m{ "}" } agenda apenas conteúdo público com direitos atuais do autor. Regras, saudações e conteúdo privado usam o mesmo renderizador. IDs de arquivo pertencem ao bot.
gg-help-family-captcha = <b>Verificação</b> · /captcha on/off; /captchamode off/button/math/text/text2; /setcaptchatext; /captcharules on; /captchakick on/off; /captchakicktime e /captchamutetime definem prazos limitados. Desafios emitidos mantêm geração/prazo. Pedidos precisam de invite-users; silêncio restrict-members. Respostas pessoais e únicas. Banimentos de federação antecedem aprovação/CAPTCHA.
gg-help-family-locks = <b>Bloqueios</b> · /lock links [ação], /unlock tipo; /locktypes lista tipos reais, /locks estado. /lockwarns controla avisos. /allowlist: domínio/caminho, convite exato, @conversa ou stickerpack:/forward:/inline:/channel:/chat:/bot:/command:. Padrões inválidos recusados. Exceções só para conteúdo correspondente; automação silenciosa precisa de criador e registro autorizado.
gg-help-family-blocklists = <b>Lista de bloqueio</b> · /addblocklist "expressão" aceita texto/prefixo/exato e identidades declaradas com motivo/ação opcionais. /rmblocklist remove chaves exatas escolhidas. /blocklistmode nothing/warn/kick/ban/tban/mute/tmute escolha ação; modos temporários exigem duração. /blocklistdelete separa eliminação. Padrões curinga limitados; entradas inválidas e excessos recusados.
gg-help-family-antispam = <b>Mensagens e entradas em massa</b> · /setflood número limita mensagens consecutivas; /setfloodtimer número duração janela temporal; /setfloodmode sanção/duração; /clearflood limpeza da sequência. Configurações antigas mantidas. /flood e /antiflood mostram política; alias é decisão local de compatibilidade. /antiraid on/off/duration, /raidtime, /raidactiontime, /autoantiraid guardam prazo e sanção separada para novas entradas. Prioridade sobre aprovação/CAPTCHA; expiração por geração resistente a reinícios.
gg-help-family-connections = <b>Links</b> · /connect groupID ou conexão pessoal. Participação do requerente e bot verificada; alterações continuam a exigir direitos exatos atuais. /connection mostra escolha, /disconnect remove, /connect mostra histórico com continuação. Conexão não dá propriedade de federação nem direitos de operador.
gg-help-family-identity = <b>Informações</b> · /id mostra IDs reais de usuário/conversa/origem; /info o alvo atual. Respostas e @nomes exigem provas atuais deste bot. Mensagens anônimas de grupo não identificam uma pessoa; não se inventa ID humano.
gg-help-family-policy = <b>Políticas</b> · /disable comando, /enable comando, /disabled, /disableable usam nomes canónicos e aliases. /disableadmin gere isenção de administradores; /disabledel eliminação. Comandos de recuperação continuam acessíveis. /bot2bot off/admin/all verifique participação real; alterações geralmente requerem revisão humana. /bot2botskipreview só criador. /silentactions exige consentimento e registro autorizado. runs/saved sem configuração devolvem explicação.
gg-help-family-cleanup = <b>Limpeza</b> · /cleancommand admin/user/other e /keepcommand escolhem comandos. /cleanmsg action/filter/note e /keepmsg só mensagens realmente enviadas por este bot; recibos e trabalhos de cinco minutos impedem IDs adivinhados. /cleanservice e /nocleanservice: join/leave/other/photo/pin/title/videochat. Processamento funcional e pagamentos válidos antes da limpeza.
gg-help-family-topics = <b>Tópicos</b> · /newtopic nome, /renametopic nome, /closetopic, /reopentopic usam o tópico real atual. /deletetopic exige confirmação do criador; /setactiontopic escolha destino no mesmo grupo. Fórum Telegram e manage-topics necessários. Erros de tópico ausente/não suportado relatados corretamente.
gg-help-family-utilities = <b>Ferramentas</b> · /echo e /say enviam conteúdo direto/respondido pelo renderizador comum limitado. /broadcast reservado ao operador configurado ou verdadeiro proprietário filho; só grupos configurados deste bot. Resultados por destino mantêm entregas parciais/incertas; estado e cancelamento não repetem anexos bem-sucedidos.
gg-help-family-federations = <b>Federações</b> · /newfed nome cria UUID neste bot. Comandos privados usam federação própria independentemente de links; ler UUID não atribui papel. /fedpromote e /feddemote gerem administradores, /feddemoteme abandona o papel. /joinfed UUID e /leavefed exigem criador atual do grupo. Eliminação não remove banimentos Telegram. /fban userID motivo e /unfban userID exigem proprietário/administrador da federação; /fedreason, /fednotif, /setfedlog proprietário. /quietfed oculta só avisos passivos. /subfed UUID dirigido, limitado e sem ciclos. /fedstat [userID], /fbanstat UUID mostram fontes/estado. /fbanlist csv/minicsv/json só proprietário com intervalo partilhado de 30 minutos; /importfbans responda a CSV limitado ou JSON real linha a linha e aceita explicitamente a própria matriz JSON. Verifique só usuários observados; não declara inventário completo de membros.
gg-help-family-portability = <b>Arquivos e privacidade</b> · /export all ou módulos exige administrador; /import e /reset criador humano atual com confirmação pessoal única de cinco minutos. Intervalo local de cinco minutos; JSON próprio versionado, máximo 2MiB e limites configurados. Módulos: moderation protections captcha flood raid night locks blocklists rules notes filters greetings policy language destinations extensions. Módulos omitidos mantidos. Confiança, desafios/trabalhos emitidos, assinaturas, papéis e banimentos ativos nunca importados. /privacy policy/data/delete só conversa privada pessoal com páginas e retenção mínima de segurança. Sem adaptador verificado para exportação Rose completa.
gg-help-family-discovery = <b>Ajuda</b> · /help mostra seções; /help comando procura nomes/aliases; /help seção 2 continua. /button ajuda na marcação. Cada guia descreve contexto, direitos, padrões e limites. /settings abra o painel pessoal do grupo.
gg-data-error-cache_pending = Dados SQL opcionais removidos. Limpeza da cache indisponível na fila; dados de segurança ativos mantidos.
