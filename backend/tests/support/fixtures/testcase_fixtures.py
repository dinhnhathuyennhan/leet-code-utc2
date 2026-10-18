"""Pytest fixtures used only by Testcase service unit tests."""

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
def testcase_user_factory(session: Session) -> Callable[..., User]:
    return lambda user_id, role_id: make_user(session, user_id, role_id)


@pytest.fixture
def testcase_admin(testcase_user_factory: Callable[..., User]) -> User:
    return testcase_user_factory("AD001", Role.ADMIN)


@pytest.fixture
def testcase_teacher(testcase_user_factory: Callable[..., User]) -> User:
    return testcase_user_factory("GV001", Role.TEACHER)


@pytest.fixture
def testcase_other_teacher(testcase_user_factory: Callable[..., User]) -> User:
    return testcase_user_factory("GV002", Role.TEACHER)


@pytest.fixture
def testcase_student(testcase_user_factory: Callable[..., User]) -> User:
    return testcase_user_factory("SV001", Role.STUDENT)


@pytest.fixture
def testcase_course_factory(session: Session) -> Callable[..., Course]:
    return lambda owner, course_id="CS101": make_course(session, owner, course_id)


@pytest.fixture
def testcase_course(
    testcase_course_factory: Callable[..., Course], testcase_teacher: User
) -> Course:
    return testcase_course_factory(testcase_teacher)


@pytest.fixture
def testcase_lesson_factory(session: Session) -> Callable[..., Lesson]:
    return lambda course, **kwargs: make_lesson(session, course, **kwargs)


@pytest.fixture
def testcase_lesson(
    testcase_lesson_factory: Callable[..., Lesson], testcase_course: Course
) -> Lesson:
    return testcase_lesson_factory(testcase_course)


@pytest.fixture
def testcase_problem_factory(session: Session) -> Callable[..., Problem]:
    return lambda lesson=None, **kwargs: make_problem(session, lesson, **kwargs)


@pytest.fixture
def testcase_problem(
    testcase_problem_factory: Callable[..., Problem], testcase_lesson: Lesson
) -> Problem:
    return testcase_problem_factory(testcase_lesson)


@pytest.fixture
def testcase_factory(session: Session) -> Callable[..., Testcase]:
    return lambda problem, **kwargs: make_testcase(session, problem, **kwargs)


@pytest.fixture
def testcase_submission_factory(session: Session) -> Callable[..., Submission]:
    return lambda problem, student, **kwargs: make_submission(
        session, problem, student, **kwargs
    )


@pytest.fixture
def testcase_enrollment_factory(session: Session) -> Callable[..., Enrollment]:
    return lambda course, student: make_enrollment(session, course, student)
