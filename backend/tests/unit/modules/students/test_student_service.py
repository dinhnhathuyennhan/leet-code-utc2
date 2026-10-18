"""Test ``import_students``: import sinh viên từ file "DS lớp học phần".

File Excel được dựng bằng fixture ``class_list_xlsx`` (xem ``conftest.py``)
theo đúng bố cục file thật: phần đầu 10 hàng, tiêu đề ở hàng 11, dữ liệu từ
hàng 12, chân trang ở cuối. Vì vậy sinh viên thứ ``n`` nằm ở dòng ``11 + n``.
"""

import logging
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import select

from app.shared.excel import (
    EmptyExcelFileError,
    ExcelFileTooLargeError,
    InvalidExcelFormatError,
)
from app.core.security.passwords import verify_password
from app.core.dependencies import Role
from app.modules.students import service as student_service
from app.modules.students.service import import_students
from app.models import Class, User

# tests/unit/modules/<module>/ -> parents[3] = tests/
XLS_FIXTURE = Path(__file__).resolve().parents[3] / "support" / "fixtures" / "ds_lop_mau.xls"
SHEET = "IT1.001.3-1-26-CQ.67.CNTT"


def _row(n: int) -> int:
    """Số dòng Excel của sinh viên thứ ``n`` (bắt đầu từ 1) trong sheet mẫu."""
    return 11 + n


def _add_class(session, class_id: str = "CQ.67.CNTT") -> Class:
    class_type, course_number, department = class_id.split(".", 2)
    db_class = Class(
        class_id=class_id,
        type=class_type,
        course_number=int(course_number),
        department=department,
    )
    session.add(db_class)
    session.commit()
    return db_class


def _add_user(session, user_id: str, email: str, role_id: int = Role.STUDENT) -> User:
    user = User(
        user_id=user_id,
        full_name=f"Có sẵn {user_id}",
        email=email,
        hashed_password="placeholder",
        role_id=role_id,
    )
    session.add(user)
    session.commit()
    return user


def _users(session) -> dict[str, User]:
    return {user.user_id: user for user in session.exec(select(User)).all()}


def _fail_commit_at(session, monkeypatch, failing_call: int, error: Exception) -> None:
    """Cho lần gọi ``session.commit()`` thứ ``failing_call`` raise ``error``."""
    real_commit = session.commit
    calls = {"count": 0}

    def flaky_commit():
        calls["count"] += 1
        if calls["count"] == failing_call:
            raise error
        real_commit()

    monkeypatch.setattr(session, "commit", flaky_commit)


# ============================== HAPPY PATH ==============================


def test_import_creates_student_accounts(session, class_list_xlsx):
    contents = class_list_xlsx(
        {
            SHEET: [
                ("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT"),
                ("6751071002", "Trần Thị", "Bình", "CQ.67.CNTT"),
            ]
        }
    )

    response = import_students(session, contents, "ds.xlsx")

    assert [row.model_dump() for row in response.created] == [
        {
            "user_id": "6751071001",
            "full_name": "Nguyễn Văn An",
            "email": "6751071001@st.utc2.edu.vn",
            "class_id": "CQ.67.CNTT",
            "temporary_password": "6751071001",
        },
        {
            "user_id": "6751071002",
            "full_name": "Trần Thị Bình",
            "email": "6751071002@st.utc2.edu.vn",
            "class_id": "CQ.67.CNTT",
            "temporary_password": "6751071002",
        },
    ]
    assert response.skipped == []
    assert response.errors == []

    user = _users(session)["6751071001"]
    assert user.full_name == "Nguyễn Văn An"
    assert user.email == "6751071001@st.utc2.edu.vn"
    assert user.role_id == Role.STUDENT
    assert user.class_id == "CQ.67.CNTT"
    assert user.must_change_password is True
    assert user.date_of_birth is None
    assert user.token_version == 0
    # Mật khẩu tạm = MSSV, lưu dạng bcrypt chứ không lưu nguyên văn
    assert user.hashed_password != "6751071001"
    assert verify_password("6751071001", user.hashed_password)


def test_import_reads_xls_fixture(session):
    response = import_students(session, XLS_FIXTURE.read_bytes(), "ds_lop_mau.xls")

    # Sheet "Ghi chu" không có hàng tiêu đề nên bị bỏ qua, không báo lỗi
    assert [row.user_id for row in response.created] == [
        "6751071001",  # ô số trong .xls (6751071001.0) không bị dính ".0"
        "675107A002",
        "A6751071003",
    ]
    assert response.errors == []
    assert set(_users(session)) == {"6751071001", "675107A002", "A6751071003"}


