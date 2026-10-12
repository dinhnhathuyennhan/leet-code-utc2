"""Service xử lý nghiệp vụ liên quan tới sinh viên.

Hiện tại gồm:
    - ``import_students``: đọc file "Danh sách lớp học phần" (.xls/.xlsx)
      của phòng đào tạo và tạo hàng loạt tài khoản sinh viên.

Mẫu file (mỗi sheet là một lớp học phần):
    - Hàng tiêu đề nằm trong 20 hàng đầu, có các cột ``STT``,
      ``Mã sinh viên``, ``Họ và tên`` (gộp 2 ô: họ đệm + tên), ``Lớp``.
      Các hàng phía trên (tên trường, học kỳ...) và các cột khác
      (điểm danh, ghi chú) bị bỏ qua.
    - Dữ liệu bắt đầu ngay dưới hàng tiêu đề. Dòng sinh viên là dòng có ô
      STT là số hoặc có MSSV; dòng trống thì bỏ qua; gặp dòng có chữ nhưng
      không có STT lẫn MSSV (phần chân trang "Người lập biểu"...) thì dừng.

Quy tắc:
    - Email tự sinh ``{MSSV}@st.utc2.edu.vn``, mật khẩu tạm = MSSV.
    - Lớp hành chính chưa có thì tự tạo từ mã lớp (vd ``CQ.67.CNTT``).
    - MSSV đã có tài khoản → ``skipped``; dòng sai → ``errors``.
    - Commit theo từng sinh viên: lỗi DB ở một dòng không làm mất các
      sinh viên đã tạo trước đó (đặc tả E3).
"""

import logging
import os
import unicodedata
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select

from app.core.excel import (
    ExcelFileTooLargeError,
    ExcelSheet,
    ExcelWorkbook,
    InvalidExcelFormatError,
    read_workbook,
)
from app.core.exceptions import AppError
from app.core.password import hash_password
from app.dependencies import Role
from app.schemas.classroom import parse_class_id
from app.schemas.student import (
    StudentImportCreatedRow,
    StudentImportErrorRow,
    StudentImportResponse,
    StudentImportRow,
    StudentImportSkippedRow,
)
from app.schemas.user import student_temp_password
from models import Class, User

logger = logging.getLogger(__name__)

STUDENT_EMAIL_DOMAIN = "st.utc2.edu.vn"
MAX_IMPORT_STUDENTS = 500
MAX_IMPORT_FILE_BYTES = 5 * 1024 * 1024
HASH_WORKERS = min(8, os.cpu_count() or 1)
HEADER_SEARCH_ROWS = 20

# Tên cột chuẩn → các cách viết tiêu đề được chấp nhận (đã strip + lower)
HEADER_ALIASES = {
    "stt": ("stt",),
    "user_id": ("mã sinh viên", "ma sinh vien", "mssv"),
    "full_name": ("họ và tên", "ho va ten", "họ tên", "ho ten"),
    "class_id": ("lớp", "lop"),
}


def import_students(
    session: Session, contents: bytes, filename: str
) -> StudentImportResponse:
    """Import danh sách sinh viên từ file danh sách lớp học phần."""
    workbook = read_workbook(contents, filename, MAX_IMPORT_FILE_BYTES)

    rows, errors = _extract_rows(workbook)
    students = _dedupe_students(rows, errors)
    if len(students) > MAX_IMPORT_STUDENTS:
        raise ExcelFileTooLargeError(
            f"File có {len(students)} sinh viên, vượt quá giới hạn "
            f"{MAX_IMPORT_STUDENTS} sinh viên mỗi lần import"
        )

    to_create, skipped = _split_existing(session, students, errors)
    _create_missing_classes(session, to_create)
    created = _save_students(session, to_create, errors)

    sheet_order = {sheet.name: index for index, sheet in enumerate(workbook.sheets)}
    errors.sort(key=lambda error: (sheet_order.get(error.sheet, 0), error.row))
    return StudentImportResponse(created=created, skipped=skipped, errors=errors)


# ---------- Bốc tách dữ liệu từ JSON của file Excel ----------


