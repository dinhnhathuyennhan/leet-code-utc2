"""
Frontend (vercel.app) và backend (onrender.com) khác site: cookie refresh_token phải là
SameSite=None; Secure, nếu không trình duyệt sẽ không lưu/gửi cookie trong request cross-site.
"""

from fastapi import Response

from app.routers.auth import (
    REFRESH_TOKEN_MAX_AGE_SECONDS,
    _clear_refresh_token_cookie,
    _set_refresh_token_cookie,
)


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
