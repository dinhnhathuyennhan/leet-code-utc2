from fastapi import APIRouter, Depends
from sqlmodel import Session
from starlette import status

from app.core.database import get_session
from app.core.dependencies import Role, get_current_user, require_role
from app.modules.enrollments.schemas import (
    AddClassToCourseRequest, AddClassToCourseResponse, AddStudentToCourseRequest,
    AddStudentToCourseResponse, GetStudentListResponse,
)
from app.modules.enrollments import service as enrollment_service
from app.models import User

router = APIRouter(tags=["enrollment"])


@router.post("/courses/{course_id}/enrollments",
             response_model=AddStudentToCourseResponse, status_code=status.HTTP_201_CREATED)
def add_student_to_course(
    data: AddStudentToCourseRequest, course_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> AddStudentToCourseResponse:
    return enrollment_service.add_student_to_course(
        student_id=data.student_id, course_id=course_id, session=session, current_user=current_user
    )


@router.post("/courses/{course_id}/enrollments/class",
             response_model=AddClassToCourseResponse, status_code=status.HTTP_201_CREATED)
def add_class_to_course(
    course_id: str, data: AddClassToCourseRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> AddClassToCourseResponse:
    return enrollment_service.add_class_to_course(session, course_id, data.class_id, current_user)


@router.delete("/courses/{course_id}/enrollments/{student_id}",
               status_code=status.HTTP_204_NO_CONTENT)
def delete_student_from_course(
    student_id: str, course_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    enrollment_service.delete_student_from_course(
        student_id=student_id, course_id=course_id, session=session, current_user=current_user
    )


@router.get("/courses/{course_id}/enrollments", response_model=list[GetStudentListResponse])
def get_course_enrollments_route(
    course_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return enrollment_service.get_course_enrollments(session, course_id, current_user)