def test_import_accepts_student_ids_with_letters(session, class_list_xlsx):
    contents = class_list_xlsx(
        {
            SHEET: [
                ("675107A095", "Lê", "Cường", "CQ.67.CNTT"),
                ("A6751071096", "Phạm", "Dũng", "CQ.67.CNTT"),
            ]
        }
    )

    response = import_students(session, contents, "ds.xlsx")

    assert [row.email for row in response.created] == [
        "675107A095@st.utc2.edu.vn",
        "A6751071096@st.utc2.edu.vn",
    ]
    assert verify_password("675107A095", _users(session)["675107A095"].hashed_password)


def test_import_stops_at_footer_and_ignores_extra_columns(session, class_list_xlsx):
    """Chân trang ("TP Hồ Chí Minh, ngày...", "Ghi chú: ...") không bị đọc thành sinh viên."""
    contents = class_list_xlsx({SHEET: [("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT")]})

    response = import_students(session, contents, "ds.xlsx")

    assert len(response.created) == 1
    assert response.errors == []
    assert len(_users(session)) == 1


def test_import_skips_rows_that_only_have_stt(session, class_list_xlsx):
    contents = class_list_xlsx(
        {
            SHEET: [
                ("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT"),
                (None, None, None, None),
                ("6751071003", "Lê", "Cường", "CQ.67.CNTT"),
            ]
        }
    )

    response = import_students(session, contents, "ds.xlsx")

    assert [row.user_id for row in response.created] == ["6751071001", "6751071003"]
    assert response.errors == []


def test_import_continues_after_blank_rows_inside_table(session, class_list_xlsx):
    """Dòng trống giữa bảng không được làm mất các SV phía sau."""
    contents = class_list_xlsx(
        {
            SHEET: [
                ("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT"),
                None,
                None,
                ("6751071002", "Trần Thị", "Bình", "CQ.67.CNTT"),
            ]
        }
    )

    response = import_students(session, contents, "ds.xlsx")

    assert [row.user_id for row in response.created] == ["6751071001", "6751071002"]
    assert response.errors == []
    assert set(_users(session)) == {"6751071001", "6751071002"}


def test_import_reads_row_with_missing_stt(session, class_list_xlsx):
    """Ô STT bị xoá hoặc gõ sai nhưng vẫn có MSSV thì vẫn là dòng sinh viên."""
    contents = class_list_xlsx(
        {
            SHEET: [
                ("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT"),
                ("6751071002", "Trần Thị", "Bình", "CQ.67.CNTT"),
                ("6751071003", "Lê", "Cường", "CQ.67.CNTT"),
            ]
        }
    )
    workbook = load_workbook(BytesIO(contents))
    workbook[SHEET].cell(row=_row(2), column=1).value = None  # xoá STT của SV thứ 2
    workbook[SHEET].cell(row=_row(3), column=1).value = "3a"  # STT gõ sai
    buffer = BytesIO()
    workbook.save(buffer)

    response = import_students(session, buffer.getvalue(), "ds.xlsx")

    assert [row.user_id for row in response.created] == [
        "6751071001",
        "6751071002",
        "6751071003",
    ]


def test_import_handles_single_full_name_column(session):
    """File chỉ có 1 cột "Họ tên" thì không được ghép nhầm ô "Lớp" vào tên."""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["STT", "MSSV", "Họ tên", "Lớp"])
    worksheet.append([1, 6751071001, "Nguyễn Văn An", "CQ.67.CNTT"])
    buffer = BytesIO()
    workbook.save(buffer)

    response = import_students(session, buffer.getvalue(), "ds.xlsx")

    assert response.created[0].full_name == "Nguyễn Văn An"
    assert response.created[0].class_id == "CQ.67.CNTT"


# ============================== LỚP HÀNH CHÍNH ==============================


