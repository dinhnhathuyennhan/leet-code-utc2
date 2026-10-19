from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import Role, require_role
from app.modules.submissions.schemas import (
    PendingSubmissionListResponse,
    SubmissionDetailResponse,
    SubmissionUpdateRequest,
)
from app.modules.submissions.service import (
    get_submission_detail,
    list_pending_submissions,
    update_submission,
)
from app.models import User

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
