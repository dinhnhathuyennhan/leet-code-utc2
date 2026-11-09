"""E2E test AI review voi Ollama that (ca VI va EN).

Chay: python -m tools.e2e_ai_review
Yeu cau: uvicorn o 127.0.0.1:8000, Ollama o 127.0.0.1:11434 (model qwen2.5-coder:7b).
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8000")
STUDENT_EMAIL = os.getenv("E2E_STUDENT_EMAIL", "6751071001@st.utc2.edu.vn")
STUDENT_PASSWORD = os.getenv("E2E_STUDENT_PASSWORD", "Password@123")

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


def login(client: httpx.Client) -> str | None:
    for password in (STUDENT_PASSWORD, "UiTest@2026", "LeetCodeForUtc2"):
        response = client.post("/auth/login", json={"email": STUDENT_EMAIL, "password": password})
        if response.status_code == 200:
            return response.json().get("access_token")
    return None


def main() -> int:
    print("=" * 92)
    print(f"E2E AI REVIEW  ->  {BASE_URL}")
    print("=" * 92)

    with httpx.Client(base_url=BASE_URL, timeout=300.0) as client:
        token = login(client)
        check("login student", token is not None, STUDENT_EMAIL)
        if not token:
            return 1
        headers = {"Authorization": f"Bearer {token}"}

        # Lay ve bai noi da accepted cua chinh SV (dung cho review).
        response = client.get("/submissions/mine", headers=headers)
        items = (response.json() if response.status_code == 200 else {}).get("items") or []
        accepted = [
            i
            for i in items
            if i.get("status") == "accepted"
            and i.get("passed_count") == i.get("total_testcases")
            and (i.get("total_testcases") or 0) > 0
        ]
        check("co bai noi accepted", len(accepted) > 0, f"count={len(accepted)}")
        if not accepted:
            return 1

        submission_id = accepted[0]["id"]
        print(f"     submission_id = {submission_id}")

        # --- 1. Review VI ---
        start = time.monotonic()
        response = client.post(f"/ai/review/{submission_id}", headers=headers, json={"locale": "vi"})
        elapsed = time.monotonic() - start
        check("POST ai-review (vi)", response.status_code == 200,
              f"status={response.status_code} time={elapsed:.1f}s")
        if response.status_code != 200:
            print(f"     body={response.text[:300]}")
            return 1
        vi = response.json()
        check("vi co summary", bool(vi.get("summary")), f"summary={str(vi.get('summary'))[:60]!r}")
        check("vi co complexity_explanation", bool(vi.get("complexity_explanation")), "")
        check("vi co time/space complexity",
              bool(vi.get("time_complexity")) and bool(vi.get("space_complexity")),
              f"t={vi.get('time_complexity')} s={vi.get('space_complexity')}")
        check("vi co optimization.is_optimizable",
              "is_optimizable" in (vi.get("optimization") or {}),
              f"={((vi.get('optimization') or {}).get('is_optimizable'))}")
        check("vi co issues list", isinstance(vi.get("issues"), list), f"n={len(vi.get('issues') or [])}")

        # --- 2. Review EN ---
        start = time.monotonic()
        response = client.post(f"/ai/review/{submission_id}", headers=headers, json={"locale": "en"})
        elapsed = time.monotonic() - start
        check("POST ai-review (en)", response.status_code == 200,
              f"status={response.status_code} time={elapsed:.1f}s")
        if response.status_code != 200:
            print(f"     body={response.text[:300]}")
            return 1
        en = response.json()
        check("en co summary", bool(en.get("summary")), f"summary={str(en.get('summary'))[:60]!r}")
        check("en co optimization.is_optimizable",
              "is_optimizable" in (en.get("optimization") or {}),
              f"={((en.get('optimization') or {}).get('is_optimizable'))}")

        # --- 3. Hai ngon ngu phai khac nhau ---
        check("vi != en", vi.get("summary") != en.get("summary"),
              "summary khac nhau")

        # --- 4. Body rong -> mac dinh VI ---
        response = client.post(f"/ai/review/{submission_id}", headers=headers)
        check("POST ai-review (body rong)", response.status_code == 200,
              f"status={response.status_code}")

        # --- 5. Bai nop chua accepted -> 409 ---
        response = client.get("/submissions/mine", headers=headers)
        all_items = (response.json() if response.status_code == 200 else {}).get("items") or []
        wrong = [i for i in all_items if i.get("status") == "wrong_answer"]
        if wrong:
            response = client.post(f"/ai/review/{wrong[0]['id']}", headers=headers)
            check("bai chua pass -> 409", response.status_code == 409, f"status={response.status_code}")

        # --- 6. Bai nop nguoi khac -> 404 ---
        response = client.post("/ai/review/999999", headers=headers)
        check("bai nop khong ton tai -> 404", response.status_code == 404, f"status={response.status_code}")

        # --- 7. Thieu token -> 401 ---
        response = client.post(f"/ai/review/{submission_id}")
        check("thieu token -> 401/403", response.status_code in (401, 403), f"status={response.status_code}")

    print("=" * 92)
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    print("=" * 92)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
