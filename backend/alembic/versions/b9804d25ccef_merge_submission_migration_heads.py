"""merge submission migration heads

Revision ID: b9804d25ccef
Revises: a4ee9e02540a, f2a4b6c8d0e1
Create Date: 2026-10-20 21:10:59.609477

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b9804d25ccef'
down_revision: Union[str, Sequence[str], None] = ('a4ee9e02540a', 'f2a4b6c8d0e1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
