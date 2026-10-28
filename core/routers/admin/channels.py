"""Required (force-subscribe) channels: add with verification, test, enable/disable, remove."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from core.callback_data import AdminChannelCb, AdminNavCb
from core.db.models import ForceSubChannel
from core.i18n import Translate
from core.routers.admin.common import actor, admin_router, back_row, btn, markup, show
from core.sdk.context import BotContext
from core.ui.text import esc

ADMIN_STATUSES = {"administrator", "creator"}


class ChannelStates(StatesGroup):
    add = State()


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "channels")

    async def verify(chat_ref: str | int) -> tuple[int, str, str]:
        """Resolve a channel and make sure the bot is an admin there. Returns (chat_id, title, invite_link)."""
        chat = await ctx.bot.get_chat(chat_ref)
        me = await ctx.bot.get_chat_member(chat.id, ctx.bot_id)
        if me.status not in ADMIN_STATUSES:
            raise PermissionError("not admin")
        link = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else "")
        if not link:
            link = (await ctx.bot.create_chat_invite_link(chat.id, name="force-sub")).invite_link
        return chat.id, chat.title or str(chat.id), link

    @router.callback_query(AdminNavCb.filter(F.tab == "channels"))
    async def channels_list(query: CallbackQuery, t: Translate) -> None:
        stg = await ctx.settings.get()
        channels = await ctx.groups.list_channels(include_inactive=True)
        rows = [
            [btn(f"{'🟢' if ch.active else '⚪'} {ch.title[:40]}", AdminChannelCb(action="view", chat_id=ch.chat_id).pack())]
            for ch in channels
        ]
        await show(
            query,
            t("adm-channels", state=t("state-on") if stg.force_sub_enabled else t("state-off")),
            markup(*rows, [btn(t("btn-adm-channel-add"), AdminChannelCb(action="add").pack())], back_row(t)),
        )

    async def render(event: Message | CallbackQuery, ch: ForceSubChannel, t: Translate) -> None:
        def cb(action: str) -> str:
            return AdminChannelCb(action=action, chat_id=ch.chat_id).pack()

        await show(
            event,
            t(
                "adm-channel-card",
                title=esc(ch.title),
                id=ch.chat_id,
                link=esc(ch.invite_link),
                state=t("state-on") if ch.active else t("state-off"),
            ),
            markup(
                [btn(t("btn-adm-channel-test"), cb("test")), btn(t("btn-adm-channel-toggle"), cb("toggle"))],
                [btn(t("btn-adm-channel-delete"), cb("delete"))],
                back_row(t, "channels"),
            ),
        )

    async def find(chat_id: int) -> ForceSubChannel | None:
        return next((c for c in await ctx.groups.list_channels(include_inactive=True) if c.chat_id == chat_id), None)

    @router.callback_query(AdminChannelCb.filter(F.action == "view"))
    async def channel_view(query: CallbackQuery, callback_data: AdminChannelCb, t: Translate) -> None:
        ch = await find(callback_data.chat_id)
        if ch is None:
            await query.answer(t("adm-not-found"), show_alert=True)
            return
        await render(query, ch, t)

    @router.callback_query(AdminChannelCb.filter(F.action == "add"))
    async def channel_prompt(query: CallbackQuery, state: FSMContext, t: Translate) -> None:
        await state.set_state(ChannelStates.add)
        await show(query, t("adm-channel-prompt"), markup(back_row(t, "channels")))

    @router.message(ChannelStates.add)
    async def channel_add(message: Message, state: FSMContext, t: Translate) -> None:
        origin = message.forward_origin
        chat_ref: str | int | None = None
        if origin is not None and getattr(origin, "chat", None) is not None:
            chat_ref = origin.chat.id  # type: ignore[union-attr]
        else:
            words = (message.text or "").split()
            if words:
                chat_ref = int(words[0]) if words[0].lstrip("-").isdigit() else words[0]
        if chat_ref is None:
            await message.answer(t("adm-channel-prompt"), reply_markup=markup(back_row(t, "channels")))
            return
        try:
            chat_id, title, link = await verify(chat_ref)
        except PermissionError:
            await message.answer(t("adm-channel-not-admin"), reply_markup=markup(back_row(t, "channels")))
            return
        except Exception as e:
            await message.answer(t("adm-channel-bad", error=esc(e)), reply_markup=markup(back_row(t, "channels")))
            return
        await state.clear()
        ch = await ctx.groups.add_channel(chat_id, title, link)
        await ctx.audit.record(actor(message), "channel.add", chat_id, title=title)
        await message.answer(t("adm-channel-added", title=esc(title)))
        await render(message, ch, t)

    @router.callback_query(AdminChannelCb.filter(F.action.in_({"test", "toggle", "delete"})))
    async def channel_change(query: CallbackQuery, callback_data: AdminChannelCb, t: Translate) -> None:
        chat_id = callback_data.chat_id
        if callback_data.action == "test":
            try:
                await verify(chat_id)
                await query.answer(t("adm-channel-ok"), show_alert=True)
            except PermissionError:
                await query.answer(t("adm-channel-not-admin"), show_alert=True)
            except Exception as e:
                await query.answer(t("adm-channel-bad", error=str(e)[:150]), show_alert=True)
            return
        if callback_data.action == "toggle":
            state = await ctx.groups.toggle_channel(chat_id)
            await ctx.audit.record(actor(query), "channel.toggle", chat_id, active=state)
            ch = await find(chat_id)
            if ch:
                await render(query, ch, t)
            return
        await ctx.groups.delete_channel(chat_id)
        await ctx.audit.record(actor(query), "channel.delete", chat_id)
        await channels_list(query, t)

    return router
