from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.dependencies import Role, require_role
from app.schemas.submission import (
    PendingSubmissionListResponse,
    SubmissionDetailResponse,
    SubmissionUpdateRequest,
)
from app.services.submission_service import (
    get_submission_detail,
    list_pending_submissions,
    update_submission,
)
from models import User

router = APIRouter(prefix="/submissions", tags=["submission"])


@router.get("/pending", response_model=PendingSubmissionListResponse)
def list_pending_submissions_route(
    filter: str = Query(default="all"),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> PendingSubmissionListResponse:
    return list_pending_submissions(session, current_user, filter, search, limit)


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
