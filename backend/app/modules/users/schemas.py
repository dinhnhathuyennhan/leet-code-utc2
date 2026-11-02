from datetime import date
from typing import Annotated

from pydantic import (
    BaseModel,
    AfterValidator,
    field_serializer,
    field_validator,
)

from app.core.utils.dates import build_date
from app.core.exceptions import InvalidFormatError
from app.core.utils.validation import AppEmailStr


def validate_account_email(value: str) -> str:
    if value.rsplit("@", 1)[-1].lower() != "st.utc2.edu.vn":
        raise InvalidFormatError("Email phải có đuôi @st.utc2.edu.vn.")
    return value


AccountEmailStr = Annotated[AppEmailStr, AfterValidator(validate_account_email)]


def parse_date_of_birth(value: date | str) -> date:
    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        raise InvalidFormatError(
            "Ngày sinh phải có định dạng dd/MM/yyyy hoặc dd-MM-yyyy"
        )

    if len(value) != 10:
        raise InvalidFormatError(
            "Ngày sinh phải có định dạng dd/MM/yyyy hoặc dd-MM-yyyy"
        )

    if value[2] == "/" and value[5] == "/":
        day_text, month_text, year_text = value.split("/")
    elif value[2] == "-" and value[5] == "-":
        day_text, month_text, year_text = value.split("-")
    elif value[4] == "-" and value[7] == "-":
        year_text, month_text, day_text = value.split("-")
    else:
        raise InvalidFormatError(
            "Ngày sinh phải có định dạng dd/MM/yyyy, dd-MM-yyyy hoặc yyyy-mm-dd"
        )

    if not (day_text.isdigit() and month_text.isdigit() and year_text.isdigit()):
        raise InvalidFormatError(
            "Ngày sinh phải có định dạng dd/MM/yyyy, dd-MM-yyyy hoặc yyyy-mm-dd"
        )

    return build_date(int(day_text), int(month_text), int(year_text))


def password_from_date(value: date) -> str:
    return value.strftime("%d%m%Y")


def student_temp_password(user_id: str) -> str:
    """Mật khẩu tạm của sinh viên = MSSV (file danh sách lớp không có ngày sinh)."""
    return user_id


class CreateTeacherRequest(BaseModel):
    user_id: str
    full_name: str
    date_of_birth: date
    email: AccountEmailStr
    avt_link: str | None = None

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth(cls, value: date | str) -> date:
        return parse_date_of_birth(value)


class CreateStudentRequest(BaseModel):
    user_id: str
    full_name: str
    date_of_birth: date
    email: AccountEmailStr
    class_id: str
    avt_link: str | None = None

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth(cls, value: date | str) -> date:
        return parse_date_of_birth(value)


class UserResponse(BaseModel):
    user_id: str
    full_name: str
    email: AppEmailStr
    role_id: int
    date_of_birth: date | None = None
    class_id: str | None = None

    @field_serializer("date_of_birth")
    def serialize_date_of_birth(self, value: date | None) -> str | None:
        return value.strftime("%d/%m/%Y") if value else None

class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int

class UserResetPasswordResponse(BaseModel):
    """Response cho API đặt lại mật khẩu của một tài khoản."""

    user_id: str
    temporary_password: str
