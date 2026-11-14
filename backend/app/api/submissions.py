from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import Role, require_role
from app.modules.submissions.schemas import (
    PendingSubmissionListResponse,
    StudentSubmissionDetailResponse,
    StudentSubmissionListResponse,
    SubmissionDetailResponse,
    SubmissionUpdateRequest,
)
from app.modules.submissions.service import (
    get_submission_detail,
    list_pending_submissions,
    update_submission,
)
from app.modules.submissions.student_service import (
    get_student_submission_detail,
    list_student_submissions,
)
from app.models import User
from app.modules.submissions.judge0.schemas import SubmissionResultResponse
from app.modules.submissions.judge0.schemas import SubmitAcceptedResponse
from app.modules.submissions.judge0 import service as judge_service

router = APIRouter(prefix="/submissions", tags=["submission"])


@router.get("/pending", response_model=PendingSubmissionListResponse)
def list_pending_submissions_route(
    filter: str = Query(default="all"),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    course: str | None = Query(default=None),
    lesson_id: int | None = Query(default=None),
    problem_id: int | None = Query(default=None),
    include_graded: bool = Query(default=False),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> PendingSubmissionListResponse:
    return list_pending_submissions(session, current_user, filter, search, limit, course, lesson_id, problem_id, include_graded)


# ─── Sinh viên ────────────────────────────────────────────────────────────────
# Đăng ký `/mine` TRƯỚC `/{submission_id}` để FastAPI không nuốt "mine" như
# một submission_id (thứ tự khai báo route quyết định route nào khớp trước).


@router.get("/mine", response_model=StudentSubmissionListResponse)
def list_my_submissions_route(
    course: str | None = Query(default=None),
    problem_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.STUDENT)),
) -> StudentSubmissionListResponse:
    """Lịch sử bài nộp của chính sinh viên đang đăng nhập."""
    return list_student_submissions(session, current_user, course, problem_id)


@router.get("/mine/{submission_id}", response_model=StudentSubmissionDetailResponse)
def get_my_submission_route(
    submission_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.STUDENT)),
) -> StudentSubmissionDetailResponse:
    """Kết quả chấm chi tiết của một bài nộp — chỉ chính chủ bài nộp được xem."""
    return get_student_submission_detail(session, current_user, submission_id)


@router.get("/{submission_id}/result", response_model=SubmissionResultResponse)
def get_submission_result_route(
    submission_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.STUDENT)),
) -> SubmissionResultResponse:
    """Kết quả chấm (dạng rút gọn) để frontend poll trong lúc chờ chấm nền xong."""
    return judge_service.get_result(session, submission_id, current_user)


@router.post(
    "/{submission_id}/regrade",
    response_model=SubmitAcceptedResponse,
    status_code=202,
)
def regrade_submission_route(
    submission_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> SubmitAcceptedResponse:
    submission = judge_service.regrade(session, submission_id, current_user)
    return SubmitAcceptedResponse(submission_id=submission.submission_id, status=submission.status)


@router.get("/{submission_id}", response_model=SubmissionDetailResponse)
def get_submission_detail_route(
    submission_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> SubmissionDetailResponse:
    return get_submission_detail(session, submission_id, current_user)


@router.patch("/{submission_id}", response_model=SubmissionDetailResponse)
def update_submission_route(
    submission_id: int,
    data: SubmissionUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> SubmissionDetailResponse:
    return update_submission(session, submission_id, data, current_user)
