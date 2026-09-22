"""Service xử lý nghiệp vụ liên quan tới sinh viên.

Hiện tại gồm:
    - ``import_students``: đọc file Excel và tạo hàng loạt tài khoản sinh viên.

Đặc tả import Excel:
    - Định dạng: .xlsx.
    - Header (hàng 1) bắt buộc có 4 cột: ``user_id``, ``full_name``,
      ``date_of_birth`` (dd/mm/yyyy hoặc yyyy-mm-dd), ``email``.
    - Mỗi dòng được xử lý **độc lập** (commit theo từng dòng): nếu một
      dòng lỗi thì chỉ dòng đó bị rollback, các dòng trước vẫn được giữ.
    - Mật khẩu tạm thời được sinh từ ngày sinh theo định dạng ``ddmmyyyy``
      (xem ``app.schemas.user.password_from_date``).
"""

from datetime import date as _date
from datetime import datetime as _datetime
from io import BytesIO

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from pydantic import BaseModel, EmailStr, ValidationError
from sqlmodel import Session, select

from app.core.exceptions import AppError
from app.core.password import hash_password
from app.dependencies import Role
from app.schemas.student import (
    StudentImportCreatedRow,
    StudentImportErrorRow,
    StudentImportResponse,
)
from app.schemas.user import (
    parse_date_of_birth,
    password_from_date,
)
from models import User

MAX_IMPORT_ROWS = 500


class _EmailCheck(BaseModel):
    """Model phụ để validate email string trong service layer."""

    email: EmailStr


class InvalidExcelFormatError(AppError):
    status_code = 422
    error_code = "INVALID_EXCEL_FORMAT"


class EmptyExcelFileError(AppError):
    status_code = 400
    error_code = "EMPTY_EXCEL_FILE"


class ExcelFileTooLargeError(AppError):
    status_code = 400
    error_code = "EXCEL_FILE_TOO_LARGE"


def _parse_excel(
    contents: bytes, filename: str, max_rows: int
) -> list[tuple[int, str, str, str, str]]:
    """Đọc file Excel và trả về các giá trị thô của từng dòng dữ liệu.

    Returns:
        list các tuple ``(row_index, user_id_raw, full_name_raw, date_raw, email_raw)``
        với mọi giá trị đều được strip; ``None`` nếu ô trống.

    Raises:
        InvalidExcelFormatError, EmptyExcelFileError, ExcelFileTooLargeError.
    """
    if not filename or not filename.lower().endswith(".xlsx"):
        raise InvalidExcelFormatError("File phải có định dạng .xlsx")

    try:
        workbook = load_workbook(BytesIO(contents), read_only=True, data_only=True)
    except (InvalidFileException, OSError) as err:
        raise InvalidExcelFormatError(f"Không đọc được file Excel: {err}") from err

    worksheet = workbook.active
    if worksheet is None:
        raise InvalidExcelFormatError("File Excel không có sheet nào")

    rows = list(worksheet.iter_rows(values_only=True))
    if not rows:
        raise EmptyExcelFileError("File không có dữ liệu")

    header = rows[0]
    if header is None or all(cell is None for cell in header):
        raise InvalidExcelFormatError("File Excel thiếu hàng tiêu đề")

    required_columns = {
        "user_id": ("user_id", "user id", "mssv", "student id"),
        "full_name": ("full_name", "full name", "name", "họ tên", "ho ten"),
        "date_of_birth": (
            "date_of_birth",
            "date of birth",
            "dob",
            "ngày sinh",
            "ngay sinh",
        ),
        "email": ("email", "e-mail", "mail"),
    }
    column_indexes: dict[str, int] = {}
    for index, cell in enumerate(header):
        if cell is None:
            continue
        normalized = str(cell).strip().lower()
        for canonical, aliases in required_columns.items():
            if normalized in aliases:
                column_indexes[canonical] = index
                break

    missing = [name for name in required_columns if name not in column_indexes]
    if missing:
        raise InvalidExcelFormatError(
            "File Excel thiếu cột bắt buộc: " + ", ".join(missing)
        )

    data_rows = rows[1:]
    if len(data_rows) > max_rows:
        raise ExcelFileTooLargeError(f"File vượt quá giới hạn {max_rows} dòng cho phép")
    if not data_rows:
        raise EmptyExcelFileError("File không có dòng dữ liệu nào")

    parsed: list[tuple[int, str, str, str, str]] = []
    for row_index, row in enumerate(data_rows, start=2):
        user_id_value = (
            _cell_to_string(row[column_indexes["user_id"]])
            if column_indexes["user_id"] < len(row)
            else ""
        )
        full_name_value = (
            _cell_to_string(row[column_indexes["full_name"]])
            if column_indexes["full_name"] < len(row)
            else ""
        )
        date_value = (
            _cell_to_string(row[column_indexes["date_of_birth"]])
            if column_indexes["date_of_birth"] < len(row)
            else ""
        )
        email_value = (
            _cell_to_string(row[column_indexes["email"]])
            if column_indexes["email"] < len(row)
            else ""
        )
        parsed.append(
            (row_index, user_id_value, full_name_value, date_value, email_value)
        )
    return parsed


