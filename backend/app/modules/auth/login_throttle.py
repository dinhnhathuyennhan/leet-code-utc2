"""Chống dò mật khẩu: đếm số lần đăng nhập sai theo email.

Sai ``LOGIN_MAX_FAILED_ATTEMPTS`` lần trong ``LOGIN_FAILURE_WINDOW_MINUTES`` phút thì
email đó bị tạm chặn đăng nhập ``LOGIN_LOCKOUT_MINUTES`` phút (kể cả khi nhập đúng mật
khẩu). Đếm theo email chứ không theo IP, vì cả phòng máy thường dùng chung một IP.

Email chưa có tài khoản cũng bị đếm và chặn giống hệt, để kẻ dò không biết email nào
tồn tại. Đăng nhập đúng thì xoá bộ đếm.

Mỗi lượt đăng nhập được "giữ chỗ" (tăng bộ đếm dưới khoá dòng rồi commit) TRƯỚC khi
kiểm tra mật khẩu. Vì vậy một đợt request song song không thể cùng lọt qua bước kiểm
tra chặn rồi được thử hết mật khẩu: request thứ ``LOGIN_MAX_FAILED_ATTEMPTS`` đặt luôn
mốc chặn, các request sau nhận 429 mà không chạy bcrypt. Đăng nhập đúng thì xoá bộ đếm,
coi như hoàn lại các lượt đã giữ chỗ.
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import delete, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import DBAPIError
from sqlmodel import Session, select

from app.core import config
from app.core.exceptions import AppError
from app.core.utils.datetime_utils import now_utc
from app.models import LoginAttempt

# Số lần thử lại khi dòng vừa tạo bị xoá ngay (đăng nhập đúng/dọn dẹp chen vào giữa)
_LOCK_RETRIES = 3
# Dọn các dòng đã hết hạn tối đa mỗi khoảng này một lần (mỗi process)
_PURGE_INTERVAL = timedelta(minutes=5)
_last_purge: datetime | None = None


class LoginRateLimitedError(AppError):
    status_code = 429
    error_code = "LOGIN_RATE_LIMITED"


@dataclass(frozen=True)
class LoginSlot:
    """Một lượt thử đã được giữ chỗ (đã tính vào bộ đếm).

    ``locked_until`` khác ``None`` nghĩa là đây là lượt cuối của cửa sổ đếm: email đã
    bị chặn tới mốc đó, chỉ được gỡ nếu chính lượt này nhập đúng mật khẩu.
    """

    reserved_at: datetime
    locked_until: datetime | None

    def fail(self) -> None:
        """Gọi khi sai mật khẩu: lượt cuối thì raise ``LoginRateLimitedError``."""
        if self.locked_until is not None:
            raise _rate_limited(self.locked_until, self.reserved_at)


def normalize_email(email: str) -> str:
    return email.strip()


def _rate_limited(locked_until: datetime, now: datetime) -> LoginRateLimitedError:
    minutes = max(1, math.ceil((locked_until - now).total_seconds() / 60))
    return LoginRateLimitedError(
        f"Bạn đã đăng nhập sai quá nhiều lần. Vui lòng thử lại sau {minutes} phút"
    )


def reserve_attempt(session: Session, email: str) -> LoginSlot:
    """Giữ chỗ một lượt thử trước khi kiểm tra mật khẩu.

    Raise ``LoginRateLimitedError`` nếu email đang bị chặn (không tính thêm lượt).
    """
    key = normalize_email(email)
    now = now_utc()
    _purge_expired(session, now)

    attempt = _lock_row(session, key, now)
    if attempt.locked_until and attempt.locked_until > now:
        session.rollback()  # nhả khoá dòng
        raise _rate_limited(attempt.locked_until, now)

    window = timedelta(minutes=config.LOGIN_FAILURE_WINDOW_MINUTES)
    if attempt.window_started_at + window <= now or attempt.locked_until:
        # Hết cửa sổ đếm hoặc đã hết thời gian chặn: đếm lại từ đầu
        attempt.failed_count = 0
        attempt.window_started_at = now
        attempt.locked_until = None

    attempt.failed_count += 1
    if attempt.failed_count >= config.LOGIN_MAX_FAILED_ATTEMPTS:
        attempt.locked_until = now + timedelta(minutes=config.LOGIN_LOCKOUT_MINUTES)
    locked_until = attempt.locked_until
    session.add(attempt)
    session.commit()  # nhả khoá dòng trước bước bcrypt chậm
    return LoginSlot(reserved_at=now, locked_until=locked_until)


def clear_failures(session: Session, email: str) -> None:
    session.exec(delete(LoginAttempt).where(LoginAttempt.email == normalize_email(email)))
    session.commit()


def _lock_row(session: Session, key: str, now: datetime) -> LoginAttempt:
    """Lấy dòng của email dưới ``FOR UPDATE``, tạo mới nếu chưa có.

    ``INSERT ... ON CONFLICT DO NOTHING`` nên hai request đầu tiên cho cùng email không
    va nhau bằng ``IntegrityError``. ``populate_existing`` bắt SQLAlchemy nạp lại giá
    trị vừa khoá thay vì trả object cũ trong identity map của session (nếu không, các
    request chờ khoá sẽ cùng ghi một giá trị cũ cộng 1 và đếm hụt).
    """
    insert = sqlite_insert if session.get_bind().dialect.name == "sqlite" else pg_insert
    for _ in range(_LOCK_RETRIES):
        session.exec(
            insert(LoginAttempt)
            .values(email=key, failed_count=0, window_started_at=now)
            .on_conflict_do_nothing(index_elements=["email"])
        )
        attempt = session.exec(
            select(LoginAttempt)
            .where(LoginAttempt.email == key)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).first()
        if attempt is not None:
            return attempt
        # Dòng bị xoá giữa INSERT và SELECT: thử lại
    # Không âm thầm bỏ qua lượt thử: dừng luôn, không kiểm tra mật khẩu
    raise RuntimeError(f"Không khoá được dòng login_attempt sau {_LOCK_RETRIES} lần thử")


def _purge_expired(session: Session, now: datetime) -> None:
    """Xoá các dòng đã hết hạn, để email sai rồi bỏ đi không nằm lại mãi trong bảng.

    Dòng hết hạn (không bị chặn và đã hết cửa sổ đếm, hoặc đã hết thời gian chặn) tương
    đương với không có dòng, nên xoá không làm đổi kết quả đếm. Chỉ là dọn dẹp: lỗi DB
    ở đây (vd deadlock giữa hai lượt dọn) được bỏ qua, không làm hỏng lượt đăng nhập.
    """
    global _last_purge
    if _last_purge is not None and now - _last_purge < _PURGE_INTERVAL:
        return
    _last_purge = now
    window_cutoff = now - timedelta(minutes=config.LOGIN_FAILURE_WINDOW_MINUTES)
    try:
        session.exec(
            delete(LoginAttempt).where(
                or_(
                    LoginAttempt.locked_until <= now,
                    LoginAttempt.locked_until.is_(None)
                    & (LoginAttempt.window_started_at <= window_cutoff),
                )
            )
        )
        session.commit()
    except DBAPIError:
        session.rollback()
