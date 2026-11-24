"""add locked_by to user

Lưu người đã khoá tài khoản, để Giáo viên không mở khoá được tài khoản do Admin
khoá. Tài khoản đang bị khoá từ trước migration có ``locked_by = NULL`` và chỉ
Admin mở khoá được.

Revision ID: c4e5f6a7b8d9
Revises: d712d1718327
Create Date: 2026-11-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e5f6a7b8d9'
down_revision: Union[str, Sequence[str], None] = 'd712d1718327'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('user', sa.Column('locked_by', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        'fk_user_locked_by_user',
        'user',
        'user',
        ['locked_by'],
        ['user_id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_user_locked_by_user', 'user', type_='foreignkey')
    op.drop_column('user', 'locked_by')
