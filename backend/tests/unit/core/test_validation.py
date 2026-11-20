"""Validator email dùng chung: giá trị không phải chuỗi phải thành InvalidFormatError."""

import pytest

from app.core.exceptions import EmptyFieldError, InvalidFormatError
from app.core.utils.validation import _validate_email


@pytest.mark.parametrize("value", [123, 1.5, True, ["a@b.com"], {"a": 1}])
def test_validate_email_rejects_non_string(value):
    with pytest.raises(InvalidFormatError, match="Email không đúng định dạng"):
        _validate_email(value)


def test_validate_email_empty_still_raises_empty_field():
    with pytest.raises(EmptyFieldError):
        _validate_email("  ")


def test_validate_email_accepts_valid_string():
    assert _validate_email("a@st.utc2.edu.vn") == "a@st.utc2.edu.vn"
