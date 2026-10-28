"""Document processing metadata.

Revision ID: 0009_doctools
Revises: 0008_cvbot
"""

from alembic import op
import sqlalchemy as sa

revision = "0009_doctools"
down_revision = "0008_cvbot"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dt_jobs",
        sa.Column("id", sa.String(32), nullable=False),
        sa.Column("bot_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("operation", sa.String(24), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("pages", sa.Integer(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["bot_id"], ["bots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dt_jobs_bot_created", "dt_jobs", ["bot_id", "created_at"])
    op.create_index("ix_dt_jobs_user_id", "dt_jobs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_dt_jobs_user_id", table_name="dt_jobs")
    op.drop_index("ix_dt_jobs_bot_created", table_name="dt_jobs")
    op.drop_table("dt_jobs")
