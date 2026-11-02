"""add student_code to user

Revision ID: c1a2b3d4e5f6
Revises: b9804d25ccef
Create Date: 2026-10-28

Thêm field student_code (Mã số sinh viên) vào bảng user.
- Nullable (chỉ bắt buộc với STUDENT, các role khác để NULL)
- Unique index để tra cứu nhanh và tránh trùng
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1a2b3d4e5f6"
down_revision: str | Sequence[str] | None = "b9804d25ccef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "user",
        sa.Column(
            "student_code",
            sqlmodel.sql.sqltypes.AutoString(length=20),
            nullable=True,
        ),
    )
    op.create_index("ix_user_student_code", "user", ["student_code"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_user_student_code", table_name="user")
    op.drop_column("user", "student_code")
