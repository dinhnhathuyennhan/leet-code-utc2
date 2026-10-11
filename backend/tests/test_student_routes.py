"""Test tầng HTTP của ``POST /students/import``: phân quyền, status code, body lỗi.

Dùng ``app`` thật (có Global Exception Handler), thay ``get_session`` bằng
SQLite in-memory và ``get_current_user`` bằng user cố định để không cần JWT.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.db import get_session
from app.dependencies import Role, get_current_user
from app.main import app
from app.services.student_service import MAX_IMPORT_FILE_BYTES
from models import User

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SHEET = "IT1.001.3-1-26-CQ.67.CNTT"


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


def _upload(client: TestClient, contents: bytes, filename: str = "ds.xlsx"):
    return client.post(
        "/students/import", files={"file": (filename, contents, XLSX_MIME)}
    )


@pytest.fixture()
def one_student_file(class_list_xlsx) -> bytes:
    return class_list_xlsx({SHEET: [("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT")]})


@pytest.mark.parametrize("role_id", [Role.ADMIN, Role.TEACHER])
def test_admin_and_teacher_can_import(client, one_student_file, role_id):
    _login_as(role_id)

    response = _upload(client, one_student_file)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["created"] == [
        {
            "user_id": "6751071001",
            "full_name": "Nguyễn Văn An",
            "email": "6751071001@st.utc2.edu.vn",
            "class_id": "CQ.67.CNTT",
            "temporary_password": "6751071001",
        }
    ]
    assert body["skipped"] == []
    assert body["errors"] == []
    # Không bao giờ trả hashed_password
    assert "hashed_password" not in response.text


@pytest.mark.parametrize("role_id", [Role.STUDENT, 99])
def test_student_and_unknown_role_are_forbidden(client, session, one_student_file, role_id):
    _login_as(role_id)

    response = _upload(client, one_student_file)

    assert response.status_code == 403
    assert session.get(User, "6751071001") is None


def test_requires_login(client, one_student_file):
    response = _upload(client, one_student_file)

    assert response.status_code == 401


def test_corrupt_file_returns_422_not_500(client):
    _login_as(Role.ADMIN)

    response = _upload(client, b"not a zip file")

    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_EXCEL_FORMAT"


def test_wrong_extension_returns_422(client, one_student_file):
    _login_as(Role.ADMIN)

    response = _upload(client, one_student_file, filename="ds.csv")

    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_EXCEL_FORMAT"


def test_file_over_size_limit_returns_400(client):
    _login_as(Role.ADMIN)

    response = _upload(client, b"x" * (MAX_IMPORT_FILE_BYTES + 1))

    assert response.status_code == 400
    assert response.json()["error_code"] == "EXCEL_FILE_TOO_LARGE"


def test_file_without_class_list_header_returns_422(client, class_list_xlsx):
    _login_as(Role.ADMIN)

    response = _upload(client, class_list_xlsx({"Huong dan": None}))

    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_EXCEL_FORMAT"


def test_missing_file_field_returns_422(client):
    _login_as(Role.ADMIN)

    response = client.post("/students/import")

    assert response.status_code == 422


def test_rows_with_errors_still_return_201(client, class_list_xlsx):
    """Use-case E1: không dòng nào hợp lệ vẫn trả 201 kèm danh sách lỗi."""
    _login_as(Role.ADMIN)
    contents = class_list_xlsx({SHEET: [(None, "Nguyễn Văn", "An", "CQ.67.CNTT")]})

    response = _upload(client, contents)

    assert response.status_code == 201
    body = response.json()
    assert body["created"] == []
    assert body["errors"] == [
        {
            "sheet": SHEET,
            "row": 12,
            "user_id": None,
            "reason": "Mã sinh viên không được trống",
        }
    ]
