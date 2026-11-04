from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Giới hạn độ dài từng phần đưa vào prompt. Tổng (system prompt + đề + code +
# phần model sinh ra) phải nằm trong OLLAMA_NUM_CTX, nếu không Ollama cắt đầu
# prompt (model đọc thiếu) hoặc cắt giữa JSON (parse lỗi).
MAX_REVIEW_CODE_CHARS = 15000
MAX_PROBLEM_TEXT_CHARS = 2000
MAX_CONSTRAINTS_CHARS = 500

#: Ngôn ngữ của nội dung review. Khớp `Locale` ("vi" | "en") ở frontend.
Locale = Literal["vi", "en"]


class AIReviewRequest(BaseModel):
    """Dữ liệu nội bộ để dựng prompt, lấy từ bài nộp trong DB (không phải request body)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=MAX_REVIEW_CODE_CHARS)
    # language được nhúng thẳng vào prompt: chỉ cho tên ngôn ngữ (chữ, số, + # . _ -
    # và khoảng trắng) để không chèn được dòng chỉ thị mới vào prompt.
    language: str = Field(
        default="python",
        min_length=1,
        max_length=30,
        pattern=r"^[A-Za-z0-9+#._ -]+$",
    )
    problem_title: str = ""
    problem_description: str = ""
    constraints: str = ""
    # Ngôn ngữ mong muốn của phần văn xuôi trong kết quả. Mặc định "vi" để
    # request cũ (không gửi locale) vẫn chạy như trước.
    locale: Locale = "vi"
    # True = code tuỳ ý do client gửi lên (`POST /ai/review`), không phải bài
    # nộp đã pass testcase. Dùng để service chọn prompt trung tính (không nói
    # "đã pass ALL testcases"), vì code lúc đó chưa chắc đã được chấm.
    free_form: bool = False


class AIReviewRequestBody(BaseModel):
    """Body tuỳ chọn của endpoint review.

    Chỉ có `locale`: code / ngôn ngữ / đề bài luôn lấy từ DB theo `submission_id`
    nên client không thể đổi nội dung được review. Body rỗng (client cũ) dùng
    mặc định "vi".
    """

    model_config = ConfigDict(extra="ignore")

    locale: Locale = "vi"


class AIReviewFreeFormRequest(BaseModel):
    """Body của ``POST /ai/review`` — review code tuỳ ý (admin/teacher).

    Giữ đúng shape như develop: chỉ ``code`` + ``language``. Không có
    ``locale`` vì endpoint này luôn trả review tiếng Việt (như develop).
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=MAX_REVIEW_CODE_CHARS)
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
