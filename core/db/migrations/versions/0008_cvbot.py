"""CV summaries and one-off Pro reviews.

Revision ID: 0008_cvbot
Revises: 0007_factory_templates
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_cvbot"
down_revision: str | None = "0007_factory_templates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("cv_reports",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False),
        sa.Column("bot_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("summary", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["bot_id"], ["bots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cv_reports_user_created", "cv_reports", ["bot_id", "user_id", "created_at"])
    op.create_table("cv_invoices",
        sa.Column("id", sa.String(32), nullable=False),
        sa.Column("bot_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["bot_id"], ["bots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cv_invoices_user", "cv_invoices", ["bot_id", "user_id"])
    op.create_table("cv_review_credits",
        sa.Column("payment_id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False),
        sa.Column("invoice_id", sa.String(32), nullable=False),
        sa.Column("bot_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invoice_id"], ["cv_invoices.id"]),
        sa.ForeignKeyConstraint(["bot_id"], ["bots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("payment_id"),
        sa.UniqueConstraint("invoice_id"),
    )
    op.create_index("ix_cv_review_credits_user", "cv_review_credits", ["bot_id", "user_id", "used_at"])


def downgrade() -> None:
    op.drop_index("ix_cv_review_credits_user", table_name="cv_review_credits")
    op.drop_table("cv_review_credits")
    op.drop_index("ix_cv_invoices_user", table_name="cv_invoices")
    op.drop_table("cv_invoices")
    op.drop_index("ix_cv_reports_user_created", table_name="cv_reports")
    op.drop_table("cv_reports")
