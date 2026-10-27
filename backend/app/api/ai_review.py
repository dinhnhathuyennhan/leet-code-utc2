from fastapi import APIRouter, Depends

from app.core.dependencies import Role, require_role
from app.models import User
from app.modules.ai_review.schemas import (
    AIReviewRequest,
    AIReviewResponse,
)
from app.modules.ai_review.service import AIReviewService


router = APIRouter(
    prefix="/ai",
    tags=["AI Review"],
)


@router.post(
    "/review",
    response_model=AIReviewResponse,
)
async def review_code(
    data: AIReviewRequest,
    # Whitelist rõ 3 vai trò được phép; role lạ/role thêm sau này bị chặn
    # thay vì mặc định được gọi endpoint tốn tài nguyên này.
    _current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER, Role.STUDENT)),
) -> AIReviewResponse:
    # Lỗi nghiệp vụ (AIReviewTimeoutError, AIReviewUnavailableError...) kế thừa
    # AppError và bay lên Global Exception Handler, router không tự bắt.
    return await AIReviewService.review(data)
