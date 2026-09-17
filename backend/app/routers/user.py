from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.exceptions import UnauthorizedError
from app.core.token import decode_token
from app.db import get_session
from app.schemas.user import CreateStudentRequest, CreateTeacherRequest, UserResponse
from app.services.user_service import (
    create_student,
    create_teacher,
    user_response,
)
from models import User

router = APIRouter()
user_bearer_scheme = HTTPBearer(auto_error=False)


def get_user_for_user_routes(
    credentials: HTTPAuthorizationCredentials | None = Depends(user_bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Vui lòng đăng nhập")

    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise UnauthorizedError("Token không hợp lệ") from None

    if payload.get("type") != "access":
        raise UnauthorizedError("Token không hợp lệ")

    user = session.get(User, payload.get("sub"))
    if user is None:
        raise UnauthorizedError("Token không hợp lệ")

    if payload.get("tv") != user.token_version:
        raise UnauthorizedError("Phiên đăng nhập đã hết hạn")

    return user


def require_user_role(*allowed_role_ids: int):
    def dependency(
        user: User = Depends(get_user_for_user_routes),
        session: Session = Depends(get_session),
    ) -> Session:
        if user.role_id not in allowed_role_ids:
            raise UnauthorizedError("Bạn không có quyền thực hiện hành động này")
        return session

    return dependency


@router.post("/teachers", response_model=UserResponse)
def create_teacher_route(
    data: CreateTeacherRequest,
    session: Session = Depends(require_user_role(1)),
):
    teacher = create_teacher(session, data)
    return user_response(teacher)


@router.post("/students", response_model=UserResponse)
def create_student_route(
    data: CreateStudentRequest,
    session: Session = Depends(require_user_role(1, 2)),
):
    student = create_student(session, data)
    return user_response(student)
