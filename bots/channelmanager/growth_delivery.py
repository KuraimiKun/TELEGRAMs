"""Fresh access checks and one fenced side effect per private growth operation."""

import asyncio
from typing import Any

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)
from aiogram.methods import (
    CreateChatInviteLink,
    RefundStarPayment,
    RevokeChatInviteLink,
    SendInvoice,
    SendMessage,
)
from aiogram.types import ChatInviteLink, LabeledPrice, Message
from sqlalchemy import exists, func, select, update

from bots.channelmanager import outbox
from bots.channelmanager.content import ContentError, PostSpec
from bots.channelmanager.growth import native_manager, opted_out, seal, unseal
from bots.channelmanager.growth_specs import GROWTH_KINDS
from bots.channelmanager.members import is_member, lead_for
from bots.channelmanager.models import (
    Campaign,
    CampaignRecipient,
    Channel,
    ChannelInvoice,
    Feedback,
    GrowthAction,
    JoinRequest,
    LockedContent,
    MemberHead,
    MemberInvite,
    MemberLead,
    Operation,
)
from bots.channelmanager.permissions import AccessDenied, operator_rights
from core.db.base import affected, utcnow
from core.db.models import Bot as BotRecord
from core.db.models import BotUser


async def reveal_access(ctx, lock, user_id):
    for channel_id in [lock.channel_id, *(v["chat_id"] for v in lock.required)]:
        bot = await ctx.bot.get_chat_member(channel_id, ctx.bot_id)
        if bot.status != "administrator" or not is_member(await ctx.bot.get_chat_member(channel_id, user_id)):
            raise AccessDenied("unlock_membership")


async def mark(ctx, op, initial):
    async with ctx.sm() as session:
        from bots.channelmanager.release import operation_allowed
        if not await operation_allowed(ctx, op.kind, session=session, channel_id=op.channel_id):
            return False
        channel = await session.get(Channel, (ctx.bot_id, initial.channel_id), with_for_update=True)
        from bots.channelmanager.senders import allowed
        if channel is None or (initial.kind not in {"refund", "revoke_invite"} and (channel.status != "active" or channel.generation != op.generation or (
                initial.kind != "invoice" and not await allowed(ctx, channel.channel_id, session=session)))):
            return False
        row = await session.get(GrowthAction, (ctx.bot_id, initial.id), with_for_update=True)
        if row is None or row.operation_id != op.id or row.status != "pending":
            return False
        from bots.channelmanager.billing import limits_for, resource_allowed
        if row.kind == "reveal":
            lock = await session.get(LockedContent, (ctx.bot_id, row.resource_id), with_for_update=True)
            if lock is None or lock.channel_id != row.channel_id or not lock.active or lock.generation != row.generation or not await resource_allowed(ctx, row.channel_id, "lock", lock.id, session=session):
                return False
        elif row.kind == "campaign":
            campaign = await session.get(Campaign, (ctx.bot_id, row.resource_id), with_for_update=True)
            recipient = await session.get(CampaignRecipient, (ctx.bot_id, row.resource_id, row.user_id), with_for_update=True)
            lead = await session.get(MemberLead, (ctx.bot_id, row.channel_id, row.user_id), with_for_update=True)
            if (campaign is None or campaign.channel_id != row.channel_id or campaign.status != "queued" or campaign.generation != row.generation or
                    recipient is None or recipient.action_id != row.id or lead is None or not lead.reachable or not lead.private_interacted_at or
                    lead.opted_out or not lead.campaign_opt_in or await opted_out(session, ctx, row.channel_id, row.user_id)):
                return False
            if campaign.total > (await limits_for(ctx, row.channel_id, session=session)).campaign_recipients:
                campaign.status = "held"
                await session.commit()
                return False
            blocked = await session.get(BotUser, (ctx.bot_id, row.user_id))
            if blocked and blocked.blocked_bot:
                return False
        elif row.kind in {"invite", "revoke_invite"}:
            invite = await session.get(MemberInvite, (ctx.bot_id, row.resource_id), with_for_update=True)
            if invite is None or invite.channel_id != row.channel_id:
                return False
            if row.kind == "invite":
                request = await session.get(JoinRequest, (ctx.bot_id, invite.request_id), with_for_update=True)
                head = await session.get(MemberHead, (ctx.bot_id, row.channel_id, row.user_id))
                if request is None or head is None or head.request_id != request.id or request.status != "pending" or request.invite_epoch != invite.epoch or request.expires_at <= utcnow():
                    return False
        elif row.kind in {"invoice", "refund"}:
            invoice = await session.get(ChannelInvoice, (ctx.bot_id, row.resource_id), with_for_update=True)
            if ctx.is_child or invoice is None or invoice.channel_id != row.channel_id or invoice.payer_id != row.user_id:
                return False
            if row.kind == "invoice" and (invoice.status not in {"quoted", "prechecked"} or invoice.expires_at <= utcnow()):
                return False
            if row.kind == "refund" and (invoice.charge_id != row.payload.get("charge_id") or invoice.status != "refunding"):
                return False
        elif row.kind in {"feedback", "reply"}:
            item = await session.get(Feedback, (ctx.bot_id, row.resource_id), with_for_update=True)
            if item is None or item.channel_id != row.channel_id or item.actor_id != row.actor_id or item.status in {"erased", "replied"}:
                return False
        changed = await session.execute(update(Operation).where(*outbox.fence(ctx, op), exists().where(BotRecord.id == ctx.bot_id,
            BotRecord.active.is_(True))).values(dispatched=True))
        await session.commit()
        return affected(changed) == 1


