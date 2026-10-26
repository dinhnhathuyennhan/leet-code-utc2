import json
import logging
import threading
from collections.abc import Callable
from contextlib import contextmanager
from datetime import timedelta
from typing import Any

from sqlmodel import Session, func, select

from app.core import config
from app.core.database import engine
from app.core.exceptions import ConflictError, ForbiddenError, InvalidFormatError, NotFoundError
from app.core.utils.datetime_utils import as_utc, now_utc
from app.models import Problem, Submission, Testcase, User
from app.modules.courses.access import (
    find_enrollment,
    get_lesson_in_course,
    get_problem_in_lesson,
)
from app.modules.submissions.judge0 import grading_queue
from app.modules.submissions.judge0.harness import (
    build_source,
    extract_result,
    json_outputs_match,
    supports_function_harness,
    text_outputs_match,
)
from app.modules.submissions.judge0.judge0_client import (
    STATUS_ACCEPTED,
    Judge0Client,
    Judge0Error,
    Judge0Result,
)
from app.modules.submissions.judge0.schemas import (
    CodeRequest,
    RunCaseResponse,
    RunResponse,
    SubmissionResultResponse,
)
from app.modules.submissions.service import get_submission_detail
from app.modules.testcases.testcase_format import decode_testcase_value

logger = logging.getLogger(__name__)

RUN_TIMEOUT_SECONDS = config.RUN_TIMEOUT_SECONDS
GRADING_TIMEOUT_SECONDS = config.GRADING_TIMEOUT_SECONDS
GRADE_RETRY_DELAY_SECONDS = config.GRADE_RETRY_DELAY_SECONDS
# Bài active quá hạn này bị coi là hỏng: không còn chặn sinh viên nộp lại, và thôi chấm thử lại
PENDING_TTL = timedelta(minutes=config.PENDING_TTL_MINUTES)
_ACTIVE_STATUSES = ("pending", "processing")


class SubmissionClosedError(ForbiddenError):
    error_code = "SUBMISSION_CLOSED"


class UnsupportedLanguageError(InvalidFormatError):
    error_code = "UNSUPPORTED_LANGUAGE"


class JudgeBusyError(Judge0Error):
    error_code = "JUDGE_BUSY"


_run_slots = threading.BoundedSemaphore(config.RUN_CONCURRENCY)
_running_users: set[str] = set()
_running_lock = threading.Lock()


@contextmanager
def _run_slot(user_id: str):
    """Mỗi sinh viên một lượt Run tại một thời điểm, và giới hạn tổng số lượt Run đang chạy."""
    with _running_lock:
        if user_id in _running_users:
            raise ConflictError("Bạn đang có một lượt chạy thử, vui lòng đợi kết quả")
        if not _run_slots.acquire(blocking=False):
            raise JudgeBusyError("Hệ thống đang có nhiều lượt chạy thử, vui lòng thử lại sau vài giây")
        _running_users.add(user_id)
    try:
        yield
    finally:
        with _running_lock:
            _running_users.discard(user_id)
        _run_slots.release()


def _get_student_problem(
    session: Session, course_id: str, lesson_id: int, problem_id: int, current_user: User
) -> Problem:
    if find_enrollment(session, course_id, current_user.user_id) is None:
        raise ForbiddenError("Bạn không có quyền làm bài trong lớp học này")
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    problem = get_problem_in_lesson(session, lesson, problem_id)
    if as_utc(problem.start_datetime) > now_utc():
        raise NotFoundError("Không tìm thấy bài tập trong buổi học")
    return problem


def _build_source(problem: Problem, language: str, code: str) -> str:
    if problem.function_name is None:
        return code
    if not supports_function_harness(language):
        raise UnsupportedLanguageError(f"Bài tập này chưa hỗ trợ chấm bằng {language}")
    return build_source(language, code, problem.function_name)


