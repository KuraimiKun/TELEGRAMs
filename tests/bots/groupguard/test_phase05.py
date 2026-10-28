"""Actual lock CRUD/effects, actor scopes and supported reaction RPCs in all bot contexts."""

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import DeleteMessageReaction
from aiogram.types import (
    Chat,
    ChatMemberLeft,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MessageEntity,
    MessageOriginChannel,
    MessageOriginUser,
    MessageReactionCountUpdated,
    MessageReactionUpdated,
    ReactionCount,
    ReactionTypeEmoji,
    Update,
)
from sqlalchemy import select

from bots.groupguard.models import GuardEventReceipt
from core.db.base import utcnow
from tests.bots.groupguard.test_groupguard import ADMIN, GROUP, MEMBER, gctx, group_msg, tg_user
from tests.bots.groupguard.test_phase01a import admin_member, env, send

__all__ = ["env", "gctx"]


@pytest.mark.parametrize(
    "kind,text,extra",
    [
        ("text", "ordinary", {}),
        ("cjk", "中文", {}),
        ("cyrillic", "Привет", {}),
        ("rtl", "مرحبا", {}),
        ("emoji", "Hello 😀", {}),
        ("emojionly", "😀 👩‍💻", {}),
        ("email", "a@example.org", {}),
        ("phone", "+1 234 567 890", {}),
        ("zalgo", "a\u0301\u0302\u0303\u0304", {}),
        ("command", "/terms", {}),
        (
            "url",
            "click",
            {"entities": [MessageEntity(type="text_link", offset=0, length=5, url="https://evil.example")]},
        ),
        ("invitelink", "https://t.me/+private", {}),
        ("botlink", "https://t.me/example_bot", {}),
        ("cashtag", "$USD", {"entities": [MessageEntity(type="cashtag", offset=0, length=4)]}),
        ("spoiler", "secret", {"entities": [MessageEntity(type="spoiler", offset=0, length=6)]}),
        (
            "emojicustom",
            "😀",
            {"entities": [MessageEntity(type="custom_emoji", offset=0, length=2, custom_emoji_id="9901")]},
        ),
        ("album", "caption", {"media_group_id": "album"}),
        (
            "forwarduser",
            "forwarded",
            {"forward_origin": MessageOriginUser(date=utcnow(), sender_user=tg_user(88))},
        ),
        (
            "forwardbot",
            "forwarded",
            {
                "forward_origin": MessageOriginUser(
                    date=utcnow(), sender_user=tg_user(88).model_copy(update={"is_bot": True})
                )
            },
        ),
        (
            "forwardchannel",
            "forwarded",
            {
                "forward_origin": MessageOriginChannel(
                    date=utcnow(), chat=Chat(id=-10088, type="channel"), message_id=9
                )
            },
        ),
        (
            "forward",
            "forwarded",
            {"forward_origin": MessageOriginUser(date=utcnow(), sender_user=tg_user(88))},
        ),
        (
            "button",
            "button",
            {
                "reply_markup": InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="Go", url="https://evil.example")]]
                )
            },
        ),
    ],
)
async def test_typed_locks_delete_actual_offending_message_and_exempt_admin(env, api, kind, text, extra):
    await send(env, group_msg("/lock " + kind, ADMIN))
    request = group_msg(text, MEMBER, **extra)
    await send(env, request)
    assert api.calls("DeleteMessage")[-1].message_id == request.message.message_id
    before = len(api.calls("DeleteMessage"))
    await send(env, group_msg(text, ADMIN, **extra))
    assert len(api.calls("DeleteMessage")) == before


