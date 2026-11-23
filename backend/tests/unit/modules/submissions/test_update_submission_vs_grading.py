"""Giáo viên không được sửa trạng thái bài nộp; trạng thái chỉ do máy chấm quyết định.

``PATCH /submissions/{id}`` chỉ nhận ``feedback`` và ``manual_score``. Gửi ``status``
bị từ chối (422), và cập nhật nhận xét/điểm không được đụng tới lease
(``grading_claimed_at``) của worker đang chấm, nên kết quả máy chấm vẫn được ghi.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.core.exceptions import InvalidFormatError
from app.main import app
from app.models.entities import Submission
from app.modules.submissions.judge0 import service as judge_service
from app.modules.submissions.schemas import SubmissionUpdateRequest
from app.modules.submissions.service import update_submission
from tests.support.fixtures.builders import make_submission

pytest_plugins = ("tests.support.fixtures.submission_fixtures",)

STATUS_REJECTED = "Không thể sửa trạng thái bài nộp: trạng thái do máy chấm quyết định"


@pytest.fixture
def in_grading(session: Session, submission_problem, submission_student, monkeypatch, engine):
    """Bài nộp đang được một worker chấm dở (đã nhận lease)."""
    monkeypatch.setattr(judge_service, "engine", engine)
    submission = make_submission(session, submission_problem, submission_student, status="pending")
    claim = judge_service._claim_submission(submission.submission_id)
    assert claim is not None
    return submission, claim


@pytest.fixture
def client(session: Session, submission_teacher) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: submission_teacher
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _row(session: Session, submission_id: int) -> Submission:
    session.expire_all()
    return session.get(Submission, submission_id)


@pytest.mark.parametrize("status", ["accepted", "wrong_answer", "pending", "bogus"])
def test_update_request_rejects_status(status):
    with pytest.raises(InvalidFormatError, match=STATUS_REJECTED):
        SubmissionUpdateRequest.model_validate({"status": status, "feedback": "Tốt"})


def test_update_request_allows_explicit_null_status():
    # Client gửi kèm `status: null` (không đổi gì) vẫn được chấp nhận
    data = SubmissionUpdateRequest.model_validate({"status": None, "manual_score": 7})

    assert data.manual_score == 7


@pytest.mark.parametrize("status", ["accepted", "wrong_answer"])
def test_patch_with_status_returns_422_and_leaves_row_unchanged(
    client, session, submission_problem, submission_student, status
):
    submission = make_submission(
        session, submission_problem, submission_student, status="compile_error", passed_count=0
    )

    response = client.patch(
        f"/submissions/{submission.submission_id}", json={"status": status, "feedback": "hack"}
    )

    assert response.status_code == 422
    assert response.json() == {"error_code": "INVALID_FORMAT", "message": STATUS_REJECTED}
    row = _row(session, submission.submission_id)
    assert (row.status, row.passed_count, row.feedback) == ("compile_error", 0, None)


def test_patch_feedback_and_score_still_works(
    client, session, submission_problem, submission_student
):
    submission = make_submission(
        session, submission_problem, submission_student, status="wrong_answer", passed_count=1
    )

    response = client.patch(
        f"/submissions/{submission.submission_id}", json={"feedback": "  Cần xử lý biên  ", "manual_score": 6}
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["status"], body["feedback"], body["manual_score"]) == (
        "wrong_answer", "Cần xử lý biên", 6
    )


def test_feedback_or_score_update_keeps_worker_lease(session, submission_teacher, in_grading):
    submission, claim = in_grading

    update_submission(
        session,
        submission.submission_id,
        SubmissionUpdateRequest(feedback="Đang chấm", manual_score=5),
        submission_teacher,
    )

    assert claim.finish(status="accepted", passed_count=3) is True
    row = _row(session, submission.submission_id)
    assert (row.status, row.feedback, row.manual_score) == ("accepted", "Đang chấm", 5)
