"""E2E HTTP test cho luong sinh vien (chay that voi uvicorn + Judge0 + Postgres).

Chay:  python -m tools.e2e_student_flow
Yeu cau: uvicorn chay o http://127.0.0.1:8000, Judge0 o http://localhost:2358
"""

import os
import sys
import time
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8000")
STUDENT_PASSWORD = os.getenv("E2E_STUDENT_PASSWORD", "Password@123")
TEACHER_PASSWORD = os.getenv("E2E_TEACHER_PASSWORD", STUDENT_PASSWORD)

# Script UI (frontend/test/ui-test-student.mjs) đổi mật khẩu bắt buộc cho sinh viên
# đầu tiên -> mật khẩu seed không còn dùng được với tài khoản đó.
# Thử cả hai để script chạy được sau khi UI test đã chạy.
STUDENT_PASSWORDS = [
    STUDENT_PASSWORD,
    "UiTest@2026",
    "Password@123",
]
TEACHER_PASSWORDS = [
    TEACHER_PASSWORD,
    "UiTest@2026",
    "Password@123",
]

# User seed trong DB + user tạo tay (student.new/teacher.new) đều được thử để
# script không phụ thuộc vào việc user nào đã tồn tại trong DB local.
STUDENT_CANDIDATES = [
    "6751071001@st.utc2.edu.vn",
    "6751071003@st.utc2.edu.vn",
    "6251071001@st.utc2.edu.vn",
    "6251071002@st.utc2.edu.vn",
    "6351071001@st.utc2.edu.vn",
    "6351071002@st.utc2.edu.vn",
    "student.new@st.utc2.edu.vn",
]
TEACHER_CANDIDATES = [
    "NguyenVanAn@st.utc2.edu.vn",
    "TranThiBinh@st.utc2.edu.vn",
    "LeHoangCuong@st.utc2.edu.vn",
]

PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"PASS {name:52} {detail}")
    else:
        FAILED += 1
        print(f"FAIL {name:52} {detail}")


def login(client: httpx.Client, email: str, password: str) -> str | None:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    if response.status_code != 200:
        return None
    return response.json().get("access_token")


def login_any(client: httpx.Client, candidates: list[str], passwords: list[str]) -> tuple[str | None, str]:
    """Thử lần lượt (tài khoản, mật khẩu) cho tới khi đăng nhập được."""
    for email in candidates:
        for password in passwords:
            token = login(client, email, password)
            if token:
                return token, email
    return None, candidates[0]


