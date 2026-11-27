"""LCUTC2-73: output giả mạo hoặc hỏng từ harness.

- Dấu mốc kết quả ngẫu nhiên cho mỗi lần chấm; dấu mốc cố định cũ không còn được nhận.
- Output không hợp lệ (thiếu mốc, mốc xuất hiện nhiều lần, JSON hỏng, có rác phía sau,
  quá lớn) chấm Wrong Answer kèm ghi chú, không làm hỏng luồng chấm.
- Bài nộp lưu dấu mốc cùng ``judge_tokens`` để chấm tiếp sau khi backend khởi động lại.
"""

import json
import shutil
import subprocess
import sys

import pytest
from sqlmodel import Session

from app.models.entities import Submission, Testcase
from app.modules.submissions.judge0 import harness
from app.modules.submissions.judge0 import service as judge_service
from app.modules.submissions.judge0.judge0_client import STATUS_ACCEPTED, Judge0Result
from tests.support.fixtures.builders import make_submission

pytest_plugins = ("tests.support.fixtures.submission_fixtures",)

MARKER = harness.new_result_marker()


def _result(stdout: str | None, stderr: str | None = None) -> Judge0Result:
    return Judge0Result(
        token="t", status_id=STATUS_ACCEPTED, stdout=stdout, stderr=stderr,
        compile_output=None, message=None, time=0.01, memory=1000,
    )


def _testcase(expected: str = "3") -> Testcase:
    return Testcase(problem_id=1, input="[1,2]", expected_output=expected)


def _run_python(source: str, stdin: str = "[1,2]") -> str:
    proc = subprocess.run(
        [sys.executable, "-c", source], input=stdin, capture_output=True, text=True, timeout=30
    )
    return proc.stdout


# ------------------------------------------------------------------ marker
def test_each_marker_is_random_and_embeddable():
    first, second = harness.new_result_marker(), harness.new_result_marker()

    assert first != second
    assert first.startswith("\n@@CHAM_CODE_RESULT_") and first.endswith("@@")
    assert first != harness.RESULT_MARKER
    assert len(first) <= 64  # vừa cột submission.result_marker


@pytest.mark.parametrize("language", ["python", "javascript"])
def test_build_source_embeds_given_marker_and_defaults_to_a_new_one(language):
    code = "def add(a, b):\n    return a + b\n" if language == "python" else "function add(a,b){return a+b}\n"

    assert MARKER.strip() in harness.build_source(language, code, "add", marker=MARKER)
    default = harness.build_source(language, code, "add")
    assert "@@CHAM_CODE_RESULT@@" not in default
    assert "@@CHAM_CODE_RESULT_" in default


@pytest.mark.parametrize("language,starter", [
    ("c", "int add(int a, int b) { return 0; }"),
    ("cpp", "int add(int a, int b) { return 0; }"),
    ("cpp", "class Solution { public: int add(int a, int b) { return 0; } };"),
    ("cpp", "int* add(int* nums, int numsSize, int* returnSize) { return 0; }"),
    ("c", "void add(int a, int b) { }"),
])
def test_c_and_cpp_sources_use_the_given_marker(language, starter):
    source = harness.build_source(language, starter, "add", starter, marker=MARKER)

    assert json.dumps(MARKER) in source
    assert "@@CHAM_CODE_RESULT@@" not in source


def test_c_harness_calls_function_before_printing_marker():
    """printf debug trong hàm C phải nằm trước dấu mốc, giống Python/JS/C++."""
    starter = "int add(int a, int b) { return 0; }"
    source = harness.build_source("c", starter, "add", starter, marker=MARKER)
    main = source[source.index("int main(void)"):]

    assert main.index("add(__arg_0, __arg_1)") < main.index(json.dumps(MARKER))


# -------------------------------------------------------------- extract_result
@pytest.mark.parametrize("stdout", [
    None,
    "",
    "3",  # không có dấu mốc
    harness.RESULT_MARKER + "3",  # dấu mốc cố định cũ, sinh viên đọc code là biết
    f"{MARKER}999{MARKER}3",  # dấu mốc xuất hiện hai lần
    f"{MARKER}abc",  # không phải JSON
    f"{MARKER}3 trailing",  # có rác in thêm phía sau
    f"{MARKER}3{MARKER[:-1]}",
    f"{MARKER}",
])
def test_invalid_harness_output_is_rejected(stdout):
    assert harness.extract_result(stdout, MARKER) is None


def test_result_larger_than_limit_is_rejected(monkeypatch):
    monkeypatch.setattr(harness, "MAX_RESULT_BYTES", 10)

    assert harness.extract_result(f"{MARKER}[1,2,3]", MARKER) == "[1,2,3]"
    assert harness.extract_result(f"{MARKER}[1,2,3,4,5]", MARKER) is None


def test_output_printed_before_the_marker_is_ignored():
    assert harness.extract_result(f"debug\n{harness.RESULT_MARKER}9{MARKER}3\n", MARKER) == "3\n"


# ----------------------------------------------------------------- _judge_case
def test_garbage_after_marker_is_wrong_answer_not_a_crash():
    """Trước đây ``json.loads`` không bắt lỗi nên cả bài nộp thành internal_error."""
    result, status, actual = judge_service._judge_case(
        _result(f"{MARKER}abc"), _testcase(), True, MARKER
    )

    assert (status, actual) == ("wrong_answer", None)
    assert result.stderr == judge_service.INVALID_RESULT_NOTE


def test_invalid_output_note_is_appended_to_existing_stderr():
    result, status, _ = judge_service._judge_case(
        _result("3", stderr="debug line\n"), _testcase(), True, MARKER
    )

    assert status == "wrong_answer"
    assert result.stderr == f"debug line\n{judge_service.INVALID_RESULT_NOTE}"


