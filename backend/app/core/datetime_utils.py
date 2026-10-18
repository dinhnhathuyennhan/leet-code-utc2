from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator

from app.core.exceptions import InvalidFormatError

# Quy ước múi giờ của hệ thống:
# - DB lưu UTC (timestamptz), API nhận datetime bắt buộc kèm offset, trả về giờ VN (+07:00).
# - Cột kiểu `date` (vd: Lesson.start_date) là ngày theo lịch VN.
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def now_utc() -> datetime:
    return datetime.now(UTC)


def today_vn() -> date:
    return datetime.now(VN_TZ).date()


def vn_day_start(day: date) -> datetime:
    """00:00:00 giờ VN của ngày `day`."""
    return datetime.combine(day, time.min, tzinfo=VN_TZ)


def vn_day_end(day: date) -> datetime:
    """23:59:59.999999 giờ VN của ngày `day`."""
    return datetime.combine(day, time.max, tzinfo=VN_TZ)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Không được dùng datetime naive (thiếu múi giờ)")
    return value.astimezone(UTC)


def require_offset(value: datetime, field_name: str) -> datetime:
    """Dùng trong schema: từ chối datetime client gửi lên mà không kèm múi giờ."""
    if value.tzinfo is None:
        raise InvalidFormatError(f"{field_name} phải kèm múi giờ, vd: 2026-09-07T00:00:00+07:00")
    return value


class UTCDateTime(TypeDecorator):
    """Kiểu cột datetime: ghi xuống DB dạng UTC, đọc lên trả về giờ VN."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return as_utc(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:  # SQLite (dùng trong test) không lưu múi giờ, giá trị đã ghi là UTC
            value = value.replace(tzinfo=UTC)
        return value.astimezone(VN_TZ)