def _judge_case(result: Judge0Result, testcase: Testcase, uses_harness: bool) -> tuple[str, Any]:
    """Trả về (status nội bộ, actual_output đã giải mã)."""
    if not result.finished:
        return "internal_error", None
    if result.status_id != STATUS_ACCEPTED:
        return result.system_status, None
    if uses_harness:
        actual = extract_result(result.stdout)
        matched = json_outputs_match(testcase.expected_output, actual)
        return ("accepted" if matched else "wrong_answer"), (
            json.loads(actual) if actual is not None else None
        )
    matched = text_outputs_match(testcase.expected_output, result.stdout)
    return ("accepted" if matched else "wrong_answer"), (result.stdout or "").strip()


def _overall_status(statuses: list[str]) -> str:
    return next((s for s in statuses if s != "accepted"), "accepted")


def _run_judge(
    problem: Problem,
    data: CodeRequest,
    testcases: list[Testcase],
    timeout: float,
    tokens: list[str] | None = None,
    on_tokens: Callable[[list[str]], None] | None = None,
) -> list[tuple[Judge0Result, str, Any]]:
    source = _build_source(problem, data.language, data.code)
    client = Judge0Client()
    try:
        if not tokens or len(tokens) != len(testcases):
            tokens = client.create_batch(
                source, data.language, [tc.input for tc in testcases], problem.time_limit_seconds
            )
            if on_tokens is not None:
                on_tokens(tokens)
        results = client.wait_for_results(tokens, timeout)
    finally:
        client.close()
    uses_harness = problem.function_name is not None
    judged = [_judge_case(r, tc, uses_harness) for r, tc in zip(results, testcases, strict=True)]
    return [(r, status, actual) for r, (status, actual) in zip(results, judged, strict=True)]


def run(
    session: Session,
    course_id: str,
    lesson_id: int,
    problem_id: int,
    data: CodeRequest,
    current_user: User,
) -> RunResponse:
    user_id = current_user.user_id
    problem = _get_student_problem(session, course_id, lesson_id, problem_id, current_user)
    samples = list(
        session.exec(
            select(Testcase)
            .where(Testcase.problem_id == problem_id, Testcase.is_sample == True)  # noqa: E712
            .order_by(Testcase.testcase_id)
        ).all()
    )
    if not samples:
        raise ConflictError("Bài tập chưa có testcase mẫu để chạy thử")
    session.close()  # trả kết nối DB về pool trước khi chờ Judge0 (tối đa RUN_TIMEOUT_SECONDS)

    with _run_slot(user_id):
        judged = _run_judge(problem, data, samples, RUN_TIMEOUT_SECONDS)
    cases = [
        RunCaseResponse(
            index=index,
            status=status,
            input=decode_testcase_value(tc.input, tc.input_type),
            expected_output=decode_testcase_value(tc.expected_output, tc.expected_output_type),
            actual_output=actual,
            stderr=result.stderr or result.message,
            time=result.time,
        )
        for index, (tc, (result, status, actual)) in enumerate(zip(samples, judged, strict=True))
    ]
    compile_output = next((r.compile_output for r, s, _ in judged if s == "compile_error"), None)
    return RunResponse(
        status=_overall_status([c.status for c in cases]),
        compile_output=compile_output,
        cases=cases,
    )


def submit(
    session: Session,
    course_id: str,
    lesson_id: int,
    problem_id: int,
    data: CodeRequest,
    current_user: User,
) -> Submission:
    problem = _get_student_problem(session, course_id, lesson_id, problem_id, current_user)
    if as_utc(problem.end_datetime) < now_utc():
        raise SubmissionClosedError("Bài tập đã hết hạn nộp")
    if not problem.total_number_testcase:
        raise ConflictError("Bài tập chưa có testcase để chấm")
    _build_source(problem, data.language, data.code)  # kiểm tra ngôn ngữ được hỗ trợ trước khi lưu

    active = session.exec(
        select(func.count())
        .select_from(Submission)
        .where(
            Submission.problem_id == problem_id,
            Submission.student_id == current_user.user_id,
            Submission.status.in_(_ACTIVE_STATUSES),
            Submission.submitted_datetime >= now_utc() - PENDING_TTL,
        )
    ).one()
    if active:
        raise ConflictError("Bạn có bài nộp đang được chấm, vui lòng đợi kết quả")

    submission = Submission(
        problem_id=problem_id,
        student_id=current_user.user_id,
        language=data.language,
        submitted_code=data.code,
        status="pending",
        submitted_datetime=now_utc(),
    )
    session.add(submission)
    session.commit()
    session.refresh(submission)
    return submission


