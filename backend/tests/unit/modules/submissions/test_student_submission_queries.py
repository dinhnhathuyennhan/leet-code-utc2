"""Truy vấn phía sinh viên: lịch sử, chi tiết, kết quả polling và lưu token chấm."""

from datetime import datetime

import pytest
from sqlmodel import Session

from app.core.dependencies import Role
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.utils.datetime_utils import VN_TZ
from app.models.entities import Problem, Submission, User
from app.modules.submissions.judge0 import service as judge_service
from app.modules.submissions.student_service import (
    get_student_submission_detail,
    list_student_submissions,
)
from tests.support.fixtures.builders import (
    make_course,
    make_lesson,
    make_problem,
    make_submission,
    make_testcase,
    make_user,
)
from tests.support.query_counter import count_queries

pytest_plugins = ("tests.support.fixtures.submission_fixtures",)


@pytest.fixture
def other_student(session: Session) -> User:
    return make_user(session, "SV002", Role.STUDENT)


@pytest.fixture
def second_course_problem(session: Session, submission_teacher: User) -> Problem:
    course = make_course(session, submission_teacher, "CS102")
    return make_problem(session, make_lesson(session, course), title="Other Problem")


class TestListStudentSubmissions:
    def test_empty_history(self, session: Session, submission_student: User):
        result = list_student_submissions(session, submission_student)

        assert result.items == [] and result.total == 0
        assert result.counts == {
            "all": 0, "accepted": 0, "wrong_answer": 0, "compile_error": 0, "pending": 0,
        }

    def test_non_student_is_forbidden(self, session: Session, submission_teacher: User):
        with pytest.raises(ForbiddenError):
            list_student_submissions(session, submission_teacher)

    def test_filters_by_course_and_problem_and_counts_only_filtered_rows(
        self,
        session: Session,
        submission_student: User,
        other_student: User,
        submission_problem: Problem,
        second_course_problem: Problem,
    ):
        a = make_submission(session, submission_problem, submission_student, status="accepted")
        b = make_submission(session, submission_problem, submission_student, status="processing")
        c = make_submission(session, second_course_problem, submission_student, status="compile_error")
        make_submission(session, submission_problem, other_student, status="accepted")

        everything = list_student_submissions(session, submission_student)
        by_course = list_student_submissions(session, submission_student, course_id="CS101")
        by_problem = list_student_submissions(
            session, submission_student, problem_id=second_course_problem.problem_id
        )
        nothing = list_student_submissions(session, submission_student, course_id="NOPE")

        assert {i.id for i in everything.items} == {a.submission_id, b.submission_id, c.submission_id}
        assert everything.counts["all"] == 3
        assert {i.id for i in by_course.items} == {a.submission_id, b.submission_id}
        assert by_course.counts == {
            "all": 2, "accepted": 1, "wrong_answer": 0, "compile_error": 0, "pending": 1,
        }
        assert [i.id for i in by_problem.items] == [c.submission_id]
        assert by_problem.items[0].course_id == "CS102"
        assert nothing.total == 0

    def test_orders_newest_first_with_id_tiebreak(
        self, session: Session, submission_student: User, submission_problem: Problem
    ):
        old = make_submission(session, submission_problem, submission_student)
        tie_a = make_submission(session, submission_problem, submission_student)
        tie_b = make_submission(session, submission_problem, submission_student)
        old.submitted_datetime = datetime(2026, 1, 1, tzinfo=VN_TZ)
        tie_a.submitted_datetime = tie_b.submitted_datetime = datetime(2026, 2, 1, tzinfo=VN_TZ)
        session.flush()

        result = list_student_submissions(session, submission_student)

        assert [i.id for i in result.items] == [
            tie_b.submission_id, tie_a.submission_id, old.submission_id,
        ]

    def test_list_is_one_statement_without_heavy_columns(
        self,
        engine,
        session: Session,
        submission_student: User,
        pending_error_submission: Submission,
    ):
        session.commit()
        session.expire_all()
        session.refresh(submission_student)

        with count_queries(engine) as queries:
            result = list_student_submissions(session, submission_student)

        assert result.total == 1
        assert queries.count == 1
        for column in ("submitted_code", "testcase_results", "judge_tokens"):
            assert column not in queries.statements[0]


