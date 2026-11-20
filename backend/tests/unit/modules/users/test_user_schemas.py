"""Test schema UpdateUserRequest.

Validator raise ``AppError`` nên lỗi giữ nguyên ``error_code`` (không bị pydantic
gói thành ``ValidationError``).
"""

import pytest

from app.core.exceptions import EmptyFieldError, InvalidFormatError
from app.modules.users.schemas import UpdateUserRequest, student_email


@pytest.mark.parametrize(
    ("code", "error"),
    [
        ("123", InvalidFormatError),
        ("68510710011", InvalidFormatError),
        ("68510710a1", InvalidFormatError),
        ("  ", EmptyFieldError),
    ],
)
def test_update_request_rejects_bad_student_code(code, error):
    with pytest.raises(error):
        UpdateUserRequest(student_code=code)


def test_update_request_rejects_wrong_email_domain():
    with pytest.raises(InvalidFormatError, match=r"st\.utc2\.edu\.vn"):
        UpdateUserRequest(email="a@example.com")


def test_update_request_rejects_blank_full_name():
    with pytest.raises(EmptyFieldError):
        UpdateUserRequest(full_name="   ")


def test_update_request_rejects_non_string_full_name():
    with pytest.raises(InvalidFormatError):
        UpdateUserRequest(full_name=123)


def test_update_request_collapses_full_name_spaces():
    assert UpdateUserRequest(full_name="  Nguyễn   Văn \t A ").full_name == "Nguyễn Văn A"


def test_update_request_rejects_non_string_class_id():
    with pytest.raises(InvalidFormatError):
        UpdateUserRequest(class_id=123)


def test_update_request_rejects_blank_class_id():
    with pytest.raises(EmptyFieldError):
        UpdateUserRequest(class_id="  ")


def test_update_request_allows_all_none():
    data = UpdateUserRequest(full_name=None, email=None, student_code=None, class_id=None)

    assert data.model_dump() == {
        "full_name": None,
        "email": None,
        "student_code": None,
        "class_id": None,
    }


def test_update_request_ignores_unknown_fields():
    data = UpdateUserRequest(**{"role_id": 1, "is_active": False, "full_name": "A"})

    assert not hasattr(data, "role_id")
    assert data.model_dump(exclude_unset=True) == {"full_name": "A"}


def test_student_email_uses_student_domain():
    assert student_email("6851071001") == "6851071001@st.utc2.edu.vn"
