from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.exceptions import EmptyFieldError, InvalidFormatError


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
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_optional_datetime(value: datetime | None) -> datetime | None:
    """Đưa optional datetime về cùng timezone-aware UTC để so sánh được với
    giá trị đang lưu trong DB (Postgres trả về tz-aware)."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class AddStudentToCourseResponse(BaseModel):
    enrollment_id: int
    course_id: str
    student_id: str


class AddStudentToCourseRequest(BaseModel):
    student_id: str

    @field_validator("student_id")
    @classmethod
    def validate_user_id(cls, v: str | None) -> str:
        if v is None:
            raise EmptyFieldError("user_id is required")
        return v


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
