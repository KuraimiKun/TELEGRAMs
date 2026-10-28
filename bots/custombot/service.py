"""Page tree storage with import/export."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bots.custombot.models import CbNode

COMMAND_RE = re.compile(r"^[a-z0-9_]{1,32}$")
URL_RE = re.compile(r"^(https?://|tg://)\S+$", re.IGNORECASE)
RESERVED = {"start", "admin", "build", "lang", "help", "terms", "support", "cancel"}
MAX_NODES = 150
MAX_CHILDREN = 24


class BuilderError(ValueError):
    """Invalid builder input; ``code`` maps to ``cb-err-<code>``."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class PageService:
    def __init__(self, sm: async_sessionmaker[AsyncSession], bot_id: int) -> None:
        self.sm = sm
        self.bot_id = bot_id

    async def root(self) -> CbNode:
        async with self.sm() as s:
            stmt = select(CbNode).where(CbNode.bot_id == self.bot_id, CbNode.parent_id.is_(None)).order_by(CbNode.id)
            node = (await s.execute(stmt.limit(1))).scalar_one_or_none()
            if node is None:
                node = CbNode(bot_id=self.bot_id, parent_id=None, title="Home", command="start")
                s.add(node)
                await s.commit()
            return node

    async def get(self, node_id: int) -> CbNode | None:
        async with self.sm() as s:
            node = await s.get(CbNode, node_id)
            return node if node is not None and node.bot_id == self.bot_id else None

    async def children(self, node_id: int) -> list[CbNode]:
        async with self.sm() as s:
            stmt = (
                select(CbNode)
                .where(CbNode.bot_id == self.bot_id, CbNode.parent_id == node_id)
                .order_by(CbNode.position, CbNode.id)
            )
            return list((await s.execute(stmt)).scalars())

    async def by_command(self, command: str) -> CbNode | None:
        if command == "start":
            return await self.root()
        async with self.sm() as s:
            stmt = select(CbNode).where(CbNode.bot_id == self.bot_id, CbNode.command == command.lower())
            return (await s.execute(stmt.limit(1))).scalar_one_or_none()

    async def count(self) -> int:
        async with self.sm() as s:
            stmt = select(func.count()).select_from(CbNode).where(CbNode.bot_id == self.bot_id)
            return int((await s.execute(stmt)).scalar_one())

    async def add_child(self, parent_id: int, title: str, url: str | None = None) -> CbNode:
        title = title.strip()[:64]
        if not title:
            raise BuilderError("title")
        if url is not None and not URL_RE.match(url.strip()):
            raise BuilderError("url")
        if await self.count() >= MAX_NODES:
            raise BuilderError("limit")
        siblings = await self.children(parent_id)
        if len(siblings) >= MAX_CHILDREN:
            raise BuilderError("limit")
        async with self.sm() as s:
            node = CbNode(bot_id=self.bot_id, parent_id=parent_id, title=title, position=len(siblings),
                          url=url.strip() if url else None)
            s.add(node)
            await s.commit()
            return node

    async def update(self, node_id: int, **fields: Any) -> None:
        async with self.sm() as s:
            await s.execute(update(CbNode).where(CbNode.id == node_id, CbNode.bot_id == self.bot_id).values(**fields))
            await s.commit()

    async def set_command(self, node_id: int, command: str | None) -> None:
        if command is not None:
            command = command.strip().lstrip("/").lower()
            if not COMMAND_RE.match(command) or command in RESERVED:
                raise BuilderError("command")
            existing = await self.by_command(command)
            if existing is not None and existing.id != node_id:
                raise BuilderError("command_taken")
        await self.update(node_id, command=command)

    async def delete(self, node_id: int) -> None:
        """Delete a page and everything under it (never the root)."""
        node = await self.get(node_id)
        if node is None or node.parent_id is None:
            return
        doomed, frontier = [], [node_id]
        while frontier:
            current = frontier.pop()
            doomed.append(current)
            frontier += [c.id for c in await self.children(current)]
        async with self.sm() as s:
            await s.execute(delete(CbNode).where(CbNode.bot_id == self.bot_id, CbNode.id.in_(doomed)))
            await s.commit()

    # ------------------------------------------------------------------ import / export
    async def export(self) -> dict[str, Any]:
        async def dump(node: CbNode) -> dict[str, Any]:
            data: dict[str, Any] = {"title": node.title}
            for field in ("command", "text", "media_kind", "file_id", "url"):
                if getattr(node, field):
                    data[field] = getattr(node, field)
            kids = await self.children(node.id)
            if kids:
                data["children"] = [await dump(k) for k in kids]
            return data

        return {"version": 1, "root": await dump(await self.root())}

    async def import_(self, data: dict[str, Any]) -> int:
        """Replace the whole tree. Returns the number of pages imported."""
        if not isinstance(data, dict) or not isinstance(data.get("root"), dict):
            raise BuilderError("import")
        total = 0

        def walk(node: dict[str, Any]) -> None:
            nonlocal total
            total += 1
            if total > MAX_NODES or not isinstance(node, dict):
                raise BuilderError("import")
            for child in node.get("children", []) or []:
                walk(child)

        walk(data["root"])
        async with self.sm() as s:
            await s.execute(delete(CbNode).where(CbNode.bot_id == self.bot_id))
            await s.commit()

        async def load(node: dict[str, Any], parent_id: int | None, position: int) -> None:
            command = node.get("command")
            if parent_id is None:
                command = "start"
            elif command is not None and (not COMMAND_RE.match(str(command)) or command in RESERVED):
                command = None
            url = node.get("url")
            async with self.sm() as s:
                row = CbNode(
                    bot_id=self.bot_id, parent_id=parent_id, position=position,
                    title=str(node.get("title") or "•")[:64], command=command,
                    text=str(node["text"])[:4000] if node.get("text") else None,
                    media_kind=node.get("media_kind"), file_id=node.get("file_id"),
                    url=str(url) if url and URL_RE.match(str(url)) else None,
                )
                s.add(row)
                await s.commit()
                new_id = row.id
            for i, child in enumerate(node.get("children", []) or []):
                await load(child, new_id, i)

        await load(data["root"], None, 0)
        return total
