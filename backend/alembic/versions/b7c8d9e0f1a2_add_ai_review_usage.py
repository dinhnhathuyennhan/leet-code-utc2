"""add ai_review_usage

Lưu từng lượt AI review của sinh viên để giới hạn số lượt cho mỗi bài tập
(``AI_REVIEW_MAX_PER_PROBLEM``, mặc định 3). Unique (student_id, problem_id,
attempt_no) chặn vượt lượt khi nhiều request chạy đồng thời. Bảng mới, không
đụng dữ liệu cũ.

Revision ID: b7c8d9e0f1a2
Revises: c4e5f6a7b8d9
Create Date: 2026-11-23 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7c8d9e0f1a2"
down_revision: str | Sequence[str] | None = "c4e5f6a7b8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_review_usage",
        sa.Column("usage_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["problem.problem_id"]),
        sa.ForeignKeyConstraint(["student_id"], ["user.user_id"]),
        sa.ForeignKeyConstraint(["submission_id"], ["submission.submission_id"]),
        sa.PrimaryKeyConstraint("usage_id"),
        sa.UniqueConstraint(
            "student_id", "problem_id", "attempt_no", name="uq_ai_review_usage_slot"
        ),
    )
    op.create_index(
        op.f("ix_ai_review_usage_student_id"), "ai_review_usage", ["student_id"], unique=False
    )
    op.create_index(
        op.f("ix_ai_review_usage_problem_id"), "ai_review_usage", ["problem_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_review_usage_problem_id"), table_name="ai_review_usage")
    op.drop_index(op.f("ix_ai_review_usage_student_id"), table_name="ai_review_usage")
    op.drop_table("ai_review_usage")
