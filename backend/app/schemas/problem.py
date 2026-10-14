from datetime import datetime

from pydantic import BaseModel, Field


class ProblemTestcaseResponse(BaseModel):
    id: int
    input: str
    expected_output: str
    is_sample: bool


# Contract chi tiết bài tập để nút "Xem chi tiết" mở được dữ liệu thật.
class ProblemDetailResponse(BaseModel):
    id: int
    lesson_id: int
    course_id: str
    code: str | None            # lấy từ Problem.report
    title: str
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
    testcases: list[ProblemTestcaseResponse]


# Contract cập nhật nội dung bài tập theo đúng các thuộc tính đang có trong models.py.
# Không thêm trường điểm tối đa vì database hiện không có cột tương ứng.
class ProblemTestcaseUpdate(BaseModel):
    input: str
    expected_output: str
    is_sample: bool = False
    input_type: str = "stdin"
    expected_output_type: str = "stdout"


class ProblemUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    constraints: str | None = None
    level: str | None = None
    hint: str | None = None
    complexity: str | None = None
    time_limit_seconds: int | None = Field(default=None, ge=1)
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    starter_code: str | None = None
    testcases: list[ProblemTestcaseUpdate] | None = None
