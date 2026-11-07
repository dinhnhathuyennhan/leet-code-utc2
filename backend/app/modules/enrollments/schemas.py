from pydantic import BaseModel, Field, field_validator

from app.core.exceptions import EmptyFieldError
from app.core.utils.validation import AppEmailStr


class AddStudentToCourseResponse(BaseModel):
    enrollment_id: int
    course_id: str
    student_id: str
    student_code: str | None = None


class AddStudentToCourseRequest(BaseModel):
    # Nhận UUID `user_id` hoặc MSSV (`student_code`, 10 chữ số).
    student_id: str

    @field_validator("student_id")
    @classmethod
    def validate_user_id(cls, v: str | None) -> str:
        if v is None or not str(v).strip():
            raise EmptyFieldError("student_id is required")
        return str(v).strip()


class AddClassToCourseRequest(BaseModel):
    class_id: str = Field(..., min_length=1, max_length=50)


class AddClassToCourseResponse(BaseModel):
    course_id: str
    class_id: str
    added_count: int
    skipped_count: int
    added_student_ids: list[str]


class GetStudentListResponse(BaseModel):
    enrollment_id: int
    student_id: str
    student_code: str | None = None
    full_name: str
    email: AppEmailStr
