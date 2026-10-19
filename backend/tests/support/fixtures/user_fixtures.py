from datetime import datetime

import pytest
from sqlmodel import Session

from app.core.dependencies import Role
from app.core.utils.datetime_utils import VN_TZ
from app.models import User


def vn(*args: int) -> datetime:
    """Build a timezone-aware datetime in the system's local timezone."""
    return datetime(*args, tzinfo=VN_TZ)


def make_user(session: Session, user_id: str, role_id: int) -> User:
    user = User(
        user_id=user_id,
        full_name=f"User {user_id}",
        email=f"{user_id.lower()}@example.com",
        hashed_password="not-a-real-hash",
        role_id=role_id,
    )
    session.add(user)
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
