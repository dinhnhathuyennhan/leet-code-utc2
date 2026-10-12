# app/seed_data.py
import logging
import os
from datetime import datetime

from sqlmodel import Session, or_, select

from app.core.password import hash_password
from app.db import engine
from models import Class, Course, Enrollment, Lesson, Problem, Submission, Testcase, User

logger = logging.getLogger("uvicorn.error")
SEED_TEACHER_ID = "6451071003"

# ===== CLASSES SEED =====
SEED_CLASSES = [
    {
        "class_id": "K62-CNTT01",
        "type": "Chinh quy",
        "course_number": 42,
        "department": "Cong nghe thong tin",
    },
    {
        "class_id": "K62-CNTT02",
        "type": "Chinh quy",
        "course_number": 42,
        "department": "Cong nghe thong tin",
    },
]

# ===== USERS SEED =====
SEED_USERS = [
    {
        "user_id": "GV001",
        "full_name": "ThS. Trần Hoàng Nam",
        "email": "tran.hoang.nam@utc2.edu.vn",
        "role_id": 2,
        "must_change_password": False,
    },
    {
        "user_id": "6451071003",
        "full_name": "TEACHER NEW",
        "email": "teacher.new@st.utc2.edu.vn",
        "role_id": 2,
        "must_change_password": True,
    },
    {
        "user_id": "6451071004",
        "full_name": "STUDENT NEW",
        "email": "student.new@st.utc2.edu.vn",
        "role_id": 3,
        "class_id": "K62-CNTT02",
        "must_change_password": True,
    },
    {
        "user_id": "6451071005",
        "full_name": "STUDENT TOKEN",
        "email": "student.token@st.utc2.edu.vn",
        "role_id": 3,
    },
    # Students for JAVA01
    {"user_id": "2151129801", "full_name": "Nguyễn Văn An", "email": "nguyen.van.an@st.utc2.edu.vn", "role_id": 3},
    {"user_id": "2151129802", "full_name": "Lê Thị Bình", "email": "le.thi.binh@st.utc2.edu.vn", "role_id": 3},
    {"user_id": "2151129803", "full_name": "Phạm Quốc Cường", "email": "pham.quoc.cuong@st.utc2.edu.vn", "role_id": 3},
    {"user_id": "2151129804", "full_name": "Hoàng Minh Đức", "email": "hoang.minh.duc@st.utc2.edu.vn", "role_id": 3},
    {"user_id": "2151129805", "full_name": "Đỗ Minh Quân", "email": "do.minh.quan@st.utc2.edu.vn", "role_id": 3},
    {"user_id": "2151129806", "full_name": "Trần Văn Cường", "email": "tran.van.cuong@st.utc2.edu.vn", "role_id": 3},
    {"user_id": "2151129807", "full_name": "Vũ Thị Thu", "email": "vu.thi.thu@st.utc2.edu.vn", "role_id": 3},
    {"user_id": "2151129808", "full_name": "Bùi Thế Anh", "email": "bui.the.anh@st.utc2.edu.vn", "role_id": 3},
    {"user_id": "2151129809", "full_name": "Lý Khánh Hà", "email": "ly.khanh.ha@st.utc2.edu.vn", "role_id": 3},
    {"user_id": "2151129810", "full_name": "Ngô Văn Khoa", "email": "ngo.van.khoa@st.utc2.edu.vn", "role_id": 3},
    {"user_id": "2151129901", "full_name": "Sinh viên kiểm thử", "email": "student.test@st.utc2.edu.vn", "role_id": 3, "class_id": "K62-CNTT02"},
]

# Students in the course all belong to the same administrative class.  Keeping
# this normalization here also upgrades existing seed users on a re-run.
for _user in SEED_USERS:
    if (
        _user.get("role_id") == 3
        and _user.get("user_id", "").startswith("215")
        and _user.get("user_id") != "2151129901"
    ):
        _user["class_id"] = "K62-CNTT01"