async def finish(ctx, op, initial, status, *, code=None, delay=0, refund=False, result=None):
    async with ctx.sm() as session:
        channel = await session.get(Channel, (ctx.bot_id, initial.channel_id), with_for_update=True)
        row = await session.get(GrowthAction, (ctx.bot_id, initial.id), with_for_update=True)
        if row is None or row.operation_id != op.id:
            return
        if not await outbox.finish(ctx, op, "succeeded" if status == "skipped" else status, code=code, delay=delay,
            refund_attempt=refund, message_id=result.message_id if isinstance(result, Message) else None, session=session):
            return
        row.status, row.error_code = status, code
        if isinstance(result, Message):
            row.remote_id = result.message_id
        if row.kind == "campaign":
            recipient = await session.get(CampaignRecipient, (ctx.bot_id, row.resource_id, row.user_id))
            if recipient:
                recipient.status = status
            campaign = await session.get(Campaign, (ctx.bot_id, row.resource_id), with_for_update=True)
            count = await session.scalar(select(func.count()).select_from(CampaignRecipient).where(CampaignRecipient.bot_id == ctx.bot_id,
                CampaignRecipient.campaign_id == row.resource_id, CampaignRecipient.status.in_({"selected", "pending"})))
            if campaign and not count and campaign.status == "queued":
                campaign.status = "done"
        if row.kind == "invite":
            invite = await session.get(MemberInvite, (ctx.bot_id, row.resource_id), with_for_update=True)
            if invite:
                invite.status = "active" if status == "succeeded" else status
                if status == "succeeded":
                    from bots.channelmanager.invitations import link_hash, revoke_for
                    invite.link_hash, invite.link_enc = link_hash(result.invite_link), seal(ctx, result.invite_link)
                    request = await session.get(JoinRequest, (ctx.bot_id, invite.request_id))
                    if request and (request.status != "pending" or request.invite_epoch != invite.epoch):
                        await revoke_for(session, ctx, channel, request)
        elif row.kind == "revoke_invite":
            invite = await session.get(MemberInvite, (ctx.bot_id, row.resource_id))
            if invite:
                invite.status = "revoked" if status == "succeeded" else status
        elif row.kind in {"invoice", "refund"}:
            invoice = await session.get(ChannelInvoice, (ctx.bot_id, row.resource_id))
            if invoice:
                if row.kind == "invoice":
                    invoice.delivery_status = status
                elif status in {"failed", "uncertain"}:
                    invoice.status = "refund_" + status
        elif row.kind in {"feedback", "reply"} and status == "succeeded":
            item = await session.get(Feedback, (ctx.bot_id, row.resource_id))
            if item and item.status != "erased":
                item.status = "relayed" if row.kind == "feedback" else "replied"
        elif row.kind == "reveal" and status == "succeeded" and row.user_id and not await opted_out(session, ctx, row.channel_id, row.user_id):
            lead = await lead_for(session, ctx, row.channel_id, row.user_id)
            lead.private_interacted_at, lead.reachable = utcnow(), True
        if code == "TelegramForbiddenError" and row.user_id and row.kind in {"campaign", "reply", "reveal"}:
            lead = await session.get(MemberLead, (ctx.bot_id, row.channel_id, row.user_id))
            if lead:
                lead.reachable = False
        if row.kind in {"campaign", "reveal", "feedback", "reply"} and row.user_id and status != "pending" and await opted_out(session, ctx, row.channel_id, row.user_id):
            # Also clear an in-flight private job after a concurrent erasure/opt-out.
            import uuid
            row.payload, row.user_id, row.dedupe_key = {}, None, "erased:" + uuid.uuid4().hex
        await session.commit()


