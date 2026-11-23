"""recount course.total_number_student from enrollment

``course.total_number_student`` là cột cache, trước đây được cộng/trừ dồn
(``+= 1`` / ``-= 1``) nên có thể lệch so với số dòng ``enrollment`` thật
(vd header lớp hiện 134 sinh viên trong khi lớp chỉ có 97). Từ nay service đếm
lại sau mỗi lần ghi danh thay đổi; migration này sửa giá trị đã lệch của mọi
course hiện có.

Chỉ biến đổi dữ liệu, không đổi schema. Downgrade không làm gì vì không có
giá trị "đúng" nào để khôi phục.

Revision ID: a9b8c7d6e5f4
Revises: c4e5f6a7b8d9
Create Date: 2026-11-22 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a9b8c7d6e5f4"
down_revision: str | Sequence[str] | None = "c4e5f6a7b8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.get_bind().execute(
        sa.text(
            """
            UPDATE course
            SET total_number_student = (
                SELECT count(*) FROM enrollment AS e
                WHERE e.course_id = course.course_id
            )
            """
        )
    )


def downgrade() -> None:
    pass
