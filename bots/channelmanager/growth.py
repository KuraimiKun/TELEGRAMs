"""Private reveals, consented channel audiences and durable growth operation planning."""

from __future__ import annotations

import base64
import hashlib
import hmac
import uuid
from datetime import timedelta

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import delete, exists, func, select, update

from bots.channelmanager import outbox
from bots.channelmanager.content import ContentError, LinkButton, PostSpec
from bots.channelmanager.growth_specs import private_content
from bots.channelmanager.member_specs import RequiredChat
from bots.channelmanager.models import (
    Campaign,
    CampaignRecipient,
    Channel,
    Event,
    Feedback,
    GrowthAction,
    LeadPrivacy,
    LockedContent,
    MemberHead,
    MemberLead,
    Operation,
    Post,
    PostVersion,
    SubscriberMenu,
)
from bots.channelmanager.permissions import AccessDenied, operator_rights, publishing_access
from core.db.base import upsert, utcnow
from core.db.models import Bot as BotRecord
from core.db.models import BotUser


def key(ctx):
    value = ctx.platform.factory_secret_key.get_secret_value() if ctx.platform.factory_secret_key else ctx.bot.token
    return hashlib.sha256(("chm-growth-v1:" + value).encode()).digest()


def seal(ctx, value):
    return Fernet(base64.urlsafe_b64encode(key(ctx))).encrypt(value.encode()).decode()


def unseal(ctx, value):
    try:
        return Fernet(base64.urlsafe_b64encode(key(ctx))).decrypt(value.encode()).decode()
    except (InvalidToken, UnicodeDecodeError):
        return None


def signed(ctx, purpose, resource_id, generation):
    value = f"{ctx.bot_id}:{purpose}:{resource_id}:{generation}"
    return hmac.new(key(ctx), value.encode(), hashlib.sha256).hexdigest()[:20]


def lock_token(ctx, row):
    return f"chl_{row.id}_{row.link_epoch}_{signed(ctx, 'lock', row.id, row.link_epoch)}"


def privacy_hash(ctx, channel_id, user_id):
    return hashlib.sha256(f"chm-optout:{ctx.bot_id}:{channel_id}:{user_id}".encode()).hexdigest()


async def opted_out(session, ctx, channel_id, user_id):
    return await session.get(LeadPrivacy, (ctx.bot_id, privacy_hash(ctx, channel_id, user_id))) is not None


async def native_manager(ctx, channel_id, actor_id):
    rights = await operator_rights(ctx, channel_id, actor_id)
    if not rights["can_edit_messages"]:
        raise AccessDenied("growth_right")


async def enqueue(session, ctx, channel, *, kind, actor_id, key, resource_id=None, generation=1, user_id=None, payload=None, run_at=None):
    dedupe = f"growth:{key}"
    old = await session.scalar(select(GrowthAction).where(GrowthAction.bot_id == ctx.bot_id, GrowthAction.dedupe_key == dedupe))
    if old:
        return old
    row = GrowthAction(bot_id=ctx.bot_id, id=uuid.uuid4().hex, channel_id=channel.channel_id, kind=kind,
        actor_id=actor_id, user_id=user_id, resource_id=resource_id, generation=generation, payload=payload or {}, dedupe_key=dedupe)
    session.add(row)
    await session.flush()
    row.operation_id = await outbox.enqueue(session, ctx, channel, kind=f"growth_{kind}", dedupe_key=dedupe,
        payload={"action_id": row.id}, run_at=run_at, growth_action_id=row.id)
    return row


async def cancel_actions(session, ctx, ids, code):
    rows = (await session.scalars(select(Operation).where(Operation.bot_id == ctx.bot_id,
        Operation.growth_action_id.in_(ids), Operation.status.in_({"pending", "running"}), Operation.dispatched.is_(False))
        .with_for_update(skip_locked=True))).all()
    for op in rows:
        op.status, op.error_code = "cancelled", code
        action = await session.get(GrowthAction, (ctx.bot_id, op.growth_action_id))
        if action:
            action.status, action.error_code = "cancelled", code