async def test_allowlist_boundaries_creator_clear_and_atomic_delta(env, api):
    await send(env, group_msg("/lock url", ADMIN))
    await send(env, group_msg("/allowlist trusted.example/docs", MEMBER))
    assert not (await env.extras["guard"].config(GROUP)).allowlist
    await send(env, group_msg("/allowlist trusted.example/docs", ADMIN))
    before = len(api.calls("DeleteMessage"))
    await send(env, group_msg("https://trusted.example/docs/read", MEMBER))
    assert len(api.calls("DeleteMessage")) == before
    await send(env, group_msg("https://trusted.example/docs/read https://evil.example", MEMBER))
    assert len(api.calls("DeleteMessage")) == before + 1
    await send(env, group_msg("/rmallowlistall confirm", MEMBER))
    assert (await env.extras["guard"].config(GROUP)).allowlist
    await send(env, group_msg("/rmallowlistall confirm", ADMIN))
    assert not (await env.extras["guard"].config(GROUP)).allowlist
    await send(env, group_msg("https://trusted.example/docs/read", MEMBER))
    assert len(api.calls("DeleteMessage")) == before + 2


@pytest.mark.parametrize("mode", ["kick", "ban", "mute", "tban 1h", "tmute 1h"])
async def test_lock_actions_actual_until_and_reason(env, api, mode):
    await send(env, group_msg("/lock url ### reason {" + mode + "}", ADMIN))
    await send(env, group_msg("https://evil.example", MEMBER))
    assert api.calls("DeleteMessage")
    if "mute" in mode:
        call = api.calls("RestrictChatMember")[-1]
    else:
        call = api.calls("BanChatMember")[-1]
        assert bool(api.calls("UnbanChatMember")) == (mode == "kick")
    assert call.user_id == MEMBER
    if mode.startswith("t"):
        assert 3590 <= call.until_date - utcnow().timestamp() <= 3601


async def test_lockwarns_use_existing_warning_generation_and_denied_union(env, api):
    await send(env, group_msg("/lock url", ADMIN))
    await send(env, group_msg("/lockwarns on", ADMIN))
    await env.extras["guard"].update_config(GROUP, warn_limit=20)
    await send(env, group_msg("https://evil.example", MEMBER))
    assert await env.extras["guard"].count_warns(GROUP, MEMBER) == 1
    old = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: (
        admin_member(env.bot_id, can_delete_messages=True) if m.user_id == env.bot_id else old(m)
    )
    before = len(api.calls("DeleteMessage"))
    await send(env, group_msg("https://evil.example", MEMBER))
    assert (
        len(api.calls("DeleteMessage")) == before
        and await env.extras["guard"].count_warns(GROUP, MEMBER) == 1
    )


def reaction(user=MEMBER, actor_chat=None):
    return MessageReactionUpdated(
        chat=Chat(id=GROUP, type="supergroup"),
        message_id=99,
        date=utcnow().replace(microsecond=0),
        old_reaction=[],
        new_reaction=[ReactionTypeEmoji(emoji="😀")],
        user=tg_user(user) if user else None,
        actor_chat=actor_chat,
    )


async def test_reaction_removal_real_method_and_semantic_duplicate(env, api):
    await send(env, group_msg("/lock reaction", ADMIN))
    event = reaction()
    for _ in range(2):
        await send(env, Update(update_id=group_msg("unique", MEMBER).update_id, message_reaction=event))
    assert len(api.calls("DeleteMessageReaction")) == 1
    call = api.calls("DeleteMessageReaction")[-1]
    assert (
        call.chat_id == GROUP
        and call.message_id == 99
        and call.user_id == MEMBER
        and call.actor_chat_id is None
    )
    await send(env, Update(update_id=group_msg("unique", MEMBER).update_id, message_reaction=reaction(ADMIN)))
    assert len(api.calls("DeleteMessageReaction")) == 1


