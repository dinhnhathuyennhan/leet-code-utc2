"""Truy vấn của build_course_response / danh sách lớp / due-this-week / xoá lớp."""

from datetime import timedelta

import pytest
from sqlmodel import Session

from app.core.dependencies import Role
from app.core.exceptions import ConflictError
from app.core.utils.datetime_utils import today_vn
from app.models.entities import Course, Lesson, Problem, User
from app.modules.courses import service as course_service
from app.modules.courses.view import build_course_response
from tests.support.fixtures.builders import (
    make_course,
    make_enrollment,
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
def student(session: Session) -> User:
    return make_user(session, "6451000001", Role.STUDENT)


@pytest.fixture
def course(session: Session, teacher: User, student: User) -> Course:
    course = make_course(session, teacher, "CS101")
    make_enrollment(session, course, student)
    return course


@pytest.fixture
def problem(session: Session, course: Course) -> Problem:
    return make_problem(session, make_lesson(session, course), total_number_testcase=4)


def _participant_statements(statements: list[str]) -> list[str]:
    # participants_by_lesson là truy vấn duy nhất đếm DISTINCT student_id
    return [s for s in statements if "distinct(submission.student_id" in s.lower()]


def _user_selects(statements: list[str]) -> list[str]:
    # truy vấn tải người tạo lớp từ bảng user (không join): selectin dùng
    # "user_id IN (...)", lazy load từng lớp dùng "user_id = ?"
    return [
        s for s in statements
        if s.lstrip().startswith("SELECT") and "FROM user" in s and "JOIN" not in s
    ]


def _lazy_user_selects(statements: list[str]) -> list[str]:
    return [s for s in _user_selects(statements) if "user.user_id = ?" in s]


def _selectin_user_selects(statements: list[str]) -> list[str]:
    return [s for s in _user_selects(statements) if "user.user_id IN" in s]


class TestBuildCourseResponseQueries:
    def test_student_view_skips_participant_query(
        self, engine, session, course, problem, student
    ):
        sub = make_submission(session, problem, student, passed_count=2)
        session.commit()
        student_id = student.user_id

        with count_queries(engine) as queries:
            response = build_course_response(course, session, only_student_id=student_id)

        assert _participant_statements(queries.statements) == []
        assert response.sessions[0].participant_count is None
        assert len(response.sessions[0].problems) == 1
        cell = response.grades[0].session_scores[str(problem.lesson_id)][0]
        assert cell.value == 5.0
        assert cell.submitted is True
        assert cell.submission_id == sub.submission_id

    def test_teacher_view_keeps_participant_count(
        self, engine, session, course, problem, student
    ):
        make_submission(session, problem, student, passed_count=2)
        make_submission(session, problem, student, passed_count=1)
        session.commit()

        with count_queries(engine) as queries:
            response = build_course_response(course, session)

        assert len(_participant_statements(queries.statements)) == 1
        assert response.sessions[0].participant_count == 1
        assert response.grades[0].overall_score == 5.0

    def test_problem_query_loads_only_needed_columns(self, engine, session, course, problem):
        session.commit()

        with count_queries(engine) as queries:
            build_course_response(course, session)

        problem_selects = [
            s for s in queries.statements if "FROM problem" in s and "problem.title" in s
        ]
        assert len(problem_selects) == 1
        for column in ("description", "starter_codes", "constraints", "hint", "complexity"):
            assert f"problem.{column}" not in problem_selects[0]

    def test_course_without_lessons(self, session, course):
        response = build_course_response(course, session)

        assert response.sessions == []
        assert response.grades[0].session_scores == {}


class TestCourseListCreatorLoading:
    def _extra_courses(self, session, student, count):
        for index in range(count):
            owner = make_user(session, f"GV9{index}", Role.TEACHER)
            extra = make_course(session, owner, f"EX{index}")
            make_enrollment(session, extra, student)
        session.commit()

    def test_admin_list_loads_creators_in_bulk(self, engine, session, student, course):
        self._extra_courses(session, student, 4)
        admin = make_user(session, "AD001", Role.ADMIN)
        session.commit()
        session.expire_all()
        session.refresh(admin)

        with count_queries(engine) as queries:
            result = course_service.get_courses(session, admin)

        assert len(result) == 5
        # một truy vấn selectin cho mọi người tạo, không phải mỗi lớp một truy vấn
        assert len(_selectin_user_selects(queries.statements)) == 1
        assert _lazy_user_selects(queries.statements) == []
        names = {r.course_id: r.teacher_name for r in result}
        assert names["CS101"] == "User GV001"
        assert names["EX0"] == "User GV90"
        assert names["EX3"] == "User GV93"

    def test_creator_queries_do_not_grow_with_courses(self, engine, session, student, course):
        admin = make_user(session, "AD001", Role.ADMIN)
        session.commit()
        session.expire_all()
        session.refresh(admin)
        with count_queries(engine) as few:
            course_service.get_courses(session, admin)

        self._extra_courses(session, student, 3)
        session.expire_all()
        session.refresh(admin)
        with count_queries(engine) as many:
            result = course_service.get_courses(session, admin)

        assert len(result) == 4
        assert _lazy_user_selects(few.statements) == _lazy_user_selects(many.statements) == []
        assert len(_selectin_user_selects(many.statements)) == 1

    def test_student_courses_and_dashboard_report_teacher_name(
        self, engine, session, student, course
    ):
        self._extra_courses(session, student, 3)
        session.expire_all()
        session.refresh(student)

        with count_queries(engine) as queries:
            courses = course_service.get_student_courses(session, str(student.user_id), student)
        assert len(courses) == 4
        assert {c.teacher_name for c in courses} == {"User GV001", "User GV90", "User GV91", "User GV92"}
        assert len(_selectin_user_selects(queries.statements)) == 1
        assert _lazy_user_selects(queries.statements) == []

        session.expire_all()
        session.refresh(student)
        with count_queries(engine) as queries:
            dashboard = course_service.get_student_dashboard(session, str(student.user_id), student)
        assert dashboard.total_classes == 4
        assert len(_selectin_user_selects(queries.statements)) == 1
        assert _lazy_user_selects(queries.statements) == []


class TestDueThisWeekAndDelete:
    def test_count_due_this_week_with_multiple_submissions_per_problem(
        self, session, teacher, student
    ):
        course = make_course(session, teacher, "CS202")
        make_enrollment(session, course, student)
        today = today_vn()
        lesson = make_lesson(
            session, course, start_date=today - timedelta(days=1), end_date=today + timedelta(days=2)
        )
        solved = make_problem(session, lesson, title="Solved")
        unsolved = make_problem(session, lesson, title="Unsolved")
        make_submission(session, solved, student, status="accepted")
        make_submission(session, solved, student, status="accepted")
        make_submission(session, unsolved, student, status="wrong_answer")
        make_submission(session, unsolved, student, status="wrong_answer")

        assert course_service._count_due_this_week(session, student.user_id, student) == 1

    def test_delete_course_with_many_submissions_on_same_problem(
        self, session, course, problem, student, teacher
    ):
        for _ in range(3):
            make_submission(session, problem, student)
        session.commit()

        with pytest.raises(ConflictError, match="3 bài nộp"):
            course_service.delete_course("CS101", session, teacher)

        assert session.get(Course, "CS101") is not None
        assert session.get(Lesson, problem.lesson_id) is not None
