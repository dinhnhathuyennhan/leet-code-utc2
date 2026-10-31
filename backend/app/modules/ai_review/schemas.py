from pydantic import BaseModel, Field, field_validator


class AIReviewRequest(BaseModel):
    code: str = Field(min_length=1, max_length=15000)
    # language được nhúng thẳng vào prompt: chỉ cho tên ngôn ngữ (chữ, số, + # . _ -
    # và khoảng trắng) để không chèn được dòng chỉ thị mới vào prompt.
    language: str = Field(
        default="python",
        min_length=1,
        max_length=30,
        pattern=r"^[A-Za-z0-9+#._ -]+$",
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Mã nguồn không được để trống")
        return value

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        return value.strip()


class AdminPreviewReviewRequest(AIReviewRequest):
    preview_token: str = Field(min_length=1)


class AIConnectionResponse(BaseModel):
    connected: bool
    model: str
    model_available: bool


class OptimizationResult(BaseModel):
    is_optimizable: bool
    suggestion: str
    expected_time_complexity: str
    expected_space_complexity: str


class AIReviewResponse(BaseModel):
    time_complexity: str
    space_complexity: str
    complexity_explanation: str
    issues: list[str]
    optimization: OptimizationResult
    summary: str
