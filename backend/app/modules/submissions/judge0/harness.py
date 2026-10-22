import json
import re

RESULT_MARKER = "\n@@CHAM_CODE_RESULT@@"
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_PYTHON_DRIVER = '''
import json as _json
import sys as _sys

def _cham_main():
    _args = _json.loads(_sys.stdin.read())
    _fn = globals().get({name!r})
    if _fn is None and "Solution" in globals():
        _fn = getattr(globals()["Solution"](), {name!r})
    _real_stdout = _sys.stdout
    _sys.stdout = _sys.stderr
    try:
        _result = _fn(*_args)
    finally:
        _sys.stdout = _real_stdout
    _real_stdout.write({marker!r} + _json.dumps(_result, separators=(",", ":"), ensure_ascii=False))
    _real_stdout.flush()

_cham_main()
'''

_JS_DRIVER = """
;(function () {{
  const __args = JSON.parse(require("fs").readFileSync(0, "utf8"));
  const __fn = typeof {name} === "function" ? {name} : null;
  const __log = console.log;
  console.log = function () {{}};
  let __result;
  try {{
    __result = __fn(...__args);
  }} finally {{
    console.log = __log;
  }}
  process.stdout.write({marker} + JSON.stringify(__result === undefined ? null : __result));
}})();
"""


def supports_function_harness(language: str) -> bool:
    return language in ("python", "javascript")


def build_source(language: str, student_code: str, function_name: str) -> str:
    if not _IDENTIFIER.match(function_name):
        raise ValueError("function_name không hợp lệ")
    if language == "python":
        driver = _PYTHON_DRIVER.format(name=function_name, marker=RESULT_MARKER)
        return f"{student_code}\n{driver}"
    if language == "javascript":
        driver = _JS_DRIVER.format(name=function_name, marker=json.dumps(RESULT_MARKER))
        return f"{student_code}\n{driver}"
    raise ValueError(f"Chưa hỗ trợ function harness cho {language}")


def extract_result(stdout: str | None) -> str | None:
    """Lấy JSON kết quả sau marker; None nếu chương trình không in ra marker."""
    if not stdout or RESULT_MARKER not in stdout:
        return None
    return stdout.rsplit(RESULT_MARKER, 1)[1]


def json_outputs_match(expected_json: str, actual_json: str | None) -> bool:
    if actual_json is None:
        return False
    try:
        return json.loads(expected_json) == json.loads(actual_json)
    except ValueError:
        return False


def text_outputs_match(expected: str, actual: str | None) -> bool:
    return (actual or "").strip() == expected.strip()
