"""Xoá lớp học phần: chỉ chủ lớp/Admin, chặn khi đã có bài nộp, giữ đề nguồn."""

import pytest
from sqlmodel import Session, select

from app.core.dependencies import Role
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models import Course, Enrollment, Lesson, Problem
from app.models import entities
from app.modules.courses.service import delete_course
from tests.support.fixtures.builders import (
    make_course,
    make_enrollment,
    make_lesson,
    make_problem,
    make_submission,
    make_testcase,
    make_user,
)


@pytest.fixture
def owner(session: Session):
    return make_user(session, "teacher_owner", Role.TEACHER)


@pytest.fixture
def course_with_content(session: Session, owner):
    course = make_course(session, owner, "DELC1")
    lesson = make_lesson(session, course)
    problem = make_problem(session, lesson)
    make_testcase(session, problem)
    student = make_user(session, "6451000001", Role.STUDENT)
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
