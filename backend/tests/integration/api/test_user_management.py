"""Test tầng HTTP của các endpoint quản lý tài khoản (khoá / mở khoá...).

Logic phân quyền nằm ở ``tests/unit/modules/users``; file này kiểm tra status
code, body lỗi và việc router dùng đúng ``require_role``.
"""

import uuid

import pytest

from app.core.dependencies import Role, get_current_user
from app.main import app
from app.models import Class, User
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
        email=(
            f"{student_code}@st.utc2.edu.vn"
            if student_code
            else f"{name}@example.com"
        ),
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


def test_teacher_unlock_account_locked_by_admin_returns_403(
    client, session, admin, teacher, student
):
    make_enrollment(session, make_course(session, teacher, "CS_API"), student)
    session.commit()
    _login_as(admin)
    assert client.post(f"/users/{student.user_id}/lock").status_code == 200
    _login_as(teacher)

    response = client.post(f"/users/{student.user_id}/unlock")

    assert response.status_code == 403
    assert response.json() == {
        "error_code": "NOT_ALLOWED_TO_MANAGE_ACCOUNT",
        "message": "Tài khoản này chỉ Quản trị viên mới được mở khoá",
    }
    session.refresh(student)
    assert student.is_active is False


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


# ---------- PATCH /users/{id} ----------


def _add_class(session, class_id: str = "CQ.67.CNTT") -> None:
    session.add(Class(class_id=class_id, type="CQ", course_number=67, department="CNTT"))
    session.commit()


def test_admin_patch_student_code_returns_new_email(client, admin, student):
    _login_as(admin)

    response = client.patch(f"/users/{student.user_id}", json={"student_code": "6851071002"})

    assert response.status_code == 200, response.text
    assert response.json()["student_code"] == "6851071002"
    assert response.json()["email"] == "6851071002@st.utc2.edu.vn"


def test_teacher_patch_own_student_returns_200(client, session, teacher, student):
    make_enrollment(session, make_course(session, teacher, "CS_PATCH"), student)
    session.commit()
    _login_as(teacher)

    response = client.patch(f"/users/{student.user_id}", json={"full_name": "  Nguyễn  Văn A "})

    assert response.status_code == 200, response.text
    assert response.json()["full_name"] == "Nguyễn Văn A"


def test_patch_invalid_student_code_returns_422_invalid_format(client, admin, student):
    _login_as(admin)

    response = client.patch(f"/users/{student.user_id}", json={"student_code": "123"})

    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_FORMAT"


def test_patch_invalid_email_domain_returns_422_invalid_format(client, admin, teacher):
    _login_as(admin)

    response = client.patch(f"/users/{teacher.user_id}", json={"email": "a@example.com"})

    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_FORMAT"


def test_patch_blank_full_name_returns_422_empty_field(client, admin, teacher):
    _login_as(admin)

    response = client.patch(f"/users/{teacher.user_id}", json={"full_name": "   "})

    assert response.status_code == 422
    assert response.json()["error_code"] == "EMPTY_FIELD"


def test_patch_student_email_returns_422_field_not_editable(client, admin, student):
    _login_as(admin)

    response = client.patch(f"/users/{student.user_id}", json={"email": "x@st.utc2.edu.vn"})

    assert response.status_code == 422
    assert response.json()["error_code"] == "FIELD_NOT_EDITABLE"


def test_patch_duplicate_student_code_returns_409(client, session, admin, student):
    other = _create_user(session, Role.STUDENT, "other")

    _login_as(admin)
    response = client.patch(f"/users/{student.user_id}", json={"student_code": other.student_code})

    assert response.status_code == 409
    assert response.json()["error_code"] == "CONFLICT"


def test_patch_missing_class_returns_404(client, admin, student):
    _login_as(admin)

    response = client.patch(f"/users/{student.user_id}", json={"class_id": "NOPE"})

    assert response.status_code == 404
    assert "NOPE" in response.json()["message"]


def test_patch_class_id_moves_student(client, session, admin, student):
    _add_class(session)
    _login_as(admin)

    response = client.patch(f"/users/{student.user_id}", json={"class_id": "CQ.67.CNTT"})

    assert response.status_code == 200, response.text
    assert response.json()["class_id"] == "CQ.67.CNTT"


