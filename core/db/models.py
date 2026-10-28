"""Multi-tenant ORM models for platform-level identity, per-bot memberships, settings and payments."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.base import Base, BigInt, JsonType, TZDateTime, utcnow


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(128))
    username: Mapped[str | None] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class User(Base):
    """Global Telegram user profile shared across all bots."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))
    language_code: Mapped[str | None] = mapped_column(String(8))
    is_globally_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow, index=True)
    last_seen: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class BotUser(Base):
    """Membership, preferences, quotas, and VIP status of a user within a specific bot."""

    __tablename__ = "bot_users"
    __table_args__ = (
        Index("ix_bot_users_bot_last_seen", "bot_id", "last_seen"),
        Index("ix_bot_users_bot_vip", "bot_id", "vip_until"),
        Index("ix_bot_users_bot_lang", "bot_id", "lang"),
        Index("ix_bot_users_referred_by", "referred_by"),
    )

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInt, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    lang: Mapped[str | None] = mapped_column(String(8))
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    ban_reason: Mapped[str | None] = mapped_column(String(256))
    blocked_bot: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    vip_until: Mapped[datetime | None] = mapped_column(TZDateTime())
    # Expiry-notice bookkeeping: which notice stage was sent for which vip_until value (renewal resets it).
    vip_notice: Mapped[str | None] = mapped_column(String(16))
    vip_notice_for: Mapped[datetime | None] = mapped_column(TZDateTime())
    referred_by: Mapped[int | None] = mapped_column(BigInt, ForeignKey("users.id", ondelete="SET NULL"))
    referral_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    referral_qualified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    actions_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    prefs: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)

    started_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)

    # Global user profile reference
    profile: Mapped[User] = relationship(User, foreign_keys=[user_id], lazy="joined")

    @property
    def id(self) -> int:
        """Alias for user_id to preserve compatibility with existing user.id references."""
        return self.user_id

    @property
    def username(self) -> str | None:
        return self.profile.username if self.profile else None

    @property
    def first_name(self) -> str | None:
        return self.profile.first_name if self.profile else None

    def is_vip(self, now: datetime | None = None) -> bool:
        if self.vip_until is None:
            return False
        vu = self.vip_until if self.vip_until.tzinfo else self.vip_until.replace(tzinfo=UTC)
        n = now or utcnow()
        return vu > n

    def pref(self, key: str, default: Any = None) -> Any:
        return (self.prefs or {}).get(key, default)

    @property
    def total_downloads(self) -> int:
        return self.actions_count


class Plan(Base):
    """VIP subscription plan (per-bot, or global pass if bot_id is NULL)."""

    __tablename__ = "plans"
    __table_args__ = (
        UniqueConstraint("bot_id", "name", name="uq_plans_bot_name"),
        CheckConstraint("days > 0 AND stars > 0", name="positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_id: Mapped[int | None] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    days: Mapped[int] = mapped_column(Integer)
    stars: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    sort: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_bot_created", "bot_id", "created_at"),
        CheckConstraint("status IN ('paid', 'refunded')", name="status"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(BigInt, ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    plan_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("plans.id", ondelete="SET NULL"))
    stars: Mapped[int] = mapped_column(Integer)
    days: Mapped[int] = mapped_column(Integer)
    charge_id: Mapped[str] = mapped_column(String(256), unique=True)
    status: Mapped[str] = mapped_column(String(16), default="paid")  # paid | refunded
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow, index=True)
    refunded_at: Mapped[datetime | None] = mapped_column(TZDateTime())


class BotSetting(Base):
    """Dynamic key-value settings per bot."""

    __tablename__ = "bot_settings"

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[object] = mapped_column(JsonType)


class ForceSubChannel(Base):
    __tablename__ = "force_sub_channels"

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=False)
    title: Mapped[str] = mapped_column(String(256))
    invite_link: Mapped[str] = mapped_column(String(256))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class Group(Base):
    __tablename__ = "groups"

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=False)
    title: Mapped[str | None] = mapped_column(String(256))
    auto_download: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    lang: Mapped[str | None] = mapped_column(String(8))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    # Bot-specific per-group preferences (e.g. socialdownload's auto_download).
    prefs: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class VipGrant(Base):
    """Ledger of every VIP extension, so refunds remove only paid time and audits can explain vip_until."""

    __tablename__ = "vip_grants"
    __table_args__ = (Index("ix_vip_grants_bot_user", "bot_id", "user_id"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(BigInt, ForeignKey("users.id", ondelete="CASCADE"))
    days: Mapped[int] = mapped_column(Integer)  # negative for deductions
    source: Mapped[str] = mapped_column(String(16))  # payment | referral | admin | refund | revoke
    payment_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), ForeignKey("payments.id", ondelete="SET NULL")
    )
    actor_id: Mapped[int | None] = mapped_column(BigInt)  # admin who granted, if any
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class Broadcast(Base):
    """Persisted broadcast job: survives restarts and can be resumed or cancelled."""

    __tablename__ = "broadcasts"
    __table_args__ = (
        Index("ix_broadcasts_bot_status", "bot_id", "status"),
        CheckConstraint(
            "status IN ('pending', 'running', 'done', 'cancelled', 'failed')",
            name="status",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"))
    created_by: Mapped[int] = mapped_column(BigInt)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    target: Mapped[str] = mapped_column(String(32), default="all")
    from_chat_id: Mapped[int] = mapped_column(BigInt)
    message_id: Mapped[int] = mapped_column(BigInteger)
    total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    sent: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    blocked: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    failed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    cursor: Mapped[int] = mapped_column(BigInt, default=0, server_default="0")  # last user_id processed
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    finished_at: Mapped[datetime | None] = mapped_column(TZDateTime())


class AdminAuditLog(Base):
    """Append-only record of every admin mutation."""

    __tablename__ = "admin_audit_log"
    __table_args__ = (Index("ix_admin_audit_log_bot_created", "bot_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"))
    admin_id: Mapped[int] = mapped_column(BigInt)
    action: Mapped[str] = mapped_column(String(64))
    target: Mapped[str | None] = mapped_column(String(128))
    details: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)


class ChildBot(Base):
    """A bot created by a user through the bot factory and hosted by the platform (slug ``c<id>``)."""

    __tablename__ = "child_bots"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'paused', 'error', 'revoked')", name="status"),
        Index("ix_child_bots_owner", "owner_id"),
        Index("ix_child_bots_status", "status"),
    )

    bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"), primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInt, ForeignKey("users.id", ondelete="CASCADE"))
    factory_bot_id: Mapped[int] = mapped_column(BigInt, ForeignKey("bots.id", ondelete="CASCADE"))
    template: Mapped[str] = mapped_column(String(32))
    # Fernet-encrypted bot token (FACTORY_SECRET_KEY); emptied when the bot is revoked or deleted.
    token_enc: Mapped[str] = mapped_column(Text)
    username: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default="active")
    last_error: Mapped[str | None] = mapped_column(String(512))
    # Show "Made with @factory" (owners with factory VIP can hide it).
    branding: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    # Listed in the factory's public gallery.
    public: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    description: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TZDateTime(), default=utcnow, onupdate=utcnow)
