import json
import keyword
import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.exceptions import EmptyFieldError, InvalidFormatError
from app.core.utils.datetime_utils import require_offset

SUPPORTED_STARTER_LANGUAGES = ("python", "c", "cpp", "java")
_FUNCTION_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_C_FAMILY_AND_JAVA_KEYWORDS = {
    "alignas", "alignof", "and", "and_eq", "asm", "assert", "auto", "bitand",
    "bitor", "bool", "break", "byte", "case", "catch", "char", "char16_t",
    "char32_t", "class", "compl", "concept", "const", "consteval", "constexpr",
    "constinit", "continue", "co_await", "co_return", "co_yield", "decltype",
    "default", "delete", "do", "double", "else", "enum", "explicit", "export",
    "extends", "extern", "false", "final", "finally", "float", "for", "friend",
    "goto", "if", "implements", "import", "instanceof", "int", "interface",
    "long", "module", "mutable", "namespace", "native", "new", "noexcept", "not",
    "not_eq", "nullptr", "operator", "or", "or_eq", "package", "permits", "private",
    "protected", "public", "record", "register", "reinterpret_cast", "requires",
    "return", "sealed", "short", "signed", "sizeof", "static", "static_assert",
    "static_cast", "strictfp", "struct", "super", "switch", "synchronized", "template",
    "this", "throw", "throws", "transient", "true", "try", "typedef", "typeid",
    "typename", "union", "unsigned", "using", "var", "virtual", "void", "volatile",
    "wchar_t", "while", "xor", "xor_eq",
}


def validate_problem_schedule(start_datetime: datetime, end_datetime: datetime) -> None:
    if start_datetime >= end_datetime:
        raise InvalidFormatError("start_datetime phải trước end_datetime.")


def validate_datetime_offset(value: datetime, field_name: str) -> datetime:
    return require_offset(value, field_name)

def validate_function_name(value: str) -> str:
    if (
        not _FUNCTION_IDENTIFIER.fullmatch(value)
        or keyword.iskeyword(value)
        or value in _C_FAMILY_AND_JAVA_KEYWORDS
    ):
        raise InvalidFormatError(
            "function_name phải là identifier ASCII hợp lệ, không phải từ khóa của Python, C/C++ hoặc Java"
        )
    return value


def validate_json_value(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise InvalidFormatError("Testcase phải chứa giá trị JSON hợp lệ") from error
    return value
class ProblemTestcaseResponse(BaseModel):
    id: int
    input: Any
    expected_output: Any
    is_sample: bool


# Contract chi tiết bài tập để nút "Xem chi tiết" mở được dữ liệu thật.
class ProblemDetailResponse(BaseModel):
    id: int
    lesson_id: int | None
    course_id: str | None
    code: str | None            # lấy từ Problem.report
    title: str
    function_name: str | None
    description: str
    constraints: str
    level: str
    hint: str | None
    complexity: str | None
    time_limit_seconds: int
    total_number_testcase: int
    start_datetime: datetime
    end_datetime: datetime
    starter_code: str
    starter_codes: dict[str, str] = Field(default_factory=dict)
    # None với Sinh viên: số bài nộp chỉ dành cho Giáo viên/Admin.
    submitted_count: int | None = None
    testcases: list[ProblemTestcaseResponse]


# Contract cập nhật nội dung bài tập theo đúng các thuộc tính đang có trong models.py.
# Không thêm trường điểm tối đa vì database hiện không có cột tương ứng.
class ProblemTestcaseUpdate(BaseModel):
    input: list[Any]
    expected_output: Any
    is_sample: bool = False

    @field_validator("input")
    @classmethod
    def validate_input_json(cls, value: list[Any]) -> list[Any]:
        return validate_json_value(value)

    @field_validator("expected_output")
    @classmethod
    def validate_output_json(cls, value: Any) -> Any:
        return validate_json_value(value)


class ProblemCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    function_name: str = Field(min_length=1, max_length=100)
    description: str
    constraints: str
    level: Literal["easy", "medium", "hard"]
    time_limit_seconds: int = Field(ge=1)
    starter_codes: dict[str, str] = Field(min_length=4)
    start_datetime: datetime
    end_datetime: datetime
    hint: str | None = None
    complexity: str | None = None
    testcases: list[ProblemTestcaseUpdate] = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise EmptyFieldError("title không được để trống")
        return value

    @field_validator("function_name")
    @classmethod
    def validate_function_name_field(cls, value: str) -> str:
        return validate_function_name(value.strip())

    @field_validator("level", mode="before")
    @classmethod
    def validate_level(cls, value: object) -> object:
        if value not in ("easy", "medium", "hard"):
            raise InvalidFormatError("level chỉ được nhận một trong các giá trị: easy, medium, hard")
        return value

    @field_validator("start_datetime", "end_datetime")
    @classmethod
    def validate_local_schedule_datetime(cls, value: datetime, info) -> datetime:
        return validate_datetime_offset(value, info.field_name)

    @field_validator("starter_codes")
    @classmethod
    def validate_starter_codes(cls, value: dict[str, str]) -> dict[str, str]:
        if set(value) != set(SUPPORTED_STARTER_LANGUAGES) or any(not code.strip() for code in value.values()):
            raise InvalidFormatError("starter_codes phải có code không rỗng cho python, c, cpp và java")
        return value

    @model_validator(mode="after")
    def validate_datetime_range(self) -> "ProblemCreateRequest":
        validate_problem_schedule(self.start_datetime, self.end_datetime)
        return self


class ProblemListItemResponse(BaseModel):
    id: int
    code: str | None
    title: str
    level: str
    lesson_id: int | None
    total_number_testcase: int


class ProblemListResponse(BaseModel):
    items: list[ProblemListItemResponse]
    total: int
    page: int
    page_size: int


class ProblemUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    function_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    constraints: str | None = None
    level: str | None = None
    hint: str | None = None
    complexity: str | None = None
    report: str | None = Field(default=None, max_length=255)
    time_limit_seconds: int | None = Field(default=None, ge=1)
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    starter_code: str | None = None  # legacy Python-only clients
    starter_codes: dict[str, str] | None = None
    testcases: list[ProblemTestcaseUpdate] | None = Field(default=None, min_length=1)

    @field_validator("title")
    @classmethod
    def validate_optional_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise EmptyFieldError("title không được để trống")
        return value

    @field_validator("function_name")
    @classmethod
    def validate_optional_function_name(cls, value: str | None) -> str | None:
        return None if value is None else validate_function_name(value.strip())

    @field_validator("level", mode="before")
    @classmethod
    def validate_optional_level(cls, value: object) -> object:
        if value is None:
            return None
        if value not in ("easy", "medium", "hard"):
            raise InvalidFormatError("level chỉ được nhận một trong các giá trị: easy, medium, hard")
        return value

    @field_validator("starter_codes")
    @classmethod
    def validate_optional_starter_codes(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None
        if set(value) != set(SUPPORTED_STARTER_LANGUAGES) or any(not code.strip() for code in value.values()):
            raise InvalidFormatError("starter_codes phải có code không rỗng cho python, c, cpp và java")
        return value

    @field_validator("start_datetime", "end_datetime")
    @classmethod
    def validate_optional_local_schedule_datetime(cls, value: datetime | None, info) -> datetime | None:
        return None if value is None else validate_datetime_offset(value, info.field_name)

    @model_validator(mode="after")
    def require_templates_when_renaming_function(self) -> "ProblemUpdateRequest":
        if self.function_name is not None and self.starter_codes is None:
            raise InvalidFormatError("Khi đổi function_name, cần gửi starter_codes cho mọi ngôn ngữ")
        return self
