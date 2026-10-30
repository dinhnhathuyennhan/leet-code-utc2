"""Short-lived proof that Judge0 evaluated the exact code under review."""

from datetime import UTC, datetime, timedelta
from hashlib import sha256

import jwt

from app.core.exceptions import ConflictError
from app.core.security.tokens import JWT_ALGORITHM, JWT_SECRET_KEY


def create_preview_receipt(*, user_id: str, problem_id: int, language: str, code: str,
                           status: str, passed_count: int, total_count: int) -> str:
    return jwt.encode({
        "type": "admin_preview",
        "sub": user_id,
        "problem_id": problem_id,
        "language": language,
        "code_hash": sha256(code.encode("utf-8")).hexdigest(),
        "status": status,
        "passed_count": passed_count,
        "total_count": total_count,
        "exp": datetime.now(UTC) + timedelta(minutes=10),
    }, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_preview_receipt(receipt: str, *, user_id: str, problem_id: int,
                           language: str, code: str) -> dict:
    try:
        payload = jwt.decode(receipt, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM],
                             options={"require": ["exp", "sub", "type", "problem_id", "code_hash"]})
    except jwt.InvalidTokenError as error:
        raise ConflictError("Kết quả chấm đã hết hạn hoặc không hợp lệ. Hãy chạy Judge0 lại.") from error
    if (payload.get("type") != "admin_preview" or payload.get("sub") != user_id
            or payload.get("problem_id") != problem_id or payload.get("language") != language
            or payload.get("code_hash") != sha256(code.encode("utf-8")).hexdigest()
            or payload.get("status") == "internal_error" or not payload.get("total_count")):
        raise ConflictError("Kết quả chấm không khớp lời giải hiện tại. Hãy chạy Judge0 lại.")
    return payload
