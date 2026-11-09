"""Test tầng HTTP của ``POST /ai/review/{id}``.

Logic gọi Ollama đã có test ở ``test_ai_review_service.py``; file này kiểm tra
điều kiện nghiệp vụ: chỉ sinh viên chủ bài nộp, chỉ bài đã pass hết testcase,
và code gửi cho AI lấy từ DB. Dùng ``app`` thật, thay ``get_current_user`` bằng
user cố định để không cần JWT.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_session
from app.core.dependencies import Role, get_current_user
from app.main import app
from app.models import User
from app.modules.ai_review.schemas import MAX_REVIEW_CODE_CHARS, AIReviewResponse
from app.modules.ai_review.service import AIReviewService, AIReviewUnavailableError
from tests.support.fixtures.builders import (
    make_course,
    make_lesson,
    make_problem,
    make_submission,
    make_user,
)

REVIEW = AIReviewResponse(
    time_complexity="O(n)",
    space_complexity="O(1)",
    complexity_explanation="Vòng lặp duyệt từ 2 tới n-1.",
    issues=["Duyệt ước quá số lần cần thiết"],
    optimization={
        "is_optimizable": True,
        "suggestion": "Chỉ cần duyệt ước tới sqrt(n).",
        "expected_time_complexity": "O(sqrt(n))",
        "expected_space_complexity": "O(1)",
    },
    summary="Có thể giảm từ O(n) xuống O(sqrt(n)).",
)


@pytest.fixture()
def client(session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def student(session) -> User:
    return make_user(session, "SV001", Role.STUDENT)


@pytest.fixture()
def problem(session):
    teacher = make_user(session, "GV001", Role.TEACHER)
    lesson = make_lesson(session, make_course(session, teacher, "CS101"))
    return make_problem(
        session,
        lesson,
        title="Kiểm tra số nguyên tố",
        description="Cho n, trả về True nếu n là số nguyên tố.",
        constraints="1 <= n <= 10^9",
        total_number_testcase=3,
    )


def _submission(session, problem, student, *, status="accepted", passed_count=3, code=None):
    submission = make_submission(session, problem, student, status=status, passed_count=passed_count)
    if code is not None:
        submission.submitted_code = code
        session.add(submission)
        session.flush()
    return submission


def _login(user: User) -> None:
    app.dependency_overrides[get_current_user] = lambda: user


@pytest.fixture()
def captured(monkeypatch) -> dict:
    """Thay service bằng bản giả, ghi lại dữ liệu được gửi cho AI."""
    calls: dict = {}

    async def review(data, transport=None):
        calls["data"] = data
        return REVIEW

    monkeypatch.setattr(AIReviewService, "review", staticmethod(review))
    return calls


def test_default_locale_is_vietnamese(client, session, problem, student, captured):
    """Client cũ không gửi body vẫn nhận review tiếng Việt."""
    submission = _submission(session, problem, student)
    _login(student)

    response = client.post(_url(submission))

    assert response.status_code == 200
    assert captured["data"].locale == "vi"


def test_empty_body_also_uses_vietnamese(client, session, problem, student, captured):
    submission = _submission(session, problem, student)
    _login(student)

    response = client.post(_url(submission), json={})

    assert response.status_code == 200
    assert captured["data"].locale == "vi"


def test_sending_locale_en_reviews_in_english(client, session, problem, student, captured):
    submission = _submission(session, problem, student)
    _login(student)

    response = client.post(_url(submission), json={"locale": "en"})

    assert response.status_code == 200
    assert captured["data"].locale == "en"


def test_invalid_locale_returns_422(client, session, problem, student, captured):
    submission = _submission(session, problem, student)
    _login(student)

    response = client.post(_url(submission), json={"locale": "fr"})

    assert response.status_code == 422
    assert "data" not in captured


def test_body_can_only_change_locale_not_code(client, session, problem, student, captured):
    """Body có `code`/`language` lạ phải bị bỏ qua (extra=ignore), không ghi đè DB."""
    submission = _submission(session, problem, student, code="print('da nop')")
    _login(student)

    client.post(
        _url(submission),
        json={"locale": "en", "code": "print('code khac')", "language": "cpp"},
    )

    assert captured["data"].code == "print('da nop')"
    assert captured["data"].language == "python"
    assert captured["data"].locale == "en"


def _url(submission) -> str:
    return f"/ai/review/{submission.submission_id}"


def test_accepted_submission_is_reviewed_with_code_from_db(client, session, problem, student, captured):
    code = "def is_prime(n):\n    for i in range(2, n):\n        if n % i == 0: return False\n    return True"
    submission = _submission(session, problem, student, code=code)
    _login(student)

    response = client.post(_url(submission))

    assert response.status_code == 200
    assert response.json()["optimization"]["expected_time_complexity"] == "O(sqrt(n))"
    data = captured["data"]
    assert data.code == code
    assert data.language == "python"
    assert data.problem_title == "Kiểm tra số nguyên tố"
    assert data.constraints == "1 <= n <= 10^9"


def test_client_body_is_ignored(client, session, problem, student, captured):
    """Client không thể thay code: endpoint luôn dùng code của bài nộp."""
    submission = _submission(session, problem, student, code="print('da nop')")
    _login(student)

    client.post(_url(submission), json={"code": "print('code khac')", "language": "cpp"})

    assert captured["data"].code == "print('da nop')"
    assert captured["data"].language == "python"


@pytest.mark.parametrize(
    ("status", "passed_count"),
    [
        ("wrong_answer", 2),
        ("compile_error", 0),
        ("time_limit_exceeded", 2),
        ("pending", 0),
        ("processing", 0),
        # status accepted nhưng chưa đủ testcase (vd giáo viên thêm testcase sau khi chấm)
        ("accepted", 2),
    ],
)
def test_submission_not_fully_passed_returns_409(client, session, problem, student, captured, status, passed_count):
    submission = _submission(session, problem, student, status=status, passed_count=passed_count)
    _login(student)

    response = client.post(_url(submission))

    assert response.status_code == 409
    assert response.json()["error_code"] == "SUBMISSION_NOT_ACCEPTED"
    assert "data" not in captured


def test_submission_without_testcases_is_not_reviewed(client, session, student, captured):
    teacher = make_user(session, "GV002", Role.TEACHER)
    empty = make_problem(session, make_lesson(session, make_course(session, teacher, "CS102")))
    submission = _submission(session, empty, student, passed_count=0)
    _login(student)

    response = client.post(_url(submission))

    assert response.status_code == 409
    assert "data" not in captured


def test_other_student_submission_returns_404(client, session, problem, student, captured):
    submission = _submission(session, problem, student)
    _login(make_user(session, "SV002", Role.STUDENT))

    response = client.post(_url(submission))

    assert response.status_code == 404
    assert "data" not in captured


def test_nonexistent_submission_returns_404(client, student, captured):
    _login(student)

    response = client.post("/ai/review/999999")

    assert response.status_code == 404


@pytest.mark.parametrize("role_id", [Role.ADMIN, Role.TEACHER, 99])
def test_non_student_role_is_forbidden_403(client, session, problem, student, captured, role_id):
    submission = _submission(session, problem, student)
    _login(make_user(session, f"U{role_id}", role_id))

    response = client.post(_url(submission))

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"
    assert "data" not in captured


def test_unauthenticated_request_is_blocked(client, session, problem, student, captured):
    submission = _submission(session, problem, student)
    app.dependency_overrides.pop(get_current_user, None)

    response = client.post(_url(submission))

    assert response.status_code in (401, 403)
    assert "data" not in captured


# ─── Route free-form (admin/teacher): POST /ai/review ───────────────────────


@pytest.mark.parametrize("role_id", [Role.ADMIN, Role.TEACHER, Role.STUDENT])
def test_free_form_route_allows_all_three_roles(client, session, captured, role_id):
    _login(make_user(session, f"F{role_id}", role_id))

    response = client.post("/ai/review", json={"code": "print(1)", "language": "python"})

    assert response.status_code == 200
    assert captured["data"].code == "print(1)"


def test_free_form_route_unknown_role_is_forbidden_403(client, session, captured):
    _login(make_user(session, "F99", 99))

    response = client.post("/ai/review", json={"code": "print(1)"})

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"
    assert "data" not in captured


def test_free_form_route_unauthenticated_is_blocked(client, session, captured):
    app.dependency_overrides.pop(get_current_user, None)

    response = client.post("/ai/review", json={"code": "print(1)"})

    assert response.status_code in (401, 403)
    assert "data" not in captured


def test_too_long_code_returns_422(client, session, problem, student, captured):
    submission = _submission(session, problem, student, code="x" * (MAX_REVIEW_CODE_CHARS + 1))
    _login(student)

    response = client.post(_url(submission))

    assert response.status_code == 422
    assert response.json()["error_code"] == "CODE_TOO_LONG"
    assert "data" not in captured


def test_endpoint_accepts_arbitrary_code(client, student, captured):
    """`POST /ai/review` (không có submission_id) review code tuỳ ý — route của admin.

    Route này tồn tại ở develop (dùng cho admin/teacher), nên phải giữ lại.
    Sinh viên vẫn dùng `/ai/review/{submission_id}` để review bài nộp đã pass.
    """
    _login(student)

    response = client.post("/ai/review", json={"code": "print(1)", "language": "python"})

    assert response.status_code == 200
    assert captured["data"].code == "print(1)"
    assert captured["data"].language == "python"
    # Code tuỳ ý chưa chắc đã pass testcase -> không giả định "passed ALL".
    assert captured["data"].free_form is True


def test_missing_code_returns_422(client, student):
    _login(student)

    response = client.post("/ai/review", json={"language": "python"})

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"


def test_service_error_goes_through_global_exception_handler(client, session, problem, student, monkeypatch):
    async def review(data, transport=None):
        raise AIReviewUnavailableError("Không thể kết nối AI Server.")

    monkeypatch.setattr(AIReviewService, "review", staticmethod(review))
    submission = _submission(session, problem, student)
    _login(student)

    response = client.post(_url(submission))

    assert response.status_code == 503
    assert response.json() == {
        "error_code": "AI_UNAVAILABLE",
        "message": "Không thể kết nối AI Server.",
    }
