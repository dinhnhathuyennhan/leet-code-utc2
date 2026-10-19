from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, insert, select

from app.core.utils.datetime_utils import (
    VN_TZ,
    UTCDateTime,
    as_utc,
    require_offset,
    vn_day_end,
    vn_day_start,
)
from app.core.exceptions import InvalidFormatError

# Bảng tạm chỉ dùng trong file này, không đụng tới models.py
_metadata = MetaData()
_events = Table(
    "events",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("at", UTCDateTime),
)


@pytest.fixture()
def conn():
    engine = create_engine("sqlite://")
    _metadata.create_all(engine)
    with engine.connect() as connection:
        yield connection


def _save_and_read(conn, value: datetime) -> datetime:
    conn.execute(insert(_events).values(id=1, at=value))
    return conn.execute(select(_events.c.at)).scalar_one()


class TestVnDayBoundaries:
    def test_day_start_is_midnight_vn(self):
        assert vn_day_start(date(2026, 9, 7)) == datetime(2026, 9, 7, 0, 0, tzinfo=VN_TZ)

    def test_day_end_is_last_microsecond_vn(self):
        assert vn_day_end(date(2026, 9, 7)) == datetime(
            2026, 9, 7, 23, 59, 59, 999999, tzinfo=VN_TZ
        )


class TestAsUtc:
    def test_converts_vn_time_to_utc(self):
        result = as_utc(datetime(2026, 9, 7, 7, 0, tzinfo=VN_TZ))
        assert result == datetime(2026, 9, 7, 0, 0, tzinfo=UTC)
        assert result.utcoffset() == timedelta(0)

    def test_rejects_naive_datetime_without_timezone(self):
        with pytest.raises(ValueError, match="datetime naive"):
            as_utc(datetime(2026, 9, 7, 7, 0))


class TestRequireOffset:
    def test_accepts_datetime_with_vietnam_offset(self):
        value = datetime(2026, 9, 7, tzinfo=VN_TZ)
        assert require_offset(value, "start_date") is value

    def test_rejects_naive_datetime_without_offset(self):
        with pytest.raises(InvalidFormatError, match=r"start_date.*phải kèm múi giờ"):
            require_offset(datetime(2026, 9, 7), "start_date")


class TestUTCDateTimeColumn:
    def test_read_back_same_instant_as_vietnam_local_wall_time(self, conn):
        saved = datetime(2026, 9, 7, 0, 0, tzinfo=VN_TZ)
        result = _save_and_read(conn, saved)
        assert result == datetime(2026, 9, 7, 0, 0, tzinfo=VN_TZ)
        assert result.tzinfo is not None

    def test_utc_input_is_returned_as_vn_time(self, conn):
        result = _save_and_read(conn, datetime(2026, 9, 7, 0, 0, tzinfo=UTC))
        assert result == datetime(2026, 9, 7, 7, 0, tzinfo=VN_TZ)

    def test_naive_value_is_rejected(self):
        with pytest.raises(ValueError, match="datetime naive"):
            UTCDateTime().process_bind_param(datetime(2026, 9, 7, 7, 0), None)
