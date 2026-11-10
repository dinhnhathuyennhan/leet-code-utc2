from pydantic import BaseModel, Field, field_validator

from app.core.utils.validation import AppEmailStr


class AddStudentToCourseResponse(BaseModel):
    enrollment_id: int
    course_id: str
    student_id: str                     # UUID của user (User.user_id)
    student_code: str | None = None     # MSSV (User.student_code)


class AddStudentToCourseRequest(BaseModel):
    """Truyền MỘT trong hai: ``student_id`` hoặc ``student_code`` (MSSV).

    ``student_id`` nhận UUID; để tương thích form FE hiện tại, giá trị không phải
    UUID được tra như MSSV.

    Không validate ở đây: service tự kiểm tra và raise ``AppError`` để lỗi đi
    qua Global Exception Handler với đúng ``error_code``.
    """

    student_id: str | None = None      # UUID của user
    student_code: str | None = None    # MSSV 10 chữ số

    @field_validator("student_code", mode="before")
    @classmethod
    def coerce_numeric_student_code(cls, value):
        # MSSV có thể được gửi dạng số JSON (vd đọc từ Excel); chỉ ép sang str,
        # việc kiểm tra định dạng để service làm (raise AppError).
        if isinstance(value, int) and not isinstance(value, bool):
            return str(value)
        return value


class AddClassToCourseRequest(BaseModel):
    class_id: str = Field(..., min_length=1, max_length=50)


class AddClassToCourseResponse(BaseModel):
    course_id: str
    class_id: str
    added_count: int
    skipped_count: int
    added_student_ids: list[str]


class GetStudentListResponse(BaseModel):
    enrollment_id: int
    student_id: str                     # UUID của user (User.user_id)
    student_code: str | None = None     # MSSV (User.student_code)
    full_name: str
    email: AppEmailStr
