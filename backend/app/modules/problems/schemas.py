import json
import keyword
import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.exceptions import EmptyFieldError, InvalidFormatError
from app.core.utils.datetime_utils import require_offset

SUPPORTED_STARTER_LANGUAGES = ("python", "c", "cpp", "java", "javascript")
FUNCTION_HARNESS_LANGUAGES = ("python", "c", "cpp", "javascript")
MIN_SAMPLE_TESTCASES = 3
MIN_HIDDEN_TESTCASES = 5
MIN_PROBLEM_TESTCASES = 10
MAX_PROBLEM_TESTCASES = 50
_FUNCTION_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_C_FAMILY_AND_JAVA_KEYWORDS = {
    "alignas", "alignof", "and", "and_eq", "asm", "assert", "async", "await", "auto", "bitand",
    "bitor", "bool", "break", "byte", "case", "catch", "char", "char16_t",
    "char32_t", "class", "compl", "concept", "const", "consteval", "constexpr",
    "constinit", "continue", "co_await", "co_return", "co_yield", "decltype",
    "debugger", "default", "delete", "do", "double", "else", "enum", "explicit", "export",
    "extends", "extern", "false", "final", "finally", "float", "for", "friend",
    "function", "goto", "if", "implements", "import", "instanceof", "int", "interface",
    "long", "module", "mutable", "namespace", "native", "new", "noexcept", "not",
    "let", "not_eq", "null", "nullptr", "of", "operator", "or", "or_eq", "package", "permits", "private",
    "protected", "public", "record", "register", "reinterpret_cast", "requires",
    "return", "sealed", "short", "signed", "sizeof", "static", "static_assert",
    "static_cast", "strictfp", "struct", "super", "switch", "synchronized", "template",
    "this", "throw", "throws", "transient", "true", "try", "typeof", "typedef", "typeid",
    "typename", "union", "unsigned", "using", "var", "virtual", "void", "volatile",
    "wchar_t", "while", "with", "xor", "xor_eq", "yield",
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
            "function_name phải là identifier ASCII hợp lệ, không phải từ khóa của Python, C/C++ hoặc JavaScript"
        )
    return value


