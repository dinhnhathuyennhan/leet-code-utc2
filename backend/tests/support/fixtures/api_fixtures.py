from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.database import get_session
from app.main import app


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    """TestClient backed by the current test's in-memory database session."""

    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