for _number in range(11, 43):
    SEED_USERS.append(
        {
            "user_id": f"21511298{_number:02d}",
            "full_name": f"Sinh vien { _number:02d}",
            "email": f"student.{_number:02d}@st.utc2.edu.vn",
            "role_id": 3,
            "class_id": "K62-CNTT01",
        }
    )

# ===== COURSES SEED =====
SEED_COURSES = [
    {
        "course_id": "JAVA01",
        "course_name": "Lập trình Java",
        "term": "HK1-2024-2025",
        "start_date": datetime(2024, 9, 1, 0, 0, 0),
        "end_date": datetime(2024, 12, 30, 23, 59, 59),
        "avt_link": "java",
        "created_by": SEED_TEACHER_ID,
        "total_number_student": 0,
    },
    {
        "course_id": "PY01",
        "course_name": "Lập trình Python",
        "term": "HK1-2024-2025",
        "start_date": datetime(2024, 9, 1, 0, 0, 0),
        "end_date": datetime(2024, 12, 30, 23, 59, 59),
        "avt_link": "python",
        "created_by": SEED_TEACHER_ID,
        "total_number_student": 0,
    },
    {
        "course_id": "JS01",
        "course_name": "Lập trình JavaScript",
        "term": "HK1-2024-2025",
        "start_date": datetime(2024, 9, 1, 0, 0, 0),
        "end_date": datetime(2024, 12, 30, 23, 59, 59),
        "avt_link": "javascript",
        "created_by": SEED_TEACHER_ID,
        "total_number_student": 0,
    },
    {
        "course_id": "CPP01",
        "course_name": "Lập trình C++",
        "term": "HK1-2024-2025",
        "start_date": datetime(2024, 9, 1, 0, 0, 0),
        "end_date": datetime(2024, 12, 30, 23, 59, 59),
        "avt_link": "cpp",
        "created_by": SEED_TEACHER_ID,
        "total_number_student": 0,
    },
    {
        "course_id": "C01",
        "course_name": "Lập trình C",
        "term": "HK1-2024-2025",
        "start_date": datetime(2024, 9, 1, 0, 0, 0),
        "end_date": datetime(2024, 12, 30, 23, 59, 59),
        "avt_link": "c",
        "created_by": SEED_TEACHER_ID,
        "total_number_student": 0,
    },
    {
        "course_id": "PY02",
        "course_name": "Lớp kiểm thử Python",
        "term": "HK1-2024-2025",
        "start_date": datetime(2024, 9, 1, 0, 0, 0),
        "end_date": datetime(2024, 12, 30, 23, 59, 59),
        "avt_link": "python",
        "created_by": "GV001",
        "total_number_student": 0,
    },
]

# ===== LESSONS SEED (for JAVA01) =====
SEED_LESSONS = [
    {
        "lesson_number": 1,
        "lesson_name": "Biến, kiểu dữ liệu và cấu trúc rẽ nhánh",
        "course_id": "JAVA01",
        "total_number_assignment": 3,
        "total_number_student_finished": 42,
        "start_date": "2024-09-05",
        "end_date": "2024-09-11",
    },
    {
        "lesson_number": 2,
        "lesson_name": "Mảng và vòng lặp",
        "course_id": "JAVA01",
        "total_number_assignment": 3,
        "total_number_student_finished": 39,
        "start_date": "2024-09-12",
        "end_date": "2024-09-18",
    },
    {
        "lesson_number": 3,
        "lesson_name": "Chuỗi ký tự và Xử lý chuỗi (String)",
        "course_id": "JAVA01",
        "total_number_assignment": 3,
        "total_number_student_finished": 0,
        "start_date": "2024-09-19",
        "end_date": "2024-09-25",
    },
]

