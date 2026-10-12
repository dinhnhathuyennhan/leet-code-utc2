from datetime import date, datetime
from app.core.datetime_utils import as_utc

from pydantic import BaseModel, Field, field_validator, model_validator
from app.core.exceptions import EmptyFieldError, InvalidFormatError

# SỬA: Giữ riêng trạng thái đã nộp để phân biệt điểm 0 với bài chưa làm.
# Không thêm cột vào models.py; đây chỉ là contract tổng hợp cho màn hình bảng điểm.
class GradeScoreResponse(BaseModel):
    value: float | None
    submitted: bool = False


class CourseGradeRowResponse(BaseModel):
    student_id: str
    full_name: str
    class_id: str | None
    overall_score: float | None
    session_scores: dict[str, list[GradeScoreResponse]]
