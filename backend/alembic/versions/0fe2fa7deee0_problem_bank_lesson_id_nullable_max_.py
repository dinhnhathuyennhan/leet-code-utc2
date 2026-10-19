"""problem bank lesson_id nullable, max_length, unique enrollment

Revision ID: 0fe2fa7deee0
Revises: 18d97a502f6f
Create Date: 2026-10-15 08:03:15.014681

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fe2fa7deee0'
down_revision: Union[str, Sequence[str], None] = '18d97a502f6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint('uq_enrollment_course_student', 'enrollment', ['course_id', 'student_id'])
    op.alter_column('problem', 'lesson_id',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    has_bank_problems = op.get_bind().execute(
        sa.text("SELECT problem_id FROM problem WHERE lesson_id IS NULL LIMIT 1")
    ).first()
    if has_bank_problems is not None:
        raise RuntimeError(
            "Cannot make problem.lesson_id NOT NULL while Problem bank rows exist. "
            "Move or remove bank Problems explicitly before retrying this downgrade."
        )

    op.alter_column('problem', 'lesson_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_constraint('uq_enrollment_course_student', 'enrollment', type_='unique')