def test_import_creates_missing_classes(session, class_list_xlsx):
    contents = class_list_xlsx(
        {
            SHEET: [
                ("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT"),
                ("6751071002", "Trần Thị", "Bình", "CQ.67.KTXDCTGT.2"),
                ("6751071003", "Lê", "Cường", "CQ.67.CLC.KTOTO"),
                ("6751071004", "Phạm", "Dũng", "CQ.67.XDDD&CN.1"),
                ("6751071005", "Võ", "Em", "CQ.67.TC-NH"),
                ("6751071006", "Đỗ", "Giang", "CQ.67.ĐK&TTĐSHĐ"),
            ]
        }
    )

    import_students(session, contents, "ds.xlsx")

    classes = {
        c.class_id: (c.type, c.course_number, c.department)
        for c in session.exec(select(Class)).all()
    }
    assert classes == {
        "CQ.67.CNTT": ("CQ", 67, "CNTT"),
        "CQ.67.KTXDCTGT.2": ("CQ", 67, "KTXDCTGT.2"),
        "CQ.67.CLC.KTOTO": ("CQ", 67, "CLC.KTOTO"),
        "CQ.67.XDDD&CN.1": ("CQ", 67, "XDDD&CN.1"),
        "CQ.67.TC-NH": ("CQ", 67, "TC-NH"),
        "CQ.67.ĐK&TTĐSHĐ": ("CQ", 67, "ĐK&TTĐSHĐ"),
    }


def test_import_does_not_duplicate_or_change_existing_class(session, class_list_xlsx):
    existing = Class(
        class_id="CQ.67.CNTT", type="Chính quy", course_number=67, department="Công nghệ thông tin"
    )
    session.add(existing)
    session.commit()
    contents = class_list_xlsx({SHEET: [("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT")]})

    import_students(session, contents, "ds.xlsx")

    classes = session.exec(select(Class)).all()
    assert len(classes) == 1
    assert classes[0].department == "Công nghệ thông tin"


def test_import_does_not_create_class_for_skipped_or_invalid_rows(session, class_list_xlsx):
    _add_user(session, "6751071001", "old@example.com")
    contents = class_list_xlsx(
        {
            SHEET: [
                ("6751071001", "Nguyễn Văn", "An", "CQ.67.KTXD"),  # đã có tài khoản
                ("67Đ1", "Trần Thị", "Bình", "CQ.67.QTKD"),  # MSSV sai
            ]
        }
    )

    import_students(session, contents, "ds.xlsx")

    assert session.exec(select(Class)).all() == []


@pytest.mark.parametrize(
    "class_id",
    [
        "CNTT",
        "CQ.K67.CNTT",
        "CQ..CNTT",
        "CQ.67.",
        "C" * 51,
        "CQ.\uff16\uff17.CNTT",  # "67" full-width: isdigit() là True nhưng int() lỗi
        "CQ.\u00b2\u2076.CNTT",  # "²⁶" (số mũ): tương tự
        "CQ.67.CNTT/1",  # ngành có "/": lớp sẽ không gọi được qua /classes/{class_id}
        "CQ.67.CN TT",
        "CQ.67..CNTT",
    ],
)
def test_import_rejects_invalid_class_id(session, class_list_xlsx, class_id):
    contents = class_list_xlsx({SHEET: [("6751071001", "Nguyễn Văn", "An", class_id)]})

    response = import_students(session, contents, "ds.xlsx")

    assert response.created == []
    assert len(response.errors) == 1
    assert response.errors[0].row == _row(1)
    assert "Mã lớp" in response.errors[0].reason
    assert session.exec(select(Class)).all() == []


# ============================== DÒNG LỖI ==============================


@pytest.mark.parametrize(
    ("student", "reason"),
    [
        ((None, "Nguyễn Văn", "An", "CQ.67.CNTT"), "Mã sinh viên không được trống"),
        (("   ", "Nguyễn Văn", "An", "CQ.67.CNTT"), "Mã sinh viên không được trống"),
        (("6" * 51, "Nguyễn Văn", "An", "CQ.67.CNTT"), "Mã sinh viên không được dài quá 50 ký tự"),
        (("67Đ1", "Nguyễn Văn", "An", "CQ.67.CNTT"), "Mã sinh viên chỉ được gồm chữ không dấu và số"),
        (("6751 071", "Nguyễn Văn", "An", "CQ.67.CNTT"), "Mã sinh viên chỉ được gồm chữ không dấu và số"),
        (("6751@071", "Nguyễn Văn", "An", "CQ.67.CNTT"), "Mã sinh viên chỉ được gồm chữ không dấu và số"),
        (("6751071001", None, None, "CQ.67.CNTT"), "Họ tên không được trống"),
        (("6751071001", "Nguyễn Văn", "An", None), "Mã lớp không được trống"),
    ],
)
def test_import_reports_invalid_row(session, class_list_xlsx, student, reason):
    contents = class_list_xlsx(
        {
            SHEET: [
                ("6751071099", "Hợp", "Lệ", "CQ.67.CNTT"),
                student,
            ]
        }
    )

    response = import_students(session, contents, "ds.xlsx")

    # Dòng sai không chặn dòng hợp lệ
    assert [row.user_id for row in response.created] == ["6751071099"]
    assert len(response.errors) == 1
    error = response.errors[0]
    assert error.sheet == SHEET
    assert error.row == _row(2)
    assert error.reason == reason


