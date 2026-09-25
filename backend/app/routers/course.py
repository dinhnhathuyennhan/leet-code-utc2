import logging

from fastapi import APIRouter, Depends
from sqlmodel import Session
from starlette import status

from app.db import get_session
from app.dependencies import get_current_user, require_role
from app.schemas.course import (
    AddStudentToCourseRequest,
    AddStudentToCourseResponse,
    GetStudentListResponse,
)
from app.services.course_service import (
    add_student_to_course as _add_student_to_course,
)
from app.services.course_service import (
    delete_student_from_course as _delete_student_from_course,
)
from app.services.course_service import (
    get_course_enrollments,
)
from models import User

router = APIRouter(tags=["course"])
logger = logging.getLogger(__name__)

@router.post(
    "/courses/{course_id}/enrollments",
        response_model=AddStudentToCourseResponse,
        status_code=status.HTTP_404_NOT_FOUND
)
def add_student_to_course(
        data: AddStudentToCourseRequest,
        course_id: str,
        session: Session = Depends(get_session),
        current_user: User = Depends(require_role(1,2))

) -> AddStudentToCourseResponse:
    return _add_student_to_course(
        student_id=data.student_id,
        course_id=course_id,
        session=session,
        current_user=current_user,
    )

@router.delete(
    "/courses/{course_id}/enrollments/{student_id}",
        status_code=status.HTTP_204_NO_CONTENT
)
def delete_student_from_course(
        student_id: str,
        course_id: str,
        session: Session = Depends(get_session),
        current_user: User = Depends(require_role(1,2))
):
    _delete_student_from_course(
        student_id=student_id,
        course_id=course_id,
        session=session,
        current_user=current_user,
    )

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
