import base64
import json

import httpx
import pytest

from app.core import config
from app.modules.submissions.judge0 import judge0_client
from app.modules.submissions.judge0.judge0_client import Judge0Client, Judge0Error, compute_limits


def _b64(text):
    return base64.b64encode(text.encode()).decode()


def test_compute_limits_factor_and_cap():
    assert compute_limits(1, "cpp") == (1, 3)
    assert compute_limits(1, "python") == (2, 5)
    assert compute_limits(100, "python") == (15, 20)


def test_create_batch_sends_encoded_payload_and_returns_tokens():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        seen["params"] = dict(request.url.params)
        return httpx.Response(201, json=[{"token": "a"}, {"token": "b"}])

    client = Judge0Client(transport=httpx.MockTransport(handler))
    tokens = client.create_batch("print(1)", "python", ["x", "y"], 1)
    assert tokens == ["a", "b"]
    first = seen["body"]["submissions"][0]
    assert first["language_id"] == 71
    assert base64.b64decode(first["source_code"]).decode() == "print(1)"
    assert first["cpu_time_limit"] == 2


def test_wait_for_results_polls_until_finished():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        status = 2 if calls["n"] < 3 else 3
        return httpx.Response(
            200,
            json={"submissions": [{"token": "a", "status": {"id": status}, "stdout": _b64("2\n")}]},
        )

    client = Judge0Client(transport=httpx.MockTransport(handler))
    (result,) = client.wait_for_results(["a"], timeout_seconds=5)
    assert calls["n"] == 3
    assert result.system_status == "accepted"
    assert result.stdout == "2\n"


@pytest.mark.parametrize(
    ("status_id", "expected"),
    [(4, "wrong_answer"), (5, "time_limit_exceeded"), (6, "compile_error"), (11, "runtime_error"), (13, "internal_error")],
)
def test_status_mapping(status_id, expected):
    result = judge0_client.Judge0Result("t", status_id, None, None, None, None, None, None)
    assert result.system_status == expected


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(config, "JUDGE0_RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(config, "JUDGE0_POLL_RETRY_SECONDS", 0)
    monkeypatch.setattr(config, "JUDGE0_POLL_INTERVAL_SECONDS", 0)


def test_server_error_exhausts_retries_then_judge0_error():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(500)

    client = Judge0Client(transport=httpx.MockTransport(handler))
    with pytest.raises(Judge0Error):
        client.create_batch("x", "python", [""], 1)
    assert calls["n"] == config.JUDGE0_RETRY_ATTEMPTS


def test_create_batch_retries_transient_errors_then_succeeds():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("down")
        if calls["n"] == 2:
            return httpx.Response(503)
        return httpx.Response(201, json=[{"token": "a"}])

    client = Judge0Client(transport=httpx.MockTransport(handler))
    assert client.create_batch("x", "python", [""], 1) == ["a"]
    assert calls["n"] == 3


def test_client_error_is_not_retried():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(401)

    client = Judge0Client(transport=httpx.MockTransport(handler))
    with pytest.raises(Judge0Error):
        client.create_batch("x", "python", [""], 1)
    assert calls["n"] == 1


def test_wait_for_results_survives_judge0_restart():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] <= 3:
            raise httpx.ConnectError("restarting")
        return httpx.Response(200, json={"submissions": [{"token": "a", "status": {"id": 3}}]})

    client = Judge0Client(transport=httpx.MockTransport(handler))
    (result,) = client.wait_for_results(["a"], timeout_seconds=30)
    assert result.system_status == "accepted"
    assert calls["n"] == 4


def test_wait_for_results_gives_up_at_deadline():
    client = Judge0Client(transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    with pytest.raises(Judge0Error):
        client.wait_for_results(["a"], timeout_seconds=0)


def test_create_batch_splits_into_chunks_of_20():
    sizes = []

    def handler(request: httpx.Request) -> httpx.Response:
        items = json.loads(request.content)["submissions"]
        sizes.append(len(items))
        return httpx.Response(201, json=[{"token": f"t{len(sizes)}-{i}"} for i in range(len(items))])

    client = Judge0Client(transport=httpx.MockTransport(handler))
    tokens = client.create_batch("x", "python", [""] * 45, 1)
    assert sizes == [20, 20, 5]  # JUDGE0_BATCH_SIZE mặc định
    assert len(tokens) == 45


@pytest.mark.parametrize("memory_limit_kb", [None, 262_144])
@pytest.mark.parametrize("compiler_options", [None, "-J-Xmx256m"])
def test_create_batch_sends_configured_memory_and_compiler_options(
    monkeypatch, memory_limit_kb, compiler_options,
):
    monkeypatch.setattr(config, "LANGUAGES", {
        "java": config.LanguageConfig(
            judge0_id=62,
            memory_limit_kb=memory_limit_kb,
            compiler_options=compiler_options,
        ),
        "python": config.LanguageConfig(judge0_id=71),
    })
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)["submissions"][0]
        return httpx.Response(201, json=[{"token": "a"}])

    client = Judge0Client(transport=httpx.MockTransport(handler))
    client.create_batch("x", "java", [""], 1)
    assert seen["body"]["language_id"] == 62
    if memory_limit_kb is None:
        assert "memory_limit" not in seen["body"]
    else:
        assert seen["body"]["memory_limit"] == memory_limit_kb
    if compiler_options is None:
        assert "compiler_options" not in seen["body"]
    else:
        assert seen["body"]["compiler_options"] == compiler_options
    client.create_batch("x", "python", [""], 1)
    assert "memory_limit" not in seen["body"]
    assert "compiler_options" not in seen["body"]
    client.close()


def test_limits_follow_config(monkeypatch):
    monkeypatch.setattr(config, "JUDGE0_WALL_TIME_FACTOR", 3)
    monkeypatch.setattr(config, "JUDGE0_WALL_TIME_EXTRA_SECONDS", 2)
    assert judge0_client.compute_limits(1, "cpp") == (1, 5)
