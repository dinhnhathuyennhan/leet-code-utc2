"""restore unique constraint on enrollment (course_id, student_id)

Revision ID: d712d1718327
Revises: b1c2d3e4f5a6
Create Date: 2026-11-20 12:00:00.000000

Migration e6f7a8b9c0d1 (user IDs to UUID) dropped and re-added
``enrollment.student_id``. Dropping the column silently dropped
``uq_enrollment_course_student`` (created in 0fe2fa7deee0), and it was never
recreated, so the database stopped enforcing "a student is enrolled in a
course at most once" even though ``Enrollment.__table_args__`` still declares
it.

While the constraint was missing, duplicate (course_id, student_id) rows could
be inserted. Before recreating the constraint this migration reports them and
resolves them as follows:

- Keep the row with the smallest ``enrollment_id`` for each pair and delete
  the other copies. ``enrollment`` has no columns besides the pair, and no
  table references ``enrollment_id``, so the extra copies carry no data.
- ``course.total_number_student`` is incremented once per enrollment row, so
  duplicates inflated it. Recount it from ``enrollment`` for the affected
  courses only.

Downgrade only drops the constraint; deleted duplicate rows are not restored.
"""

import logging
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d712d1718327"
down_revision: str | Sequence[str] | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONSTRAINT_NAME = "uq_enrollment_course_student"

logger = logging.getLogger(f"alembic.migration.{revision}")


def find_duplicate_enrollments(bind: sa.Connection) -> list[sa.Row]:
    """Return one row per duplicated pair: course_id, student_id, copies, kept_id."""
    return bind.execute(
        sa.text(
            """
            SELECT course_id, student_id, count(*) AS copies,
                   min(enrollment_id) AS kept_id
            FROM enrollment
            GROUP BY course_id, student_id
            HAVING count(*) > 1
            ORDER BY course_id, student_id
            """
        )
    ).all()


def remove_duplicate_enrollments(bind: sa.Connection) -> int:
    """Delete duplicate enrollments and recount affected courses.

    Returns the number of deleted rows.
    """
    duplicates = find_duplicate_enrollments(bind)
    if not duplicates:
        return 0

    for course_id, student_id, copies, kept_id in duplicates:
        logger.warning(
            "Duplicate enrollment: course_id=%r student_id=%s copies=%d, "
            "keeping enrollment_id=%d",
            course_id,
            student_id,
            copies,
            kept_id,
        )

    deleted = bind.execute(
        sa.text(
            """
            DELETE FROM enrollment
            WHERE enrollment_id NOT IN (
                SELECT min(enrollment_id) FROM enrollment
                GROUP BY course_id, student_id
            )
            """
        )
    ).rowcount

    affected_courses = sorted({row.course_id for row in duplicates})
    bind.execute(
        sa.text(
            """
            UPDATE course
            SET total_number_student = (
                SELECT count(*) FROM enrollment AS e
                WHERE e.course_id = course.course_id
            )
            WHERE course_id IN :course_ids
            """
        ).bindparams(sa.bindparam("course_ids", expanding=True)),
        {"course_ids": affected_courses},
    )

    logger.warning(
        "Deleted %d duplicate enrollment row(s) across %d pair(s); recounted "
        "total_number_student for course(s): %s",
        deleted,
        len(duplicates),
        ", ".join(affected_courses),
    )
    return deleted


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Block concurrent inserts so no new duplicate slips in between the
        # duplicate report, the DELETE and the constraint creation.
        bind.execute(sa.text("LOCK TABLE enrollment IN SHARE ROW EXCLUSIVE MODE"))
    remove_duplicate_enrollments(bind)
    # batch_alter_table runs a plain ALTER TABLE on PostgreSQL; it also lets
    # the migration run on SQLite in unit tests.
    with op.batch_alter_table("enrollment") as batch_op:
        batch_op.create_unique_constraint(CONSTRAINT_NAME, ["course_id", "student_id"])


def downgrade() -> None:
    with op.batch_alter_table("enrollment") as batch_op:
        batch_op.drop_constraint(CONSTRAINT_NAME, type_="unique")
