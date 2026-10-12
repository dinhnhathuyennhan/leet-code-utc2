"""Schema cho lớp hành chính (Class) và quy ước mã lớp.

Mã lớp có dạng ``<hệ>.<khoá>.<ngành>``, vd ``CQ.67.CNTT``:
    - ``build_class_id``: ghép 3 phần thành mã lớp (dùng cho ``POST /classes``).
    - ``parse_class_id``: tách mã lớp thành 3 phần (dùng cho import Excel).
Hai hàm ngược chiều nhau nên lớp tạo bằng tay và lớp tạo khi import luôn
cùng một định dạng.
"""

import unicodedata
from typing import NamedTuple

from pydantic import BaseModel, field_validator, model_validator

from app.core.exceptions import InvalidFormatError
from app.core.Validator import required_text


CLASS_ID_MAX_LEN = 50
DEPARTMENT_RULE = (
    "chỉ được gồm chữ cái, chữ số và các ký tự . & - "
    "(dấu chấm không được ở đầu, ở cuối hoặc đứng liền nhau)"
)


class ClassIdParts(NamedTuple):
    class_id: str
    type: str
    course_number: int
    department: str


def build_class_id(class_type: str, course_number: int, department: str) -> str:
    """Ghép mã lớp, vd ``("CQ", 67, "CNTT")`` → ``"CQ.67.CNTT"``."""
    return f"{class_type}.{course_number}.{department}"


def parse_class_id(value) -> ClassIdParts:
    """Tách mã lớp tại 2 dấu chấm đầu tiên.

    ``CQ.67.CNTT`` → CQ / 67 / CNTT; ``CQ.67.KTXDCTGT.2`` → CQ / 67 / KTXDCTGT.2.
    """
    class_id = unicodedata.normalize("NFC", required_text(value, "Mã lớp không được trống"))
    _check_class_id_length(class_id)
    parts = class_id.split(".", 2)
    if (
        len(parts) != 3
        or not all(parts)
        or not (parts[1].isascii() and parts[1].isdigit())
    ):
        raise InvalidFormatError(
            f"Mã lớp {class_id} không đúng dạng <hệ>.<khoá>.<ngành> (vd CQ.67.CNTT)"
        )
    class_type, course_number, department = parts
    if not _is_valid_department(department):
        raise InvalidFormatError(f"Mã lớp {class_id} có ngành {DEPARTMENT_RULE}")
    return ClassIdParts(class_id, class_type, int(course_number), department)


def _check_class_id_length(class_id: str) -> None:
    if len(class_id) > CLASS_ID_MAX_LEN:
        raise InvalidFormatError(f"Mã lớp không được dài quá {CLASS_ID_MAX_LEN} ký tự")


def _is_valid_department(department: str) -> bool:
    """Ngành theo file thật: ``CNTT``, ``KTXDCTGT.2``, ``XDDD&CN.1``, ``TC-NH``, ``ĐK&TTĐSHĐ``.

    Chặn ``/`` (lớp sẽ không gọi được qua ``/classes/{class_id}``), khoảng trắng
    và các ký tự đặc biệt khác.
    """
    return (
        all(ch.isalpha() or ch in "0123456789.&-" for ch in department)
        and not department.startswith(".")
        and not department.endswith(".")
        and ".." not in department
    )


class CreateClassRequest(BaseModel):
    """Body của ``POST /classes``: client gửi 3 phần, server tự ghép ``class_id``."""

    type: str
    course_number: int
    department: str

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, value) -> str:
        class_type = required_text(value, "Hệ đào tạo không được trống")
        # chỉ chữ cái không dấu: chặn cả dấu chấm (ký tự ngăn cách trong mã lớp),
        # số, khoảng trắng và ký tự đặc biệt
        if not (class_type.isascii() and class_type.isalpha()):
            raise InvalidFormatError("Hệ đào tạo chỉ được gồm chữ cái không dấu")
        return class_type

    @field_validator("course_number", mode="before")
    @classmethod
    def reject_bool_course_number(cls, value):
        # pydantic tự đổi true/false thành 1/0, nên chặn trước khi parse
        if isinstance(value, bool):
            raise InvalidFormatError("Khoá phải là số nguyên dương")
        return value

    @field_validator("course_number")
    @classmethod
    def validate_course_number(cls, value: int) -> int:
        if value <= 0:
            raise InvalidFormatError("Khoá phải là số nguyên dương")
        return value

    @field_validator("department", mode="before")
    @classmethod
    def validate_department(cls, value) -> str:
        # required_text gọi str(), nên phải chặn list/dict/số trước,
        # nếu không ["CNTT"] sẽ thành ngành "['CNTT']"
        if value is not None and not isinstance(value, str):
            raise InvalidFormatError("Ngành phải là chuỗi")
        department = unicodedata.normalize("NFC", required_text(value, "Ngành không được trống"))
        if not _is_valid_department(department):
            raise InvalidFormatError(f"Ngành {DEPARTMENT_RULE}")
        return department

    @model_validator(mode="after")
    def validate_class_id_length(self) -> "CreateClassRequest":
        _check_class_id_length(self.class_id)
        return self

    @property
    def class_id(self) -> str:
        return build_class_id(self.type, self.course_number, self.department)


class ClassResponse(BaseModel):
    class_id: str
    type: str
    course_number: int
    department: str
    student_count: int
