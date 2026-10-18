from pydantic import BaseModel, Field, field_validator

from app.core.exceptions import EmptyFieldError
from app.core.utils.validation import AppEmailStr


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
    full_name: str
    email: AppEmailStr
    class_id: str | None = None
    accepted_problems: int = 0
    total_lessons: int = 0
    progress_percent: float = 0