async def test_outside_reaction_and_sender_channel_identity_not_fake_user(env, api):
    await send(env, group_msg("/lock outsidereaction", ADMIN))
    original = api.responses["GetChatMember"]
    original_chat = api.responses["GetChat"]
    api.responses["GetChat"] = lambda m: original_chat(m).model_copy(update={"linked_chat_id": -100101})
    api.responses["GetChatMember"] = lambda m: (
        ChatMemberLeft(user=tg_user(MEMBER)) if m.user_id == MEMBER else original(m)
    )
    await send(env, Update(update_id=group_msg("unique", MEMBER).update_id, message_reaction=reaction()))
    assert api.calls("DeleteMessageReaction")[-1].user_id == MEMBER
    await send(env, group_msg("/lock reaction", ADMIN))
    event = reaction(None, Chat(id=-10099, type="channel"))
    await send(env, Update(update_id=group_msg("unique", MEMBER).update_id, message_reaction=event))
    assert (
        api.calls("DeleteMessageReaction")[-1].actor_chat_id == -10099
        and api.calls("DeleteMessageReaction")[-1].user_id is None
    )


async def test_unsupported_server_and_anonymous_aggregate_are_explicit_failures(env, api):
    await send(env, group_msg("/lock reaction", ADMIN))
    api.responses["DeleteMessageReaction"] = TelegramBadRequest(
        method=DeleteMessageReaction(chat_id=GROUP, message_id=99, user_id=MEMBER),
        message="method not supported",
    )
    await send(env, Update(update_id=group_msg("unique", MEMBER).update_id, message_reaction=reaction()))
    aggregate = MessageReactionCountUpdated(
        chat=Chat(id=GROUP, type="supergroup"),
        message_id=99,
        date=utcnow(),
        reactions=[ReactionCount(type=ReactionTypeEmoji(emoji="😀"), total_count=2)],
    )
    await send(env, Update(update_id=group_msg("unique", MEMBER).update_id, message_reaction_count=aggregate))
    assert len(api.calls("DeleteMessageReaction")) == 1 and not api.calls("DeleteAllMessageReactions")
    async with env.sm() as session:
        rows = list(
            (
                await session.execute(select(GuardEventReceipt).where(GuardEventReceipt.bot_id == env.bot_id))
            ).scalars()
        )
    assert {r.error_code for r in rows} == {"TelegramBadRequest", "anonymous_actor_unavailable"} and all(
        r.status == "failed" for r in rows
    )


@pytest.mark.parametrize(
    "kind",
    [
        "photo",
        "video",
        "gif",
        "audio",
        "document",
        "voice",
        "videonote",
        "sticker",
        "stickeranimated",
        "stickerpremium",
        "location",
        "contact",
        "poll",
        "game",
        "emojigame",
        "checklist",
        "inline",
        "guestbot",
        "forwardstory",
        "externalreply",
        "bot",
        "anonchannel",
    ],
)
async def test_remaining_typed_fields_reach_actual_deletion(env, api, kind):
    from aiogram.types import (
        Animation,
        Audio,
        Checklist,
        ChecklistTask,
        Contact,
        Dice,
        Document,
        ExternalReplyInfo,
        File,
        Game,
        Location,
        PhotoSize,
        Poll,
        PollOption,
        Sticker,
        Story,
        Video,
        VideoNote,
        Voice,
    )

    fields = dict(file_id="file", file_unique_id="unique")
    photo = [PhotoSize(**fields, width=10, height=10)]
    origin = MessageOriginUser(date=utcnow(), sender_user=tg_user(88))
    values = {
        "photo": {"photo": photo},
        "video": {"video": Video(**fields, width=10, height=10, duration=1)},
        "gif": {"animation": Animation(**fields, width=10, height=10, duration=1)},
        "audio": {"audio": Audio(**fields, duration=1)},
        "document": {"document": Document(**fields)},
        "voice": {"voice": Voice(**fields, duration=1)},
        "videonote": {"video_note": VideoNote(**fields, length=10, duration=1)},
        "location": {"location": Location(latitude=1, longitude=1)},
        "contact": {"contact": Contact(phone_number="1234567", first_name="Person")},
        "poll": {
            "poll": Poll(
                id="poll",
                question="Question?",
                options=[PollOption(persistent_id="yes", text="Yes", voter_count=1)],
                total_voter_count=1,
                is_closed=False,
                is_anonymous=True,
                type="regular",
                allows_multiple_answers=False,
                allows_revoting=False,
                members_only=False,
            )
        },
        "game": {"game": Game(title="Game", description="Game", photo=photo)},
        "emojigame": {"dice": Dice(emoji="🎲", value=1)},
        "checklist": {"checklist": Checklist(title="Tasks", tasks=[ChecklistTask(id=1, text="Task")])},
        "inline": {"via_bot": tg_user(98).model_copy(update={"is_bot": True})},
        "guestbot": {"guest_bot_caller_user": tg_user(98)},
        "forwardstory": {"story": Story(chat=Chat(id=-10098, type="channel"), id=1)},
        "externalreply": {"external_reply": ExternalReplyInfo(origin=origin)},
        "bot": {"from_user": tg_user(MEMBER).model_copy(update={"is_bot": True})},
        "anonchannel": {"sender_chat": Chat(id=-10098, type="channel")},
    }
    for sticker_kind in ("sticker", "stickeranimated", "stickerpremium"):
        values[sticker_kind] = {
            "sticker": Sticker(
                **fields,
                type="regular",
                width=10,
                height=10,
                is_animated=sticker_kind == "stickeranimated",
                is_video=False,
                premium_animation=File(**fields) if sticker_kind == "stickerpremium" else None,
            )
        }
    await send(env, group_msg("/lock " + kind, ADMIN))
    request = group_msg("caption", MEMBER)
    request = request.model_copy(update={"message": request.message.model_copy(update=values[kind])})
    await send(env, request)
    assert api.calls("DeleteMessage")[-1].message_id == request.message.message_id


