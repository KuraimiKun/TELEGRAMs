"""Private collaboration, growth and Stars menus with actor-bound review actions."""

import contextlib

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message, PreCheckoutQuery
from sqlalchemy import exists, select

from bots.channelmanager.billing import is_catalog_admin, limits_for
from bots.channelmanager.content import ContentError, PostSpec, from_message, parse_buttons
from bots.channelmanager.growth import lock_token, native_manager
from bots.channelmanager.growth_specs import ChannelLimits, ChannelPlanSpec, DelegateSpec
from bots.channelmanager.models import (
    BillingIncident,
    Campaign,
    Channel,
    ChannelInvoice,
    ChannelPlanVersion,
    Feedback,
    LockedContent,
    MemberHead,
    MemberLead,
    SenderBinding,
    SubscriberMenu,
    VirtualGrant,
)
from bots.channelmanager.permissions import AccessDenied, publishing_access
from bots.channelmanager.publishing_ui import btn as post_button
from bots.channelmanager.publishing_ui import kb, owner
from core.i18n import Translate
from core.ui.respond import show
from core.ui.text import esc


class GrowthInput(StatesGroup):
    value = State()


class GrowthCb(CallbackData, prefix="ch6"):
    a: str
    x: str
    g: int
    u: int


def button(text, action, resource, generation, actor):
    return InlineKeyboardButton(text=text, callback_data=GrowthCb(a=action, x=str(resource), g=generation, u=actor).pack())


def parse_plan(text):
    lines = text.strip().splitlines()
    tier, rank, days, stars = lines[1].split()
    caps = lines[2].split()
    if len(lines) != 3 or len(caps) != 8 or caps[-1] not in {"yes", "no"}:
        raise ContentError("plan")
    limits = dict(zip(["schedules", "rules", "routes", "delegates", "locks", "campaign_recipients", "invite_threshold"], map(int, caps[:-1]), strict=True))
    return ChannelPlanSpec(name=lines[0], tier=tier, rank=int(rank), days=int(days), stars=int(stars),
        limits=ChannelLimits(**limits, branded=caps[-1] == "yes"))


