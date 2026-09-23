from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator

from app.core.exceptions import EmptyFieldError, InvalidFormatError


class AddStudentToCourseResponse(BaseModel):
    enrollment_id: int
    course_id: str
    student_id: str


class AddStudentToCourseRequest(BaseModel):
    student_id: str

    @field_validator("student_id")
    @classmethod
    def validate_user_id(cls, v) -> str:
        if v is None:
            raise EmptyFieldError("user_id is required")
        return v


def _required_str(value: str | None, field_name: str) -> str:
    """Chuẩn hoá các trường string bắt buộc: trim và reject rỗng."""
    if value is None or not value.strip():
        raise EmptyFieldError(f"{field_name} không được để trống")
    return value.strip()


def _required_datetime(value: datetime | None, field_name: str) -> datetime:
    """Reject datetime bắt buộc nếu client không gửi."""
    if value is None:
        raise EmptyFieldError(f"{field_name} không được để trống")
    return value


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

    course_id: str
    course_name: str
    term: str
    start_date: datetime
    end_date: datetime
    avt_link: str | None = None

    @field_validator("course_id", "course_name", "term")
    @classmethod
    def validate_required_str(cls, v, info) -> str:
        return _required_str(v, info.field_name)

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_required_datetime(cls, v, info) -> datetime:
        return _required_datetime(v, info.field_name)

    @model_validator(mode="after")
    def validate_date_range(self) -> "CreateCourseRequest":
        if self.start_date >= self.end_date:
            raise InvalidFormatError(
                "start_date phải trước end_date"
            )
        return self


class UpdateCourseRequest(BaseModel):
    """Body cho `PATCH /courses/{course_id}` — partial update.

    Tất cả field đều optional; chỉ field được truyền mới được cập nhật.
    - `course_id`, `created_by`, `total_number_student` KHÔNG cho sửa.
    - Nếu truyền cả `start_date` và `end_date`, phải bảo đảm
      `start_date < end_date` (model_validator).
    """

    course_name: str | None = None
    term: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    avt_link: str | None = None

    @field_validator("course_name", "term")
    @classmethod
    def validate_optional_str(cls, v, info) -> str | None:
        # Chỉ reject nếu client cố tình truyền chuỗi rỗng sau khi trim.
        if v is not None and not v.strip():
            raise EmptyFieldError(f"{info.field_name} không được để trống")
        return v.strip() if isinstance(v, str) else v

    @model_validator(mode="after")
    def validate_date_range(self) -> "UpdateCourseRequest":
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date >= self.end_date
        ):
            raise InvalidFormatError(
                "start_date phải trước end_date"
            )
        return self
