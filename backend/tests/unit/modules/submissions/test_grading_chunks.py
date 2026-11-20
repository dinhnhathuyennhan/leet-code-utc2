"""Chấm theo lô (dừng sớm khi TLE) và lưu kết quả từng testcase."""

from types import SimpleNamespace

import pytest
from sqlmodel import Session

from app.core import config
from app.models.entities import Submission, User
from app.modules.submissions.judge0 import service as judge_service
from app.modules.submissions.judge0.schemas import CodeRequest
from app.modules.submissions.student_service import get_student_submission_detail
from app.modules.submissions.testcase_results import build_testcase_results
from tests.support.fixtures.builders import make_testcase

pytest_plugins = ("tests.support.fixtures.submission_fixtures",)


def _testcases(n: int) -> list[SimpleNamespace]:
    return [SimpleNamespace(testcase_id=i + 1, input="[]", is_sample=i == 0) for i in range(n)]


def _fake_judge(status_of):
    """`_run_judge` giả: trạng thái theo testcase_id, ghi lại số test của mỗi lô."""
    calls: list[int] = []

    def fake(problem, data, testcases, timeout, tokens=None, on_tokens=None):
        calls.append(len(testcases))
        if on_tokens is not None:
            on_tokens([f"t{tc.testcase_id}" for tc in testcases])
        return [
            (SimpleNamespace(time=0.1), status_of(tc.testcase_id), None) for tc in testcases
        ]

    return fake, calls


@pytest.fixture
def problem():
    return SimpleNamespace(time_limit_seconds=1, function_name=None)


@pytest.fixture(autouse=True)
def _chunk_of_ten(monkeypatch):
    monkeypatch.setattr(config, "GRADING_CHUNK_SIZE", 10)


def test_grades_all_chunks_when_no_tle(monkeypatch, problem):
    fake, calls = _fake_judge(lambda i: "accepted" if i % 2 else "wrong_answer")
    monkeypatch.setattr(judge_service, "_run_judge", fake)
    saved: list[list[str]] = []

    judged = judge_service._grade_in_chunks(
        problem, CodeRequest(language="python", code="x"), _testcases(25), None, saved.append
    )

    assert calls == [10, 10, 5]
    assert [status for _, status, _ in judged].count("accepted") == 13
    assert saved[-1] == [f"t{i}" for i in range(1, 26)]


def test_stops_after_chunk_with_tle_and_marks_rest_skipped(monkeypatch, problem):
    fake, calls = _fake_judge(lambda i: "time_limit_exceeded" if i == 3 else "accepted")
    monkeypatch.setattr(judge_service, "_run_judge", fake)

    judged = judge_service._grade_in_chunks(
        problem, CodeRequest(language="python", code="x"), _testcases(50), None, lambda _: None
    )

    statuses = [status for _, status, _ in judged]
    assert calls == [10]
    assert len(statuses) == 50
    assert statuses[2] == "time_limit_exceeded"
    assert statuses[10:] == ["skipped"] * 40
    assert judge_service._overall_status(statuses) == "time_limit_exceeded"


def test_compile_error_is_not_resubmitted_for_every_chunk(monkeypatch, problem):
    fake, calls = _fake_judge(lambda i: "compile_error")
    monkeypatch.setattr(judge_service, "_run_judge", fake)

    judged = judge_service._grade_in_chunks(
        problem, CodeRequest(language="python", code="x"), _testcases(30), None, lambda _: None
    )

    assert calls == [10]
    assert [status for _, status, _ in judged] == ["compile_error"] * 30


def test_resumes_with_saved_tokens_per_chunk(monkeypatch, problem):
    seen_tokens: list = []

    def fake(problem, data, testcases, timeout, tokens=None, on_tokens=None):
        seen_tokens.append(tokens)
        return [(SimpleNamespace(time=None), "accepted", None) for _ in testcases]

    monkeypatch.setattr(judge_service, "_run_judge", fake)
    tokens = [f"old{i}" for i in range(12)]  # lô 1 đủ, lô 2 mới gửi được 2/5

    judge_service._grade_in_chunks(
        problem, CodeRequest(language="python", code="x"), _testcases(15), tokens, lambda _: None
    )

    assert seen_tokens == [tokens[:10], None]


