"""Test quy ước mã lớp (``parse_class_id``, ``build_class_id``) và ``CreateClassRequest``.

Validator raise ``AppError`` nên lỗi bay thẳng ra ngoài (không bị pydantic gói
thành ``ValidationError``). Chỉ lỗi sai kiểu dữ liệu do chính pydantic kiểm tra
(vd ``course_number = "abc"``) mới ra ``ValidationError``.
"""

import pytest
from pydantic import ValidationError

from app.core.exceptions import EmptyFieldError, InvalidFormatError
from app.schemas.classroom import (
    CLASS_ID_MAX_LEN,
    ClassIdParts,
    CreateClassRequest,
    build_class_id,
    parse_class_id,
)


def _request(class_type="CQ", course_number=67, department="CNTT") -> CreateClassRequest:
    return CreateClassRequest(
        type=class_type, course_number=course_number, department=department
    )


# ---------- parse_class_id (dùng cho import) ----------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("CQ.67.CNTT", ClassIdParts("CQ.67.CNTT", "CQ", 67, "CNTT")),
        # tách tại 2 dấu chấm đầu tiên: phần ngành giữ được dấu chấm
        ("CQ.67.KTXDCTGT.2", ClassIdParts("CQ.67.KTXDCTGT.2", "CQ", 67, "KTXDCTGT.2")),
        ("  CQ.67.CNTT  ", ClassIdParts("CQ.67.CNTT", "CQ", 67, "CNTT")),
    ],
)
def test_parse_class_id_splits_parts(value, expected):
    assert parse_class_id(value) == expected


@pytest.mark.parametrize("value", [None, "", "   "])
def test_parse_class_id_empty_raises(value):
    with pytest.raises(EmptyFieldError, match="Mã lớp không được trống"):
        parse_class_id(value)


@pytest.mark.parametrize(
    "value",
    [
        "CQ67CNTT",  # không có dấu chấm
        "CQ.67",  # thiếu ngành
        "CQ..CNTT",  # thiếu khoá
        ".67.CNTT",  # thiếu hệ
        "CQ.67.",  # ngành rỗng
        "CQ.K67.CNTT",  # khoá không phải số
        "CQ.\uff16\uff17.CNTT",  # khoá là chữ số full-width
        "CQ.\u00b2\u2076.CNTT",  # khoá là chữ số mũ
    ],
)
def test_parse_class_id_wrong_format_raises(value):
    with pytest.raises(InvalidFormatError, match="không đúng dạng"):
        parse_class_id(value)


def test_parse_class_id_too_long_raises():
    class_id = "CQ.67." + "X" * (CLASS_ID_MAX_LEN - 5)

    with pytest.raises(InvalidFormatError, match="không được dài quá 50 ký tự"):
        parse_class_id(class_id)


def test_parse_class_id_exactly_max_length_is_valid():
    class_id = "CQ.67." + "X" * (CLASS_ID_MAX_LEN - 6)

    assert parse_class_id(class_id).class_id == class_id


# ---------- build_class_id và tính ngược chiều với parse_class_id ----------


def test_build_class_id_joins_parts():
    assert build_class_id("CQ", 67, "CNTT") == "CQ.67.CNTT"


@pytest.mark.parametrize(
    ("class_type", "course_number", "department"),
    [("CQ", 67, "CNTT"), ("VLVH", 1, "KTXDCTGT.2"), ("cq", 100, "A.B.C")],
)
def test_parse_reverses_build(class_type, course_number, department):
    """Lớp tạo bằng tay (build) luôn tách lại đúng khi đi qua import (parse)."""
    class_id = build_class_id(class_type, course_number, department)

    assert parse_class_id(class_id) == (class_id, class_type, course_number, department)


# ---------- CreateClassRequest (body của POST /classes) ----------


def test_create_request_builds_class_id():
    request = _request()

    assert request.class_id == "CQ.67.CNTT"
    assert request.model_dump() == {"type": "CQ", "course_number": 67, "department": "CNTT"}


def test_create_request_strips_text_and_parses_course_number_string():
    request = _request("  CQ ", "067", " KTXDCTGT.2 ")

    assert request.class_id == "CQ.67.KTXDCTGT.2"
    assert (request.type, request.course_number, request.department) == ("CQ", 67, "KTXDCTGT.2")


def test_create_request_ignores_class_id_from_client():
    request = CreateClassRequest(
        type="CQ", course_number=67, department="CNTT", class_id="HACK"
    )

    assert request.class_id == "CQ.67.CNTT"


def test_create_request_keeps_letter_case():
    """Mã lớp phân biệt hoa/thường, lưu đúng như gửi."""
    assert _request("cq").class_id == "cq.67.CNTT"


@pytest.mark.parametrize("class_type", [None, "", "   "])
def test_create_request_empty_type_raises(class_type):
    with pytest.raises(EmptyFieldError, match="Hệ đào tạo không được trống"):
        _request(class_type=class_type)


@pytest.mark.parametrize(
    "class_type",
    [
        "C.Q",  # dấu chấm là ký tự ngăn cách trong mã lớp
        "CQ1",
        "C Q",
        "CQ-",
        "CQ@",
        "CQ_",
        "Đ",  # chữ có dấu
        "\uff23\uff31",  # chữ full-width
        "\u00aa",  # ký tự isalpha() nhưng không phải chữ ASCII
    ],
)
def test_create_request_type_must_be_ascii_letters(class_type):
    with pytest.raises(InvalidFormatError, match="Hệ đào tạo chỉ được gồm chữ cái không dấu"):
        _request(class_type=class_type)


@pytest.mark.parametrize("department", [None, "", "   "])
def test_create_request_empty_department_raises(department):
    with pytest.raises(EmptyFieldError, match="Ngành không được trống"):
        _request(department=department)


@pytest.mark.parametrize("course_number", [0, -1, "0", True, False])
def test_create_request_course_number_must_be_positive(course_number):
    with pytest.raises(InvalidFormatError, match="Khoá phải là số nguyên dương"):
        _request(course_number=course_number)


@pytest.mark.parametrize("course_number", ["abc", None, 6.5])
def test_create_request_course_number_wrong_type_is_pydantic_error(course_number):
    with pytest.raises(ValidationError):
        _request(course_number=course_number)


def test_create_request_missing_field_is_pydantic_error():
    with pytest.raises(ValidationError):
        CreateClassRequest(type="CQ", course_number=67)


def test_create_request_class_id_too_long_raises():
    # "CQ.67." dài 6 ký tự, cộng ngành 45 ký tự = 51
    with pytest.raises(InvalidFormatError, match="không được dài quá 50 ký tự"):
        _request(department="X" * (CLASS_ID_MAX_LEN - 5))


def test_create_request_class_id_exactly_max_length_is_valid():
    request = _request(department="X" * (CLASS_ID_MAX_LEN - 6))

    assert len(request.class_id) == CLASS_ID_MAX_LEN
