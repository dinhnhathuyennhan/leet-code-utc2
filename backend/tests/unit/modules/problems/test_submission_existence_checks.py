"""Kiểm tra tồn tại bài nộp (_has_submissions / _assert_no_submissions) dùng LIMIT 1."""

import pytest
from sqlmodel import Session

from app.core.dependencies import Role
from app.core.exceptions import ConflictError
from app.modules.problems.service import _has_submissions
from app.modules.testcases.service import HAS_SUBMISSION_MESSAGE, _assert_no_submissions
from tests.support.fixtures.builders import (
    make_course,
    make_lesson,
    make_problem,
    make_submission,
    make_user,
)
from tests.support.query_counter import count_queries


@pytest.fixture
def problem(session: Session):
    teacher = make_user(session, "GV001", Role.TEACHER)
    return make_problem(session, make_lesson(session, make_course(session, teacher, "CS101")))


@pytest.fixture
def student(session: Session):
    return make_user(session, "6451000001", Role.STUDENT)


def _select_statements(queries) -> list[str]:
    return [s for s in queries.statements if s.lstrip().startswith("SELECT")]


class TestHasSubmissions:
    def test_false_without_submissions(self, session, problem):
        assert _has_submissions(session, problem.problem_id) is False

    def test_true_with_multiple_submissions_and_single_limited_query(
        self, engine, session, problem, student
    ):
        for _ in range(3):
            make_submission(session, problem, student)
        session.commit()
        problem_id = problem.problem_id

        with count_queries(engine) as queries:
            assert _has_submissions(session, problem_id) is True

        statements = _select_statements(queries)
        assert len(statements) == 1
        assert "LIMIT" in statements[0]

    def test_ignores_submissions_of_other_problems(self, session, problem, student):
        other = make_problem(session, None, title="Other")
        make_submission(session, other, student)

        assert _has_submissions(session, problem.problem_id) is False


class TestAssertNoSubmissions:
    def test_passes_without_submissions(self, session, problem):
        _assert_no_submissions(session, problem.problem_id)

    def test_raises_with_multiple_submissions_and_single_limited_query(
        self, engine, session, problem, student
    ):
        for _ in range(3):
            make_submission(session, problem, student)
        session.commit()
        problem_id = problem.problem_id

        with count_queries(engine) as queries, pytest.raises(
            ConflictError, match=HAS_SUBMISSION_MESSAGE
        ):
            _assert_no_submissions(session, problem_id)

        statements = _select_statements(queries)
        assert len(statements) == 1
        assert "LIMIT" in statements[0]
