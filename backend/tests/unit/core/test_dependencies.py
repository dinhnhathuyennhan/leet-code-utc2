"""Test cho get_current_user: token hợp lệ, user bị khoá, token_version cũ, user đã xoá."""

import uuid

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.dependencies import get_current_user
from app.core.exceptions import AccountLockedError, UnauthorizedError
from app.core.security import tokens as token_mod
from app.core.security.passwords import hash_password
from app.core.security.tokens import create_access_token
from app.models import User


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setattr(token_mod, "JWT_SECRET_KEY", "test-secret-key-at-least-32-bytes-long!!")


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def user(session):
    u = User(
        full_name="Nguyen Van A",
        email="a@example.com",
        hashed_password=hash_password("Old-Password-123"),
        role_id=1,
        must_change_password=False,
        token_version=0,
    )
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def _creds(user: User) -> HTTPAuthorizationCredentials:
    token = create_access_token(
        user_id=user.user_id, role_id=user.role_id, token_version=user.token_version
    )
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_returns_active_user(session, user):
    assert get_current_user(_creds(user), session).user_id == user.user_id


def test_rejects_locked_user_with_account_locked(session, user):
    creds = _creds(user)
    user.is_active = False
    session.add(user)
    session.commit()

    with pytest.raises(AccountLockedError) as exc:
        get_current_user(creds, session)
    assert exc.value.status_code == 403
    assert exc.value.error_code == "ACCOUNT_LOCKED"
    assert exc.value.message == "Tài khoản đã bị khoá"


def test_rejects_stale_token_version_with_401(session, user):
    creds = _creds(user)
    user.token_version += 1
    session.add(user)
    session.commit()

    with pytest.raises(UnauthorizedError) as exc:
        get_current_user(creds, session)
    assert exc.value.status_code == 401


def test_locked_wins_over_stale_token_version(session, user):
    """Khoá luôn tăng token_version: người đang đăng nhập bị khoá phải nhận ACCOUNT_LOCKED."""
    creds = _creds(user)
    user.is_active = False
    user.token_version += 1
    session.add(user)
    session.commit()

    with pytest.raises(AccountLockedError) as exc:
        get_current_user(creds, session)
    assert exc.value.status_code == 403
    assert exc.value.error_code == "ACCOUNT_LOCKED"


def test_rejects_deleted_user(session, user):
    creds = _creds(user)
    session.delete(user)
    session.commit()

    with pytest.raises(UnauthorizedError) as exc:
        get_current_user(creds, session)
    assert exc.value.status_code == 401


def test_rejects_unknown_user_id(session):
    ghost = User(
        user_id=uuid.uuid4(),
        full_name="x",
        email="x@example.com",
        hashed_password="x",
        role_id=1,
        token_version=0,
    )
    with pytest.raises(UnauthorizedError):
        get_current_user(_creds(ghost), session)