def test_import_reports_empty_student_id_as_none(session, class_list_xlsx):
    contents = class_list_xlsx({SHEET: [(None, "Nguyễn Văn", "An", "CQ.67.CNTT")]})

    response = import_students(session, contents, "ds.xlsx")

    assert response.errors[0].user_id is None


def test_import_with_only_invalid_rows_returns_errors_without_creating(session, class_list_xlsx):
    """Use-case E1: không có dòng nào hợp lệ thì không tạo gì, vẫn trả đủ lỗi."""
    contents = class_list_xlsx(
        {
            SHEET: [
                (None, "Nguyễn Văn", "An", "CQ.67.CNTT"),
                ("6751071002", "Trần Thị", "Bình", "CNTT"),
            ]
        }
    )

    response = import_students(session, contents, "ds.xlsx")

    assert response.created == []
    assert response.skipped == []
    assert [error.row for error in response.errors] == [_row(1), _row(2)]
    assert _users(session) == {}
    assert session.exec(select(Class)).all() == []


def test_import_sorts_errors_by_sheet_then_row(session, class_list_xlsx):
    _add_user(session, "other", "6751071003@st.utc2.edu.vn", role_id=Role.TEACHER)
    contents = class_list_xlsx(
        {
            "Lop1": [
                ("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT"),
                ("6751071003", "Lê", "Cường", "CQ.67.CNTT"),  # lỗi email (bước đối chiếu DB)
                (None, "Thiếu", "Mã", "CQ.67.CNTT"),  # lỗi dòng (bước bốc tách)
            ],
            "Lop2": [
                ("6751071001", "Khác", "Tên", "CQ.67.CNTT"),  # lỗi trùng (bước gộp)
            ],
        }
    )

    response = import_students(session, contents, "ds.xlsx")

    assert [(error.sheet, error.row) for error in response.errors] == [
        ("Lop1", _row(2)),
        ("Lop1", _row(3)),
        ("Lop2", _row(1)),
    ]


# ============================== TRÙNG LẶP ==============================


def test_import_skips_students_that_already_have_accounts(session, class_list_xlsx):
    _add_user(session, "6751071001", "6751071001@st.utc2.edu.vn")
    contents = class_list_xlsx(
        {
            SHEET: [
                ("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT"),
                ("6751071002", "Trần Thị", "Bình", "CQ.67.CNTT"),
            ]
        }
    )

    response = import_students(session, contents, "ds.xlsx")

    assert [row.user_id for row in response.created] == ["6751071002"]
    assert [row.model_dump() for row in response.skipped] == [
        {
            "sheet": SHEET,
            "row": _row(1),
            "user_id": "6751071001",
            "reason": "Sinh viên đã có tài khoản",
        }
    ]
    assert response.errors == []
    # Tài khoản cũ giữ nguyên, không bị ghi đè
    assert _users(session)["6751071001"].full_name == "Có sẵn 6751071001"


def test_import_twice_skips_everyone_the_second_time(session, class_list_xlsx):
    contents = class_list_xlsx(
        {
            SHEET: [
                ("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT"),
                ("6751071002", "Trần Thị", "Bình", "CQ.67.CNTT"),
            ]
        }
    )
    import_students(session, contents, "ds.xlsx")

    response = import_students(session, contents, "ds.xlsx")

    assert response.created == []
    assert [row.user_id for row in response.skipped] == ["6751071001", "6751071002"]
    assert response.errors == []


