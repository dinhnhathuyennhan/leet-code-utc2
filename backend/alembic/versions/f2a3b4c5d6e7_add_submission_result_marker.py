"""add submission.result_marker

Lưu dấu mốc kết quả ngẫu nhiên của harness đã nhúng vào source lúc gửi bài lên Judge0,
để worker chấm tiếp token cũ sau khi backend khởi động lại vẫn đọc đúng kết quả
(LCUTC2-73). Bài nộp cũ có ``result_marker = NULL`` và được đọc theo dấu mốc cố định cũ.

Revision ID: f2a3b4c5d6e7
Revises: c4e5f6a7b8d9
Create Date: 2026-11-24 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, Sequence[str], None] = 'c4e5f6a7b8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('submission', sa.Column('result_marker', sa.String(length=64), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('submission', 'result_marker')
