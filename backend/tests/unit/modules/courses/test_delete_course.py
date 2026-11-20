"""Xoá lớp học phần: chỉ chủ lớp/Admin, chặn khi đã có bài nộp, giữ đề nguồn."""

import logging

import pytest
from sqlalchemy import text
from sqlmodel import Session, select

from app.core.dependencies import Role
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models import Course, Enrollment, Lesson, Problem, Submission, User
from app.models import entities
from app.modules.courses import service as course_service
from app.modules.courses.service import CourseHasSubmissionsError, delete_course
from tests.support.fixtures.builders import (
    make_course,
    make_enrollment,
    make_lesson,
    make_problem,
    make_submission,
    make_testcase,
    make_user,
)


pytest_plugins = ("tests.support.fixtures.db_fixtures",)


def _student(session: Session, mssv: str):
    student = make_user(session, mssv, Role.STUDENT)
    student.email = f"{mssv}@st.utc2.edu.vn"
    return student


@pytest.fixture
def owner(session: Session):
    return make_user(session, "teacher_owner", Role.TEACHER)


@pytest.fixture
def course_with_content(session: Session, owner):
    course = make_course(session, owner, "DELC1")
    lesson = make_lesson(session, course)
    problem = make_problem(session, lesson)
    make_testcase(session, problem)
    student = _student(session, "6451000001")
    make_enrollment(session, course, student)
    bank_problem = make_problem(session, None, title="Bank source")
    session.commit()
    return course, lesson, problem, student, bank_problem


def test_owner_deletes_course_with_lessons_problems_and_enrollments(
    session: Session, owner, course_with_content
):
    _, lesson, problem, _, bank_problem = course_with_content

    delete_course("DELC1", session, owner)

    assert session.get(Course, "DELC1") is None
    assert session.get(Lesson, lesson.lesson_id) is None
    assert session.get(Problem, problem.problem_id) is None
    assert session.exec(select(entities.Testcase).where(entities.Testcase.problem_id == problem.problem_id)).first() is None
    assert session.exec(select(Enrollment).where(Enrollment.course_id == "DELC1")).first() is None
    # Đề nguồn trong ngân hàng không bị xoá
    assert session.get(Problem, bank_problem.problem_id) is not None


def test_admin_can_delete_any_course(session: Session, course_with_content):
    admin = make_user(session, "admin_x", Role.ADMIN)

    delete_course("DELC1", session, admin)

    assert session.get(Course, "DELC1") is None


def test_other_teacher_cannot_delete(session: Session, course_with_content):
    other = make_user(session, "teacher_other", Role.TEACHER)

    with pytest.raises(ForbiddenError):
        delete_course("DELC1", session, other)


def test_course_with_submissions_is_not_deleted(session: Session, owner, course_with_content):
    _, _, problem, student, _ = course_with_content
    make_submission(session, problem, student)
    session.commit()

    with pytest.raises(ConflictError, match="đã có bài nộp"):
        delete_course("DELC1", session, owner)
    assert session.get(Course, "DELC1") is not None


def test_missing_course_returns_not_found(session: Session, owner):
    with pytest.raises(NotFoundError):
        delete_course("NOPE", session, owner)


def _count_submissions_in(session: Session, problem_ids) -> int:
    return len(session.exec(select(Submission).where(Submission.problem_id.in_(problem_ids))).all())


def _two_submissions(session: Session, problem, student):
    make_submission(session, problem, student)
    make_submission(session, problem, student, status="accepted")
    session.commit()


def test_submissions_block_delete_with_code_and_count(session: Session, owner, course_with_content):
    _, _, problem, student, _ = course_with_content
    _two_submissions(session, problem, student)

    with pytest.raises(CourseHasSubmissionsError) as exc_info:
        delete_course("DELC1", session, owner)

    assert exc_info.value.status_code == 409
    assert exc_info.value.error_code == "COURSE_HAS_SUBMISSIONS"
    assert "(2 bài nộp)" in exc_info.value.message


def test_admin_force_deletes_course_and_its_submissions_only(session: Session, course_with_content, owner):
    _, lesson, problem, student, bank_problem = course_with_content
    _two_submissions(session, problem, student)
    other_course = make_course(session, owner, "DELC2")
    other_problem = make_problem(session, make_lesson(session, other_course))
    other_student = _student(session, "6451000002")
    make_submission(session, other_problem, other_student)
    admin = make_user(session, "admin_x", Role.ADMIN)
    session.commit()

    delete_course("DELC1", session, admin, force=True)

    assert session.get(Course, "DELC1") is None
    assert session.get(Lesson, lesson.lesson_id) is None
    assert session.get(Problem, problem.problem_id) is None
    assert _count_submissions_in(session, [problem.problem_id]) == 0
    # Dữ liệu ngoài lớp bị xoá vẫn còn nguyên
    assert session.get(Course, "DELC2") is not None
    assert _count_submissions_in(session, [other_problem.problem_id]) == 1
    assert session.get(Problem, bank_problem.problem_id) is not None
    assert session.get(User, student.user_id) is not None
    assert session.get(User, other_student.user_id) is not None


