import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from sqlmodel import Session, select

from app.core import config
from app.core.database import engine
from app.models import Submission

logger = logging.getLogger(__name__)

_executor: ThreadPoolExecutor | None = None
_lock = threading.Lock()
STARTUP_QUERY_TIMEOUT_SECONDS = float(os.getenv("GRADING_STARTUP_TIMEOUT_SECONDS", "10"))


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    with _lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(
                max_workers=config.GRADING_WORKERS, thread_name_prefix="grading"
            )
        return _executor


def _grade(submission_id: int) -> None:
    from app.modules.submissions.judge0.service import grade_submission  # tránh import vòng

    try:
        grade_submission(submission_id)
    except Exception:
        logger.exception("Chấm bài thất bại ngoài dự kiến, submission_id=%s", submission_id)


def enqueue(submission_id: int, delay_seconds: float = 0) -> None:
    if delay_seconds > 0:
        timer = threading.Timer(delay_seconds, enqueue, args=(submission_id,))
        timer.daemon = True
        timer.start()
        return
    _get_executor().submit(_grade, submission_id)


def start() -> None:
    """Gọi lúc backend khởi động: chấm lại các bài đang dở dang do backend từng dừng."""
    _get_executor()
    started_at = time.monotonic()
    logger.info("Grading queue startup: checking for pending submissions")
    try:
        with Session(engine) as session:
            submission_ids = session.exec(
                select(Submission.submission_id).where(
                    Submission.status.in_(("pending", "processing"))
                )
            ).all()
        elapsed = time.monotonic() - started_at
        if elapsed > STARTUP_QUERY_TIMEOUT_SECONDS:
            logger.warning(
                "Grading queue startup query took %.2fs (target <= %.2fs)",
                elapsed,
                STARTUP_QUERY_TIMEOUT_SECONDS,
            )
    except Exception:
        logger.exception("Could not load pending submissions for grading queue recovery")
        return
    for submission_id in submission_ids:
        enqueue(submission_id)
    if submission_ids:
        logger.info("Đã đưa %d bài nộp dở dang vào hàng đợi chấm", len(submission_ids))
    logger.info(
        "Grading queue startup complete in %.2fs; recovered %d submissions",
        time.monotonic() - started_at,
        len(submission_ids),
    )


def stop() -> None:
    if _executor is not None:
        _executor.shutdown(wait=False, cancel_futures=True)
