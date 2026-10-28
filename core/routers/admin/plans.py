"""VIP plan management: list, add, edit, enable/disable, delete (global plans: super-admins only)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from core.callback_data import AdminNavCb, AdminPlanCb
from core.db.models import Plan
from core.i18n import Translate
from core.routers.admin.common import actor, admin_router, back_row, btn, markup, show
from core.sdk.context import BotContext
from core.services.subscriptions import PlanError
from core.ui.text import esc


class PlanStates(StatesGroup):
    edit = State()


def parse_plan(text: str) -> tuple[str, int, int]:
    """'Name | days | stars' -> (name, days, stars)."""
    parts = [p.strip() for p in text.split("|")]
    if len(parts) != 3:
        raise PlanError("format: Name | days | stars")
    try:
        return parts[0], int(parts[1]), int(parts[2])
    except ValueError as e:
        raise PlanError("days and stars must be whole numbers") from e


def build_router(ctx: BotContext) -> Router:
    router = admin_router(ctx, "plans")

    def label(p: Plan) -> str:
        state = "🟢" if p.active else "⚪"
        scope = "🌐 " if p.bot_id is None else ""
        return f"{state} {scope}{p.name} · {p.days}d · {p.stars}⭐"

    @router.callback_query(AdminNavCb.filter(F.tab == "plans"))
    async def plans_list(query: CallbackQuery, t: Translate) -> None:
        plans = await ctx.subs.list_plans()
        rows = [[btn(label(p), AdminPlanCb(action="view", plan_id=p.id).pack())] for p in plans]
        await show(
            query,
            t("adm-plans"),
            markup(*rows, [btn(t("btn-adm-plan-add"), AdminPlanCb(action="add").pack())], back_row(t)),
        )

    async def render_plan(event: Message | CallbackQuery, plan: Plan, t: Translate) -> None:
        def cb(action: str) -> str:
            return AdminPlanCb(action=action, plan_id=plan.id).pack()

        text = t(
            "adm-plan-card",
            name=esc(plan.name),
            scope=t("adm-plan-global") if plan.bot_id is None else "",
            days=plan.days,
            stars=plan.stars,
            state=t("state-on") if plan.active else t("state-off"),
        )
        await show(
            event,
            text,
            markup(
                [btn(t("btn-adm-plan-edit"), cb("edit")), btn(t("btn-adm-plan-toggle"), cb("toggle"))],
                [btn(t("btn-adm-plan-delete"), cb("delete"))],
                back_row(t, "plans"),
            ),
        )

    @router.callback_query(AdminPlanCb.filter(F.action == "view"))
    async def plan_view(query: CallbackQuery, callback_data: AdminPlanCb, t: Translate) -> None:
        plan = await ctx.subs.get_plan(callback_data.plan_id)
        if plan is None:
            await query.answer(t("adm-not-found"), show_alert=True)
            return
        await render_plan(query, plan, t)

    @router.callback_query(AdminPlanCb.filter(F.action.in_({"add", "edit"})))
    async def plan_prompt(query: CallbackQuery, callback_data: AdminPlanCb, state: FSMContext, t: Translate) -> None:
        await state.set_state(PlanStates.edit)
        await state.update_data(plan_id=callback_data.plan_id if callback_data.action == "edit" else 0)
        await show(query, t("adm-plan-prompt"), markup(back_row(t, "plans")))

    @router.message(PlanStates.edit, F.text)
    async def plan_save(message: Message, state: FSMContext, t: Translate) -> None:
        data = await state.get_data()
        plan_id = int(data.get("plan_id") or 0) or None
        try:
            name, days, stars = parse_plan(message.text or "")
            existing = await ctx.subs.get_plan(plan_id) if plan_id else None
            plan = await ctx.subs.add_or_update_plan(
                plan_id,
                name,
                days,
                stars,
                active=existing.active if existing else True,
                sort=existing.sort if existing else 0,
                allow_global=ctx.is_super_admin(actor(message)),
            )
        except (PlanError, Exception) as e:
            await message.answer(t("adm-error", error=esc(e)), reply_markup=markup(back_row(t, "plans")))
            return
        await state.clear()
        await ctx.audit.record(actor(message), "plan.save", plan.id, name=name, days=days, stars=stars)
        await render_plan(message, plan, t)

    @router.callback_query(AdminPlanCb.filter(F.action.in_({"toggle", "delete"})))
    async def plan_change(query: CallbackQuery, callback_data: AdminPlanCb, t: Translate) -> None:
        allow_global = ctx.is_super_admin(actor(query))
        plan = await ctx.subs.get_plan(callback_data.plan_id)
        if plan is None:
            await query.answer(t("adm-not-found"), show_alert=True)
            return
        try:
            if callback_data.action == "toggle":
                plan = await ctx.subs.set_plan_active(plan.id, not plan.active, allow_global=allow_global)
                await ctx.audit.record(actor(query), "plan.toggle", plan.id, active=plan.active)
                await render_plan(query, plan, t)
            else:
                await ctx.subs.delete_plan(plan.id, allow_global=allow_global)
                await ctx.audit.record(actor(query), "plan.delete", plan.id, name=plan.name)
                await query.answer(t("adm-plan-deleted"))
                await plans_list(query, t)
        except PlanError as e:
            await query.answer(str(e), show_alert=True)

    return router
