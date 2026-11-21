"""Giáo viên sửa trạng thái bài đang được máy chấm: kết quả máy chấm không được ghi đè.

Worker giữ quyền chấm bằng ``grading_claimed_at`` (lease) và mọi lần ghi đều kèm điều
kiện lease còn đúng. ``update_submission`` đổi ``status`` thì thu hồi lease, nên
``finish()``/``heartbeat`` của worker cũ khớp 0 dòng và tự bỏ kết quả.
"""

import pytest
from sqlmodel import Session

from app.models.entities import Submission
from app.modules.submissions import service as submission_service
from app.modules.submissions.judge0 import service as judge_service
from app.modules.submissions.schemas import SubmissionUpdateRequest
from app.modules.submissions.service import update_submission
from tests.support.fixtures.builders import make_submission

pytest_plugins = ("tests.support.fixtures.submission_fixtures",)


@pytest.fixture
def enqueued(monkeypatch, engine):
    monkeypatch.setattr(judge_service, "engine", engine)
    calls: list[int] = []
    monkeypatch.setattr(
        submission_service.grading_queue, "enqueue", lambda sid, *a, **k: calls.append(sid)
    )
    monkeypatch.setattr(
        judge_service.grading_queue, "enqueue", lambda sid, *a, **k: calls.append(sid)
    )
    return calls


@pytest.fixture
def in_grading(session: Session, submission_problem, submission_student, enqueued):
    """Bài nộp đang được một worker chấm dở (đã nhận lease)."""
    submission = make_submission(session, submission_problem, submission_student, status="pending")
    claim = judge_service._claim_submission(submission.submission_id)
    assert claim is not None
    return submission, claim


def _row(session: Session, submission_id: int) -> Submission:
    session.expire_all()
    return session.get(Submission, submission_id)


@pytest.mark.parametrize("status", ["accepted", "wrong_answer", "compile_error"])
def test_worker_result_does_not_overwrite_status_set_by_teacher(
    session, submission_teacher, in_grading, enqueued, status
):
    submission, claim = in_grading

    update_submission(
        session, submission.submission_id, SubmissionUpdateRequest(status=status), submission_teacher
    )
    saved = claim.finish(status="internal_error", passed_count=0)

    assert saved is False
    row = _row(session, submission.submission_id)
    assert row.status == status
    assert row.grading_claimed_at is None
    assert enqueued == []


def test_worker_heartbeat_stops_grading_after_teacher_changes_status(
    session, submission_teacher, in_grading
):
    submission, claim = in_grading
    update_submission(
        session,
        submission.submission_id,
        SubmissionUpdateRequest(status="wrong_answer"),
        submission_teacher,
    )

    with pytest.raises(judge_service._SubmissionDeleted):
        claim.save_tokens(["token"])


@pytest.mark.parametrize("status", ["pending", "processing"])
def test_reset_to_waiting_status_discards_old_worker_and_requeues(
    session, submission_teacher, in_grading, enqueued, status
):
    submission, claim = in_grading

    update_submission(
        session, submission.submission_id, SubmissionUpdateRequest(status=status), submission_teacher
    )

    assert enqueued == [submission.submission_id]
    assert claim.finish(status="accepted", passed_count=3) is False
    # Worker mới nhận được bài ngay vì lease cũ đã bị thu hồi.
    assert judge_service._claim_submission(submission.submission_id) is not None
    assert _row(session, submission.submission_id).status == "processing"


def test_feedback_or_score_only_update_keeps_worker_lease(
    session, submission_teacher, in_grading, enqueued
):
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
    assert enqueued == []


