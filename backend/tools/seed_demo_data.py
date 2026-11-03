"""Seed bộ dữ liệu DEMO đầy đủ để test MỌI nhánh của giao diện sinh viên.

Chạy:
    python -m tools.seed_demo_data            # thêm vào (idempotent, chạy lại không nhân đôi)
    python -m tools.seed_demo_data --reset    # xoá dữ liệu demo rồi tạo lại từ đầu

Dữ liệu tạo ra
--------------
- Lớp hành chính mới: ``CQ.67.CNTT``
- 1 giáo viên demo + 3 sinh viên demo
- Khoá học ``DEMO101-2026A`` với 4 buổi học phủ đủ trạng thái:
    * Buổi 1, 2 : đang mở   (open)
    * Buổi 3    : sắp tới   (upcoming)
    * Buổi 4    : đã kết thúc (closed)
- 9 bài tập phủ đủ:
    * level easy / medium / hard
    * bài có testcase mẫu + testcase ẩn
    * bài CHƯA MỞ (start_datetime ở tương lai -> sinh viên không thấy)
    * bài KHÔNG CÓ TESTCASE (để test nhánh "Bài tập chưa có testcase để chấm")
- 11 bài nộp phủ đủ 8 trạng thái:
    accepted, wrong_answer, compile_error, runtime_error,
    time_limit_exceeded, pending, internal_error, error
- 1 sinh viên KHÔNG tham gia lớp nào -> test empty state

Ngày tháng được tính TƯƠNG ĐỐI so với hôm nay, nên dữ liệu luôn còn hạn
dù bạn chạy script vào bất kỳ ngày nào.
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

from sqlmodel import Session, select  # noqa: E402

from app.core.database import engine  # noqa: E402
from app.core.dependencies import Role  # noqa: E402
from app.core.security.passwords import hash_password  # noqa: E402
from app.core.utils.datetime_utils import (  # noqa: E402
    VN_TZ,
    today_vn,
    vn_day_end,
    vn_day_start,
)
from app.models import (  # noqa: E402
    Class,
    Course,
    Enrollment,
    Lesson,
    Problem,
    Submission,
    Testcase,
    User,
)

# ─── Hằng số định danh ──────────────────────────────────────────────────────

EMAIL_DOMAIN = "st.utc2.edu.vn"
DEFAULT_PASSWORD = os.getenv("SEED_DEFAULT_PASSWORD", "Password@123")

DEMO_CLASS_ID = "CQ.67.CNTT"
DEMO_COURSE_ID = "DEMO101-2026A"
# Khoá thứ hai (khác học kỳ) để test dashboard: grid/list view, filter học kỳ,
# filter năm học và search theo mã/tên lớp.
DEMO_COURSE_ID_2 = "DEMO102-2025B"
DEMO_COURSE_IDS = [DEMO_COURSE_ID, DEMO_COURSE_ID_2]

TEACHER = {
    "user_id": "1111111117",
    "full_name": "Giảng Viên Demo",
    "date_of_birth": date(1987, 4, 9),
}

# Sinh viên chính để test — có bài nộp đủ mọi trạng thái.
MAIN_STUDENT = {
    "user_id": "6751071001",
    "full_name": "Đặng Minh Demo",
    "date_of_birth": date(2005, 5, 15),
}
# Sinh viên cùng lớp, có ít bài nộp (test danh sách nhiều sinh viên).
PEER_STUDENT = {
    "user_id": "6751071003",
    "full_name": "Trần Văn Bạn Học",
    "date_of_birth": date(2005, 11, 2),
}
# Sinh viên KHÔNG tham gia lớp nào -> test empty state.
EMPTY_STUDENT = {
    "user_id": "6751071002",
    "full_name": "Nguyễn Thị Trống",
    "date_of_birth": date(2005, 8, 20),
}

DEMO_STUDENTS = [MAIN_STUDENT, PEER_STUDENT, EMPTY_STUDENT]
ENROLLED_STUDENT_IDS = [MAIN_STUDENT["user_id"], PEER_STUDENT["user_id"]]
DEMO_USER_IDS = [TEACHER["user_id"], *[s["user_id"] for s in DEMO_STUDENTS]]

IO_TYPE = "string"

# ─── Mẫu code khởi tạo theo ngôn ngữ ────────────────────────────────────────
# Schema của API yêu cầu đủ 4 ngôn ngữ python/c/cpp/java; javascript là bonus
# để tab JS trong editor cũng có mẫu riêng thay vì rơi về skeleton mặc định.

STARTER_CODES: dict[str, str] = {
    "python": (
        "import sys\n"
        "\n"
        "def main():\n"
        "    data = sys.stdin.read().split()\n"
        "    # TODO: viết lời giải của bạn ở đây\n"
        "    pass\n"
        "\n"
        "\n"
        "if __name__ == \"__main__\":\n"
        "    main()\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "\n"
        "int main(void) {\n"
        "    /* TODO: viết lời giải của bạn ở đây */\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "using namespace std;\n"
        "\n"
        "int main() {\n"
        "    // TODO: viết lời giải của bạn ở đây\n"
        "    return 0;\n"
        "}\n"
    ),
    "java": (
        "import java.util.*;\n"
        "\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        // TODO: viết lời giải của bạn ở đây\n"
        "    }\n"
        "}\n"
    ),
    "javascript": (
        "const fs = require('fs');\n"
        "const data = fs.readFileSync(0, 'utf8').trim().split(/\\s+/);\n"
        "// TODO: viết lời giải của bạn ở đây\n"
    ),
}

DEFAULT_CONSTRAINTS = (
    "Dòng đầu là số lượng phần tử / số bộ dữ liệu.\n"
    "Đọc dữ liệu từ stdin, in kết quả ra stdout.\n"
    "Không in thêm bất kỳ nội dung nào khác."
)


# ─── Tiện ích thời gian ─────────────────────────────────────────────────────

def _day(offset: int) -> date:
    """Ngày cách hôm nay `offset` ngày (âm = quá khứ)."""
    return today_vn() + timedelta(days=offset)


def _at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=VN_TZ)


# ─── Định nghĩa dữ liệu ─────────────────────────────────────────────────────

# (số buổi, tên, offset_start, offset_end, mô tả trạng thái mong đợi)
LESSONS = [
    (1, "Nhập môn và tính toán", -30, +30, "open"),
    (2, "Mảng và chuỗi", -10, +20, "open"),
    (3, "Sắp tới (chưa mở)", +14, +28, "upcoming"),
    (4, "Đã kết thúc", -60, -30, "closed"),
]

# Mỗi problem:
#   lesson_no, title, level, time_limit, hint, complexity, report_code,
#   tests (list[tuple[input, expected]]), sample_count, start_offset_days | None
PROBLEMS = [
    {
        "lesson_no": 1,
        "title": "Tổng hai số",
        "level": "easy",
        "time_limit": 1,
        "hint": "Đọc 2 số nguyên rồi in tổng.",
        "complexity": "O(1)",
        "report": "DEMO_SUM",
        "tests": [("1 2", "3"), ("-5 5", "0"), ("100 250", "350"), ("0 0", "0")],
        "sample_count": 2,
    },
    {
        "lesson_no": 1,
        "title": "Tính giai thừa",
        "level": "easy",
        "time_limit": 1,
        "hint": "0! = 1. Dùng vòng lặp để tránh đệ quy sâu.",
        "complexity": "O(n)",
        "report": "DEMO_FACT",
        "tests": [("0", "1"), ("5", "120"), ("10", "3628800")],
        "sample_count": 2,
    },
    {
        "lesson_no": 1,
        "title": "Kiểm tra số nguyên tố",
        "level": "medium",
        "time_limit": 1,
        "hint": "Chỉ cần thử ước tới căn bậc hai của n.",
        "complexity": "O(√n)",
        "report": "DEMO_PRIME",
        "tests": [("7", "true"), ("1", "false"), ("15", "false"), ("2", "true")],
        "sample_count": 2,
    },
    {
        "lesson_no": 2,
        "title": "Đảo ngược mảng",
        "level": "medium",
        "time_limit": 2,
        "hint": "In các phần tử theo thứ tự ngược, cách nhau bởi dấu cách.",
        "complexity": "O(n)",
        "report": "DEMO_REV",
        "tests": [
            ("3\n1 2 3", "3 2 1"),
            ("1\n5", "5"),
            ("4\n-1 0 7 2", "2 7 0 -1"),
        ],
        "sample_count": 2,
    },
    {
        "lesson_no": 2,
        "title": "Sắp xếp mảng tăng dần",
        "level": "hard",
        "time_limit": 2,
        "hint": "Có thể dùng sort sẵn của ngôn ngữ, nhưng hãy thử tự cài đặt.",
        "complexity": "O(n log n)",
        "report": "DEMO_SORT",
        "tests": [
            ("5\n5 3 8 1 9", "1 3 5 8 9"),
            ("3\n-2 -5 -1", "-5 -2 -1"),
            ("1\n0", "0"),
        ],
        "sample_count": 2,
    },
    {
        # Bài cố tình không có testcase -> test nhánh lỗi khi nộp bài.
        "lesson_no": 2,
        "title": "Bài chưa có testcase (dùng để test lỗi)",
        "level": "easy",
        "time_limit": 1,
        "hint": "Bài này cố tình không có testcase để kiểm tra thông báo lỗi.",
        "complexity": "—",
        "report": "DEMO_NO_TC",
        "tests": [],
        "sample_count": 0,
    },
    {
        # Bài chưa mở: start_datetime ở tương lai -> sinh viên KHÔNG thấy.
        "lesson_no": 2,
        "title": "Bài chưa mở (sinh viên không thấy)",
        "level": "easy",
        "time_limit": 1,
        "hint": "Bài này sẽ mở sau 7 ngày.",
        "complexity": "O(1)",
        "report": "DEMO_LOCKED",
        "tests": [("1", "1")],
        "sample_count": 1,
        "start_offset_days": 7,
    },
    {
        "lesson_no": 3,
        "title": "Bài của buổi sắp tới",
        "level": "easy",
        "time_limit": 1,
        "hint": "Sẽ mở khi buổi học bắt đầu.",
        "complexity": "O(1)",
        "report": "DEMO_FUTURE",
        "tests": [("2", "4")],
        "sample_count": 1,
    },
    {
        "lesson_no": 4,
        "title": "Bài của buổi đã kết thúc",
        "level": "medium",
        "time_limit": 1,
        "hint": "Buổi học đã kết thúc, nhưng bài vẫn nộp được (test edge case).",
        "complexity": "O(1)",
        "report": "DEMO_CLOSED",
        "tests": [("2", "4")],
        "sample_count": 1,
    },
]

# Khoá 2 (học kỳ trước) — bài ngắn gọn, đủ để test filter/search dashboard.
LESSONS_2 = [
    (1, "Ôn tập cú pháp", -200, -160, "closed"),
    (2, "Mảng một chiều", -160, -120, "closed"),
]

PROBLEMS_2 = [
    {
        "lesson_no": 1,
        "title": "In Hello World",
        "level": "easy",
        "time_limit": 1,
        "hint": "In đúng chuỗi Hello World.",
        "complexity": "O(1)",
        "report": "DEMO2_HELLO",
        "tests": [("", "Hello World")],
        "sample_count": 1,
    },
    {
        "lesson_no": 2,
        "title": "Tổng các phần tử mảng",
        "level": "easy",
        "time_limit": 1,
        "hint": "Duyệt mảng và cộng dồn.",
        "complexity": "O(n)",
        "report": "DEMO2_SUMARR",
        "tests": [
            ("3\n1 2 3", "6"),
            ("4\n10 20 30 40", "100"),
        ],
        "sample_count": 1,
    },
]

# (student_id, report_code, language, status, passed, compile_output, feedback, day_offset)
SUBMISSIONS = [
    (
        MAIN_STUDENT["user_id"], "DEMO_SUM", "python", "accepted", 4, None,
        "Chính xác! Cách giải tối ưu.", -5,
    ),
    (
        MAIN_STUDENT["user_id"], "DEMO_SUM", "cpp", "wrong_answer", 2, None,
        "Sai ở testcase có số âm.", -4,
    ),
    (
        MAIN_STUDENT["user_id"], "DEMO_SUM", "java", "compile_error", 0,
        "Main.java:5: error: ';' expected\n        int a = 1\n                    ^",
        None, -4,
    ),
    (
        MAIN_STUDENT["user_id"], "DEMO_FACT", "python", "runtime_error", 1,
        "Traceback (most recent call last):\n"
        "  File \"script.py\", line 4, in <module>\n"
        "RecursionError: maximum recursion depth exceeded",
        None, -3,
    ),
    (
        MAIN_STUDENT["user_id"], "DEMO_FACT", "javascript", "time_limit_exceeded", 0,
        "Vượt quá giới hạn thời gian 1s", None, -3,
    ),
    (
        MAIN_STUDENT["user_id"], "DEMO_PRIME", "python", "pending", 0, None, None, -2,
    ),
    (
        MAIN_STUDENT["user_id"], "DEMO_REV", "c", "accepted", 3, None,
        "Tốt lắm!", -2,
    ),
    (
        MAIN_STUDENT["user_id"], "DEMO_SORT", "python", "internal_error", 0,
        "Hệ thống chấm bài gặp lỗi nội bộ", None, -1,
    ),
    (
        MAIN_STUDENT["user_id"], "DEMO_SORT", "python", "error", 0,
        "Không kết nối được Judge0", None, -1,
    ),
    (
        PEER_STUDENT["user_id"], "DEMO_SUM", "python", "accepted", 4, None,
        "Đạt.", -3,
    ),
    (
        PEER_STUDENT["user_id"], "DEMO_FACT", "cpp", "wrong_answer", 2, None,
        "Sai ở n = 0.", -2,
    ),
    (
        MAIN_STUDENT["user_id"], "DEMO2_HELLO", "python", "accepted", 1, None,
        "Đạt.", -180,
    ),
    (
        MAIN_STUDENT["user_id"], "DEMO2_SUMARR", "cpp", "wrong_answer", 1, None,
        "Sai khi mảng có số âm.", -150,
    ),
]


# ─── Các bước seed ──────────────────────────────────────────────────────────

def _wipe(session: Session) -> None:
    """Xoá sạch dữ liệu demo (đúng thứ tự khoá ngoại)."""
    lesson_ids = [
        lesson.lesson_id
        for lesson in session.exec(
            select(Lesson).where(Lesson.course_id.in_(DEMO_COURSE_IDS))
        ).all()
    ]
    problem_ids = (
        [
            problem.problem_id
            for problem in session.exec(
                select(Problem).where(Problem.lesson_id.in_(lesson_ids))
            ).all()
        ]
        if lesson_ids
        else []
    )

    if problem_ids:
        for submission in session.exec(
            select(Submission).where(Submission.problem_id.in_(problem_ids))
        ).all():
            session.delete(submission)
        for testcase in session.exec(
            select(Testcase).where(Testcase.problem_id.in_(problem_ids))
        ).all():
            session.delete(testcase)
        for problem in session.exec(
            select(Problem).where(Problem.problem_id.in_(problem_ids))
        ).all():
            session.delete(problem)
    if lesson_ids:
        for lesson in session.exec(
            select(Lesson).where(Lesson.lesson_id.in_(lesson_ids))
        ).all():
            session.delete(lesson)

    for enrollment in session.exec(
        select(Enrollment).where(Enrollment.course_id.in_(DEMO_COURSE_IDS))
    ).all():
        session.delete(enrollment)

    for course_id in DEMO_COURSE_IDS:
        course = session.get(Course, course_id)
        if course:
            session.delete(course)

    for user_id in DEMO_USER_IDS:
        user = session.get(User, user_id)
        if user:
            session.delete(user)

    demo_class = session.get(Class, DEMO_CLASS_ID)
    if demo_class:
        session.delete(demo_class)

    session.commit()
    print("  -> Đã xoá dữ liệu demo cũ")


def _seed_class(session: Session) -> None:
    if session.get(Class, DEMO_CLASS_ID) is None:
        session.add(
            Class(
                class_id=DEMO_CLASS_ID,
                type="CQ",
                course_number=67,
                department="CNTT",
            )
        )
        session.commit()
        print(f"  + Lớp {DEMO_CLASS_ID}")
    else:
        print(f"  = Lớp {DEMO_CLASS_ID} đã có")


def _seed_users(session: Session) -> None:
    hashed = hash_password(DEFAULT_PASSWORD)
    rows = [
        {**TEACHER, "role_id": Role.TEACHER},
        *[{**student, "role_id": Role.STUDENT} for student in DEMO_STUDENTS],
    ]
    for row in rows:
        if session.get(User, row["user_id"]):
            print(f"  = User {row['user_id']} đã có")
            continue
        session.add(
            User(
                user_id=row["user_id"],
                full_name=row["full_name"],
                email=f"{row['user_id']}@{EMAIL_DOMAIN}",
                date_of_birth=row["date_of_birth"],
                role_id=row["role_id"],
                hashed_password=hashed,
                # Tài khoản demo đăng nhập được ngay, không bị bắt đổi mật khẩu.
                must_change_password=False,
                class_id=DEMO_CLASS_ID,
            )
        )
        print(f"  + User {row['user_id']} ({row['full_name']})")
    session.commit()


def _seed_course_and_enrollments(session: Session) -> None:
    courses = [
        {
            "course_id": DEMO_COURSE_ID,
            "course_name": "Lập trình Demo (đầy đủ tình huống)",
            "term": "HK1 2026-2027",
            # Ảnh bìa: frontend suy luận ngôn ngữ từ avt_link.
            "avt_link": "/images/background-python1.jpg",
            "start_date": _at(_day(-60), 0),
            "end_date": _at(_day(+90), 23, 59),
        },
        {
            "course_id": DEMO_COURSE_ID_2,
            "course_name": "Cấu trúc dữ liệu Demo (học kỳ trước)",
            "term": "HK2 2025-2026",
            "avt_link": "/images/background-c++.jpg",
            "start_date": _at(_day(-200), 0),
            "end_date": _at(_day(-100), 23, 59),
        },
    ]
    for course in courses:
        if session.get(Course, course["course_id"]) is None:
            session.add(
                Course(
                    **course,
                    created_by=TEACHER["user_id"],
                    total_number_student=len(ENROLLED_STUDENT_IDS),
                )
            )
            session.commit()
            print(f"  + Khoá {course['course_id']}")
        else:
            # Cập nhật avt_link để mỗi lớp demo có ảnh bìa khác nhau
            # (frontend suy luận ngôn ngữ/ảnh bìa từ avt_link).
            existing = session.get(Course, course["course_id"])
            if existing and existing.avt_link != course["avt_link"]:
                existing.avt_link = course["avt_link"]
                session.add(existing)
                session.commit()
            print(f"  = Khoá {course['course_id']} đã có")

    for student_id in ENROLLED_STUDENT_IDS:
        for course_id in DEMO_COURSE_IDS:
            exists = session.exec(
                select(Enrollment).where(
                    Enrollment.course_id == course_id,
                    Enrollment.student_id == student_id,
                )
            ).first()
            if exists is None:
                session.add(
                    Enrollment(course_id=course_id, student_id=student_id)
                )
                print(f"  + Ghi danh {student_id} -> {course_id}")
    session.commit()


def _seed_lessons(
    session: Session, specs, course_id: str
) -> dict[int, Lesson]:
    lessons: dict[int, Lesson] = {}
    for number, name, start_offset, end_offset, _state in specs:
        lesson = session.exec(
            select(Lesson).where(
                Lesson.course_id == course_id,
                Lesson.lesson_number == number,
            )
        ).first()
        if lesson is None:
            lesson = Lesson(
                lesson_number=number,
                lesson_name=name,
                course_id=course_id,
                start_date=_day(start_offset),
                end_date=_day(end_offset),
            )
            session.add(lesson)
            session.commit()
            session.refresh(lesson)
            print(f"  + [{course_id}] Buổi {number}: {name}")
        lessons[number] = lesson
    return lessons


def _seed_problems(
    session: Session, lessons: dict[int, Lesson], specs
) -> dict[str, Problem]:
    problems: dict[str, Problem] = {}
    for spec in specs:
        lesson = lessons[spec["lesson_no"]]
        problem = session.exec(
            select(Problem).where(
                Problem.lesson_id == lesson.lesson_id,
                Problem.title == spec["title"],
            )
        ).first()

        start_day = (
            _day(spec["start_offset_days"])
            if spec.get("start_offset_days") is not None
            else lesson.start_date
        )
        end_day = lesson.end_date

        if problem is None:
            problem = Problem(
                lesson_id=lesson.lesson_id,
                title=spec["title"],
                function_name=None,
                description=(
                    f"{spec['title']}.\n\n"
                    "Đây là bài tập trong bộ dữ liệu DEMO, được tạo để kiểm thử "
                    "giao diện sinh viên ở mọi tình huống."
                ),
                time_limit_seconds=spec["time_limit"],
                start_format_code=STARTER_CODES["python"],
                starter_codes=dict(STARTER_CODES),
                constraints=DEFAULT_CONSTRAINTS,
                level=spec["level"],
                hint=spec["hint"],
                complexity=spec["complexity"],
                start_datetime=vn_day_start(start_day),
                end_datetime=vn_day_end(end_day),
                total_number_testcase=0,
                report=spec["report"],
            )
            session.add(problem)
            session.commit()
            session.refresh(problem)
            print(
                f"  + Bài {spec['report']}: {spec['title']} "
                f"({len(spec['tests'])} testcase)"
            )

        # Testcase: tạo nếu chưa có (so khớp theo input).
        existing_inputs = {
            testcase.input
            for testcase in session.exec(
                select(Testcase).where(Testcase.problem_id == problem.problem_id)
            ).all()
        }
        for index, (test_input, expected) in enumerate(spec["tests"]):
            if test_input in existing_inputs:
                continue
            session.add(
                Testcase(
                    problem_id=problem.problem_id,
                    input=test_input,
                    expected_output=expected,
                    is_sample=index < spec["sample_count"],
                    input_type=IO_TYPE,
                    expected_output_type=IO_TYPE,
                )
            )
        session.commit()

        problem.total_number_testcase = len(
            session.exec(
                select(Testcase).where(Testcase.problem_id == problem.problem_id)
            ).all()
        )
        session.add(problem)
        session.commit()
        session.refresh(problem)
        problems[spec["report"]] = problem
    return problems


def _seed_submissions(
    session: Session, problems: dict[str, Problem]
) -> None:
    for (
        student_id,
        report_code,
        language,
        status,
        passed,
        compile_output,
        feedback,
        day_offset,
    ) in SUBMISSIONS:
        problem = problems.get(report_code)
        if problem is None:
            print(f"  ! Bỏ qua bài nộp: không tìm thấy bài {report_code}")
            continue

        submitted_at = _at(_day(day_offset), 20, 30)
        exists = session.exec(
            select(Submission).where(
                Submission.problem_id == problem.problem_id,
                Submission.student_id == student_id,
                Submission.status == status,
                Submission.submitted_datetime == submitted_at,
            )
        ).first()
        if exists is not None:
            continue

        session.add(
            Submission(
                problem_id=problem.problem_id,
                student_id=student_id,
                language=language,
                submitted_code=STARTER_CODES.get(language, STARTER_CODES["python"]),
                status=status,
                compile_output=compile_output,
                feedback=feedback,
                manual_score=None,
                passed_count=passed,
                submitted_datetime=submitted_at,
            )
        )
    session.commit()
    total = len(
        session.exec(
            select(Submission).where(
                Submission.problem_id.in_(
                    [problem.problem_id for problem in problems.values()]
                )
            )
        ).all()
    )
    print(f"  -> Tổng số bài nộp của bộ demo: {total}")


def _refresh_counters(
    session: Session, lessons_by_course: dict[str, dict[int, Lesson]]
) -> None:
    for course_id, lessons in lessons_by_course.items():
        course = session.get(Course, course_id)
        if course:
            course.total_number_student = len(
                session.exec(
                    select(Enrollment).where(Enrollment.course_id == course_id)
                ).all()
            )
            session.add(course)

        for lesson in lessons.values():
            problems = session.exec(
                select(Problem).where(Problem.lesson_id == lesson.lesson_id)
            ).all()
            lesson.total_number_assignment = len(problems)

        finished: set[str] | None = None
        for problem in problems:
            solved = {
                submission.student_id
                for submission in session.exec(
                    select(Submission).where(
                        Submission.problem_id == problem.problem_id,
                        Submission.status == "accepted",
                    )
                ).all()
            }
            finished = solved if finished is None else finished & solved
        lesson.total_number_student_finished = len(finished or ())
        session.add(lesson)
    session.commit()


# ─── Entrypoint ─────────────────────────────────────────────────────────────

def main() -> int:
    reset = "--reset" in sys.argv

    print("=" * 78)
    print("SEED DỮ LIỆU DEMO CHO SINH VIÊN")
    print("=" * 78)
    print(f"Hôm nay (VN): {today_vn().isoformat()}")

    with Session(engine) as session:
        if reset:
            print("\n[0] Xoá dữ liệu demo cũ")
            _wipe(session)

        print("\n[1] Lớp hành chính")
        _seed_class(session)

        print("\n[2] Người dùng")
        _seed_users(session)

        print("\n[3] Khoá học + ghi danh")
        _seed_course_and_enrollments(session)

        print("\n[4] Buổi học")
        lessons_by_course = {
            DEMO_COURSE_ID: _seed_lessons(session, LESSONS, DEMO_COURSE_ID),
            DEMO_COURSE_ID_2: _seed_lessons(session, LESSONS_2, DEMO_COURSE_ID_2),
        }

        print("\n[5] Bài tập + testcase")
        problems: dict[str, Problem] = {}
        problems.update(_seed_problems(session, lessons_by_course[DEMO_COURSE_ID], PROBLEMS))
        problems.update(
            _seed_problems(session, lessons_by_course[DEMO_COURSE_ID_2], PROBLEMS_2)
        )

        print("\n[6] Bài nộp (phủ mọi trạng thái)")
        _seed_submissions(session, problems)

        print("\n[7] Cập nhật cột đếm")
        _refresh_counters(session, lessons_by_course)

    print("\n" + "=" * 78)
    print("HOÀN TẤT — TÀI KHOẢN ĐỂ TEST")
    print("=" * 78)
    print(f"Mật khẩu chung: {DEFAULT_PASSWORD}")
    print()
    print("SINH VIÊN CHÍNH (có bài nộp đủ 8 trạng thái):")
    print(f"  {MAIN_STUDENT['user_id']}@{EMAIL_DOMAIN}   ({MAIN_STUDENT['full_name']})")
    print()
    print("SINH VIÊN CÙNG LỚP (có ít bài nộp):")
    print(f"  {PEER_STUDENT['user_id']}@{EMAIL_DOMAIN}   ({PEER_STUDENT['full_name']})")
    print()
    print("SINH VIÊN KHÔNG CÓ LỚP (test empty state):")
    print(f"  {EMPTY_STUDENT['user_id']}@{EMAIL_DOMAIN}   ({EMPTY_STUDENT['full_name']})")
    print()
    print("GIÁO VIÊN (chủ khoá demo):")
    print(f"  {TEACHER['user_id']}@{EMAIL_DOMAIN}   ({TEACHER['full_name']})")
    print()
    print(f"Khoá học: {DEMO_COURSE_ID}  (HK1 2026-2027 — đang diễn ra)")
    print("  Buổi 1, 2 : đang mở")
    print("  Buổi 3    : sắp tới (chưa mở)")
    print("  Buổi 4    : đã kết thúc")
    print("  Bài DEMO_NO_TC : không có testcase (test nhánh lỗi)")
    print("  Bài DEMO_LOCKED: chưa mở (sinh viên không thấy)")
    print(f"Khoá học: {DEMO_COURSE_ID_2}  (HK2 2025-2026 — đã kết thúc)")
    print("  Dùng để test filter học kỳ / năm học + search trên dashboard.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
