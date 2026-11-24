"""Chống dò mật khẩu: đếm số lần đăng nhập sai theo email.

Sai ``LOGIN_MAX_FAILED_ATTEMPTS`` lần trong ``LOGIN_FAILURE_WINDOW_MINUTES`` phút thì
email đó bị tạm chặn đăng nhập ``LOGIN_LOCKOUT_MINUTES`` phút (kể cả khi nhập đúng mật
khẩu). Đếm theo email chứ không theo IP, vì cả phòng máy thường dùng chung một IP.

Email chưa có tài khoản cũng bị đếm và chặn giống hệt, để kẻ dò không biết email nào
tồn tại. Đăng nhập đúng thì xoá bộ đếm.
"""

import math
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core import config
from app.core.exceptions import AppError
from app.core.utils.datetime_utils import now_utc
from app.models import LoginAttempt


class LoginRateLimitedError(AppError):
    status_code = 429
    error_code = "LOGIN_RATE_LIMITED"


def normalize_email(email: str) -> str:
    return email.strip()


def _rate_limited(locked_until: datetime, now: datetime) -> LoginRateLimitedError:
    minutes = max(1, math.ceil((locked_until - now).total_seconds() / 60))
    return LoginRateLimitedError(
        f"Bạn đã đăng nhập sai quá nhiều lần. Vui lòng thử lại sau {minutes} phút"
    )


def ensure_not_locked(session: Session, email: str) -> None:
    """Raise ``LoginRateLimitedError`` nếu email đang bị tạm chặn."""
    attempt = session.get(LoginAttempt, normalize_email(email))
    now = now_utc()
    if attempt and attempt.locked_until and attempt.locked_until > now:
        raise _rate_limited(attempt.locked_until, now)


def record_failure(session: Session, email: str) -> None:
    """Ghi thêm một lần sai; nếu chạm ngưỡng thì chặn và raise ``LoginRateLimitedError``."""
    key = normalize_email(email)
    for _ in range(2):
        now = now_utc()
        # Khoá dòng (Postgres) để hai request sai cùng lúc không đếm hụt
        attempt = session.exec(
            select(LoginAttempt).where(LoginAttempt.email == key).with_for_update()
        ).first()
        window = timedelta(minutes=config.LOGIN_FAILURE_WINDOW_MINUTES)
        if attempt is None:
            attempt = LoginAttempt(email=key, failed_count=0, window_started_at=now)
        elif attempt.window_started_at + window <= now or (
            attempt.locked_until and attempt.locked_until <= now
        ):
            # Hết cửa sổ đếm hoặc đã hết thời gian chặn: đếm lại từ đầu
            attempt.failed_count = 0
            attempt.window_started_at = now
            attempt.locked_until = None

        attempt.failed_count += 1
        if attempt.failed_count >= config.LOGIN_MAX_FAILED_ATTEMPTS:
            attempt.locked_until = now + timedelta(minutes=config.LOGIN_LOCKOUT_MINUTES)
        session.add(attempt)
        try:
            session.commit()
        except IntegrityError:
            # Request khác vừa tạo dòng cho cùng email: đọc lại và cộng tiếp
            session.rollback()
            continue
        if attempt.locked_until:
            raise _rate_limited(attempt.locked_until, now)
        return


def clear_failures(session: Session, email: str) -> None:
    attempt = session.get(LoginAttempt, normalize_email(email))
    if attempt is not None:
        session.delete(attempt)
        session.commit()
