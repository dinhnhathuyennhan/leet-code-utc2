"""Test AWS Judge0 + AI Review với CHI PHÍ AWS TỐI THIỂU.

Mục tiêu: xác nhận backend nối được Judge0 trên AWS (instance của nhóm) và
AI review chạy được, mà không đốt nhiều tài nguyên AWS.

Chi phí AWS: 1 lần submit = 1 batch POST + vài lần GET poll trên
`/submissions/batch`. Tổng cộng <= 1 request chấm code thật.

AI review dùng Ollama LOCAL (D:\\qweencode) nên không tốn AWS.

Chạy: python -m tools.aws_smoke_test
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8000")
STUDENT_EMAIL = os.getenv("E2E_STUDENT_EMAIL", "6251071001@st.utc2.edu.vn")
STUDENT_PASSWORD = os.getenv("E2E_STUDENT_PASSWORD", "Password@123")

# Bài "Tổng hai số" — 3 testcase, code ngắn nhất trong bộ seed.
CODE = "a, b = map(int, input().split())\nprint(a + b)\n"

PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"PASS {name:44} {detail}")
    else:
        FAILED += 1
        print(f"FAIL {name:44} {detail}")


def main() -> int:
    print("=" * 92)
    print(f"AWS SMOKE TEST (chi phi AWS toi thieu)  ->  {BASE_URL}")
    print("=" * 92)

    with httpx.Client(base_url=BASE_URL, timeout=300.0) as client:
        # ---------- 1. Login ----------
        response = client.post(
            "/auth/login", json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        check("login student", response.status_code == 200, STUDENT_EMAIL)
        if response.status_code != 200:
            print(f"     body={response.text[:300]}")
            return 1
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # ---------- 2. Tim bai "Tong hai so" ----------
        response = client.get("/courses", headers=headers)
        courses = response.json() if response.status_code == 200 else []
        target = None
        for course in courses:
            course_id = course.get("course_id")
            detail_resp = client.get(f"/courses/{course_id}", headers=headers)
            detail = detail_resp.json() if detail_resp.status_code == 200 else {}
            for lesson in detail.get("sessions") or detail.get("lessons") or []:
                for problem in lesson.get("problems") or []:
                    title = (problem.get("title") or "").lower()
                    if "tổng hai số" in title or "tong hai so" in title:
                        target = (
                            course_id,
                            lesson.get("id") or lesson.get("lesson_id"),
                            problem.get("id") or problem.get("problem_id"),
                        )
                        break
                if target:
                    break
            if target:
                break

        check("tim thay bai 'Tong hai so'", target is not None, str(target))
        if not target:
            print("     -> khong tim thay bai, dung")
            return 1
        course_id, lesson_id, problem_id = target

        # ---------- 3. Submit 1 lan (bat buoc, day la phan ton AWS lon nhat) ----------
        response = client.post(
            f"/courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/submissions",
            headers=headers,
            json={"language": "python", "code": CODE},
        )
        check("POST submit -> 202", response.status_code == 202, f"status={response.status_code}")
        if response.status_code != 202:
            print(f"     body={response.text[:400]}")
            return 1
        submission_id = response.json()["submission_id"]

        # ---------- 4. Poll ket qua (Judge0 tren AWS) ----------
        result = {}
        for _ in range(180):
            time.sleep(1.0)
            poll = client.get(f"/submissions/{submission_id}/result", headers=headers)
            if poll.status_code != 200:
                continue
            result = poll.json()
            if result.get("status") not in ("pending", "processing"):
                break

        check("Judge0 AWS cham xong", result.get("status") == "accepted",
              f"status={result.get('status')} "
              f"passed={result.get('passed_count')}/{result.get('total_testcases')}")
        if result.get("status") != "accepted":
            print(f"     body={result}")
            return 1

        # ---------- 5. AI review (Ollama LOCAL - khong ton AWS) ----------
        start = time.monotonic()
        response = client.post(
            f"/ai/review/{submission_id}", headers=headers, json={"locale": "vi"}
        )
        elapsed = time.monotonic() - start
        check("POST /ai/review/{id} (VI)", response.status_code == 200,
              f"status={response.status_code} time={elapsed:.1f}s")
        if response.status_code != 200:
            print(f"     body={response.text[:400]}")
            return 1
        review = response.json()
        check("review co summary", bool(review.get("summary")),
              str(review.get("summary"))[:50])
        check("review co time/space complexity",
              bool(review.get("time_complexity")) and bool(review.get("space_complexity")),
              f"t={review.get('time_complexity')} s={review.get('space_complexity')}")

    print("=" * 92)
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    print("=" * 92)
    print("=> TAT AWS NGAY (dong EC2) de khong ton tien.")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
