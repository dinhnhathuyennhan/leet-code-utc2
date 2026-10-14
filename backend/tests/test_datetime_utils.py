from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, insert, select
from sqlalchemy.exc import StatementError

from app.core.datetime_utils import (
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
        assert vn_day_start(date(2026, 9, 7)) == datetime(2026, 9, 6, 17, 0, tzinfo=UTC)

    def test_day_end_is_last_microsecond_vn(self):
        assert vn_day_end(date(2026, 9, 7)) == datetime(2026, 9, 7, 16, 59, 59, 999999, tzinfo=UTC)


class TestAsUtc:
    def test_converts_vn_time_to_utc(self):
        result = as_utc(datetime(2026, 9, 7, 7, 0, tzinfo=VN_TZ))
        assert result == datetime(2026, 9, 7, 0, 0, tzinfo=UTC)
        assert result.utcoffset() == timedelta(0)

    def test_rejects_naive_datetime(self):
        with pytest.raises(ValueError):
            as_utc(datetime(2026, 9, 7))


class TestRequireOffset:
    def test_returns_value_when_offset_present(self):
        value = datetime(2026, 9, 7, tzinfo=UTC)
        assert require_offset(value, "start_date") is value

    def test_rejects_naive_with_field_name_in_message(self):
        with pytest.raises(InvalidFormatError, match="start_date phải kèm múi giờ"):
            require_offset(datetime(2026, 9, 7), "start_date")


class TestUTCDateTimeColumn:
    def test_read_back_same_instant_in_vn_offset(self, conn):
        saved = datetime(2026, 9, 7, 0, 0, tzinfo=VN_TZ)
        result = _save_and_read(conn, saved)
        assert result == saved
        assert result.utcoffset() == timedelta(hours=7)

    def test_utc_input_is_returned_as_vn_time(self, conn):
        result = _save_and_read(conn, datetime(2026, 9, 7, 0, 0, tzinfo=UTC))
        assert (result.hour, result.utcoffset()) == (7, timedelta(hours=7))

    def test_naive_value_cannot_be_saved(self, conn):
        with pytest.raises(StatementError):
            conn.execute(insert(_events).values(id=1, at=datetime(2026, 9, 7)))
