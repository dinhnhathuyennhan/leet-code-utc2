"""Sanity test for the shared ``fk_session`` fixture."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import User

pytest_plugins = ("tests.support.fixtures.db_fixtures",)


def test_fk_session_enforces_foreign_keys(fk_session):
    user = User(
        full_name="Orphan",
        email=f"orphan-{uuid.uuid4()}@st.utc2.edu.vn",
        hashed_password="x",
        role_id=3,
        class_id="no-such-class",
    )
    fk_session.add(user)

    with pytest.raises(IntegrityError):
        fk_session.commit()
