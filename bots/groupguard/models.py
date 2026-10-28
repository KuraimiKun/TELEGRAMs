"""Group Guard tables. Every row carries ``bot_id``: user-created copies of the bot share them."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base, BigInt, JsonType, TZDateTime, utcnow


class GuardChat(Base):
    """One protected group and its configuration (see ``chatconfig.ChatConfig``)."""

    __tablename__ = "gg_chats"
    __table_args__ = (Index("ix_gg_chats_night", "bot_id", "night"),)

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=False)
    title: Mapped[str | None] = mapped_column(String(256))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    # Denormalised from config so the night-mode job can find its chats with an index.
    night: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    config: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow, onupdate=utcnow)


class GuardConnection(Base):
    """One current group plus last-five convenience history; neither grants permissions."""
    __tablename__ = "gg_connections"
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    chat_id: Mapped[int | None] = mapped_column(BigInt)
    history: Mapped[list[int]] = mapped_column(JsonType, default=list)
    revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardBroadcast(Base):
    """An operator's group-only campaign, scoped separately from core user broadcasts."""
    __tablename__ = "gg_broadcasts"
    __table_args__ = (Index("ix_gg_broadcasts_active", "bot_id", "status", "id"),)
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer,"sqlite"),primary_key=True)
    bot_id: Mapped[int] = mapped_column(BigInt,ForeignKey("bots.id",ondelete="CASCADE"))
    author_id: Mapped[int] = mapped_column(BigInt)
    content: Mapped[dict[str,Any]] = mapped_column(JsonType)
    subject: Mapped[dict[str,Any]] = mapped_column(JsonType)
    status: Mapped[str] = mapped_column(String(16))
    cursor: Mapped[int] = mapped_column(BigInt,default=-(2**63))
    expanded: Mapped[bool] = mapped_column(Boolean,default=False)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(),default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(),default=utcnow)


class GuardRaid(Base):
    """An activation's frozen policy and deadline, independent from configured defaults."""
    __tablename__ = "gg_raids"
    __table_args__ = (Index("ix_gg_raids_due", "bot_id", "status", "deadline"),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    generation: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16))
    deadline: Mapped[datetime] = mapped_column(TZDateTime())
    ban_seconds: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardSweep(Base):
    """Persistent bounded keyset progress, including bot factory discovery."""
    __tablename__ = "gg_sweeps"
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), primary_key=True)
    scope_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    last_id: Mapped[int] = mapped_column(BigInt)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardWarn(Base):
    __tablename__ = "gg_warns"
    __table_args__ = (Index("ix_gg_warns_member", "bot_id", "chat_id", "user_id"), {"sqlite_autoincrement": True})

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"))
    chat_id: Mapped[int] = mapped_column(BigInt)
    user_id: Mapped[int] = mapped_column(BigInt)
    reason: Mapped[str | None] = mapped_column(String(256))
    by_id: Mapped[int | None] = mapped_column(BigInt)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(TZDateTime())


class GuardItem(Base):
    """A saved note (``#name`` / ``/get name``) or a keyword filter (auto-reply)."""

    __tablename__ = "gg_items"
    __table_args__ = (UniqueConstraint("bot_id", "chat_id", "kind", "key", name="uq_gg_items_key"),
                      UniqueConstraint("bot_id", "chat_id", "id", name="uq_gg_items_scope_id"))

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"))
    chat_id: Mapped[int] = mapped_column(BigInt)
    kind: Mapped[str] = mapped_column(String(8))  # note | filter
    key: Mapped[str] = mapped_column(String(64))
    text: Mapped[str | None] = mapped_column(Text)  # HTML
    media_kind: Mapped[str | None] = mapped_column(String(16))  # photo | video | animation | document | sticker | ...
    file_id: Mapped[str | None] = mapped_column(String(256))
    content_format: Mapped[str] = mapped_column("format", String(8), default="html", server_default="html")
    options: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict, server_default=sql_text("'{}'"))
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardRepeat(Base):
    __tablename__ = "gg_repeats"
    __table_args__ = (Index("ix_gg_repeats_due", "bot_id", "status", "next_run"),
        ForeignKeyConstraint(["bot_id", "chat_id", "item_id"], ["gg_items.bot_id", "gg_items.chat_id", "gg_items.id"],
                             ondelete="CASCADE"))
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    item_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    generation: Mapped[str] = mapped_column(String(32))
    author_id: Mapped[int] = mapped_column(BigInt)
    interval_seconds: Mapped[int] = mapped_column(Integer)
    next_run: Mapped[datetime] = mapped_column(TZDateTime())
    status: Mapped[str] = mapped_column(String(16), default="active")
    thread_id: Mapped[int | None] = mapped_column(Integer)


