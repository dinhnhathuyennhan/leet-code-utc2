"""Test `app/modules/judge0/client.py` — client chạy thử code của admin.

Bối cảnh: Judge0 Community Edition KHÔNG hỗ trợ `wait=true`
(trả `400 {"error":"wait not allowed"}`), nên client phải theo mô hình
submit -> nhận token -> poll `GET /submissions/{token}` cho tới khi xong.
"""

import asyncio

import httpx
import pytest

from app.modules.judge0.client import Judge0Client, Judge0Error


def _run(coro):
    return asyncio.run(coro)


def test_submit_does_not_use_wait_param(monkeypatch):
    """Regression: không gửi `wait=true` — Judge0 CE từ chối với 400."""
    import app.modules.judge0.client as client_module

    seen = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"token": "tok-1"}

    class FakeGet:
        def raise_for_status(self):
            pass

        def json(self):
            return {"status": {"id": 3}, "stdout": "Hello Judge0\n"}

    class FakeHttp:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, params=None, json=None, headers=None):
            seen["params"] = params
            return FakeResponse()

        async def get(self, url, params=None, headers=None):
            return FakeGet()

    monkeypatch.setattr(client_module.httpx, "AsyncClient", lambda timeout: FakeHttp())

    result = _run(
        Judge0Client().submit(source_code='print("Hello Judge0")', language_id=71)
    )

    assert "wait" not in (seen["params"] or {})
    assert result["status"] == {"id": 3}


def test_submit_polls_until_finished(monkeypatch):
    """Poll GET cho tới khi status.id khác 1/2 rồi mới trả kết quả."""
    import app.modules.judge0.client as client_module

    calls = {"get": 0}

    class FakeResponse:
        def __init__(self, body):
            self._body = body

        def raise_for_status(self):
            pass

        def json(self):
            return self._body

    class FakeHttp:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, params=None, json=None, headers=None):
            return FakeResponse({"token": "tok-1"})

        async def get(self, url, params=None, headers=None):
            calls["get"] += 1
            status = 2 if calls["get"] < 3 else 3
            return FakeResponse({"status": {"id": status}, "stdout": "x\n"})

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(client_module.httpx, "AsyncClient", lambda timeout: FakeHttp())
    monkeypatch.setattr(client_module.asyncio, "sleep", no_sleep)

    result = _run(Judge0Client().submit(source_code="print(1)", language_id=71))

    assert calls["get"] == 3
    assert result["status"] == {"id": 3}


def test_submit_http_error_becomes_judge0_error(monkeypatch):
    """Judge0 trả 400/500 -> Judge0Error chứ không crash."""
    import app.modules.judge0.client as client_module

    class FakeHttp:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, params=None, json=None, headers=None):
            request = httpx.Request("POST", "http://judge0/submissions")
            response = httpx.Response(400, request=request)
            raise httpx.HTTPStatusError("bad", request=request, response=response)

    monkeypatch.setattr(client_module.httpx, "AsyncClient", lambda timeout: FakeHttp())

    with pytest.raises(Judge0Error, match="HTTP 400"):
        _run(Judge0Client().submit(source_code="print(1)", language_id=71))
