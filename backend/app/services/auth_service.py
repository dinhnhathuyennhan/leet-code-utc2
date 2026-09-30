from sqlalchemy import update
from sqlmodel import Session, select

from app.core.exceptions import AppError
from app.core.password import hash_password, verify_password
from app.core.token import create_access_token, create_refresh_token, decode_token, TokenError
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    UserResponse,
)
from models import User


_DUMMY_HASH = hash_password("dummy-password-for-timing-only")

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
    existing = session.exec(select(User).where(User.email == data.email.strip().lower())).first()

    # existing null (email không tồn tại sẽ không verify password
    # kẻ tấn công có thể dò ra được email nào tồn tại và không
    # luôn verify với DUMMY_HASH khi email không tồn tại
    hashed = existing.hashed_password if existing else _DUMMY_HASH
    password_ok = _safe_verify(data.password, hashed)

    if existing is None or not password_ok:
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

    session.exec(
        update(User)
        .where(User.user_id == user.user_id)
        .values(
            hashed_password=hash_password(data.new_password),
            must_change_password=False,
            token_version=User.token_version + 1,
        )
    )

    session.commit()
    session.refresh(user)

    return _build_login_response(user)

def refresh_access_token(session: Session, refresh_token: str | None) -> str:
    if not refresh_token:
        raise SessionExpiredError("Phiên đăng nhập đã hết hạn")

    try:
        payload = decode_token(refresh_token, "refresh")
    except TokenError as err:
        raise SessionExpiredError("Phiên đăng nhập đã hết hạn") from err

    sub, tv = payload.get("sub"), payload.get("tv")
    if payload.get("type") != "refresh" or sub is None or tv is None:
        raise SessionExpiredError("Phiên đăng nhập đã hết hạn")

    user = session.get(User, sub)
    if user is None or user.token_version != tv:
        raise SessionRevokedError("Phiên đăng nhập không còn hợp lệ")

    return create_access_token(user.user_id, user.role_id, user.token_version)

def _safe_verify(password: str, hashed_password: str) -> bool:
    try:
        return verify_password(password=password, hashed_password=hashed_password)
    except ValueError:
        return False