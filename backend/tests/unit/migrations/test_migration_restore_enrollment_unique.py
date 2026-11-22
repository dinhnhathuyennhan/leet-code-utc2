"""Tests for migration d712d1718327 (restore uq_enrollment_course_student).

The migration runs here against an in-memory SQLite database with minimal
``course``/``enrollment`` tables that lack the unique constraint, the same
state e6f7a8b9c0d1 left PostgreSQL in.
"""

import importlib.util
import io
import logging
import uuid
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlmodel.pool import StaticPool

from app.models import Enrollment

BACKEND_DIR = Path(__file__).resolve().parents[3]
MIGRATION_PATH = (
    BACKEND_DIR
    / "alembic"
    / "versions"
    / "d712d1718327_restore_enrollment_unique_constraint.py"
)

S1 = str(uuid.UUID(int=1))
S2 = str(uuid.UUID(int=2))


def _load_migration():
    spec = importlib.util.spec_from_file_location(
        "migration_d712d1718327", MIGRATION_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


migration = _load_migration()


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE course (course_id VARCHAR(50) PRIMARY KEY, "
                "total_number_student INTEGER NOT NULL DEFAULT 0)"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE enrollment (enrollment_id INTEGER PRIMARY KEY, "
                "course_id VARCHAR(50) NOT NULL, student_id CHAR(36) NOT NULL)"
            )
        )
    yield engine
    engine.dispose()


def _seed(engine, courses, enrollments):
    with engine.begin() as conn:
        for course_id, total in courses:
            conn.execute(
                text("INSERT INTO course VALUES (:c, :t)"), {"c": course_id, "t": total}
            )
        for enrollment_id, course_id, student_id in enrollments:
            conn.execute(
                text("INSERT INTO enrollment VALUES (:e, :c, :s)"),
                {"e": enrollment_id, "c": course_id, "s": student_id},
            )


def _run(engine, step):
    with engine.begin() as conn, Operations.context(MigrationContext.configure(conn)):
        step()


def _enrollments(engine):
    with engine.connect() as conn:
        return conn.execute(
            text(
                "SELECT enrollment_id, course_id, student_id FROM enrollment ORDER BY 1"
            )
        ).all()


def _totals(engine):
    with engine.connect() as conn:
        return dict(
            conn.execute(
                text("SELECT course_id, total_number_student FROM course")
            ).all()
        )


def _insert_enrollment(engine, enrollment_id, course_id, student_id):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO enrollment VALUES (:e, :c, :s)"),
            {"e": enrollment_id, "c": course_id, "s": student_id},
        )


def test_upgrade_without_duplicates_keeps_data_and_enforces_uniqueness(engine, caplog):
    # A1's counter drifted for an unrelated reason; it must not be touched.
    _seed(engine, [("A1", 9), ("B1", 1)], [(1, "A1", S1), (2, "A1", S2), (3, "B1", S1)])

    with caplog.at_level(logging.WARNING):
        _run(engine, migration.upgrade)

    assert _enrollments(engine) == [(1, "A1", S1), (2, "A1", S2), (3, "B1", S1)]
    assert _totals(engine) == {"A1": 9, "B1": 1}
    assert not caplog.records
    with pytest.raises(IntegrityError):
        _insert_enrollment(engine, 4, "A1", S1)


def test_upgrade_removes_duplicates_keeping_lowest_id_and_recounts(engine, caplog):
    _seed(
        engine,
        [("A1", 4), ("B1", 7)],
        [
            (5, "A1", S1),
            (2, "A1", S1),
            (9, "A1", S1),
            (3, "A1", S2),
            (4, "B1", S1),
        ],
    )

    with caplog.at_level(logging.WARNING):
        _run(engine, migration.upgrade)

    assert _enrollments(engine) == [(2, "A1", S1), (3, "A1", S2), (4, "B1", S1)]
    # Only the course that had duplicates is recounted.
    assert _totals(engine) == {"A1": 2, "B1": 7}
    messages = [record.getMessage() for record in caplog.records]
    assert any("copies=3" in m and "keeping enrollment_id=2" in m for m in messages)
    assert any(
        "Deleted 2 duplicate enrollment row(s) across 1 pair(s)" in m for m in messages
    )
    with pytest.raises(IntegrityError):
        _insert_enrollment(engine, 10, "A1", S2)


def test_upgrade_recounts_every_course_with_duplicates(engine):
    _seed(
        engine,
        [("A1", 3), ("B1", 2), ("C1", 0)],
        [(1, "A1", S1), (2, "A1", S1), (3, "A1", S1), (4, "B1", S2), (5, "B1", S2)],
    )

    _run(engine, migration.upgrade)

    assert _enrollments(engine) == [(1, "A1", S1), (4, "B1", S2)]
    assert _totals(engine) == {"A1": 1, "B1": 1, "C1": 0}


def test_upgrade_on_empty_enrollment_table(engine):
    _run(engine, migration.upgrade)

    assert _enrollments(engine) == []
    _insert_enrollment(engine, 1, "A1", S1)
    with pytest.raises(IntegrityError):
        _insert_enrollment(engine, 2, "A1", S1)


def test_find_duplicate_enrollments_reports_each_pair(engine):
    _seed(
        engine,
        [("A1", 0)],
        [(7, "A1", S2), (3, "A1", S2), (1, "A1", S1), (4, "A1", S1), (5, "A1", S1)],
    )

    with engine.connect() as conn:
        rows = [tuple(row) for row in migration.find_duplicate_enrollments(conn)]

    assert rows == [("A1", S1, 3, 1), ("A1", S2, 2, 3)]


def test_downgrade_drops_constraint(engine):
    _seed(engine, [("A1", 1)], [(1, "A1", S1)])
    _run(engine, migration.upgrade)

    _run(engine, migration.downgrade)

    _insert_enrollment(engine, 2, "A1", S1)
    assert _enrollments(engine) == [(1, "A1", S1), (2, "A1", S1)]


def test_constraint_name_matches_model():
    names = {constraint.name for constraint in Enrollment.__table__.constraints}
    assert migration.CONSTRAINT_NAME in names


def test_migration_history_has_single_head():
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    heads = ScriptDirectory.from_config(config).get_heads()
    assert len(heads) == 1, f"Multiple Alembic heads, add a merge or rebase: {heads}"


def _offline_postgres_sql(step) -> str:
    buffer = io.StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql", opts={"as_sql": True, "output_buffer": buffer}
    )
    with Operations.context(context):
        step()
    return buffer.getvalue()


def test_upgrade_on_postgres_locks_table_and_alters_in_place(monkeypatch):
    # Offline mode cannot run the duplicate queries, which are covered above.
    monkeypatch.setattr(migration, "remove_duplicate_enrollments", lambda bind: 0)

    sql = _offline_postgres_sql(migration.upgrade)

    assert "LOCK TABLE enrollment IN SHARE ROW EXCLUSIVE MODE" in sql
    assert (
        "ALTER TABLE enrollment ADD CONSTRAINT uq_enrollment_course_student "
        "UNIQUE (course_id, student_id)" in sql
    )
    # batch_alter_table must not fall back to recreating the table on PostgreSQL.
    assert "CREATE TABLE" not in sql
    assert sql.index("LOCK TABLE") < sql.index("ALTER TABLE")


def test_downgrade_on_postgres_drops_constraint_in_place():
    sql = _offline_postgres_sql(migration.downgrade)

    assert "ALTER TABLE enrollment DROP CONSTRAINT uq_enrollment_course_student" in sql
    assert "CREATE TABLE" not in sql
