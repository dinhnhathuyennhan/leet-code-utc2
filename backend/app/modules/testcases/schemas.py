from typing import Any

from pydantic import BaseModel, field_validator


class TestcaseResponse(BaseModel):
    id: int
    input: Any
    expected_output: Any
    is_sample: bool
    input_type: str
    expected_output_type: str


class TestcaseListResponse(BaseModel):
    testcases: list[TestcaseResponse]
    total_sample: int
    total_hidden: int


class TestcaseUpdateRequest(BaseModel):

    input: Any = None
    expected_output: Any = None
    is_sample: bool | None = None


class TestcaseBatchRequest(BaseModel):
    testcase_ids: list[int]
    is_sample: bool

    @field_validator("testcase_ids")
    @classmethod
    def validate_testcase_ids(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("testcase_ids không được để trống")
        return v


class TestcasePreviewRequest(BaseModel):
    # list[Any]: từng item được kiểm tra thủ công trong service để trả về
    # danh sách `errors` theo vị trí, thay vì để pydantic 422 cả request.
    testcases: list[Any]

    @field_validator("testcases")
    @classmethod
    def validate_testcases(cls, v: list[Any]) -> list[Any]:
        if not v:
            raise ValueError("testcases không được để trống")
        return v


class PreviewErrorResponse(BaseModel):
    index: int  # 1-based
    message: str


class PreviewWarningResponse(BaseModel):
    message: str


class TestcasePreviewResponse(BaseModel):
    valid: bool
    count: int
    sample_count: int
    hidden_count: int
    errors: list[PreviewErrorResponse]
    warnings: list[PreviewWarningResponse]
