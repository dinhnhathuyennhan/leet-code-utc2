from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, insert, select

from app.core.datetime_utils import (
    VN_TZ,
    UTCDateTime,
    as_utc,
    require_vietnam_local_datetime,
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
        assert vn_day_start(date(2026, 9, 7)) == datetime(2026, 9, 7, 0, 0)

    def test_day_end_is_last_microsecond_vn(self):
        assert vn_day_end(date(2026, 9, 7)) == datetime(2026, 9, 7, 23, 59, 59, 999999)


class TestAsUtc:
    def test_converts_vn_time_to_utc(self):
        result = as_utc(datetime(2026, 9, 7, 7, 0, tzinfo=VN_TZ))
        assert result == datetime(2026, 9, 7, 0, 0, tzinfo=UTC)
        assert result.utcoffset() == timedelta(0)

    def test_interprets_naive_datetime_as_vietnam_local_time(self):
        result = as_utc(datetime(2026, 9, 7, 7, 0))
        assert result == datetime(2026, 9, 7, 0, 0, tzinfo=UTC)


class TestRequireVietnamLocalDatetime:
    def test_accepts_naive_vietnam_local_datetime(self):
        value = datetime(2026, 9, 7)
        assert require_vietnam_local_datetime(value, "start_date") is value

    def test_rejects_datetime_with_offset(self):
        with pytest.raises(InvalidFormatError, match=r"start_date.*không kèm timezone offset"):
            require_vietnam_local_datetime(datetime(2026, 9, 7, tzinfo=UTC), "start_date")


class TestUTCDateTimeColumn:
    def test_read_back_same_instant_as_vietnam_local_wall_time(self, conn):
        saved = datetime(2026, 9, 7, 0, 0, tzinfo=VN_TZ)
        result = _save_and_read(conn, saved)
        assert result == datetime(2026, 9, 7, 0, 0)
        assert result.tzinfo is None

    def test_utc_input_is_returned_as_vn_time(self, conn):
        result = _save_and_read(conn, datetime(2026, 9, 7, 0, 0, tzinfo=UTC))
        assert result == datetime(2026, 9, 7, 7, 0)

    def test_naive_value_is_stored_as_vietnam_local_time(self, conn):
        result = _save_and_read(conn, datetime(2026, 9, 7, 7, 0))
        assert result == datetime(2026, 9, 7, 7, 0)
