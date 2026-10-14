from datetime import UTC, datetime


def now_utc() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """Quy ước hiện tại: datetime naive được coi là UTC (khớp code cũ).

    Khi nhóm chốt múi giờ (Phase 0), chỉ cần sửa file này."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
