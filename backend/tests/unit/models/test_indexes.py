"""Index trên bảng submission và các FK nằm trên đường JOIN.

Test chạy trên SQLite với ``create_all`` (không chạy migration) nên index phải
được khai báo trong model; Alembic migration được kiểm bằng ``alembic check``.
"""

import pytest
from sqlalchemy import inspect

from app.models import entities

EXPECTED_INDEXES = [
    (
        entities.Submission,
        "ix_submission_problem_student",
        ["problem_id", "student_id"],
    ),
    (
        entities.Submission,
        "ix_submission_student_submitted",
        ["student_id", "submitted_datetime", "submission_id"],
    ),
    (entities.Problem, "ix_problem_lesson_id", ["lesson_id"]),
    (entities.Lesson, "ix_lesson_course_id", ["course_id"]),
    (entities.Testcase, "ix_testcase_problem_id", ["problem_id"]),
    (entities.Course, "ix_course_created_by", ["created_by"]),
    (entities.Enrollment, "ix_enrollment_student_id", ["student_id"]),
]


@pytest.mark.parametrize(("model", "name", "columns"), EXPECTED_INDEXES)
def test_model_declares_index(model, name, columns):
    declared = {ix.name: [c.name for c in ix.columns] for ix in model.__table__.indexes}

    assert declared[name] == columns


@pytest.mark.parametrize(("model", "name", "columns"), EXPECTED_INDEXES)
def test_index_is_created_in_database(engine, model, name, columns):
    created = {
        ix["name"]: ix["column_names"]
        for ix in inspect(engine).get_indexes(model.__tablename__)
    }

    assert created[name] == columns