def validate_json_value(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise InvalidFormatError("Testcase phải chứa giá trị JSON hợp lệ") from error
    return value


def validate_testcase_coverage(testcases: list[Any]) -> list[Any]:
    if len(testcases) < MIN_PROBLEM_TESTCASES:
        raise InvalidFormatError(
            f"Problem cần ít nhất {MIN_PROBLEM_TESTCASES} testcase tổng cộng"
        )
    if len(testcases) > MAX_PROBLEM_TESTCASES:
        raise InvalidFormatError(
            f"Problem chỉ được có tối đa {MAX_PROBLEM_TESTCASES} testcase"
        )
    sample_count = sum(
        bool(testcase.get("is_sample", False) if isinstance(testcase, dict) else testcase.is_sample)
        for testcase in testcases
    )
    hidden_count = len(testcases) - sample_count
    if sample_count < MIN_SAMPLE_TESTCASES:
        raise InvalidFormatError(
            f"Problem cần ít nhất {MIN_SAMPLE_TESTCASES} testcase mẫu (is_sample=true)"
        )
    if hidden_count < MIN_HIDDEN_TESTCASES:
        raise InvalidFormatError(
            f"Problem cần ít nhất {MIN_HIDDEN_TESTCASES} hidden testcase (is_sample=false)"
        )
    return testcases
class ProblemTestcaseResponse(BaseModel):
    id: int
    input: Any
    expected_output: Any
    is_sample: bool
    input_type: str
    expected_output_type: str


# Contract chi tiết bài tập để nút "Xem chi tiết" mở được dữ liệu thật.
class ProblemDetailResponse(BaseModel):
    id: int
    lesson_id: int | None
    course_id: str | None
    code: str | None            # giá trị của Problem.report (mã tùy chọn)
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
    supported_languages: list[str] = Field(default_factory=list)


# Contract cập nhật nội dung bài tập theo đúng các thuộc tính đang có trong models.py.
# Không thêm trường điểm tối đa vì database hiện không có cột tương ứng.
class ProblemTestcaseUpdate(BaseModel):
    input: Any
    expected_output: Any
    is_sample: bool = False


def validate_problem_testcase_mode(
    testcases: list[ProblemTestcaseUpdate], function_name: str | None,
) -> list[ProblemTestcaseUpdate]:
    """Function problems use JSON arguments; stdin/stdout problems use text."""
    for index, testcase in enumerate(testcases, start=1):
        if function_name is None:
            if not isinstance(testcase.input, str) or not isinstance(testcase.expected_output, str):
                raise InvalidFormatError(
                    f"Testcase #{index} của bài stdin/stdout cần input và expected_output dạng chuỗi"
                )
        else:
            if not isinstance(testcase.input, list):
                raise InvalidFormatError(
                    f"Testcase #{index} của bài chấm theo hàm cần input là mảng tham số JSON"
                )
            validate_json_value(testcase.input)
            validate_json_value(testcase.expected_output)
    return testcases


class AdminTestcaseMutation(BaseModel):
    input: Any
    expected_output: Any
    is_sample: bool = False
    input_type: Literal["json_args", "stdin"] = "json_args"
    expected_output_type: Literal["json", "stdout"] = "json"

    @model_validator(mode="after")
    def validate_format(self) -> "AdminTestcaseMutation":
        if (self.input_type, self.expected_output_type) == ("stdin", "stdout"):
            if not isinstance(self.input, str) or not isinstance(self.expected_output, str):
                raise ValueError("Testcase stdin/stdout cần input và output dạng chuỗi")
        elif (self.input_type, self.expected_output_type) == ("json_args", "json"):
            if not isinstance(self.input, list):
                raise ValueError("Input testcase JSON phải là mảng tham số")
            validate_json_value(self.input)
            validate_json_value(self.expected_output)
        else:
            raise ValueError("Định dạng input và output testcase không khớp")
        return self


class ProblemCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    report: str | None = Field(default=None, max_length=255)
    function_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str
    constraints: str
    level: Literal["easy", "medium", "hard"]
    time_limit_seconds: int = Field(ge=1)
    starter_codes: dict[str, str] = Field(default_factory=dict)
    start_datetime: datetime
    end_datetime: datetime
    hint: str | None = None
    complexity: str | None = None
    testcases: list[ProblemTestcaseUpdate] = Field(
        min_length=MIN_PROBLEM_TESTCASES, max_length=MAX_PROBLEM_TESTCASES
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise EmptyFieldError("title không được để trống")
        return value

    @field_validator("report")
    @classmethod
    def normalize_report(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("description", "constraints")
    @classmethod
    def validate_required_text(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise EmptyFieldError(f"{info.field_name} không được để trống")
        return value

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

    @field_validator("function_name")
    @classmethod
    def validate_function_name_field(cls, value: str | None) -> str | None:
        return None if value is None else validate_function_name(value.strip())

    @model_validator(mode="after")
    def validate_datetime_range(self) -> "ProblemCreateRequest":
        from app.modules.submissions.judge0.harness import validate_starter_codes  # import muộn để tránh vòng
        validate_starter_codes(self.function_name, self.starter_codes)
        validate_problem_schedule(self.start_datetime, self.end_datetime)
        validate_problem_testcase_mode(self.testcases, self.function_name)
        validate_testcase_coverage(self.testcases)
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


class ProblemImportItemResponse(BaseModel):
    id: int
    code: str | None = None
    title: str
    total_number_testcase: int


class ProblemImportResponse(BaseModel):
    created_count: int
    problems: list[ProblemImportItemResponse]


class ProblemImportIssueResponse(BaseModel):
    index: int | None = None
    code: str | None = None
    message: str


class ProblemImportPreviewResponse(BaseModel):
    valid: bool
    problem_count: int
    ready_problem_count: int
    testcase_count: int
    sample_testcase_count: int
    hidden_testcase_count: int
    issues: list[ProblemImportIssueResponse]



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
    testcases: list[ProblemTestcaseUpdate] | None = Field(
        default=None, min_length=MIN_PROBLEM_TESTCASES, max_length=MAX_PROBLEM_TESTCASES
    )

    @field_validator("title")
    @classmethod
    def validate_optional_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise EmptyFieldError("title không được để trống")
        return value

    @field_validator("report")
    @classmethod
    def normalize_optional_report(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("description", "constraints")
    @classmethod
    def validate_optional_required_text(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise EmptyFieldError(f"{info.field_name} không được để trống")
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

    @field_validator("start_datetime", "end_datetime")
    @classmethod
    def validate_optional_local_schedule_datetime(cls, value: datetime | None, info) -> datetime | None:
        return None if value is None else validate_datetime_offset(value, info.field_name)

class ProblemBankUpdateRequest(ProblemUpdateRequest):
    """Update contract for a source problem that is not attached to a lesson."""
    pass