async def execute(ctx, op):
    row = None
    try:
        job = outbox.AutoJob.model_validate(op.payload)
        if op.kind not in GROWTH_KINDS or op.growth_action_id != job.action_id:
            raise ContentError("growth_scope")
        async with ctx.sm() as session:
            row = await session.get(GrowthAction, (ctx.bot_id, job.action_id))
            if row is None or row.channel_id != op.channel_id or row.operation_id != op.id or op.kind != f"growth_{row.kind}":
                raise ContentError("growth_scope")
        method: Any
        destination = row.user_id
        if row.kind == "reveal":
            async with ctx.sm() as session:
                lock = await session.get(LockedContent, (ctx.bot_id, row.resource_id))
            if lock is None or lock.channel_id != row.channel_id:
                raise ContentError("growth_scope")
            await reveal_access(ctx, lock, row.user_id)
            method = PostSpec.model_validate(lock.secret).send_method(row.user_id)
        elif row.kind == "campaign":
            await native_manager(ctx, row.channel_id, row.actor_id)
            async with ctx.sm() as session:
                campaign = await session.get(Campaign, (ctx.bot_id, row.resource_id))
            if campaign is None:
                raise ContentError("growth_scope")
            method = PostSpec.model_validate(campaign.spec).send_method(row.user_id)
        elif row.kind in {"invite", "revoke_invite"}:
            async with ctx.sm() as session:
                invite = await session.get(MemberInvite, (ctx.bot_id, row.resource_id))
                request = await session.get(JoinRequest, (ctx.bot_id, invite.request_id)) if invite else None
            if invite is None or request is None:
                raise ContentError("growth_scope")
            bot = await ctx.bot.get_chat_member(row.channel_id, ctx.bot_id)
            if bot.status != "administrator" or not getattr(bot, "can_invite_users", False):
                raise AccessDenied("invite_right")
            if row.kind == "invite":
                from bots.channelmanager.members import rights
                await rights(ctx, row.channel_id, row.actor_id)
                if request.expires_at <= utcnow():
                    raise ContentError("expired")
                method = CreateChatInviteLink(chat_id=row.channel_id, name=f"req-{request.id}", creates_join_request=True, expire_date=request.expires_at)
            else:
                link = unseal(ctx, invite.link_enc) if invite.link_enc else None
                if not link:
                    raise ContentError("invite_key_changed")
                method = RevokeChatInviteLink(chat_id=row.channel_id, invite_link=link)
            destination = row.channel_id
        elif row.kind in {"invoice", "refund"}:
            async with ctx.sm() as session:
                invoice = await session.get(ChannelInvoice, (ctx.bot_id, row.resource_id))
            if invoice is None or ctx.is_child:
                raise ContentError("control_billing_only")
            if row.kind == "invoice":
                await operator_rights(ctx, row.channel_id, row.actor_id)
                user = await ctx.users.get(invoice.payer_id)
                language = ctx.translator.resolve(user.lang if user else None)
                description = ctx.translator.get(language, "chm6-invoice-native", channel=str(row.channel_id),
                    kind=ctx.translator.get(language, f"chm6-kind-{invoice.kind}"), seconds=str(invoice.seconds))
                method = SendInvoice(chat_id=invoice.payer_id, title=invoice.spec["name"], description=description,
                    payload=f"chp_{invoice.id}", currency="XTR", provider_token="", prices=[LabeledPrice(label=invoice.spec["name"], amount=invoice.amount)])
            else:
                from bots.channelmanager.billing import is_catalog_admin
                if row.actor_id != invoice.payer_id and not is_catalog_admin(ctx, row.actor_id):
                    raise AccessDenied("refund_payer")
                method = RefundStarPayment(user_id=invoice.payer_id, telegram_payment_charge_id=invoice.charge_id)
        elif row.kind in {"feedback", "reply"}:
            await native_manager(ctx, row.channel_id, row.actor_id)
            async with ctx.sm() as session:
                item = await session.get(Feedback, (ctx.bot_id, row.resource_id))
            if item is None:
                raise ContentError("growth_scope")
            destination = row.actor_id if row.kind == "feedback" else row.user_id
            user = await ctx.users.get(destination)
            language = ctx.translator.resolve(user.lang if user else None)
            text = ctx.translator.get(language, "chm6-feedback-native", channel=str(row.channel_id), id=item.id,
                user=str(item.user_id), text=item.text) if row.kind == "feedback" else row.payload["text"]
            method = SendMessage(chat_id=destination, text=text, parse_mode=None)
        else:
            raise ContentError("growth_scope")
        try:
            delay = await outbox.reserve_budget(ctx, destination)
        except Exception:
            await finish(ctx, op, row, "pending", code="rate_store_unavailable", delay=5, refund=True)
            return
        if delay:
            await finish(ctx, op, row, "pending", code="local_rate", delay=delay, refund=True)
            return
        if not await mark(ctx, op, row):
            await finish(ctx, op, row, "cancelled", code="growth_changed")
            return
        op.dispatched = True
        result = await ctx.bot(method, request_timeout=30)
        if row.kind in {"invite", "revoke_invite"}:
            if not isinstance(result, ChatInviteLink) or result.creator.id != ctx.bot_id or (row.kind == "invite" and (result.is_revoked or not result.creates_join_request)):
                raise ValueError("invalid_invite_result")
        elif row.kind == "refund":
            if result is not True:
                raise ValueError("invalid_refund_result")
            await ctx.extras["billing"].apply_refund(row.payload["charge_id"])
        elif not isinstance(result, Message):
            raise ValueError("invalid_growth_result")
    except asyncio.CancelledError:
        raise
    except TelegramRetryAfter as exc:
        if row:
            await finish(ctx, op, row, "pending" if op.attempts < op.max_attempts else "failed", code="TelegramRetryAfter", delay=max(1, exc.retry_after))
    except (TelegramNetworkError, TelegramServerError, TimeoutError):
        if row:
            await finish(ctx, op, row, "uncertain" if op.dispatched else "failed", code="growth_unknown")
    except (ContentError, AccessDenied, TelegramBadRequest, TelegramForbiddenError) as exc:
        if row:
            await finish(ctx, op, row, "failed", code=str(exc) if isinstance(exc, ContentError) else type(exc).__name__)
    except Exception:
        if row:
            await finish(ctx, op, row, "uncertain" if op.dispatched else "failed", code="invalid_growth")
        else:
            await outbox.finish(ctx, op, "failed", code="invalid_growth")
    else:
        await finish(ctx, op, row, "succeeded", result=result)