async def test_custom_emoji_exception_is_per_id_and_does_not_allow_unrelated_pack(env, api):
    from aiogram.types import Sticker

    def sticker(identifier, pack):
        return Sticker(
            file_id=identifier,
            file_unique_id=identifier,
            type="custom_emoji",
            width=10,
            height=10,
            is_animated=False,
            is_video=False,
            custom_emoji_id=identifier,
            set_name=pack,
        )

    api.responses["GetCustomEmojiStickers"] = [sticker("991", "Allowed"), sticker("992", "Other")]
    await send(env, group_msg("/lock emojicustom", ADMIN))
    await send(env, group_msg("/allowlist emojipack:Allowed", ADMIN))
    allowed_msg = group_msg(
        "😀", MEMBER, entities=[MessageEntity(type="custom_emoji", offset=0, length=2, custom_emoji_id="991")]
    )
    before = len(api.calls("DeleteMessage"))
    await send(env, allowed_msg)
    assert len(api.calls("DeleteMessage")) == before
    mixed = group_msg(
        "😀😀",
        MEMBER,
        entities=[
            MessageEntity(type="custom_emoji", offset=0, length=2, custom_emoji_id="991"),
            MessageEntity(type="custom_emoji", offset=2, length=2, custom_emoji_id="992"),
        ],
    )
    await send(env, mixed)
    assert api.calls("DeleteMessage")[-1].message_id == mixed.message.message_id


async def test_comment_only_targets_actual_linked_discussion_nonmembers(env, api):
    await send(env, group_msg("/lock comment", ADMIN))
    original = api.responses["GetChatMember"]
    api.responses["GetChatMember"] = lambda m: (
        ChatMemberLeft(user=tg_user(MEMBER)) if m.user_id == MEMBER else original(m)
    )
    await send(env, group_msg("ordinary nonmember", MEMBER))
    assert not api.calls("DeleteMessage")
    original_chat = api.responses["GetChat"]
    api.responses["GetChat"] = lambda m: original_chat(m).model_copy(update={"linked_chat_id": -10099})
    await env.redis.delete(env.keys("linked_discussion", GROUP))
    request = group_msg("discussion comment", MEMBER)
    await send(env, request)
    assert api.calls("DeleteMessage")[-1].message_id == request.message.message_id