def test_import_matches_existing_student_id_exactly(session, class_list_xlsx):
    """MSSV có chữ hoa đã có trong DB phải vào skipped, không lọt xuống commit lỗi SQL.

    Và vì so khớp phân biệt hoa/thường, "sv001" khác "SV001" nên được tạo mới.
    """
    _add_user(session, "SV001", "sv-cu@example.com")
    contents = class_list_xlsx(
        {
            SHEET: [
                ("SV001", "Nguyễn Văn", "An", "CQ.67.CNTT"),
                ("sv001", "Trần Thị", "Bình", "CQ.67.CNTT"),
            ]
        }
    )

    response = import_students(session, contents, "ds.xlsx")

    assert [row.user_id for row in response.skipped] == ["SV001"]
    assert [row.user_id for row in response.created] == ["sv001"]
    assert response.errors == []


def test_import_reports_email_already_used_by_another_account(session, class_list_xlsx):
    _add_user(session, "gv01", "6751071001@st.utc2.edu.vn", role_id=Role.TEACHER)
    contents = class_list_xlsx({SHEET: [("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT")]})

    response = import_students(session, contents, "ds.xlsx")

    assert response.created == []
    assert response.skipped == []
    assert response.errors[0].user_id == "6751071001"
    assert response.errors[0].reason == (
        "Email 6751071001@st.utc2.edu.vn đã được dùng cho tài khoản khác"
    )
    assert set(_users(session)) == {"gv01"}


def test_import_merges_same_student_across_sheets(session, class_list_xlsx):
    """Một SV học nhiều lớp học phần xuất hiện ở nhiều sheet → chỉ tạo 1 lần."""
    student = ("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT")
    contents = class_list_xlsx(
        {
            "Lop1": [student],
            "Lop2": [("6751071002", "Trần Thị", "Bình", "CQ.67.CNTT"), student],
        }
    )

    response = import_students(session, contents, "ds.xlsx")

    assert [row.user_id for row in response.created] == ["6751071001", "6751071002"]
    assert response.errors == []
    assert len(_users(session)) == 2


def test_import_reports_same_student_id_with_different_info(session, class_list_xlsx):
    contents = class_list_xlsx(
        {
            "Lop1": [("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT")],
            "Lop2": [("6751071001", "Nguyễn Văn", "Ân", "CQ.67.CNTT")],
        }
    )

    response = import_students(session, contents, "ds.xlsx")

    # Lần xuất hiện đầu tiên vẫn được tạo, lần sau khác thông tin thì báo lỗi
    assert [row.full_name for row in response.created] == ["Nguyễn Văn An"]
    assert len(response.errors) == 1
    error = response.errors[0]
    assert (error.sheet, error.row, error.user_id) == ("Lop2", _row(1), "6751071001")
    assert error.reason == (
        f"Mã sinh viên trùng với dòng {_row(1)} (sheet Lop1) nhưng khác họ tên hoặc lớp"
    )


# ============================== ĐỊNH DẠNG FILE ==============================


def test_import_ignores_sheets_without_header(session, class_list_xlsx):
    contents = class_list_xlsx(
        {
            "Huong dan": None,
            SHEET: [("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT")],
        }
    )

    response = import_students(session, contents, "ds.xlsx")

    assert len(response.created) == 1
    assert response.errors == []


def test_import_rejects_file_without_class_list_header(session, class_list_xlsx):
    contents = class_list_xlsx({"Huong dan": None})

    with pytest.raises(InvalidExcelFormatError):
        import_students(session, contents, "ds.xlsx")


def test_import_rejects_old_five_column_template(session):
    """Mẫu cũ (user_id, full_name, date_of_birth, email, class_id) không còn được nhận."""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["user_id", "full_name", "date_of_birth", "email", "class_id"])
    worksheet.append(["sv001", "A", "31/08/2005", "a@x.vn", "CQ.67.CNTT"])
    buffer = BytesIO()
    workbook.save(buffer)

    with pytest.raises(InvalidExcelFormatError):
        import_students(session, buffer.getvalue(), "ds.xlsx")


@pytest.mark.parametrize(
    ("contents", "filename", "error"),
    [
        (b"abc", "ds.csv", InvalidExcelFormatError),
        (b"not a zip", "ds.xlsx", InvalidExcelFormatError),
        (b"garbage" * 100, "ds.xls", InvalidExcelFormatError),
    ],
)
def test_import_rejects_unreadable_file(session, contents, filename, error):
    with pytest.raises(error):
        import_students(session, contents, filename)


