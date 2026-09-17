"""add avt_link to user and course

Revision ID: 8b2c3d4e5f6a
Revises: 7a1c2d3e4f5a
Create Date: 2026-09-16

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8b2c3d4e5f6a"
down_revision: str | Sequence[str] | None = "7a1c2d3e4f5a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add optional avatar links to users and courses."""
    op.add_column(
        "user",
        sa.Column("avt_link", sa.String(length=2048), nullable=True),
    )
    op.add_column(
        "course",
        sa.Column("avt_link", sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    """Remove avatar links from users and courses."""
    op.drop_column("course", "avt_link")
    op.drop_column("user", "avt_link")
