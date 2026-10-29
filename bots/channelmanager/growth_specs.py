"""Typed collaboration, private content and channel plan contracts."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bots.channelmanager.content import ContentError, PostSpec

GROWTH_KINDS = frozenset(f"growth_{kind}" for kind in {"reveal", "campaign", "invite", "revoke_invite", "invoice", "refund", "feedback", "reply"})
GROWTH_CLEANUP = frozenset({"growth_revoke_invite", "growth_refund"})


class DelegateSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    create: bool = True
    edit_own: bool = True
    edit_all: bool = False
    delete_own: bool = True
    delete_all: bool = False
    schedules: bool = False
    settings: bool = False

    @model_validator(mode="after")
    def valid(self):
        if not any(self.model_dump().values()):
            raise ContentError("delegation_empty")
        return self


class ChannelLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schedules: int = Field(default=20, ge=0, le=10000)
    rules: int = Field(default=25, ge=0, le=100)
    routes: int = Field(default=25, ge=0, le=100)
    delegates: int = Field(default=3, ge=0, le=100)
    locks: int = Field(default=10, ge=0, le=1000)
    campaign_recipients: int = Field(default=1000, ge=0, le=100000)
    invite_threshold: int = Field(default=10, ge=0, le=100)
    branded: bool = True


class ChannelPlanSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=32)
    tier: str = Field(min_length=1, max_length=32, pattern=r"^[a-z][a-z0-9_]*$")
    rank: int = Field(ge=1, le=1000)
    days: int = Field(ge=1, le=365)
    stars: int = Field(ge=1, le=1000000)
    limits: ChannelLimits = Field(default_factory=ChannelLimits)


def private_content(spec: PostSpec, bot_id: int, *, protected=False) -> PostSpec:
    if spec.media_bot_id not in {None, bot_id} or spec.pin or spec.reply_message_id or spec.delete_after_seconds or spec.reactions:
        raise ContentError("private_content")
    if any(b.kind not in {"link", "copy"} for row in spec.buttons for b in row):
        raise ContentError("private_content")
    return PostSpec.model_validate({**spec.model_dump(mode="json"), "protected": protected or spec.protected})
