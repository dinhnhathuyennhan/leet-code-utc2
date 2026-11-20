"""best_grade_scores: chọn bài nộp tốt nhất mỗi (sinh viên, bài) ngay trong SQL."""

from datetime import datetime

import pytest
from sqlmodel import Session

from app.core.dependencies import Role
from app.core.utils.datetime_utils import VN_TZ
from app.models.entities import Problem, Submission, User
from app.modules.courses import grade_service
from tests.support.fixtures.builders import (
    make_course,
    make_lesson,
    make_problem,
    make_submission,
    make_user,
)
from tests.support.query_counter import count_queries


@pytest.fixture
def teacher(session: Session) -> User:
    return make_user(session, "GV001", Role.TEACHER)


@pytest.fixture
def student_a(session: Session) -> User:
    return make_user(session, "6451000001", Role.STUDENT)


@pytest.fixture
def student_b(session: Session) -> User:
    return make_user(session, "6451000002", Role.STUDENT)


@pytest.fixture
def problems(session: Session, teacher: User) -> tuple[Problem, Problem]:
    lesson = make_lesson(session, make_course(session, teacher, "CS101"))
    return make_problem(session, lesson, title="P1"), make_problem(session, lesson, title="P2")


def _submit(session, problem, student, *, passed=0, day=10, manual=None, feedback=None, **kwargs) -> Submission:
    submission = make_submission(session, problem, student, passed_count=passed, **kwargs)
    submission.submitted_datetime = datetime(2026, 1, day, tzinfo=VN_TZ)
    submission.manual_score = manual
    submission.feedback = feedback
    session.flush()
    return submission


class TestBestGradeScores:
    def test_manual_score_beats_higher_passed_count(self, session, problems, student_a):
        p1, _ = problems
        _submit(session, p1, student_a, passed=9, day=12)
        graded = _submit(session, p1, student_a, passed=1, day=5, manual=0.0, feedback="ok")

        best = grade_service.best_grade_scores(session, [p1.problem_id])

        row = best[(student_a.user_id, p1.problem_id)]
        assert row.submission_id == graded.submission_id
        assert row.manual_score == 0.0
        assert row.feedback == "ok"

    def test_higher_passed_count_wins_over_later_submission(self, session, problems, student_a):
        p1, _ = problems
        better = _submit(session, p1, student_a, passed=5, day=2)
        _submit(session, p1, student_a, passed=3, day=20)

        best = grade_service.best_grade_scores(session, [p1.problem_id])

        assert best[(student_a.user_id, p1.problem_id)].submission_id == better.submission_id

    def test_equal_passed_count_later_datetime_wins(self, session, problems, student_a):
        p1, _ = problems
        _submit(session, p1, student_a, passed=4, day=3)
        later = _submit(session, p1, student_a, passed=4, day=8)
        _submit(session, p1, student_a, passed=4, day=1)

        best = grade_service.best_grade_scores(session, [p1.problem_id])

        assert best[(student_a.user_id, p1.problem_id)].submission_id == later.submission_id

    def test_equal_passed_count_and_datetime_higher_id_wins(self, session, problems, student_a):
        p1, _ = problems
        _submit(session, p1, student_a, passed=4, day=3)
        newest = _submit(session, p1, student_a, passed=4, day=3)

        best = grade_service.best_grade_scores(session, [p1.problem_id])

        assert best[(student_a.user_id, p1.problem_id)].submission_id == newest.submission_id

    def test_among_manual_scores_higher_passed_count_wins(self, session, problems, student_a):
        p1, _ = problems
        _submit(session, p1, student_a, passed=1, day=9, manual=5.0)
        winner = _submit(session, p1, student_a, passed=3, day=1, manual=2.0)

        best = grade_service.best_grade_scores(session, [p1.problem_id])

        assert best[(student_a.user_id, p1.problem_id)].submission_id == winner.submission_id

    def test_exposes_attributes_read_by_build_grade_rows(self, session, problems, student_a):
        p1, _ = problems
        sub = _submit(session, p1, student_a, passed=2, status="accepted")

        row = grade_service.best_grade_scores(session, [p1.problem_id])[(student_a.user_id, p1.problem_id)]

        assert row.submission_id == sub.submission_id
        assert row.passed_count == 2
        assert row.manual_score is None
        assert row.feedback is None
        assert row.status == "accepted"
        assert row.submitted_datetime == datetime(2026, 1, 10, tzinfo=VN_TZ)

    def test_several_pairs_at_once(self, session, problems, student_a, student_b):
        p1, p2 = problems
        a1 = _submit(session, p1, student_a, passed=2)
        _submit(session, p1, student_a, passed=1)
        a2 = _submit(session, p2, student_a, passed=3)
        b1 = _submit(session, p1, student_b, passed=1)

        best = grade_service.best_grade_scores(session, [p1.problem_id, p2.problem_id])

        assert {k: v.submission_id for k, v in best.items()} == {
            (student_a.user_id, p1.problem_id): a1.submission_id,
            (student_a.user_id, p2.problem_id): a2.submission_id,
            (student_b.user_id, p1.problem_id): b1.submission_id,
        }

    def test_problem_filter_excludes_other_problems(self, session, problems, student_a):
        p1, p2 = problems
        _submit(session, p1, student_a, passed=2)
        _submit(session, p2, student_a, passed=2)

        best = grade_service.best_grade_scores(session, [p2.problem_id])

        assert list(best) == [(student_a.user_id, p2.problem_id)]

    def test_student_filter_none_vs_subset(self, session, problems, student_a, student_b):
        p1, _ = problems
        _submit(session, p1, student_a, passed=2)
        _submit(session, p1, student_b, passed=1)

        everyone = grade_service.best_grade_scores(session, [p1.problem_id], None)
        only_b = grade_service.best_grade_scores(session, [p1.problem_id], [student_b.user_id])

        assert {sid for sid, _ in everyone} == {student_a.user_id, student_b.user_id}
        assert list(only_b) == [(student_b.user_id, p1.problem_id)]

    def test_empty_student_ids_returns_empty_without_query(self, engine, session, problems, student_a):
        p1, _ = problems
        _submit(session, p1, student_a, passed=2)
        session.commit()
        problem_id = p1.problem_id

        with count_queries(engine) as queries:
            assert grade_service.best_grade_scores(session, [problem_id], []) == {}

        assert queries.count == 0

    def test_empty_problem_ids_returns_empty_without_query(self, engine, session, student_a):
        with count_queries(engine) as queries:
            assert grade_service.best_grade_scores(session, [], [student_a.user_id]) == {}
            assert grade_service.best_grade_scores(session, []) == {}

        assert queries.count == 0

    def test_no_submissions_returns_empty(self, session, problems):
        p1, _ = problems

        assert grade_service.best_grade_scores(session, [p1.problem_id]) == {}

    def test_single_statement_without_heavy_columns(self, engine, session, problems, student_a):
        p1, _ = problems
        _submit(session, p1, student_a, passed=2)
        session.commit()
        problem_id = p1.problem_id

        with count_queries(engine) as queries:
            grade_service.best_grade_scores(session, [problem_id])

        assert queries.count == 1
        assert "submitted_code" not in queries.statements[0]
        assert "testcase_results" not in queries.statements[0]
