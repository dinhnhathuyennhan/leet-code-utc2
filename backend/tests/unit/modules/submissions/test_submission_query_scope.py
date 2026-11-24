"""Phạm vi truy vấn của module bài nộp phía giáo viên/admin: quyền xem, bộ lọc, thứ tự, số câu SQL."""

from datetime import datetime

import pytest
from sqlmodel import Session

from app.core.dependencies import Role
from app.core.exceptions import NotFoundError
from app.core.utils.datetime_utils import VN_TZ
from app.models.entities import Course, Lesson, Problem, Submission, User
from app.modules.submissions.schemas import SubmissionUpdateRequest
from app.modules.submissions.service import (
    get_submission_detail,
    list_pending_submissions,
    update_submission,
)
from app.modules.submissions.judge0 import service as judge_service
from tests.support.fixtures.builders import (
    make_course,
    make_lesson,
    make_problem,
    make_submission,
    make_user,
)
from tests.support.query_counter import count_queries

pytest_plugins = ("tests.support.fixtures.submission_fixtures",)


@pytest.fixture
def other_teacher(session: Session) -> User:
    return make_user(session, "GV002", Role.TEACHER)


@pytest.fixture
def admin(session: Session) -> User:
    return make_user(session, "ADMIN_SCOPE", Role.ADMIN)


@pytest.fixture
def foreign_submission(session: Session, other_teacher: User) -> Submission:
    """Bài nộp thuộc khoá của giáo viên khác (GV002)."""
    course = make_course(session, other_teacher, "CS202")
    problem = make_problem(session, make_lesson(session, course))
    student = make_user(session, "SV900", Role.STUDENT)
    return make_submission(session, problem, student, status="wrong_answer")


class TestVisibilityScope:
    def test_teacher_cannot_get_detail_of_other_teachers_submission(
        self, session: Session, submission_teacher: User, foreign_submission: Submission
    ):
        with pytest.raises(NotFoundError, match="Không tìm thấy bài nộp"):
            get_submission_detail(session, foreign_submission.submission_id, submission_teacher)

    def test_teacher_cannot_update_other_teachers_submission(
        self, session: Session, submission_teacher: User, foreign_submission: Submission
    ):
        with pytest.raises(NotFoundError, match="Không tìm thấy bài nộp"):
            update_submission(
                session,
                foreign_submission.submission_id,
                SubmissionUpdateRequest(feedback="hack"),
                submission_teacher,
            )

        session.expire_all()
        assert session.get(Submission, foreign_submission.submission_id).feedback is None

    def test_teacher_cannot_regrade_other_teachers_submission(
        self, session: Session, submission_teacher: User, foreign_submission: Submission
    ):
        foreign_submission.status = "internal_error"
        session.add(foreign_submission)
        session.commit()

        with pytest.raises(NotFoundError, match="Không tìm thấy bài nộp"):
            judge_service.regrade(session, foreign_submission.submission_id, submission_teacher)

        session.refresh(foreign_submission)
        assert foreign_submission.status == "internal_error"

    def test_unknown_submission_id_is_not_found(self, session: Session, submission_teacher: User):
        with pytest.raises(NotFoundError, match="Không tìm thấy bài nộp"):
            get_submission_detail(session, 999999, submission_teacher)

    def test_teacher_sees_own_submission(
        self, session: Session, submission_teacher: User, pending_error_submission: Submission
    ):
        detail = get_submission_detail(
            session, pending_error_submission.submission_id, submission_teacher
        )

        assert detail.id == pending_error_submission.submission_id
        assert detail.submitted_code == pending_error_submission.submitted_code
        assert detail.course_code == "CS101"

    def test_admin_sees_every_submission(
        self,
        session: Session,
        admin: User,
        pending_error_submission: Submission,
        foreign_submission: Submission,
    ):
        for submission in (pending_error_submission, foreign_submission):
            assert get_submission_detail(session, submission.submission_id, admin).id == (
                submission.submission_id
            )
        assert list_pending_submissions(session, admin).total == 2

    def test_update_missing_submission_is_not_found(
        self, session: Session, submission_teacher: User
    ):
        with pytest.raises(NotFoundError):
            update_submission(
                session, 999999, SubmissionUpdateRequest(feedback="x"), submission_teacher
            )

    def test_update_feedback_keeps_status_and_returns_full_detail(
        self, session: Session, submission_teacher: User, pending_error_submission: Submission
    ):
        result = update_submission(
            session,
            pending_error_submission.submission_id,
            SubmissionUpdateRequest(feedback="  Tốt  "),
            submission_teacher,
        )

        assert result.status == pending_error_submission.status
        assert result.feedback == "Tốt"
        assert result.submitted_code == pending_error_submission.submitted_code

    def test_list_scopes_to_own_courses_and_teacher_without_courses_sees_nothing(
        self,
        session: Session,
        submission_teacher: User,
        other_teacher: User,
        pending_error_submission: Submission,
        foreign_submission: Submission,
    ):
        mine = list_pending_submissions(session, submission_teacher)
        theirs = list_pending_submissions(session, other_teacher)
        nobody = list_pending_submissions(session, make_user(session, "GV003", Role.TEACHER))

        assert [item.id for item in mine.items] == [pending_error_submission.submission_id]
        assert [item.id for item in theirs.items] == [foreign_submission.submission_id]
        assert (nobody.items, nobody.total, nobody.counts["all"]) == ([], 0, 0)


