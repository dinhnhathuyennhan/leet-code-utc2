"""Nop bai 'chay duoc nhung chua toi uu' de kiem tra AI review co goi y toi uu khong.

Bai DEMO_PRIME (problem_id 49): dung thuat toan O(n) thay vi O(sqrt(n)).
Chay: python -m tools.check_review_optimizable
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8000")
STUDENT_EMAIL = os.getenv("E2E_STUDENT_EMAIL", "6751071001@st.utc2.edu.vn")
STUDENT_PASSWORD = os.getenv("E2E_STUDENT_PASSWORD", "Password@123")

COURSE_ID = "DEMO101-2026A"
LESSON_ID = 28
PROBLEM_ID = 49

# O(n): duyet het 2..n-1 thay vi chi den sqrt(n). Van pass het testcase
# nhung bi review phat hien la du thua.
SUBOPTIMAL_CODE = """import sys

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, n):
        if n % i == 0:
            return False
    return True

def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    print("true" if is_prime(n) else "false")

if __name__ == "__main__":
    main()
"""


def main() -> int:
    with httpx.Client(base_url=BASE_URL, timeout=300.0) as client:
        token = None
        for password in (STUDENT_PASSWORD, "UiTest@2026", "LeetCodeForUtc2"):
            response = client.post("/auth/login", json={"email": STUDENT_EMAIL, "password": password})
            if response.status_code == 200:
                token = response.json()["access_token"]
                break
        if not token:
            print("FAIL: khong dang nhap duoc")
            return 1
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            f"/courses/{COURSE_ID}/lessons/{LESSON_ID}/problems/{PROBLEM_ID}/submissions",
            headers=headers,
            json={"language": "python", "code": SUBOPTIMAL_CODE},
        )
        if response.status_code != 202:
            print(f"FAIL: submit status={response.status_code} {response.text[:200]}")
            return 1
        submission_id = response.json()["submission_id"]
        print(f"submission_id = {submission_id}")

        for _ in range(120):
            time.sleep(0.5)
            data = client.get(f"/submissions/{submission_id}/result", headers=headers).json()
            if data.get("status") not in ("pending", "processing"):
                break
        print(f"grading: status={data.get('status')} "
              f"passed={data.get('passed_count')}/{data.get('total_testcases')}")
        if data.get("status") != "accepted":
            print("FAIL: bai khong pass het testcase -> khong review duoc")
            return 1

        for locale in ("vi", "en"):
            start = time.monotonic()
            response = client.post(
                f"/ai/review/{submission_id}", headers=headers, json={"locale": locale}
            )
            elapsed = time.monotonic() - start
            print(f"\n--- review [{locale}] status={response.status_code} ({elapsed:.1f}s) ---")
            if response.status_code != 200:
                print(response.text[:300])
                continue
            review = response.json()
            optimization = review.get("optimization") or {}
            print(f"time  : {review.get('time_complexity')}")
            print(f"space : {review.get('space_complexity')}")
            print(f"optimizable: {optimization.get('is_optimizable')}")
            print(f"expected time : {optimization.get('expected_time_complexity')}")
            print(f"expected space: {optimization.get('expected_space_complexity')}")
            print(f"issues: {review.get('issues')}")
            print(f"summary: {review.get('summary')}")
            print(f"explanation: {review.get('complexity_explanation')}")
            print(f"suggestion: {optimization.get('suggestion')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
