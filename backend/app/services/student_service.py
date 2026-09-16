from io import BytesIO

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from app.core.password import generate_temporary_password, hash_password
from app.dependencies import Role
from app.schemas.student import (
    StudentCreate,
    StudentImportCreatedRow,
    StudentImportErrorRow,
    StudentImportResponse,
)
from models import User

MAX_IMPORT_ROWS = 500


class _EmailCheck(BaseModel):
    """Model phụ để validate email string trong service layer."""

    email: EmailStr


class EmailAlreadyExistsError(Exception):
    """Email đã tồn tại trong hệ thống."""


class InvalidExcelFormatError(Exception):
    """File Excel sai định dạng (không phải .xlsx hoặc thiếu cột bắt buộc)."""


class EmptyExcelFileError(Exception):
    """File Excel không có dữ liệu."""


class ExcelFileTooLargeError(Exception):
    """File Excel vượt quá số dòng cho phép."""


def create_student(
    session: Session, data: StudentCreate
) -> tuple[User, str]:
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise EmailAlreadyExistsError(data.email)

    temporary_password = generate_temporary_password()
    student = User(
        user_id=data.email,
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(temporary_password),
        must_change_password=True,
        role_id=Role.STUDENT,
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    return student, temporary_password


def _parse_excel(
    contents: bytes, filename: str, max_rows: int
) -> list[tuple[int, object | None, object | None]]:
    """Parse file Excel. Trả về list (row_number, full_name_raw, email_raw).

    Raises:
        InvalidExcelFormatError: file không đúng định dạng/thiếu cột.
        EmptyExcelFileError: file không có dữ liệu.
        ExcelFileTooLargeError: vượt quá số dòng cho phép.
    """
    if not filename or not filename.lower().endswith(".xlsx"):
        raise InvalidExcelFormatError("File phải có định dạng .xlsx")

    try:
        workbook = load_workbook(BytesIO(contents), read_only=True, data_only=True)
    except (InvalidFileException, OSError) as err:
        raise InvalidExcelFormatError(
            f"Không đọc được file Excel: {err}"
        ) from err

    worksheet = workbook.active
    if worksheet is None:
        raise InvalidExcelFormatError("File Excel không có sheet nào")

    rows = list(worksheet.iter_rows(values_only=True))
    if not rows:
        raise EmptyExcelFileError("File không có dữ liệu")

    header = rows[0]
    if header is None or all(cell is None for cell in header):
        raise InvalidExcelFormatError("File Excel thiếu hàng tiêu đề")

    name_index: int | None = None
    email_index: int | None = None
    for index, cell in enumerate(header):
        if cell is None:
            continue
        normalized = str(cell).strip().lower()
        if normalized == "full_name":
            name_index = index
        elif normalized == "email":
            email_index = index

    if name_index is None or email_index is None:
        raise InvalidExcelFormatError(
            "File Excel phải có đầy đủ 2 cột: full_name, email"
        )

    data_rows = rows[1:]
    if len(data_rows) > max_rows:
        raise ExcelFileTooLargeError(
            f"File vượt quá giới hạn {max_rows} dòng cho phép"
        )
    if not data_rows:
        raise EmptyExcelFileError("File không có dòng dữ liệu nào")

    parsed: list[tuple[int, object | None, object | None]] = []
    for row_index, row in enumerate(data_rows, start=2):
        name_value = row[name_index] if name_index < len(row) else None
        email_value = row[email_index] if email_index < len(row) else None
        parsed.append((row_index, name_value, email_value))
    return parsed


def import_students(
    session: Session, contents: bytes, filename: str
) -> StudentImportResponse:
    """Xử lý best-effort: dòng hợp lệ tạo tài khoản, dòng lỗi liệt kê trong errors."""
    parsed_rows = _parse_excel(contents, filename, MAX_IMPORT_ROWS)

    valid_rows: list[tuple[int, str, str]] = []
    errors: list[StudentImportErrorRow] = []
    seen_emails: set[str] = set()

    for row_index, full_name_raw, email_raw in parsed_rows:
        full_name_str = (
            str(full_name_raw).strip() if full_name_raw is not None else ""
        )
        email_str = str(email_raw).strip() if email_raw is not None else ""

        if not full_name_str:
            errors.append(
                StudentImportErrorRow(
                    row=row_index,
                    email=email_str or None,
                    reason="Họ tên không được trống",
                )
            )
            continue
        if not email_str:
            errors.append(
                StudentImportErrorRow(
                    row=row_index, email=None, reason="Email không được trống"
                )
            )
            continue
        try:
            _EmailCheck(email=email_str)
        except ValueError:
            errors.append(
                StudentImportErrorRow(
                    row=row_index,
                    email=email_str,
                    reason="Email không đúng định dạng",
                )
            )
            continue

        email_lower = email_str.lower()
        if email_lower in seen_emails:
            errors.append(
                StudentImportErrorRow(
                    row=row_index,
                    email=email_str,
                    reason="Email đã xuất hiện trước đó trong file",
                )
            )
            continue
        seen_emails.add(email_lower)
        valid_rows.append((row_index, full_name_str, email_str))

    existing_emails: set[str] = set()
    if valid_rows:
        emails_to_check = {row[2] for row in valid_rows}
        existing = session.exec(
            select(User.email).where(User.email.in_(emails_to_check))
        ).all()
        existing_emails = set(existing)

    created: list[StudentImportCreatedRow] = []
    for row_index, full_name, email in valid_rows:
        if email in existing_emails:
            errors.append(
                StudentImportErrorRow(
                    row=row_index,
                    email=email,
                    reason="Email đã tồn tại trong hệ thống",
                )
            )
            continue

        temporary_password = generate_temporary_password()
        student = User(
            user_id=email,
            full_name=full_name,
            email=email,
            hashed_password=hash_password(temporary_password),
            must_change_password=True,
            role_id=Role.STUDENT,
        )
        session.add(student)
        created.append(
            StudentImportCreatedRow(
                user_id=email,
                full_name=full_name,
                email=email,
                temporary_password=temporary_password,
            )
        )

    if created:
        session.commit()

    return StudentImportResponse(created=created, errors=errors)
