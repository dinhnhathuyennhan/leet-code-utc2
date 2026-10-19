from datetime import date, datetime

from sqlalchemy import JSON, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.core.utils.datetime_utils import UTCDateTime


# ==================== CLASS ====================
class Class(SQLModel, table=True):
    class_id: str = Field(primary_key=True, max_length=50)
    type: str
    course_number: int
    department: str

    students: list["User"] = Relationship(back_populates="class_")


# ==================== USER ====================
class User(SQLModel, table=True):
    user_id: str = Field(primary_key=True, max_length=50)
    full_name: str
    avt_link: str | None = Field(default=None, max_length=2048)
    date_of_birth: date | None = None
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    must_change_password: bool = Field(default=False)
    role_id: int  # 1: admin, 2: teacher, 3: student (tùy quy ước của bạn)
    token_version: int = Field(default=0)
    class_id: str | None = Field(
        default=None, foreign_key="class.class_id", max_length=50
    )

    class_: Class | None = Relationship(back_populates="students")
    # Quan hệ: 1 giáo viên "create" nhiều course
    created_courses: list["Course"] = Relationship(back_populates="creator")
    # Quan hệ: 1 sinh viên "participate" nhiều enrollment
    enrollments: list["Enrollment"] = Relationship(back_populates="student")
    # Quan hệ: 1 sinh viên "submit" nhiều submission
    submissions: list["Submission"] = Relationship(back_populates="student")


# ==================== COURSE ====================
class Course(SQLModel, table=True):
    course_id: str = Field(primary_key=True, max_length=50)
    course_name: str
    avt_link: str | None = Field(default=None, max_length=2048)
    created_by: str = Field(foreign_key="user.user_id", max_length=50)
    term: str
    start_date: datetime = Field(sa_type=UTCDateTime)
    end_date: datetime = Field(sa_type=UTCDateTime)
    total_number_student: int = Field(default=0)

    creator: User | None = Relationship(back_populates="created_courses")
    enrollments: list["Enrollment"] = Relationship(back_populates="course")
    lessons: list["Lesson"] = Relationship(back_populates="course")


# ==================== ENROLLMENT ====================
class Enrollment(SQLModel, table=True):
    # unique(course_id, student_id) => không thể thêm cùng một sinh viên vào cùng một khóa học
    # lớp ràng buộc cuối cùng tại db
    __table_args__ = (
        UniqueConstraint(
            "course_id", "student_id", name="uq_enrollment_course_student"
        ),
    )
    enrollment_id: int | None = Field(default=None, primary_key=True)
    course_id: str = Field(foreign_key="course.course_id", max_length=50)
    student_id: str = Field(foreign_key="user.user_id", max_length=50)

    course: Course | None = Relationship(back_populates="enrollments")
    student: User | None = Relationship(back_populates="enrollments")


# ==================== LESSON ====================
class Lesson(SQLModel, table=True):
    lesson_id: int | None = Field(default=None, primary_key=True)
    lesson_number: int
    lesson_name: str
    course_id: str = Field(foreign_key="course.course_id", max_length=50)
    total_number_assignment: int = Field(default=0)
    total_number_student_finished: int = Field(default=0)
    start_date: date
    end_date: date

    course: Course | None = Relationship(back_populates="lessons")
    problems: list["Problem"] = Relationship(back_populates="lesson")


# ==================== PROBLEM ====================
class Problem(SQLModel, table=True):
    problem_id: int | None = Field(default=None, primary_key=True)
    # NULL = bài nằm trong ngân hàng đề, chưa gắn buổi học nào
    lesson_id: int | None = Field(default=None, foreign_key="lesson.lesson_id")
    title: str = Field(max_length=255)
    # Method runner sẽ gọi; NULL chỉ dành cho Problem cũ chưa chuyển từ stdin/stdout.
    function_name: str | None = Field(default=None, max_length=100)
    description: str
    time_limit_seconds: int
    start_format_code: str  # template Python cũ, giữ để tương thích API/dữ liệu legacy
    # Mẫu code theo ngôn ngữ, ví dụ {"python": "...", "java": "..."}.
    starter_codes: dict[str, str] = Field(default_factory=dict, sa_type=JSON)
    constraints: str
    level: str
    hint: str | None = None
    complexity: str | None = None
    start_datetime: datetime = Field(sa_type=UTCDateTime)
    end_datetime: datetime = Field(sa_type=UTCDateTime)
    total_number_testcase: int = Field(default=0)
    report: str | None = Field(default=None, max_length=255)

    lesson: Lesson | None = Relationship(back_populates="problems")
    testcases: list["Testcase"] = Relationship(back_populates="problem")
    submissions: list["Submission"] = Relationship(back_populates="problem")


# ==================== TESTCASE ====================
class Testcase(SQLModel, table=True):
    testcase_id: int | None = Field(default=None, primary_key=True)
    problem_id: int = Field(foreign_key="problem.problem_id")
    input: str
    expected_output: str
    is_sample: bool = Field(default=False)
    input_type: str
    expected_output_type: str

    problem: Problem | None = Relationship(back_populates="testcases")


# ==================== SUBMISSION ====================
class Submission(SQLModel, table=True):
    submission_id: int | None = Field(default=None, primary_key=True)
    problem_id: int = Field(foreign_key="problem.problem_id")
    # varchar để khớp kiểu với user.user_id
    student_id: str = Field(foreign_key="user.user_id", max_length=50)
    language: str
    submitted_code: str
    status: str  # pending / accepted / wrong_answer / compile_error...
    compile_output: str | None = None
    feedback: str | None = None
    passed_count: int = Field(default=0)
    submitted_datetime: datetime = Field(sa_type=UTCDateTime)

    problem: Problem | None = Relationship(back_populates="submissions")
    student: User | None = Relationship(back_populates="submissions")