class TestScopeFailsClosedForNonTeacherRoles:
    """Vai trò không phải ADMIN/TEACHER (kể cả role lạ) không được thấy bài nộp của khoá người khác."""

    @pytest.fixture(params=[Role.STUDENT, 99], ids=["student", "undefined_role"])
    def outsider(self, session: Session, request) -> User:
        return make_user(session, "OUT001", request.param)

    def test_list_returns_nothing(
        self, session: Session, outsider: User, foreign_submission: Submission
    ):
        result = list_pending_submissions(session, outsider, include_graded=True)

        assert (result.items, result.total) == ([], 0)

    def test_detail_is_not_found(
        self, session: Session, outsider: User, foreign_submission: Submission
    ):
        with pytest.raises(NotFoundError, match="Không tìm thấy bài nộp"):
            get_submission_detail(session, foreign_submission.submission_id, outsider)

    def test_update_is_not_found_and_leaves_row_unchanged(
        self, session: Session, outsider: User, foreign_submission: Submission
    ):
        with pytest.raises(NotFoundError, match="Không tìm thấy bài nộp"):
            update_submission(
                session,
                foreign_submission.submission_id,
                SubmissionUpdateRequest(feedback="hack", manual_score=10),
                outsider,
            )

        session.expire_all()
        row = session.get(Submission, foreign_submission.submission_id)
        assert row.status == "wrong_answer"
        assert row.feedback is None


@pytest.fixture
def two_lessons(session: Session, submission_course: Course, submission_lesson: Lesson):
    """Thêm buổi học + bài tập thứ hai trong cùng khoá."""
    lesson2 = make_lesson(session, submission_course, "Lesson 2", lesson_number=2)
    problem2 = make_problem(session, lesson2, title="Three Sum", report="THREE_SUM")
    return lesson2, problem2