def test_status_update_revokes_lease_claimed_after_teacher_loaded_row(
    session, engine, submission_teacher, submission_problem, submission_student, enqueued,
    monkeypatch,
):
    """Worker nhận bài sau khi giáo viên đã đọc bản ghi (lease còn NULL lúc đọc)."""
    submission = make_submission(session, submission_problem, submission_student, status="pending")
    claims = []
    original = submission_service.get_visible_submission

    def load_then_worker_claims(*args, **kwargs):
        result = original(*args, **kwargs)
        claims.append(judge_service._claim_submission(submission.submission_id))
        return result

    monkeypatch.setattr(submission_service, "get_visible_submission", load_then_worker_claims)

    update_submission(
        session,
        submission.submission_id,
        SubmissionUpdateRequest(status="accepted"),
        submission_teacher,
    )

    assert claims[0] is not None
    assert claims[0].finish(status="wrong_answer", passed_count=0) is False
    assert _row(session, submission.submission_id).status == "accepted"


def test_status_update_on_idle_submission_is_unchanged(
    session, submission_teacher, submission_problem, submission_student, enqueued
):
    submission = make_submission(
        session, submission_problem, submission_student, status="wrong_answer"
    )
    submission.grading_claimed_at = None
    session.add(submission)
    session.commit()

    update_submission(
        session, submission.submission_id, SubmissionUpdateRequest(status="accepted"), submission_teacher
    )

    row = _row(session, submission.submission_id)
    assert row.status == "accepted"
    assert row.grading_claimed_at is None
    assert enqueued == []


@pytest.mark.parametrize("status", ["pending", "processing"])
def test_requeue_discards_old_judge_tokens_and_results(
    session, submission_teacher, submission_problem, submission_student, enqueued, status
):
    """Chấm lại từ đầu như regrade: worker mới không được poll lại token Judge0 cũ."""
    submission = make_submission(
        session, submission_problem, submission_student, status="wrong_answer", passed_count=2
    )
    submission.judge_tokens = ["old-token-1", "old-token-2"]
    submission.testcase_results = [{"testcase_id": 1, "status": "accepted", "time": 0.1}]
    submission.compile_output = "warning"
    session.add(submission)
    session.commit()

    update_submission(
        session, submission.submission_id, SubmissionUpdateRequest(status=status), submission_teacher
    )

    row = _row(session, submission.submission_id)
    assert row.status == status
    assert row.judge_tokens is None
    assert row.testcase_results is None
    assert row.passed_count == 0
    assert row.compile_output is None
    assert enqueued == [submission.submission_id]


def test_final_status_update_keeps_existing_results(
    session, submission_teacher, submission_problem, submission_student, enqueued
):
    submission = make_submission(
        session, submission_problem, submission_student, status="wrong_answer", passed_count=2
    )
    submission.judge_tokens = ["token"]
    session.add(submission)
    session.commit()

    update_submission(
        session, submission.submission_id, SubmissionUpdateRequest(status="accepted"), submission_teacher
    )

    row = _row(session, submission.submission_id)
    assert (row.status, row.passed_count, row.judge_tokens) == ("accepted", 2, ["token"])


def test_same_status_as_loaded_still_wins_over_worker_writing_in_between(
    session, submission_teacher, submission_problem, submission_student, enqueued, monkeypatch
):
    """GV gửi status trùng bản đã đọc, nhưng worker vừa ghi kết quả khác giữa lúc đọc và lưu."""
    submission = make_submission(session, submission_problem, submission_student, status="pending")
    session.commit()
    original = submission_service.get_visible_submission

    calls = []

    def load_then_worker_finishes(*args, **kwargs):
        result = original(*args, **kwargs)
        if not calls:  # chỉ lần đọc đầu; get_submission_detail cũng gọi lại hàm này
            calls.append(1)
            claim = judge_service._claim_submission(submission.submission_id)
            assert claim.finish(status="wrong_answer", passed_count=0)
        return result

    monkeypatch.setattr(submission_service, "get_visible_submission", load_then_worker_finishes)

    update_submission(
        session, submission.submission_id, SubmissionUpdateRequest(status="pending"), submission_teacher
    )

    assert _row(session, submission.submission_id).status == "pending"
    assert enqueued == [submission.submission_id]
