"""Kiểm tra các đoạn code mẫu dùng trong hướng dẫn test tay.

Chạy: python -m tools.check_guide_solutions
"""

from __future__ import annotations

import os

import httpx

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8000")
EMAIL = "6751071001@st.utc2.edu.vn"
PASSWORD = os.getenv("SEED_DEFAULT_PASSWORD", "Password@123")
COURSE = "DEMO101-2026A"

# Danh sách (lesson_id, problem_id, language, code, expected_status).
#
# Dùng list thay vì dict vì cùng một bài (28, 47) được test với 2 ngôn ngữ
# khác nhau (python -> accepted, cpp -> wrong_answer). Dict sẽ ghi đè key trùng
# và khiến nhánh "accepted" không bao giờ chạy.
SOLUTIONS: list[tuple[int, int, str, str, str]] = [
    # (28, 47): python — code đúng -> accepted
    (
        28,
        47,
        "python",
        "import sys\n"
        "d = sys.stdin.read().split()\n"
        "print(int(d[0]) + int(d[1]))\n",
        "accepted",
    ),
    (
        28,
        48,
        "python",
        "import sys\n"
        "n = int(sys.stdin.read().strip())\n"
        "r = 1\n"
        "for i in range(2, n + 1):\n"
        "    r *= i\n"
        "print(r)\n",
        "accepted",
    ),
    (
        28,
        49,
        "python",
        "import sys\n"
        "n = int(sys.stdin.read().strip())\n"
        "ok = n > 1 and all(n % i for i in range(2, int(n ** 0.5) + 1))\n"
        "print('true' if ok else 'false')\n",
        "accepted",
    ),
    (
        29,
        50,
        "python",
        "import sys\n"
        "d = sys.stdin.read().split()\n"
        "print(' '.join(reversed(d[1:1 + int(d[0])])))\n",
        "accepted",
    ),
    (
        29,
        51,
        "python",
        "import sys\n"
        "d = sys.stdin.read().split()\n"
        "n = int(d[0])\n"
        "a = sorted(int(x) for x in d[1:1 + n])\n"
        "print(' '.join(map(str, a)))\n",
        "accepted",
    ),
    (
        31,
        55,
        "python",
        "import sys\n"
        "n = int(sys.stdin.read().strip())\n"
        "print(n * 2)\n",
        "accepted",
    ),
    # (28, 47): cpp — code cố tình sai -> wrong_answer
    (
        28,
        47,
        "cpp",
        "#include <iostream>\n"
        "int main() { std::cout << 0; return 0; }\n",
        "wrong_answer",
    ),
]


def main() -> int:
    with httpx.Client(base_url=BASE_URL, timeout=120.0) as client:
        token = client.post(
            "/auth/login", json={"email": EMAIL, "password": PASSWORD}
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        failures = 0
        for lesson_id, problem_id, language, code, expected in SOLUTIONS:
            response = client.post(
                f"/courses/{COURSE}/lessons/{lesson_id}/problems/{problem_id}/submit",
                headers=headers,
                json={"language": language, "source_code": code},
            )
            if response.status_code != 200:
                print(
                    f"FAIL p{problem_id} {language:8} HTTP {response.status_code} "
                    f"{response.text[:90]}"
                )
                failures += 1
                continue
            actual = response.json()["status"]
            passed = response.json()["passed_count"]
            total = response.json()["total_testcases"]
            ok = actual == expected
            print(
                f"{'PASS' if ok else 'FAIL'} p{problem_id} {language:8} "
                f"-> {actual:20} ({passed}/{total})  mong doi={expected}"
            )
            failures += 0 if ok else 1
        return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
