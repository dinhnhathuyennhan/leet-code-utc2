"""Đếm câu SQL thực sự gửi xuống DB trong một khối lệnh, để test khẳng định hiệu năng truy vấn."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import event
from sqlalchemy.engine import Engine


class QueryLog:
    """Danh sách câu SQL đã chạy (``statements``) và số lượng (``count``)."""

    def __init__(self) -> None:
        self.statements: list[str] = []

    @property
    def count(self) -> int:
        return len(self.statements)


@contextmanager
def count_queries(engine: Engine) -> Iterator[QueryLog]:
    """Ghi lại mọi câu SQL ``engine`` thực thi cho tới khi thoát khối ``with``.

    Dùng: ``with count_queries(engine) as queries: ...`` rồi đọc
    ``queries.statements`` (list[str]) và ``queries.count``.
    """
    log = QueryLog()

    def record(conn, cursor, statement, parameters, context, executemany):
        log.statements.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        yield log
    finally:
        event.remove(engine, "before_cursor_execute", record)
