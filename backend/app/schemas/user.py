from datetime import date

from pydantic import (
    BaseModel,
    field_serializer,
    field_validator,
)

from app.core.date import build_date
from app.core.exceptions import InvalidFormatError
from app.core.Validator import AppEmailStr


def parse_date_of_birth(value: date | str) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        if len(value) == 10 and value[2] == "/" and value[5] == "/":
            day_text, month_text, year_text = value.split("/")
        elif len(value) == 10 and value[4] == "-" and value[7] == "-":
            year_text, month_text, day_text = value.split("-")
        else:
            raise InvalidFormatError(
                "Ngày sinh phải có định dạng yyyy-mm-dd"
            )

        if not (day_text.isdigit() and month_text.isdigit() and year_text.isdigit()):
            raise InvalidFormatError(
                "Ngày sinh phải có định dạng yyyy-mm-dd"
            )

        return build_date(int(day_text), int(month_text), int(year_text))

    raise InvalidFormatError(
        "Ngày sinh phải có định dạng yyyy-mm-dd"
    )


def password_from_date(value: date) -> str:
    return value.strftime("%d%m%Y")


class CreateTeacherRequest(BaseModel):
    user_id: str
    full_name: str
    date_of_birth: date
    email: AppEmailStr
    avt_link: str | None = None

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth(cls, value: date | str) -> date:
        return parse_date_of_birth(value)


class CreateStudentRequest(BaseModel):
    user_id: str
    full_name: str
    date_of_birth: date
    email: AppEmailStr
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
    date_of_birth: date

    @field_serializer("date_of_birth")
    def serialize_date_of_birth(self, value: date) -> str:
        return value.strftime("%d/%m/%Y")