def _cell_to_string(cell_value) -> str:
    """Chuẩn hoá một ô Excel thành chuỗi để truyền cho các bước validate.

    openpyxl trả về kiểu dữ liệu phụ thuộc vào định dạng ô:
        - Ô format ``Date``: trả về ``datetime.datetime`` hoặc ``datetime.date``.
          ``str(datetime)`` cho ra ``"yyyy-mm-dd hh:mm:ss"`` không khớp với
          ``parse_date_of_birth`` (chỉ nhận ``dd/mm/yyyy`` hoặc ``yyyy-mm-dd``),
          nên ta phải gọi ``.date().isoformat()`` để ra đúng ``yyyy-mm-dd``.
        - Ô text / số: trả về chuỗi ``str(value).strip()`` như cũ.
        - Ô rỗng (``None``): trả về ``""``.
    """
    if cell_value is None:
        return ""
    if isinstance(cell_value, _datetime):
        return cell_value.date().isoformat()
    if isinstance(cell_value, _date):
        return cell_value.isoformat()
    return str(cell_value).strip()


def _validate_row(
    row_index: int,
    user_id: str,
    full_name: str,
    date_str: str,
    email: str,
    seen_user_ids: set[str],
    seen_emails: set[str],
    existing_user_ids: set[str],
    existing_emails: set[str],
) -> tuple[User | None, str, str, str, str | None, str | None]:
    """Validate một dòng Excel và trả về dữ liệu đã chuẩn hoá hoặc lỗi.

    Returns:
        tuple ``(student_or_None, user_id, full_name, email_or_None,
        date_of_birth_or_None, error_reason_or_None)``.

        Khi ``error_reason`` không phải ``None``, dòng này bị lỗi và
        sẽ được đưa vào ``errors``. Ngược lại dòng đã sẵn sàng để insert.
    """
    if not user_id:
        return None, user_id, full_name, email, None, "user_id không được trống"
    if not full_name:
        return None, user_id, full_name, email, None, "Họ tên không được trống"
    if not date_str:
        return None, user_id, full_name, email, None, "Ngày sinh không được trống"
    if not email:
        return None, user_id, full_name, None, None, "Email không được trống"

    try:
        _EmailCheck(email=email)
    except ValidationError:
        return None, user_id, full_name, email, None, "Email không đúng định dạng"

    try:
        parsed_date = parse_date_of_birth(date_str)
    except ValueError as err:
        return None, user_id, full_name, email, None, str(err)

    email_lower = email.lower()
    user_id_lower = user_id.lower()

    if user_id_lower in seen_user_ids:
        return (
            None, user_id, full_name, email, None,
            "user_id đã xuất hiện trước đó trong file",
        )
    if email_lower in seen_emails:
        return (
            None, user_id, full_name, email, None,
            "Email đã xuất hiện trước đó trong file",
        )
    if user_id_lower in existing_user_ids:
        return (
            None, user_id, full_name, email, None,
            "user_id đã tồn tại trong hệ thống",
        )
    if email_lower in existing_emails:
        return (
            None, user_id, full_name, email, None,
            "Email đã tồn tại trong hệ thống",
        )

    student = User(
        user_id=user_id,
        full_name=full_name,
        email=email,
        hashed_password=hash_password(password_from_date(parsed_date)),
        must_change_password=True,
        date_of_birth=parsed_date,
        role_id=Role.STUDENT,
    )
    seen_user_ids.add(user_id_lower)
    seen_emails.add(email_lower)
    return student, user_id, full_name, email, date_str, None


