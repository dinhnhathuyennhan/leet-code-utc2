"""Test tầng HTTP của ``POST /ai/review``: phân quyền và dạng response lỗi.

Logic gọi Ollama đã có test ở ``test_ai_review_service.py``; file này kiểm tra
những gì chỉ router quyết định (ai được gọi, lỗi có đi qua Global Exception
Handler hay không). Dùng ``app`` thật, thay ``get_current_user`` bằng user cố
định để không cần JWT.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_session
from app.core.dependencies import Role, get_current_user
from app.main import app
from app.models import User
from app.modules.ai_review.schemas import AIReviewResponse
from app.modules.ai_review.service import AIReviewService, AIReviewUnavailableError

BODY = {"code": "print(1)", "language": "python"}
REVIEW = AIReviewResponse(
    time_complexity="O(n^2)",
    space_complexity="O(1)",
    complexity_explanation="Hai vòng lặp lồng nhau.",
    issues=[],
    optimization={
        "is_optimizable": False,
        "suggestion": "Không có.",
        "expected_time_complexity": "O(n^2)",
        "expected_space_complexity": "O(1)",
    },
    summary="Đã tối ưu.",
)


@pytest.fixture()
def client(session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _login_as(role_id: int) -> None:
    user = User(
        user_id=f"caller{role_id}",
        full_name="Người Gọi",
        email=f"caller{role_id}@st.utc2.edu.vn",
        hashed_password="x",
        role_id=role_id,
    )
    app.dependency_overrides[get_current_user] = lambda: user


@pytest.fixture()
def service_khong_duoc_goi(monkeypatch):
    """Chặn service: dùng cho các test mà request phải bị từ chối trước đó."""

    async def review(data, transport=None):
        raise AssertionError("request đáng ra phải bị chặn trước khi tới service")

    monkeypatch.setattr(AIReviewService, "review", staticmethod(review))


@pytest.mark.parametrize("role_id", [Role.ADMIN, Role.TEACHER, Role.STUDENT])
def test_ba_vai_tro_duoc_phep_goi(client, monkeypatch, role_id):
    called = {}

    async def review(data, transport=None):
        called["code"] = data.code
        return REVIEW

    monkeypatch.setattr(AIReviewService, "review", staticmethod(review))
    _login_as(role_id)

    response = client.post("/ai/review", json=BODY)

    assert response.status_code == 200
    assert called["code"] == "print(1)"
    assert response.json()["time_complexity"] == "O(n^2)"


def test_role_la_bi_chan_403(client, service_khong_duoc_goi):
    """Role không nằm trong whitelist (vd role mới thêm sau này) phải bị chặn."""
    _login_as(99)

    response = client.post("/ai/review", json=BODY)

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"


def test_chua_dang_nhap_bi_chan(client, service_khong_duoc_goi):
    app.dependency_overrides.pop(get_current_user, None)

    response = client.post("/ai/review", json=BODY)

    assert response.status_code in (401, 403)


def test_loi_service_di_qua_global_exception_handler(client, monkeypatch):
    async def review(data, transport=None):
        raise AIReviewUnavailableError("Không thể kết nối AI Server.")

    monkeypatch.setattr(AIReviewService, "review", staticmethod(review))
    _login_as(Role.STUDENT)

    response = client.post("/ai/review", json=BODY)

    assert response.status_code == 503
    # Phải là ErrorResponse của handler tập trung, không phải {"detail": ...} của FastAPI
    body = response.json()
    assert body == {
        "error_code": "AI_UNAVAILABLE",
        "message": "Không thể kết nối AI Server.",
    }


def test_body_thieu_code_tra_422(client, service_khong_duoc_goi):
    _login_as(Role.STUDENT)

    response = client.post("/ai/review", json={"language": "python"})

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"
