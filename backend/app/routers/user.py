from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.dependencies import get_current_user, require_role
from app.schemas.user import (
    CreateStudentRequest,
    CreateTeacherRequest,
    UserResetPasswordResponse,
    UserResponse,
)
from app.services.user_service import (
    create_student,
    create_teacher,
    reset_password,
    user_response,
)
from models import User

router = APIRouter()


@router.post("/teachers", response_model=UserResponse)
def create_teacher_route(
    data: CreateTeacherRequest,
    session: Session = Depends(get_session),
    current_user=Depends(require_role(1)),
):
    teacher = create_teacher(session, data)
    return user_response(teacher)


@router.post("/students", response_model=UserResponse)
def create_student_route(
    data: CreateStudentRequest,
    session: Session = Depends(get_session),
    current_user=Depends(require_role(1, 2)),
):
    student = create_student(session, data)
    return user_response(student)


@router.post(
    "/users/{user_id}/reset-password", response_model=UserResetPasswordResponse
)
def reset_password_route(
    user_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    target_user_id, temporary_password = reset_password(
        session, current_user, user_id
    )
    return UserResetPasswordResponse(
        user_id=target_user_id, temporary_password=temporary_password
    )
