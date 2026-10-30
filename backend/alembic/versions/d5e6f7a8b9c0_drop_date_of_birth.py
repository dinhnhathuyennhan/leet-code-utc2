"""drop date_of_birth from user

Revision ID: d5e6f7a8b9c0
Revises: c1a2b3d4e5f6
Create Date: 2026-10-28
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d5e6f7a8b9c0"
down_revision: str | Sequence[str] | None = "c1a2b3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("user", "date_of_birth")


def downgrade() -> None:
    import sqlalchemy as sa

    op.add_column("user", sa.Column("date_of_birth", sa.Date(), nullable=True))
