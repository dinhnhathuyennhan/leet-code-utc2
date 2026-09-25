from pydantic import BaseModel, field_validator

from app.core.exceptions import EmptyFieldError
from app.core.Validator import AppEmailStr


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

class GetStudentListResponse(BaseModel):
    enrollment_id: int
    student_id: str
    full_name: str
    email: AppEmailStr
