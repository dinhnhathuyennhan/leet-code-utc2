# ruff: noqa: F401
# Re-export TẠM để các import cũ `from app.schemas.course import ...` vẫn chạy.
# Xoá dòng noqa này và khối re-export ở Bước 6, sau khi đã đổi import ở routers/ và services/.
from datetime import date, datetime
from app.core.datetime_utils import as_utc

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.exceptions import EmptyFieldError, InvalidFormatError
from app.schemas.class_ import ClassResponse, ClassStudentResponse
from app.schemas.enrollment import (
    AddClassToCourseRequest,
    AddClassToCourseResponse,
    AddStudentToCourseRequest,
    AddStudentToCourseResponse,
    GetStudentListResponse,
)

# ----- hằng số giới hạn độ dài (khớp với column max_length trong models.py) -----
COURSE_ID_MAX_LEN = 50
AVT_LINK_MAX_LEN = 2048
SHORT_STR_MAX_LEN = 255


def _required_str(value: str | None, field_name: str) -> str:
    """Chuẩn hoá trường string bắt buộc: trim và reject rỗng."""
    if value is None or not str(value).strip():
        raise EmptyFieldError(f"{field_name} không được để trống")
    return str(value).strip()


def _required_datetime(value: datetime | None, field_name: str) -> datetime:
    """Reject datetime bắt buộc nếu client không gửi, đồng thời chuẩn hoá timezone.

    Pydantic đã parse datetime từ client; ta chỉ việc:
      1. Đảm bảo không null.
      2. Đưa về timezone-aware UTC để các phép so sánh (model_validator)
         không ném TypeError khi trộn TZ-aware và naive.
    """
    if value is None:
        raise EmptyFieldError(f"{field_name} không được để trống")
    return as_utc(value)


def _normalize_optional_datetime(value: datetime | None) -> datetime | None:
    """Đưa optional datetime về cùng timezone-aware UTC để so sánh được với
    giá trị đang lưu trong DB (Postgres trả về tz-aware)."""
    return None if value is None else as_utc(value)


# class AddStudentToCourseResponse(BaseModel):
#     enrollment_id: int
#     course_id: str
#     student_id: str


# class AddStudentToCourseRequest(BaseModel):
#     student_id: str

#     @field_validator("student_id")
#     @classmethod
#     def validate_user_id(cls, v: str | None) -> str:
#         if v is None:
#             raise EmptyFieldError("user_id is required")
#         return v


# # SỬA: Contract cho thao tác thêm toàn bộ sinh viên thuộc một lớp hành chính.
# class AddClassToCourseRequest(BaseModel):
#     class_id: str = Field(..., min_length=1, max_length=50)


# class AddClassToCourseResponse(BaseModel):
#     course_id: str
#     class_id: str
#     added_count: int
#     skipped_count: int
#     added_student_ids: list[str]


# # SỬA: Contract danh sách lớp và sinh viên để dropdown chọn lớp dùng API thật.
# class ClassResponse(BaseModel):
#     class_id: str
#     type: str
#     course_number: int
#     department: str


# class ClassStudentResponse(BaseModel):
#     user_id: str
#     full_name: str
#     email: AppEmailStr
#     class_id: str | None

# class GetStudentListResponse(BaseModel):
#     enrollment_id: int
#     student_id: str
#     full_name: str
#     email: AppEmailStr
#     class_id: str | None = None
#     # SỬA: Trả trực tiếp số bài AC để tab Sinh viên không phải đoán từ dữ liệu thiếu.
#     submitted_lessons: int = 0
#     total_lessons: int = 0
#     progress_percent: float = 0


class CourseProblemResponse(BaseModel):
    id: int
    title: str
    report: str | None
    level: str
    start_datetime: datetime
    end_datetime: datetime
    total_number_testcase: int


class CourseLessonResponse(BaseModel):
    id: int
    order: int
    title: str
    status: str
    opens_at: datetime | None
    deadline: datetime
    problems: list[CourseProblemResponse]
    participant_count: int | None


