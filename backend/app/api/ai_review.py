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
    AIReviewUsageResponse,
)
from app.modules.ai_review.service import (
    AIReviewService,
    build_review_request,
    get_review_usage,
    release_review_slot,
    reserve_review_slot,
)

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
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
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
    # Chỉ Admin/Teacher: sinh viên gửi code tuỳ ý vào đây sẽ vượt qua điều kiện
    # "pass hết testcase" và giới hạn lượt review của route theo bài nộp bên dưới.
    _current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
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
    # Bài đủ điều kiện mới giữ lượt; hết lượt thì báo 429 trước khi gọi Ollama.
    usage_id = await run_in_threadpool(reserve_review_slot, session, submission_id, current_user)
    # Lỗi nghiệp vụ (AIReviewTimeoutError, AIReviewBusyError...) kế thừa AppError và
    # bay lên Global Exception Handler; ở đây chỉ hoàn lượt rồi ném tiếp.
    try:
        return await AIReviewService.review(data)
    except Exception:
        await run_in_threadpool(release_review_slot, session, usage_id)
        raise


@router.get(
    "/review/{submission_id}/usage",
    response_model=AIReviewUsageResponse,
)
def get_review_usage_route(
    submission_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.STUDENT)),
) -> AIReviewUsageResponse:
    return get_review_usage(session, submission_id, current_user)
