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
    status: str
    manual_score: float | None = None
    passed_count: int = 0
    total_testcases: int = 0


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
    student_name: str
    student_code: str
    class_id: str | None
    course_code: str
    course_name: str
    session_label: str
    problem_code: str | None
    problem_title: str
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


# ─── Sinh viên: xem lịch sử nộp bài và kết quả chấm ─────────────────────────────


class StudentSubmissionResponse(BaseModel):
    """Một dòng trong lịch sử nộp bài của sinh viên."""

    id: int
    problem_id: int
    problem_code: str | None
    problem_title: str
    course_id: str
    course_name: str
    lesson_id: int
    session_label: str
    language: str
    status: str
    passed_count: int
    total_testcases: int
    submitted_datetime: datetime


class StudentSubmissionListResponse(BaseModel):
    items: list[StudentSubmissionResponse]
    total: int
    counts: dict[str, int]


class StudentSubmissionTestcaseResponse(BaseModel):
    id: int
    input: Any
    expected_output: Any
    is_sample: bool


class StudentSubmissionDetailResponse(BaseModel):
    """Chi tiết bài nộp + kết quả chấm, dành cho sinh viên xem."""

    id: int
    problem_id: int
    problem_code: str | None
    problem_title: str
    course_id: str
    course_name: str
    lesson_id: int
    session_label: str
    language: str
    submitted_code: str
    status: str
    compile_output: str | None
    feedback: str | None
    passed_count: int
    total_testcases: int
    submitted_datetime: datetime
    testcases: list[StudentSubmissionTestcaseResponse]