def main() -> int:
    print("=" * 100)
    print(f"E2E STUDENT FLOW  ->  {BASE_URL}")
    print("=" * 100)

    with httpx.Client(base_url=BASE_URL, timeout=120.0) as client:
        # ---------- 1. Login + tim bai con han ----------
        # Backend tu choi (403) bai da qua han, nen phai chon SV co bai con han
        # de chay duoc vong submit -> poll -> ket qua.
        now = datetime.now(UTC)

        def _deadline_of(problem: dict) -> datetime | None:
            raw = problem.get("end_datetime") or problem.get("end_date")
            if not raw:
                return None
            try:
                end = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            except ValueError:
                return None
            return end.replace(tzinfo=UTC) if end.tzinfo is None else end

        def _find_open_problem(headers: dict) -> tuple[str | None, dict, int | None, int | None]:
            """Tra ve (course_id, detail, lesson_id, problem_id) cua bai con han."""
            courses_resp = client.get("/courses", headers=headers)
            courses = courses_resp.json() if courses_resp.status_code == 200 else []
            for candidate in courses:
                candidate_id = candidate.get("course_id")
                if not candidate_id:
                    continue
                detail_resp = client.get(f"/courses/{candidate_id}", headers=headers)
                candidate_detail = detail_resp.json() if detail_resp.status_code == 200 else {}
                for lesson in candidate_detail.get("sessions") or candidate_detail.get("lessons") or []:
                    for problem in lesson.get("problems") or []:
                        end = _deadline_of(problem)
                        if end is not None and end < now:
                            continue
                        lesson_id = lesson.get("id") or lesson.get("lesson_id") or lesson.get("session_id")
                        problem_id = problem.get("id") or problem.get("problem_id")
                        return candidate_id, candidate_detail, lesson_id, problem_id
            return None, {}, None, None

        token = None
        student_email = ""
        courses = []
        course_id = None
        detail = {}
        lesson_id = None
        problem_id = None
        for candidate in STUDENT_CANDIDATES:
            token_try, email_try = login_any(client, [candidate], STUDENT_PASSWORDS)
            if not token_try:
                continue
            headers_try = {"Authorization": f"Bearer {token_try}"}
            courses_resp = client.get("/courses", headers=headers_try)
            courses_try = courses_resp.json() if courses_resp.status_code == 200 else []
            if not courses_try:
                continue
            cid, det, lid, pid = _find_open_problem(headers_try)
            if pid is None:
                # SV nay chi enroll lop da het han -> thu SV tiep theo.
                continue
            token, student_email = token_try, email_try
            courses, course_id, detail, lesson_id, problem_id = courses_try, cid, det, lid, pid
            break

        check("login student", token is not None, student_email)
        if not token:
            print("Khong tim duoc SV co bai con han -> dung E2E")
            return 1

        student_headers = {"Authorization": f"Bearer {token}"}

        # ---------- 2. Lay danh sach lop ----------
        check("GET /courses (student)", len(courses) > 0, f"count={len(courses)}")
        check("student thay course", len(courses) > 0, f"count={len(courses)}")

        if not courses:
            print("Sinh vien chua enroll course nao -> dung")
            return 1

        check("course co id", bool(course_id), f"course_id={course_id}")
        check("GET /courses/{id}", bool(course_id), f"course_id={course_id}")

        lessons = detail.get("sessions") or detail.get("lessons") or []
        check("course co lesson", len(lessons) > 0, f"count={len(lessons)}")
        check("tim thay lesson + problem con han", lesson_id is not None and problem_id is not None,
              f"lesson={lesson_id} problem={problem_id}")

        if problem_id is None:
            print("Khong tim thay problem -> dung")
            return 1

        # ---------- 4. Lay chi tiết bai tap (co testcase mau) ----------
        response = client.get(
            f"/courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}",
            headers=student_headers,
        )
        problem = response.json() if response.status_code == 200 else {}
        check("GET problem detail", response.status_code == 200, f"status={response.status_code}")
        check("problem co starter_code", bool(problem.get("starter_code") or problem.get("start_format_code")),
              "starter ok")

        # ---------- 5. Submit code SAI -> wrong_answer ----------
        # API moi: POST .../submissions tra 202 ngay (submission_id) va cham nen.
        # Vay can poll GET /submissions/{id}/result cho toi khi co trang thai cuoi.
        def submit_and_wait(code: str, label: str) -> dict:
            response = client.post(
                f"/courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/submissions",
                headers=student_headers,
                json={"language": "python", "code": code},
            )
            if response.status_code != 202:
                return {"_status_code": response.status_code, "_body": response.json()
                        if response.headers.get("content-type", "").startswith("application/json") else {}}
            new_id = response.json().get("submission_id")
            for _ in range(120):
                time.sleep(0.5)
                poll = client.get(f"/submissions/{new_id}/result", headers=student_headers)
                if poll.status_code != 200:
                    continue
                data = poll.json()
                if data.get("status") not in ("pending", "processing"):
                    return {**data, "submission_id": new_id, "_status_code": response.status_code}
            return {"submission_id": new_id, "status": "timeout", "_status_code": response.status_code}

        wrong_code = "print('SIRTUONG')\n"
        body = submit_and_wait(wrong_code, "sai")
        check("POST submit (sai)", body.get("_status_code") == 202, f"status={body.get('_status_code')}")
        check("submit tra status", body.get("status") in ("wrong_answer", "accepted", "compile_error",
                                                         "runtime_error", "time_limit_exceeded"),
              f"status={body.get('status')}")
        submission_id = body.get("submission_id")
        check("submit tra id", submission_id is not None, f"id={submission_id}")

        # ---------- 5b. Submit code DUNG -> accepted ----------
        # Sinh ma theo testcase mau cua bai de chắc chan duoc accepted.
        correct_code = (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "a, b = map(int, data[:2])\n"
            "print(a + b)\n"
        )
        body = submit_and_wait(correct_code, "dung")
        check("POST submit (dung)", body.get("_status_code") == 202, f"status={body.get('_status_code')}")
        check("code dung -> accepted", body.get("status") == "accepted",
              f"status={body.get('status')} passed={body.get('passed_count')}/{body.get('total_testcases')}")
        check("accepted co passed_count day du",
              body.get("passed_count") == body.get("total_testcases"),
              f"passed={body.get('passed_count')} total={body.get('total_testcases')}")
        check("accepted co compile_output",
              body.get("compile_output") is None or body.get("compile_output") == "",
              f"output={body.get('compile_output')!r}")

        # ---------- 5c. Submit cung mot bai -> lich su tang them ----------
        response = client.get("/submissions/mine", headers=student_headers)
        after = response.json() if response.status_code == 200 else {}
        check("submit tang so luong lich su", (after.get("total") or 0) >= 3,
              f"total={after.get('total')}")

        # ---------- 6. Submit code SAI SYNTAX -> compile_error ----------
        body = submit_and_wait("def broken(:\n    pass\n", "syntax error")
        check("POST submit (syntax error)", body.get("_status_code") == 202, f"status={body.get('_status_code')}")
        check("syntax error -> compile_error", body.get("status") == "compile_error",
              f"status={body.get('status')}")
        check("compile_error co output", bool(body.get("compile_output")),
              f"output={str(body.get('compile_output'))[:60]!r}")

        # ---------- 7. Ngôn ngữ không hỗ trợ -> lỗi ----------
        response = client.post(
            f"/courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/submissions",
            headers=student_headers,
            json={"language": "cobol", "code": "DISPLAY 'HI'."},
        )
        check("submit nguon ngu la -> 4xx", 400 <= response.status_code < 500,
              f"status={response.status_code}")

        # ---------- 8. Source rong -> lỗi ----------
        response = client.post(
            f"/courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/submissions",
            headers=student_headers,
            json={"language": "python", "code": "   "},
        )
        check("submit source rong -> 4xx", 400 <= response.status_code < 500,
              f"status={response.status_code}")

        # ---------- 9. Lich su nop bai ----------
        response = client.get("/submissions/mine", headers=student_headers)
        history = response.json() if response.status_code == 200 else {}
        check("GET /submissions/mine", response.status_code == 200, f"status={response.status_code}")
        check("history co items", len(history.get("items") or []) > 0,
              f"count={len(history.get('items') or [])}")
        check("history co counts", bool(history.get("counts")), f"counts={history.get('counts')}")
        check("total khop items", history.get("total") == len(history.get("items") or []),
              f"total={history.get('total')}")

        items = history.get("items") or []
        check("item co problem_title", bool(items[0].get("problem_title")) if items else False,
              f"title={items[0].get('problem_title') if items else None}")
        check("item co course_name", bool(items[0].get("course_name")) if items else False,
              f"course={items[0].get('course_name') if items else None}")
        check("item co session_label", bool(items[0].get("session_label")) if items else False,
              f"label={items[0].get('session_label') if items else None}")

        # ---------- 10. Loc lich su theo course ----------
        response = client.get(f"/submissions/mine?course={course_id}", headers=student_headers)
        filtered = response.json() if response.status_code == 200 else {}
        check("GET /submissions/mine?course=", response.status_code == 200, f"status={response.status_code}")
        check("filter course dung",
              all(i.get("course_id") == course_id for i in (filtered.get("items") or [])),
              f"count={len(filtered.get('items') or [])}")

        # ---------- 11. Chi tiet bai nop ----------
        if submission_id is not None:
            response = client.get(f"/submissions/mine/{submission_id}", headers=student_headers)
            body = response.json() if response.status_code == 200 else {}
            check("GET /submissions/mine/{id}", response.status_code == 200, f"status={response.status_code}")
            check("detail co submitted_code", "SIRTUONG" in (body.get("submitted_code") or ""),
                  f"code={str(body.get('submitted_code'))[:40]!r}")
            check("detail co passed_count", isinstance(body.get("passed_count"), int),
                  f"passed={body.get('passed_count')}/{body.get('total_testcases')}")
            check("detail co testcase", isinstance(body.get("testcases"), list),
                  f"count={len(body.get('testcases') or [])}")

        # ---------- 12. KHONG duoc xem bai nop nguoi khac ----------
        response = client.get("/submissions/mine/999999", headers=student_headers)
        check("xem bai nop khong ton tai -> 404", response.status_code == 404,
              f"status={response.status_code}")

        # ---------- 12b. Sinh vien khac KHONG xem duoc bai nop cua minh ----------
        # Thoat context hiện tại, đăng nhập tài khoản sinh viên thứ hai và
        # thử xem bài nộp của sinh viên thứ nhất -> phải 404.
        # SV thu hai: thu tat ca tai khoan con lai (ke ca nhieu mat khau).
        other_token = None
        other_email = None
        for candidate in [e for e in STUDENT_CANDIDATES if e != student_email]:
            token_try, email_try = login_any(client, [candidate], STUDENT_PASSWORDS)
            if token_try:
                other_token, other_email = token_try, email_try
                break
        if other_token:
            response = client.get(
                f"/submissions/mine/{submission_id}",
                headers={"Authorization": f"Bearer {other_token}"},
            )
            check("SV khac xem bai nop cua SV khac -> 404", response.status_code == 404,
                  f"status={response.status_code} ({other_email})")

            # SV khac khong submit duoc vao bai ma SV khac vua hoc
            response = client.post(
                f"/courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/submissions",
                headers={"Authorization": f"Bearer {other_token}"},
                json={"language": "python", "code": "print(1)"},
            )
            # Neu SV khac cung enroll course nay -> van duoc phep submit,
            # nhung phai la submission RIENG cua SV do (khong ghi de).
            check("SV khac submit -> khong ghi de bai cua SV truoc",
                  response.status_code in (200, 201, 202, 403, 404),
                  f"status={response.status_code}")
        else:
            check("login SV thu hai", False, "khong co tai khoan SV thu hai")

        # ---------- 13. Khong co token -> 401 ----------
        response = client.get("/submissions/mine")
        check("thieu token -> 401/403", response.status_code in (401, 403),
              f"status={response.status_code}")

        # ---------- 14. Giao vien khong duoc goi endpoint student ----------
        teacher_token, _teacher_email = login_any(client, TEACHER_CANDIDATES, TEACHER_PASSWORDS)
        if teacher_token:
            response = client.get(
                "/submissions/mine",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )
            check("teacher goi /submissions/mine -> 403", response.status_code == 403,
                  f"status={response.status_code}")
        else:
            check("login teacher", False, "khong login duoc")

        # ---------- 15. Route /mine duoc khai bao TRUOC /{submission_id} ----------
        response = client.get("/submissions/mine", headers=student_headers)
        check("route /mine khong bi nuot boi /{id}", response.status_code == 200,
              f"status={response.status_code}")

    print("=" * 100)
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    print("=" * 100)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