# ===== PROBLEMS SEED (for JAVA01, lesson 2 - Mảng và vòng lặp) =====
SEED_PROBLEMS = [
    {
        "lesson_ref": 1,  # index in SEED_LESSONS
        "title": "Tổng các phần tử trong mảng 1 chiều",
        "description": "Cho mảng số nguyên A gồm N phần tử. Viết chương trình tính tổng toàn bộ các phần tử dương chẵn nằm trong mảng.",
        "time_limit_seconds": 1,
        "start_format_code": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        // Write your code here\n    }\n}",
        "constraints": "1 <= N <= 10^5, -10^9 <= A[i] <= 10^9",
        "level": "easy",
        "hint": "Duyệt qua từng phần tử, kiểm tra điều kiện dương và chẵn",
        "complexity": "O(N)",
        "start_datetime": datetime(2024, 9, 12, 7, 0, 0),
        "end_datetime": datetime(2024, 9, 18, 23, 59, 59),
        "total_number_testcase": 12,
        "report": "ARR_01",
    },
    {
        "lesson_ref": 1,  # index in SEED_LESSONS (lesson 2)
        "title": "Đếm số phần tử xuất hiện nhiều nhất",
        "description": "Cho mảng số nguyên A gồm N phần tử. Tìm giá trị xuất hiện nhiều nhất trong mảng.",
        "time_limit_seconds": 1,
        "start_format_code": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        // Write your code here\n    }\n}",
        "constraints": "1 <= N <= 10^5, 1 <= A[i] <= 10^9",
        "level": "medium",
        "hint": "Dùng HashMap để đếm tần suất",
        "complexity": "O(N)",
        "start_datetime": datetime(2024, 9, 12, 7, 0, 0),
        "end_datetime": datetime(2024, 9, 18, 23, 59, 59),
        "total_number_testcase": 12,
        "report": "ARR_02",
    },
    {
        "lesson_ref": 1,  # index in SEED_LESSONS (lesson 2)
        "title": "Sắp xếp mảng MergeSort",
        "description": "Cho mảng số nguyên A gồm N phần tử. Sắp xếp mảng theo thứ tự không giảm dần bằng thuật toán MergeSort.",
        "time_limit_seconds": 1,
        "start_format_code": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        // Write your code here\n    }\n}",
        "constraints": "1 <= N <= 10^5, -10^9 <= A[i] <= 10^9",
        "level": "medium",
        "hint": "Chia đôi mảng, đệ quy sắp xếp từng nửa, sau đó merge lại",
        "complexity": "O(N log N)",
        "start_datetime": datetime(2024, 9, 12, 7, 0, 0),
        "end_datetime": datetime(2024, 9, 18, 23, 59, 59),
        "total_number_testcase": 12,
        "report": "ARR_03",
    },
    {
        "lesson_ref": 2,  # lesson 3 (Chuỗi ký tự)
        "title": "Đảo ngược chuỗi",
        "description": "Cho chuỗi ký tự S. Viết chương trình đảo ngược chuỗi đó.",
        "time_limit_seconds": 1,
        "start_format_code": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        // Write your code here\n    }\n}",
        "constraints": "1 <= |S| <= 10^5",
        "level": "easy",
        "hint": "Dùng StringBuilder hoặc duyệt từ cuối về đầu",
        "complexity": "O(N)",
        "start_datetime": datetime(2024, 9, 19, 7, 0, 0),
        "end_datetime": datetime(2024, 9, 25, 23, 59, 59),
        "total_number_testcase": 10,
        "report": "STR_01",
    },
]

