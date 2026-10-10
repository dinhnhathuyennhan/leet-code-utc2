from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.dependencies import get_current_user, require_role, Role
from app.schemas.user import (
    CreateStudentRequest,
    CreateTeacherRequest,
    UserResetPasswordResponse,
    UserResponse, UserListResponse,
)
from app.services.user_service import (
    create_student,
    create_teacher,
    reset_password,
    user_response, list_users,
)
from models import User

router = APIRouter(tags=["user"])


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

@router.get("/users/me", response_model=UserResponse)
def get_me_route(current_user: User = Depends(get_current_user)):
    return user_response(current_user)


@router.get("/users", response_model=UserListResponse)
def list_users_route(
    role_id: int | None = Query(default=None),
    class_id: str | None = Query(default=None, min_length=1, max_length=50),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    return list_users(session, current_user, role_id, class_id, page, page_size)