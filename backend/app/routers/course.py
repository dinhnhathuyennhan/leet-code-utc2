from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.dependencies import get_current_user
from app.schemas.course import GetStudentListResponse
from app.services.course_service import get_course_enrollments
from models import User

router = APIRouter(tags=["course"])


@router.get(
    "/courses/{course_id}/enrollments",
    response_model=list[GetStudentListResponse],
)
def get_course_enrollments_route(
    course_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return get_course_enrollments(session, course_id, current_user)
