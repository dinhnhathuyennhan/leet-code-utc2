from typing import Any, Literal

from pydantic import BaseModel, field_validator

from app.core import config
from app.core.exceptions import EmptyFieldError, InvalidFormatError

MAX_CODE_BYTES = 64 * 1024
Language = Literal["python", "c", "cpp", "java", "javascript"]


class CodeRequest(BaseModel):
    language: str
    code: str

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        language = v.strip()
        if language not in config.LANGUAGES:
            supported = ", ".join(config.LANGUAGES)
            raise InvalidFormatError(f"language không được hỗ trợ, chọn một trong: {supported}")
        return language

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.strip():
            raise EmptyFieldError("code không được để trống")
        if len(v.encode("utf-8")) > config.MAX_CODE_BYTES:
            raise InvalidFormatError(f"Code vượt quá {config.MAX_CODE_BYTES // 1024}KB")
        return v


class RunCaseResponse(BaseModel):
    index: int
    status: str
    input: Any
    expected_output: Any
    actual_output: Any | None
    stderr: str | None
    time: float | None


class RunResponse(BaseModel):
    status: str
    compile_output: str | None
    cases: list[RunCaseResponse]
    review_token: str | None = None


class SubmitAcceptedResponse(BaseModel):
    submission_id: int
    status: str


class SubmissionResultResponse(BaseModel):
    submission_id: int
    status: str
    passed_count: int
    total_testcases: int
    compile_output: str | None