def test_import_rejects_empty_workbook(session):
    buffer = BytesIO()
    Workbook().save(buffer)

    with pytest.raises(EmptyExcelFileError):
        import_students(session, buffer.getvalue(), "ds.xlsx")


def test_import_rejects_file_over_byte_limit(session, class_list_xlsx, monkeypatch):
    monkeypatch.setattr(student_service, "MAX_IMPORT_FILE_BYTES", 1024)
    contents = class_list_xlsx({SHEET: [("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT")]})

    with pytest.raises(ExcelFileTooLargeError):
        import_students(session, contents, "ds.xlsx")


# ============================== GIỚI HẠN SỐ SINH VIÊN ==============================


def test_import_rejects_more_than_max_students(session, class_list_xlsx):
    students = [
        (f"67510{i:05d}", "Sinh", f"Viên {i}", "CQ.67.CNTT")
        for i in range(student_service.MAX_IMPORT_STUDENTS + 1)
    ]
    contents = class_list_xlsx({SHEET: students})

    with pytest.raises(ExcelFileTooLargeError):
        import_students(session, contents, "ds.xlsx")

    # Bị chặn trước khi ghi DB: không có SV hay lớp nào được tạo
    assert _users(session) == {}
    assert session.exec(select(Class)).all() == []


def test_import_counts_limit_after_merging_duplicates(session, class_list_xlsx, monkeypatch):
    monkeypatch.setattr(student_service, "MAX_IMPORT_STUDENTS", 2)
    students = [
        ("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT"),
        ("6751071002", "Trần Thị", "Bình", "CQ.67.CNTT"),
    ]
    contents = class_list_xlsx({"Lop1": students, "Lop2": students, "Lop3": students})

    response = import_students(session, contents, "ds.xlsx")

    assert len(response.created) == 2


# ============================== LỖI DB GIỮA CHỪNG ==============================


def test_import_keeps_other_students_when_one_commit_hits_integrity_error(
    session, class_list_xlsx, monkeypatch
):
    """E3: lỗi ở 1 SV không làm mất SV khác; lý do lỗi không lộ câu SQL."""
    _add_class(session)  # lớp đã có → commit đầu tiên là SV thứ nhất
    contents = class_list_xlsx(
        {
            SHEET: [
                ("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT"),
                ("6751071002", "Trần Thị", "Bình", "CQ.67.CNTT"),
                ("6751071003", "Lê", "Cường", "CQ.67.CNTT"),
            ]
        }
    )
    sql_error = IntegrityError(
        "INSERT INTO user (hashed_password) VALUES ('$2b$12$secret')", {}, Exception("dup")
    )
    _fail_commit_at(session, monkeypatch, failing_call=2, error=sql_error)

    response = import_students(session, contents, "ds.xlsx")

    assert [row.user_id for row in response.created] == ["6751071001", "6751071003"]
    assert len(response.errors) == 1
    error = response.errors[0]
    assert (error.row, error.user_id) == (_row(2), "6751071002")
    assert error.reason == "Mã sinh viên hoặc email đã tồn tại"
    assert "INSERT" not in error.reason
    assert "$2b$" not in error.reason
    assert set(_users(session)) == {"6751071001", "6751071003"}


def test_import_logs_and_hides_unexpected_db_error(
    session, class_list_xlsx, monkeypatch, caplog
):
    _add_class(session)
    contents = class_list_xlsx(
        {
            SHEET: [
                ("6751071001", "Nguyễn Văn", "An", "CQ.67.CNTT"),
                ("6751071002", "Trần Thị", "Bình", "CQ.67.CNTT"),
            ]
        }
    )
    db_error = OperationalError(
        "INSERT INTO user (hashed_password) VALUES ('$2b$12$secret')", {}, Exception("down")
    )
    _fail_commit_at(session, monkeypatch, failing_call=1, error=db_error)

    with caplog.at_level(logging.ERROR, logger=student_service.__name__):
        response = import_students(session, contents, "ds.xlsx")

    assert [row.user_id for row in response.created] == ["6751071002"]
    assert response.errors[0].reason == "Không lưu được dòng này, vui lòng thử lại"
    assert "$2b$" not in response.errors[0].reason
    # Chi tiết lỗi chỉ nằm trong log phía server
    assert "6751071001" in caplog.text
