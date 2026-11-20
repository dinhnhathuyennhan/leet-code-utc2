"""Nhận quyền chấm bài bằng UPDATE có điều kiện + lease, để không chấm trùng một bài nộp.

Tình huống thật: lúc khởi động, ``grading_queue.start`` đưa lại mọi bài pending/processing
vào hàng đợi, trong khi bài đó có thể đã được enqueue (hoặc đang được backend cũ chấm khi
hai container chạy chồng lúc deploy).
"""

import logging
from datetime import timedelta

import pytest
from sqlmodel import Session

from app.core.utils.datetime_utils import as_utc, now_utc
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
        judge_service.grading_queue, "enqueue", lambda *args, **kwargs: calls.append(args)
    )
    return calls


def _submission(
    session: Session,
    problem: Problem,
    student: User,
    status: str,
    claimed_at=None,
) -> Submission:
    submission = make_submission(session, problem, student, status=status)
    submission.grading_claimed_at = claimed_at
    session.add(submission)
    session.commit()
    return submission


def _row(session: Session, submission_id: int) -> Submission:
    session.expire_all()
    return session.get(Submission, submission_id)


def _fake_judging(monkeypatch, grade):
    monkeypatch.setattr(judge_service, "_grade_in_chunks", grade)
    monkeypatch.setattr(judge_service, "_testcase_results", lambda *a, **k: [])
    monkeypatch.setattr(judge_service, "_compile_output_of", lambda *a, **k: None)


class TestClaimSubmission:
    def test_pending_submission_is_claimed(
        self, session, enqueue_calls, submission_problem, submission_student
    ):
        submission = _submission(session, submission_problem, submission_student, "pending")

        claim = judge_service._claim_submission(submission.submission_id)

        assert claim is not None
        row = _row(session, submission.submission_id)
        assert row.status == "processing"
        assert as_utc(row.grading_claimed_at) == claim.claimed_at
        assert enqueue_calls == []

    def test_second_claim_on_live_lease_is_refused_and_rechecked_after_lease(
        self, session, enqueue_calls, submission_problem, submission_student
    ):
        submission = _submission(session, submission_problem, submission_student, "pending")
        first = judge_service._claim_submission(submission.submission_id)

        second = judge_service._claim_submission(submission.submission_id)

        assert first is not None
        assert second is None
        assert as_utc(_row(session, submission.submission_id).grading_claimed_at) == first.claimed_at
        # Hẹn kiểm tra lại lúc lease hết hạn, phòng khi worker đang giữ quyền bị chết
        assert len(enqueue_calls) == 1
        submission_id, delay = enqueue_calls[0]
        assert submission_id == submission.submission_id
        lease = judge_service.GRADING_LEASE.total_seconds()
        assert lease - 5 <= delay <= lease + 1

    def test_processing_with_expired_lease_is_reclaimed(
        self, session, enqueue_calls, submission_problem, submission_student
    ):
        stale = now_utc() - judge_service.GRADING_LEASE - timedelta(seconds=1)
        submission = _submission(
            session, submission_problem, submission_student, "processing", claimed_at=stale
        )

        claim = judge_service._claim_submission(submission.submission_id)

        assert claim is not None
        assert claim.claimed_at > stale
        assert as_utc(_row(session, submission.submission_id).grading_claimed_at) == claim.claimed_at
        assert enqueue_calls == []

    def test_processing_without_lease_is_claimed(
        self, session, enqueue_calls, submission_problem, submission_student
    ):
        """Bài đang processing từ trước khi có cột lease (hoặc NULL vì lý do khác) vẫn được nhận."""
        submission = _submission(session, submission_problem, submission_student, "processing")

        assert judge_service._claim_submission(submission.submission_id) is not None

    @pytest.mark.parametrize(
        "status", ["accepted", "wrong_answer", "compile_error", "internal_error"]
    )
    def test_finished_submission_is_not_claimed(
        self, session, enqueue_calls, submission_problem, submission_student, status
    ):
        submission = _submission(session, submission_problem, submission_student, status)

        assert judge_service._claim_submission(submission.submission_id) is None
        row = _row(session, submission.submission_id)
        assert row.status == status
        assert row.grading_claimed_at is None
        assert enqueue_calls == []

    def test_missing_submission_is_not_claimed(self, enqueue_calls, caplog):
        with caplog.at_level(logging.INFO, logger=judge_service.logger.name):
            assert judge_service._claim_submission(424242) is None

        assert enqueue_calls == []
        assert any("đã bị xoá trước khi bắt đầu chấm" in r.getMessage() for r in caplog.records)


