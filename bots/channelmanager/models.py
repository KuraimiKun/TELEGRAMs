"""Channel and publishing records. Composite foreign keys enforce namespace isolation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base, BigInt, JsonType, TZDateTime, utcnow


class Channel(Base):
    __tablename__ = "chm_channels"
    __table_args__ = (
        CheckConstraint("channel_id < 0", name="channel_id_negative"),
        CheckConstraint("generation >= 1", name="generation_positive"),
        CheckConstraint("status IN ('observed','active','degraded','removed','disconnected')", name="status"),
        Index("ix_chm_channels_operator", "bot_id", "connected_by", "channel_id"),
    )

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    title: Mapped[str] = mapped_column(String(256))
    username: Mapped[str | None] = mapped_column(String(64))
    connected_by: Mapped[int | None] = mapped_column(BigInt)
    status: Mapped[str] = mapped_column(String(16), default="observed")
    bot_status: Mapped[str] = mapped_column(String(16), default="left")
    rights: Mapped[dict[str, bool]] = mapped_column(JsonType, default=dict)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    generation: Mapped[int] = mapped_column(Integer, default=1)
    sender_paused: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    last_event_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    last_update_id: Mapped[int | None] = mapped_column(BigInt)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class ChannelRole(Base):
    __tablename__ = "chm_channel_roles"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"], ondelete="CASCADE"),
        CheckConstraint("source IN ('native','virtual')", name="source"),
        CheckConstraint("user_id > 0", name="user_positive"),
    )

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    source: Mapped[str] = mapped_column(String(16), default="native")
    permissions: Mapped[dict[str, bool]] = mapped_column(JsonType, default=dict)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class Entitlement(Base):
    __tablename__ = "chm_entitlements"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"], ondelete="CASCADE"),
        CheckConstraint("max_schedules >= 0", name="schedule_limit"),
    )

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    tier: Mapped[str] = mapped_column(String(32), default="free")
    max_schedules: Mapped[int] = mapped_column(Integer, default=20)
    expires_at: Mapped[datetime | None] = mapped_column(TZDateTime())


class Inbox(Base):
    __tablename__ = "chm_inbox"
    __table_args__ = (
        CheckConstraint("status IN ('pending','completed','failed')", name="status"),
        Index("ix_chm_inbox_due", "bot_id", "status", "available_at", "update_id"),
    )

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    update_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64))
    available_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    lease_owner: Mapped[str | None] = mapped_column(String(32))
    lease_until: Mapped[datetime | None] = mapped_column(TZDateTime())


class Operation(Base):
    __tablename__ = "chm_operations"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["bot_id", "channel_id", "delivery_id"],
                             ["chm_deliveries.bot_id", "chm_deliveries.channel_id", "chm_deliveries.id"]),
        ForeignKeyConstraint(["bot_id", "channel_id", "automation_id"],
                             ["chm_auto_actions.bot_id", "chm_auto_actions.channel_id", "chm_auto_actions.id"]),
        ForeignKeyConstraint(["bot_id", "channel_id", "member_action_id"],
                             ["chm_member_actions.bot_id", "chm_member_actions.channel_id", "chm_member_actions.id"]),
        ForeignKeyConstraint(["bot_id", "channel_id", "growth_action_id"],
                             ["chm_growth_actions.bot_id", "chm_growth_actions.channel_id", "chm_growth_actions.id"]),
        CheckConstraint("status IN ('pending','running','succeeded','failed','uncertain','cancelled')", name="status"),
        CheckConstraint("attempts >= 0 AND max_attempts > 0", name="attempts"),
        Index("uq_chm_operations_dedupe", "bot_id", "dedupe_key", unique=True),
        Index("ix_chm_operations_due", "bot_id", "status", "run_at"),
    )

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    delivery_id: Mapped[str | None] = mapped_column(String(32))
    automation_id: Mapped[str | None] = mapped_column(String(32))
    member_action_id: Mapped[str | None] = mapped_column(String(32))
    growth_action_id: Mapped[str | None] = mapped_column(String(32))
    generation: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(32))
    dedupe_key: Mapped[str] = mapped_column(String(160))
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    run_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    lease_owner: Mapped[str | None] = mapped_column(String(32))
    lease_until: Mapped[datetime | None] = mapped_column(TZDateTime())
    dispatched: Mapped[bool] = mapped_column(Boolean, default=False)
    error_code: Mapped[str | None] = mapped_column(String(64))
    remote_message_id: Mapped[int | None] = mapped_column(BigInt)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class Event(Base):
    __tablename__ = "chm_events"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"], ondelete="CASCADE"),
        Index("ix_chm_events_channel", "bot_id", "channel_id", "created_at"),
    )

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    actor_id: Mapped[int | None] = mapped_column(BigInt)
    action: Mapped[str] = mapped_column(String(64))
    details: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class ChannelStyle(Base):
    __tablename__ = "chm_channel_styles"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"], ondelete="CASCADE"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    signature: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)


class Post(Base):
    __tablename__ = "chm_posts"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        CheckConstraint("generation > 0 AND version > 0", name="versions_positive"),
        Index("uq_chm_posts_source", "bot_id", "source_key", unique=True),
        Index("ix_chm_posts_creator", "bot_id", "creator_id", "created_at"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    creator_id: Mapped[int] = mapped_column(BigInt)
    generation: Mapped[int] = mapped_column(Integer, default=1)
    version: Mapped[int] = mapped_column(Integer, default=1)
    target_ids: Mapped[list[int]] = mapped_column(JsonType)
    source_key: Mapped[str | None] = mapped_column(String(128))
    detached: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class PostVersion(Base):
    __tablename__ = "chm_post_versions"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "post_id"], ["chm_posts.bot_id", "chm_posts.id"], ondelete="CASCADE"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    post_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    number: Mapped[int] = mapped_column(Integer, primary_key=True)
    spec: Mapped[dict[str, Any]] = mapped_column(JsonType)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class Delivery(Base):
    __tablename__ = "chm_deliveries"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        ForeignKeyConstraint(["bot_id", "post_id", "version"],
                             ["chm_post_versions.bot_id", "chm_post_versions.post_id", "chm_post_versions.number"]),
        CheckConstraint("state IN ('pending','sent','failed','uncertain','cancelled','held','deleted','detached')", name="state"),
        Index("ix_chm_deliveries_post", "bot_id", "post_id", "channel_id"),
        Index("ix_chm_deliveries_remote", "bot_id", "channel_id", "message_id"),
        UniqueConstraint("bot_id", "post_id", "channel_id", name="uq_chm_delivery_target"),
        UniqueConstraint("bot_id", "channel_id", "id", name="uq_chm_delivery_scope"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    post_id: Mapped[str] = mapped_column(String(32))
    channel_id: Mapped[int] = mapped_column(BigInt)
    version: Mapped[int] = mapped_column(Integer)
    generation: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[int] = mapped_column(BigInt)
    state: Mapped[str] = mapped_column(String(16), default="pending")
    message_id: Mapped[int | None] = mapped_column(BigInt)
    sent_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    publish_op: Mapped[str | None] = mapped_column(String(32))
    edit_op: Mapped[str | None] = mapped_column(String(32))
    pin_op: Mapped[str | None] = mapped_column(String(32))
    delete_op: Mapped[str | None] = mapped_column(String(32))
    markup_op: Mapped[str | None] = mapped_column(String(32))
    edit_status: Mapped[str] = mapped_column(String(16), default="none")
    pin_status: Mapped[str] = mapped_column(String(16), default="none")
    delete_status: Mapped[str] = mapped_column(String(16), default="none")
    markup_status: Mapped[str] = mapped_column(String(16), default="none")
    replace_pending: Mapped[bool] = mapped_column(Boolean, default=False)
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class PostSchedule(Base):
    __tablename__ = "chm_post_schedules"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "post_id"], ["chm_posts.bot_id", "chm_posts.id"], ondelete="CASCADE"),
        CheckConstraint("status IN ('pending','fired','cancelled','held')", name="status"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    post_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    generation: Mapped[int] = mapped_column(Integer)
    run_at: Mapped[datetime] = mapped_column(TZDateTime())
    status: Mapped[str] = mapped_column(String(16), default="pending")


class Preset(Base):
    __tablename__ = "chm_presets"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id"], ["bots.id"], ondelete="CASCADE"),
        UniqueConstraint("bot_id", "owner_id", "kind", "name", name="uq_chm_preset_name"),
        CheckConstraint("kind IN ('buttons','channels')", name="kind"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInt)
    kind: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(64))
    value: Mapped[dict[str, Any]] = mapped_column(JsonType)
    generation: Mapped[int] = mapped_column(Integer, default=1)


class ChannelDefaults(Base):
    __tablename__ = "chm_channel_defaults"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"], ondelete="CASCADE"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    reactions: Mapped[list[str]] = mapped_column(JsonType, default=list)


class VoteBoard(Base):
    __tablename__ = "chm_vote_boards"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "delivery_id"], ["chm_deliveries.bot_id", "chm_deliveries.id"]),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    delivery_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    closed: Mapped[bool] = mapped_column(Boolean, default=False)
    revision: Mapped[int] = mapped_column(Integer, default=0)


class Vote(Base):
    __tablename__ = "chm_votes"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "delivery_id", "version"],
            ["chm_vote_boards.bot_id", "chm_vote_boards.delivery_id", "chm_vote_boards.version"], ondelete="CASCADE"),
        CheckConstraint("choice >= 0 AND choice < 46", name="choice"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    delivery_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    choice: Mapped[int] = mapped_column(Integer)


class Recurrence(Base):
    __tablename__ = "chm_recurrences"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "post_id"], ["chm_posts.bot_id", "chm_posts.id"]),
        UniqueConstraint("bot_id", "post_id", name="uq_chm_recurrence_post"),
        CheckConstraint("status IN ('active','paused','finished')", name="status"),
        Index("ix_chm_recurrences_due", "bot_id", "status", "next_at"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    post_id: Mapped[str] = mapped_column(String(32))
    rule: Mapped[dict[str, Any]] = mapped_column(JsonType)
    replace_previous: Mapped[bool] = mapped_column(Boolean, default=False)
    generation: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="active")
    next_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    last_skipped_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    error_code: Mapped[str | None] = mapped_column(String(64))


class Occurrence(Base):
    __tablename__ = "chm_occurrences"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "recurrence_id"], ["chm_recurrences.bot_id", "chm_recurrences.id"]),
        ForeignKeyConstraint(["bot_id", "post_id"], ["chm_posts.bot_id", "chm_posts.id"]),
        UniqueConstraint("bot_id", "post_id", name="uq_chm_occurrence_post"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    recurrence_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    scheduled_at: Mapped[datetime] = mapped_column(TZDateTime(), primary_key=True)
    post_id: Mapped[str] = mapped_column(String(32))
    root_version: Mapped[int] = mapped_column(Integer)


class Batch(Base):
    __tablename__ = "chm_batches"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        CheckConstraint("status IN ('collecting','ready','queued','cancelled')", name="status"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    creator_id: Mapped[int] = mapped_column(BigInt)
    generation: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="collecting")
    defaults: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    buttons_mode: Mapped[str] = mapped_column(String(16), default="shared")
    reactions_mode: Mapped[str] = mapped_column(String(16), default="shared")


class BatchItem(Base):
    __tablename__ = "chm_batch_items"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "batch_id"], ["chm_batches.bot_id", "chm_batches.id"]),
        ForeignKeyConstraint(["bot_id", "post_id"], ["chm_posts.bot_id", "chm_posts.id"]),
        UniqueConstraint("bot_id", "post_id", name="uq_chm_batch_item_post"),
        UniqueConstraint("bot_id", "batch_id", "input_key", name="uq_chm_batch_input"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[str] = mapped_column(String(32))
    input_key: Mapped[str] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Calendar(Base):
    __tablename__ = "chm_calendars"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        UniqueConstraint("bot_id", "channel_id", "name", name="uq_chm_calendar_name"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    name: Mapped[str] = mapped_column(String(64))
    timezone: Mapped[str] = mapped_column(String(64))
    slots: Mapped[list[dict[str, Any]]] = mapped_column(JsonType)
    generation: Mapped[int] = mapped_column(Integer, default=1)


class CalendarReservation(Base):
    __tablename__ = "chm_calendar_reservations"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "calendar_id"], ["chm_calendars.bot_id", "chm_calendars.id"]),
        ForeignKeyConstraint(["bot_id", "post_id"], ["chm_posts.bot_id", "chm_posts.id"]),
        # Completed reservations remain claimed; cancellation releases only unsent slots.
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    calendar_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    run_at: Mapped[datetime] = mapped_column(TZDateTime(), primary_key=True)
    post_id: Mapped[str] = mapped_column(String(32))


class AutomationControl(Base):
    __tablename__ = "chm_auto_controls"
    __table_args__ = (ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    generation: Mapped[int] = mapped_column(Integer, default=1)


class AutoRule(Base):
    __tablename__ = "chm_auto_rules"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        UniqueConstraint("bot_id", "channel_id", "id", name="uq_chm_auto_rule_scope"),
        UniqueConstraint("bot_id", "channel_id", "name", name="uq_chm_auto_rule_name"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    creator_id: Mapped[int] = mapped_column(BigInt)
    name: Mapped[str] = mapped_column(String(64))
    priority: Mapped[int] = mapped_column(Integer, default=100)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    generation: Mapped[int] = mapped_column(Integer, default=1)
    spec: Mapped[dict[str, Any]] = mapped_column(JsonType)
    active_since: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class ForwardRoute(Base):
    __tablename__ = "chm_forward_routes"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        UniqueConstraint("bot_id", "channel_id", "id", name="uq_chm_route_scope"),
        UniqueConstraint("bot_id", "channel_id", "name", name="uq_chm_route_name"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    creator_id: Mapped[int] = mapped_column(BigInt)
    destination_id: Mapped[int] = mapped_column(BigInt)
    destination_type: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    generation: Mapped[int] = mapped_column(Integer, default=1)
    spec: Mapped[dict[str, Any]] = mapped_column(JsonType)
    active_since: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class AutoSource(Base):
    __tablename__ = "chm_auto_sources"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        ForeignKeyConstraint(["bot_id", "mirror_post_id"], ["chm_posts.bot_id", "chm_posts.id"]),
        UniqueConstraint("bot_id", "channel_id", "id", name="uq_chm_source_scope"),
        UniqueConstraint("bot_id", "channel_id", "source_key", name="uq_chm_source_key"),
        CheckConstraint("status IN ('collecting','planned','ignored','held')", name="status"),
        Index("ix_chm_auto_sources_due", "bot_id", "status", "available_at"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    source_key: Mapped[str] = mapped_column(String(128))
    generation: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="collecting")
    error_code: Mapped[str | None] = mapped_column(String(64))
    album: Mapped[bool] = mapped_column(Boolean, default=False)
    edited: Mapped[bool] = mapped_column(Boolean, default=False)
    mirror_post_id: Mapped[str | None] = mapped_column(String(32))
    provenance: Mapped[list[int]] = mapped_column(JsonType, default=list)
    available_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class AutoPart(Base):
    __tablename__ = "chm_auto_parts"
    __table_args__ = (ForeignKeyConstraint(["bot_id", "source_id"], ["chm_auto_sources.bot_id", "chm_auto_sources.id"]),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    message_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    body: Mapped[dict[str, Any]] = mapped_column(JsonType)
    fingerprint: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(TZDateTime())
    update_id: Mapped[int] = mapped_column(BigInt)
    received_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    affixes: Mapped[dict[str, str]] = mapped_column(JsonType, default=dict)


class AutoSnapshot(Base):
    __tablename__ = "chm_auto_snapshots"
    __table_args__ = (ForeignKeyConstraint(["bot_id", "source_id"], ["chm_auto_sources.bot_id", "chm_auto_sources.id"]),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    number: Mapped[int] = mapped_column(Integer, primary_key=True)
    original: Mapped[list[dict[str, Any]]] = mapped_column(JsonType)
    transformed: Mapped[list[dict[str, Any]]] = mapped_column(JsonType)
    warnings: Mapped[list[str]] = mapped_column(JsonType, default=list)


class AutoAction(Base):
    __tablename__ = "chm_auto_actions"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id", "source_id"], ["chm_auto_sources.bot_id", "chm_auto_sources.channel_id", "chm_auto_sources.id"]),
        ForeignKeyConstraint(["bot_id", "source_id", "version"], ["chm_auto_snapshots.bot_id", "chm_auto_snapshots.source_id", "chm_auto_snapshots.number"]),
        ForeignKeyConstraint(["bot_id", "channel_id", "rule_id"], ["chm_auto_rules.bot_id", "chm_auto_rules.channel_id", "chm_auto_rules.id"]),
        ForeignKeyConstraint(["bot_id", "channel_id", "route_id"], ["chm_forward_routes.bot_id", "chm_forward_routes.channel_id", "chm_forward_routes.id"]),
        UniqueConstraint("bot_id", "channel_id", "id", name="uq_chm_auto_action_scope"),
        UniqueConstraint("bot_id", "source_id", "version", "action_key", name="uq_chm_auto_action_key"),
        Index("ix_chm_auto_actions_source", "bot_id", "source_id", "version"),
        CheckConstraint("status IN ('pending','succeeded','failed','uncertain','cancelled','held','skipped')", name="status"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    source_id: Mapped[str] = mapped_column(String(16))
    version: Mapped[int] = mapped_column(Integer)
    action_key: Mapped[str] = mapped_column(String(96))
    rule_id: Mapped[str | None] = mapped_column(String(16))
    route_id: Mapped[str | None] = mapped_column(String(16))
    control_generation: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[int] = mapped_column(BigInt)
    destination_id: Mapped[int] = mapped_column(BigInt)
    kind: Mapped[str] = mapped_column(String(24))
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    operation_id: Mapped[str | None] = mapped_column(String(32))
    remote_ids: Mapped[list[int]] = mapped_column(JsonType, default=list)
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class AutoOutput(Base):
    __tablename__ = "chm_auto_outputs"
    __table_args__ = (ForeignKeyConstraint(["bot_id", "action_id"], ["chm_auto_actions.bot_id", "chm_auto_actions.id"]),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    message_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    action_id: Mapped[str] = mapped_column(String(32))


class MemberConfig(Base):
    __tablename__ = "chm_member_configs"
    __table_args__ = (ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    actor_id: Mapped[int] = mapped_column(BigInt)
    generation: Mapped[int] = mapped_column(Integer, default=1)
    spec: Mapped[dict[str, Any]] = mapped_column(JsonType)
    active_since: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class MemberHead(Base):
    __tablename__ = "chm_member_heads"
    __table_args__ = (ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    generation: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[str] = mapped_column(String(16), default="unknown")
    observed_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    update_id: Mapped[int] = mapped_column(BigInt, default=0)
    request_id: Mapped[str | None] = mapped_column(String(16))
    last_request_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    last_actor_id: Mapped[int | None] = mapped_column(BigInt)


class JoinRequest(Base):
    __tablename__ = "chm_join_requests"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id", "user_id"], ["chm_member_heads.bot_id", "chm_member_heads.channel_id", "chm_member_heads.user_id"]),
        UniqueConstraint("bot_id", "channel_id", "id", name="uq_chm_join_request_scope"),
        UniqueConstraint("bot_id", "channel_id", "user_id", "generation", name="uq_chm_join_request_generation"),
        CheckConstraint("status IN ('pending','held','approved','declined','expired','superseded','uncertain','cancelled')", name="status"),
        Index("ix_chm_join_requests_due", "bot_id", "status", "next_check"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    user_id: Mapped[int] = mapped_column(BigInt)
    generation: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[int] = mapped_column(BigInt)
    config_generation: Mapped[int] = mapped_column(Integer)
    spec: Mapped[dict[str, Any]] = mapped_column(JsonType)
    profile: Mapped[dict[str, Any]] = mapped_column(JsonType)
    requested_at: Mapped[datetime] = mapped_column(TZDateTime())
    contact_chat_id: Mapped[int] = mapped_column(BigInt)
    contact_deadline: Mapped[datetime] = mapped_column(TZDateTime())
    expires_at: Mapped[datetime] = mapped_column(TZDateTime())
    approve_after: Mapped[datetime] = mapped_column(TZDateTime())
    next_check: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    error_code: Mapped[str | None] = mapped_column(String(64))
    manual_release: Mapped[bool] = mapped_column(Boolean, default=False)
    captcha_solved: Mapped[bool] = mapped_column(Boolean, default=False)
    captcha_attempts: Mapped[int] = mapped_column(Integer, default=0)
    challenge: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    required_index: Mapped[int] = mapped_column(Integer, default=0)
    filter_code: Mapped[str | None] = mapped_column(String(64))
    invite_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    invite_epoch: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    referral_hash: Mapped[str | None] = mapped_column(String(64))
    referral_eligible: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class MemberLead(Base):
    __tablename__ = "chm_member_leads"
    __table_args__ = (ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    private_interacted_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    reachable: Mapped[bool] = mapped_column(Boolean, default=False)
    opted_out: Mapped[bool] = mapped_column(Boolean, default=False)
    campaign_opt_in: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    last_join_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    last_leave_at: Mapped[datetime | None] = mapped_column(TZDateTime())


class MemberGateReceipt(Base):
    __tablename__ = "chm_member_gate_receipts"
    __table_args__ = (ForeignKeyConstraint(["bot_id", "request_id"], ["chm_join_requests.bot_id", "chm_join_requests.id"]),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    callback_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(16))


class MemberAction(Base):
    __tablename__ = "chm_member_actions"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        ForeignKeyConstraint(["bot_id", "channel_id", "request_id"], ["chm_join_requests.bot_id", "chm_join_requests.channel_id", "chm_join_requests.id"]),
        UniqueConstraint("bot_id", "channel_id", "id", name="uq_chm_member_action_scope"),
        UniqueConstraint("bot_id", "dedupe_key", name="uq_chm_member_action_key"),
        CheckConstraint("status IN ('pending','succeeded','failed','uncertain','cancelled','skipped')", name="status"),
        Index("ix_chm_member_actions_request", "bot_id", "request_id"),
        Index("ix_chm_member_actions_output", "bot_id", "kind", "remote_id"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    request_id: Mapped[str | None] = mapped_column(String(16))
    user_id: Mapped[int | None] = mapped_column(BigInt)
    actor_id: Mapped[int] = mapped_column(BigInt)
    generation: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(16))
    dedupe_key: Mapped[str] = mapped_column(String(160))
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType)
    cleanup: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    error_code: Mapped[str | None] = mapped_column(String(64))
    operation_id: Mapped[str | None] = mapped_column(String(32))
    remote_id: Mapped[int | None] = mapped_column(BigInt)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class MemberBan(Base):
    __tablename__ = "chm_member_bans"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        ForeignKeyConstraint(["bot_id", "channel_id", "action_id"], ["chm_member_actions.bot_id", "chm_member_actions.channel_id", "chm_member_actions.id"]),
        UniqueConstraint("bot_id", "action_id", name="uq_chm_member_ban_action"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    chat_id: Mapped[int] = mapped_column(BigInt)
    user_id: Mapped[int] = mapped_column(BigInt)
    action_id: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    until_date: Mapped[datetime | None] = mapped_column(TZDateTime())


class MemberBulk(Base):
    __tablename__ = "chm_member_bulk"
    __table_args__ = (ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    actor_id: Mapped[int] = mapped_column(BigInt)
    config_generation: Mapped[int] = mapped_column(Integer)
    request_ids: Mapped[list[str]] = mapped_column(JsonType)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    result: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    expires_at: Mapped[datetime] = mapped_column(TZDateTime())


class VirtualGrant(Base):
    __tablename__ = "chm_virtual_grants"
    __table_args__ = (ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    grantor_id: Mapped[int] = mapped_column(BigInt)
    generation: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    permissions: Mapped[dict[str, Any]] = mapped_column(JsonType)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class LockedContent(Base):
    __tablename__ = "chm_locked_content"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        ForeignKeyConstraint(["bot_id", "post_id"], ["chm_posts.bot_id", "chm_posts.id"]),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    creator_id: Mapped[int] = mapped_column(BigInt)
    post_id: Mapped[str] = mapped_column(String(32))
    generation: Mapped[int] = mapped_column(Integer, default=1)
    link_epoch: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    secret: Mapped[dict[str, Any]] = mapped_column(JsonType)
    required: Mapped[list[dict[str, Any]]] = mapped_column(JsonType, default=list)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class Campaign(Base):
    __tablename__ = "chm_campaigns"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        UniqueConstraint("bot_id", "channel_id", "id", name="uq_chm_campaign_scope"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    creator_id: Mapped[int] = mapped_column(BigInt)
    generation: Mapped[int] = mapped_column(Integer, default=1)
    spec: Mapped[dict[str, Any]] = mapped_column(JsonType)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    total: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(TZDateTime())
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class CampaignRecipient(Base):
    __tablename__ = "chm_campaign_recipients"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id", "campaign_id"], ["chm_campaigns.bot_id", "chm_campaigns.channel_id", "chm_campaigns.id"]),
        ForeignKeyConstraint(["bot_id", "channel_id", "user_id"], ["chm_member_leads.bot_id", "chm_member_leads.channel_id", "chm_member_leads.user_id"]),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    status: Mapped[str] = mapped_column(String(16), default="selected")
    action_id: Mapped[str | None] = mapped_column(String(32))


class GrowthAction(Base):
    __tablename__ = "chm_growth_actions"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        UniqueConstraint("bot_id", "channel_id", "id", name="uq_chm_growth_action_scope"),
        UniqueConstraint("bot_id", "dedupe_key", name="uq_chm_growth_action_key"),
        Index("ix_chm_growth_actions_resource", "bot_id", "kind", "resource_id"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    actor_id: Mapped[int] = mapped_column(BigInt)
    user_id: Mapped[int | None] = mapped_column(BigInt)
    kind: Mapped[str] = mapped_column(String(24))
    resource_id: Mapped[str | None] = mapped_column(String(32))
    generation: Mapped[int] = mapped_column(Integer, default=1)
    dedupe_key: Mapped[str] = mapped_column(String(160))
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    error_code: Mapped[str | None] = mapped_column(String(64))
    operation_id: Mapped[str | None] = mapped_column(String(32))
    remote_id: Mapped[int | None] = mapped_column(BigInt)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class MemberInvite(Base):
    __tablename__ = "chm_member_invites"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id", "request_id"], ["chm_join_requests.bot_id", "chm_join_requests.channel_id", "chm_join_requests.id"]),
        UniqueConstraint("bot_id", "request_id", "epoch", name="uq_chm_invite_epoch"),
        UniqueConstraint("bot_id", "channel_id", "link_hash", name="uq_chm_invite_link"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    request_id: Mapped[str] = mapped_column(String(16))
    user_id: Mapped[int] = mapped_column(BigInt)
    epoch: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    link_hash: Mapped[str | None] = mapped_column(String(64))
    link_enc: Mapped[str | None] = mapped_column(Text)


class InviteCredit(Base):
    __tablename__ = "chm_invite_credits"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        ForeignKeyConstraint(["bot_id", "invite_id"], ["chm_member_invites.bot_id", "chm_member_invites.id"]),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    invitee_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    invite_id: Mapped[str] = mapped_column(String(16))
    request_id: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class ChannelPlanVersion(Base):
    __tablename__ = "chm_plan_versions"
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    spec: Mapped[dict[str, Any]] = mapped_column(JsonType)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(BigInt)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class ChannelInvoice(Base):
    __tablename__ = "chm_channel_invoices"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        ForeignKeyConstraint(["bot_id", "plan_id"], ["chm_plan_versions.bot_id", "chm_plan_versions.id"]),
        UniqueConstraint("bot_id", "channel_id", "id", name="uq_chm_invoice_scope"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    payer_id: Mapped[int] = mapped_column(BigInt)
    plan_id: Mapped[str] = mapped_column(String(16))
    spec: Mapped[dict[str, Any]] = mapped_column(JsonType)
    amount: Mapped[int] = mapped_column(Integer)
    seconds: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(16), default="renew")
    base_grant_id: Mapped[str | None] = mapped_column(String(16))
    basis_hash: Mapped[str | None] = mapped_column(String(64))
    coverage_end: Mapped[datetime | None] = mapped_column(TZDateTime())
    status: Mapped[str] = mapped_column(String(16), default="quoted")
    checkout_id: Mapped[str | None] = mapped_column(String(128))
    checkout_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id"))
    charge_id: Mapped[str | None] = mapped_column(String(256))
    delivery_status: Mapped[str] = mapped_column(String(16), default="none")
    expires_at: Mapped[datetime] = mapped_column(TZDateTime())
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class ChannelGrant(Base):
    __tablename__ = "chm_channel_grants"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id", "invoice_id"], ["chm_channel_invoices.bot_id", "chm_channel_invoices.channel_id", "chm_channel_invoices.id"]),
        ForeignKeyConstraint(["bot_id", "channel_id", "parent_id"], ["chm_channel_grants.bot_id", "chm_channel_grants.channel_id", "chm_channel_grants.id"]),
        UniqueConstraint("bot_id", "channel_id", "id", name="uq_chm_grant_scope"),
        UniqueConstraint("payment_id", name="uq_chm_grant_payment"),
        Index("ix_chm_grants_period", "bot_id", "channel_id", "ends_at"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    invoice_id: Mapped[str] = mapped_column(String(32))
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"))
    parent_id: Mapped[str | None] = mapped_column(String(16))
    spec: Mapped[dict[str, Any]] = mapped_column(JsonType)
    seconds: Mapped[int] = mapped_column(Integer)
    starts_at: Mapped[datetime] = mapped_column(TZDateTime())
    ends_at: Mapped[datetime] = mapped_column(TZDateTime())
    status: Mapped[str] = mapped_column(String(16), default="paid")
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class ChannelBilling(Base):
    __tablename__ = "chm_channel_billing"
    __table_args__ = (ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    generation: Mapped[int] = mapped_column(Integer, default=1)
    current_plan: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    paid_until: Mapped[datetime | None] = mapped_column(TZDateTime())


class BillingIncident(Base):
    __tablename__ = "chm_billing_incidents"
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payer_id: Mapped[int] = mapped_column(BigInt)
    invoice_id: Mapped[str | None] = mapped_column(String(32))
    charge_id: Mapped[str] = mapped_column(String(256))
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8))
    code: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="review")
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class SenderBinding(Base):
    __tablename__ = "chm_sender_bindings"
    __table_args__ = (
        ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),
        UniqueConstraint("sender_bot_id", "channel_id", name="uq_chm_bound_sender_channel"),
    )
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    sender_bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("child_bots.bot_id", ondelete="CASCADE"))
    owner_id: Mapped[int] = mapped_column(BigInt)
    token_epoch: Mapped[str] = mapped_column(String(64))
    generation: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    control_username: Mapped[str] = mapped_column(String(64))


class SubscriberMenu(Base):
    __tablename__ = "chm_subscriber_menus"
    __table_args__ = (ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt, primary_key=True)
    actor_id: Mapped[int] = mapped_column(BigInt)
    generation: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[dict[str, Any]] = mapped_column(JsonType)
    feedback: Mapped[bool] = mapped_column(Boolean, default=False)


class Feedback(Base):
    __tablename__ = "chm_feedback"
    __table_args__ = (ForeignKeyConstraint(["bot_id", "channel_id"], ["chm_channels.bot_id", "chm_channels.channel_id"]),)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInt)
    user_id: Mapped[int] = mapped_column(BigInt)
    actor_id: Mapped[int] = mapped_column(BigInt)
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="received")
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class LeadPrivacy(Base):
    __tablename__ = "chm_lead_privacy"
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
