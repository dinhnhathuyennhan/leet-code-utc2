from pydantic import BaseModel, ConfigDict, Field


class AIReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=15000)
    # language được nhúng thẳng vào prompt: chỉ cho tên ngôn ngữ (chữ, số, + # . _ -
    # và khoảng trắng) để không chèn được dòng chỉ thị mới vào prompt.
    language: str = Field(
        default="python",
        min_length=1,
        max_length=30,
        pattern=r"^[A-Za-z0-9+#._ -]+$",
    )


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
