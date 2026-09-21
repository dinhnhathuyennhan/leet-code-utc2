from pydantic import BaseModel

from app.core.Validator import AppEmailStr


class GetStudentListResponse(BaseModel):
    enrollment_id: int
    student_id: str
    full_name: str
    email: AppEmailStr
