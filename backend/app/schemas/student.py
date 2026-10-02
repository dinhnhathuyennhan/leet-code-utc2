from pydantic import BaseModel


class StudentImportCreatedRow(BaseModel):
    """Một dòng import Excel đã tạo tài khoản thành công."""

    user_id: str
    full_name: str
    email: str
    date_of_birth: str
    temporary_password: str


class StudentImportErrorRow(BaseModel):
    """Một dòng import Excel bị lỗi, kèm lý do."""

    row: int
    email: str | None = None
    date_of_birth: str | None = None
    reason: str


class StudentImportResponse(BaseModel):
    """Kết quả import Excel — liệt kê các dòng tạo thành công và các dòng lỗi."""

    created: list[StudentImportCreatedRow]
    errors: list[StudentImportErrorRow]
