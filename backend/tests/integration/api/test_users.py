"""Test tầng HTTP của ``POST /teachers`` và ``POST /students``: phân quyền, status code.

Logic tạo tài khoản đã có test ở ``test_user_service.py``; file này kiểm tra
những gì chỉ router quyết định (status 201, ai được gọi, response không lộ
mật khẩu). Dùng ``app`` thật, thay ``get_session`` bằng SQLite in-memory và
``get_current_user`` bằng user cố định để không cần JWT.
"""

from collections.abc import Iterator
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_session
from app.core.dependencies import Role, get_current_user
from app.main import app
from app.models import Class, User

TEACHER_BODY = {
    "full_name": "Giáo Viên Mới",
    "email": "GiaoVienMoi@st.utc2.edu.vn",
}
STUDENT_BODY = {
    "student_code": "6851071001",
    "full_name": "Sinh Viên Mới",
    "email": "6851071001@st.utc2.edu.vn",
    "class_id": "CQ.68.CNTT",
}


@pytest.fixture()
def client(session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def class_68(session) -> None:
    session.add(Class(class_id="CQ.68.CNTT", type="CQ", course_number=68, department="CNTT"))
    session.commit()


def _login_as(role_id: int) -> None:
    user = User(
        user_id=uuid.uuid4(),
        full_name="Người gọi",
        email=f"caller{role_id}@example.com",
        hashed_password="placeholder",
        role_id=role_id,
    )
    app.dependency_overrides[get_current_user] = lambda: user


# ---------- POST /teachers ----------


def test_admin_creates_teacher_returns_201(client, session):
    _login_as(Role.ADMIN)

    response = client.post("/teachers", json=TEACHER_BODY)

    assert response.status_code == 201, response.text
    body = response.json()
    assert uuid.UUID(body["user_id"])
    assert body["role_id"] == Role.TEACHER
    assert "hashed_password" not in body
    assert session.exec(User.__table__.select().where(User.email == TEACHER_BODY["email"])).first() is not None


@pytest.mark.parametrize("role_id", [Role.TEACHER, Role.STUDENT, 99])
def test_only_admin_can_create_teacher(client, session, role_id):
    _login_as(role_id)

    response = client.post("/teachers", json=TEACHER_BODY)

    assert response.status_code == 403
    assert session.exec(User.__table__.select().where(User.email == TEACHER_BODY["email"])).first() is None


def test_create_teacher_requires_login(client):
    response = client.post("/teachers", json=TEACHER_BODY)

    assert response.status_code == 401


# ---------- POST /students ----------


@pytest.mark.parametrize("role_id", [Role.ADMIN, Role.TEACHER])
def test_admin_and_teacher_create_student_returns_201(client, session, class_68, role_id):
    _login_as(role_id)

    response = client.post("/students", json=STUDENT_BODY)

    assert response.status_code == 201, response.text
    body = response.json()
    assert uuid.UUID(body["user_id"])
    assert body["student_code"] == "6851071001"
    assert body["role_id"] == Role.STUDENT
    assert body["class_id"] == "CQ.68.CNTT"
    assert "hashed_password" not in body
    assert session.exec(User.__table__.select().where(User.student_code == "6851071001")).first() is not None


@pytest.mark.parametrize("role_id", [Role.STUDENT, 99])
def test_student_and_unknown_role_cannot_create_student(client, session, class_68, role_id):
    _login_as(role_id)

    response = client.post("/students", json=STUDENT_BODY)

    assert response.status_code == 403
    assert session.exec(User.__table__.select().where(User.student_code == "6851071001")).first() is None


def test_create_student_in_missing_class_returns_404(client):
    _login_as(Role.ADMIN)

    response = client.post("/students", json={**STUDENT_BODY, "class_id": "CQ.99.CNTT"})

    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"


def test_create_student_requires_login(client, class_68):
    response = client.post("/students", json=STUDENT_BODY)

    assert response.status_code == 401