def import_students(
    session: Session, contents: bytes, filename: str
) -> StudentImportResponse:
    """Import danh sách sinh viên từ file Excel.

    Xử lý theo từng dòng (best-effort, commit theo từng dòng):
        - Mỗi dòng hợp lệ sẽ được ``session.add()`` và ``session.commit()``
          ngay để đảm bảo một dòng lỗi không rollback cả batch.
        - Mỗi dòng lỗi sẽ được đưa vào ``errors`` cùng lý do cụ thể.
    """
    parsed_rows = _parse_excel(contents, filename, MAX_IMPORT_ROWS)

    # Tập trung query một lần để check trùng với DB
    user_ids_to_check = {row[1].lower() for row in parsed_rows if row[1]}
    emails_to_check = {row[4].lower() for row in parsed_rows if row[4]}

    existing_user_ids: set[str] = set()
    if user_ids_to_check:
        rows = session.exec(
            select(User.user_id).where(User.user_id.in_(user_ids_to_check))
        ).all()
        existing_user_ids = {r.lower() for r in rows}

    existing_emails: set[str] = set()
    if emails_to_check:
        rows = session.exec(
            select(User.email).where(User.email.in_(emails_to_check))
        ).all()
        existing_emails = {r.lower() for r in rows}

    created: list[StudentImportCreatedRow] = []
    errors: list[StudentImportErrorRow] = []
    seen_user_ids: set[str] = set()
    seen_emails: set[str] = set()

    for row_index, user_id, full_name, date_str, email in parsed_rows:
        try:
            (
                student,
                final_user_id,
                final_full_name,
                final_email,
                final_date,
                error_reason,
            ) = _validate_row(
                row_index,
                user_id,
                full_name,
                date_str,
                email,
                seen_user_ids,
                seen_emails,
                existing_user_ids,
                existing_emails,
            )
        except Exception as err:  # bảo vệ ngoại lệ không lường trước trong validate
            errors.append(
                StudentImportErrorRow(
                    row=row_index,
                    email=email or None,
                    date_of_birth=date_str or None,
                    reason=f"Lỗi không xác định: {err}",
                )
            )
            continue

        if error_reason is not None:
            errors.append(
                StudentImportErrorRow(
                    row=row_index,
                    email=final_email,
                    date_of_birth=final_date,
                    reason=error_reason,
                )
            )
            continue

        # Commit theo từng dòng: lỗi DB ở dòng này không ảnh hưởng dòng khác
        try:
            session.add(student)
            session.commit()
            session.refresh(student)
        except Exception as err:
            session.rollback()
            errors.append(
                StudentImportErrorRow(
                    row=row_index,
                    email=final_email,
                    date_of_birth=final_date,
                    reason=f"Lỗi khi lưu vào cơ sở dữ liệu: {err}",
                )
            )
            continue

        created.append(
            StudentImportCreatedRow(
                user_id=final_user_id,
                full_name=final_full_name,
                email=final_email,
                date_of_birth=final_date,
                temporary_password=password_from_date(student.date_of_birth),
            )
        )

    return StudentImportResponse(created=created, errors=errors)