class GuardMember(Base):
    """A scoped serialization point and minimal observed member state."""
    __tablename__ = "gg_members"
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    warning_generation: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    warning_job: Mapped[str | None] = mapped_column(String(32))
    verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(256))
    last_seen: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardApproval(Base):
    __tablename__ = "gg_approvals"
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    reason: Mapped[str | None] = mapped_column(String(256))
    by_id: Mapped[int | None] = mapped_column(BigInt)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardChallenge(Base):
    __tablename__ = "gg_challenges"
    __table_args__ = (Index("ix_gg_challenges_due", "bot_id", "status", "deadline"),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    generation: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    message_id: Mapped[int] = mapped_column(BigInt)
    message_chat_id: Mapped[int] = mapped_column(BigInt)
    thread_id: Mapped[int | None] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(String(16))
    prompt: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict, server_default=sql_text("'{}'"))
    progress: Mapped[str] = mapped_column(String(8), default="", server_default="")
    question_solved: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    rules_accepted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    answer: Mapped[str] = mapped_column(String(64))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    deadline: Mapped[datetime] = mapped_column(TZDateTime())
    policy: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    request_contact_id: Mapped[int | None] = mapped_column(BigInt)
    contact_deadline: Mapped[datetime | None] = mapped_column(TZDateTime())
    claim_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardJoinReceipt(Base):
    """Bounded semantic join delivery receipts, including interrupted uncertainty."""
    __tablename__ = "gg_join_receipts"
    __table_args__ = (Index("ix_gg_join_receipts_retention", "bot_id", "created_at"),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), default="processing")
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardEventReceipt(Base):
    __tablename__ = "gg_event_receipts"
    __table_args__ = (Index("ix_gg_event_receipts_retention", "bot_id", "created_at"),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInt)
    actor_chat_id: Mapped[int | None] = mapped_column(BigInt)
    status: Mapped[str] = mapped_column(String(16), default="processing")
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardRestriction(Base):
    __tablename__ = "gg_restrictions"
    __table_args__ = (Index("ix_gg_restrictions_expiry", "bot_id", "until"),
                      Index("ix_gg_restrictions_recovery", "bot_id", "state", "updated_at"))
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    source: Mapped[str] = mapped_column(String(96), primary_key=True)
    mode: Mapped[str] = mapped_column(String(16))
    state: Mapped[str] = mapped_column(String(16), default="applied", server_default="applied")
    generation: Mapped[str | None] = mapped_column(String(32))
    until: Mapped[datetime | None] = mapped_column(TZDateTime())
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardNight(Base):
    __tablename__ = "gg_night_state"
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    generation: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16))
    window_key: Mapped[str | None] = mapped_column(String(96))
    snapshot: Mapped[dict[str, Any]] = mapped_column(JsonType)
    closed_permissions: Mapped[dict[str, Any]] = mapped_column(JsonType)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardJob(Base):
    __tablename__ = "gg_jobs"
    __table_args__ = (UniqueConstraint("bot_id", "dedupe_key", name="uq_gg_jobs_dedupe"),
                      Index("ix_gg_jobs_due", "bot_id", "status", "run_at"))
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"))
    chat_id: Mapped[int] = mapped_column(BigInt)
    user_id: Mapped[int | None] = mapped_column(BigInt)
    kind: Mapped[str] = mapped_column(String(32))
    dedupe_key: Mapped[str] = mapped_column(String(160))
    generation: Mapped[str | None] = mapped_column(String(32))
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    run_at: Mapped[datetime] = mapped_column(TZDateTime())
    lease_until: Mapped[datetime | None] = mapped_column(TZDateTime())
    lease_owner: Mapped[str | None] = mapped_column(String(32))
    dispatched: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardInbox(Base):
    __tablename__ = "gg_inbox"
    __table_args__ = (Index("ix_gg_inbox_recovery", "bot_id", "status", "lease_until"),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    update_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType)
    status: Mapped[str] = mapped_column(String(16), default="received")
    lease_until: Mapped[datetime | None] = mapped_column(TZDateTime())
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    error_code: Mapped[str | None] = mapped_column(String(64))


