"""Shared ``fk_session`` fixture: in-memory SQLite that enforces foreign keys.

SQLite does not check foreign keys by default, but Postgres does. This fixture
turns on ``PRAGMA foreign_keys=ON`` on every connection so tests that rely on
FK rejection (e.g. deleting a row still referenced by another) behave like
production.

Opt in per file with::

    pytest_plugins = ("tests.support.fixtures.db_fixtures",)
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


@pytest.fixture()
def fk_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
