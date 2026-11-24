from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.core.exceptions import InvalidFormatError


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
    # Kết quả chấm của test này; None với bài nộp cũ (chưa lưu kết quả từng test)
    status: str | None = None
    time: float | None = None


class TestcaseResultResponse(BaseModel):
    """Kết quả một testcase theo thứ tự chấm (1-based), KHÔNG kèm dữ liệu test.

    Dùng để hiển thị đúng/sai của cả test ẩn mà không lộ input/expected_output.
    Danh sách rỗng nghĩa là bài nộp được chấm trước khi hệ thống lưu kết quả từng test.
    """

    index: int
    is_sample: bool
    status: str
    time: float | None = None


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
    testcase_results: list[TestcaseResultResponse] = []


class SubmissionUpdateRequest(BaseModel):
    """Giáo viên chỉ được nhận xét và ghi đè điểm; trạng thái chấm do máy chấm quyết định."""

    feedback: str | None = Field(default=None, max_length=10000)
    manual_score: float | None = Field(default=None, ge=0, le=10)

    @model_validator(mode="before")
    @classmethod
    def reject_status(cls, data):
        # Báo lỗi rõ ràng thay vì lặng lẽ bỏ qua field lạ: client cũ gửi `status`
        # phải biết thao tác không có tác dụng. Muốn chấm lại dùng POST .../regrade.
        if isinstance(data, dict) and data.get("status") is not None:
            raise InvalidFormatError(
                "Không thể sửa trạng thái bài nộp: trạng thái do máy chấm quyết định"
            )
        return data


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
    """Testcase MẪU (có dữ liệu) trong kết quả chấm của sinh viên."""

    id: int
    input: Any
    expected_output: Any
    is_sample: bool
    status: str | None = None
    time: float | None = None


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
    testcase_results: list[TestcaseResultResponse] = []
