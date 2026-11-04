from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import Role, require_role
from app.models import User
from app.modules.ai_review.schemas import (
    AIReviewFreeFormRequest,
    AIReviewRequest,
    AIReviewRequestBody,
    AIReviewResponse,
)
from app.modules.ai_review.service import AIReviewService, build_review_request

router = APIRouter(
    prefix="/ai",
    tags=["AI Review"],
)


@router.post(
    "/review",
    response_model=AIReviewResponse,
)
async def review_code(
    data: AIReviewFreeFormRequest,
    # Whitelist rõ 3 vai trò được phép; role lạ/role thêm sau này bị chặn
    # thay vì mặc định được gọi endpoint tốn tài nguyên này.
    _current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER, Role.STUDENT)),
) -> AIReviewResponse:
    # Endpoint review code tuỳ ý (dùng cho admin/teacher). Sinh viên dùng
    # route `/ai/review/{submission_id}` bên dưới: code lấy từ bài nộp đã pass.
    # Lỗi nghiệp vụ (AIReviewTimeoutError, AIReviewUnavailableError...) kế thừa
    # AppError và bay lên Global Exception Handler, router không tự bắt.
    return await AIReviewService.review(
        AIReviewRequest(
            code=data.code,
            language=data.language,
            free_form=True,
        )
    )


@router.post(
    "/review/{submission_id}",
    response_model=AIReviewResponse,
)
async def review_submission(
    submission_id: int,
    body: AIReviewRequestBody | None = None,
    session: Session = Depends(get_session),
    # Chỉ sinh viên chủ bài nộp: nút "Review code" là tính năng của sinh viên
    # sau khi đã pass hết testcase.
    current_user: User = Depends(require_role(Role.STUDENT)),
) -> AIReviewResponse:
    # Body rỗng (client cũ hoặc không gửi gì) => dùng ngôn ngữ mặc định "vi".
    locale = body.locale if body is not None else "vi"
    # Truy vấn DB là đồng bộ: đẩy sang threadpool để không chặn event loop
    # trong lúc các request AI khác đang chờ Ollama.
    data = await run_in_threadpool(
        build_review_request, session, submission_id, current_user, locale
    )
    # Lỗi nghiệp vụ (SubmissionNotAcceptedError, AIReviewTimeoutError...) kế thừa
    # AppError và bay lên Global Exception Handler, router không tự bắt.
    return await AIReviewService.review(data)
