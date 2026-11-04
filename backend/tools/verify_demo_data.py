"""Kiểm tra bộ dữ liệu demo qua HTTP API thật (không đụng DB trực tiếp).

Chạy: python -m tools.verify_demo_data
Yêu cầu: backend đang chạy ở :8000 và Judge0 đang chạy.
"""

from __future__ import annotations

import os

import httpx

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8000")
PASSWORD = os.getenv("SEED_DEFAULT_PASSWORD", "Password@123")
COURSE = "DEMO101-2026A"

MAIN_STUDENT = "6751071001@st.utc2.edu.vn"
PEER_STUDENT = "6751071003@st.utc2.edu.vn"
EMPTY_STUDENT = "6751071002@st.utc2.edu.vn"

PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"PASS {name:56} {detail}")
    else:
        FAILED += 1
        print(f"FAIL {name:56} {detail}")


def login(client: httpx.Client, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    response.raise_for_status()
    return response.json()["access_token"]


def main() -> int:
    print("=" * 100)
    print(f"VERIFY DEMO DATA  ->  {BASE_URL}")
    print("=" * 100)

    with httpx.Client(base_url=BASE_URL, timeout=120.0) as client:
        # ---------- Sinh viên chính ----------
        token = login(client, MAIN_STUDENT)
        headers = {"Authorization": f"Bearer {token}"}
        check("login SV chinh", True, MAIN_STUDENT)

        me = client.get("/users/me", headers=headers)
        check("/users/me", me.status_code == 200, f"status={me.status_code}")

        courses = client.get("/courses", headers=headers)
        check("GET /courses", courses.status_code == 200, f"status={courses.status_code}")
        course_ids = [c["course_id"] for c in courses.json()]
        check("thay khoa demo", COURSE in course_ids, f"courses={course_ids}")

        detail = client.get(f"/courses/{COURSE}", headers=headers)
        check("GET /courses/{id}", detail.status_code == 200, f"status={detail.status_code}")
        body = detail.json()
        sessions = body.get("sessions") or []
        check("co 4 buoi hoc", len(sessions) == 4, f"count={len(sessions)}")

        statuses = {s["order"]: s["status"] for s in sessions}
        check("buoi 1 dang mo", statuses.get(1) == "open", f"status={statuses.get(1)}")
        check("buoi 2 dang mo", statuses.get(2) == "open", f"status={statuses.get(2)}")
        check("buoi 3 sap toi", statuses.get(3) == "upcoming", f"status={statuses.get(3)}")
        check("buoi 4 da ket thuc", statuses.get(4) == "closed", f"status={statuses.get(4)}")

        # Gom toàn bộ problem sinh viên nhìn thấy.
        visible: dict[str, dict] = {}
        for session in sessions:
            for problem in session.get("problems") or []:
                visible[problem.get("report") or problem["title"]] = {
                    "problem": problem,
                    "lesson_id": session["id"],
                }

        check(
            "thay bai DEMO_SUM",
            "DEMO_SUM" in visible,
            f"visible={sorted(visible)}",
        )
        check(
            "KHONG thay bai chua mo (DEMO_LOCKED)",
            "DEMO_LOCKED" not in visible,
            "",
        )
        check(
            "thay bai khong co testcase (de test loi)",
            "DEMO_NO_TC" in visible,
            "",
        )
        check(
            "an testcase an (chi 2 sample)",
            all(
                len(
                    [
                        testcase
                        for testcase in client.get(
                            f"/courses/{COURSE}/lessons/{info['lesson_id']}"
                            f"/problems/{info['problem']['id']}",
                            headers=headers,
                        ).json().get("testcases", [])
                        if testcase.get("is_sample")
                    ]
                )
                <= 2
                for key, info in visible.items()
                if key in ("DEMO_SUM", "DEMO_FACT")
            ),
            "",
        )

        # ---------- Chi tiết problem ----------
        sum_info = visible.get("DEMO_SUM")
        check("co bai DEMO_SUM de test", sum_info is not None)
        if sum_info:
            problem_detail = client.get(
                f"/courses/{COURSE}/lessons/{sum_info['lesson_id']}"
                f"/problems/{sum_info['problem']['id']}",
                headers=headers,
            )
            check(
                "problem detail 200",
                problem_detail.status_code == 200,
                f"status={problem_detail.status_code}",
            )
            problem = problem_detail.json()
            check("co starter_codes", bool(problem.get("starter_codes")), "")
            check(
                "starter_codes du 5 ngon ngu",
                set(problem.get("starter_codes") or {})
                >= {"python", "c", "cpp", "java"},
                f"keys={sorted(problem.get('starter_codes') or {})}",
            )
            check("co hint", bool(problem.get("hint")), "")
            # Sinh viên chỉ được thấy testcase MẪU (is_sample), testcase ẩn bị giấu.
            testcases = problem.get("testcases") or []
            check(
                "chi tra testcase mau cho SV",
                len(testcases) == 2 and all(t.get("is_sample") for t in testcases),
                f"count={len(testcases)}",
            )
            check(
                "tong so testcase van bao 4",
                problem.get("total_number_testcase") == 4,
                f"total={problem.get('total_number_testcase')}",
            )

            # ---------- Nộp bài ĐÚNG -> accepted ----------
            submit = client.post(
                f"/courses/{COURSE}/lessons/{sum_info['lesson_id']}"
                f"/problems/{sum_info['problem']['id']}/submit",
                headers=headers,
                json={
                    "language": "python",
                    "source_code": (
                        "import sys\n"
                        "d = sys.stdin.read().split()\n"
                        "print(int(d[0]) + int(d[1]))\n"
                    ),
                },
            )
            check("nop bai dung -> 200", submit.status_code == 200, f"status={submit.status_code}")
            if submit.status_code == 200:
                result = submit.json()
                check(
                    "code dung -> accepted",
                    result.get("status") == "accepted",
                    f"status={result.get('status')}",
                )
                check(
                    "dat 4/4 testcase",
                    result.get("passed_count") == 4,
                    f"passed={result.get('passed_count')}/{result.get('total_testcases')}",
                )

            # ---------- Nộp bài SAI -> wrong_answer ----------
            submit_wrong = client.post(
                f"/courses/{COURSE}/lessons/{sum_info['lesson_id']}"
                f"/problems/{sum_info['problem']['id']}/submit",
                headers=headers,
                json={"language": "python", "source_code": "print(0)\n"},
            )
            if submit_wrong.status_code == 200:
                result = submit_wrong.json()
                check(
                    "code sai -> wrong_answer",
                    result.get("status") == "wrong_answer",
                    f"status={result.get('status')}",
                )
                check(
                    "wrong_answer co testcase detail",
                    len(result.get("testcases") or []) == 4,
                    f"count={len(result.get('testcases') or [])}",
                )

            # ---------- Nộp bài lỗi cú pháp -> compile_error ----------
            submit_syntax = client.post(
                f"/courses/{COURSE}/lessons/{sum_info['lesson_id']}"
                f"/problems/{sum_info['problem']['id']}/submit",
                headers=headers,
                json={"language": "python", "source_code": "def broken(:\n"},
            )
            if submit_syntax.status_code == 200:
                result = submit_syntax.json()
                check(
                    "syntax error -> compile_error",
                    result.get("status") == "compile_error",
                    f"status={result.get('status')}",
                )
                check(
                    "compile_error co output",
                    bool(result.get("compile_output")),
                    "",
                )

        # ---------- Bài không có testcase -> lỗi rõ ràng ----------
        no_tc = visible.get("DEMO_NO_TC")
        if no_tc:
            response = client.post(
                f"/courses/{COURSE}/lessons/{no_tc['lesson_id']}"
                f"/problems/{no_tc['problem']['id']}/submit",
                headers=headers,
                json={"language": "python", "source_code": "print(1)\n"},
            )
            check(
                "bai khong testcase -> 4xx",
                400 <= response.status_code < 500,
                f"status={response.status_code}",
            )
            check(
                "thong bao loi de hieu",
                "testcase" in response.text.lower(),
                response.text[:80],
            )

        # ---------- Lịch sử nộp bài ----------
        history = client.get("/submissions/mine", headers=headers)
        check("GET /submissions/mine", history.status_code == 200, f"status={history.status_code}")
        if history.status_code == 200:
            payload = history.json()
            counts = payload.get("counts") or {}
            items = payload.get("items") or []
            check("lich su co items", len(items) > 0, f"count={len(items)}")
            check(
                "counts khop total",
                counts.get("all") == len(items),
                f"all={counts.get('all')} items={len(items)}",
            )
            present = {item["status"] for item in items}
            expected = {
                "accepted",
                "wrong_answer",
                "compile_error",
                "runtime_error",
                "time_limit_exceeded",
                "pending",
                "internal_error",
                "error",
            }
            check(
                "phu du 8 trang thai",
                expected <= present,
                f"missing={sorted(expected - present)}",
            )

            # Chi tiết 1 bài nộp
            detail_res = client.get(
                f"/submissions/mine/{items[0]['id']}", headers=headers
            )
            check(
                "GET /submissions/mine/{id}",
                detail_res.status_code == 200,
                f"status={detail_res.status_code}",
            )

            # Lọc theo course
            filtered = client.get(
                f"/submissions/mine?course={COURSE}", headers=headers
            )
            check(
                "loc theo course",
                filtered.status_code == 200,
                f"status={filtered.status_code}",
            )

        # ---------- Sinh viên cùng lớp ----------
        peer_token = login(client, PEER_STUDENT)
        peer_headers = {"Authorization": f"Bearer {peer_token}"}
        peer_history = client.get("/submissions/mine", headers=peer_headers)
        check(
            "SV cung lop co lich su",
            peer_history.status_code == 200
            and len(peer_history.json().get("items") or []) == 2,
            f"count={len(peer_history.json().get('items') or [])}",
        )

        # SV khác không xem được bài nộp của SV chính.
        if history.status_code == 200 and history.json().get("items"):
            other_id = history.json()["items"][0]["id"]
            cross = client.get(f"/submissions/mine/{other_id}", headers=peer_headers)
            check(
                "SV khac xem bai nop -> 404",
                cross.status_code == 404,
                f"status={cross.status_code}",
            )

        # ---------- Sinh viên không có lớp ----------
        empty_token = login(client, EMPTY_STUDENT)
        empty_headers = {"Authorization": f"Bearer {empty_token}"}
        empty_courses = client.get("/courses", headers=empty_headers)
        check(
            "SV khong lop -> 0 khoa hoc",
            empty_courses.status_code == 200 and empty_courses.json() == [],
            f"courses={empty_courses.text[:60]}",
        )
        empty_history = client.get("/submissions/mine", headers=empty_headers)
        check(
            "SV khong lop -> lich su rong",
            empty_history.status_code == 200
            and len(empty_history.json().get("items") or []) == 0,
            "",
        )

    print("=" * 100)
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    print("=" * 100)
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
