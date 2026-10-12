from pydantic import BaseModel, field_validator

from app.core.exceptions import InvalidFormatError
from app.core.Validator import required_text
from app.schemas.classroom import parse_class_id

MAX_ID_LENGTH = 50


class StudentImportRow(BaseModel):
    """Một sinh viên đã bốc tách từ file danh sách lớp và đã validate.

    Validator raise ``AppError`` (không phải ``ValueError``) nên pydantic
    không gói lại thành ``ValidationError``: service bắt ``AppError`` và lấy
    ``err.message`` làm lý do lỗi của dòng.
    """

    sheet: str
    row: int
    user_id: str
    full_name: str
    class_id: str

    @field_validator("user_id", mode="before")
    @classmethod
    def validate_user_id(cls, value) -> str:
        user_id = required_text(value, "Mã sinh viên không được trống")
        if len(user_id) > MAX_ID_LENGTH:
            raise InvalidFormatError(
                f"Mã sinh viên không được dài quá {MAX_ID_LENGTH} ký tự"
            )
        if not (user_id.isascii() and user_id.isalnum()):
            raise InvalidFormatError("Mã sinh viên chỉ được gồm chữ không dấu và số")
        return user_id

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

    user_id: str
    full_name: str
    email: str
    class_id: str
    temporary_password: str


class StudentImportSkippedRow(BaseModel):
    """Một sinh viên bị bỏ qua vì đã có tài khoản (không phải lỗi)."""

    sheet: str
    row: int
    user_id: str
    reason: str


class StudentImportErrorRow(BaseModel):
    """Một dòng bị lỗi, kèm lý do."""

    sheet: str
    row: int
    user_id: str | None = None
    reason: str


class StudentImportResponse(BaseModel):
    """Kết quả import: đã tạo, bỏ qua, và lỗi."""

    created: list[StudentImportCreatedRow]
    skipped: list[StudentImportSkippedRow]
    errors: list[StudentImportErrorRow]
