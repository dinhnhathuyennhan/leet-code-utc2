from pydantic import (
    BaseModel,
    field_validator,
)

from app.core.exceptions import InvalidFormatError
from app.core.utils.validation import AppEmailStr, required_text

STUDENT_CODE_LENGTH = 10


def _validate_student_code(value: str) -> str:
    """Validate MSSV đúng 10 chữ số."""
    code = required_text(value, "Mã sinh viên không được trống")
    if len(code) != STUDENT_CODE_LENGTH:
        raise InvalidFormatError(
            f"Mã sinh viên phải gồm đúng {STUDENT_CODE_LENGTH} chữ số"
        )
    if not code.isascii() or not code.isdigit():
        raise InvalidFormatError("Mã sinh viên chỉ được gồm chữ số (0-9)")
    return code


class CreateTeacherRequest(BaseModel):
    full_name: str
    email: AppEmailStr
    avt_link: str | None = None


class CreateStudentRequest(BaseModel):
    student_code: str
    full_name: str
    email: AppEmailStr
    class_id: str
    avt_link: str | None = None

    @field_validator("student_code", mode="before")
    @classmethod
    def validate_student_code(cls, value) -> str:
        return _validate_student_code(str(value) if value is not None else "")


class UserResponse(BaseModel):
    user_id: str
    full_name: str
    email: AppEmailStr
    role_id: int
    student_code: str | None = None
    class_id: str | None = None


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int


class UserResetPasswordResponse(BaseModel):
    """Response cho API đặt lại mật khẩu của một tài khoản."""

    user_id: str
    temporary_password: str
