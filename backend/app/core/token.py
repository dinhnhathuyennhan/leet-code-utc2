import os
from datetime import UTC, datetime, timedelta

import jwt

from app.core.exceptions import TokenError

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32:
    raise RuntimeError("JWT_SECRET_KEY phải được đặt và dài tối thiểu 32 ký tự")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: str, role_id: int, token_version: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "role": role_id,
        "tv": token_version,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, token_version: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "tv": token_version,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub", "tv", "type"]},
        )
    except jwt.InvalidTokenError as err:  # hết hạn, sai chữ ký, sai alg, thiếu claim, rác
        raise TokenError("Token không hợp lệ") from err

    if payload["type"] != expected_type:
        raise TokenError("Sai loại token")

    return payload