def test_reused_chunk_still_renews_the_grading_lease(monkeypatch, problem):
    """Chấm tiếp bằng token cũ không gửi lô mới, nhưng vẫn phải gọi on_tokens để gia hạn lease."""

    def fake(problem, data, testcases, timeout, tokens=None, on_tokens=None):
        return [(SimpleNamespace(time=None), "accepted", None) for _ in testcases]

    monkeypatch.setattr(judge_service, "_run_judge", fake)
    tokens = [f"old{i}" for i in range(15)]
    renewals: list[list[str]] = []

    judge_service._grade_in_chunks(
        problem, CodeRequest(language="python", code="x"), _testcases(15), tokens, renewals.append
    )

    assert renewals == [tokens, tokens]  # một lần trước mỗi lô dùng lại token


def test_chunk_timeout_covers_every_test_hitting_wall_time(problem):
    timeout = judge_service._chunk_timeout(problem, "python", 50)
    _, wall = judge_service.compute_limits(1, "python")
    assert timeout >= 50 * wall


class TestTestcaseResults:
    def test_returns_results_in_testcase_order(self):
        testcases = _testcases(3)
        submission = Submission(
            testcase_results=[
                {"testcase_id": 3, "status": "skipped", "time": None},
                {"testcase_id": 1, "status": "accepted", "time": 0.2},
                {"testcase_id": 2, "status": "wrong_answer", "time": 0.1},
            ]
        )

        results = build_testcase_results(submission, testcases)

        assert [(r.index, r.status, r.is_sample) for r in results] == [
            (1, "accepted", True),
            (2, "wrong_answer", False),
            (3, "skipped", False),
        ]

    def test_old_submission_without_results_returns_empty(self):
        assert build_testcase_results(Submission(testcase_results=None), _testcases(2)) == []

    def test_changed_testcases_after_grading_returns_empty(self):
        submission = Submission(testcase_results=[{"testcase_id": 1, "status": "accepted"}])
        assert build_testcase_results(submission, _testcases(2)) == []

    def test_student_detail_shows_hidden_status_without_hidden_data(
        self,
        session: Session,
        submission_problem,
        submission_student: User,
        pending_error_submission,
    ):
        sample = make_testcase(
            session, submission_problem, input_value="[1,2]", expected_output="3", is_sample=True
        )
        hidden = make_testcase(
            session, submission_problem, input_value="[9,9]", expected_output="18", is_sample=False
        )
        pending_error_submission.testcase_results = [
            {"testcase_id": sample.testcase_id, "status": "wrong_answer", "time": 0.1},
            {"testcase_id": hidden.testcase_id, "status": "accepted", "time": 0.2},
        ]
        session.add(pending_error_submission)
        session.commit()

        result = get_student_submission_detail(
            session, submission_student, pending_error_submission.submission_id
        )
        payload = result.model_dump()

        assert result.testcases[0].status == "wrong_answer"
        assert [(r.index, r.status, r.is_sample) for r in result.testcase_results] == [
            (1, "wrong_answer", True),
            (2, "accepted", False),
        ]
        assert "[9,9]" not in str(payload) and "18" not in str(payload["testcase_results"])


def test_tle_case_reports_wall_time_limit_instead_of_cpu_time(problem):
    _, wall = judge_service.compute_limits(problem.time_limit_seconds, "python")
    tle = judge_service._case_time(SimpleNamespace(time=0.001), "time_limit_exceeded", problem, "python")
    ok = judge_service._case_time(SimpleNamespace(time=0.02), "accepted", problem, "python")

    assert tle == wall
    assert ok == 0.02
    assert judge_service._case_time(None, "skipped", problem, "python") is None
