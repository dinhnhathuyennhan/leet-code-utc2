"""HTTP tests của ``DELETE /courses/{id}``: phân quyền, 409 khi có bài nộp, ``?force=true`` chỉ Admin."""

import pytest
from sqlmodel import select

from app.core.dependencies import Role, get_current_user
from app.main import app
from app.models import Course, Submission
from tests.support.fixtures.builders import (
    make_course,
    make_enrollment,
    make_lesson,
    make_problem,
    make_submission,
)
from tests.support.fixtures.user_fixtures import make_user

pytest_plugins = (
    "tests.support.fixtures.api_fixtures",
    "tests.support.fixtures.user_fixtures",
)


def _login_as(user) -> None:
    app.dependency_overrides[get_current_user] = lambda: user


@pytest.fixture
def course_with_submissions(session, owner_teacher):
    course = make_course(session, owner_teacher, "DELH1")
    problem = make_problem(session, make_lesson(session, course))
    student = make_user(session, "6451000001", Role.STUDENT)
    student.email = "6451000001@st.utc2.edu.vn"
    make_enrollment(session, course, student)
    make_submission(session, problem, student)
    make_submission(session, problem, student, status="accepted")
    session.commit()
    return course


@pytest.fixture
def empty_course(session, owner_teacher):
    course = make_course(session, owner_teacher, "DELH0")
    session.commit()
    return course


def _submission_count(session) -> int:
    return len(session.exec(select(Submission)).all())


def test_owner_teacher_deletes_course_returns_204(client, session, owner_teacher, empty_course):
    _login_as(owner_teacher)

    response = client.delete("/courses/DELH0")

    assert response.status_code == 204
    assert session.get(Course, "DELH0") is None


def test_admin_deletes_any_course_returns_204(client, session, admin, empty_course):
    _login_as(admin)

    response = client.delete("/courses/DELH0")

    assert response.status_code == 204
    assert session.get(Course, "DELH0") is None


def test_other_teacher_returns_403(client, session, other_teacher, empty_course):
    _login_as(other_teacher)

    response = client.delete("/courses/DELH0")

    assert response.status_code == 403
    assert session.get(Course, "DELH0") is not None


@pytest.mark.parametrize("role_id", [Role.STUDENT, 99])
def test_student_and_unknown_role_return_403(client, session, empty_course, role_id):
    _login_as(make_user(session, "CALLER1", role_id))

    response = client.delete("/courses/DELH0")

    assert response.status_code == 403
    assert session.get(Course, "DELH0") is not None


def test_missing_course_returns_404(client, admin):
    _login_as(admin)

    response = client.delete("/courses/NOPE")

    assert response.status_code == 404


def test_course_with_submissions_returns_409_course_has_submissions(
    client, session, owner_teacher, course_with_submissions
):
    _login_as(owner_teacher)

    response = client.delete("/courses/DELH1")

    assert response.status_code == 409
    body = response.json()
    assert body["error_code"] == "COURSE_HAS_SUBMISSIONS"
    assert "(2 bài nộp)" in body["message"]
    assert session.get(Course, "DELH1") is not None
    assert _submission_count(session) == 2


def test_admin_force_returns_204_and_removes_submissions(
    client, session, admin, course_with_submissions
):
    _login_as(admin)

    response = client.delete("/courses/DELH1?force=true")

    assert response.status_code == 204
    assert session.get(Course, "DELH1") is None
    assert _submission_count(session) == 0


def test_teacher_force_returns_403_and_keeps_data(
    client, session, owner_teacher, course_with_submissions
):
    _login_as(owner_teacher)

    response = client.delete("/courses/DELH1?force=true")

    assert response.status_code == 403
    assert session.get(Course, "DELH1") is not None
    assert _submission_count(session) == 2


def test_invalid_force_value_returns_422(client, session, admin, course_with_submissions):
    _login_as(admin)

    response = client.delete("/courses/DELH1?force=maybe")

    assert response.status_code == 422
    assert session.get(Course, "DELH1") is not None
    assert _submission_count(session) == 2


def test_delete_requires_login_returns_401(client, empty_course):
    response = client.delete("/courses/DELH0")

    assert response.status_code == 401
