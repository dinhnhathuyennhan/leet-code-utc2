from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.exceptions import EmptyFieldError, InvalidFormatError
from app.modules.problems.schemas import ProblemTestcaseResponse


class LessonCreateRequest(BaseModel):
    lesson_name: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: date
    problem_ids: list[int] = Field(default_factory=list)

    @field_validator("lesson_name")
    @classmethod
    def validate_lesson_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise EmptyFieldError("lesson_name không được để trống")
        return value

    @model_validator(mode="after")
    def validate_lesson_dates(self) -> "LessonCreateRequest":
        if self.start_date > self.end_date:
            raise InvalidFormatError("start_date phải trước hoặc bằng end_date")
        return self


class LessonUpdateRequest(BaseModel):
    lesson_name: str | None = Field(default=None, min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    problem_ids: list[int] | None = None  # chỉ THÊM bài vào buổi; muốn gỡ bài dùng DELETE problem

    @field_validator("lesson_name")
    @classmethod
    def validate_optional_lesson_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise EmptyFieldError("lesson_name không được để trống")
        return value

    @model_validator(mode="after")
    def validate_optional_dates(self) -> "LessonUpdateRequest":
        if self.start_date is not None and self.end_date is not None and self.start_date > self.end_date:
            raise InvalidFormatError("start_date phải trước hoặc bằng end_date")
        return self


class LessonProblemAttachRequest(BaseModel):
    problem_ids: list[int]

    @field_validator("problem_ids")
    @classmethod
    def validate_problem_ids(cls, value: list[int]) -> list[int]:
        if not value:
            raise InvalidFormatError("problem_ids không được để trống")
        return value


class LessonReorderRequest(BaseModel):
    order: list[int]


class LessonDuplicateRequest(BaseModel):
    new_start_date: date
    new_end_date: date
    target_course_id: str | None = Field(default=None, min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_lesson_dates(self) -> "LessonDuplicateRequest":
        if self.new_start_date > self.new_end_date:
            raise InvalidFormatError("start_date phải trước hoặc bằng end_date")
        return self


class LessonStatsResponse(BaseModel):
    submission_rate: float
    completed_students: int
    avg_score: float
    score_diff: str
    ast_cases: int
    ast_similarity: str


class LessonAlertResponse(BaseModel):
    missing_students: int
    problem_name: str
    problem_code: str
    deadline_text: str


class LessonExerciseResponse(BaseModel):
    id: int
    order: int
    title: str
    function_name: str | None
    report: str | None
    level: str
    description: str
    constraints: str
    hint: str | None
    complexity: str | None
    time_limit_seconds: int
    total_number_testcase: int
    starter_code: str
    starter_codes: dict[str, str] = Field(default_factory=dict)
    submitted_count: int | None = None
    testcases: list[ProblemTestcaseResponse]


class LessonDetailResponse(BaseModel):
    id: int
    order: int
    title: str
    course_code: str
    course_name: str
    start_date: date
    end_date: date
    deadline_notice: str
    submitted_students: int | None = None
    total_students: int | None = None
    stats: LessonStatsResponse | None = None
    alert: LessonAlertResponse | None = None
    exercises: list[LessonExerciseResponse]
