from pydantic import BaseModel

from app.core.Validator import AppEmailStr


class ClassResponse(BaseModel):
    class_id: str
    type: str
    course_number: int
    department: str


class ClassStudentResponse(BaseModel):
    user_id: str
    full_name: str
    email: AppEmailStr
    class_id: str | None
