"""add submission grading_claimed_at

Lease cho worker chấm bài: worker nhận bài bằng UPDATE có điều kiện trên cột này, để
khôi phục lúc khởi động và lượt enqueue mới không chấm trùng một bài nộp.

Revision ID: b1c2d3e4f5a6
Revises: f0c2c81e8bc3
Create Date: 2026-11-20 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'f0c2c81e8bc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'submission',
        sa.Column('grading_claimed_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('submission', 'grading_claimed_at')
