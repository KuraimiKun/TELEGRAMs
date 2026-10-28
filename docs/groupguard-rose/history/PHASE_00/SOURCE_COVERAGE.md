# Source coverage ledger — incomplete

Date: 2026-10-12, Asia/Jakarta. `retrieved` means actual content was read, not inferred from a familiar bot or old API knowledge.

| Source | Section | Outcome / evidence |
|---|---|---|
| https://missrose.org/docs/ | Root and all nested functional/explanation links | **Not retrieved.** Proxy CONNECT 403; root link graph unavailable. Nested URL/section denominator unknown. Zero Rose pages read. |
| https://core.telegram.org/bots/api | Current methods/types/limitations | **Not retrieved.** Proxy CONNECT 403. Installed SDK evidence below cannot certify current website text. |
| https://raw.githubusercontent.com/tdlib/telegram-bot-api/master/README.md | Usage/local mode/documentation | **Retrieved.** Official local server README; no claim deployed server/version verified. |
| Repository README.md; docs/BOT_SDK.md; docs/DESIGN_SYSTEM.md; docs/OPERATIONS.md | Setup, SDK, UI, production operations | **Read locally** at audited HEAD. |
| pyproject.toml; bots/groupguard and locales/tests; core SDK/runtime/middleware/services; factory lifecycle; migrations 0001–0007; existing test harness | Local behavior and implementation evidence | **Inspected**, with exact evidence paths in matrix/baseline. |
| Supplied local reference d55fc44… | Previous checkout comparison | **Unavailable.** Absent object and upload-pack not our ref on fetch. |

Required Rose coverage categories remain unretrieved: all pages/anchors/tables; aliases/variants/modifiers and indirect commands; default behavior; caller/bot rights; private/connection flows; language roster; custom clone annotations; relevant functional external links; ambiguous examples; explanation-only sections. None can be counted complete from the prompt's roadmap. REQ-P02..P12 rows enumerate 51 requested planning areas, not Rose's actual section list.

## Current client evidence and exact verification gaps

Installed aiogram 3.31.0 contains Update.message_reaction and message_reaction_count, Message.sender_chat, ChatJoinRequest.user_chat_id, ChatPermissions.can_react_to_messages/can_manage_topics, independent-permission flags on restrictChatMember/setChatPermissions, and methods banChatSenderChat/unbanChatSenderChat/setMessageReaction/promoteChatMember/setChatAdministratorCustomTitle/deleteMessages/unpinAllChatMessages/createForumTopic/editForumTopic/getChatMember.

Its generated Update docstrings say reaction subscriptions must be explicit and the bot must be administrator; aggregate anonymous counts can be delayed and are not per-user identity. getUpdates/setWebhook docstrings exclude chat_member and both reaction types from the empty-list default. Restriction docstrings state supergroup/admin requirements and durations below 30s or above 366d become indefinite. deleteMessages accepts 1–100 IDs and shares deleteMessage limits including 48h. Join-request docstrings state user_chat_id is usable for 5 minutes until processing, subject to no other admin having contacted the user; approval needs can_invite_users. These are installed-client evidence, not a successful live call or retrieved current official site.

The official README verifies local mode's 2000MB upload/unlimited download/local file and webhook options; it does not verify reaction semantics, bot-to-bot rules, cross-bot file_id portability or any deployed aiogram/telegram-bot-api image. The repository's default local image tag is latest and no local server is running here. Treat media file_ids as origin-bot scoped until exact sending-files semantics/transport are verified; file_unique_id is not a send credential.

Before closing Phase 0, obtain read access or a complete dated snapshot, enumerate every reachable URL and functional anchor, paraphrase behaviors, expand all area rows into independent acceptance IDs, reconcile source coverage against matrix, and update ambiguous/unavailable entries explicitly. Do not manufacture a page roster from memory.
