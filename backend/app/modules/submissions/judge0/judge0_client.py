import base64
import logging
import time
from dataclasses import dataclass

import httpx

from app.core import config
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

RESULT_FIELDS = "token,status,stdout,stderr,compile_output,message,time,memory"

# Judge0 status.id → trạng thái nội bộ của Submission
STATUS_IN_QUEUE = 1
STATUS_PROCESSING = 2
STATUS_ACCEPTED = 3
_STATUS_MAP = {
    3: "accepted",
    4: "wrong_answer",
    5: "time_limit_exceeded",
    6: "compile_error",
    13: "internal_error",
    14: "internal_error",
}

_BUSY_MESSAGE = "Hệ thống chấm bài đang bận, vui lòng thử lại sau"


class Judge0Error(AppError):
    status_code = 503
    error_code = "JUDGE_UNAVAILABLE"


@dataclass
class Judge0Result:
    token: str
    status_id: int
    stdout: str | None
    stderr: str | None
    compile_output: str | None
    message: str | None
    time: float | None
    memory: int | None

    @property
    def finished(self) -> bool:
        return self.status_id not in (STATUS_IN_QUEUE, STATUS_PROCESSING)

    @property
    def system_status(self) -> str:
        if self.status_id in _STATUS_MAP:
            return _STATUS_MAP[self.status_id]
        return "runtime_error"  # 7-12: SIGSEGV, SIGXFSZ, SIGFPE, SIGABRT, NZEC, other


def compute_limits(time_limit_seconds: float, language: str) -> tuple[float, float]:
    cpu = min(
        time_limit_seconds * config.LANGUAGES[language].cpu_time_factor,
        config.JUDGE0_MAX_CPU_TIME_SECONDS,
    )
    wall = min(
        cpu * config.JUDGE0_WALL_TIME_FACTOR + config.JUDGE0_WALL_TIME_EXTRA_SECONDS,
        config.JUDGE0_MAX_WALL_TIME_SECONDS,
    )
    return cpu, wall


def _encode(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _decode(value: str | None) -> str | None:
    if value is None:
        return None
    return base64.b64decode(value).decode("utf-8", errors="replace")


def _to_result(data: dict) -> Judge0Result:
    status_id = (data.get("status") or {}).get("id", STATUS_IN_QUEUE)
    time_value = data.get("time")
    return Judge0Result(
        token=data["token"],
        status_id=status_id,
        stdout=_decode(data.get("stdout")),
        stderr=_decode(data.get("stderr")),
        compile_output=_decode(data.get("compile_output")),
        message=_decode(data.get("message")),
        time=float(time_value) if time_value is not None else None,
        memory=data.get("memory"),
    )


class Judge0Client:
    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        headers = {}
        if config.JUDGE0_AUTH_TOKEN:
            headers["X-Auth-Token"] = config.JUDGE0_AUTH_TOKEN
        self._http = httpx.Client(
            base_url=config.JUDGE0_URL,
            headers=headers,
            timeout=config.JUDGE0_HTTP_TIMEOUT_SECONDS,
            transport=transport,
        )

    def close(self) -> None:
        self._http.close()

    def _send(self, method: str, url: str, attempts: int = 1, **kwargs) -> httpx.Response:
        """Gửi request, chỉ thử lại với lỗi tạm thời (mất kết nối, timeout, 5xx)."""
        for attempt in range(1, attempts + 1):
            try:
                response = self._http.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except (httpx.TransportError, httpx.HTTPStatusError) as error:
                retryable = (
                    isinstance(error, httpx.TransportError) or error.response.status_code >= 500
                )
                if not retryable or attempt == attempts:
                    logger.error("Judge0 lỗi: %s (url=%s)", error, config.JUDGE0_URL)
                    raise Judge0Error(_BUSY_MESSAGE) from None
                time.sleep(config.JUDGE0_RETRY_BACKOFF_SECONDS * 2 ** (attempt - 1))
        raise Judge0Error(_BUSY_MESSAGE)

    def create_batch(
        self,
        source_code: str,
        language: str,
        stdins: list[str],
        time_limit_seconds: float,
    ) -> list[str]:
        size = config.JUDGE0_BATCH_SIZE
        tokens: list[str] = []
        for start in range(0, len(stdins), size):
            chunk = stdins[start : start + size]
            tokens += self._create_chunk(source_code, language, chunk, time_limit_seconds)
        return tokens

    def _create_chunk(
        self,
        source_code: str,
        language: str,
        stdins: list[str],
        time_limit_seconds: float,
    ) -> list[str]:
        language_config = config.LANGUAGES[language]
        cpu, wall = compute_limits(time_limit_seconds, language)
        extra = {}
        if language_config.memory_limit_kb:
            extra["memory_limit"] = language_config.memory_limit_kb
        if language_config.compiler_options:
            extra["compiler_options"] = language_config.compiler_options
        payload = {
            "submissions": [
                {
                    "source_code": _encode(source_code),
                    "language_id": language_config.judge0_id,
                    "stdin": _encode(stdin),
                    "cpu_time_limit": cpu,
                    "wall_time_limit": wall,
                    **extra,
                }
                for stdin in stdins
            ]
        }
        response = self._send(
            "POST",
            "/submissions/batch",
            config.JUDGE0_RETRY_ATTEMPTS,
            params={"base64_encoded": "true"},
            json=payload,
        )
        try:
            return [item["token"] for item in response.json()]
        except (KeyError, TypeError, ValueError):
            raise Judge0Error(_BUSY_MESSAGE) from None

    def get_batch(self, tokens: list[str]) -> list[Judge0Result]:
        size = config.JUDGE0_BATCH_SIZE
        results: list[Judge0Result] = []
        for start in range(0, len(tokens), size):
            results += self._get_chunk(tokens[start : start + size])
        return results

    def _get_chunk(self, tokens: list[str]) -> list[Judge0Result]:
        response = self._send(
            "GET",
            "/submissions/batch",
            params={"tokens": ",".join(tokens), "base64_encoded": "true", "fields": RESULT_FIELDS},
        )
        try:
            by_token = {item["token"]: _to_result(item) for item in response.json()["submissions"]}
            return [by_token[token] for token in tokens]
        except (KeyError, TypeError, ValueError):
            raise Judge0Error(_BUSY_MESSAGE) from None

    def wait_for_results(self, tokens: list[str], timeout_seconds: float) -> list[Judge0Result]:
        """Poll tới khi mọi token xong hoặc hết timeout (kết quả chưa xong trả về nguyên trạng)."""
        deadline = time.monotonic() + timeout_seconds
        while True:
            try:
                results = self.get_batch(tokens)
            except Judge0Error:
                # Judge0 có thể đang khởi động lại: chịu lỗi tới khi hết hạn thay vì bỏ cuộc ngay
                if time.monotonic() >= deadline:
                    raise
                time.sleep(config.JUDGE0_POLL_RETRY_SECONDS)
                continue
            if all(r.finished for r in results) or time.monotonic() >= deadline:
                return results
            time.sleep(config.JUDGE0_POLL_INTERVAL_SECONDS)