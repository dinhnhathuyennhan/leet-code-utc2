"""Dịch vụ chấm Judge0: lưu token chấm và chấm lại bài nộp."""

import pytest
from sqlmodel import Session

from app.core.exceptions import ConflictError
from app.core.utils.datetime_utils import as_utc, now_utc
from app.models.entities import Submission, User
from app.modules.submissions.judge0 import service as judge_service
from tests.support.fixtures.builders import make_submission

pytest_plugins = ("tests.support.fixtures.submission_fixtures",)


class TestSaveTokens:
    def test_tokens_are_persisted_as_a_list_and_lease_renewed(
        self, engine, session: Session, monkeypatch, submission_problem, submission_student
    ):
        submission = make_submission(session, submission_problem, submission_student, status="pending")
        session.commit()
        monkeypatch.setattr(judge_service, "engine", engine)
        claim = judge_service._claim_submission(submission.submission_id)
        first_claim = claim.claimed_at

        claim.save_tokens(["t1", "t2"])

        session.expire_all()
        row = session.get(Submission, submission.submission_id)
        assert row.judge_tokens == ["t1", "t2"]
        assert claim.claimed_at >= first_claim
        assert as_utc(row.grading_claimed_at) == claim.claimed_at

    def test_unknown_submission_raises_submission_deleted(
        self, engine, session: Session, monkeypatch
    ):
        monkeypatch.setattr(judge_service, "engine", engine)
        claim = judge_service._GradingClaim(999999, now_utc())

        with pytest.raises(judge_service._SubmissionDeleted):
            claim.save_tokens(["t1"])

        assert session.get(Submission, 999999) is None


class TestRegrade:
    def test_owner_regrades_internal_error_and_resets_fields(
        self,
        session: Session,
        submission_teacher: User,
        pending_error_submission: Submission,
        monkeypatch,
    ):
        queued: list[int] = []
        monkeypatch.setattr(judge_service.grading_queue, "enqueue", lambda sid, *a: queued.append(sid))
        submission = pending_error_submission
        submission.status = "internal_error"
        submission.passed_count = 2
        submission.compile_output = "x"
        submission.judge_tokens = ["t"]
        submission.testcase_results = [{"testcase_id": 1, "status": "accepted", "time": 0.1}]
        submission.grading_claimed_at = now_utc()
        session.add(submission)
        session.commit()

        result = judge_service.regrade(session, submission.submission_id, submission_teacher)

        assert result.status == "pending"
        assert (result.passed_count, result.compile_output) == (0, None)
        assert (result.judge_tokens, result.testcase_results) == (None, None)
        assert result.grading_claimed_at is None
        assert queued == [submission.submission_id]

    def test_non_internal_error_conflicts(
        self,
        session: Session,
        submission_teacher: User,
        pending_error_submission: Submission,
    ):
        with pytest.raises(ConflictError, match="Chỉ chấm lại được bài bị lỗi hệ thống chấm"):
            judge_service.regrade(session, pending_error_submission.submission_id, submission_teacher)
