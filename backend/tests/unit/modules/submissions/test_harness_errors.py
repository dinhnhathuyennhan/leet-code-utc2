"""Thông báo lỗi của harness Python: không lộ khung chấm bài cho sinh viên."""

import json
import subprocess
import sys

from app.modules.submissions.judge0.harness import build_source, extract_result, new_result_marker

MARKER = new_result_marker()


def _run(code: str, args: list) -> tuple[int, str | None, str]:
    source = build_source("python", code, "add", marker=MARKER)
    proc = subprocess.run(
        [sys.executable, "-c", source],
        input=json.dumps(args).encode(),
        capture_output=True,
        timeout=30,
    )
    return proc.returncode, extract_result(proc.stdout.decode(), MARKER), proc.stderr.decode("utf-8")


def test_correct_function_still_returns_result():
    assert _run("def add(x, y):\n    return x + y\n", [1, 2])[:2] == (0, "3")


def test_solution_class_method_is_supported():
    code = "class Solution:\n    def add(self, x, y):\n        return x + y\n"
    assert _run(code, [2, 3])[:2] == (0, "5")


def test_missing_function_gives_friendly_message():
    code, result, stderr = _run("def addition(x, y):\n    return x + y\n", [1, 2])

    assert code == 1 and result is None
    assert "Không tìm thấy hàm 'add'" in stderr
    assert "_cham_main" not in stderr


def test_runtime_error_traceback_hides_harness_frames():
    code, result, stderr = _run("def add(x, y):\n    return x / 0\n", [1, 2])

    assert code == 1 and result is None
    assert "ZeroDivisionError" in stderr
    assert "line 2, in add" in stderr
    assert "_cham_main" not in stderr
