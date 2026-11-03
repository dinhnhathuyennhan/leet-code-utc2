"""Test việc đọc cấu hình Judge0 từ env, gồm alias cho instance AWS/VPS.

Tên biến chuẩn của dự án là `JUDGE0_URL` / `JUDGE0_AUTH_TOKEN` (Judge0 local
trong docker-compose). Instance dựng trên AWS/VPS dùng `JUDGE0_API_URL` /
`JUDGE0_API_TOKEN`. `app/core/config.py` chấp nhận cả hai, ưu tiên nhóm chuẩn.
"""

import pytest

from app.core import config


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    for name in ("JUDGE0_URL", "JUDGE0_AUTH_TOKEN", "JUDGE0_API_URL", "JUDGE0_API_TOKEN"):
        monkeypatch.delenv(name, raising=False)


def test_default_is_local_judge0():
    assert config._judge0_url() == "http://localhost:2358"
    assert config._judge0_token() == ""


def test_standard_env_vars_are_used(monkeypatch):
    monkeypatch.setenv("JUDGE0_URL", "http://localhost:2358")
    monkeypatch.setenv("JUDGE0_AUTH_TOKEN", "local-dev-token-abc123")
    assert config._judge0_url() == "http://localhost:2358"
    assert config._judge0_token() == "local-dev-token-abc123"


def test_api_alias_env_vars_are_used(monkeypatch):
    """Nhóm biến của instance AWS/VPS cũng phải được đọc."""
    monkeypatch.setenv("JUDGE0_API_URL", "https://utc2-judge0.duckdns.org")
    monkeypatch.setenv("JUDGE0_API_TOKEN", "token-abc")
    assert config._judge0_url() == "https://utc2-judge0.duckdns.org"
    assert config._judge0_token() == "token-abc"


def test_standard_vars_win_over_alias(monkeypatch):
    monkeypatch.setenv("JUDGE0_URL", "http://localhost:2358")
    monkeypatch.setenv("JUDGE0_AUTH_TOKEN", "local-token")
    monkeypatch.setenv("JUDGE0_API_URL", "https://utc2-judge0.duckdns.org")
    monkeypatch.setenv("JUDGE0_API_TOKEN", "remote-token")
    assert config._judge0_url() == "http://localhost:2358"
    assert config._judge0_token() == "local-token"


def test_trailing_slash_is_stripped(monkeypatch):
    monkeypatch.setenv("JUDGE0_API_URL", "https://utc2-judge0.duckdns.org/")
    assert config._judge0_url() == "https://utc2-judge0.duckdns.org"


@pytest.mark.parametrize("env_name", ["JUDGE0_URL", "JUDGE0_API_URL"])
def test_url_can_come_from_either_name(monkeypatch, env_name):
    monkeypatch.setenv(env_name, "http://example.test:2358")
    assert config._judge0_url() == "http://example.test:2358"


@pytest.mark.parametrize("env_name", ["JUDGE0_AUTH_TOKEN", "JUDGE0_API_TOKEN"])
def test_token_can_come_from_either_name(monkeypatch, env_name):
    monkeypatch.setenv(env_name, "tok")
    assert config._judge0_token() == "tok"
