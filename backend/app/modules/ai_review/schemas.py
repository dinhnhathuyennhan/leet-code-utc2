from pydantic import BaseModel, ConfigDict, Field


class AIReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=15000)
    language: str = Field(default="python", min_length=1, max_length=30)


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
