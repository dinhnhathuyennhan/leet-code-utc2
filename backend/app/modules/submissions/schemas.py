from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PendingSubmissionResponse(BaseModel):
    id: int
    course_id: str
    lesson_id: int
    problem_id: int
    student_name: str
    student_code: str
    course_code: str
    session_label: str
    topic: str
    judge_kind: str
    judge_label: str
    issue: str


class PendingSubmissionListResponse(BaseModel):
    items: list[PendingSubmissionResponse]
    total: int
    counts: dict[str, int]


class SubmissionTestcaseResponse(BaseModel):
    id: int
    input: Any
    expected_output: Any
    is_sample: bool


class SubmissionDetailResponse(BaseModel):
    id: int
    problem_id: int
    student_name: str
    student_code: str
    class_id: str | None
    course_code: str
    course_name: str
    session_label: str
    problem_code: str | None
    problem_title: str
    problem_description: str
    problem_constraints: str
    problem_level: str
    problem_function_name: str | None
    language: str
    submitted_code: str
    status: str
    compile_output: str | None
    feedback: str | None
    manual_score: float | None
    passed_count: int
    total_testcases: int
    submitted_datetime: datetime
    testcases: list[SubmissionTestcaseResponse]


class SubmissionUpdateRequest(BaseModel):
    feedback: str | None = Field(default=None, max_length=10000)
    status: str | None = Field(default=None, max_length=50)
    manual_score: float | None = Field(default=None, ge=0, le=10)