async def test_lock_panel_alias_callbacks_toggle_canonical_current_state(env, api):
    from tests.bots.groupguard.test_groupguard import bound_callback

    await send(env, group_msg("/lock url", ADMIN))
    await send(env, group_msg("/settings", ADMIN))
    panel = api.messages[-2] if api.messages[-1].chat.id == GROUP else api.messages[-1]
    await send(env, bound_callback(f"gg:lock:{GROUP}:0:links", panel, ADMIN))
    assert not (await env.extras["guard"].config(GROUP)).locked("url")
    await send(env, bound_callback(f"gg:lock:{GROUP}:0:links", panel, ADMIN))
    assert (await env.extras["guard"].config(GROUP)).locks == ["url"]


async def test_rich_content_and_paid_media_do_not_bypass_typed_locks(env, api):
    from aiogram.types import (
        PaidMediaInfo,
        PaidMediaPhoto,
        PhotoSize,
        RichBlockParagraph,
        RichMessage,
    )

    await send(env, group_msg("/lock text photo", ADMIN))
    rich = group_msg("unused", MEMBER)
    rich = rich.model_copy(
        update={
            "message": rich.message.model_copy(
                update={
                    "text": None,
                "rich_message": RichMessage(blocks=[RichBlockParagraph(text="Actual rich text")]),
                }
            )
        }
    )
    await send(env, rich)
    assert api.calls("DeleteMessage")[-1].message_id == rich.message.message_id
    paid = group_msg("unused", MEMBER)
    paid = paid.model_copy(
        update={
            "message": paid.message.model_copy(
                update={
                    "text": None,
                    "paid_media": PaidMediaInfo(
                        star_count=1,
                        paid_media=[
                            PaidMediaPhoto(
                                photo=[
                                    PhotoSize(file_id="file", file_unique_id="unique", width=10, height=10)
                                ]
                            )
                        ],
                    ),
                }
            )
        }
    )
    await send(env, paid)
    assert api.calls("DeleteMessage")[-1].message_id == paid.message.message_id


async def test_numeric_chat_exception_uses_actual_or_observed_target_only(env,api):
    from aiogram.types import ChatInviteLink, ChatJoinRequest

    from bots.groupguard import allow_refs
    await send(env,group_msg('/lock invitelink',ADMIN))
    await send(env,group_msg('/allowlist chat:-100900',ADMIN))
    original=api.responses['GetChat']
    def chats(method):
        if method.chat_id=='@publicroom':
            return original(type('Lookup',(),{'chat_id':-100900})()).model_copy(update={'username':'publicroom'})
        return original(method)
    api.responses['GetChat']=chats
    before=len(api.calls('DeleteMessage'))
    await send(env,group_msg('https://t.me/publicroom',MEMBER))
    assert len(api.calls('DeleteMessage'))==before
    unknown=group_msg('https://t.me/+unknown',MEMBER)
    await send(env,unknown)
    assert api.calls('DeleteMessage')[-1].message_id==unknown.message.message_id
    link='https://t.me/+observed'
    invite=ChatInviteLink(invite_link=link,creator=tg_user(ADMIN),creates_join_request=True,is_primary=False,is_revoked=False)
    observed=ChatJoinRequest(chat=Chat(id=-100900,type='supergroup'),from_user=tg_user(MEMBER),user_chat_id=MEMBER,
        date=utcnow(),invite_link=invite)
    await allow_refs.remember(env,observed)
    before=len(api.calls('DeleteMessage'))
    await send(env,group_msg(link,MEMBER))
    assert len(api.calls('DeleteMessage'))==before


async def test_optional_lock_action_and_encoded_path_actual_enforcement(env,api):
    await send(env,group_msg('/lock url {tban 1h}',ADMIN))
    await send(env,group_msg('/allowlist trusted.example/docs',ADMIN))
    request=group_msg('https://trusted.example/docs/%2e%2e/admin',MEMBER)
    await send(env,request)
    assert api.calls('DeleteMessage')[-1].message_id==request.message.message_id
    assert api.calls('BanChatMember')[-1].user_id==MEMBER
