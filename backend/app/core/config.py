import json
import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


@dataclass(frozen=True)
class LanguageConfig:
    judge0_id: int
    cpu_time_factor: float = 2
    memory_limit_kb: int | None = None  # None = mặc định của Judge0
    compiler_options: str | None = None


_DEFAULT_LANGUAGES: dict[str, dict] = {
    "python": {"judge0_id": 71, "cpu_time_factor": 2},
    "javascript": {"judge0_id": 63, "cpu_time_factor": 2, "memory_limit_kb": 2_048_000},
    "c": {"judge0_id": 50, "cpu_time_factor": 1},
    "cpp": {"judge0_id": 54, "cpu_time_factor": 1},
    "java": {
        "judge0_id": 62,
        "cpu_time_factor": 2,
        "memory_limit_kb": 6_144_000,
        "compiler_options": "-J-XX:CompressedClassSpaceSize=64m -J-XX:ReservedCodeCacheSize=64m -J-Xmx256m",
    },
}


def parse_languages(raw: str | None) -> dict[str, LanguageConfig]:
    """Gộp cấu hình ngôn ngữ mặc định với JUDGE_LANGUAGES (JSON).

    Mỗi khoá là tên ngôn ngữ; giá trị là object ghi đè từng trường, hoặc null để gỡ ngôn ngữ đó.
    """
    merged = {name: dict(values) for name, values in _DEFAULT_LANGUAGES.items()}
    if raw and raw.strip():
        try:
            overrides = json.loads(raw)
            if not isinstance(overrides, dict):
                raise ValueError("phải là một object")
            for name, values in overrides.items():
                if values is None:
                    merged.pop(name, None)
                elif isinstance(values, dict):
                    merged.setdefault(name, {}).update(values)
                else:
                    raise ValueError(f"cấu hình của '{name}' phải là object hoặc null")
        except ValueError as error:
            raise RuntimeError(f"JUDGE_LANGUAGES không hợp lệ: {error}") from error
    try:
        return {name: LanguageConfig(**values) for name, values in merged.items()}
    except TypeError as error:
        raise RuntimeError(f"JUDGE_LANGUAGES không hợp lệ: {error}") from error


# ===== Kết nối Judge0 =====
JUDGE0_URL = os.getenv("JUDGE0_URL", "http://localhost:2358").rstrip("/")
JUDGE0_AUTH_TOKEN = os.getenv("JUDGE0_AUTH_TOKEN", "")
JUDGE0_HTTP_TIMEOUT_SECONDS = _env_float("JUDGE0_HTTP_TIMEOUT_SECONDS", 10)
# Phải <= MAX_SUBMISSION_BATCH_SIZE của Judge0 (mặc định 20)
JUDGE0_BATCH_SIZE = _env_int("JUDGE0_BATCH_SIZE", 20)

# ===== Thử lại và poll =====
JUDGE0_RETRY_ATTEMPTS = _env_int("JUDGE0_RETRY_ATTEMPTS", 3)
JUDGE0_RETRY_BACKOFF_SECONDS = _env_float("JUDGE0_RETRY_BACKOFF_SECONDS", 0.5)
JUDGE0_POLL_INTERVAL_SECONDS = _env_float("JUDGE0_POLL_INTERVAL_SECONDS", 0.5)
JUDGE0_POLL_RETRY_SECONDS = _env_float("JUDGE0_POLL_RETRY_SECONDS", 1.0)

# ===== Giới hạn chạy: wall = min(cpu * FACTOR + EXTRA, MAX_WALL), cpu bị chặn bởi MAX_CPU =====
# Hai trần MAX phải <= MAX_CPU_TIME_LIMIT / MAX_WALL_TIME_LIMIT trong judge0.conf
JUDGE0_MAX_CPU_TIME_SECONDS = _env_float("JUDGE0_MAX_CPU_TIME_SECONDS", 15)
JUDGE0_MAX_WALL_TIME_SECONDS = _env_float("JUDGE0_MAX_WALL_TIME_SECONDS", 20)
JUDGE0_WALL_TIME_FACTOR = _env_float("JUDGE0_WALL_TIME_FACTOR", 2)
JUDGE0_WALL_TIME_EXTRA_SECONDS = _env_float("JUDGE0_WALL_TIME_EXTRA_SECONDS", 1)

# ===== Chạy thử và chấm bài =====
RUN_TIMEOUT_SECONDS = _env_float("RUN_TIMEOUT_SECONDS", 10)
GRADING_TIMEOUT_SECONDS = _env_float("GRADING_TIMEOUT_SECONDS", 300)
GRADE_RETRY_DELAY_SECONDS = _env_float("GRADE_RETRY_DELAY_SECONDS", 15)
# Bài đang pending/processing quá hạn này bị coi là hỏng
PENDING_TTL_MINUTES = _env_float("PENDING_TTL_MINUTES", 10)
# Số bài nộp chấm song song trong backend, nên xấp xỉ số worker Judge0
GRADING_WORKERS = _env_int("GRADING_WORKERS", 4)
# Số lượt Run đang chạy đồng thời tối đa, để không chiếm hết thread của API
RUN_CONCURRENCY = _env_int("RUN_CONCURRENCY", 10)
MAX_CODE_BYTES = _env_int("MAX_CODE_BYTES", 64 * 1024)

# ===== Ngôn ngữ hỗ trợ =====
LANGUAGES = parse_languages(os.getenv("JUDGE_LANGUAGES"))