"""Giới hạn lượt AI review: mỗi sinh viên tối đa ``AI_REVIEW_MAX_PER_PROBLEM`` lượt/bài tập.

- Lượt cố định theo (sinh viên, bài tập): nộp lại bài không được thêm lượt.
- Lượt gọi AI lỗi (AI bận, timeout, mất kết nối) được hoàn lại.
- Bài chưa đủ điều kiện review (chưa pass hết) không tốn lượt.
- ``GET /ai/review/{submission_id}/usage`` cho biết số lượt đã dùng / còn lại.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from app.core import config
from app.core.database import get_session
from app.core.dependencies import Role, get_current_user
from app.main import app
from app.models import AIReviewUsage, User
from app.modules.ai_review.schemas import AIReviewResponse
from app.modules.ai_review import service as ai_review_service
from app.modules.ai_review.service import (
    AIReviewLimitReachedError,
    AIReviewService,
    AIReviewTimeoutError,
    reserve_review_slot,
)
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
    complexity_explanation="Một vòng lặp.",
    issues=[],
    optimization={
        "is_optimizable": False,
        "suggestion": "Đã tối ưu.",
        "expected_time_complexity": "O(n)",
        "expected_space_complexity": "O(1)",
    },
    summary="Ổn.",
)
LIMIT_MESSAGE = "Bạn đã dùng hết 3 lượt AI review cho bài tập này"


@pytest.fixture(autouse=True)
def limit_three(monkeypatch):
    monkeypatch.setattr(config, "AI_REVIEW_MAX_PER_PROBLEM", 3)


@pytest.fixture()
def client(session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def ai_calls(monkeypatch) -> list:
    calls: list = []

    async def review(data, transport=None):
        calls.append(data)
        return REVIEW

    monkeypatch.setattr(AIReviewService, "review", staticmethod(review))
    return calls


@pytest.fixture()
def student(session) -> User:
    return make_user(session, "SV001", Role.STUDENT)


@pytest.fixture()
def lesson(session):
    teacher = make_user(session, "GV001", Role.TEACHER)
    return make_lesson(session, make_course(session, teacher, "CS101"))


@pytest.fixture()
def problem(session, lesson):
    return make_problem(session, lesson, total_number_testcase=3)


def _accepted(session, problem, student):
    return make_submission(session, problem, student, status="accepted", passed_count=3)


def _login(user: User) -> None:
    app.dependency_overrides[get_current_user] = lambda: user


def _review(client, submission):
    return client.post(f"/ai/review/{submission.submission_id}")


def _usage(client, submission) -> dict:
    response = client.get(f"/ai/review/{submission.submission_id}/usage")
    assert response.status_code == 200, response.text
    return response.json()


def test_fourth_review_of_same_problem_is_rejected_with_429(client, session, problem, student, ai_calls):
    submission = _accepted(session, problem, student)
    _login(student)

    for _ in range(3):
        assert _review(client, submission).status_code == 200

    response = _review(client, submission)

    assert response.status_code == 429
    assert response.json() == {"error_code": "AI_REVIEW_LIMIT_REACHED", "message": LIMIT_MESSAGE}
    assert len(ai_calls) == 3
    assert _usage(client, submission) == {"limit": 3, "used": 3, "remaining": 0}


def test_resubmitting_does_not_grant_more_reviews(client, session, problem, student, ai_calls):
    first = _accepted(session, problem, student)
    _login(student)
    for _ in range(3):
        _review(client, first)

    second = _accepted(session, problem, student)

    assert _review(client, second).status_code == 429
    assert _usage(client, second)["remaining"] == 0


def test_limit_is_per_problem_and_per_student(client, session, lesson, problem, student, ai_calls):
    other_problem = make_problem(session, lesson, title="Other", total_number_testcase=3)
    classmate = make_user(session, "SV002", Role.STUDENT)
    _login(student)
    for _ in range(3):
        _review(client, _accepted(session, problem, student))

    _login(student)
    assert _review(client, _accepted(session, other_problem, student)).status_code == 200
    _login(classmate)
    assert _review(client, _accepted(session, problem, classmate)).status_code == 200


def test_failed_ai_call_does_not_consume_a_review(client, session, problem, student, monkeypatch):
    async def timeout(data, transport=None):
        raise AIReviewTimeoutError("AI xử lý quá thời gian cho phép.")

    monkeypatch.setattr(AIReviewService, "review", staticmethod(timeout))
    submission = _accepted(session, problem, student)
    _login(student)

    response = _review(client, submission)

    assert response.status_code == 504
    assert _usage(client, submission) == {"limit": 3, "used": 0, "remaining": 3}
    assert session.exec(select(AIReviewUsage)).all() == []


def test_not_fully_passed_submission_does_not_consume_a_review(client, session, problem, student, ai_calls):
    submission = make_submission(session, problem, student, status="wrong_answer", passed_count=1)
    _login(student)

    assert _review(client, submission).status_code == 409
    assert _usage(client, submission)["used"] == 0
    assert ai_calls == []


def test_usage_starts_full_and_counts_down(client, session, problem, student, ai_calls):
    submission = _accepted(session, problem, student)
    _login(student)

    assert _usage(client, submission) == {"limit": 3, "used": 0, "remaining": 3}
    _review(client, submission)
    assert _usage(client, submission) == {"limit": 3, "used": 1, "remaining": 2}


def test_usage_of_other_student_submission_is_404(client, session, problem, student):
    submission = _accepted(session, problem, student)
    _login(make_user(session, "SV003", Role.STUDENT))

    response = client.get(f"/ai/review/{submission.submission_id}/usage")

    assert response.status_code == 404


@pytest.mark.parametrize("role_id", [Role.ADMIN, Role.TEACHER])
def test_usage_route_is_student_only(client, session, problem, student, role_id):
    submission = _accepted(session, problem, student)
    _login(make_user(session, f"X{role_id}", role_id))

    assert client.get(f"/ai/review/{submission.submission_id}/usage").status_code == 403


def test_slot_taken_concurrently_moves_to_next_free_number(session, problem, student, monkeypatch):
    """Request khác vừa lấy cùng số lượt: ràng buộc unique chặn, hàm thử số kế tiếp."""
    submission = _accepted(session, problem, student)
    session.add(AIReviewUsage(
        student_id=student.user_id, problem_id=problem.problem_id,
        submission_id=submission.submission_id, attempt_no=1,
        created_at=submission.submitted_datetime,
    ))
    session.commit()
    real = ai_review_service._used_attempts
    reads: list[int] = []

    def stale_first_read(*args):
        reads.append(1)
        # Lần đọc đầu chưa thấy lượt số 1 (request kia chưa commit lúc đọc)
        return set() if len(reads) == 1 else real(*args)

    monkeypatch.setattr(ai_review_service, "_used_attempts", stale_first_read)

    usage_id = reserve_review_slot(session, submission.submission_id, student)

    assert session.get(AIReviewUsage, usage_id).attempt_no == 2
    assert len(reads) == 2


def test_concurrent_requests_never_exceed_limit(session, problem, student, monkeypatch):
    submission = _accepted(session, problem, student)
    for _ in range(3):
        reserve_review_slot(session, submission.submission_id, student)
    # Mọi lần đọc đều "trễ" (thấy chưa dùng lượt nào): insert nào cũng vấp unique
    monkeypatch.setattr(ai_review_service, "_used_attempts", lambda *args: set())

    with pytest.raises(AIReviewLimitReachedError, match=LIMIT_MESSAGE):
        reserve_review_slot(session, submission.submission_id, student)
    assert len(session.exec(select(AIReviewUsage)).all()) == 3
