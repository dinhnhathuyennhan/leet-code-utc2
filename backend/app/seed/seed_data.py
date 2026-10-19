
import logging
import os
from datetime import date, datetime

from sqlmodel import Session, func, or_, select

from app.core.utils.datetime_utils import VN_TZ, vn_day_end, vn_day_start
from app.core.security.passwords import hash_password
from app.core.database import engine

from app.core.dependencies import Role
from app.modules.classrooms.schemas import build_class_id
from app.models import (
    Class,
    Course,
    Enrollment,
    Lesson,
    Problem,
    Submission,
    Testcase,
    User,
)

logger = logging.getLogger("uvicorn.error")
SEED_TEACHER_ID = "6451071003"

# ---- Giá trị tự quy ước (models.py không ràng buộc), sửa tại đây nếu cần ----
IO_TYPE = "string"
STARTER_CODE = "def solve():\n    # TODO: viết lời giải\n    pass\n\n\nsolve()\n"
DEFAULT_CONSTRAINTS = "Đọc dữ liệu từ stdin, in kết quả ra stdout."

# ---- Convention của dự án ----
EMAIL_DOMAIN = "st.utc2.edu.vn"
CLASS_TYPE = "CQ"
MAJOR_ABBR = "CNTT"


def class_id_of(course_number: int) -> str:
    return build_class_id(CLASS_TYPE, course_number, MAJOR_ABBR)


def vn_datetime(*args: int) -> datetime:
    """Mốc thời gian trong dữ liệu seed được viết theo giờ VN."""
    return datetime(*args, tzinfo=VN_TZ)


# ---- Dữ liệu ----
CLASS_COURSE_NUMBERS = [62, 63, 64, 65, 66]

# (alias, user_id, full_name, date_of_birth, email_name)
STAFF = [
    ("AD01", "1111111111", "Quản Trị Viên", date(1980, 1, 1), "QuanTri", Role.ADMIN),
    ("GV01", "1111111112", "Nguyễn Văn An", date(1985, 3, 12), "NguyenVanAn", Role.TEACHER),
    ("GV02", "1111111113", "Trần Thị Bình", date(1988, 7, 25), "TranThiBinh", Role.TEACHER),
    ("GV03", "1111111114", "Lê Hoàng Cường", date(1990, 11, 2), "LeHoangCuong", Role.TEACHER),
    ("GV04", "1111111115", "Phạm Minh Dũng", date(1982, 1, 30), "PhamMinhDung", Role.TEACHER),
    ("GV05", "1111111116", "Võ Thị Em", date(1992, 9, 18), "VoThiEm", Role.TEACHER),
]

# (alias, MSSV, full_name, date_of_birth, course_number) — email = <MSSV>@st.utc2.edu.vn
STUDENTS = [
    ("SV01", "6251071001", "Đặng Quốc Huy", date(2005, 5, 15), 62),
    ("SV02", "6251071002", "Bùi Thanh Hà", date(2005, 8, 20), 62),
    ("SV03", "6351071001", "Ngô Minh Khang", date(2004, 12, 3), 63),
    ("SV04", "6351071002", "Hoàng Gia Linh", date(2005, 2, 14), 63),
    ("SV05", "6451071001", "Phan Đức Mạnh", date(2006, 1, 9), 64),
    ("SV06", "6451071002", "Trương Ngọc Nhi", date(2005, 6, 30), 64),
    ("SV07", "6551071001", "Lý Anh Phúc", date(2004, 10, 11), 65),
    ("SV08", "6551071002", "Đỗ Khánh Quyên", date(2005, 3, 27), 65),
    ("SV09", "6651071001", "Vũ Thành Sơn", date(2005, 9, 5), 66),
    ("SV10", "6651071002", "Mai Bảo Trân", date(2006, 4, 22), 66),
]

# alias -> user_id thật
UID = {row[0]: row[1] for row in STAFF + STUDENTS}

