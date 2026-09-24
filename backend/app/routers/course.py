import logging

from fastapi import APIRouter, Depends
from sqlmodel import Session
from starlette import status

from app.db import get_session
from app.dependencies import Role, require_role
from app.schemas.course import (
    AddStudentToCourseRequest,
    AddStudentToCourseResponse,
    CourseResponse,
    CreateCourseRequest,
    UpdateCourseRequest,
)
from app.services.course_service import add_student_to_course as _add_student_to_course
from app.services.course_service import create_course as _create_course
from app.services.course_service import (
    delete_student_from_course as _delete_student_from_course,
)
from app.services.course_service import update_course as _update_course
from models import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course_route(
    data: CreateCourseRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> CourseResponse:
    return _create_course(
        data=data,
        session=session,
        current_user=current_user,
    )


@router.patch(
    "/courses/{course_id}",
    response_model=CourseResponse,
)
def update_course_route(
    course_id: str,
    data: UpdateCourseRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> CourseResponse:
    return _update_course(
        course_id=course_id,
        data=data,
        session=session,
        current_user=current_user,
    )


@router.post(
    "/courses/{course_id}/enrollments",
    response_model=AddStudentToCourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_student_to_course(
    data: AddStudentToCourseRequest,
    course_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> AddStudentToCourseResponse:
    return _add_student_to_course(
        student_id=data.student_id,
        course_id=course_id,
        session=session,
        current_user=current_user,
    )


@router.delete(
    "/courses/{course_id}/enrollments/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_student_from_course(
    student_id: str,
    course_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    _delete_student_from_course(
        student_id=student_id,
        course_id=course_id,
        session=session,
        current_user=current_user,
    )
