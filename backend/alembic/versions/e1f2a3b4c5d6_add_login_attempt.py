"""add login_attempt

Đếm số lần đăng nhập sai theo email để tạm chặn khi bị dò mật khẩu (LCUTC2-70).

Revision ID: e1f2a3b4c5d6
Revises: c4e5f6a7b8d9
Create Date: 2026-11-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'c4e5f6a7b8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'login_attempt',
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('failed_count', sa.Integer(), nullable=False),
        sa.Column('window_started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('email'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('login_attempt')
