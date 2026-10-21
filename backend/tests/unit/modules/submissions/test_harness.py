import json
import shutil
import subprocess
import sys

import pytest

from app.modules.submissions.judge0 import harness

PY = "def add(a, b):\n    print('debug')\n    return a + b\n"
JS = "function add(a, b) { console.log('debug'); return a + b; }\n"


def _run(cmd, source, tmp_path, suffix, stdin):
    path = tmp_path / f"main{suffix}"
    path.write_text(source, encoding="utf-8")
    return subprocess.run([*cmd, str(path)], input=stdin, capture_output=True, text=True, timeout=10).stdout


def test_python_harness_ignores_student_prints(tmp_path):
    source = harness.build_source("python", PY, "add")
    out = _run([sys.executable], source, tmp_path, ".py", "[1,2]")
    assert harness.json_outputs_match("3", harness.extract_result(out))


@pytest.mark.skipif(shutil.which("node") is None, reason="node không có")
def test_js_harness_ignores_student_prints(tmp_path):
    source = harness.build_source("javascript", JS, "add")
    out = _run(["node"], source, tmp_path, ".js", "[1,2]")
    assert harness.json_outputs_match("3", harness.extract_result(out))


def test_invalid_function_name_rejected():
    with pytest.raises(ValueError):
        harness.build_source("python", PY, "add(); import os")


def test_matchers():
    assert harness.json_outputs_match("[1,2]", "[1, 2]")
    assert not harness.json_outputs_match("[1,2]", None)
    assert harness.text_outputs_match("a b\n", " a b")
    assert harness.extract_result("noise") is None
    assert json.loads(harness.extract_result("x" + harness.RESULT_MARKER + "5")) == 5
