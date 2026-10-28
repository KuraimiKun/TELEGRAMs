"""Group Guard approvals, scoped to bot and group."""
from alembic import op
import sqlalchemy as sa

revision = "0011_gg_approvals"
down_revision = "0010_gg_foundations"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("gg_restrictions", sa.Column("state", sa.String(16), nullable=False, server_default="applied"))
    op.create_index("ix_gg_restrictions_recovery", "gg_restrictions", ["bot_id", "state", "updated_at"])
    op.create_table("gg_approvals",
        sa.Column("bot_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(256), nullable=True),
        sa.Column("by_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["bot_id"], ["bots.id"], name=op.f("fk_gg_approvals_bot_id_bots"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("bot_id", "chat_id", "user_id", name=op.f("pk_gg_approvals")))


def downgrade():
    op.drop_table("gg_approvals")
    op.drop_index("ix_gg_restrictions_recovery", table_name="gg_restrictions")
    op.drop_column("gg_restrictions", "state")
