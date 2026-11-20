"""grade_submission bỏ qua kết quả của bài nộp bị xoá trong lúc chấm (admin xoá khoá học)."""

import logging

import pytest
from sqlmodel import Session

from app.models.entities import Problem, Submission, User
from app.modules.submissions.judge0 import service as judge_service
from app.modules.submissions.judge0.judge0_client import Judge0Error
from tests.support.fixtures.builders import make_submission

pytest_plugins = ("tests.support.fixtures.submission_fixtures",)


@pytest.fixture
def enqueue_calls(monkeypatch, engine):
    monkeypatch.setattr(judge_service, "engine", engine)
    calls: list[tuple] = []
    monkeypatch.setattr(
        judge_service.grading_queue, "enqueue", lambda *args, **kwargs: calls.append((args, kwargs))
    )
    return calls


@pytest.fixture
def pending_submission(
    session: Session, submission_problem: Problem, submission_student: User
) -> Submission:
    submission = make_submission(session, submission_problem, submission_student, status="pending")
    session.commit()
    return submission


def _delete_row(engine, submission_id: int) -> None:
    with Session(engine) as other:
        other.delete(other.get(Submission, submission_id))
        other.commit()


def test_result_is_dropped_when_submission_deleted_mid_grading(
    engine, session, enqueue_calls, pending_submission, monkeypatch, caplog
):
    submission_id = pending_submission.submission_id

    def fake_grade(*args, **kwargs):
        _delete_row(engine, submission_id)
        return [(None, "accepted", None)]

    monkeypatch.setattr(judge_service, "_grade_in_chunks", fake_grade)
    monkeypatch.setattr(judge_service, "_testcase_results", lambda *a, **k: [])
    monkeypatch.setattr(judge_service, "_compile_output_of", lambda *a, **k: None)

    with caplog.at_level(logging.INFO, logger=judge_service.logger.name):
        judge_service.grade_submission(submission_id)

    session.expire_all()
    assert session.get(Submission, submission_id) is None
    assert enqueue_calls == []
    assert any("đã bị xoá" in r.getMessage() for r in caplog.records)


def test_deleted_submission_is_not_retried_after_judge0_error(
    engine, session, enqueue_calls, pending_submission, monkeypatch
):
    submission_id = pending_submission.submission_id

    def failing_grade(*args, **kwargs):
        _delete_row(engine, submission_id)
        raise Judge0Error("down")

    monkeypatch.setattr(judge_service, "_grade_in_chunks", failing_grade)

    judge_service.grade_submission(submission_id)

    session.expire_all()
    assert session.get(Submission, submission_id) is None
    assert enqueue_calls == []


def test_returns_early_when_submission_already_gone(engine, enqueue_calls, monkeypatch):
    def must_not_run(*args, **kwargs):
        raise AssertionError("không được chấm bài nộp không tồn tại")

    monkeypatch.setattr(judge_service, "_grade_in_chunks", must_not_run)

    judge_service.grade_submission(12345)

    assert enqueue_calls == []
