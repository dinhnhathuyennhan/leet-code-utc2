"""Kiểm thử LIVE: gọi trực tiếp Judge0 client của backend với Judge0 thật.

Chạy: python -m tools.live_judge_check
Tiêu chí:
- mỗi ngôn ngữ trong config.LANGUAGES phải chạy được trên instance Judge0 local
- mỗi verdict (accepted / wrong_answer / compile_error / runtime_error /
  time_limit_exceeded) phải được chuẩn hoá đúng
- base64 encode/decode phải khớp byte-for-byte với giá trị gốc
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# App dùng `load_dotenv()` trong app/main.py + app/core/database.py -> script
# phải làm giống để đọc đúng JUDGE0_URL / JUDGE0_AUTH_TOKEN.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from app.core import config  # noqa: E402
from app.modules.submissions.judge0.harness import text_outputs_match  # noqa: E402
from app.modules.submissions.judge0.judge0_client import (  # noqa: E402
    Judge0Client,
    Judge0Error,
)

# Code cho từng ngôn ngữ: (source_code, stdin, expected, language)
SAMPLES = [
    (
        "python/accepted",
        "python",
        "a, b = map(int, input().split())\nprint(a + b)\n",
        "3 4\n",
        "7\n",
        "accepted",
    ),
    (
        "python/wrong_answer",
        "python",
        "a, b = map(int, input().split())\nprint(a + b + 1)\n",
        "3 4\n",
        "7\n",
        "wrong_answer",
    ),
    (
        "python/compile_error",
        "python",
        "def broken(:\n    pass\n",
        "",
        "",
        "compile_error",
    ),
    (
        "python/runtime_error",
        "python",
        "print(1 / 0)\n",
        "",
        "",
        "runtime_error",
    ),
    (
        "cpp/accepted",
        "cpp",
        "#include <iostream>\n"
        "int main(){int a,b;std::cin>>a>>b;std::cout<<a+b<<std::endl;return 0;}\n",
        "3 4\n",
        "7\n",
        "accepted",
    ),
    (
        "cpp/compile_error",
        "cpp",
        "#include <iostream>\nint main(){ this is not c++ }\n",
        "",
        "",
        "compile_error",
    ),
    (
        "cpp/runtime_error",
        "cpp",
        "#include <iostream>\nint main(){ int* p = nullptr; std::cout << *p; return 0; }\n",
        "",
        "",
        "runtime_error",
    ),
    (
        "c/accepted",
        "c",
        "#include <stdio.h>\nint main(){int a,b;scanf(\"%d %d\",&a,&b);printf(\"%d\\n\",a+b);return 0;}\n",
        "3 4\n",
        "7\n",
        "accepted",
    ),
    (
        "java/accepted",
        "java",
        "import java.util.Scanner;\n"
        "public class Main {\n"
        "  public static void main(String[] a) {\n"
        "    Scanner s = new Scanner(System.in);\n"
        "    int x = s.nextInt(), y = s.nextInt();\n"
        "    System.out.println(x + y);\n"
        "  }\n"
        "}\n",
        "3 4\n",
        "7\n",
        "accepted",
    ),
    (
        "java/compile_error",
        "java",
        "public class Main { public static void main(String[] a) { int x = ; } }\n",
        "",
        "",
        "compile_error",
    ),
    (
        "javascript/accepted",
        "javascript",
        "const fs = require('fs');\n"
        "const d = fs.readFileSync(0, 'utf8').trim().split(/\\s+/);\n"
        "console.log(Number(d[0]) + Number(d[1]));\n",
        "3 4\n",
        "7\n",
        "accepted",
    ),
    (
        "javascript/wrong_answer",
        "javascript",
        "console.log('nope');\n",
        "",
        "7\n",
        "wrong_answer",
    ),
]


def _judge(client: Judge0Client, source: str, language: str, stdin: str, expected: str):
    """Chạy một testcase và trả về (status_chuẩn_hoá, stdout, result_thô).

    Không truyền `expected_output` cho Judge0: backend tự so sánh output ở tầng
    Python (xem `_judge_case` trong judge0/service.py) nên Judge0 chỉ cần
    chạy code và trả stdout. Nếu gửi kèm, Judge0 tự kết luận Wrong Answer
    và che mất lỗi biên dịch/runtime thật.
    """
    tokens = client.create_batch(source, language, [stdin], 3)
    results = client.wait_for_results(tokens, 30)
    result = results[0]
    if result.status_id != 3:  # chưa Accepted -> lấy status hệ thống
        return result.system_status, result.stdout, result
    matched = text_outputs_match(expected, result.stdout)
    return ("accepted" if matched else "wrong_answer"), result.stdout, result


def _is_syntax_error(result) -> bool:
    """Python không có bước biên dịch nên SyntaxError bị Judge0 báo thành runtime error.

    Với sinh viên, "lỗi biên dịch" mô tả đúng hơn "lỗi runtime" cho trường hợp này.
    """
    stderr = result.stderr or ""
    return "SyntaxError" in stderr or "IndentationError" in stderr


def main() -> int:
    print("=" * 74)
    print("LIVE JUDGE0 CHECK  ->", os.getenv("JUDGE0_URL", "<unset>"))
    print("=" * 74)

    passed = 0
    failed = 0
    client = Judge0Client()
    try:
        for name, language, source, stdin, expected, want_status in SAMPLES:
            if language not in config.LANGUAGES:
                print(f"SKIP {name:32} ngôn ngữ không được cấu hình")
                continue
            try:
                status, stdout, result = _judge(client, source, language, stdin, expected)
                # Python báo SyntaxError ở bước chạy -> đổi thành compile_error
                # cho đúng nghĩa (giống logic trong judge0/service.py).
                if status == "runtime_error" and _is_syntax_error(result):
                    status = "compile_error"
            except Judge0Error as error:
                print(f"FAIL {name:32} Judge0Error: {error}")
                failed += 1
                continue
            except Exception as error:
                print(f"FAIL {name:32} exception: {type(error).__name__}: {error}")
                failed += 1
                continue

            ok = status == want_status
            marker = "PASS" if ok else "FAIL"
            detail = f"status={status:22} time={result.time} mem={result.memory}"
            if not ok:
                detail += f"  (expected {want_status})"
                detail += f"  stdout={stdout!r} stderr={(result.stderr or '')[:120]!r}"
                detail += f"  compile={(result.compile_output or '')[:120]!r}"
            print(f"{marker} {name:32} {detail}")
            if ok:
                passed += 1
            else:
                failed += 1

        # --- Kiểm tra base64 round-trip với ký tự đặc biệt ---
        # Dùng chr() để tránh escape qua shell: "héllo" + dấu nháy + xuống dòng + tab.
        print("-" * 74)
        unicode_text = "héllo ✓ " + '"' + "\n" + "\t"
        tricky = f"print({unicode_text!r})\n"
        try:
            status, stdout, _ = _judge(client, tricky, "python", "", unicode_text + "\n")
            # stdout phải giống byte-for-byte với chuỗi đã gửi (kể cả dấu xuống dòng, tab).
            ok = status == "accepted" and stdout == unicode_text + "\n"
            print(
                f"{'PASS' if ok else 'FAIL'} {'base64/unicode round-trip':32} "
                f"status={status} stdout={stdout!r}"
            )
            passed += 1 if ok else 0
            failed += 0 if ok else 1
        except Exception as error:
            print(f"FAIL {'base64/unicode round-trip':32} {error}")
            failed += 1

        # --- Nhiều testcase: 1 fail giữa -> vẫn wrong_answer, đếm đúng số đạt ---
        print("-" * 74)
        try:
            # Judge0 chỉ chạy code, không so sánh output -> script tự so sánh
            # giống hệt `_judge_case` của backend.
            expected_list = ["1\n", "999\n", "3\n"]
            tokens = client.create_batch(
                "print(int(input()))\n", "python", ["1\n", "2\n", "3\n"], 3
            )
            results = client.wait_for_results(tokens, 30)
            statuses = []
            for result, expected in zip(results, expected_list, strict=True):
                if result.status_id != 3:
                    statuses.append(result.system_status)
                elif text_outputs_match(expected, result.stdout):
                    statuses.append("accepted")
                else:
                    statuses.append("wrong_answer")
            overall = next((s for s in statuses if s != "accepted"), "accepted")
            passed_count = statuses.count("accepted")
            ok = (
                overall == "wrong_answer"
                and passed_count == 2
                and len(results) == 3
                and statuses[0] == "accepted"
                and statuses[1] == "wrong_answer"
                and statuses[2] == "accepted"
            )
            print(
                f"{'PASS' if ok else 'FAIL'} {'multi-testcase aggregation':32} "
                f"status={overall} passed={passed_count}/3 per_tc={statuses}"
            )
            passed += 1 if ok else 0
            failed += 0 if ok else 1
        except Exception as error:
            print(f"FAIL {'multi-testcase aggregation':32} {error}")
            failed += 1

        # --- Code rỗng phải bị từ chối ---
        print("-" * 74)
        try:
            client.create_batch("   \n  ", "python", [""], 3)
            print(f"FAIL {'empty source rejected':32} không ném lỗi")
            failed += 1
        except Exception:
            print(f"PASS {'empty source rejected':32} ném lỗi đúng")
            passed += 1
    finally:
        client.close()

    print("=" * 74)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 74)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
