import secrets

import bcrypt


def generate_temporary_password(length: int = 12) -> str:
    """Sinh mật khẩu tạm ngẫu nhiên, URL-safe, dùng cho tài khoản mới/reset."""
    return secrets.token_urlsafe(length)


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
