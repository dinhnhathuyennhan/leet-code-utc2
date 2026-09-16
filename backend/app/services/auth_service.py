from sqlmodel import Session, select

from app.core.exceptions import AppError
from app.core.password import hash_password, verify_password
from app.core.token import create_access_token, create_refresh_token, decode_token
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    UserResponse,
)
from models import User


# Định nghĩa một số Exception riêng cho domain auth
class InvalidCredentialsError(AppError):
    status_code = 401
    error_code = "INVALID_CREDENTIALS"


class WrongCurrentPasswordError(AppError):
    status_code = 401
    error_code = "WRONG_PASSWORD"


class SamePasswordError(AppError):
    status_code = 400
    error_code = "SAME_PASSWORD"

class SessionExpiredError(AppError):
    status_code = 401
    error_code = "SESSION_EXPIRED"


class SessionRevokedError(AppError):
    status_code = 401
    error_code = "SESSION_REVOKED"

def _build_login_response(user: User) -> tuple[LoginResponse, str]:
    access_token = create_access_token(
        user_id=user.user_id, role_id=user.role_id, token_version=user.token_version
    )
    refresh_token = create_refresh_token(
        user_id=user.user_id, token_version=user.token_version
    )
    response = LoginResponse(
        access_token=access_token,
        user=UserResponse(
            user_id=user.user_id,
            full_name=user.full_name,
            email=user.email,
            role_id=user.role_id,
            must_change_password=user.must_change_password,
        ),
    )
    return response, refresh_token


def login(session: Session, data: LoginRequest) -> tuple[LoginResponse, str]:
    existing = session.exec(select(User).where(User.email == data.email)).first()

    if existing is None or not verify_password(
        password=data.password, hashed_password=existing.hashed_password
    ):
        raise InvalidCredentialsError("Email hoặc mật khẩu không đúng")

    return _build_login_response(existing)


def change_password(
    session: Session, user: User, data: ChangePasswordRequest
) -> tuple[LoginResponse, str]:
    if not verify_password(
        password=data.current_password, hashed_password=user.hashed_password
    ):
        raise WrongCurrentPasswordError("Mật khẩu hiện tại không đúng")

    if data.current_password == data.new_password:
        raise SamePasswordError("Mật khẩu mới phải khác mật khẩu hiện tại")

    user.hashed_password = hash_password(data.new_password)
    user.must_change_password = False
    user.token_version += 1

    session.add(user)
    session.commit()
    session.refresh(user)

    return _build_login_response(user)

def refresh_access_token(session: Session, refresh_token: str | None) -> str:
    if not refresh_token:
        raise SessionExpiredError("Phiên đăng nhập đã hết hạn")

    payload = decode_token(refresh_token)
    # try:
    # except TokenError as err:
    #     raise SessionExpiredError("Phiên đăng nhập đã hết hạn") from err

    user = session.get(User, payload["sub"])
    if user is None or user.token_version != payload["tv"]:
        raise SessionRevokedError("Phiên đăng nhập không còn hợp lệ")

    return create_access_token(user.user_id, user.role_id, user.token_version)