class TestListFilters:
    def test_filters_by_course_lesson_and_problem(
        self,
        session: Session,
        submission_teacher: User,
        submission_student: User,
        submission_problem: Problem,
        submission_lesson: Lesson,
        two_lessons,
    ):
        lesson2, problem2 = two_lessons
        course2 = make_course(session, submission_teacher, "CS102")
        problem3 = make_problem(session, make_lesson(session, course2), title="Four Sum")
        s1 = make_submission(session, submission_problem, submission_student)
        s2 = make_submission(session, problem2, submission_student)
        s3 = make_submission(session, problem3, submission_student)

        def ids(**kwargs):
            result = list_pending_submissions(session, submission_teacher, **kwargs)
            return {item.id for item in result.items}, result

        assert ids()[0] == {s1.submission_id, s2.submission_id, s3.submission_id}
        assert ids(course_id="CS101")[0] == {s1.submission_id, s2.submission_id}
        assert ids(course_id="CS102")[0] == {s3.submission_id}
        assert ids(course_id="NOPE")[0] == set()
        assert ids(lesson_id=lesson2.lesson_id)[0] == {s2.submission_id}
        assert ids(lesson_id=submission_lesson.lesson_id)[0] == {s1.submission_id}
        assert ids(problem_id=problem3.problem_id)[0] == {s3.submission_id}
        assert ids(course_id="CS101", problem_id=problem3.problem_id)[0] == set()
        scoped = ids(course_id="CS102")[1]
        assert scoped.total == 1 and scoped.counts["all"] == 1

    def test_include_graded_adds_accepted(
        self,
        session: Session,
        submission_teacher: User,
        submission_student: User,
        submission_problem: Problem,
    ):
        make_submission(session, submission_problem, submission_student, status="accepted")
        make_submission(session, submission_problem, submission_student, status="pending")

        hidden = list_pending_submissions(session, submission_teacher)
        shown = list_pending_submissions(session, submission_teacher, include_graded=True)

        assert [item.status for item in hidden.items] == ["pending"]
        assert shown.total == 2
        assert shown.counts["graded"] == 1 and shown.counts["ungraded"] == 1

    def test_limit_truncates_items_but_not_total_or_counts(
        self,
        session: Session,
        submission_teacher: User,
        submission_student: User,
        submission_problem: Problem,
    ):
        for _ in range(3):
            make_submission(session, submission_problem, submission_student, status="pending")

        result = list_pending_submissions(session, submission_teacher, limit=2)
        floor = list_pending_submissions(session, submission_teacher, limit=0)

        assert len(result.items) == 2
        assert result.total == 3
        assert result.counts["all"] == 3 and result.counts["pending"] == 3
        assert len(floor.items) == 1  # limit tối thiểu là 1

    def test_orders_by_datetime_desc_then_id_desc(
        self,
        session: Session,
        submission_teacher: User,
        submission_student: User,
        submission_problem: Problem,
    ):
        old = make_submission(session, submission_problem, submission_student)
        tie_a = make_submission(session, submission_problem, submission_student)
        tie_b = make_submission(session, submission_problem, submission_student)
        newest = make_submission(session, submission_problem, submission_student)
        old.submitted_datetime = datetime(2026, 1, 1, tzinfo=VN_TZ)
        tie_a.submitted_datetime = tie_b.submitted_datetime = datetime(2026, 2, 1, tzinfo=VN_TZ)
        newest.submitted_datetime = datetime(2026, 3, 1, tzinfo=VN_TZ)
        session.flush()

        result = list_pending_submissions(session, submission_teacher)

        assert [item.id for item in result.items] == [
            newest.submission_id,
            tie_b.submission_id,
            tie_a.submission_id,
            old.submission_id,
        ]

    def test_status_with_different_case_is_still_listed_and_counted(
        self,
        session: Session,
        submission_teacher: User,
        submission_student: User,
        submission_problem: Problem,
    ):
        make_submission(session, submission_problem, submission_student, status="Wrong_Answer")
        make_submission(session, submission_problem, submission_student, status="PENDING")
        make_submission(session, submission_problem, submission_student, status="Accepted")

        result = list_pending_submissions(session, submission_teacher)
        graded = list_pending_submissions(session, submission_teacher, include_graded=True)

        assert {item.status for item in result.items} == {"Wrong_Answer", "PENDING"}
        assert result.counts["wrong_answer"] == 1 and result.counts["pending"] == 1
        assert {item.judge_kind for item in result.items} == {"wrong_answer", "pending"}
        assert graded.total == 3 and graded.counts["graded"] == 1

    def test_search_still_matches_vietnamese_text_case_insensitively(
        self,
        session: Session,
        submission_teacher: User,
        submission_problem: Problem,
        pending_error_submission: Submission,
    ):
        submission_problem.title = "BÀI TẬP Đặc Biệt"
        session.add(submission_problem)
        session.flush()

        assert list_pending_submissions(session, submission_teacher, search="đặc biệt").total == 1
        assert list_pending_submissions(session, submission_teacher, search="  zzz ").total == 0


class TestQueryShape:
    def test_pending_list_is_one_statement_without_heavy_columns(
        self,
        engine,
        session: Session,
        submission_teacher: User,
        pending_error_submission: Submission,
    ):
        session.commit()
        session.expire_all()
        session.refresh(submission_teacher)  # tránh đếm lần nạp lại người gọi

        with count_queries(engine) as queries:
            result = list_pending_submissions(session, submission_teacher, include_graded=True)

        assert result.total == 1
        assert queries.count == 1
        sql = queries.statements[0]
        for column in ("submitted_code", "testcase_results", "judge_tokens", "hashed_password"):
            assert column not in sql

    def test_detail_filters_by_id_in_a_bounded_number_of_statements(
        self,
        engine,
        session: Session,
        submission_teacher: User,
        pending_error_submission: Submission,
    ):
        session.commit()
        session.expire_all()
        submission_id = pending_error_submission.submission_id
        session.refresh(submission_teacher)  # tránh đếm lần nạp lại người gọi

        with count_queries(engine) as queries:
            get_submission_detail(session, submission_id, submission_teacher)

        assert queries.count == 2  # bài nộp + testcase
        assert "submission.submission_id = ?" in queries.statements[0]
        assert "course.created_by = ?" in queries.statements[0]

    def test_admin_detail_query_is_not_scoped_by_course_owner(
        self,
        engine,
        session: Session,
        admin: User,
        pending_error_submission: Submission,
    ):
        session.commit()
        submission_id = pending_error_submission.submission_id
        session.refresh(admin)

        with count_queries(engine) as queries:
            get_submission_detail(session, submission_id, admin)

        assert "course.created_by = ?" not in queries.statements[0]
