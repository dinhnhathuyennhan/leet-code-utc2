"""Pytest fixtures used by Submission service unit tests."""

import pytest
from sqlmodel import Session

from app.core.dependencies import Role
from app.models.entities import Course, Lesson, Problem, Submission, User
from tests.support.fixtures.builders import (
    make_course,
    make_lesson,
    make_problem,
    make_submission,
    make_user,
)


@pytest.fixture
def submission_teacher(session: Session) -> User:
    return make_user(session, "GV001", Role.TEACHER)


@pytest.fixture
def submission_student(session: Session) -> User:
    return make_user(session, "SV001", Role.STUDENT)


@pytest.fixture
def submission_course(session: Session, submission_teacher: User) -> Course:
    return make_course(session, submission_teacher, "CS101")


@pytest.fixture
def submission_lesson(session: Session, submission_course: Course) -> Lesson:
    return make_lesson(session, submission_course)


@pytest.fixture
def submission_problem(session: Session, submission_lesson: Lesson) -> Problem:
    return make_problem(session, submission_lesson)


@pytest.fixture
def pending_error_submission(
    session: Session, submission_problem: Problem, submission_student: User
) -> Submission:
    return make_submission(
        session,
        submission_problem,
        submission_student,
        status="compile_error",
    )
