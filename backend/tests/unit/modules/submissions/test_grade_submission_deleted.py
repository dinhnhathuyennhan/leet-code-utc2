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


def _delete_on_nth_commit(monkeypatch, engine, submission_id: int, nth: int):
    """Session xoá hàng bài nộp ngay trước lần commit thứ ``nth``, mô phỏng admin xoá giữa get và commit."""
    real_session = judge_service.Session
    counter = {"n": 0}

    class RacingSession(real_session):
        def commit(self):
            counter["n"] += 1
            if counter["n"] == nth:
                _delete_row(engine, submission_id)
            super().commit()

    monkeypatch.setattr(judge_service, "Session", RacingSession)


def test_stale_row_on_result_commit_is_tolerated(
    engine, session, enqueue_calls, pending_submission, monkeypatch, caplog
):
    submission_id = pending_submission.submission_id
    # commit 1 = chuyển processing, commit 2 = lưu kết quả cuối
    _delete_on_nth_commit(monkeypatch, engine, submission_id, 2)
    monkeypatch.setattr(judge_service, "_grade_in_chunks", lambda *a, **k: [(None, "accepted", None)])
    monkeypatch.setattr(judge_service, "_testcase_results", lambda *a, **k: [])
    monkeypatch.setattr(judge_service, "_compile_output_of", lambda *a, **k: None)

    with caplog.at_level(logging.INFO, logger=judge_service.logger.name):
        judge_service.grade_submission(submission_id)

    session.expire_all()
    assert session.get(Submission, submission_id) is None
    assert enqueue_calls == []
    assert any("bị xoá trong lúc lưu kết quả" in r.getMessage() for r in caplog.records)
    assert not any(r.levelno >= logging.ERROR for r in caplog.records)


def test_stale_row_on_processing_commit_is_tolerated(
    engine, session, enqueue_calls, pending_submission, monkeypatch, caplog
):
    submission_id = pending_submission.submission_id
    _delete_on_nth_commit(monkeypatch, engine, submission_id, 1)

    def must_not_run(*args, **kwargs):
        raise AssertionError("không được chấm bài nộp đã bị xoá")

    monkeypatch.setattr(judge_service, "_grade_in_chunks", must_not_run)

    with caplog.at_level(logging.INFO, logger=judge_service.logger.name):
        judge_service.grade_submission(submission_id)

    session.expire_all()
    assert session.get(Submission, submission_id) is None
    assert enqueue_calls == []
    assert any("đã bị xoá trước khi bắt đầu chấm" in r.getMessage() for r in caplog.records)
    assert not any(r.levelno >= logging.ERROR for r in caplog.records)


def test_stale_row_on_token_save_stops_grading_without_retry(
    engine, session, enqueue_calls, pending_submission, monkeypatch, caplog
):
    submission_id = pending_submission.submission_id
    reached = []

    def grade_saving_tokens(problem, data, testcases, tokens, save):
        _delete_row(engine, submission_id)
        save(["tok"])
        reached.append("after_save")  # không được tới đây: phải dừng chấm
        return [(None, "accepted", None)]

    monkeypatch.setattr(judge_service, "_grade_in_chunks", grade_saving_tokens)

    with caplog.at_level(logging.INFO, logger=judge_service.logger.name):
        judge_service.grade_submission(submission_id)

    session.expire_all()
    assert reached == []
    assert session.get(Submission, submission_id) is None
    assert enqueue_calls == []
    assert any("bị xoá trong lúc lưu token" in r.getMessage() for r in caplog.records)
    assert not any(r.levelno >= logging.ERROR for r in caplog.records)