# GV04, GV05 không tạo course; SV09, SV10 không học course nào
# (để test case Teacher bị 403 khi reset mật khẩu / xem lớp)
# (course_id, course_name, term, start, end, created_by)
COURSES = [
    ("CS101-2026A", "Lập trình cơ bản", "HK1 2026-2027",
     vn_datetime(2026, 9, 7), vn_datetime(2026, 12, 27), "GV01"),
    ("CS102-2026A", "Cấu trúc dữ liệu", "HK1 2026-2027",
     vn_datetime(2026, 9, 7), vn_datetime(2026, 12, 27), "GV01"),
    ("CS201-2026A", "Giải thuật", "HK1 2026-2027",
     vn_datetime(2026, 9, 7), vn_datetime(2026, 12, 27), "GV02"),
    ("CS202-2026A", "Lập trình hướng đối tượng", "HK1 2026-2027",
     vn_datetime(2026, 9, 14), vn_datetime(2027, 1, 10), "GV02"),
    ("CS301-2026A", "Cơ sở dữ liệu", "HK1 2026-2027",
     vn_datetime(2026, 9, 14), vn_datetime(2027, 1, 10), "GV03"),
]

ENROLLMENTS = {
    "CS101-2026A": ["SV01", "SV02", "SV03", "SV04"],
    "CS102-2026A": ["SV01", "SV02", "SV05"],
    "CS201-2026A": ["SV03", "SV04", "SV05", "SV06"],
    "CS202-2026A": ["SV06", "SV07"],
    "CS301-2026A": ["SV01", "SV07", "SV08"],
}

LESSON_DATES = {
    1: (date(2026, 9, 7), date(2026, 9, 27)),
    2: (date(2026, 9, 28), date(2026, 10, 18)),
}
LESSON_NAMES = {
    "CS101-2026A": ["Nhập môn và biến", "Rẽ nhánh"],
    "CS102-2026A": ["Chuỗi ký tự", "Ngăn xếp"],
    "CS201-2026A": ["Đệ quy", "Tìm kiếm"],
    "CS202-2026A": ["Chuỗi và ký tự", "Hàm và đệ quy"],
    "CS301-2026A": ["Thống kê mảng", "Số học"],
}