def test_admin_force_without_submissions_deletes_normally(session: Session, course_with_content):
    admin = make_user(session, "admin_x", Role.ADMIN)

    delete_course("DELC1", session, admin, force=True)

    assert session.get(Course, "DELC1") is None


def test_owner_teacher_force_is_forbidden_and_keeps_data(session: Session, owner, course_with_content):
    _, _, problem, student, _ = course_with_content
    _two_submissions(session, problem, student)

    with pytest.raises(ForbiddenError, match="Chỉ Admin"):
        delete_course("DELC1", session, owner, force=True)

    assert session.get(Course, "DELC1") is not None
    assert _count_submissions_in(session, [problem.problem_id]) == 2


@pytest.mark.parametrize("role_id", [Role.STUDENT, 99])
def test_non_admin_non_teacher_force_is_forbidden(session: Session, course_with_content, role_id):
    _, _, problem, student, _ = course_with_content
    _two_submissions(session, problem, student)
    stranger = make_user(session, f"role_{role_id}", role_id)

    with pytest.raises(ForbiddenError):
        delete_course("DELC1", session, stranger, force=True)

    assert session.get(Course, "DELC1") is not None
    assert _count_submissions_in(session, [problem.problem_id]) == 2


def test_force_delete_is_audit_logged(session: Session, course_with_content, caplog):
    _, _, problem, student, _ = course_with_content
    _two_submissions(session, problem, student)
    admin = make_user(session, "admin_x", Role.ADMIN)

    with caplog.at_level(logging.INFO, logger=course_service.logger.name):
        delete_course("DELC1", session, admin, force=True)

    messages = [r.getMessage() for r in caplog.records if r.levelno == logging.INFO]
    assert f"Admin {admin.user_id} đã xoá cưỡng bức lớp DELC1 cùng 2 bài nộp" in messages


def test_non_force_delete_is_not_audit_logged(session: Session, owner, course_with_content, caplog):
    with caplog.at_level(logging.INFO, logger=course_service.logger.name):
        delete_course("DELC1", session, owner)

    assert not any("cưỡng bức" in r.getMessage() for r in caplog.records)


def test_submission_arriving_during_force_delete_blocks_it(fk_session: Session, monkeypatch, caplog):
    session = fk_session
    owner = make_user(session, "teacher_owner", Role.TEACHER)
    admin = make_user(session, "admin_x", Role.ADMIN)
    course = make_course(session, owner, "DELC1")
    problem = make_problem(session, make_lesson(session, course))
    student = _student(session, "6451000001")
    make_enrollment(session, course, student)
    make_submission(session, problem, student)
    session.commit()
    problem_id, student_id = problem.problem_id, student.user_id

    real_exec = session.exec

    def exec_then_race(statement, *args, **kwargs):
        result = real_exec(statement, *args, **kwargs)
        if str(statement).startswith("DELETE FROM submission"):
            # Bài nộp mới chen vào sau lúc xoá hàng loạt, trước khi xoá đề bài
            session.execute(
                text(
                    "INSERT INTO submission (problem_id, student_id, language, submitted_code, "
                    "status, passed_count, submitted_datetime) VALUES "
                    "(:p, :s, 'python', 'x', 'pending', 0, '2026-01-11 00:00:00')"
                ),
                {"p": problem_id, "s": student_id.hex},
            )
        return result

    monkeypatch.setattr(session, "exec", exec_then_race)

    with (
        caplog.at_level(logging.INFO, logger=course_service.logger.name),
        pytest.raises(CourseHasSubmissionsError, match="vừa có bài nộp mới"),
    ):
        delete_course("DELC1", session, admin, force=True)

    session.expire_all()
    assert session.get(Course, "DELC1") is not None
    assert session.get(Problem, problem_id) is not None
    assert _count_submissions_in(session, [problem_id]) == 1  # giao dịch rollback, bài nộp gốc còn
    assert not any("cưỡng bức" in r.getMessage() for r in caplog.records)


def test_submission_arriving_after_check_blocks_non_force_delete(
    fk_session: Session, monkeypatch
):
    session = fk_session
    owner = make_user(session, "teacher_owner", Role.TEACHER)
    course = make_course(session, owner, "DELC1")
    problem = make_problem(session, make_lesson(session, course))
    student = _student(session, "6451000001")
    make_enrollment(session, course, student)
    make_submission(session, problem, student)
    session.commit()
    # Mô phỏng bài nộp chen vào sau lúc kiểm tra: kiểm tra thấy 0 nhưng DB đã có
    monkeypatch.setattr(course_service, "_count_submissions", lambda *_: 0)

    with pytest.raises(CourseHasSubmissionsError, match="vui lòng thử lại"):
        delete_course("DELC1", session, owner)

    assert session.get(Course, "DELC1") is not None
    assert _count_submissions_in(session, [problem.problem_id]) == 1


def test_non_force_never_deletes_submissions(session: Session, owner, course_with_content):
    _, _, problem, student, _ = course_with_content
    _two_submissions(session, problem, student)
    admin = make_user(session, "admin_x", Role.ADMIN)

    with pytest.raises(CourseHasSubmissionsError):
        delete_course("DELC1", session, admin)

    assert _count_submissions_in(session, [problem.problem_id]) == 2
