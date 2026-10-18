"""store datetimes as timestamptz

Revision ID: 18d97a502f6f
Revises: 28018a8cce68
Create Date: 2026-10-14

Dữ liệu cũ (timestamp naive) đang là giờ VN nên được quy đổi theo
'Asia/Ho_Chi_Minh' khi chuyển sang timestamptz.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "18d97a502f6f"
down_revision: str | Sequence[str] | None = "28018a8cce68"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DATETIME_COLUMNS = (
    ("course", "start_date"),
    ("course", "end_date"),
    ("problem", "start_datetime"),
    ("problem", "end_datetime"),
    ("submission", "submitted_datetime"),
)


def upgrade() -> None:
    """Upgrade schema."""
    for table, column in DATETIME_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=False,
            postgresql_using=f"{column} AT TIME ZONE 'Asia/Ho_Chi_Minh'",
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table, column in DATETIME_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using=f"{column} AT TIME ZONE 'Asia/Ho_Chi_Minh'",
        )
