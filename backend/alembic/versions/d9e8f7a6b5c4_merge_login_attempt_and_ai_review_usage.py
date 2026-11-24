"""merge heads: login_attempt và ai_review_usage

Hai migration ``e1f2a3b4c5d6`` (login_attempt, LCUTC2-70) và ``b7c8d9e0f1a2``
(ai_review_usage, LCUTC2-71) được tạo song song trên hai nhánh, cùng nối sau
``c4e5f6a7b8d9``. Revision này gộp hai head lại để ``alembic upgrade head`` chạy được.
Không thay đổi schema.

Revision ID: d9e8f7a6b5c4
Revises: b7c8d9e0f1a2, e1f2a3b4c5d6
Create Date: 2026-11-24 16:00:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'd9e8f7a6b5c4'
down_revision: Union[str, Sequence[str], None] = ('b7c8d9e0f1a2', 'e1f2a3b4c5d6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
