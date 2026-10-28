"""Live settings editor (typed, validated, audited)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from core.callback_data import AdminNavCb, AdminSettingCb
from core.i18n import Translate
from core.routers.admin.common import actor, admin_router, back_row, btn, markup, show
from core.sdk.context import BotContext
from core.services.settings import field_type, parse_value
from core.ui.text import esc

HINTS = {int: "adm-hint-int", float: "adm-hint-float", list: "adm-hint-list", str: "adm-hint-str"}


class SettingStates(StatesGroup):
    value = State()


def fmt(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(map(str, value)) or "—"
    if value in (None, ""):
        return "—"
    return str(value)


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "settings")
    model = ctx.module.settings_model
    groups_map = {g: [k for k in keys if k in model.model_fields] for g, keys in model.setting_groups().items()}

    def key_at(group: str, idx: int) -> str | None:
        keys = groups_map.get(group, [])
        return keys[idx] if 0 <= idx < len(keys) else None

    @router.callback_query(AdminNavCb.filter(F.tab == "settings"))
    async def settings_menu(query: CallbackQuery, t: Translate) -> None:
        rows = [[btn(f"📁 {g.title()}", AdminSettingCb(group=g).pack())] for g in groups_map]
        await show(query, t("adm-settings"), markup(*rows, back_row(t)))

    async def render_group(event: Message | CallbackQuery, group: str, t: Translate) -> None:
        stg = await ctx.settings.get()
        rows = []
        for i, k in enumerate(groups_map.get(group, [])):
            value = getattr(stg, k)
            if field_type(model, k) is bool:
                rows.append([btn(f"{'✅' if value else '❌'} {k}", AdminSettingCb(group=group, idx=i, action="toggle").pack())])
            else:
                rows.append([btn(f"✏️ {k}: {fmt(value)[:24]}", AdminSettingCb(group=group, idx=i, action="edit").pack())])
        await show(event, t("adm-settings-group", group=esc(group.title())), markup(*rows, back_row(t, "settings")))

    @router.callback_query(AdminSettingCb.filter(F.action == "view"))
    async def group_view(query: CallbackQuery, callback_data: AdminSettingCb, t: Translate) -> None:
        if callback_data.group not in groups_map:
            await query.answer(t("adm-not-found"), show_alert=True)
            return
        await render_group(query, callback_data.group, t)

    @router.callback_query(AdminSettingCb.filter(F.action == "toggle"))
    async def toggle(query: CallbackQuery, callback_data: AdminSettingCb, t: Translate) -> None:
        key = key_at(callback_data.group, callback_data.idx)
        if key is None or field_type(model, key) is not bool:
            await query.answer(t("adm-not-found"), show_alert=True)
            return
        new = not getattr(await ctx.settings.get(), key)
        await ctx.settings.set(key, new)
        await ctx.audit.record(actor(query), "setting.set", key, value=new)
        await render_group(query, callback_data.group, t)

    @router.callback_query(AdminSettingCb.filter(F.action == "edit"))
    async def edit_prompt(query: CallbackQuery, callback_data: AdminSettingCb, state: FSMContext, t: Translate) -> None:
        key = key_at(callback_data.group, callback_data.idx)
        if key is None:
            await query.answer(t("adm-not-found"), show_alert=True)
            return
        await state.set_state(SettingStates.value)
        await state.update_data(group=callback_data.group, key=key)
        current = getattr(await ctx.settings.get(), key)
        await show(
            query,
            t("adm-setting-prompt", key=esc(key), value=esc(fmt(current)), hint=t(HINTS[field_type(model, key)])),
            markup([btn(t("btn-back"), AdminSettingCb(group=callback_data.group).pack())]),
        )

    @router.message(SettingStates.value, F.text)
    async def edit_save(message: Message, state: FSMContext, t: Translate) -> None:
        data = await state.get_data()
        group, key = data.get("group", ""), data.get("key", "")
        back = markup([btn(t("btn-back"), AdminSettingCb(group=group).pack())])
        if key not in model.model_fields:
            await state.clear()
            return
        try:
            value = parse_value(model, key, message.text or "")
            await ctx.settings.set(key, value)
        except Exception as e:
            # Keep the state so the admin can simply send a corrected value.
            await message.answer(t("adm-setting-invalid", key=esc(key), error=esc(e)), reply_markup=back)
            return
        await state.clear()
        await ctx.audit.record(actor(message), "setting.set", key, value=value)
        await message.answer(t("adm-setting-saved", key=esc(key), value=esc(fmt(value))), reply_markup=back)

    return router