class TestStudentDetail:
    def test_other_students_submission_is_not_found(
        self, session: Session, other_student: User, pending_error_submission: Submission
    ):
        with pytest.raises(NotFoundError, match="Không tìm thấy bài nộp"):
            get_student_submission_detail(
                session, other_student, pending_error_submission.submission_id
            )

    def test_unknown_id_is_not_found(self, session: Session, submission_student: User):
        with pytest.raises(NotFoundError, match="Không tìm thấy bài nộp"):
            get_student_submission_detail(session, submission_student, 999999)

    def test_non_student_is_forbidden_before_lookup(
        self, session: Session, submission_teacher: User, pending_error_submission: Submission
    ):
        with pytest.raises(ForbiddenError):
            get_student_submission_detail(
                session, submission_teacher, pending_error_submission.submission_id
            )

    def test_owner_gets_full_detail_in_two_statements(
        self,
        engine,
        session: Session,
        submission_student: User,
        pending_error_submission: Submission,
    ):
        session.commit()
        session.expire_all()
        submission_id = pending_error_submission.submission_id
        session.refresh(submission_student)

        with count_queries(engine) as queries:
            detail = get_student_submission_detail(session, submission_student, submission_id)

        assert detail.submitted_code == "class Solution: pass"
        assert detail.course_id == "CS101"
        assert queries.count == 2
        assert "submission.submission_id = ?" in queries.statements[0]
        assert "submission.student_id = ?" in queries.statements[0]


class TestGetResult:
    def test_returns_status_and_counts_all_testcases(
        self,
        session: Session,
        submission_student: User,
        submission_problem: Problem,
    ):
        for _ in range(3):
            make_testcase(session, submission_problem)
        submission_problem.total_number_testcase = 99  # không được dùng cột này
        submission = make_submission(
            session, submission_problem, submission_student, status="wrong_answer", passed_count=2
        )
        submission.compile_output = "boom"
        session.flush()

        result = judge_service.get_result(session, submission.submission_id, submission_student)

        assert result.submission_id == submission.submission_id
        assert result.status == "wrong_answer"
        assert result.passed_count == 2
        assert result.total_testcases == 3
        assert result.compile_output == "boom"

    def test_other_students_submission_is_not_found(
        self, session: Session, other_student: User, pending_error_submission: Submission
    ):
        with pytest.raises(NotFoundError, match="Không tìm thấy bài nộp"):
            judge_service.get_result(
                session, pending_error_submission.submission_id, other_student
            )

    def test_missing_submission_is_not_found(self, session: Session, submission_student: User):
        with pytest.raises(NotFoundError, match="Không tìm thấy bài nộp"):
            judge_service.get_result(session, 999999, submission_student)

    def test_does_not_load_submitted_code(
        self,
        engine,
        session: Session,
        submission_student: User,
        pending_error_submission: Submission,
    ):
        session.commit()
        session.expire_all()
        submission_id = pending_error_submission.submission_id
        session.refresh(submission_student)

        with count_queries(engine) as queries:
            judge_service.get_result(session, submission_id, submission_student)

        assert queries.count == 2
        assert all("submitted_code" not in sql for sql in queries.statements)


class TestSaveTokens:
    def test_tokens_are_persisted_as_a_list(
        self, engine, session: Session, monkeypatch, pending_error_submission: Submission
    ):
        session.commit()
        monkeypatch.setattr(judge_service, "engine", engine)

        judge_service._save_tokens(pending_error_submission.submission_id, ["t1", "t2"])

        session.expire_all()
        assert session.get(Submission, pending_error_submission.submission_id).judge_tokens == [
            "t1", "t2",
        ]

    def test_unknown_submission_raises_submission_deleted(
        self, engine, session: Session, monkeypatch
    ):
        monkeypatch.setattr(judge_service, "engine", engine)

        with pytest.raises(judge_service._SubmissionDeleted):
            judge_service._save_tokens(999999, ["t1"])

        assert session.get(Submission, 999999) is None


class TestRegrade:
    def test_owner_regrades_internal_error_and_resets_fields(
        self,
        session: Session,
        submission_teacher: User,
        pending_error_submission: Submission,
        monkeypatch,
    ):
        queued: list[int] = []
        monkeypatch.setattr(judge_service.grading_queue, "enqueue", lambda sid, *a: queued.append(sid))
        submission = pending_error_submission
        submission.status = "internal_error"
        submission.passed_count = 2
        submission.compile_output = "x"
        submission.judge_tokens = ["t"]
        submission.testcase_results = [{"testcase_id": 1, "status": "accepted", "time": 0.1}]
        session.add(submission)
        session.commit()

        result = judge_service.regrade(session, submission.submission_id, submission_teacher)

        assert result.status == "pending"
        assert (result.passed_count, result.compile_output) == (0, None)
        assert (result.judge_tokens, result.testcase_results) == (None, None)
        assert queued == [submission.submission_id]

    def test_non_internal_error_conflicts(
        self,
        session: Session,
        submission_teacher: User,
        pending_error_submission: Submission,
    ):
        from app.core.exceptions import ConflictError

        with pytest.raises(ConflictError, match="Chỉ chấm lại được bài bị lỗi hệ thống chấm"):
            judge_service.regrade(session, pending_error_submission.submission_id, submission_teacher)