def _extract_rows(
    workbook: ExcelWorkbook,
) -> tuple[list[StudentImportRow], list[StudentImportErrorRow]]:
    """Duyệt mọi sheet, lấy các dòng sinh viên trong bảng của từng sheet."""
    rows: list[StudentImportRow] = []
    errors: list[StudentImportErrorRow] = []
    found_header = False

    for sheet in workbook.sheets:
        header = _find_header(sheet)
        if header is None:
            continue  # sheet không theo mẫu (vd sheet ghi chú) thì bỏ qua
        found_header = True
        header_index, columns = header

        # "Họ và tên" gộp 2 ô: chỉ lấy thêm ô bên phải khi tiêu đề của ô đó trống
        name_col = columns["full_name"]
        name_has_two_cells = _cell(sheet.rows[header_index], name_col + 1) == ""

        for index in range(header_index + 1, len(sheet.rows)):
            row = sheet.rows[index]
            user_id = _cell(row, columns["user_id"])
            if not _cell(row, columns["stt"]).isdigit() and not user_id:
                if any(row):
                    break  # hết bảng, tới phần chân trang
                continue  # dòng trống giữa bảng: bỏ qua, đọc tiếp

            name_parts = [_cell(row, name_col)]
            if name_has_two_cells:
                name_parts.append(_cell(row, name_col + 1))
            full_name = " ".join(part for part in name_parts if part)
            class_id = _cell(row, columns["class_id"])
            if not (user_id or full_name or class_id):
                continue  # dòng chỉ có STT, chưa điền gì

            try:
                rows.append(
                    StudentImportRow(
                        sheet=sheet.name,
                        row=index + 1,
                        user_id=user_id,
                        full_name=full_name,
                        class_id=class_id,
                    )
                )
            except AppError as err:
                errors.append(
                    StudentImportErrorRow(
                        sheet=sheet.name,
                        row=index + 1,
                        user_id=user_id or None,
                        reason=err.message,
                    )
                )

    if not found_header:
        raise InvalidExcelFormatError(
            "File không đúng mẫu danh sách lớp: không tìm thấy hàng tiêu đề "
            "có các cột STT, Mã sinh viên, Họ và tên, Lớp"
        )
    return rows, errors


def _find_header(sheet: ExcelSheet) -> tuple[int, dict[str, int]] | None:
    """Tìm hàng tiêu đề, trả về ``(chỉ số hàng, {tên cột chuẩn: chỉ số cột})``."""
    for index, row in enumerate(sheet.rows[:HEADER_SEARCH_ROWS]):
        columns: dict[str, int] = {}
        for col, cell in enumerate(row):
            label = unicodedata.normalize("NFC", cell).strip().lower()
            for key, aliases in HEADER_ALIASES.items():
                if label in aliases and key not in columns:
                    columns[key] = col
        if len(columns) == len(HEADER_ALIASES):
            return index, columns
    return None


def _cell(row: list[str], index: int) -> str:
    """Lấy ô thứ ``index``; hàng ngắn hơn (đã bỏ ô trống cuối) thì trả ``""``."""
    return row[index] if index < len(row) else ""


def _dedupe_students(
    rows: list[StudentImportRow], errors: list[StudentImportErrorRow]
) -> list[StudentImportRow]:
    """Gộp MSSV xuất hiện nhiều lần (một SV học nhiều lớp học phần).

    Cùng họ tên và lớp → giữ lần đầu. Khác thông tin → dòng sau bị lỗi.
    """
    unique: dict[str, StudentImportRow] = {}
    for row in rows:
        first = unique.get(row.user_id)
        if first is None:
            unique[row.user_id] = row
        elif (first.full_name, first.class_id) != (row.full_name, row.class_id):
            errors.append(
                StudentImportErrorRow(
                    sheet=row.sheet,
                    row=row.row,
                    user_id=row.user_id,
                    reason=(
                        f"Mã sinh viên trùng với dòng {first.row} (sheet {first.sheet}) "
                        "nhưng khác họ tên hoặc lớp"
                    ),
                )
            )
    return list(unique.values())


# ---------- Đối chiếu với DB và lưu ----------


