"""
Frontend (vercel.app) và backend (onrender.com) khác site: cookie refresh_token phải là
SameSite=None; Secure, nếu không trình duyệt sẽ không lưu/gửi cookie trong request cross-site.
"""

import pytest
from fastapi import Response

from app.core.security import tokens as token_mod
from app.core.security.passwords import hash_password
from app.core.security.tokens import create_access_token, create_refresh_token
from app.models import User
from app.modules.users.service import lock_user
from app.api.auth import (
    REFRESH_TOKEN_MAX_AGE_SECONDS,
    _clear_refresh_token_cookie,
    _set_refresh_token_cookie,
)

pytest_plugins = ("tests.support.fixtures.api_fixtures",)


def _set_cookie_header(response: Response) -> str:
    return response.headers["set-cookie"].lower()


def test_set_refresh_cookie_is_cross_site_compatible():
    response = Response()
    _set_refresh_token_cookie(response, "token-value")
    header = _set_cookie_header(response)

    assert header.startswith("refresh_token=token-value;")
    assert "httponly" in header
    assert "secure" in header
    assert "samesite=none" in header
    assert "path=/auth" in header
    assert f"max-age={REFRESH_TOKEN_MAX_AGE_SECONDS}" in header


def test_clear_refresh_cookie_matches_set_attributes():
    response = Response()
    _clear_refresh_token_cookie(response)
    header = _set_cookie_header(response)

    assert header.startswith("refresh_token=")
    assert "max-age=0" in header
    assert "secure" in header
    assert "samesite=none" in header
    assert "path=/auth" in header


def test_session_ended_response_clears_cookie_cross_site(client):
    response = client.post("/auth/refresh-access-token")

    assert response.status_code == 401
    assert response.json()["error_code"] == "SESSION_EXPIRED"
    header = response.headers["set-cookie"].lower()
    assert "refresh_token=" in header
    assert "max-age=0" in header
    assert "secure" in header
    assert "samesite=none" in header
    assert "path=/auth" in header


# ---------------------------------------------------------------- locked accounts
LOCKED_PASSWORD = "Correct-Password-123"
LOCKED_BODY = {"error_code": "ACCOUNT_LOCKED", "message": "Tài khoản đã bị khoá"}


@pytest.fixture
def locked_user(session, monkeypatch):
    monkeypatch.setattr(token_mod, "JWT_SECRET_KEY", "test-secret-key-at-least-32-bytes-long!!")
    user = User(
        full_name="Locked Student",
        email="locked@example.com",
        hashed_password=hash_password(LOCKED_PASSWORD),
        role_id=3,
        must_change_password=False,
        token_version=0,
        is_active=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_login_locked_account_returns_403_account_locked(client, locked_user):
    response = client.post(
        "/auth/login", json={"email": "locked@example.com", "password": LOCKED_PASSWORD}
    )

    assert response.status_code == 403
    assert response.json() == LOCKED_BODY


def test_login_locked_account_wrong_password_returns_generic_401(client, locked_user):
    response = client.post(
        "/auth/login", json={"email": "locked@example.com", "password": "Wrong-Password-999"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "error_code": "INVALID_CREDENTIALS",
        "message": "Email hoặc mật khẩu không đúng",
    }


def test_refresh_locked_account_returns_403_and_clears_cookie(client, locked_user):
    refresh = create_refresh_token(
        user_id=locked_user.user_id, token_version=locked_user.token_version
    )
    client.cookies.set("refresh_token", refresh)

    response = client.post("/auth/refresh-access-token")

    assert response.status_code == 403
    assert response.json() == LOCKED_BODY
    header = response.headers["set-cookie"].lower()
    assert "refresh_token=" in header
    assert "max-age=0" in header
    assert "secure" in header
    assert "samesite=none" in header
    assert "path=/auth" in header


def test_api_call_with_locked_account_token_returns_403(client, locked_user):
    access = create_access_token(
        user_id=locked_user.user_id,
        role_id=locked_user.role_id,
        token_version=locked_user.token_version,
    )

    response = client.get("/users/me", headers={"Authorization": f"Bearer {access}"})

    assert response.status_code == 403
    assert response.json() == LOCKED_BODY


def test_online_user_locked_by_admin_gets_account_locked_with_old_tokens(
    client, session, monkeypatch
):
    """Kịch bản thật: user đang đăng nhập rồi bị khoá (khoá luôn tăng token_version)."""
    monkeypatch.setattr(token_mod, "JWT_SECRET_KEY", "test-secret-key-at-least-32-bytes-long!!")
    admin = User(full_name="Admin", email="admin@example.com", hashed_password="x", role_id=1)
    student = User(
        full_name="Online Student",
        email="0000000001@st.utc2.edu.vn",
        student_code="0000000001",
        hashed_password="x",
        role_id=3,
    )
    session.add_all([admin, student])
    session.commit()
    access = create_access_token(
        user_id=student.user_id, role_id=student.role_id, token_version=student.token_version
    )
    refresh = create_refresh_token(user_id=student.user_id, token_version=student.token_version)

    lock_user(session, admin, student.user_id)

    api = client.get("/users/me", headers={"Authorization": f"Bearer {access}"})
    assert api.status_code == 403
    assert api.json() == LOCKED_BODY

    client.cookies.set("refresh_token", refresh)
    refreshed = client.post("/auth/refresh-access-token")
    assert refreshed.status_code == 403
    assert refreshed.json() == LOCKED_BODY
    assert "max-age=0" in refreshed.headers["set-cookie"].lower()


# ------------------------------------------------------------ brute-force
def test_too_many_wrong_logins_return_429_body(client, monkeypatch):
    from app.core import config

    monkeypatch.setattr(config, "LOGIN_MAX_FAILED_ATTEMPTS", 2)
    monkeypatch.setattr(config, "LOGIN_LOCKOUT_MINUTES", 15)
    body = {"email": "ai-do@example.com", "password": "Wrong-Password-999"}

    assert client.post("/auth/login", json=body).status_code == 401
    response = client.post("/auth/login", json=body)

    assert response.status_code == 429
    assert response.json() == {
        "error_code": "LOGIN_RATE_LIMITED",
        "message": "Bạn đã đăng nhập sai quá nhiều lần. Vui lòng thử lại sau 15 phút",
    }
