from datetime import date, datetime

from pydantic import (
    BaseModel,
    EmailStr,
    field_serializer,
    field_validator,
)


def parse_date_of_birth(value: date | str) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for date_format in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
        raise ValueError("Ngày sinh phải có định dạng dd/mm/yyyy hoặc yyyy-mm-dd")
    return value


def password_from_date(value: date) -> str:
    return value.strftime("%d%m%Y")


class CreateTeacherRequest(BaseModel):
    user_id: str
    full_name: str
    date_of_birth: date
    email: EmailStr
    avt_link: str | None = None

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth(cls, value: date | str) -> date:
        return parse_date_of_birth(value)


class CreateStudentRequest(BaseModel):
    user_id: str
    full_name: str
    date_of_birth: date
    email: EmailStr
    avt_link: str | None = None

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth(cls, value: date | str) -> date:
        return parse_date_of_birth(value)

class UserResponse(BaseModel):
    user_id: str
    full_name: str
    email: EmailStr
    role_id: int
    date_of_birth: date

    @field_serializer("date_of_birth")
    def serialize_date_of_birth(self, value: date) -> str:
        return value.strftime("%d/%m/%Y")


class UserResetPasswordResponse(BaseModel):
    """Response cho API đặt lại mật khẩu của một tài khoản."""

    user_id: str
    temporary_password: str

