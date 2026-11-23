"""Test tầng HTTP của ``/classes``: phân quyền, status code, body lỗi.

Dùng ``app`` thật (có Global Exception Handler), thay ``get_session`` bằng
SQLite in-memory và ``get_current_user`` bằng user cố định để không cần JWT.
"""

from collections.abc import Iterator
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_session
from app.core.dependencies import Role, get_current_user
from app.main import app
from app.models import Class, User

CNTT_67 = {"type": "CQ", "course_number": 67, "department": "CNTT"}


@pytest.fixture()
def client(session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _login_as(role_id: int) -> None:
    user = User(
        user_id=uuid.uuid4(),
        full_name="Người gọi",
        email=f"caller{role_id}@example.com",
        hashed_password="placeholder",
        role_id=role_id,
    )
    app.dependency_overrides[get_current_user] = lambda: user


def _add_class(session, class_id: str = "CQ.67.CNTT") -> None:
    class_type, course_number, department = class_id.split(".", 2)
    session.add(
        Class(
            class_id=class_id,
            type=class_type,
            course_number=int(course_number),
            department=department,
        )
    )
    session.commit()


def _add_student(session, user_id: str, class_id: str) -> User:
    student = User(
        user_id=uuid.uuid4(),
        student_code=user_id if user_id.isascii() and user_id.isdigit() and len(user_id) == 10 else None,
        full_name="Sinh viên",
        email=f"{user_id}@example.com",
        hashed_password="placeholder",
        role_id=Role.STUDENT,
        class_id=class_id,
    )
    session.add(student)
    session.commit()
    return student


# ---------- POST /classes ----------


@pytest.mark.parametrize("role_id", [Role.ADMIN, Role.TEACHER])
def test_admin_and_teacher_can_create_class(client, session, role_id):
    _login_as(role_id)

    response = client.post(
        "/classes", json={"type": "CQ", "course_number": 67, "department": "KTXDCTGT.2"}
    )

    assert response.status_code == 201, response.text
    assert response.json() == {
        "class_id": "CQ.67.KTXDCTGT.2",
        "type": "CQ",
        "course_number": 67,
        "department": "KTXDCTGT.2",
        "student_count": 0,
    }
    assert session.get(Class, "CQ.67.KTXDCTGT.2") is not None


@pytest.mark.parametrize("role_id", [Role.STUDENT, 99])
def test_student_and_unknown_role_cannot_create_class(client, session, role_id):
    _login_as(role_id)

    response = client.post("/classes", json=CNTT_67)

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"
    assert session.get(Class, "CQ.67.CNTT") is None


def test_create_class_requires_login(client):
    response = client.post("/classes", json=CNTT_67)

    assert response.status_code == 401


def test_create_class_ignores_class_id_in_body(client):
    _login_as(Role.ADMIN)

    response = client.post("/classes", json={**CNTT_67, "class_id": "HACK"})

    assert response.status_code == 201
    assert response.json()["class_id"] == "CQ.67.CNTT"


def test_create_duplicate_class_returns_409(client, session):
    _login_as(Role.TEACHER)
    _add_class(session)

    response = client.post("/classes", json=CNTT_67)

    assert response.status_code == 409
    assert response.json() == {
        "error_code": "CONFLICT",
        "message": "Lớp CQ.67.CNTT đã tồn tại",
    }


@pytest.mark.parametrize(
    ("body", "error_code", "message"),
    [
        ({**CNTT_67, "type": "   "}, "EMPTY_FIELD", "Hệ đào tạo không được trống"),
        ({**CNTT_67, "type": None}, "EMPTY_FIELD", "Hệ đào tạo không được trống"),
        ({**CNTT_67, "department": ""}, "EMPTY_FIELD", "Ngành không được trống"),
        ({**CNTT_67, "type": "C.Q"}, "INVALID_FORMAT", "Hệ đào tạo chỉ được gồm chữ cái không dấu"),
        ({**CNTT_67, "course_number": 0}, "INVALID_FORMAT", "Khoá phải là số nguyên dương"),
        ({**CNTT_67, "course_number": True}, "INVALID_FORMAT", "Khoá phải là số nguyên dương"),
        ({**CNTT_67, "department": "X" * 45}, "INVALID_FORMAT", "Mã lớp không được dài quá 50 ký tự"),
        (
            {**CNTT_67, "department": "CNTT/1"},
            "INVALID_FORMAT",
            "Ngành chỉ được gồm chữ cái, chữ số và các ký tự . & - "
            "(dấu chấm không được ở đầu, ở cuối hoặc đứng liền nhau)",
        ),
        ({**CNTT_67, "department": ["CNTT"]}, "INVALID_FORMAT", "Ngành phải là chuỗi"),
    ],
)
def test_create_class_invalid_body_returns_422_with_message(client, body, error_code, message):
    _login_as(Role.ADMIN)

    response = client.post("/classes", json=body)

    assert response.status_code == 422
    assert response.json() == {"error_code": error_code, "message": message}


@pytest.mark.parametrize(
    "body",
    [
        {**CNTT_67, "course_number": "abc"},
        {**CNTT_67, "course_number": None},
        {"type": "CQ", "course_number": 67},  # thiếu department
        {},
    ],
)
def test_create_class_wrong_type_or_missing_field_returns_validation_error(client, body):
    _login_as(Role.ADMIN)

    response = client.post("/classes", json=body)

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"


# ---------- GET /classes ----------


@pytest.mark.parametrize("role_id", [Role.ADMIN, Role.TEACHER])
def test_admin_and_teacher_can_list_classes(client, session, role_id):
    _login_as(role_id)
    _add_class(session, "CQ.68.CNTT")
    _add_class(session, "CQ.67.CNTT")
    _add_student(session, "sv1", "CQ.67.CNTT")

    response = client.get("/classes")

    assert response.status_code == 200
    assert [(c["class_id"], c["student_count"]) for c in response.json()] == [
        ("CQ.67.CNTT", 1),
        ("CQ.68.CNTT", 0),
    ]


def test_list_classes_empty_returns_empty_array(client):
    _login_as(Role.ADMIN)

    response = client.get("/classes")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("role_id", [Role.STUDENT, 99])
def test_student_and_unknown_role_cannot_list_classes(client, session, role_id):
    _login_as(role_id)
    _add_class(session)

    response = client.get("/classes")

    assert response.status_code == 403


def test_list_classes_requires_login(client):
    response = client.get("/classes")

    assert response.status_code == 401


# ---------- GET /classes/{class_id} ----------


@pytest.mark.parametrize("role_id", [Role.ADMIN, Role.TEACHER])
def test_get_class_with_dots_in_path(client, session, role_id):
    _login_as(role_id)
    _add_class(session, "CQ.67.KTXDCTGT.2")

    response = client.get("/classes/CQ.67.KTXDCTGT.2")

    assert response.status_code == 200
    assert response.json() == {
        "class_id": "CQ.67.KTXDCTGT.2",
        "type": "CQ",
        "course_number": 67,
        "department": "KTXDCTGT.2",
        "student_count": 0,
    }


def test_get_class_not_found_returns_404(client):
    _login_as(Role.ADMIN)

    response = client.get("/classes/CQ.99.CNTT")

    assert response.status_code == 404
    assert response.json() == {
        "error_code": "NOT_FOUND",
        "message": "Không tìm thấy lớp CQ.99.CNTT",
    }


@pytest.mark.parametrize("role_id", [Role.STUDENT, 99])
def test_student_and_unknown_role_cannot_get_class(client, session, role_id):
    _login_as(role_id)
    _add_class(session)

    response = client.get("/classes/CQ.67.CNTT")

    assert response.status_code == 403


# ---------- GET /classes/{class_id}/students ----------


@pytest.mark.parametrize("role_id", [Role.ADMIN, Role.TEACHER])
def test_admin_and_teacher_can_list_class_students(client, session, role_id):
    _login_as(role_id)
    _add_class(session, "CQ.67.KTXDCTGT.2")
    _add_class(session, "CQ.68.CNTT")
    student = _add_student(session, "6751071001", "CQ.67.KTXDCTGT.2")
    _add_student(session, "6851071001", "CQ.68.CNTT")

    response = client.get("/classes/CQ.67.KTXDCTGT.2/students")

    assert response.status_code == 200, response.text
    assert response.json() == [
        {
            "user_id": str(student.user_id),
            "student_code": "6751071001",
            "full_name": "Sinh viên",
            "email": "6751071001@example.com",
            "class_id": "CQ.67.KTXDCTGT.2",
        }
    ]


def test_list_class_students_not_found_returns_404(client):
    _login_as(Role.TEACHER)

    response = client.get("/classes/CQ.99.CNTT/students")

    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"


@pytest.mark.parametrize("role_id", [Role.STUDENT, 99])
def test_student_and_unknown_role_cannot_list_class_students(client, session, role_id):
    _login_as(role_id)
    _add_class(session)

    response = client.get("/classes/CQ.67.CNTT/students")

    assert response.status_code == 403


# ---------- DELETE /classes/{class_id} ----------


def test_admin_can_delete_empty_class(client, session):
    _login_as(Role.ADMIN)
    _add_class(session)

    response = client.delete("/classes/CQ.67.CNTT")

    assert response.status_code == 204
    assert response.content == b""
    assert session.get(Class, "CQ.67.CNTT") is None


@pytest.mark.parametrize("role_id", [Role.TEACHER, Role.STUDENT, 99])
def test_only_admin_can_delete_class(client, session, role_id):
    _login_as(role_id)
    _add_class(session)

    response = client.delete("/classes/CQ.67.CNTT")

    assert response.status_code == 403
    assert session.get(Class, "CQ.67.CNTT") is not None


def test_delete_class_requires_login(client, session):
    _add_class(session)

    response = client.delete("/classes/CQ.67.CNTT")

    assert response.status_code == 401
    assert session.get(Class, "CQ.67.CNTT") is not None


def test_delete_class_with_students_returns_409(client, session):
    _login_as(Role.ADMIN)
    _add_class(session)
    student = _add_student(session, "sv1", "CQ.67.CNTT")

    response = client.delete("/classes/CQ.67.CNTT")

    assert response.status_code == 409
    assert response.json() == {
        "error_code": "CONFLICT",
        "message": "Lớp CQ.67.CNTT đang có 1 sinh viên, không thể xóa",
    }
    assert session.get(User, student.user_id).class_id == "CQ.67.CNTT"


def test_delete_class_not_found_returns_404(client):
    _login_as(Role.ADMIN)

    response = client.delete("/classes/CQ.67.CNTT")

    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"


# ---------- PATCH /classes/{class_id} ----------

CNTT_68 = {"type": "CQ", "course_number": 68, "department": "CNTT"}


def test_admin_updates_class_returns_new_class_with_student_count(client, session):
    _login_as(Role.ADMIN)
    _add_class(session)
    _add_student(session, "6751070001", "CQ.67.CNTT")
    _add_student(session, "6751070002", "CQ.67.CNTT")

    response = client.patch("/classes/CQ.67.CNTT", json=CNTT_68)

    assert response.status_code == 200, response.text
    assert response.json() == {
        "class_id": "CQ.68.CNTT",
        "type": "CQ",
        "course_number": 68,
        "department": "CNTT",
        "student_count": 2,
    }
    assert session.get(Class, "CQ.67.CNTT") is None


def test_update_class_same_code_returns_200_unchanged(client, session):
    _login_as(Role.ADMIN)
    _add_class(session)
    _add_student(session, "6751070001", "CQ.67.CNTT")

    response = client.patch("/classes/CQ.67.CNTT", json=CNTT_67)

    assert response.status_code == 200
    assert response.json() == {**CNTT_67, "class_id": "CQ.67.CNTT", "student_count": 1}


def test_update_class_with_dots_in_path(client, session):
    _login_as(Role.ADMIN)
    _add_class(session, "CQ.67.KTXDCTGT.2")

    response = client.patch(
        "/classes/CQ.67.KTXDCTGT.2",
        json={"type": "CQ", "course_number": 67, "department": "KTXDCTGT.3"},
    )

    assert response.status_code == 200
    assert response.json()["class_id"] == "CQ.67.KTXDCTGT.3"


def test_users_filter_by_new_class_after_update(client, session):
    _login_as(Role.ADMIN)
    _add_class(session)
    student = _add_student(session, "6751070001", "CQ.67.CNTT")

    assert client.patch("/classes/CQ.67.CNTT", json=CNTT_68).status_code == 200

    users = client.get("/users", params={"class_id": "CQ.68.CNTT"})
    assert users.status_code == 200
    assert [u["user_id"] for u in users.json()["items"]] == [str(student.user_id)]
    assert client.get("/users", params={"class_id": "CQ.67.CNTT"}).json()["items"] == []
    assert client.get("/classes/CQ.67.CNTT").status_code == 404


@pytest.mark.parametrize("role_id", [Role.TEACHER, Role.STUDENT, 99])
def test_only_admin_can_update_class(client, session, role_id):
    _login_as(role_id)
    _add_class(session)

    response = client.patch("/classes/CQ.67.CNTT", json=CNTT_68)

    assert response.status_code == 403
    assert session.get(Class, "CQ.67.CNTT") is not None
    assert session.get(Class, "CQ.68.CNTT") is None


def test_update_class_requires_login(client, session):
    _add_class(session)

    response = client.patch("/classes/CQ.67.CNTT", json=CNTT_68)

    assert response.status_code == 401
    assert session.get(Class, "CQ.67.CNTT") is not None


def test_update_class_to_existing_returns_409(client, session):
    _login_as(Role.ADMIN)
    _add_class(session, "CQ.67.CNTT")
    _add_class(session, "CQ.68.CNTT")

    response = client.patch("/classes/CQ.67.CNTT", json=CNTT_68)

    assert response.status_code == 409
    assert response.json() == {
        "error_code": "CONFLICT",
        "message": "Lớp CQ.68.CNTT đã tồn tại",
    }


def test_update_class_not_found_returns_404(client):
    _login_as(Role.ADMIN)

    response = client.patch("/classes/CQ.99.CNTT", json=CNTT_68)

    assert response.status_code == 404
    assert response.json() == {
        "error_code": "NOT_FOUND",
        "message": "Không tìm thấy lớp CQ.99.CNTT",
    }


@pytest.mark.parametrize(
    ("body", "error_code", "message"),
    [
        ({**CNTT_68, "type": "   "}, "EMPTY_FIELD", "Hệ đào tạo không được trống"),
        ({**CNTT_68, "department": ""}, "EMPTY_FIELD", "Ngành không được trống"),
        ({**CNTT_68, "type": "C.Q"}, "INVALID_FORMAT", "Hệ đào tạo chỉ được gồm chữ cái không dấu"),
        ({**CNTT_68, "course_number": 0}, "INVALID_FORMAT", "Khoá phải là số nguyên dương"),
        ({**CNTT_68, "course_number": True}, "INVALID_FORMAT", "Khoá phải là số nguyên dương"),
        ({**CNTT_68, "department": "X" * 45}, "INVALID_FORMAT", "Mã lớp không được dài quá 50 ký tự"),
        ({**CNTT_68, "department": ["CNTT"]}, "INVALID_FORMAT", "Ngành phải là chuỗi"),
    ],
)
def test_update_class_invalid_body_returns_422_with_message(
    client, session, body, error_code, message
):
    _login_as(Role.ADMIN)
    _add_class(session)

    response = client.patch("/classes/CQ.67.CNTT", json=body)

    assert response.status_code == 422
    assert response.json() == {"error_code": error_code, "message": message}
    assert session.get(Class, "CQ.67.CNTT") is not None


def test_update_class_missing_field_returns_validation_error(client, session):
    _login_as(Role.ADMIN)
    _add_class(session)

    response = client.patch("/classes/CQ.67.CNTT", json={"type": "CQ", "course_number": 68})

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"