class TestGradeSubmissionClaim:
    def test_duplicate_enqueue_while_grading_does_not_grade_twice(
        self, session, enqueue_calls, submission_problem, submission_student, monkeypatch
    ):
        """Khôi phục lúc khởi động và một lượt enqueue khác cùng chạy: chỉ một lượt được chấm."""
        submission = _submission(session, submission_problem, submission_student, "pending")
        graded: list[int] = []

        def grade(problem, data, testcases, tokens, save_tokens):
            graded.append(submission.submission_id)
            # Lượt chấm thứ hai bắt đầu khi lượt đầu còn đang chờ Judge0
            judge_service.grade_submission(submission.submission_id)
            return [(None, "accepted", None)]

        _fake_judging(monkeypatch, grade)

        judge_service.grade_submission(submission.submission_id)

        assert graded == [submission.submission_id]
        row = _row(session, submission.submission_id)
        assert (row.status, row.passed_count, row.grading_claimed_at) == ("accepted", 1, None)
        # Lượt thứ hai chỉ hẹn kiểm tra lại, không chấm
        assert [call[0] for call in enqueue_calls] == [submission.submission_id]

    def test_result_saved_and_lease_released(
        self, session, enqueue_calls, submission_problem, submission_student, monkeypatch
    ):
        submission = _submission(session, submission_problem, submission_student, "pending")
        _fake_judging(monkeypatch, lambda *a, **k: [(None, "accepted", None), (None, "wrong_answer", None)])

        judge_service.grade_submission(submission.submission_id)

        row = _row(session, submission.submission_id)
        assert (row.status, row.passed_count) == ("wrong_answer", 1)
        assert row.testcase_results == []
        assert row.grading_claimed_at is None
        assert enqueue_calls == []

    def test_worker_that_lost_its_lease_does_not_overwrite_result(
        self, engine, session, enqueue_calls, submission_problem, submission_student, monkeypatch, caplog
    ):
        """Worker chậm bị coi là chết, worker khác đã nhận lại bài: kết quả cũ bị bỏ, không retry."""
        submission = _submission(session, submission_problem, submission_student, "pending")
        takeover = now_utc() + timedelta(seconds=30)

        def grade(*args, **kwargs):
            with Session(engine) as other:
                row = other.get(Submission, submission.submission_id)
                row.grading_claimed_at = takeover
                other.add(row)
                other.commit()
            return [(None, "accepted", None)]

        _fake_judging(monkeypatch, grade)

        with caplog.at_level(logging.INFO, logger=judge_service.logger.name):
            judge_service.grade_submission(submission.submission_id)

        row = _row(session, submission.submission_id)
        assert (row.status, row.passed_count) == ("processing", 0)
        assert as_utc(row.grading_claimed_at) == takeover
        assert enqueue_calls == []
        assert any("worker khác nhận chấm" in r.getMessage() for r in caplog.records)
        assert not any(r.levelno >= logging.ERROR for r in caplog.records)

    def test_worker_that_lost_its_lease_stops_at_token_save(
        self, engine, session, enqueue_calls, submission_problem, submission_student, monkeypatch
    ):
        submission = _submission(session, submission_problem, submission_student, "pending")
        reached: list[str] = []

        def grade(problem, data, testcases, tokens, save_tokens):
            with Session(engine) as other:
                row = other.get(Submission, submission.submission_id)
                row.grading_claimed_at = now_utc() + timedelta(seconds=30)
                other.add(row)
                other.commit()
            save_tokens(["tok"])
            reached.append("after_save")
            return [(None, "accepted", None)]

        _fake_judging(monkeypatch, grade)

        judge_service.grade_submission(submission.submission_id)

        assert reached == []
        row = _row(session, submission.submission_id)
        assert row.judge_tokens is None
        assert row.status == "processing"
        assert enqueue_calls == []

    def test_judge0_down_returns_to_pending_and_releases_lease(
        self, session, enqueue_calls, submission_problem, submission_student, monkeypatch
    ):
        submission = _submission(session, submission_problem, submission_student, "pending")
        submission.submitted_datetime = now_utc()
        session.add(submission)
        session.commit()

        def down(*args, **kwargs):
            raise Judge0Error("down")

        _fake_judging(monkeypatch, down)

        judge_service.grade_submission(submission.submission_id)

        row = _row(session, submission.submission_id)
        assert (row.status, row.grading_claimed_at) == ("pending", None)
        assert enqueue_calls == [(submission.submission_id, judge_service.GRADE_RETRY_DELAY_SECONDS)]
        # Lượt retry nhận lại được bài
        assert judge_service._claim_submission(submission.submission_id) is not None

    def test_unexpected_error_marks_internal_error_and_releases_lease(
        self, session, enqueue_calls, submission_problem, submission_student, monkeypatch
    ):
        submission = _submission(session, submission_problem, submission_student, "pending")

        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        _fake_judging(monkeypatch, boom)

        judge_service.grade_submission(submission.submission_id)

        row = _row(session, submission.submission_id)
        assert (row.status, row.grading_claimed_at) == ("internal_error", None)
        assert enqueue_calls == []

    def test_live_lease_is_not_graded_again(
        self, session, enqueue_calls, submission_problem, submission_student, monkeypatch
    ):
        submission = _submission(
            session, submission_problem, submission_student, "processing", claimed_at=now_utc()
        )

        def must_not_run(*args, **kwargs):
            raise AssertionError("bài đang được worker khác chấm, không được chấm lại")

        _fake_judging(monkeypatch, must_not_run)

        judge_service.grade_submission(submission.submission_id)

        assert _row(session, submission.submission_id).status == "processing"
        assert [call[0] for call in enqueue_calls] == [submission.submission_id]
