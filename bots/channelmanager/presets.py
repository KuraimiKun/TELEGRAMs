"""Personal named sets and channel defaults, copied into immutable post versions."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from bots.channelmanager.content import ContentError, LinkButton, PostSpec
from bots.channelmanager.models import ChannelDefaults, Preset
from bots.channelmanager.permissions import AccessDenied, publishing_access
from core.db.base import upsert
from core.db.models import Bot as BotRecord
from core.sdk.context import BotContext


class PresetService:
    def __init__(self, ctx: BotContext):
        self.ctx = ctx

    async def list_for(self, user_id: int) -> list[Preset]:
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(Preset).where(Preset.bot_id == self.ctx.bot_id,
                Preset.owner_id == user_id).order_by(Preset.name).limit(100))).all())

    async def get(self, preset_id: str, user_id: int) -> Preset:
        async with self.ctx.sm() as session:
            row = await session.get(Preset, (self.ctx.bot_id, preset_id))
            if row is None or row.owner_id != user_id:
                raise AccessDenied("preset_owner")
            return row

    async def save(self, user_id: int, name: str, kind: str, value: dict, *, preset_id: str | None = None,
                   generation: int | None = None) -> Preset:
        name = name.strip()
        if not 1 <= len(name) <= 64:
            raise ContentError("content")
        if kind == "buttons":
            buttons = [[LinkButton.model_validate(b) for b in row] for row in value.get("buttons", [])]
            # Use the canonical validator, including all keyboard size limits.
            PostSpec.model_validate({"body": {"text": "validation"}, "buttons": buttons})
            for button_row in buttons:
                for b in button_row:
                    if b.required_channel:
                        await publishing_access(self.ctx, b.required_channel, user_id)
            value = {"buttons": [[b.model_dump(mode="json") for b in row] for row in buttons]}
        elif kind == "channels":
            ids = value.get("channels", [])
            if not 1 <= len(ids) <= 10 or len(set(ids)) != len(ids) or any(type(i) is not int or i >= 0 for i in ids):
                raise ContentError("targets")
            for channel_id in ids:
                await publishing_access(self.ctx, channel_id, user_id, action="create")
            value = {"channels": sorted(ids)}
        else:
            raise ContentError("content")
        async with self.ctx.sm() as session:
            await session.get(BotRecord, self.ctx.bot_id, with_for_update=True)
            row = await session.get(Preset, (self.ctx.bot_id, preset_id), with_for_update=True) if preset_id else None
            if preset_id and (row is None or row.owner_id != user_id or row.generation != generation or row.kind != kind):
                raise ContentError("stale")
            duplicate = await session.scalar(select(Preset.id).where(Preset.bot_id == self.ctx.bot_id, Preset.owner_id == user_id,
                Preset.kind == kind, Preset.name == name))
            if duplicate and (row is None or duplicate != row.id):
                raise ContentError("name")
            if row is None:
                count = await session.scalar(select(func.count()).select_from(Preset).where(
                    Preset.bot_id == self.ctx.bot_id, Preset.owner_id == user_id))
                if int(count or 0) >= (await self.ctx.settings.get()).max_presets_per_operator:
                    raise ContentError("limit")
                row = Preset(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], owner_id=user_id, kind=kind, name=name, value=value)
                session.add(row)
            else:
                row.name, row.value, row.generation = name, value, row.generation + 1
            await session.commit()
            return row

    async def delete(self, preset_id: str, user_id: int, generation: int) -> None:
        async with self.ctx.sm() as session:
            row = await session.get(Preset, (self.ctx.bot_id, preset_id), with_for_update=True)
            if row is None or row.owner_id != user_id or row.generation != generation:
                raise ContentError("stale")
            await session.delete(row)
            await session.commit()

    async def reactions(self, channel_id: int) -> list[str]:
        async with self.ctx.sm() as session:
            row = await session.get(ChannelDefaults, (self.ctx.bot_id, channel_id))
            return list(row.reactions) if row else []

    async def set_reactions(self, channel_id: int, user_id: int, labels: list[str]) -> None:
        await publishing_access(self.ctx, channel_id, user_id, action="settings")
        PostSpec.model_validate({"body": {"text": "validation"}, "reactions": labels})
        async with self.ctx.sm() as session:
            await session.execute(upsert(session, ChannelDefaults).values(bot_id=self.ctx.bot_id, channel_id=channel_id,
                reactions=labels).on_conflict_do_update(index_elements=["bot_id", "channel_id"], set_={"reactions": labels}))
            await session.commit()

    async def apply(self, preset_id: str, post_id: str, user_id: int, generation: int):
        preset = await self.get(preset_id, user_id)
        posts = self.ctx.extras["posts"]
        if preset.kind == "channels":
            return await posts.targets(post_id, user_id, generation, preset.value["channels"])
        view = await posts.view(post_id, user_id, "edit")
        values = view.spec.model_dump(mode="json")
        values["buttons"] = preset.value["buttons"]
        return await posts.edit(post_id, user_id, generation, PostSpec.model_validate(values))