class GrowthService:
    def __init__(self, ctx):
        self.ctx = ctx

    async def create_lock(self, channel_id, actor_id, teaser: PostSpec, secret: PostSpec, required=None):
        await publishing_access(self.ctx, channel_id, actor_id, action="create")
        secret = private_content(secret, self.ctx.bot_id, protected=True)
        self.ctx.extras["posts"].check_media(teaser)
        await self.ctx.extras["posts"].validate_buttons(teaser, actor_id)
        needs = [RequiredChat.model_validate(v) for v in required or []]
        if len(needs) > 10 or channel_id in {v.chat_id for v in needs} or len({v.chat_id for v in needs}) != len(needs):
            raise ContentError("required_chat")
        for required_chat in needs:
            for user_id in (self.ctx.bot_id, actor_id):
                member = await self.ctx.bot.get_chat_member(required_chat.chat_id, user_id)
                if member.status not in {"creator", "administrator"}:
                    raise AccessDenied("required_chat_admin")
        from bots.channelmanager.billing import limits_for
        limits = await limits_for(self.ctx, channel_id)
        username = self.ctx.username or (await self.ctx.bot.get_me()).username
        if not username:
            raise ContentError("sender_username")
        user = await self.ctx.users.get(actor_id)
        language = self.ctx.translator.resolve(user.lang if user else None)
        lock_id = uuid.uuid4().hex[:16]
        token = f"chl_{lock_id}_1_{signed(self.ctx, 'lock', lock_id, 1)}"
        public = PostSpec.model_validate({**teaser.model_dump(mode="json"), "buttons": [*teaser.model_dump(mode="json")["buttons"],
            [LinkButton(text=self.ctx.translator.get(language, "chm6-unlock"), url=f"https://t.me/{username}?start={token}").model_dump(mode="json")]]})
        async with self.ctx.sm() as session:
            await session.get(BotRecord, self.ctx.bot_id, with_for_update=True)
            channel = await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            if channel is None or channel.status != "active":
                raise AccessDenied("channel_inactive")
            count = int(await session.scalar(select(func.count()).select_from(LockedContent).where(LockedContent.bot_id == self.ctx.bot_id,
                LockedContent.channel_id == channel_id, LockedContent.active.is_(True))) or 0)
            if count >= limits.locks:
                raise ContentError("plan_limit")
            post = Post(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=channel_id, creator_id=actor_id, target_ids=[channel_id])
            session.add(post)
            await session.flush()
            session.add(PostVersion(bot_id=self.ctx.bot_id, post_id=post.id, number=1, spec=public.model_dump(mode="json")))
            row = LockedContent(bot_id=self.ctx.bot_id, id=lock_id, channel_id=channel_id, creator_id=actor_id,
                post_id=post.id, secret=secret.model_dump(mode="json"), required=[v.model_dump() for v in needs])
            session.add(row)
            session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=channel_id, actor_id=actor_id,
                action="lock.created", details={"lock_id": row.id, "post_id": post.id}))
            await session.commit()
            return row

    async def lock_for_token(self, token):
        parts = token.split("_")
        if len(parts) != 4 or parts[0] != "chl":
            raise ContentError("stale")
        async with self.ctx.sm() as session:
            row = await session.get(LockedContent, (self.ctx.bot_id, parts[1]))
        if row is None or not row.active or not hmac.compare_digest(lock_token(self.ctx, row), token):
            raise ContentError("stale")
        return row

    async def reveal(self, user_id, token, receipt_key):
        row = await self.lock_for_token(token)
        from bots.channelmanager.growth_delivery import reveal_access
        await reveal_access(self.ctx, row, user_id)
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, row.channel_id), with_for_update=True)
            current = await session.get(LockedContent, (self.ctx.bot_id, row.id), with_for_update=True)
            if not current.active or current.generation != row.generation:
                raise ContentError("stale")
            count = int(await session.scalar(select(func.count()).select_from(GrowthAction).where(GrowthAction.bot_id == self.ctx.bot_id,
                GrowthAction.kind == "reveal", GrowthAction.user_id == user_id, GrowthAction.created_at > utcnow() - timedelta(minutes=1))) or 0)
            if count >= 10:
                raise ContentError("limit")
            return await self._commit_action(session, channel, kind="reveal", actor_id=current.creator_id,
                key=f"reveal:{current.id}:{user_id}:{receipt_key}", resource_id=current.id, generation=current.generation, user_id=user_id)

    async def _commit_action(self, session, channel, **values):
        row = await enqueue(session, self.ctx, channel, **values)
        await session.commit()
        return row

    async def locks(self, channel_id, actor_id):
        await publishing_access(self.ctx, channel_id, actor_id)
        async with self.ctx.sm() as session:
            return list((await session.scalars(select(LockedContent).where(LockedContent.bot_id == self.ctx.bot_id,
                LockedContent.channel_id == channel_id).order_by(LockedContent.created_at.desc()).limit(30))).all())

    async def disable_lock(self, lock_id, actor_id):
        async with self.ctx.sm() as session:
            initial = await session.get(LockedContent, (self.ctx.bot_id, lock_id))
        if initial is None:
            raise ContentError("stale")
        await self.ctx.extras["posts"].view(initial.post_id, actor_id, "edit")
        async with self.ctx.sm() as session:
            await session.get(Channel, (self.ctx.bot_id, initial.channel_id), with_for_update=True)
            row = await session.get(LockedContent, (self.ctx.bot_id, lock_id), with_for_update=True)
            row.active, row.generation, row.link_epoch = False, row.generation + 1, row.link_epoch + 1
            await session.commit()

    async def snapshot(self, channel_id, actor_id, content: PostSpec, *, limit=None):
        await native_manager(self.ctx, channel_id, actor_id)
        content = private_content(content, self.ctx.bot_id)
        from bots.channelmanager.billing import limits_for
        cap = (await limits_for(self.ctx, channel_id)).campaign_recipients
        size = cap if limit is None else limit
        if not 1 <= size <= cap:
            raise ContentError("plan_limit")
        async with self.ctx.sm() as session:
            await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            from bots.channelmanager.senders import allowed
            if not await allowed(self.ctx, channel_id, session=session):
                raise ContentError("sender_changed")
            users = list((await session.scalars(select(MemberLead.user_id).where(MemberLead.bot_id == self.ctx.bot_id,
                MemberLead.channel_id == channel_id, MemberLead.private_interacted_at.is_not(None), MemberLead.reachable.is_(True),
                MemberLead.campaign_opt_in.is_(True), MemberLead.opted_out.is_(False), ~exists().where(BotUser.bot_id == self.ctx.bot_id,
                    BotUser.user_id == MemberLead.user_id, BotUser.blocked_bot.is_(True))).order_by(MemberLead.user_id).limit(size))).all())
            users = [u for u in users if not await opted_out(session, self.ctx, channel_id, u)]
            row = Campaign(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=channel_id, creator_id=actor_id,
                spec=content.model_dump(mode="json"), total=len(users), expires_at=utcnow() + timedelta(minutes=15))
            session.add(row)
            await session.flush()
            for user_id in users:
                session.add(CampaignRecipient(bot_id=self.ctx.bot_id, campaign_id=row.id, channel_id=channel_id, user_id=user_id))
            await session.commit()
            return row

    async def confirm(self, campaign_id, actor_id, generation):
        row = await self.campaign(campaign_id, actor_id)
        from bots.channelmanager.billing import limits_for
        if row.total > (await limits_for(self.ctx, row.channel_id)).campaign_recipients:
            raise ContentError("plan_limit")
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, row.channel_id), with_for_update=True)
            current = await session.get(Campaign, (self.ctx.bot_id, campaign_id), with_for_update=True)
            if current.generation != generation or current.expires_at <= utcnow() or current.creator_id != actor_id:
                raise ContentError("stale")
            if current.status in {"queued", "done"}:
                return current
            if current.status != "draft":
                raise ContentError("stale")
            recipients = (await session.scalars(select(CampaignRecipient).where(CampaignRecipient.bot_id == self.ctx.bot_id,
                CampaignRecipient.campaign_id == campaign_id, CampaignRecipient.status == "selected").order_by(CampaignRecipient.user_id))).all()
            for recipient in recipients:
                job = await enqueue(session, self.ctx, channel, kind="campaign", actor_id=actor_id,
                    key=f"campaign:{campaign_id}:{generation}:{recipient.user_id}", resource_id=campaign_id, generation=generation, user_id=recipient.user_id)
                recipient.status, recipient.action_id = "pending", job.id
            current.status = "queued" if recipients else "done"
            session.add(Event(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex, channel_id=row.channel_id, actor_id=actor_id,
                action="campaign.confirmed", details={"campaign_id": row.id, "recipients": len(recipients)}))
            await session.commit()
            return current

    async def campaign(self, campaign_id, actor_id):
        async with self.ctx.sm() as session:
            row = await session.get(Campaign, (self.ctx.bot_id, campaign_id))
        if row is None:
            raise ContentError("stale")
        await native_manager(self.ctx, row.channel_id, actor_id)
        return row

    async def stop_campaign(self, campaign_id, actor_id):
        initial = await self.campaign(campaign_id, actor_id)
        async with self.ctx.sm() as session:
            await session.get(Channel, (self.ctx.bot_id, initial.channel_id), with_for_update=True)
            row = await session.get(Campaign, (self.ctx.bot_id, campaign_id), with_for_update=True)
            row.status, row.generation = "cancelled", row.generation + 1
            actions = (await session.scalars(select(GrowthAction.id).where(GrowthAction.bot_id == self.ctx.bot_id,
                GrowthAction.kind == "campaign", GrowthAction.resource_id == campaign_id))).all()
            await cancel_actions(session, self.ctx, actions, "campaign_cancelled")
            await session.commit()

    async def resume_campaign(self, campaign_id, actor_id, generation):
        """Prepare a new review of the same unsent recipients; ambiguous/sent outcomes stay excluded."""
        initial = await self.campaign(campaign_id, actor_id)
        async with self.ctx.sm() as session:
            await session.get(Channel, (self.ctx.bot_id, initial.channel_id), with_for_update=True)
            row = await session.get(Campaign, (self.ctx.bot_id, campaign_id), with_for_update=True)
            if row.generation != generation or row.status not in {"cancelled", "done", "held"}:
                raise ContentError("stale")
            pending = await session.scalar(select(GrowthAction.id).where(GrowthAction.bot_id == self.ctx.bot_id,
                GrowthAction.resource_id == campaign_id, GrowthAction.kind == "campaign", GrowthAction.status == "pending").limit(1))
            if pending:
                raise ContentError("busy")
            recipients = (await session.scalars(select(CampaignRecipient).where(CampaignRecipient.bot_id == self.ctx.bot_id,
                CampaignRecipient.campaign_id == campaign_id, CampaignRecipient.status.in_({"selected", "failed", "cancelled"})))).all()
            for recipient in recipients:
                recipient.status, recipient.action_id = "selected", None
            row.status, row.creator_id, row.generation = "draft", actor_id, row.generation + 1
            row.expires_at = utcnow() + timedelta(minutes=15)
            await session.commit()
            return row

    async def campaign_report(self, campaign_id, actor_id):
        row = await self.campaign(campaign_id, actor_id)
        async with self.ctx.sm() as session:
            counts = dict((await session.execute(select(CampaignRecipient.status, func.count()).where(
                CampaignRecipient.bot_id == self.ctx.bot_id, CampaignRecipient.campaign_id == campaign_id)
                .group_by(CampaignRecipient.status))).all())
        return row, counts

    async def edit_lock(self, lock_id, actor_id, secret, generation):
        async with self.ctx.sm() as session:
            initial = await session.get(LockedContent, (self.ctx.bot_id, lock_id))
        if initial is None:
            raise ContentError("stale")
        await self.ctx.extras["posts"].view(initial.post_id, actor_id, "edit")
        secret = private_content(secret, self.ctx.bot_id, protected=True)
        async with self.ctx.sm() as session:
            await session.get(Channel, (self.ctx.bot_id, initial.channel_id), with_for_update=True)
            row = await session.get(LockedContent, (self.ctx.bot_id, lock_id), with_for_update=True)
            if row.generation != generation or not row.active:
                raise ContentError("stale")
            row.secret, row.generation = secret.model_dump(mode="json"), row.generation + 1
            await session.commit()
            return row

    async def consent(self, channel_id, user_id, *, subscribe):
        verified = False
        if subscribe:
            async with self.ctx.sm() as session:
                known = await session.get(MemberLead, (self.ctx.bot_id, channel_id, user_id)) or await session.get(MemberHead, (self.ctx.bot_id, channel_id, user_id))
            if known is None:
                from bots.channelmanager.members import is_member
                bot = await self.ctx.bot.get_chat_member(channel_id, self.ctx.bot_id)
                verified = bot.status == "administrator" and is_member(await self.ctx.bot.get_chat_member(channel_id, user_id))
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            lead = await session.get(MemberLead, (self.ctx.bot_id, channel_id, user_id), with_for_update=True)
            head = await session.get(MemberHead, (self.ctx.bot_id, channel_id, user_id))
            if channel is None or (lead is None and head is None and not verified and not await opted_out(session, self.ctx, channel_id, user_id)):
                raise ContentError("lead_scope")
            if subscribe:
                await session.execute(delete(LeadPrivacy).where(LeadPrivacy.bot_id == self.ctx.bot_id,
                    LeadPrivacy.key_hash == privacy_hash(self.ctx, channel_id, user_id)))
                from bots.channelmanager.members import lead_for
                lead = await lead_for(session, self.ctx, channel_id, user_id)
                lead.private_interacted_at, lead.reachable, lead.opted_out, lead.campaign_opt_in = utcnow(), True, False, True
            else:
                if lead:
                    lead.opted_out, lead.campaign_opt_in = True, False
                await session.execute(upsert(session, LeadPrivacy).values(bot_id=self.ctx.bot_id,
                    key_hash=privacy_hash(self.ctx, channel_id, user_id)).on_conflict_do_nothing())
            await session.commit()

    async def forget(self, channel_id, user_id):
        await self.consent(channel_id, user_id, subscribe=False)
        async with self.ctx.sm() as session:
            await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            ids = (await session.scalars(select(GrowthAction.id).where(GrowthAction.bot_id == self.ctx.bot_id,
                GrowthAction.channel_id == channel_id, GrowthAction.user_id == user_id,
                GrowthAction.kind.in_({"campaign", "reveal", "feedback", "reply"})))).all()
            await cancel_actions(session, self.ctx, ids, "lead_removed")
            await session.execute(delete(CampaignRecipient).where(CampaignRecipient.bot_id == self.ctx.bot_id,
                CampaignRecipient.channel_id == channel_id, CampaignRecipient.user_id == user_id))
            await session.execute(delete(MemberLead).where(MemberLead.bot_id == self.ctx.bot_id,
                MemberLead.channel_id == channel_id, MemberLead.user_id == user_id))
            await session.execute(update(Feedback).where(Feedback.bot_id == self.ctx.bot_id,
                Feedback.channel_id == channel_id, Feedback.user_id == user_id).values(text="[removed]", user_id=0, status="erased"))
            for job in (await session.scalars(select(GrowthAction).where(GrowthAction.bot_id == self.ctx.bot_id, GrowthAction.id.in_(ids)))).all():
                if job.status != "pending":
                    job.payload, job.user_id, job.dedupe_key = {}, None, "erased:" + uuid.uuid4().hex
            await session.commit()

    async def menu(self, channel_id, actor_id, content, *, feedback=False):
        await native_manager(self.ctx, channel_id, actor_id)
        content = private_content(content, self.ctx.bot_id)
        async with self.ctx.sm() as session:
            await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            row = await session.get(SubscriberMenu, (self.ctx.bot_id, channel_id), with_for_update=True)
            if row is None:
                row = SubscriberMenu(bot_id=self.ctx.bot_id, channel_id=channel_id, actor_id=actor_id, content=content.model_dump(mode="json"))
                session.add(row)
            else:
                row.generation += 1
            row.content, row.feedback, row.actor_id = content.model_dump(mode="json"), feedback, actor_id
            await session.commit()
            return row

    async def feedback(self, channel_id, user_id, text, receipt_key):
        from bots.channelmanager.content import utf16len
        if not text.strip() or utf16len(text) > 3500:
            raise ContentError("length")
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, channel_id), with_for_update=True)
            menu = await session.get(SubscriberMenu, (self.ctx.bot_id, channel_id))
            if channel is None or menu is None or not menu.feedback:
                raise ContentError("feedback_disabled")
            if await session.get(MemberHead, (self.ctx.bot_id, channel_id, user_id)) is None and await session.get(MemberLead, (self.ctx.bot_id, channel_id, user_id)) is None:
                raise ContentError("lead_scope")
            old = await session.scalar(select(GrowthAction).where(GrowthAction.bot_id == self.ctx.bot_id,
                GrowthAction.dedupe_key == f"growth:feedback:{channel_id}:{user_id}:{receipt_key}"))
            if old:
                return await session.get(Feedback, (self.ctx.bot_id, old.resource_id))
            row = Feedback(bot_id=self.ctx.bot_id, id=uuid.uuid4().hex[:16], channel_id=channel_id, user_id=user_id, actor_id=menu.actor_id, text=text)
            session.add(row)
            await session.flush()
            await enqueue(session, self.ctx, channel, kind="feedback", actor_id=menu.actor_id, user_id=user_id,
                key=f"feedback:{channel_id}:{user_id}:{receipt_key}", resource_id=row.id, generation=menu.generation)
            await session.commit()
            return row

    async def reply(self, feedback_id, actor_id, text):
        from bots.channelmanager.content import utf16len
        if not text.strip() or utf16len(text) > 3500:
            raise ContentError("length")
        async with self.ctx.sm() as session:
            row = await session.get(Feedback, (self.ctx.bot_id, feedback_id))
        if row is None or row.actor_id != actor_id:
            raise AccessDenied("feedback_owner")
        await native_manager(self.ctx, row.channel_id, actor_id)
        async with self.ctx.sm() as session:
            channel = await session.get(Channel, (self.ctx.bot_id, row.channel_id), with_for_update=True)
            row = await session.get(Feedback, (self.ctx.bot_id, feedback_id), with_for_update=True)
            if row.status in {"replied", "erased"}:
                raise ContentError("already_sent")
            return await self._commit_action(session, channel, kind="reply", actor_id=actor_id, user_id=row.user_id,
                key=f"reply:{feedback_id}", resource_id=row.id, payload={"text": text})