def build_router(ctx):
    router = Router(name=f"chm_growth_{ctx.slug}")
    router.message.filter(F.chat.type == "private")
    router.callback_query.filter(F.message.chat.type == "private")
    growth, billing, team, senders = (ctx.extras[k] for k in ["growth", "billing", "team", "senders"])

    async def fail(event, t, exc):
        await show(event, t("chm7-paused" if str(exc) == "release_stage" else "chm-error-access" if isinstance(exc, AccessDenied) else "chm6-invalid"))

    async def ask(event, state, t, field, channel=0, generation=0, resource="", **extra):
        await state.set_state(GrowthInput.value)
        await state.set_data({"actor": owner(event), "field": field, "channel": channel, "generation": generation, "resource": resource, **extra})
        await show(event, t(f"chm6-prompt-{field}"))

    async def choose(event, t, section, offset=0):
        rows = []
        channels = await ctx.extras["channelmanager"].known(owner(event), offset=offset)
        for channel in channels:
            try:
                await publishing_access(ctx, channel.channel_id, owner(event))
            except (AccessDenied, TelegramAPIError):
                continue
            rows.append([button(channel.title[:50], section, channel.channel_id, channel.generation, owner(event))])
        if len(channels) == 10:
            rows.append([button("▶", "more", section, offset + 10, owner(event))])
        if section == "plans":
            rows.append([button(t("chm6-invoices"), "invoices", "0", 0, owner(event))])
            if is_catalog_admin(ctx, owner(event)):
                rows.append([button(t("chm6-catalog"), "catalog", "0", 0, owner(event))])
        await show(event, t("chm6-choose"), kb(*rows))

    async def campaign_panel(event, campaign_id, t):
        row, counts = await growth.campaign_report(campaign_id, owner(event))
        text = t("chm6-campaign-summary", id=row.id, count=str(row.total), status=esc(row.status))
        text += "\n" + ", ".join(f"{t('chm6-result-' + k)}: {v}" for k, v in counts.items())
        rows = [[button(t("chm-btn-preview"), "cprev", row.id, row.generation, owner(event))]]
        if row.status == "draft":
            rows.append([button(t("chm6-send-campaign"), "csend", row.id, row.generation, owner(event))])
        elif row.status in {"done", "cancelled", "held"}:
            rows.append([button(t("chm6-review-unsent"), "cresume", row.id, row.generation, owner(event))])
        rows += [[button(t("btn-cancel"), "cstop", row.id, row.generation, owner(event))],
            [button(t("chm-btn-refresh"), "campaign", row.id, row.generation, owner(event))]]
        await show(event, text, kb(*rows))

    async def invoice_panel(event, invoice_id, t):
        row = await billing.invoice(invoice_id, owner(event))
        impact = await billing.impact(row.channel_id, owner(event), ChannelPlanSpec.model_validate(row.spec).limits) if row.status == "quoted" else {}
        text = t("chm6-invoice-summary", id=row.id, channel=str(row.channel_id), name=esc(row.spec["name"]),
            amount=str(row.amount), seconds=str(row.seconds), kind=esc(row.kind), status=esc(row.status), expiry=row.expires_at.isoformat())
        text += "\n" + t("chm6-invoice-delivery", status=esc(row.delivery_status))
        if impact:
            text += "\n" + t("chm6-impact", **{k: str(v) for k, v in impact.items()})
        rows = []
        if row.status == "quoted":
            rows.append([button(t("chm6-send-invoice"), "pay", row.id, 0, owner(event))])
        if row.status in {"paid", "review"} and row.charge_id:
            rows.append([button(t("chm6-refund"), "rfask", row.id, 0, owner(event))])
        await show(event, text, kb(*rows))

    async def panel(event, channel_id, section, state, t):
        actor = owner(event)
        channel = await ctx.extras["channelmanager"].get(channel_id)
        if channel is None:
            raise ContentError("stale")
        await publishing_access(ctx, channel_id, actor)
        def b(key, action, resource=channel_id, generation=channel.generation):
            return button(t(key), action, resource, generation, actor)
        text, rows = t("chm6-channel", title=esc(channel.title)), []
        if section == "team":
            for grant in await team.list(channel_id, actor):
                text += "\n" + t("chm6-delegate", user=str(grant.user_id), status=t("chm4-yes" if grant.active else "chm4-no"),
                    permissions=esc(", ".join(k for k, v in grant.permissions.items() if v)))
            rows = [[b("chm6-edit-team", "teamedit"), b("chm6-adopt", "adopt")]]
        elif section == "locked":
            for row in await growth.locks(channel_id, actor):
                rows.append([b("chm6-lock-item", "lock", row.id, row.generation)])
            rows.append([b("chm6-new-lock", "newlock")])
        elif section == "campaigns":
            await native_manager(ctx, channel_id, actor)
            async with ctx.sm() as session:
                campaigns = (await session.scalars(select(Campaign).where(Campaign.bot_id == ctx.bot_id,
                    Campaign.channel_id == channel_id).order_by(Campaign.created_at.desc()).limit(15))).all()
            rows = [[button(f"{r.id[:8]} · {r.status}", "campaign", r.id, r.generation, actor)] for r in campaigns]
            rows.append([b("chm6-new-campaign", "newcamp")])
        elif section == "plans":
            if ctx.is_child:
                async with ctx.sm() as session:
                    binding = await session.scalar(select(SenderBinding).where(SenderBinding.sender_bot_id == ctx.bot_id,
                        SenderBinding.channel_id == channel_id, SenderBinding.active.is_(True)))
                if binding and binding.control_username:
                    rows.append([InlineKeyboardButton(text=t("chm6-control-billing"), url=f"https://t.me/{binding.control_username}?start=plans")])
                await show(event, t("chm6-control-billing"), kb(*rows))
                return
            await native_manager(ctx, channel_id, actor)
            caps = await limits_for(ctx, channel_id)
            text += "\n" + t("chm6-limits", schedules=str(caps.schedules), rules=str(caps.rules), routes=str(caps.routes),
                delegates=str(caps.delegates), locks=str(caps.locks), recipients=str(caps.campaign_recipients))
            await state.set_data({"actor": actor, "plan_channel": channel_id, "plan_generation": channel.generation})
            for plan in await billing.plans():
                rows.append([button(plan.spec["name"], "plan", plan.id, channel.generation, actor)])
            if not rows:
                text += "\n" + t("chm6-no-plans")
            rows.append([b("chm6-invoices", "invoices", "0", 0)])
        elif section == "senders":
            await native_manager(ctx, channel_id, actor)
            text += "\n" + t("chm6-sender-guide")
            await state.set_data({"actor": actor, "sender_channel": channel_id, "sender_generation": channel.generation})
            rows = [[button("@" + child.username, "bindask", child.bot_id, channel.generation, actor)] for child in await senders.choices(actor)]
            rows.append([b("chm6-unbind", "unbindask")])
        elif section == "menu":
            await native_manager(ctx, channel_id, actor)
            rows = [[b("chm6-menu-edit", "menuedit"), b("chm6-feedback", "feedbacks")]]
        await show(event, text[:3900], kb(*rows))

    async def subscribers(event, t, action="subscriber"):
        actor = owner(event)
        async with ctx.sm() as session:
            channels = (await session.scalars(select(Channel).where(Channel.bot_id == ctx.bot_id,
                (exists().where(MemberLead.bot_id == ctx.bot_id, MemberLead.channel_id == Channel.channel_id, MemberLead.user_id == actor)) |
                (exists().where(MemberHead.bot_id == ctx.bot_id, MemberHead.channel_id == Channel.channel_id, MemberHead.user_id == actor)))
                .order_by(Channel.channel_id).limit(100))).all()
        await show(event, t("chm6-subscriber-choose"), kb(*[[button(c.title[:50], action, c.channel_id, 0, actor)] for c in channels]))

    @router.message(Command("team", "locked", "campaigns", "plans", "senders", "menus"))
    async def command(message: Message, state: FSMContext, command: CommandObject, t: Translate):
        await state.clear()
        await choose(message, t, "menu" if command.command == "menus" else command.command)

    @router.message(Command("subscriber", "subscribe", "unsubscribe", "forget"))
    async def subscriber_command(message: Message, state: FSMContext, command: CommandObject, t: Translate):
        await state.clear()
        await subscribers(message, t, command.command)

    @router.message(F.text.regexp(r"^/start(?:@\w+)?\s+plans$"))
    async def start_plans(message: Message, state: FSMContext, t: Translate):
        await state.clear()
        await choose(message, t, "plans")

    @router.message(F.text.regexp(r"^/start(?:@\w+)?\s+chl_"))
    async def unlock(message: Message, state: FSMContext, t: Translate):
        await state.clear()
        token = (message.text or "").split(maxsplit=1)[1].strip()
        try:
            await growth.reveal(owner(message), token, str(message.message_id))
            await show(message, t("chm6-queued"))
        except AccessDenied:
            row = await growth.lock_for_token(token)
            source = await ctx.extras["channelmanager"].get(row.channel_id)
            rows = []
            if source and source.username:
                rows.append([InlineKeyboardButton(text=source.title[:60], url=f"https://t.me/{source.username}")])
            rows += [[InlineKeyboardButton(text=t("chm5-join-required", number=str(index + 1)), url=entry["url"])]
                for index, entry in enumerate(row.required)]
            username = ctx.username or (await ctx.bot.get_me()).username
            if username:
                rows.append([InlineKeyboardButton(text=t("chm5-check"), url=f"https://t.me/{username}?start={token}")])
            text = t("chm6-unlock-required")
            if source:
                text += "\n" + t("chm6-unlock-source", title=esc(source.title))
            await show(message, text, kb(*rows))
        except (ValueError, TelegramAPIError):
            await show(message, t("chm6-unlock-required"))

    @router.pre_checkout_query()
    async def checkout(query: PreCheckoutQuery, t: Translate):
        accepted = False
        with contextlib.suppress(ValueError, AccessDenied, TelegramAPIError, TimeoutError):
            accepted = not (await ctx.settings.get()).maintenance and await billing.checkout(query)
        await query.answer(ok=accepted, error_message=None if accepted else t("chm6-checkout-denied"))

    @router.message(GrowthInput.value, ~F.text.startswith("/"))
    async def input_value(message: Message, state: FSMContext, t: Translate):
        data = await state.get_data()
        if data.get("actor") != owner(message):
            return
        c, field, text = data["channel"], data["field"], (message.text or "").strip()
        try:
            if field == "team":
                user, _, rights = text.partition(" ")
                names = [s.strip() for s in rights.split(",")]
                spec = DelegateSpec(**{k: k in names for k in DelegateSpec.model_fields}) if rights != "revoke" else DelegateSpec()
                if rights != "revoke" and set(names) - DelegateSpec.model_fields.keys():
                    raise ContentError("delegation")
                async with ctx.sm() as session:
                    old = await session.get(VirtualGrant, (ctx.bot_id, c, int(user)))
                await state.update_data(delegate=int(user), permissions=spec.model_dump(), active=rights != "revoke", grant_generation=old.generation if old else 0)
                await show(message, t("chm6-team-confirm", user=user, permissions=esc(rights)), kb(
                    [button(t("chm-btn-confirm"), "teamsave", c, data["generation"], owner(message))]))
                await state.set_state(None)
                return
            if field == "adopt":
                await team.adopt(text, owner(message))
                await show(message, t("chm6-adopted"))
            elif field == "teaser":
                await ask(message, state, t, "secret", c, data["generation"], teaser=from_message(message, ctx.bot_id).model_dump(mode="json"))
                return
            elif field == "secret":
                await ask(message, state, t, "requirements", c, data["generation"], teaser=data["teaser"], secret=from_message(message, ctx.bot_id).model_dump(mode="json"))
                return
            elif field == "requirements":
                required = [] if text == "-" else [{"chat_id": int(line.split(maxsplit=1)[0]), "url": line.split(maxsplit=1)[1]} for line in text.splitlines()]
                row = await growth.create_lock(c, owner(message), PostSpec.model_validate(data["teaser"]), PostSpec.model_validate(data["secret"]), required)
                view = await ctx.extras["posts"].view(row.post_id, owner(message))
                await show(message, t("chm6-lock-created"), kb([post_button(t("chm-btn-preview"), "view", row.post_id, view.post.generation, owner(message))]))
            elif field == "editsecret":
                await growth.edit_lock(data["resource"], owner(message), from_message(message, ctx.bot_id), data["generation"])
                await show(message, t("chm6-saved"))
            elif field == "campaign":
                row = await growth.snapshot(c, owner(message), from_message(message, ctx.bot_id))
                await campaign_panel(message, row.id, t)
            elif field == "plan":
                row = await billing.create_plan(owner(message), parse_plan(text))
                await show(message, t("chm6-plan-review", name=esc(row.spec["name"]), days=str(row.spec["days"]), stars=str(row.spec["stars"])),
                    kb([button(t("chm6-publish-plan"), "planpub", row.id, 0, owner(message))]))
            elif field == "menu":
                await ask(message, state, t, "menulinks", c, data["generation"], content=from_message(message, ctx.bot_id).model_dump(mode="json"))
                return
            elif field == "menulinks":
                content = PostSpec.model_validate({**data["content"], "buttons": parse_buttons(text) if text != "-" else []})
                await growth.menu(c, owner(message), content, feedback=True)
                await show(message, t("chm6-saved"))
            elif field == "feedback":
                await growth.feedback(c, owner(message), text, str(message.message_id))
                await show(message, t("chm6-queued"))
            elif field == "reply":
                await growth.reply(data["resource"], owner(message), text)
                await show(message, t("chm6-queued"))
            await state.clear()
        except (ValueError, AccessDenied, TelegramAPIError, IndexError) as exc:
            await fail(message, t, exc)

    @router.callback_query(GrowthCb.filter())
    async def callback(query: CallbackQuery, callback_data: GrowthCb, state: FSMContext, t: Translate):
        cb = callback_data
        if cb.u != owner(query):
            await query.answer(t("chm-denied"), show_alert=True)
            return
        try:
            if cb.a in {"team", "locked", "campaigns", "plans", "senders", "menu"}:
                await state.clear()
                await panel(query, int(cb.x), cb.a, state, t)
            elif cb.a == "more":
                if not 0 <= cb.g <= 10000:
                    raise ContentError("stale")
                await choose(query, t, cb.x, cb.g)
            elif cb.a in {"teamedit", "adopt", "newlock", "newcamp", "menuedit"}:
                channel = await ctx.extras["channelmanager"].get(int(cb.x))
                if channel is None or channel.generation != cb.g:
                    raise ContentError("stale")
                await ask(query, state, t, {"teamedit": "team", "adopt": "adopt", "newlock": "teaser", "newcamp": "campaign", "menuedit": "menu"}[cb.a], int(cb.x), cb.g)
            elif cb.a == "teamsave":
                data = await state.get_data()
                if data.get("actor") != cb.u or data.get("channel") != int(cb.x) or data.get("generation") != cb.g:
                    raise ContentError("stale")
                await team.save(int(cb.x), cb.u, data["delegate"], DelegateSpec.model_validate(data["permissions"]), generation=data["grant_generation"], active=data["active"])
                await state.clear()
                await panel(query, int(cb.x), "team", state, t)
            elif cb.a in {"lock", "lockoff", "lockedit"}:
                async with ctx.sm() as session:
                    row = await session.get(LockedContent, (ctx.bot_id, cb.x))
                if row is None or row.generation != cb.g:
                    raise ContentError("stale")
                view = await ctx.extras["posts"].view(row.post_id, cb.u, "edit" if cb.a != "lock" else "view")
                if cb.a == "lockoff":
                    await growth.disable_lock(row.id, cb.u)
                    await show(query, t("chm6-saved"))
                elif cb.a == "lockedit":
                    await ask(query, state, t, "editsecret", row.channel_id, row.generation, row.id)
                else:
                    username = ctx.username or (await ctx.bot.get_me()).username
                    await show(query, t("chm6-lock-details", id=row.id, status=t("chm4-yes" if row.active else "chm4-no"),
                        url=f"https://t.me/{username}?start={lock_token(ctx, row)}"), kb(
                            [post_button(t("chm-btn-preview"), "view", row.post_id, view.post.generation, cb.u)],
                            [button(t("chm6-secret-edit"), "lockedit", row.id, row.generation, cb.u), button(t("chm6-disable-lock"), "lockoff", row.id, row.generation, cb.u)]))
            elif cb.a in {"campaign", "cprev", "csend", "cstop", "cresume"}:
                row = await growth.campaign(cb.x, cb.u)
                if row.generation != cb.g:
                    raise ContentError("stale")
                if cb.a == "cprev":
                    await ctx.bot(PostSpec.model_validate(row.spec).send_method(cb.u, preview=True))
                elif cb.a == "csend":
                    await growth.confirm(cb.x, cb.u, cb.g)
                elif cb.a == "cstop":
                    await growth.stop_campaign(cb.x, cb.u)
                elif cb.a == "cresume":
                    await growth.resume_campaign(cb.x, cb.u, cb.g)
                await campaign_panel(query, cb.x, t)
            elif cb.a == "catalog":
                if not is_catalog_admin(ctx, cb.u):
                    raise AccessDenied("catalog_admin")
                async with ctx.sm() as session:
                    plans = (await session.scalars(select(ChannelPlanVersion).where(ChannelPlanVersion.bot_id == ctx.bot_id).order_by(ChannelPlanVersion.created_at.desc()).limit(30))).all()
                rows = [[button(f"{p.spec['name']} · {p.spec['stars']} ⭐", "plreview", p.id, 0, cb.u)] for p in plans]
                rows.append([button(t("chm6-plan-new"), "plannew", "0", 0, cb.u)])
                await show(query, t("chm6-catalog-guide"), kb(*rows))
            elif cb.a == "plannew":
                await ask(query, state, t, "plan")
            elif cb.a == "plreview":
                if not is_catalog_admin(ctx, cb.u):
                    raise AccessDenied("catalog_admin")
                async with ctx.sm() as session:
                    plan = await session.get(ChannelPlanVersion, (ctx.bot_id, cb.x))
                if plan is None:
                    raise ContentError("stale")
                spec = ChannelPlanSpec.model_validate(plan.spec)
                text = t("chm6-plan-review", name=esc(spec.name), days=str(spec.days), stars=str(spec.stars))
                text += "\n" + t("chm6-limits", schedules=str(spec.limits.schedules), rules=str(spec.limits.rules), routes=str(spec.limits.routes),
                    delegates=str(spec.limits.delegates), locks=str(spec.limits.locks), recipients=str(spec.limits.campaign_recipients))
                await show(query, text, kb([button(t("chm6-retire-plan" if plan.published else "chm6-publish-plan"),
                    "planoff" if plan.published else "planpub", plan.id, 0, cb.u)]))
            elif cb.a in {"planpub", "planoff"}:
                await billing.publish_plan(cb.u, cb.x, active=cb.a == "planpub")
                await show(query, t("chm6-saved"))
            elif cb.a in {"plan", "q"}:
                data = await state.get_data()
                if data.get("actor") != cb.u or data.get("plan_generation") != cb.g:
                    raise ContentError("stale")
                if cb.a == "plan":
                    await show(query, t("chm6-plan-kind"), kb(*[[button(t(f"chm6-{name}"), "q", cb.x + "." + name[0], cb.g, cb.u)] for name in ["renew", "upgrade", "downgrade"]]))
                else:
                    plan_id, kind = cb.x.split(".")
                    row = await billing.quote(data["plan_channel"], cb.u, plan_id, kind={"r": "renew", "u": "upgrade", "d": "downgrade"}[kind])
                    await invoice_panel(query, row.id, t)
            elif cb.a == "invoices":
                if ctx.is_child:
                    await show(query, t("chm6-control-billing"))
                    return
                async with ctx.sm() as session:
                    invoices = (await session.scalars(select(ChannelInvoice).where(ChannelInvoice.bot_id == ctx.bot_id,
                        ChannelInvoice.payer_id == cb.u).order_by(ChannelInvoice.created_at.desc()).limit(20))).all()
                    incidents = (await session.scalars(select(BillingIncident).where(BillingIncident.bot_id == ctx.bot_id,
                        BillingIncident.payer_id == cb.u, BillingIncident.status == "review").limit(10))).all()
                rows = [[button(f"{r.channel_id} · {r.amount} ⭐ · {r.status}", "iv", r.id, 0, cb.u)] for r in invoices]
                rows += [[button(t("chm6-payment-review"), "irask", r.id[:16], 0, cb.u)] for r in incidents if r.currency == "XTR"]
                text = t("chm6-invoices")
                for item in incidents:
                    if item.currency != "XTR":
                        text += "\n" + t("chm6-payment-manual", currency=esc(item.currency), amount=str(item.amount))
                await show(query, text, kb(*rows))
            elif cb.a == "iv":
                await invoice_panel(query, cb.x, t)
            elif cb.a == "pay":
                await billing.send_invoice(cb.x, cb.u)
                await show(query, t("chm6-queued"))
            elif cb.a in {"rfask", "rfdo"}:
                row = await billing.invoice(cb.x, cb.u)
                if cb.a == "rfask":
                    amount, impact = await billing.refund_preview(row.id, cb.u)
                    await state.set_data({"refund_invoice": row.id, "actor": cb.u})
                    text = t("chm6-refund-confirm", amount=str(amount)) + "\n" + t("chm6-impact", **{k: str(v) for k, v in impact.items()})
                    await show(query, text, kb([button(t("chm-btn-confirm"), "rfdo", row.id, 0, cb.u)]))
                else:
                    if await state.get_data() != {"refund_invoice": row.id, "actor": cb.u}:
                        raise ContentError("stale")
                    await billing.request_refund(row.id, cb.u)
                    await state.clear()
                    await show(query, t("chm6-queued"))
            elif cb.a in {"irask", "irdo"}:
                async with ctx.sm() as session:
                    matches = (await session.scalars(select(BillingIncident).where(BillingIncident.bot_id == ctx.bot_id,
                        BillingIncident.payer_id == cb.u, BillingIncident.id.startswith(cb.x)))).all()
                if len(matches) != 1:
                    raise ContentError("stale")
                item = matches[0]
                if cb.a == "irask":
                    await state.set_data({"refund_incident": item.id, "actor": cb.u})
                    await show(query, t("chm6-refund-confirm", amount=str(item.amount)), kb([button(t("chm-btn-confirm"), "irdo", cb.x, 0, cb.u)]))
                else:
                    if await state.get_data() != {"refund_incident": item.id, "actor": cb.u}:
                        raise ContentError("stale")
                    result = await billing.refund_incident(item.id, cb.u)
                    await state.clear()
                    await show(query, t(f"chm6-result-{result}"))
            elif cb.a in {"bindask", "binddo"}:
                data = await state.get_data()
                if data.get("actor") != cb.u or data.get("sender_generation") != cb.g:
                    raise ContentError("stale")
                if cb.a == "bindask":
                    await state.update_data(confirm_sender=int(cb.x))
                    await show(query, t("chm6-bind-confirm"), kb([button(t("chm-btn-confirm"), "binddo", cb.x, cb.g, cb.u)]))
                else:
                    if data.get("confirm_sender") != int(cb.x):
                        raise ContentError("stale")
                    channel = await ctx.extras["channelmanager"].get(data["sender_channel"])
                    if channel is None or channel.generation != cb.g:
                        raise ContentError("stale")
                    await senders.bind(data["sender_channel"], cb.u, int(cb.x))
                    await state.clear()
                    await show(query, t("chm6-saved"))
            elif cb.a in {"unbindask", "unbinddo"}:
                if cb.a == "unbindask":
                    await state.set_data({"unbind": int(cb.x), "actor": cb.u})
                    await show(query, t("chm6-unbind-confirm"), kb([button(t("chm-btn-confirm"), "unbinddo", cb.x, cb.g, cb.u)]))
                else:
                    if await state.get_data() != {"unbind": int(cb.x), "actor": cb.u}:
                        raise ContentError("stale")
                    await senders.unbind(int(cb.x), cb.u)
                    await state.clear()
                    await show(query, t("chm6-saved"))
            elif cb.a in {"subscriber", "subscribe", "unsubscribe", "forget", "forgetdo", "fbnew"}:
                c = int(cb.x)
                if cb.a in {"subscribe", "unsubscribe"}:
                    await growth.consent(c, cb.u, subscribe=cb.a == "subscribe")
                    await show(query, t("chm6-subscribed" if cb.a == "subscribe" else "chm6-unsubscribed"))
                elif cb.a == "forget":
                    await state.set_data({"forget": c, "actor": cb.u})
                    await show(query, t("chm6-forget-confirm"), kb([button(t("chm-btn-confirm"), "forgetdo", c, 0, cb.u)]))
                elif cb.a == "forgetdo":
                    if await state.get_data() != {"forget": c, "actor": cb.u}:
                        raise ContentError("stale")
                    await growth.forget(c, cb.u)
                    await state.clear()
                    await show(query, t("chm6-forgotten"))
                else:
                    async with ctx.sm() as session:
                        lead = await session.get(MemberLead, (ctx.bot_id, c, cb.u))
                        head = await session.get(MemberHead, (ctx.bot_id, c, cb.u))
                        menu = await session.get(SubscriberMenu, (ctx.bot_id, c))
                    if (lead is None and head is None) or menu is None:
                        raise ContentError("lead_scope")
                    if cb.a == "fbnew":
                        await ask(query, state, t, "feedback", c)
                    else:
                        from bots.channelmanager.senders import allowed
                        async with ctx.sm() as session:
                            if not await allowed(ctx, c, session=session):
                                raise ContentError("sender_changed")
                        await ctx.bot(PostSpec.model_validate(menu.content).send_method(cb.u))
                        rows = [[button(t("chm6-subscribe"), "subscribe", c, 0, cb.u), button(t("chm6-unsubscribe"), "unsubscribe", c, 0, cb.u)]]
                        if menu.feedback:
                            rows.append([button(t("chm6-feedback"), "fbnew", c, 0, cb.u)])
                        await show(query, t("chm6-subscriber-actions"), kb(*rows))
            elif cb.a == "feedbacks":
                await native_manager(ctx, int(cb.x), cb.u)
                async with ctx.sm() as session:
                    items = (await session.scalars(select(Feedback).where(Feedback.bot_id == ctx.bot_id,
                        Feedback.channel_id == int(cb.x), Feedback.actor_id == cb.u, Feedback.status != "erased")
                        .order_by(Feedback.created_at.desc()).limit(15))).all()
                await show(query, t("chm6-feedback"), kb(*[[button(f"{item.user_id} · {item.status}", "fbview", item.id, 0, cb.u)] for item in items]))
            elif cb.a in {"fbview", "fbreply"}:
                async with ctx.sm() as session:
                    item = await session.get(Feedback, (ctx.bot_id, cb.x))
                if item is None or item.actor_id != cb.u or item.status == "erased":
                    raise AccessDenied("feedback_owner")
                await native_manager(ctx, item.channel_id, cb.u)
                if cb.a == "fbreply":
                    await ask(query, state, t, "reply", item.channel_id, resource=item.id)
                else:
                    await show(query, esc(item.text), kb([button(t("chm6-reply"), "fbreply", item.id, 0, cb.u)]))
            else:
                raise ContentError("stale")
        except (ValueError, AccessDenied, TelegramAPIError, KeyError, IndexError) as exc:
            await fail(query, t, exc)

    @router.callback_query(F.data.startswith("ch6:"))
    async def malformed(query: CallbackQuery, t: Translate):
        await query.answer(t("chm-denied"), show_alert=True)

    return router
