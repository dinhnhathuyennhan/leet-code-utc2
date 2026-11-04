import httpx

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import Role, require_role
from app.modules.ai_review.preview_receipt import verify_preview_receipt
from app.models import User
from app.modules.ai_review.schemas import (
    AIConnectionResponse,
    AdminPreviewReviewRequest,
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

admin_router = APIRouter(prefix="/ai", tags=["AI Review"])


@admin_router.get("/test-connection", response_model=AIConnectionResponse)
async def test_ai_connection(
    _current_user: User = Depends(require_role(Role.ADMIN)),
) -> AIConnectionResponse:
    try:
        return await AIReviewService.test_connection()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI Server không phản hồi kịp thời.") from None
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=502, detail="Không thể kiểm tra kết nối AI Server.") from None


@admin_router.post("/problems/{problem_id}/review-preview", response_model=AIReviewResponse)
async def review_admin_preview(
    problem_id: int,
    data: AdminPreviewReviewRequest,
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> AIReviewResponse:
    verdict = verify_preview_receipt(
        data.preview_token, user_id=current_user.user_id, problem_id=problem_id,
        language=data.language, code=data.code,
    )
    summary = (f"status={verdict['status']}; "
               f"passed={verdict['passed_count']}/{verdict['total_count']} test cases")
    try:
        return await AIReviewService.review(data, judge_summary=summary)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI xử lý quá thời gian cho phép.") from None
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Không thể kết nối AI Server.") from None
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=502, detail="AI trả về dữ liệu không hợp lệ.") from None


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