# (course_id, lesson_number, title, description, level, time_limit_s, hint, complexity, tests)
PROBLEMS = [
    ("CS101-2026A", 1, "Tổng hai số", "Cho hai số nguyên a, b trên cùng một dòng. In ra tổng a + b.",
     "easy", 1, "Dùng input().split()", "O(1)",
     [("1 2", "3"), ("-5 5", "0"), ("100 250", "350")]),
    ("CS101-2026A", 2, "Chẵn hay lẻ", "Cho số nguyên n. In 'even' nếu n chẵn, ngược lại in 'odd'.",
     "easy", 1, "Dùng toán tử %", "O(1)",
     [("4", "even"), ("7", "odd"), ("0", "even")]),
    ("CS102-2026A", 1, "Đảo ngược chuỗi", "Cho một chuỗi s. In ra chuỗi đảo ngược của s.",
     "easy", 1, "Dùng slicing s[::-1]", "O(n)",
     [("hello", "olleh"), ("abc", "cba"), ("a", "a")]),
    ("CS102-2026A", 2, "Dấu ngoặc hợp lệ",
     "Cho chuỗi chỉ gồm ()[]{}. In 'true' nếu các dấu ngoặc khớp đúng, ngược lại in 'false'.",
     "medium", 1, "Dùng stack", "O(n)",
     [("()[]{}", "true"), ("(]", "false"), ("{[]}", "true")]),
    ("CS201-2026A", 1, "Fibonacci thứ n", "Cho n (0 ≤ n ≤ 30). In ra số Fibonacci thứ n với F(0)=0, F(1)=1.",
     "easy", 1, "Thử đệ quy có nhớ hoặc vòng lặp", "O(n)",
     [("0", "0"), ("10", "55"), ("20", "6765")]),
    ("CS201-2026A", 2, "Tìm kiếm nhị phân",
     "Dòng 1: n. Dòng 2: n số nguyên tăng dần. Dòng 3: giá trị x. In chỉ số của x, hoặc -1 nếu không có.",
     "medium", 1, "Chia đôi khoảng tìm kiếm", "O(log n)",
     [("5\n1 3 5 7 9\n7", "3"), ("5\n1 3 5 7 9\n4", "-1"), ("3\n2 4 6\n2", "0")]),
    ("CS202-2026A", 1, "Đếm nguyên âm", "Cho chuỗi s. In ra số nguyên âm (a, e, i, o, u, không phân biệt hoa thường).",
     "easy", 1, "Chuyển về chữ thường trước khi đếm", "O(n)",
     [("hello", "2"), ("xyz", "0"), ("Education", "5")]),
    ("CS202-2026A", 2, "Giai thừa", "Cho n (0 ≤ n ≤ 12). In ra n!.",
     "easy", 1, "0! = 1", "O(n)",
     [("5", "120"), ("0", "1"), ("10", "3628800")]),
    ("CS301-2026A", 1, "Số lớn nhất trong mảng",
     "Dòng 1: n. Dòng 2: n số nguyên. In ra giá trị lớn nhất.",
     "easy", 1, "Duyệt một lần, giữ giá trị lớn nhất", "O(n)",
     [("5\n3 9 2 7 1", "9"), ("3\n-4 -2 -8", "-2"), ("1\n42", "42")]),
    ("CS301-2026A", 2, "Kiểm tra số nguyên tố", "Cho n. In 'true' nếu n là số nguyên tố, ngược lại in 'false'.",
     "medium", 1, "Chỉ cần thử ước đến căn bậc hai của n", "O(√n)",
     [("7", "true"), ("1", "false"), ("15", "false")]),
]