def test_patch_role_id_in_body_is_ignored(client, admin, student):
    _login_as(admin)

    response = client.patch(
        f"/users/{student.user_id}", json={"role_id": 1, "full_name": "Tên Mới"}
    )

    assert response.status_code == 200, response.text
    assert response.json()["role_id"] == Role.STUDENT
    assert response.json()["full_name"] == "Tên Mới"


def test_patch_response_has_no_hashed_password(client, admin, teacher):
    _login_as(admin)

    response = client.patch(f"/users/{teacher.user_id}", json={"full_name": "Cô Lan"})

    assert response.status_code == 200, response.text
    assert "hashed_password" not in response.json()


@pytest.mark.parametrize("role_id", [Role.STUDENT, 99])
def test_patch_student_and_unknown_role_get_403(client, session, student, role_id):
    caller = _create_user(session, role_id, f"caller{role_id}")
    _login_as(caller)

    response = client.patch(f"/users/{student.user_id}", json={"full_name": "X"})

    assert response.status_code == 403


def test_patch_teacher_outside_scope_returns_403(client, teacher, student):
    _login_as(teacher)

    response = client.patch(f"/users/{student.user_id}", json={"full_name": "X"})

    assert response.status_code == 403
    assert response.json() == NOT_ALLOWED


def test_patch_admin_self_returns_200(client, admin):
    _login_as(admin)

    response = client.patch(
        f"/users/{admin.user_id}",
        json={"full_name": "Quản trị viên", "email": "quantri@st.utc2.edu.vn"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Quản trị viên"
    assert body["email"] == "quantri@st.utc2.edu.vn"
    assert body["role_id"] == Role.ADMIN
    assert "hashed_password" not in body


def test_patch_admin_self_resubmitting_own_email_is_not_conflict(client, session, admin):
    admin.email = "quantri@st.utc2.edu.vn"
    session.add(admin)
    session.commit()
    _login_as(admin)

    response = client.patch(
        f"/users/{admin.user_id}",
        json={"full_name": "Quản trị viên", "email": "quantri@st.utc2.edu.vn"},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Quản trị viên"


def test_patch_admin_self_duplicate_email_returns_409(client, session, admin):
    taken = _create_user(session, Role.TEACHER, "gv2")
    taken.email = "gv2@st.utc2.edu.vn"
    session.add(taken)
    session.commit()
    _login_as(admin)

    response = client.patch(f"/users/{admin.user_id}", json={"email": "gv2@st.utc2.edu.vn"})

    assert response.status_code == 409
    assert response.json() == {"error_code": "CONFLICT", "message": "Email đã được đăng ký"}


def test_patch_admin_self_student_code_returns_422_field_not_editable(client, admin):
    _login_as(admin)

    response = client.patch(f"/users/{admin.user_id}", json={"student_code": "6851071009"})

    assert response.status_code == 422
    assert response.json()["error_code"] == "FIELD_NOT_EDITABLE"


def test_patch_admin_other_admin_returns_403(client, session, admin):
    other_admin = _create_user(session, Role.ADMIN, "admin2")
    _login_as(admin)

    response = client.patch(f"/users/{other_admin.user_id}", json={"full_name": "X"})

    assert response.status_code == 403
    assert response.json() == NOT_ALLOWED


def test_patch_teacher_self_returns_403(client, teacher):
    _login_as(teacher)

    response = client.patch(f"/users/{teacher.user_id}", json={"full_name": "X"})

    assert response.status_code == 403
    assert response.json() == NOT_ALLOWED


def test_patch_student_self_returns_403(client, student):
    _login_as(student)

    response = client.patch(f"/users/{student.user_id}", json={"full_name": "X"})

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"


def test_patch_requires_login_returns_401(client, student):
    response = client.patch(f"/users/{student.user_id}", json={"full_name": "X"})

    assert response.status_code == 401


def test_patch_unknown_user_returns_404_user_not_found(client, admin):
    _login_as(admin)

    response = client.patch(f"/users/{uuid.uuid4()}", json={"full_name": "X"})

    assert response.status_code == 404
    assert response.json()["error_code"] == "USER_NOT_FOUND"


def test_patch_non_string_email_returns_422_invalid_format(client, admin, student):
    _login_as(admin)

    response = client.patch(f"/users/{student.user_id}", json={"email": 123})

    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_FORMAT"
