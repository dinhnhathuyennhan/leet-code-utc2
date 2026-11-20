import unicodedata
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    field_validator,
)

from app.core.exceptions import InvalidFormatError
from app.core.utils.validation import AppEmailStr, required_text


ACCOUNT_EMAIL_DOMAIN = "st.utc2.edu.vn"


def student_email(code: str) -> str:
    """Email sinh viên luôn là <MSSV>@st.utc2.edu.vn."""
    return f"{code}@{ACCOUNT_EMAIL_DOMAIN}"


def validate_account_email(value: str) -> str:
    if value.rsplit("@", 1)[-1].lower() != ACCOUNT_EMAIL_DOMAIN:
        raise InvalidFormatError("Email phải có đuôi @st.utc2.edu.vn.")
    return value


AccountEmailStr = Annotated[
    AppEmailStr,
    AfterValidator(validate_account_email),
]


STUDENT_CODE_LENGTH = 10


def _validate_student_code(value: str) -> str:
    """Validate MSSV đúng 10 chữ số."""
    code = required_text(value, "Mã sinh viên không được trống")

    if len(code) != STUDENT_CODE_LENGTH:
        raise InvalidFormatError(
            f"Mã sinh viên phải gồm đúng {STUDENT_CODE_LENGTH} chữ số"
        )

    if not code.isascii() or not code.isdigit():
        raise InvalidFormatError(
            "Mã sinh viên chỉ được gồm chữ số (0-9)"
        )

    return code


class CreateTeacherRequest(BaseModel):
    full_name: str
    email: AccountEmailStr
    avt_link: str | None = None


class CreateStudentRequest(BaseModel):
    student_code: str
    full_name: str
    email: AccountEmailStr
    class_id: str
    avt_link: str | None = None

    @field_validator("student_code", mode="before")
    @classmethod
    def validate_student_code(cls, value) -> str:
        return _validate_student_code(
            str(value) if value is not None else ""
        )


def _validate_full_name(value) -> str:
    if not isinstance(value, str):
        raise InvalidFormatError("Họ và tên phải là chuỗi")
    text = required_text(value, "Họ và tên không được để trống")
    return " ".join(text.split())


class UpdateUserRequest(BaseModel):
    """Body PATCH /users/{id}. Field không gửi hoặc null = không đổi."""

    full_name: str | None = None
    email: AccountEmailStr | None = None
    student_code: str | None = None
    class_id: str | None = None

    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, value):
        return None if value is None else _validate_full_name(value)

    @field_validator("student_code", mode="before")
    @classmethod
    def validate_student_code(cls, value):
        return None if value is None else _validate_student_code(str(value))

    @field_validator("class_id", mode="before")
    @classmethod
    def validate_class_id(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidFormatError("Mã lớp phải là chuỗi")
        return required_text(unicodedata.normalize("NFC", value), "Mã lớp không được trống")


class UserResponse(BaseModel):
    user_id: str
    full_name: str
    email: AppEmailStr
    role_id: int
    student_code: str | None = None
    class_id: str | None = None
    is_active: bool


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int


class UserResetPasswordResponse(BaseModel):
    """Response cho API đặt lại mật khẩu của một tài khoản."""

    user_id: str
    temporary_password: str