# (course_id, lesson_number, student_alias, language, status, passed_count,
#  submitted_datetime, compile_output, feedback)
SUBMISSIONS = [
    ("CS101-2026A", 1, "SV01", "python", "accepted", 3, vn_datetime(2026, 9, 10, 9, 15), None, "Đạt 3/3 testcase"),
    ("CS101-2026A", 1, "SV02", "python", "wrong_answer", 2, vn_datetime(2026, 9, 11, 20, 30), None, "Sai ở testcase số âm"),
    ("CS101-2026A", 1, "SV02", "python", "accepted", 3, vn_datetime(2026, 9, 11, 20, 45), None, "Đạt 3/3 testcase"),
    ("CS101-2026A", 1, "SV03", "java", "compile_error", 0, vn_datetime(2026, 9, 12, 14, 0),
     "Main.java:3: error: ';' expected", None),
    ("CS101-2026A", 2, "SV01", "python", "accepted", 3, vn_datetime(2026, 10, 1, 10, 0), None, "Đạt 3/3 testcase"),
    ("CS102-2026A", 1, "SV01", "cpp", "accepted", 3, vn_datetime(2026, 9, 15, 8, 40), None, "Đạt 3/3 testcase"),
    ("CS102-2026A", 1, "SV05", "python", "wrong_answer", 1, vn_datetime(2026, 9, 16, 19, 5), None, "Sai với chuỗi 1 ký tự"),
    ("CS201-2026A", 1, "SV03", "python", "accepted", 3, vn_datetime(2026, 9, 14, 21, 0), None, "Đạt 3/3 testcase"),
    ("CS201-2026A", 1, "SV04", "python", "pending", 0, vn_datetime(2026, 9, 20, 22, 10), None, None),
    ("CS201-2026A", 2, "SV05", "java", "wrong_answer", 2, vn_datetime(2026, 10, 2, 15, 30), None, "Sai khi không tìm thấy phần tử"),
    ("CS202-2026A", 1, "SV06", "python", "accepted", 3, vn_datetime(2026, 9, 22, 9, 0), None, "Đạt 3/3 testcase"),
    ("CS301-2026A", 1, "SV07", "python", "accepted", 3, vn_datetime(2026, 9, 18, 13, 20), None, "Đạt 3/3 testcase"),
    ("CS301-2026A", 1, "SV08", "cpp", "wrong_answer", 0, vn_datetime(2026, 9, 19, 16, 45), None, "Chưa xử lý số âm"),
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
        "start_datetime": vn_datetime(2024, 9, 12, 7, 0, 0),
        "end_datetime": vn_datetime(2024, 9, 18, 23, 59, 59),
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
        "start_datetime": vn_datetime(2024, 9, 12, 7, 0, 0),
        "end_datetime": vn_datetime(2024, 9, 18, 23, 59, 59),
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
        "start_datetime": vn_datetime(2024, 9, 12, 7, 0, 0),
        "end_datetime": vn_datetime(2024, 9, 18, 23, 59, 59),
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
        "start_datetime": vn_datetime(2024, 9, 19, 7, 0, 0),
        "end_datetime": vn_datetime(2024, 9, 25, 23, 59, 59),
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
        "submitted_datetime": vn_datetime(2024, 9, 15, 10, 20, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129802",
        "language": "java",
        "submitted_code": "// Wrong answer\nimport java.util.*;\npublic class Main { public static void main(String[] args) { Scanner sc = new Scanner(System.in); int n = sc.nextInt(); long sum=0; for(int i=0;i<n;i++){int x=sc.nextInt(); if(x%2==0) sum+=x;} System.out.println(sum); } }",
        "status": "wrong_answer",
        "passed_count": 8,
        "submitted_datetime": vn_datetime(2024, 9, 13, 14, 45, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129803",
        "language": "java",
        "submitted_code": "// Compile error\nimport java.util.*;\npublic class Main { public static void main(String args) { System.out.println(missing_var); } }",
        "status": "compile_error",
        "compile_output": "Main.java:2: error: cannot find symbol\n  System.out.println(missing_var);",
        "passed_count": 0,
        "submitted_datetime": vn_datetime(2024, 9, 14, 9, 0, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129804",
        "language": "java",
        "submitted_code": "// Compile error\nimport java.util.*;\npublic class Main { public static void main(String[] args) { int x = ; System.out.println(x); } }",
        "status": "compile_error",
        "compile_output": "Main.java:2: error: illegal start of expression",
        "passed_count": 0,
        "submitted_datetime": vn_datetime(2024, 9, 14, 16, 30, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129805",
        "language": "java",
        "submitted_code": "// Similarity case\nimport java.util.*;\npublic class Main { public static void main(String[] args) { Scanner sc = new Scanner(System.in); int n = sc.nextInt(); int[] a = new int[n]; for(int i=0;i<n;i++) a[i]=sc.nextInt(); long sum=0; for(int x:a) if(x>0&&x%2==0) sum+=x; System.out.println(sum); } }",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": vn_datetime(2024, 9, 15, 10, 25, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129806",
        "language": "java",
        "submitted_code": "// Same as above - plagiarism\nimport java.util.*;\npublic class Main { public static void main(String[] args) { Scanner sc = new Scanner(System.in); int n = sc.nextInt(); int[] a = new int[n]; for(int i=0;i<n;i++) a[i]=sc.nextInt(); long s=0; for(int x:a) if(x>0&&x%2==0) s+=x; System.out.println(s); } }",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": vn_datetime(2024, 9, 15, 10, 28, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129807",
        "language": "java",
        "submitted_code": "// Wrong answer - late submission",
        "status": "wrong_answer",
        "passed_count": 5,
        "submitted_datetime": vn_datetime(2024, 9, 19, 8, 0, 0),  # late
    },
    # More submissions for other students
    {
        "problem_ref": 0,
        "student_id": "2151129808",
        "language": "java",
        "submitted_code": "// Accepted",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": vn_datetime(2024, 9, 15, 11, 0, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129809",
        "language": "java",
        "submitted_code": "// Wrong answer",
        "status": "wrong_answer",
        "passed_count": 7,
        "submitted_datetime": vn_datetime(2024, 9, 16, 9, 30, 0),
    },
    {
        "problem_ref": 0,
        "student_id": "2151129810",
        "language": "java",
        "submitted_code": "// Late submission",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": vn_datetime(2024, 9, 19, 7, 30, 0),  # late
    },
    # Submissions for problem ARR_02
    {
        "problem_ref": 1,
        "student_id": "2151129801",
        "language": "java",
        "submitted_code": "// Accepted solution for freq count",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": vn_datetime(2024, 9, 15, 14, 0, 0),
    },
    {
        "problem_ref": 1,
        "student_id": "2151129802",
        "language": "java",
        "submitted_code": "// Accepted",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": vn_datetime(2024, 9, 15, 14, 30, 0),
    },
    {
        "problem_ref": 1,
        "student_id": "2151129803",
        "language": "java",
        "submitted_code": "// Wrong answer",
        "status": "wrong_answer",
        "passed_count": 6,
        "submitted_datetime": vn_datetime(2024, 9, 16, 10, 0, 0),
    },
    # Submissions for ARR_03 (MergeSort) - some missing = deadline warning
    {
        "problem_ref": 2,
        "student_id": "2151129801",
        "language": "java",
        "submitted_code": "// MergeSort accepted",
        "status": "accepted",
        "passed_count": 12,
        "submitted_datetime": vn_datetime(2024, 9, 17, 15, 0, 0),
    },
    {
        "problem_ref": 2,
        "student_id": "2151129802",
        "language": "java",
        "submitted_code": "// MergeSort wrong",
        "status": "wrong_answer",
        "passed_count": 4,
        "submitted_datetime": vn_datetime(2024, 9, 17, 16, 0, 0),
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


class SeedStepError(Exception):
    """Một bước seed thất bại."""

def _report(kind: str, created: list[str], total: int) -> None:
    for item in created:
        logger.info("Seed %s: đã tạo %s", kind, item)
    logger.info(
        "Seed %s: thêm mới %d, bỏ qua (đã tồn tại) %d",
        kind,
        len(created),
        total - len(created),
    )


# ---- Từng bước (mỗi bước dùng 1 session riêng, idempotent) ----
def _seed_classes(session: Session) -> None:
    created: list[str] = []
    for course_number in CLASS_COURSE_NUMBERS:
        class_id = class_id_of(course_number)
        if session.get(Class, class_id) is None:
            session.add(
                Class(
                    class_id=class_id,
                    type=CLASS_TYPE,
                    course_number=course_number,
                    department=MAJOR_ABBR,
                )
            )
            created.append(class_id)
    session.commit()
    _report("class", created, len(CLASS_COURSE_NUMBERS))


def _user_rows() -> list[dict]:
    rows = [
        {
            "user_id": user_id,
            "full_name": name,
            "email": f"{email_name}@{EMAIL_DOMAIN}",
            "date_of_birth": dob,
            "role_id": role_id,
            "must_change_password": True,
        }
        for _, user_id, name, dob, email_name, role_id in STAFF
    ]
    rows += [
        {
            "user_id": mssv,
            "full_name": name,
            "email": f"{mssv}@{EMAIL_DOMAIN}",
            "date_of_birth": dob,
            "role_id": Role.STUDENT,
            "class_id": class_id_of(course_number),
            "must_change_password": True,
        }
        for _, mssv, name, dob, course_number in STUDENTS
    ]
    return rows


def _seed_users(session: Session, password: str) -> None:
    rows = _user_rows()
    hashed_password = hash_password(password)  # cùng mật khẩu nên băm 1 lần
    created: list[str] = []
    for data in rows:
        exists = session.exec(
            select(User).where(
                or_(User.user_id == data["user_id"], User.email == data["email"])
            )
        ).first()
        if exists:
            continue
        session.add(User(**data, hashed_password=hashed_password))
        created.append(f"{data['user_id']} ({data['email']})")
    session.commit()
    _report("user", created, len(rows))


def _seed_courses_and_enrollments(session: Session) -> None:
    created_courses: list[str] = []
    for course_id, name, term, start, end, created_by in COURSES:
        if session.get(Course, course_id) is None:
            session.add(
                Course(
                    course_id=course_id,
                    course_name=name,
                    term=term,
                    start_date=start,
                    end_date=end,
                    created_by=UID[created_by],
                )
            )
            created_courses.append(f"{course_id} (GV {UID[created_by]})")
    session.commit()
    _report("course", created_courses, len(COURSES))

    created_enrollments: list[str] = []
    total = 0
    for course_id, aliases in ENROLLMENTS.items():
        for alias in aliases:
            total += 1
            student_id = UID[alias]
            exists = session.exec(
                select(Enrollment).where(
                    Enrollment.course_id == course_id,
                    Enrollment.student_id == student_id,
                )
            ).first()
            if exists is None:
                session.add(Enrollment(course_id=course_id, student_id=student_id))
                created_enrollments.append(f"{student_id} -> {course_id}")
    session.commit()
    _report("enrollment", created_enrollments, total)


def _seed_lessons_problems_testcases(session: Session) -> None:
    created_lessons: list[str] = []
    created_problems: list[str] = []
    created_tests: list[str] = []
    lessons_seen: set[tuple[str, int]] = set()
    tests_total = 0

    for course_id, number, title, description, level, time_limit, hint, complexity, tests in PROBLEMS:
        lessons_seen.add((course_id, number))
        lesson = session.exec(
            select(Lesson).where(
                Lesson.course_id == course_id, Lesson.lesson_number == number
            )
        ).first()
        if lesson is None:
            start, end = LESSON_DATES[number]
            lesson = Lesson(
                lesson_number=number,
                lesson_name=LESSON_NAMES[course_id][number - 1],
                course_id=course_id,
                start_date=start,
                end_date=end,
            )
            session.add(lesson)
            session.commit()
            session.refresh(lesson)
            created_lessons.append(f"{course_id} / bài {number}")

        problem = session.exec(
            select(Problem).where(
                Problem.lesson_id == lesson.lesson_id, Problem.title == title
            )
        ).first()
        if problem is None:
            problem = Problem(
                lesson_id=lesson.lesson_id,
                title=title,
                description=description,
                time_limit_seconds=time_limit,
                start_format_code=STARTER_CODE,
                constraints=DEFAULT_CONSTRAINTS,
                level=level,
                hint=hint,
                complexity=complexity,
                start_datetime=vn_day_start(lesson.start_date),
                end_datetime=vn_day_end(lesson.end_date),
            )
            session.add(problem)
            session.commit()
            session.refresh(problem)
            created_problems.append(f"{course_id} / bài {number}: {title}")

        for index, (test_input, expected) in enumerate(tests):
            tests_total += 1
            exists = session.exec(
                select(Testcase).where(
                    Testcase.problem_id == problem.problem_id,
                    Testcase.input == test_input,
                )
            ).first()
            if exists is None:
                session.add(
                    Testcase(
                        problem_id=problem.problem_id,
                        input=test_input,
                        expected_output=expected,
                        is_sample=index < 2,  # 2 testcase đầu là sample, còn lại ẩn
                        input_type=IO_TYPE,
                        expected_output_type=IO_TYPE,
                    )
                )
                created_tests.append(f"{title} #{index + 1}")
    session.commit()

    _report("lesson", created_lessons, len(lessons_seen))
    _report("problem", created_problems, len(PROBLEMS))
    _report("testcase", created_tests, tests_total)


def _seed_submissions(session: Session) -> None:
    created: list[str] = []
    for course_id, number, alias, language, status, passed, submitted, compile_out, feedback in SUBMISSIONS:
        problem = session.exec(
            select(Problem)
            .join(Lesson, Lesson.lesson_id == Problem.lesson_id)
            .where(Lesson.course_id == course_id, Lesson.lesson_number == number)
        ).first()
        if problem is None:
            raise SeedStepError(f"Không tìm thấy problem của {course_id} / bài {number}")
        student_id = UID[alias]
        exists = session.exec(
            select(Submission).where(
                Submission.problem_id == problem.problem_id,
                Submission.student_id == student_id,
                Submission.submitted_datetime == submitted,
            )
        ).first()
        if exists is None:
            session.add(
                Submission(
                    problem_id=problem.problem_id,
                    student_id=student_id,
                    language=language,
                    submitted_code=STARTER_CODE,
                    status=status,
                    compile_output=compile_out,
                    feedback=feedback,
                    passed_count=passed,
                    submitted_datetime=submitted,
                )
            )
            created.append(f"{student_id} -> {course_id} / bài {number} [{status}]")
    session.commit()
    _report("submission", created, len(SUBMISSIONS))


def _refresh_counters(session: Session) -> None:
    """Tính lại các cột đếm từ dữ liệu thật để luôn khớp với bảng liên quan."""
    course_ids = [c[0] for c in COURSES]
    for course in session.exec(select(Course).where(Course.course_id.in_(course_ids))).all():
        course.total_number_student = session.exec(
            select(func.count()).select_from(Enrollment).where(Enrollment.course_id == course.course_id)
        ).one()

    for lesson in session.exec(select(Lesson).where(Lesson.course_id.in_(course_ids))).all():
        problems = session.exec(select(Problem).where(Problem.lesson_id == lesson.lesson_id)).all()
        lesson.total_number_assignment = len(problems)

        # Student hoàn thành lesson = có submission accepted cho TẤT CẢ problem của lesson
        finished: set[str] | None = None
        for problem in problems:
            problem.total_number_testcase = session.exec(
                select(func.count()).select_from(Testcase).where(Testcase.problem_id == problem.problem_id)
            ).one()
            solved = set(
                session.exec(
                    select(Submission.student_id).where(
                        Submission.problem_id == problem.problem_id,
                        Submission.status == "accepted",
                    )
                ).all()
            )
            finished = solved if finished is None else finished & solved
        lesson.total_number_student_finished = len(finished or ())
    session.commit()
    logger.info("Seed counter: đã cập nhật các cột total_number_* theo dữ liệu thật")


def _run_step(name: str, func_, *args) -> bool:
    with Session(engine) as session:
        try:
            func_(session, *args)
        except Exception:
            session.rollback()
            logger.exception("Seed %s: THẤT BẠI, đã rollback phần chưa commit", name)
            return False
    return True


def seed_data() -> None:
    flag = os.getenv("SEED_DATA")
    logger.info("Seed data: bắt đầu (SEED_DATA=%s)", flag)

    if (flag or "false").lower() != "true":
        logger.info("Seed data: KHÔNG CHẠY vì SEED_DATA không phải 'true'")
        return

    password = os.getenv("SEED_DEFAULT_PASSWORD")
    if password:
        logger.info("Seed data: dùng SEED_DEFAULT_PASSWORD từ môi trường")
    else:
        # trên prod thiếu password_default không seed data
        logger.warning(
            "Seed data: SEED_DEFAULT_PASSWORD chưa set, dùng mật khẩu mặc định trong code "
            "(chỉ nên dùng khi dev)"
        )
        return

    steps = (
        ("class", _seed_classes, ()),
        ("user", _seed_users, (password,)),
        ("course + enrollment", _seed_courses_and_enrollments, ()),
        ("lesson + problem + testcase", _seed_lessons_problems_testcases, ()),
        ("submission", _seed_submissions, ()),
        ("counter", _refresh_counters, ()),
    )
    for name, func_, args in steps:
        if not _run_step(name, func_, *args):
            logger.error("Seed data: DỪNG ở bước '%s', các bước sau bị bỏ qua", name)
            return

    logger.info("Seed data: hoàn tất")
