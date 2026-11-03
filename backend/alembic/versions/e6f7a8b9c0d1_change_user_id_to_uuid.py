"""change user primary and foreign keys to UUID

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-10-28

Existing student user_id values are copied to student_code only when they are
exactly ten ASCII digits. If any student still has no valid student_code, this
migration stops before changing the primary or foreign keys so the old IDs can
be reconciled manually first.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e6f7a8b9c0d1"
down_revision: str | Sequence[str] | None = "d5e6f7a8b9c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("UUID migration only supports PostgreSQL")

    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # Legacy student IDs were MSSVs. Backfill missing or malformed student_code
    # values from the old ID when that ID is still a valid 10-digit MSSV.
    op.execute(
        sa.text(
            """
            UPDATE "user"
            SET student_code = user_id
            WHERE role_id = 3
              AND (student_code IS NULL OR student_code !~ '^[0-9]{10}$')
              AND user_id ~ '^[0-9]{10}$'
            """
        )
    )
    invalid_students = bind.execute(
        sa.text(
            'SELECT user_id, student_code FROM "user" '
            "WHERE role_id = 3 AND (student_code IS NULL "
            "OR student_code !~ '^[0-9]{10}$')"
        )
    ).all()
    if invalid_students:
        examples = ", ".join(
            f"user_id={user_id!r}, student_code={student_code!r}"
            for user_id, student_code in invalid_students[:10]
        )
        raise RuntimeError(
            f"{len(invalid_students)} student account(s) still have no valid "
            "10-digit student_code after backfilling from legacy user_id. "
            f"Examples: {examples}. Reconcile these records, then rerun this migration."
        )

    uuid_type = postgresql.UUID(as_uuid=True)
    op.add_column("user", sa.Column("new_user_id", uuid_type, nullable=True))
    op.add_column("course", sa.Column("new_created_by", uuid_type, nullable=True))
    op.add_column("enrollment", sa.Column("new_student_id", uuid_type, nullable=True))
    op.add_column("submission", sa.Column("new_student_id", uuid_type, nullable=True))

    op.execute('UPDATE "user" SET new_user_id = gen_random_uuid()')
    op.execute(
        """
        UPDATE course AS c
        SET new_created_by = u.new_user_id
        FROM "user" AS u
        WHERE c.created_by = u.user_id
        """
    )
    op.execute(
        """
        UPDATE enrollment AS e
        SET new_student_id = u.new_user_id
        FROM "user" AS u
        WHERE e.student_id = u.user_id
        """
    )
    op.execute(
        """
        UPDATE submission AS s
        SET new_student_id = u.new_user_id
        FROM "user" AS u
        WHERE s.student_id = u.user_id
        """
    )

    # Check every replacement key was populated before dropping the old IDs.
    # This gives a targeted failure if legacy FK data is inconsistent.
    unmapped = {
        f"{table}.{column}": bind.execute(
            sa.text(f'SELECT count(*) FROM "{table}" WHERE "{column}" IS NULL')
        ).scalar_one()
        for table, column in (
            ("user", "new_user_id"),
            ("course", "new_created_by"),
            ("enrollment", "new_student_id"),
            ("submission", "new_student_id"),
        )
    }
    unmapped = {column: count for column, count in unmapped.items() if count}
    if unmapped:
        details = ", ".join(f"{column}: {count}" for column, count in unmapped.items())
        raise RuntimeError(
            "UUID backfill left unmapped rows; old IDs were not dropped. "
            f"Repair the referenced records and rerun the migration. Details: {details}"
        )

    for table, column in (
        ("user", "new_user_id"),
        ("course", "new_created_by"),
        ("enrollment", "new_student_id"),
        ("submission", "new_student_id"),
    ):
        op.alter_column(table, column, nullable=False)

    op.drop_constraint("course_created_by_fkey", "course", type_="foreignkey")
    op.drop_constraint("enrollment_student_id_fkey", "enrollment", type_="foreignkey")
    op.drop_constraint("submission_student_id_fkey", "submission", type_="foreignkey")
    op.drop_constraint("user_pkey", "user", type_="primary")

    op.drop_column("user", "user_id")
    op.drop_column("course", "created_by")
    op.drop_column("enrollment", "student_id")
    op.drop_column("submission", "student_id")

    op.alter_column("user", "new_user_id", new_column_name="user_id")
    op.alter_column("course", "new_created_by", new_column_name="created_by")
    op.alter_column("enrollment", "new_student_id", new_column_name="student_id")
    op.alter_column("submission", "new_student_id", new_column_name="student_id")

    op.create_primary_key("user_pkey", "user", ["user_id"])
    op.create_foreign_key(
        "course_created_by_fkey", "course", "user", ["created_by"], ["user_id"]
    )
    op.create_foreign_key(
        "enrollment_student_id_fkey",
        "enrollment",
        "user",
        ["student_id"],
        ["user_id"],
    )
    op.create_foreign_key(
        "submission_student_id_fkey",
        "submission",
        "user",
        ["student_id"],
        ["user_id"],
    )


def downgrade() -> None:
    raise NotImplementedError(
        "UUID-to-legacy-ID downgrade is not supported; restore a database backup instead."
    )
