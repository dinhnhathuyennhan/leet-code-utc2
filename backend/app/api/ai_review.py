import httpx

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_user
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
    _current_user: User = Depends(get_current_user),
) -> AIReviewResponse:
    try:
        return await AIReviewService.review(data)

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="AI xử lý quá thời gian cho phép.",
        ) from None

    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Không thể kết nối AI Server.",
        ) from None

    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="AI trả về dữ liệu không hợp lệ.",
        ) from None