# SỬA: Giữ riêng trạng thái đã nộp để phân biệt điểm 0 với bài chưa làm.
# Không thêm cột vào models.py; đây chỉ là contract tổng hợp cho màn hình bảng điểm.
class GradeScoreResponse(BaseModel):
    value: float | None
    submitted: bool = False


class CourseGradeRowResponse(BaseModel):
    student_id: str
    full_name: str
    class_id: str | None
    overall_score: float | None
    session_scores: dict[str, list[GradeScoreResponse]]


# SỬA: Bổ sung contract cho dữ liệu buổi học, dùng chung cho API tạo/sửa và frontend.
class LessonCreateRequest(BaseModel):
    lesson_name: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: date
    problem_ids: list[int] = Field(default_factory=list)

    @field_validator("lesson_name")
    @classmethod
    def validate_lesson_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise EmptyFieldError("lesson_name không được để trống")
        return value

    @model_validator(mode="after")
    def validate_lesson_dates(self) -> "LessonCreateRequest":
        if self.start_date > self.end_date:
            raise InvalidFormatError("start_date phải trước hoặc bằng end_date")
        return self


# SỬA: Cho phép cập nhật từng phần thông tin buổi học và danh sách bài tập.
class LessonUpdateRequest(BaseModel):
    lesson_name: str | None = Field(default=None, min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    problem_ids: list[int] | None = None

    @field_validator("lesson_name")
    @classmethod
    def validate_optional_lesson_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise EmptyFieldError("lesson_name không được để trống")
        return value

    @model_validator(mode="after")
    def validate_optional_dates(self) -> "LessonUpdateRequest":
        if self.start_date is not None and self.end_date is not None and self.start_date > self.end_date:
            raise InvalidFormatError("start_date phải trước hoặc bằng end_date")
        return self


# SỬA: Response chi tiết buổi học phục vụ trang quản trị và thống kê bài nộp.
class LessonDetailResponse(BaseModel):
    id: int
    order: int
    title: str
    course_code: str
    course_name: str
    start_date: date
    end_date: date
    deadline_notice: str
    submitted_students: int
    total_students: int
    stats: dict[str, float | int | str]
    alert: dict[str, int | str]
    exercises: list[dict[str, object]]


# SỬA: Contract chi tiết bài tập để nút "Xem chi tiết" mở được dữ liệu thật.
class ProblemDetailResponse(BaseModel):
    id: int
    lesson_id: int
    course_id: str
    code: str | None
    title: str
    description: str
    constraints: str
    level: str
    hint: str | None
    complexity: str | None
    time_limit_seconds: int
    total_number_testcase: int
    start_datetime: datetime
    end_datetime: datetime
    starter_code: str
    testcases: list[dict[str, int | str | bool]]


# SỬA: Contract cập nhật nội dung bài tập theo đúng các thuộc tính đang có trong models.py.
# Không thêm trường điểm tối đa vì database hiện không có cột tương ứng.
class ProblemTestcaseUpdate(BaseModel):
    input: str
    expected_output: str
    is_sample: bool = False
    input_type: str = "stdin"
    expected_output_type: str = "stdout"


class ProblemUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    constraints: str | None = None
    level: str | None = None
    hint: str | None = None
    complexity: str | None = None
    time_limit_seconds: int | None = Field(default=None, ge=1)
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    starter_code: str | None = None
    testcases: list[ProblemTestcaseUpdate] | None = None

class CourseResponse(BaseModel):
    """Response chuẩn cho mọi endpoint thuộc module Course.

    Cùng shape với `POST /courses`, dùng lại cho GET/PATCH.
    """

    course_id: str
    course_name: str
    term: str
    start_date: datetime
    end_date: datetime
    avt_link: str | None
    created_by: str
    total_number_student: int
    sessions: list[CourseLessonResponse] = Field(default_factory=list)
    grades: list[CourseGradeRowResponse] = Field(default_factory=list)


class CreateCourseRequest(BaseModel):
    """Body cho `POST /courses` — tạo lớp học mới.

    Quy tắc nghiệp vụ (theo api-design-course.md):
    - `course_id`, `course_name`, `term`, `start_date`, `end_date` bắt buộc.
    - `start_date` phải trước `end_date` (model_validator).
    - `created_by` và `total_number_student` KHÔNG nhận từ client
      → server tự set ở service layer.
    """

    course_id: str = Field(..., min_length=1, max_length=COURSE_ID_MAX_LEN)
    course_name: str = Field(..., min_length=1, max_length=SHORT_STR_MAX_LEN)
    term: str = Field(..., min_length=1, max_length=SHORT_STR_MAX_LEN)
    start_date: datetime
    end_date: datetime
    avt_link: str | None = Field(default=None, max_length=AVT_LINK_MAX_LEN)

    @field_validator("course_id", "course_name", "term")
    @classmethod
    def validate_required_str(cls, v: str | None, info) -> str:
        return _required_str(v, info.field_name)

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_required_datetime(cls, v: datetime | None, info) -> datetime:
        return _required_datetime(v, info.field_name)

    @model_validator(mode="after")
    def validate_date_range(self) -> "CreateCourseRequest":
        # Cả hai đã được đưa về tz-aware UTC ở field_validator ở trên,
        # nên phép so sánh an toàn, không gây TypeError.
        if self.start_date >= self.end_date:
            raise InvalidFormatError("start_date phải trước end_date")
        return self


class UpdateCourseRequest(BaseModel):
    """Body cho `PATCH /courses/{course_id}` — partial update.

    Tất cả field đều optional; chỉ field được truyền mới được cập nhật.
    - `course_id`, `created_by`, `total_number_student` KHÔNG cho sửa.
    - Nếu client truyền cả `start_date` lẫn `end_date`, phải bảo đảm
      `start_date < end_date`. Nếu chỉ gửi một trong hai, validation
      cuối cùng sẽ do service layer so với giá trị đang lưu trong DB.
    - Field gửi lên `null` sẽ bị bỏ qua (không ghi đè cột NOT NULL).
    """

    course_name: str | None = Field(default=None, max_length=SHORT_STR_MAX_LEN)
    term: str | None = Field(default=None, max_length=SHORT_STR_MAX_LEN)
    start_date: datetime | None = None
    end_date: datetime | None = None
    avt_link: str | None = Field(default=None, max_length=AVT_LINK_MAX_LEN)

    @field_validator("course_name", "term")
    @classmethod
    def validate_optional_str(cls, v: str | None, info) -> str | None:
        # None nghĩa là client không gửi → bỏ qua.
        if v is None:
            return None
        if not v.strip():
            raise EmptyFieldError(f"{info.field_name} không được để trống")
        return v.strip()

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_datetime_from_string(cls, v):
        """Chuyển string ISO datetime → datetime object (pydantic v2 chạy mode=before trước parse)."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        # Client gửi string → pydantic gọi validator trước khi parse → ta parse ở đây.
        from datetime import datetime as dt

        if isinstance(v, str):
            # Chuẩn hoá: đảm bảo có timezone info mặc định UTC khi parse.
            try:
                return dt.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                # Fallback: pydantic sẽ catch lỗi format sau đó
                return v
        return v

    @field_validator("start_date", "end_date", mode="after")
    @classmethod
    def normalize_optional_datetime(cls, v: datetime | None) -> datetime | None:
        return _normalize_optional_datetime(v)

    @model_validator(mode="after")
    def validate_date_range(self) -> "UpdateCourseRequest":
        # Chỉ check khi client gửi cả hai. Nếu chỉ gửi một, service sẽ
        # đối chiếu với giá trị DB trước khi commit.
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date >= self.end_date
        ):
            raise InvalidFormatError("start_date phải trước end_date")
        return self