async def reconcile(ctx, limit=100):
    async with ctx.sm() as session:
        ids = (await session.scalars(select(GrowthAction.id).join(Operation, (Operation.bot_id == GrowthAction.bot_id) &
            (Operation.id == GrowthAction.operation_id)).where(GrowthAction.bot_id == ctx.bot_id, GrowthAction.status == "pending",
                Operation.status.in_({"failed", "uncertain", "cancelled"})).limit(limit))).all()
    for action_id in ids:
        async with ctx.sm() as session:
            initial = await session.get(GrowthAction, (ctx.bot_id, action_id))
            await session.get(Channel, (ctx.bot_id, initial.channel_id), with_for_update=True)
            row = await session.get(GrowthAction, (ctx.bot_id, action_id), with_for_update=True, populate_existing=True)
            op = await session.get(Operation, (ctx.bot_id, row.operation_id))
            if row.status == "pending" and op.status in {"failed", "uncertain", "cancelled"}:
                row.status, row.error_code = op.status, op.error_code
                if row.kind == "campaign":
                    target = await session.get(CampaignRecipient, (ctx.bot_id, row.resource_id, row.user_id))
                    if target:
                        target.status = op.status
                elif row.kind == "invite":
                    target_invite = await session.get(MemberInvite, (ctx.bot_id, row.resource_id))
                    if target_invite:
                        target_invite.status = op.status
                elif row.kind == "refund":
                    invoice = await session.get(ChannelInvoice, (ctx.bot_id, row.resource_id))
                    if invoice:
                        invoice.status = "refund_" + op.status
                elif row.kind == "invoice":
                    invoice = await session.get(ChannelInvoice, (ctx.bot_id, row.resource_id))
                    if invoice:
                        invoice.delivery_status = op.status
            await session.commit()
    async with ctx.sm() as session:
        campaigns = (await session.scalars(select(Campaign).where(Campaign.bot_id == ctx.bot_id,
            Campaign.status == "queued", ~exists().where(CampaignRecipient.bot_id == Campaign.bot_id,
                CampaignRecipient.campaign_id == Campaign.id, CampaignRecipient.status.in_({"selected", "pending"})))
            .limit(limit).with_for_update(skip_locked=True))).all()
        for campaign in campaigns:
            campaign.status = "done"
        await session.commit()
