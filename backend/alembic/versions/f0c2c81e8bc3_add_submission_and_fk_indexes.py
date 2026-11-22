"""add submission and fk indexes

Index cho bảng submission (tra cứu theo bài/sinh viên) và các khoá ngoại nằm
trên đường JOIN. Postgres không tự tạo index cho cột FK.

Revision ID: f0c2c81e8bc3
Revises: a8b9c0d1e2f3
Create Date: 2026-11-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f0c2c81e8bc3'
down_revision: Union[str, Sequence[str], None] = 'a8b9c0d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'ix_submission_problem_student',
        'submission',
        ['problem_id', 'student_id'],
        unique=False,
    )
    op.create_index(
        'ix_submission_student_submitted',
        'submission',
        ['student_id', 'submitted_datetime', 'submission_id'],
        unique=False,
    )
    op.create_index('ix_problem_lesson_id', 'problem', ['lesson_id'], unique=False)
    op.create_index('ix_lesson_course_id', 'lesson', ['course_id'], unique=False)
    op.create_index('ix_testcase_problem_id', 'testcase', ['problem_id'], unique=False)
    op.create_index('ix_course_created_by', 'course', ['created_by'], unique=False)
    op.create_index(
        'ix_enrollment_student_id', 'enrollment', ['student_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_enrollment_student_id', table_name='enrollment')
    op.drop_index('ix_course_created_by', table_name='course')
    op.drop_index('ix_testcase_problem_id', table_name='testcase')
    op.drop_index('ix_lesson_course_id', table_name='lesson')
    op.drop_index('ix_problem_lesson_id', table_name='problem')
    op.drop_index('ix_submission_student_submitted', table_name='submission')
    op.drop_index('ix_submission_problem_student', table_name='submission')
