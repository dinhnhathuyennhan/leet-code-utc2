"""add manual score to submission"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "2a7b8c9d0e1f"
down_revision: str | Sequence[str] | None = "18d97a502f6f"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("submission", sa.Column("manual_score", sa.Float(), nullable=True))

def downgrade() -> None:
    op.drop_column("submission", "manual_score")
