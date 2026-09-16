from io import BytesIO

from openpyxl import Workbook
from sqlalchemy import select

from app.core.password import verify_password
from app.services.student_service import (
    EmptyExcelFileError,
    ExcelFileTooLargeError,
    InvalidExcelFormatError,
    import_students,
)
from models import User


def make_excel_bytes(headers: list[str], rows: list[list]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_import_students_success(session):
    contents = make_excel_bytes(
        ["full_name", "email"],
        [
            ["Nguyễn Văn A", "a@example.com"],
            ["Nguyễn Văn B", "b@example.com"],
        ],
    )

    response = import_students(session, contents, "students.xlsx")

    assert len(response.created) == 2
    assert response.errors == []
    assert response.created[0].email == "a@example.com"
    assert response.created[0].user_id == "a@example.com"
    assert response.created[0].temporary_password

    users = session.exec(select(User)).scalars().all()
    assert len(users) == 2
    for student, row in zip(users, response.created, strict=True):
        assert verify_password(row.temporary_password, student.hashed_password)
        assert student.role_id == 3
        assert student.must_change_password is True


def test_import_students_best_effort_skips_invalid_rows(session):
    contents = make_excel_bytes(
        ["full_name", "email"],
        [
            ["Nguyễn Văn A", "a@example.com"],
            ["", "empty@example.com"],
            ["Nguyễn Văn C", "not-an-email"],
            ["Nguyễn Văn D", "a@example.com"],
            ["Nguyễn Văn E", "e@example.com"],
        ],
    )

    response = import_students(session, contents, "students.xlsx")

    assert len(response.created) == 2
    assert response.created[0].email == "a@example.com"
    assert response.created[1].email == "e@example.com"
    assert len(response.errors) == 3
    error_rows = [err.row for err in response.errors]
    assert error_rows == [3, 4, 5]
    error_reasons = [err.reason for err in response.errors]
    assert "Họ tên không được trống" in error_reasons
    assert "Email không đúng định dạng" in error_reasons
    assert "Email đã xuất hiện trước đó trong file" in error_reasons


def test_import_students_all_invalid_returns_201_with_empty_created(session):
    contents = make_excel_bytes(
        ["full_name", "email"],
        [
            ["", "x@example.com"],
            ["Người B", "not-an-email"],
        ],
    )

    response = import_students(session, contents, "students.xlsx")

    assert response.created == []
    assert len(response.errors) == 2
    assert len(session.exec(select(User)).scalars().all()) == 0


def test_import_students_skips_existing_emails(session):
    session.add(
        User(
            user_id="existing@example.com",
            full_name="Existing",
            email="existing@example.com",
            hashed_password="x",
            role_id=3,
        )
    )
    session.commit()

    contents = make_excel_bytes(
        ["full_name", "email"],
        [
            ["Nguyễn Văn A", "a@example.com"],
            ["Người Cũ", "existing@example.com"],
        ],
    )

    response = import_students(session, contents, "students.xlsx")

    assert len(response.created) == 1
    assert response.created[0].email == "a@example.com"
    assert len(response.errors) == 1
    assert response.errors[0].reason == "Email đã tồn tại trong hệ thống"
    assert response.errors[0].email == "existing@example.com"


def test_import_students_invalid_extension_raises(session):
    contents = make_excel_bytes(["full_name", "email"], [["A", "a@example.com"]])

    with __import__("pytest").raises(InvalidExcelFormatError):
        import_students(session, contents, "students.csv")


def test_import_students_missing_columns_raises(session):
    contents = make_excel_bytes(["full_name"], [["Nguyễn Văn A"]])

    with __import__("pytest").raises(InvalidExcelFormatError):
        import_students(session, contents, "students.xlsx")


def test_import_students_empty_file_raises(session):
    contents = make_excel_bytes(["full_name", "email"], [])

    with __import__("pytest").raises(EmptyExcelFileError):
        import_students(session, contents, "students.xlsx")


def test_import_students_too_many_rows_raises(session):
    rows = [["Người thứ " + str(i), f"user{i}@example.com"] for i in range(501)]
    contents = make_excel_bytes(["full_name", "email"], rows)

    with __import__("pytest").raises(ExcelFileTooLargeError):
        import_students(session, contents, "students.xlsx")
