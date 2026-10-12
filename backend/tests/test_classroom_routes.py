"""Test tầng HTTP của ``/classes``: phân quyền, status code, body lỗi.

Dùng ``app`` thật (có Global Exception Handler), thay ``get_session`` bằng
SQLite in-memory và ``get_current_user`` bằng user cố định để không cần JWT.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.db import get_session
from app.dependencies import Role, get_current_user
from app.main import app
from models import Class, User

CNTT_67 = {"type": "CQ", "course_number": 67, "department": "CNTT"}


@pytest.fixture()
def client(session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _login_as(role_id: int) -> None:
    user = User(
        user_id=f"caller{role_id}",
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


def _add_student(session, user_id: str, class_id: str) -> None:
    session.add(
        User(
            user_id=user_id,
            full_name="Sinh viên",
            email=f"{user_id}@example.com",
            hashed_password="placeholder",
            role_id=Role.STUDENT,
            class_id=class_id,
        )
    )
    session.commit()


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
    _add_student(session, "sv1", "CQ.67.CNTT")

    response = client.delete("/classes/CQ.67.CNTT")

    assert response.status_code == 409
    assert response.json() == {
        "error_code": "CONFLICT",
        "message": "Lớp CQ.67.CNTT đang có 1 sinh viên, không thể xóa",
    }
    assert session.get(User, "sv1").class_id == "CQ.67.CNTT"


def test_delete_class_not_found_returns_404(client):
    _login_as(Role.ADMIN)

    response = client.delete("/classes/CQ.67.CNTT")

    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"