def _student_email(user_id: str) -> str:
    return f"{user_id}@{STUDENT_EMAIL_DOMAIN}"


def _split_existing(
    session: Session,
    students: list[StudentImportRow],
    errors: list[StudentImportErrorRow],
) -> tuple[list[StudentImportRow], list[StudentImportSkippedRow]]:
    """Tách SV đã có tài khoản (skipped) và SV bị trùng email (errors)."""
    if not students:
        return [], []

    user_ids = [student.user_id for student in students]
    emails = [_student_email(user_id) for user_id in user_ids]
    existing_user_ids = set(
        session.exec(select(User.user_id).where(User.user_id.in_(user_ids))).all()
    )
    taken_emails = set(
        session.exec(select(User.email).where(User.email.in_(emails))).all()
    )

    to_create: list[StudentImportRow] = []
    skipped: list[StudentImportSkippedRow] = []
    for student in students:
        if student.user_id in existing_user_ids:
            skipped.append(
                StudentImportSkippedRow(
                    sheet=student.sheet,
                    row=student.row,
                    user_id=student.user_id,
                    reason="Sinh viên đã có tài khoản",
                )
            )
        elif _student_email(student.user_id) in taken_emails:
            errors.append(
                StudentImportErrorRow(
                    sheet=student.sheet,
                    row=student.row,
                    user_id=student.user_id,
                    reason=(
                        f"Email {_student_email(student.user_id)} "
                        "đã được dùng cho tài khoản khác"
                    ),
                )
            )
        else:
            to_create.append(student)
    return to_create, skipped


def _create_missing_classes(session: Session, students: list[StudentImportRow]) -> None:
    """Tạo các lớp hành chính chưa có, vd ``CQ.67.CNTT`` → CQ / 67 / CNTT."""
    class_ids = {student.class_id for student in students}
    if not class_ids:
        return
    existing = set(
        session.exec(select(Class.class_id).where(Class.class_id.in_(class_ids))).all()
    )
    missing = sorted(class_ids - existing)
    if not missing:
        return

    for class_id in missing:
        # StudentImportRow đã kiểm tra mã lớp nên parse ở đây không raise
        parts = parse_class_id(class_id)
        session.add(
            Class(
                class_id=parts.class_id,
                type=parts.type,
                course_number=parts.course_number,
                department=parts.department,
            )
        )
    session.commit()


def _save_students(
    session: Session,
    students: list[StudentImportRow],
    errors: list[StudentImportErrorRow],
) -> list[StudentImportCreatedRow]:
    """Băm mật khẩu song song rồi lưu từng sinh viên."""
    passwords = [student_temp_password(student.user_id) for student in students]
    # bcrypt nhả GIL khi băm nên các thread chạy song song thật sự
    with ThreadPoolExecutor(max_workers=HASH_WORKERS) as pool:
        hashed_passwords = list(pool.map(hash_password, passwords))

    created: list[StudentImportCreatedRow] = []
    for student, password, hashed in zip(
        students, passwords, hashed_passwords, strict=True
    ):
        email = _student_email(student.user_id)
        session.add(
            User(
                user_id=student.user_id,
                full_name=student.full_name,
                email=email,
                hashed_password=hashed,
                must_change_password=True,
                role_id=Role.STUDENT,
                class_id=student.class_id,
            )
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            errors.append(_save_error(student, "Mã sinh viên hoặc email đã tồn tại"))
            continue
        except SQLAlchemyError:
            session.rollback()
            logger.exception("Không lưu được sinh viên %s khi import", student.user_id)
            errors.append(
                _save_error(student, "Không lưu được dòng này, vui lòng thử lại")
            )
            continue

        created.append(
            StudentImportCreatedRow(
                user_id=student.user_id,
                full_name=student.full_name,
                email=email,
                class_id=student.class_id,
                temporary_password=password,
            )
        )
    return created


def _save_error(student: StudentImportRow, reason: str) -> StudentImportErrorRow:
    return StudentImportErrorRow(
        sheet=student.sheet, row=student.row, user_id=student.user_id, reason=reason
    )