def _save_tokens(submission_id: int, tokens: list[str]) -> None:
    with Session(engine) as session:
        submission = session.get(Submission, submission_id)
        if submission is not None:
            submission.judge_tokens = tokens
            session.add(submission)
            session.commit()


def grade_submission(submission_id: int) -> None:
    """Chạy trong worker nền: mở Session riêng và không giữ kết nối DB trong lúc chờ Judge0."""
    with Session(engine) as session:
        submission = session.get(Submission, submission_id)
        if submission is None or submission.status not in _ACTIVE_STATUSES:
            return
        submission.status = "processing"
        session.add(submission)
        session.commit()
        session.refresh(submission)

        problem = session.get(Problem, submission.problem_id)
        testcases = list(
            session.exec(
                select(Testcase)
                .where(Testcase.problem_id == submission.problem_id)
                .order_by(Testcase.testcase_id)
            ).all()
        )
        data = CodeRequest(language=submission.language, code=submission.submitted_code)
        tokens = submission.judge_tokens
        submitted_at = as_utc(submission.submitted_datetime)
        session.close()

        retry = False
        passed_count = 0
        compile_output = None
        try:
            judged = _run_judge(
                problem,
                data,
                testcases,
                GRADING_TIMEOUT_SECONDS,
                tokens,
                lambda new_tokens: _save_tokens(submission_id, new_tokens),
            )
            statuses = [status for _, status, _ in judged]
            status = _overall_status(statuses)
            passed_count = statuses.count("accepted")
            compile_output = next((r.compile_output for r, s, _ in judged if s == "compile_error"), None)
        except Judge0Error:
            logger.warning("Judge0 không khả dụng khi chấm, submission_id=%s", submission_id)
            if now_utc() - submitted_at > PENDING_TTL:
                status = "internal_error"
            else:
                status, retry = "pending", True
        except Exception:
            logger.exception("Chấm bài thất bại, submission_id=%s", submission_id)
            status = "internal_error"

        submission = session.get(Submission, submission_id)
        submission.status = status
        submission.passed_count = passed_count
        submission.compile_output = compile_output
        session.add(submission)
        session.commit()

    if retry:
        grading_queue.enqueue(submission_id, GRADE_RETRY_DELAY_SECONDS)


def regrade(session: Session, submission_id: int, current_user: User) -> Submission:
    get_submission_detail(session, submission_id, current_user)  # raise nếu không đủ quyền xem bài nộp
    submission = session.get(Submission, submission_id)
    if submission.status != "internal_error":
        raise ConflictError("Chỉ chấm lại được bài bị lỗi hệ thống chấm")
    submission.status = "pending"
    submission.passed_count = 0
    submission.compile_output = None
    submission.judge_tokens = None
    session.add(submission)
    session.commit()
    session.refresh(submission)
    grading_queue.enqueue(submission.submission_id)
    return submission


def get_result(session: Session, submission_id: int, current_user: User) -> SubmissionResultResponse:
    submission = session.get(Submission, submission_id)
    if submission is None or submission.student_id != current_user.user_id:
        raise NotFoundError("Không tìm thấy bài nộp")
    total = session.exec(
        select(func.count()).select_from(Testcase).where(Testcase.problem_id == submission.problem_id)
    ).one()
    return SubmissionResultResponse(
        submission_id=submission.submission_id,
        status=submission.status,
        passed_count=submission.passed_count,
        total_testcases=total,
        compile_output=submission.compile_output,
    )