def test_valid_output_keeps_result_untouched():
    original = _result(f"{MARKER}3", stderr="debug")
    result, status, actual = judge_service._judge_case(original, _testcase(), True, MARKER)

    assert (status, actual) == ("accepted", 3)
    assert result is original


def test_stdin_problem_ignores_marker():
    _, status, actual = judge_service._judge_case(
        _result("3\n"), _testcase(), False, MARKER
    )
    assert (status, actual) == ("accepted", "3")


# ----------------------------------------------- tấn công thật trên harness Python
def test_python_student_cannot_fake_result_with_fixed_marker():
    """Sinh viên in dấu mốc cố định cũ rồi thoát sớm: không còn được tính là kết quả."""
    code = (
        "import os\n"
        "def add(a, b):\n"
        f"    os.write(1, {harness.RESULT_MARKER!r}.encode() + b'3')\n"
        "    os._exit(0)\n"
    )
    stdout = _run_python(harness.build_source("python", code, "add", marker=MARKER))

    assert harness.RESULT_MARKER in stdout
    assert harness.extract_result(stdout, MARKER) is None


def test_python_student_extra_output_after_result_is_rejected():
    """In thêm sau kết quả (atexit) làm phần sau dấu mốc không còn là một giá trị JSON.

    Nếu phần in thêm vẫn giữ JSON hợp lệ (vd nối thêm chữ số) thì chỉ đổi đáp án của
    chính sinh viên, vẫn phải tự biết đáp án đúng nên không lợi gì.
    """
    code = (
        "import atexit, os\n"
        "atexit.register(lambda: os.write(1, b' extra'))\n"
        "def add(a, b):\n"
        "    return a + b\n"
    )
    stdout = _run_python(harness.build_source("python", code, "add", marker=MARKER))

    assert stdout.endswith("3 extra")
    assert harness.extract_result(stdout, MARKER) is None


def test_python_correct_solution_still_accepted_with_random_marker():
    stdout = _run_python(harness.build_source("python", "def add(a, b):\n    return a + b\n", "add", marker=MARKER))

    assert harness.json_outputs_match("3", harness.extract_result(stdout, MARKER))


@pytest.mark.skipif(shutil.which("node") is None, reason="node không có")
def test_js_student_cannot_fake_result_with_fixed_marker(tmp_path):
    code = (
        "function add(a, b) {\n"
        f"  process.stdout.write({json.dumps(harness.RESULT_MARKER)} + '3');\n"
        "  process.exit(0);\n"
        "}\n"
    )
    path = tmp_path / "main.js"
    path.write_text(harness.build_source("javascript", code, "add", marker=MARKER), encoding="utf-8")
    stdout = subprocess.run(
        ["node", str(path)], input="[1,2]", capture_output=True, text=True, timeout=30
    ).stdout

    assert harness.extract_result(stdout, MARKER) is None


# ------------------------------------------------- lưu dấu mốc khi chấm bài nộp
@pytest.fixture
def grading(monkeypatch, engine):
    monkeypatch.setattr(judge_service, "engine", engine)
    monkeypatch.setattr(judge_service.grading_queue, "enqueue", lambda *a, **k: None)
    monkeypatch.setattr(judge_service, "_testcase_results", lambda *a, **k: [])
    monkeypatch.setattr(judge_service, "_compile_output_of", lambda *a, **k: None)
    seen: list[str] = []

    def grade(problem, data, testcases, tokens, save_tokens, heartbeat=None, marker=None):
        seen.append(marker)
        if not tokens:
            save_tokens(["token-1"])
        return [(None, "accepted", None)]

    monkeypatch.setattr(judge_service, "_grade_in_chunks", grade)
    return seen


def _pending(session: Session, problem, student, *, tokens=None, marker=None) -> Submission:
    submission = make_submission(session, problem, student, status="pending")
    submission.grading_claimed_at = None
    submission.judge_tokens = tokens
    submission.result_marker = marker
    session.add(submission)
    session.commit()
    return submission


def _row(session: Session, submission_id: int) -> Submission:
    session.expire_all()
    return session.get(Submission, submission_id)


def test_new_grading_saves_random_marker_with_tokens(
    session, grading, submission_problem, submission_student
):
    submission = _pending(session, submission_problem, submission_student)

    judge_service.grade_submission(submission.submission_id)

    row = _row(session, submission.submission_id)
    assert row.judge_tokens == ["token-1"]
    assert row.result_marker == grading[0]
    assert row.result_marker.startswith("\n@@CHAM_CODE_RESULT_")


def test_resumed_grading_reuses_saved_marker(
    session, grading, submission_problem, submission_student
):
    submission = _pending(
        session, submission_problem, submission_student, tokens=["old"], marker=MARKER
    )

    judge_service.grade_submission(submission.submission_id)

    assert grading == [MARKER]
    assert _row(session, submission.submission_id).result_marker == MARKER


def test_resumed_grading_from_before_migration_uses_fixed_marker(
    session, grading, submission_problem, submission_student
):
    submission = _pending(session, submission_problem, submission_student, tokens=["old"])

    judge_service.grade_submission(submission.submission_id)

    assert grading == [harness.RESULT_MARKER]


def test_regrade_without_tokens_gets_a_fresh_marker(
    session, grading, submission_problem, submission_student
):
    """Chấm lại từ đầu (token đã bị xoá) thì dấu mốc cũ còn sót trong cột bị thay mới."""
    submission = _pending(session, submission_problem, submission_student, marker=MARKER)

    judge_service.grade_submission(submission.submission_id)

    row = _row(session, submission.submission_id)
    assert grading[0] != MARKER
    assert row.result_marker == grading[0]