class GuardMessage(Base):
    __tablename__ = "gg_messages"
    __table_args__ = (Index("ix_gg_messages_observed", "bot_id", "chat_id", "user_id"),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    message_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInt)
    content_version: Mapped[str] = mapped_column(String(64))
    counted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardFederation(Base):
    __tablename__ = 'gg_federations'
    __table_args__ = (UniqueConstraint('bot_id', 'owner_id', name='uq_gg_federations_owner'),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey('bots.id', ondelete='CASCADE'), primary_key=True)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInt)
    name: Mapped[str] = mapped_column(String(64))
    reason_required: Mapped[bool] = mapped_column(Boolean, default=False)
    notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    log_chat_id: Mapped[int | None] = mapped_column(BigInt)
    revision: Mapped[int] = mapped_column(Integer, default=0, server_default='0')
    graph_generation: Mapped[int] = mapped_column(Integer, default=0, server_default='0')
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardFedAdmin(Base):
    __tablename__ = 'gg_fed_admins'
    __table_args__ = (ForeignKeyConstraint(['bot_id', 'fed_id'], ['gg_federations.bot_id', 'gg_federations.id'],
        ondelete='CASCADE'), Index('ix_gg_fed_admins_user', 'bot_id', 'user_id', 'fed_id'))
    bot_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    fed_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    by_id: Mapped[int] = mapped_column(BigInt)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardFedChat(Base):
    __tablename__ = 'gg_fed_chats'
    __table_args__ = (ForeignKeyConstraint(['bot_id', 'fed_id'], ['gg_federations.bot_id', 'gg_federations.id'],
        ondelete='CASCADE'), ForeignKeyConstraint(['bot_id', 'chat_id'], ['gg_chats.bot_id', 'gg_chats.chat_id'],
        ondelete='CASCADE'), Index('ix_gg_fed_chats_federation', 'bot_id', 'fed_id', 'chat_id'))
    bot_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    fed_id: Mapped[str] = mapped_column(String(36))
    quiet: Mapped[bool] = mapped_column(Boolean, default=False)
    generation: Mapped[str] = mapped_column(String(32))
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
# Also add GuardFederation.graph_generation Integer default0/server_default0 in0018.


class GuardFedBan(Base):
    __tablename__ = 'gg_fed_bans'
    __table_args__ = (ForeignKeyConstraint(['bot_id', 'fed_id'], ['gg_federations.bot_id', 'gg_federations.id'],
        ondelete='CASCADE'), Index('ix_gg_fed_bans_user', 'bot_id', 'user_id', 'active'),
        Index('ix_gg_fed_bans_active', 'bot_id', 'fed_id', 'active', 'user_id'))
    bot_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    fed_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    reason: Mapped[str | None] = mapped_column(String(1024))
    first_name: Mapped[str | None] = mapped_column(String(256))
    username: Mapped[str | None] = mapped_column(String(64))
    by_id: Mapped[int] = mapped_column(BigInt)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardFedSub(Base):
    __tablename__ = 'gg_fed_subs'
    __table_args__ = (ForeignKeyConstraint(['bot_id', 'fed_id'], ['gg_federations.bot_id', 'gg_federations.id'],
        name='fk_gg_fed_subs_source', ondelete='CASCADE'),
        ForeignKeyConstraint(['bot_id', 'target_id'], ['gg_federations.bot_id', 'gg_federations.id'],
            name='fk_gg_fed_subs_target', ondelete='CASCADE'),
        CheckConstraint('fed_id <> target_id', name='no_self'),
        Index('ix_gg_fed_subs_reverse', 'bot_id', 'target_id', 'fed_id'))
    bot_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    fed_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    target_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class GuardFedObservation(Base):
    __tablename__ = 'gg_fed_observations'
    __table_args__ = (ForeignKeyConstraint(['bot_id', 'chat_id'], ['gg_chats.bot_id', 'gg_chats.chat_id'],
        ondelete='CASCADE'), Index('ix_gg_fed_observations_user', 'bot_id', 'user_id', 'chat_id'))
    bot_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    first_name: Mapped[str | None] = mapped_column(String(256))
    username: Mapped[str | None] = mapped_column(String(64))
    last_seen: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
