"""add date_of_birth to user

Revision ID: 7a1c2d3e4f5a
Revises: 5c094a3746cd
Create Date: 2026-09-14

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7a1c2d3e4f5a"
down_revision: str | Sequence[str] | None = "5c094a3746cd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("user", sa.Column("date_of_birth", sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("user", "date_of_birth")
