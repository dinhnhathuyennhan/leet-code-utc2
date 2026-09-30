"""
decode_token(token, expected_type) là nơi DUY NHẤT chạm vào thư viện JWT: mọi lỗi của PyJWT
phải được bọc thành TokenError (AppError, 401), và loại token (access/refresh) phải khớp.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import pytest
from app.core import token as token_mod
from app.core.exceptions import AppError, TokenError
from app.core.token import create_access_token, create_refresh_token, decode_token

SECRET = "test-secret-key-at-least-32-bytes-long!!"


def _future() -> datetime:
    return datetime.now(UTC) + timedelta(days=1)


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setattr(token_mod, "JWT_SECRET_KEY", SECRET)


def _forge(payload: dict, key=SECRET, alg="HS256") -> str:
    return jwt.encode(payload, key, algorithm=alg)


def _full_payload(**overrides) -> dict:
    payload = {"sub": "U001", "tv": 0, "type": "access", "exp": _future()}
    payload.update(overrides)
    return payload


# ------------------------------------------------------------ claim / lifetime
def test_access_token_claims():
    payload = decode_token(create_access_token("U001", 2, 5), "access")
    assert payload["sub"] == "U001"
    assert payload["role"] == 2
    assert payload["tv"] == 5
    assert payload["type"] == "access"


def test_refresh_token_claims_and_no_role():
    payload = decode_token(create_refresh_token("U001", 5), "refresh")
    assert payload["sub"] == "U001"
    assert payload["tv"] == 5
    assert payload["type"] == "refresh"
    assert "role" not in payload


def test_access_token_lifetime_is_15_minutes():
    p = decode_token(create_access_token("U001", 1, 0), "access")
    assert p["exp"] - p["iat"] == 15 * 60


def test_refresh_token_lifetime_is_7_days():
    p = decode_token(create_refresh_token("U001", 0), "refresh")
    assert p["exp"] - p["iat"] == 7 * 24 * 3600


# ------------------------------------------------- loại token (expected_type)
def test_access_token_rejected_when_refresh_expected():
    with pytest.raises(TokenError):
        decode_token(create_access_token("U001", 1, 0), "refresh")


def test_refresh_token_rejected_when_access_expected():
    with pytest.raises(TokenError):
        decode_token(create_refresh_token("U001", 0), "access")


# ------------------------------------------ mọi lỗi PyJWT -> TokenError (401)
def test_token_error_is_an_app_error_with_401():
    with pytest.raises(TokenError) as exc:
        decode_token("not-a-jwt", "access")
    assert isinstance(exc.value, AppError)
    assert exc.value.status_code == 401
    assert exc.value.error_code == "INVALID_TOKEN"


@pytest.mark.parametrize("garbage", ["", "not-a-jwt", "a.b.c", "....", " "])
def test_garbage_token_raises_token_error(garbage):
    with pytest.raises(TokenError):
        decode_token(garbage, "access")


def test_expired_token_raises_token_error():
    expired = _forge(_full_payload(exp=datetime.now(UTC) - timedelta(seconds=5)))
    with pytest.raises(TokenError) as exc:
        decode_token(expired, "access")
    assert isinstance(exc.value.__cause__, jwt.ExpiredSignatureError)  # giữ nguyên nhân gốc


def test_tampered_token_raises_token_error():
    token = create_access_token("U001", 1, 0)
    head, body, sig = token.split(".")
    tampered = ".".join([head, body[:-2] + ("AA" if body[-2:] != "AA" else "BB"), sig])
    with pytest.raises(TokenError):
        decode_token(tampered, "access")


def test_wrong_secret_raises_token_error():
    forged = _forge(_full_payload(), key="another-secret-another-secret-123456")
    with pytest.raises(TokenError):
        decode_token(forged, "access")


def test_alg_none_is_rejected():
    unsigned = jwt.encode(_full_payload(), None, algorithm="none")
    with pytest.raises(TokenError):
        decode_token(unsigned, "access")


@pytest.mark.parametrize("missing", ["exp", "sub", "tv", "type"])
def test_token_missing_required_claim_is_rejected(missing):
    """Token ký ĐÚNG secret nhưng thiếu claim bắt buộc phải bị từ chối
    (đặc biệt `exp`: thiếu thì token sống vĩnh viễn)."""
    payload = _full_payload()
    del payload[missing]
    with pytest.raises(TokenError):
        decode_token(_forge(payload), "access")


# ---------------------------------------------------------- cấu hình secret
def test_signing_without_secret_fails(monkeypatch):
    monkeypatch.setattr(token_mod, "JWT_SECRET_KEY", None)
    with pytest.raises((TypeError, jwt.InvalidKeyError)):  # PyJWT: key=None không ký được
        create_access_token("U001", 1, 0)


# app/core/token.py -> parents[0]=core, [1]=app, [2]=thư mục gốc chứa package `app`.
# Tính từ vị trí file thật của module để KHÔNG phụ thuộc vào thư mục chạy pytest.
PROJECT_ROOT = Path(token_mod.__file__).resolve().parents[2]

