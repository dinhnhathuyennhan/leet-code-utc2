
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.datetime_utils import as_utc
from app.core.exceptions import EmptyFieldError, InvalidFormatError
from app.schemas.grade import CourseGradeRowResponse

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
    if value is None:
        raise EmptyFieldError(f"{field_name} không được để trống")
    return as_utc(value)


def _normalize_optional_datetime(value: datetime | None) -> datetime | None:
    return None if value is None else as_utc(value)


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


class CourseResponse(BaseModel):
    """Response chuẩn cho mọi endpoint thuộc module Course (cùng shape với `POST /courses`)."""

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


class CourseTermsResponse(BaseModel):
    academic_years: list[str]
    semesters: list[int]


class CreateCourseRequest(BaseModel):
    """Body cho `POST /courses` — tạo lớp học mới.

    `created_by` và `total_number_student` KHÔNG nhận từ client (server tự set).
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
        if self.start_date >= self.end_date:
            raise InvalidFormatError("start_date phải trước end_date")
        return self


class UpdateCourseRequest(BaseModel):
    """Body cho `PATCH /courses/{course_id}` — partial update (field null bị bỏ qua)."""

    course_name: str | None = Field(default=None, max_length=SHORT_STR_MAX_LEN)
    term: str | None = Field(default=None, max_length=SHORT_STR_MAX_LEN)
    start_date: datetime | None = None
    end_date: datetime | None = None
    avt_link: str | None = Field(default=None, max_length=AVT_LINK_MAX_LEN)

    @field_validator("course_name", "term")
    @classmethod
    def validate_optional_str(cls, v: str | None, info) -> str | None:
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
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                return v
        return v

    @field_validator("start_date", "end_date", mode="after")
    @classmethod
    def normalize_optional_datetime(cls, v: datetime | None) -> datetime | None:
        return _normalize_optional_datetime(v)

    @model_validator(mode="after")
    def validate_date_range(self) -> "UpdateCourseRequest":
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date >= self.end_date
        ):
            raise InvalidFormatError("start_date phải trước end_date")
        return self
