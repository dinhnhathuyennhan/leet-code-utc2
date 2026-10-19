"""Pytest fixtures used only by Lesson service unit tests."""

from collections.abc import Callable

import pytest
from sqlmodel import Session

from app.core.dependencies import Role
from app.models.entities import Course, Enrollment, Lesson, Problem, Submission, Testcase, User
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
def lesson_user_factory(session: Session) -> Callable[..., User]:
    return lambda user_id, role_id: make_user(session, user_id, role_id)


@pytest.fixture
def lesson_teacher(lesson_user_factory: Callable[..., User]) -> User:
    return lesson_user_factory("GV001", Role.TEACHER)


@pytest.fixture
def lesson_other_teacher(lesson_user_factory: Callable[..., User]) -> User:
    return lesson_user_factory("GV002", Role.TEACHER)


@pytest.fixture
def lesson_student(lesson_user_factory: Callable[..., User]) -> User:
    return lesson_user_factory("SV001", Role.STUDENT)


@pytest.fixture
def lesson_course_factory(session: Session) -> Callable[..., Course]:
    return lambda owner, course_id="CS101": make_course(session, owner, course_id)


@pytest.fixture
def lesson_course(
    lesson_course_factory: Callable[..., Course], lesson_teacher: User
) -> Course:
    return lesson_course_factory(lesson_teacher)


@pytest.fixture
def lesson_other_course(
    lesson_course_factory: Callable[..., Course], lesson_other_teacher: User
) -> Course:
    return lesson_course_factory(lesson_other_teacher, "CS202")


@pytest.fixture
def lesson_factory(session: Session) -> Callable[..., Lesson]:
    return lambda course, **kwargs: make_lesson(session, course, **kwargs)


@pytest.fixture
def lesson_record(
    lesson_factory: Callable[..., Lesson], lesson_course: Course
) -> Lesson:
    return lesson_factory(lesson_course)


@pytest.fixture
def lesson_other_lesson(
    lesson_factory: Callable[..., Lesson], lesson_other_course: Course
) -> Lesson:
    return lesson_factory(lesson_other_course, lesson_name="Other course lesson")


@pytest.fixture
def lesson_problem_factory(session: Session) -> Callable[..., Problem]:
    return lambda lesson=None, **kwargs: make_problem(session, lesson, **kwargs)


@pytest.fixture
def lesson_problem(
    lesson_problem_factory: Callable[..., Problem], lesson_record: Lesson
) -> Problem:
    return lesson_problem_factory(lesson_record)


@pytest.fixture
def lesson_bank_problem(lesson_problem_factory: Callable[..., Problem]) -> Problem:
    return lesson_problem_factory(title="Bank Two Sum")


@pytest.fixture
def lesson_testcase_factory(session: Session) -> Callable[..., Testcase]:
    return lambda problem, **kwargs: make_testcase(session, problem, **kwargs)


@pytest.fixture
def lesson_submission_factory(session: Session) -> Callable[..., Submission]:
    return lambda problem, student, **kwargs: make_submission(
        session, problem, student, **kwargs
    )


@pytest.fixture
def lesson_enrollment_factory(session: Session) -> Callable[..., Enrollment]:
    return lambda course, student: make_enrollment(session, course, student)
