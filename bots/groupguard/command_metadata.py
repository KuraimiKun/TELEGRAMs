"""Canonical command purposes and context policy; a catalog name alone is not execution."""

from __future__ import annotations

import re
from dataclasses import dataclass

from aiogram.types import Message

DISABLEABLE = frozenset(
    {
        "adminlist",
        "antiflood",
        "approval",
        "connect",
        "fedadmins",
        "fedinfo",
        "fedsubs",
        "filters",
        "flood",
        "id",
        "info",
        "kickme",
        "locks",
        "locktypes",
        "notes",
        "rules",
        "runs",
        "saved",
        "warnings",
        "warns",
    }
)
UNRESOLVED = frozenset({"runs", "saved"})
# Group-message IDs cannot be inferred from a private reply's message ID.
GROUP_ONLY = frozenset(
    {
        "purge",
        "spurge",
        "purgefrom",
        "purgeto",
        "del",
        "delete",
        "pin",
        "unpin",
        "dban",
        "dmute",
        "dkick",
        "dwarn",
        "setactiontopic",
        "report", "admin", "admins",
    }
)
RECOVERY = frozenset(
    {"disable", "enable", "disabled", "disableable", "disableadmin", "disabledel", "disconnect"}
)


@dataclass(frozen=True, slots=True)
class CommandMeta:
    name: str
    canonical: str
    module: str
    pm: bool = True
    unsupported: bool = False


REGISTRY: dict[str, CommandMeta] = {}


def family(module: str, names: str):
    for name in names.split():
        REGISTRY[name] = CommandMeta(name, name, module, name not in GROUP_ONLY, name in UNRESOLVED)


family(
    "moderation",
    "ban tban dban sban unban mute tmute dmute smute unmute kick dkick skick kickme warn dwarn swarn warns warnings rmwarn unwarn resetwarn resetwarns setwarnlimit setwarnmode setwarntime warntime approve approval approved unapprove unapproveall reports report admin admins promote demote adminlist admincache adminerror anonadmin",
)
family(
    "messages",
    "purge spurge purgefrom purgeto del delete pin permapin unpin unpinall antichannelpin cleanlinked",
)
family("logging", "setlog unsetlog logchannel logcategories log nolog")
family("settings", "settings night lang language")
family("settings", "setlang")
family(
    "content",
    "rules setrules clearrules resetrules privaterules resetrulesbutton setrulesbutton rulesbutton save get notes clear clearall privatenotes filter filterprefix filterexact stop stopall filters button welcome setwelcome resetwelcome goodbye setgoodbye resetgoodbye cleanwelcome",
)
family(
    "captcha",
    "captcha captchamode setcaptchatext resetcaptchatext captchakick captchakicktime captcharules captchamutetime",
)
family("locks", "lock unlock locks locktypes lockwarns allowlist rmallowlist rmallowlistall")
family(
    "blocklists",
    "addblocklist blocklist rmblocklist rmblocklistall addblock rmblock unblocklist blocklistmode blocklistdelete setblocklistreason resetblocklistreason",
)
family(
    "antispam",
    "flood antiflood setflood setfloodtimer setfloodmode clearflood antiraid raidtime raidactiontime autoantiraid",
)
family("connections", "connect disconnect connection reconnect")
family("identity", "id info")
family(
    "policy",
    "disabled disableable disable enable disabledel disableadmin silentactions bot2bot bot2botskipreview runs saved",
)
family(
    "cleanup",
    "cleancommand keepcommand cleancommandtypes cleanmsg keepmsg cleanmsgtypes cleanservice nocleanservice cleanservicetypes",
)
family("topics", "setactiontopic actiontopic newtopic renametopic closetopic reopentopic deletetopic")
family("utilities", "echo say broadcast")
# Later owning phases use the same context/policy rather than their own bypassing routers.
family(
    "federations",
    "newfed renamefed delfed fedpromote feddemote feddemoteme fedreason fednotif setfedlog unsetfedlog fedinfo fedadmins chatfed myfeds joinfed leavefed quietfed fban unfban fedstat fbanstat fbanlist importfbans subfed unsubfed fedsubs",
)
family("portability", "export import reset privacy")
family("discovery", "help")

ALIASES = {
    "antiflood": "flood",
    "reconnect": "connect",
    "admins": "report",
    "admin": "report",
    "delete": "del",
    "unwarn": "rmwarn",
    "resetwarns": "resetwarn",
    "warntime": "setwarntime",
    "say": "echo",
    "addblock": "addblocklist",
    "rmblock": "rmblocklist",
    "unblocklist": "rmblocklist",
}
for alias, canonical in ALIASES.items():
    item = REGISTRY[alias]
    REGISTRY[alias] = CommandMeta(item.name, canonical, item.module, item.pm, item.unsupported)


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    name: str
    args: str
    addressed_to: str | None


def parse(message: Message) -> ParsedCommand | None:
    text = message.text or message.caption or ""
    found = re.match(r"^/([A-Za-z0-9_]{1,32})(?:@([A-Za-z0-9_]{1,32}))?(?:\s+([\s\S]*))?$", text)
    return (
        ParsedCommand(found[1].lower(), (found[3] or "").strip(), found[2].lower() if found[2] else None)
        if found
        else None
    )


def purpose(name: str, args: str = "") -> str:
    if name == "locks" and args.lower() == "list":
        return "locktypes"
    return REGISTRY[name].canonical if name in REGISTRY else name
