"""Test tầng HTTP của các endpoint quản lý tài khoản (khoá / mở khoá...).

Logic phân quyền nằm ở ``tests/unit/modules/users``; file này kiểm tra status
code, body lỗi và việc router dùng đúng ``require_role``.
"""

import uuid

import pytest

from app.core.dependencies import Role, get_current_user
from app.main import app
from app.models import User
from tests.support.fixtures.builders import make_course, make_enrollment

pytest_plugins = ("tests.support.fixtures.api_fixtures",)

NOT_ALLOWED = {
    "error_code": "NOT_ALLOWED_TO_MANAGE_ACCOUNT",
    "message": "Bạn không có quyền quản lý tài khoản này",
}


def _create_user(session, role_id: int, name: str) -> User:
    student_code = None
    if role_id == Role.STUDENT:
        student_code = f"{uuid.uuid5(uuid.NAMESPACE_DNS, name).int % 10**10:010d}"
    user = User(
        user_id=uuid.uuid4(),
        student_code=student_code,
        full_name=name,
        email=f"{name}@example.com",
        hashed_password="placeholder",
        role_id=role_id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _login_as(user: User) -> None:
    app.dependency_overrides[get_current_user] = lambda: user


@pytest.fixture
def admin(session):
    return _create_user(session, Role.ADMIN, "admin")


@pytest.fixture
def teacher(session):
    return _create_user(session, Role.TEACHER, "teacher")


@pytest.fixture
def student(session):
    return _create_user(session, Role.STUDENT, "student")


# ---------- POST /users/{id}/lock, /unlock ----------


def test_admin_lock_then_unlock_student_returns_status(client, admin, student):
    _login_as(admin)

    locked = client.post(f"/users/{student.user_id}/lock")
    assert locked.status_code == 200, locked.text
    assert locked.json()["is_active"] is False
    assert locked.json()["user_id"] == str(student.user_id)
    assert "hashed_password" not in locked.json()

    unlocked = client.post(f"/users/{student.user_id}/unlock")
    assert unlocked.status_code == 200, unlocked.text
    assert unlocked.json()["is_active"] is True
    assert "hashed_password" not in unlocked.json()


def test_teacher_locks_own_student_returns_200(client, session, teacher, student):
    make_enrollment(session, make_course(session, teacher, "CS_API"), student)
    session.commit()
    _login_as(teacher)

    response = client.post(f"/users/{student.user_id}/lock")

    assert response.status_code == 200, response.text
    assert response.json()["is_active"] is False


def test_teacher_lock_student_outside_courses_returns_403_not_allowed_to_manage_account(
    client, teacher, student
):
    _login_as(teacher)

    response = client.post(f"/users/{student.user_id}/lock")

    assert response.status_code == 403
    assert response.json() == NOT_ALLOWED


@pytest.mark.parametrize("action", ["lock", "unlock"])
@pytest.mark.parametrize("role_id", [Role.STUDENT, 99])
def test_student_and_unknown_role_get_403(client, session, student, role_id, action):
    caller = _create_user(session, role_id, f"caller{role_id}")
    _login_as(caller)

    response = client.post(f"/users/{student.user_id}/{action}")

    assert response.status_code == 403


def test_admin_lock_self_returns_403(client, admin):
    _login_as(admin)

    response = client.post(f"/users/{admin.user_id}/lock")

    assert response.status_code == 403
    assert response.json() == NOT_ALLOWED


def test_lock_unknown_user_returns_404_user_not_found(client, admin):
    _login_as(admin)

    response = client.post(f"/users/{uuid.uuid4()}/lock")

    assert response.status_code == 404
    assert response.json()["error_code"] == "USER_NOT_FOUND"


def test_lock_non_uuid_user_returns_404_user_not_found(client, admin):
    _login_as(admin)

    response = client.post("/users/not-a-uuid/unlock")

    assert response.status_code == 404
    assert response.json()["error_code"] == "USER_NOT_FOUND"


@pytest.mark.parametrize("action", ["lock", "unlock"])
def test_lock_requires_login_returns_401(client, student, action):
    response = client.post(f"/users/{student.user_id}/{action}")

    assert response.status_code == 401
