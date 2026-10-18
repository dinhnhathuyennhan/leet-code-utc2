from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator

from app.core.exceptions import InvalidFormatError


VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
VIETNAM_TZ = VN_TZ


def now_utc() -> datetime:
    return datetime.now(UTC)


def today_vn() -> date:
    return datetime.now(VN_TZ).date()


def vn_day_start(day: date) -> datetime:
    """Return midnight as a Vietnam-local wall time without an offset."""
    return datetime.combine(day, time.min)


def vn_day_end(day: date) -> datetime:
    """Return the last microsecond as a Vietnam-local wall time without an offset."""
    return datetime.combine(day, time.max)


def is_vietnam_local_datetime(value: datetime) -> bool:
    """API datetimes are Vietnam-local wall times and must not include an offset."""
    return value.tzinfo is None or value.utcoffset() is None


def require_vietnam_local_datetime(value: datetime, field_name: str) -> datetime:
    if not is_vietnam_local_datetime(value):
        raise InvalidFormatError(f"{field_name} phải dùng giờ Việt Nam và không kèm timezone offset")
    return value


def as_utc(value: datetime) -> datetime:
    """Interpret naive values as Vietnam local time, then return the UTC instant."""
    if value.tzinfo is None or value.utcoffset() is None:
        value = value.replace(tzinfo=VN_TZ)
    return value.astimezone(UTC)


class UTCDateTime(TypeDecorator):
    """Store UTC instants while exposing timezone-naive Vietnam local datetimes."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect):
        if value is None:
            return None
        return as_utc(value)

    def process_result_value(self, value: datetime | None, dialect):
        if value is None:
            return None
        if value.tzinfo is None:  # SQLite returns the UTC value without timezone metadata.
            value = value.replace(tzinfo=UTC)
        return value.astimezone(VN_TZ).replace(tzinfo=None)