# ===== SUBMISSIONS SEED =====
SEED_SUBMISSIONS = [
    # Submissions for problem ARR_01 (lesson 2, problem 1)
    {
        "problem_ref": 0,  # index in SEED_PROBLEMS
        "student_id": "2151129801",
        "language": "java",
        "submitted_code": "// Accepted solution\nimport java.util.*;\npublic class Main { public static void main(String[] args) { Scanner sc = new Scanner(System.in); int n = sc.nextInt(); int[] a = new int[n]; for(int i=0;i<n;i++) a[i]=sc.nextInt(); long sum=0; for(int x:a) if(x>0&&x%2==0) sum+=x; System.out.println(sum); } }",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": datetime(2024, 9, 15, 10, 20, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129802",
        "language": "java",
        "submitted_code": "// Wrong answer\nimport java.util.*;\npublic class Main { public static void main(String[] args) { Scanner sc = new Scanner(System.in); int n = sc.nextInt(); long sum=0; for(int i=0;i<n;i++){int x=sc.nextInt(); if(x%2==0) sum+=x;} System.out.println(sum); } }",
        "status": "wrong_answer",
        "passed_count": 8,
        "submitted_datetime": datetime(2024, 9, 13, 14, 45, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129803",
        "language": "java",
        "submitted_code": "// Compile error\nimport java.util.*;\npublic class Main { public static void main(String args) { System.out.println(missing_var); } }",
        "status": "compile_error",
        "compile_output": "Main.java:2: error: cannot find symbol\n  System.out.println(missing_var);",
        "passed_count": 0,
        "submitted_datetime": datetime(2024, 9, 14, 9, 0, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129804",
        "language": "java",
        "submitted_code": "// Compile error\nimport java.util.*;\npublic class Main { public static void main(String[] args) { int x = ; System.out.println(x); } }",
        "status": "compile_error",
        "compile_output": "Main.java:2: error: illegal start of expression",
        "passed_count": 0,
        "submitted_datetime": datetime(2024, 9, 14, 16, 30, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129805",
        "language": "java",
        "submitted_code": "// Similarity case\nimport java.util.*;\npublic class Main { public static void main(String[] args) { Scanner sc = new Scanner(System.in); int n = sc.nextInt(); int[] a = new int[n]; for(int i=0;i<n;i++) a[i]=sc.nextInt(); long sum=0; for(int x:a) if(x>0&&x%2==0) sum+=x; System.out.println(sum); } }",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": datetime(2024, 9, 15, 10, 25, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129806",
        "language": "java",
        "submitted_code": "// Same as above - plagiarism\nimport java.util.*;\npublic class Main { public static void main(String[] args) { Scanner sc = new Scanner(System.in); int n = sc.nextInt(); int[] a = new int[n]; for(int i=0;i<n;i++) a[i]=sc.nextInt(); long s=0; for(int x:a) if(x>0&&x%2==0) s+=x; System.out.println(s); } }",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": datetime(2024, 9, 15, 10, 28, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129807",
        "language": "java",
        "submitted_code": "// Wrong answer - late submission",
        "status": "wrong_answer",
        "passed_count": 5,
        "submitted_datetime": datetime(2024, 9, 19, 8, 0, 0),  # late
    },
    # More submissions for other students
    {
        "problem_ref": 0,
        "student_id": "2151129808",
        "language": "java",
        "submitted_code": "// Accepted",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": datetime(2024, 9, 15, 11, 0, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129809",
        "language": "java",
        "submitted_code": "// Wrong answer",
        "status": "wrong_answer",
        "passed_count": 7,
        "submitted_datetime": datetime(2024, 9, 16, 9, 30, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129810",
        "language": "java",
        "submitted_code": "// Late submission",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": datetime(2024, 9, 19, 7, 30, 0),  # late
    },
    # Submissions for problem ARR_02
    {
        "problem_ref": 1,
        "student_id": "2151129801",
        "language": "java",
        "submitted_code": "// Accepted solution for freq count",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": datetime(2024, 9, 15, 14, 0, 0),
    },
    {
        "problem_ref": 1,
        "student_id": "2151129802",
        "language": "java",
        "submitted_code": "// Accepted",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": datetime(2024, 9, 15, 14, 30, 0),
    },
    {
        "problem_ref": 1,
        "student_id": "2151129803",
        "language": "java",
        "submitted_code": "// Wrong answer",
        "status": "wrong_answer",
        "passed_count": 6,
        "submitted_datetime": datetime(2024, 9, 16, 10, 0, 0),
    },
    # Submissions for ARR_03 (MergeSort) - some missing = deadline warning
    {
        "problem_ref": 2,
        "student_id": "2151129801",
        "language": "java",
        "submitted_code": "// MergeSort accepted",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": datetime(2024, 9, 17, 15, 0, 0),
    },
    {
        "problem_ref": 2,
        "student_id": "2151129802",
        "language": "java",
        "submitted_code": "// MergeSort wrong",
        "status": "wrong_answer",
        "passed_count": 4,
        "submitted_datetime": datetime(2024, 9, 17, 16, 0, 0),
    },
]


def _upsert_user(session: Session, data: dict, hashed_password: str) -> bool:
    """Insert user nếu chưa tồn tại. Return True nếu tạo mới."""
    exists = session.exec(
        select(User).where(
            or_(User.user_id == data["user_id"], User.email == data["email"])
        )
    ).first()
    if exists:
        if data.get("class_id") and exists.class_id != data["class_id"]:
            exists.class_id = data["class_id"]
            session.add(exists)
        return False
    session.add(User(**data, hashed_password=hashed_password))
    return True


def _upsert_course(session: Session, data: dict) -> Course | None:
    """Insert course nếu chưa tồn tại. Return Course object."""
    existing = session.get(Course, data["course_id"])
    if existing:
        return existing
    course = Course(**data)
    session.add(course)
    session.flush()
    return course


def seed_users() -> None:
    logger.info("Seed users: bắt đầu (SEED_DATA=%s)", os.getenv("SEED_DATA"))

    if os.getenv("SEED_DATA", "false").lower() != "true":
        logger.info("Seed users: bỏ qua vì SEED_DATA không phải 'true'")
        return

    password = os.getenv("SEED_DEFAULT_PASSWORD", "LeetCodeForUtc2")

    with Session(engine) as session:
        for class_data in SEED_CLASSES:
            if not session.get(Class, class_data["class_id"]):
                session.add(Class(**class_data))
        session.commit()

        created_users = 0
        for data in SEED_USERS:
            if _upsert_user(session, data, hash_password(password)):
                created_users += 1
                logger.info("Seed users: tạo user %s", data["email"])
            else:
                logger.info("Seed users: %s đã tồn tại, bỏ qua", data["email"])

        session.commit()
        logger.info("Seed users: đã thêm %d user", created_users)

        # ---- Seed courses ----
        created_courses = 0
        for data in SEED_COURSES:
            existing_course = session.get(Course, data["course_id"])
            if existing_course:
                if existing_course.created_by != data["created_by"]:
                    existing_course.created_by = data["created_by"]
                    session.add(existing_course)
            else:
                session.add(Course(**data))
                created_courses += 1
        session.commit()
        logger.info("Seed courses: đã thêm %d course", created_courses)

        # ---- Seed enrollments for JAVA01 ----
        student_ids = [
            u["user_id"]
            for u in SEED_USERS
            if (
                u.get("role_id") == 3
                and u.get("user_id", "").startswith("215")
                and u.get("user_id") != "2151129901"
            )
        ]
        java_course = session.get(Course, "JAVA01")
        if java_course:
            enrolled_count = 0
            for sid in student_ids:
                existing = session.exec(
                    select(Enrollment).where(
                        Enrollment.course_id == "JAVA01",
                        Enrollment.student_id == sid,
                    )
                ).first()
                if not existing:
                    session.add(Enrollment(course_id="JAVA01", student_id=sid))
                    enrolled_count += 1
            test_enrollment = session.exec(
                select(Enrollment).where(
                    Enrollment.course_id == "JAVA01",
                    Enrollment.student_id == "2151129901",
                )
            ).first()
            if test_enrollment:
                session.delete(test_enrollment)
            java_course.total_number_student = len(
                session.exec(select(Enrollment).where(Enrollment.course_id == "JAVA01")).all()
            )
            session.add(java_course)
            session.commit()
            logger.info("Seed enrollments: đã thêm %d enrollment cho JAVA01", enrolled_count)

        # ---- Seed lessons & problems for JAVA01 ----
        from datetime import date

        lesson_ids = []
        for ldata in SEED_LESSONS:
            existing = session.exec(
                select(Lesson).where(
                    Lesson.course_id == ldata["course_id"],
                    Lesson.lesson_number == ldata["lesson_number"],
                )
            ).first()
            if existing:
                lesson_ids.append(existing.lesson_id)
                logger.info("Seed lessons: lesson %d đã tồn tại", ldata["lesson_number"])
            else:
                lesson = Lesson(
                    lesson_number=ldata["lesson_number"],
                    lesson_name=ldata["lesson_name"],
                    course_id=ldata["course_id"],
                    total_number_assignment=ldata["total_number_assignment"],
                    total_number_student_finished=ldata["total_number_student_finished"],
                    start_date=date.fromisoformat(ldata["start_date"]),
                    end_date=date.fromisoformat(ldata["end_date"]),
                )
                session.add(lesson)
                session.flush()
                lesson_ids.append(lesson.lesson_id)
        session.commit()
        logger.info("Seed lessons: xong, lesson_ids=%s", lesson_ids)

        # ---- Seed problems ----
        problem_ids = []
        for pdata in SEED_PROBLEMS:
            lesson_idx = pdata["lesson_ref"]
            lesson_id = lesson_ids[lesson_idx] if lesson_idx < len(lesson_ids) else None
            if lesson_id is None:
                logger.warning("Seed problems: không tìm thấy lesson_id cho problem %s", pdata["title"])
                problem_ids.append(None)
                continue
            existing = session.exec(
                select(Problem).where(
                    Problem.lesson_id == lesson_id,
                    Problem.title == pdata["title"],
                )
            ).first()
            if existing:
                problem_ids.append(existing.problem_id)
            else:
                problem = Problem(
                    lesson_id=lesson_id,
                    title=pdata["title"],
                    description=pdata["description"],
                    time_limit_seconds=pdata["time_limit_seconds"],
                    start_format_code=pdata["start_format_code"],
                    constraints=pdata["constraints"],
                    level=pdata["level"],
                    hint=pdata.get("hint"),
                    complexity=pdata.get("complexity"),
                    start_datetime=pdata["start_datetime"],
                    end_datetime=pdata["end_datetime"],
                    total_number_testcase=pdata["total_number_testcase"],
                    report=pdata.get("report"),
                )
                session.add(problem)
                session.flush()
                problem_ids.append(problem.problem_id)
                # Add testcases
                for tc_idx in range(pdata["total_number_testcase"]):
                    session.add(Testcase(
                        problem_id=problem.problem_id,
                        input=f"5\n{'1 2 3 4 5' if tc_idx < 5 else '10 20 30 40 50 60'}",
                        expected_output=f"{6 if tc_idx < 5 else 60}",
                        is_sample=(tc_idx < 2),
                        input_type="array",
                        expected_output_type="int",
                    ))
        session.commit()
        logger.info("Seed problems: xong, problem_ids=%s", problem_ids)

        # ---- Seed submissions ----
        created_subs = 0
        for sdata in SEED_SUBMISSIONS:
            prob_idx = sdata["problem_ref"]
            problem_id = problem_ids[prob_idx] if prob_idx < len(problem_ids) else None
            if problem_id is None:
                continue
            existing = session.exec(
                select(Submission).where(
                    Submission.problem_id == problem_id,
                    Submission.student_id == sdata["student_id"],
                )
            ).first()
            if not existing:
                session.add(Submission(
                    problem_id=problem_id,
                    student_id=sdata["student_id"],
                    language=sdata["language"],
                    submitted_code=sdata["submitted_code"],
                    status=sdata["status"],
                    compile_output=sdata.get("compile_output"),
                    feedback=sdata.get("feedback"),
                    passed_count=sdata["passed_count"],
                    submitted_datetime=sdata["submitted_datetime"],
                ))
                created_subs += 1
        session.commit()
        logger.info("Seed submissions: đã thêm %d submission", created_subs)
