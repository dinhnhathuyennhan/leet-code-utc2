from pydantic import BaseModel, field_validator

from app.core.exceptions import InvalidFormatError
from app.core.utils.validation import required_text
from app.modules.classrooms.schemas import parse_class_id

STUDENT_CODE_LENGTH = 10


def _validate_student_code(value: str) -> str:
    """Validate MSSV đúng 10 chữ số."""
    code = required_text(value, "Mã sinh viên không được trống")
    if len(code) != STUDENT_CODE_LENGTH:
        raise InvalidFormatError(f"Mã sinh viên phải gồm đúng {STUDENT_CODE_LENGTH} chữ số")
    if not code.isascii() or not code.isdigit():
        raise InvalidFormatError("Mã sinh viên chỉ được gồm chữ số (0-9)")
    return code


class StudentImportRow(BaseModel):
    """Một sinh viên đã bốc tách từ file danh sách lớp và đã validate.

    Validator raise ``AppError`` (không phải ``ValueError``) nên pydantic
    không gói lại thành ``ValidationError``: service bắt ``AppError`` và lấy
    ``err.message`` làm lý do lỗi của dòng.
    """

    sheet: str
    row: int
    student_code: str   # MSSV đọc từ cột "Mã sinh viên" trong file Excel
    full_name: str
    class_id: str

    @field_validator("student_code", mode="before")
    @classmethod
    def validate_student_code(cls, value) -> str:
        return _validate_student_code(str(value) if value is not None else "")

    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, value) -> str:
        return required_text(value, "Họ tên không được trống")

    @field_validator("class_id", mode="before")
    @classmethod
    def validate_class_id(cls, value) -> str:
        return parse_class_id(value).class_id


class StudentImportCreatedRow(BaseModel):
    """Một sinh viên đã được tạo tài khoản."""

    student_code: str
    full_name: str
    email: str
    class_id: str
    temporary_password: str


class StudentImportSkippedRow(BaseModel):
    """Một sinh viên bị bỏ qua vì đã có tài khoản (không phải lỗi)."""

    sheet: str
    row: int
    student_code: str
    reason: str


class StudentImportErrorRow(BaseModel):
    """Một dòng bị lỗi, kèm lý do."""

    sheet: str
    row: int
    student_code: str | None = None
    reason: str


class StudentImportResponse(BaseModel):
    """Kết quả import: đã tạo, bỏ qua, và lỗi."""

    created: list[StudentImportCreatedRow]
    skipped: list[StudentImportSkippedRow]
    errors: list[StudentImportErrorRow]
