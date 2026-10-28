"""Canonical documented roster and explicit historical aliases."""

CANONICAL_LOCKS = (
    "album",
    "anonchannel",
    "audio",
    "bot",
    "button",
    "cashtag",
    "checklist",
    "cjk",
    "command",
    "comment",
    "contact",
    "cyrillic",
    "document",
    "email",
    "emoji",
    "emojicustom",
    "emojigame",
    "emojionly",
    "externalreply",
    "forward",
    "forwarduser",
    "forwardbot",
    "forwardchannel",
    "forwardstory",
    "game",
    "gif",
    "guestbot",
    "inline",
    "invitelink",
    "botlink",
    "location",
    "outsidereaction",
    "phone",
    "photo",
    "poll",
    "reaction",
    "rtl",
    "spoiler",
    "sticker",
    "stickeranimated",
    "stickerpremium",
    "text",
    "url",
    "video",
    "videonote",
    "voice",
    "zalgo",
)
LEGACY_LOCKS = {
    "links": ("url",),
    "invites": ("invitelink",),
    "forwards": ("forward",),
    "media": ("photo", "video", "document", "audio"),
    "stickers": ("sticker",),
    "gifs": ("gif",),
    "polls": ("poll",),
    "bots": ("bot",),
}
LOCK_TYPES = (*CANONICAL_LOCKS, *LEGACY_LOCKS)


def expand(types: list[str]) -> list[str]:
    expanded: list[str] = []
    for name in types:
        if name == "all":
            expanded.extend(CANONICAL_LOCKS)
        elif name in CANONICAL_LOCKS:
            expanded.append(name)
        elif name in LEGACY_LOCKS:
            expanded.extend(LEGACY_LOCKS[name])
        else:
            raise ValueError("lock_type_invalid")
    return list(dict.fromkeys(expanded))
