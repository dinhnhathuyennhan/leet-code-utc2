"""Pytest fixtures used only by Problem service unit tests."""

from collections.abc import Callable

import pytest
from sqlmodel import Session

from app.dependencies import Role
from app.schemas.problem import ProblemCreateRequest
from models import Course, Enrollment, Lesson, Problem, Submission, Testcase, User
from fixtures.builders import (
    make_course,
    make_enrollment,
    make_lesson,
    make_problem,
    make_problem_create_request,
    make_submission,
    make_testcase,
    make_user,
)


@pytest.fixture
def problem_user_factory(session: Session) -> Callable[..., User]:
    return lambda user_id, role_id: make_user(session, user_id, role_id)


@pytest.fixture
def problem_admin(problem_user_factory: Callable[..., User]) -> User:
    return problem_user_factory("AD001", Role.ADMIN)


@pytest.fixture
def problem_teacher(problem_user_factory: Callable[..., User]) -> User:
    return problem_user_factory("GV001", Role.TEACHER)


@pytest.fixture
def problem_other_teacher(problem_user_factory: Callable[..., User]) -> User:
    return problem_user_factory("GV002", Role.TEACHER)


@pytest.fixture
def problem_student(problem_user_factory: Callable[..., User]) -> User:
    return problem_user_factory("SV001", Role.STUDENT)


@pytest.fixture
def problem_course_factory(session: Session) -> Callable[..., Course]:
    return lambda owner, course_id="CS101": make_course(session, owner, course_id)


@pytest.fixture
def problem_course(
    problem_course_factory: Callable[..., Course], problem_teacher: User
) -> Course:
    return problem_course_factory(problem_teacher)


@pytest.fixture
def problem_other_course(
    problem_course_factory: Callable[..., Course], problem_other_teacher: User
) -> Course:
    return problem_course_factory(problem_other_teacher, "CS202")


@pytest.fixture
def problem_lesson_factory(session: Session) -> Callable[..., Lesson]:
    return lambda course, **kwargs: make_lesson(session, course, **kwargs)


@pytest.fixture
def problem_lesson(
    problem_lesson_factory: Callable[..., Lesson], problem_course: Course
) -> Lesson:
    return problem_lesson_factory(problem_course)


@pytest.fixture
def problem_other_lesson(
    problem_lesson_factory: Callable[..., Lesson], problem_other_course: Course
) -> Lesson:
    return problem_lesson_factory(
        problem_other_course, lesson_name="Other course lesson"
    )


@pytest.fixture
def problem_factory(session: Session) -> Callable[..., Problem]:
    return lambda lesson=None, **kwargs: make_problem(session, lesson, **kwargs)


@pytest.fixture
def problem_record(
    problem_factory: Callable[..., Problem], problem_lesson: Lesson
) -> Problem:
    return problem_factory(problem_lesson)


@pytest.fixture
def problem_bank_problem(problem_factory: Callable[..., Problem]) -> Problem:
    return problem_factory(title="Bank Two Sum")


@pytest.fixture
def problem_testcase_factory(session: Session) -> Callable[..., Testcase]:
    return lambda problem, **kwargs: make_testcase(session, problem, **kwargs)


@pytest.fixture
def problem_submission_factory(session: Session) -> Callable[..., Submission]:
    return lambda problem, student, **kwargs: make_submission(
        session, problem, student, **kwargs
    )


@pytest.fixture
def problem_enrollment_factory(session: Session) -> Callable[..., Enrollment]:
    return lambda course, student: make_enrollment(session, course, student)


@pytest.fixture
def problem_create_request_factory() -> Callable[..., ProblemCreateRequest]:
    return make_problem_create_request
