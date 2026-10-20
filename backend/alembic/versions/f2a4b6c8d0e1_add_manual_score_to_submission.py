"""add manual score to submission

Revision ID: f2a4b6c8d0e1
Revises: e81ae8ef47ef
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "f2a4b6c8d0e1"
down_revision: str | None = "e81ae8ef47ef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("submission", sa.Column("manual_score", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("submission", "manual_score")
