from datetime import datetime

import pytest
from sqlmodel import Session

from app.core.dependencies import Role
from app.core.utils.datetime_utils import VN_TZ
from app.models import User
from tests.support.fixtures.builders import make_user as build_user


def vn(*args: int) -> datetime:
    """Build a timezone-aware datetime in the system's local timezone."""
    return datetime(*args, tzinfo=VN_TZ)


def make_user(session: Session, user_id: str, role_id: int) -> User:
    user = build_user(session, user_id, role_id)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def admin(session: Session) -> User:
    return make_user(session, "AD001", Role.ADMIN)


@pytest.fixture
def owner_teacher(session: Session) -> User:
    return make_user(session, "GV001", Role.TEACHER)


@pytest.fixture
def other_teacher(session: Session) -> User:
    return make_user(session, "GV002", Role.TEACHER)


@pytest.fixture
def student(session: Session) -> User:
    return make_user(session, "SV001", Role.STUDENT)
