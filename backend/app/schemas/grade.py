
from pydantic import BaseModel

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
