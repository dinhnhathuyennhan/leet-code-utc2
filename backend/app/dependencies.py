from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.token import decode_token
from app.db import get_session
from models import User

bearer_scheme = HTTPBearer()


class Role:
    ADMIN = 1
    TEACHER = 2
    STUDENT = 3


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Token không hợp lệ") from None

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token không hợp lệ")

    user = session.get(User, payload.get("sub"))
    if user is None:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")

    if payload.get("tv") != user.token_version:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập đã hết hạn")

    return user


def require_role(*allowed_role_ids: int):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role_id not in allowed_role_ids:
            raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện hành động này")
        return user

    return dependency
