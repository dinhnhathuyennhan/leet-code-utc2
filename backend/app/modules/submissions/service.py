from sqlalchemy.orm import load_only
from sqlmodel import Session, func, select

from app.core.exceptions import NotFoundError
from app.modules.testcases.testcase_format import testcase_to_api_values
from app.modules.submissions.testcase_results import build_testcase_results, result_by_testcase
from app.modules.submissions.schemas import (
    PendingSubmissionListResponse,
    PendingSubmissionResponse,
    SubmissionDetailResponse,
    SubmissionTestcaseResponse,
    SubmissionUpdateRequest,
)
from app.models import Course, Lesson, Problem, Submission, Testcase, User


_NEW_STATUSES = {"processing", "time_limit_exceeded", "runtime_error", "internal_error"}
_VISIBLE_STATUSES = {"pending", "wrong_answer", "compile_error"} | _NEW_STATUSES
# Các giá trị `filter` lọc theo nhóm judge_kind mà frontend hiển thị thành chip.
_JUDGE_KIND_FILTERS = {"pending", "wrong_answer", "compile_error", "accepted"}


def _submission_query(*entities):
    return (
        select(*entities)
        .select_from(Submission)
        .join(Problem, Submission.problem_id == Problem.problem_id)
        .join(Lesson, Problem.lesson_id == Lesson.lesson_id)
        .join(Course, Lesson.course_id == Course.course_id)
        .join(User, Submission.student_id == User.user_id)
    )


def _scope_to_viewer(statement, current_user: User):
    """Chỉ thấy bài nộp trong các lớp do chính mình tạo (giảng viên chủ lớp).

    Admin không quản lý bài nộp nên không có nhánh xem tất cả.
    """
    return statement.where(Course.created_by == current_user.user_id)


def get_visible_submission(
    session: Session, submission_id: int, current_user: User
) -> tuple[Submission, Problem, Lesson, Course, User]:
    """Một bài nộp (đủ cột) mà người gọi được phép thấy, hoặc NotFoundError."""
    statement = _scope_to_viewer(
        _submission_query(Submission, Problem, Lesson, Course, User).where(
            Submission.submission_id == submission_id
        ),
        current_user,
    )
    row = session.exec(statement).first()
    if row is None:
        raise NotFoundError("Không tìm thấy bài nộp")
    return tuple(row)


def _judge_kind(status: str) -> str:
    normalized = status.lower()
    if normalized == "accepted":
        return "accepted"
    if normalized == "pending":
        return "pending"
    if normalized == "compile_error":
        return "compile_error"
    return "wrong_answer"


def _judge_label(status: str) -> str:
    return {
        "accepted": "Đã chấm",
        "pending": "Đang chờ chấm",
        "wrong_answer": "Sai kết quả",
        "compile_error": "Lỗi biên dịch",
        "processing": "Đang chấm",
        "time_limit_exceeded": "Quá thời gian",
        "runtime_error": "Lỗi khi chạy",
        "internal_error": "Lỗi hệ thống chấm",
    }.get(status.lower(), status)


def _needs_grading(submission: Submission) -> bool:
    """Bài còn phải chấm tay: chưa có điểm tay và judge chưa cho đạt."""
    return submission.manual_score is None and _judge_kind(submission.status) != "accepted"


def _issue(submission: Submission, problem: Problem) -> str:
    if submission.status.lower() == "compile_error":
        return submission.compile_output or "Bài nộp bị lỗi biên dịch."
    if problem.total_number_testcase:
        return f"Sai {problem.total_number_testcase - submission.passed_count}/{problem.total_number_testcase} test case"
    return "Bài nộp chưa đạt yêu cầu."


def list_pending_submissions(
    session: Session,
    current_user: User,
    filter_name: str = "all",
    search: str | None = None,
    limit: int = 100,
    course_id: str | None = None,
    lesson_id: int | None = None,
    problem_id: int | None = None,
    include_graded: bool = False,
) -> PendingSubmissionListResponse:
    visible_statuses = _VISIBLE_STATUSES | {"accepted"} if include_graded else _VISIBLE_STATUSES
    statement = (
        _submission_query(Submission, Problem, Lesson, Course, User)
        .options(
            load_only(
                Submission.submission_id,
                Submission.status,
                Submission.manual_score,
                Submission.passed_count,
                Submission.compile_output,
                Submission.submitted_datetime,
                raiseload=True,
            ),
            load_only(
                Problem.problem_id,
                Problem.title,
                Problem.report,
                Problem.total_number_testcase,
                raiseload=True,
            ),
            load_only(
                Lesson.lesson_id,
                Lesson.lesson_number,
                Lesson.lesson_name,
                Lesson.course_id,
                raiseload=True,
            ),
            load_only(Course.course_id, Course.course_name, raiseload=True),
            load_only(User.full_name, User.student_code, raiseload=True),
        )
        .where(func.lower(Submission.status).in_(visible_statuses))
        .order_by(Submission.submitted_datetime.desc(), Submission.submission_id.desc())
    )
    if course_id:
        statement = statement.where(Course.course_id == course_id)
    if lesson_id is not None:
        statement = statement.where(Lesson.lesson_id == lesson_id)
    if problem_id is not None:
        statement = statement.where(Problem.problem_id == problem_id)
    rows = list(session.exec(_scope_to_viewer(statement, current_user)).all())

    if search:
        query = search.strip().lower()
        rows = [
            row for row in rows
            if query in (row[4].student_code or "").lower()
            or query in row[4].full_name.lower()
            or query in row[2].course_id.lower()
            or query in row[3].course_name.lower()
            or query in (row[1].report or "").lower()
            or query in row[1].title.lower()
        ]

    counts = {
        "all": len(rows),
        "graded": sum(row[0].status.lower() == "accepted" for row in rows),
        "ungraded": sum(row[0].status.lower() != "accepted" for row in rows),
        "pending": sum(_judge_kind(row[0].status) == "pending" for row in rows),
        "wrong_answer": sum(_judge_kind(row[0].status) == "wrong_answer" for row in rows),
        "compile_error": sum(_judge_kind(row[0].status) == "compile_error" for row in rows),
        "needs_grading": sum(_needs_grading(row[0]) for row in rows),
        "late_appeal": 0,
        "similarity": 0,
        "error": sum(row[0].status.lower() == "compile_error" for row in rows),
    }

    if filter_name == "graded":
        filtered = [row for row in rows if row[0].status.lower() == "accepted"]
    elif filter_name == "error":
        filtered = [row for row in rows if row[0].status.lower() == "compile_error"]
    elif filter_name in _JUDGE_KIND_FILTERS:
        filtered = [row for row in rows if _judge_kind(row[0].status) == filter_name]
    elif filter_name == "needs_grading":
        filtered = [row for row in rows if _needs_grading(row[0])]
    elif filter_name in {"late_appeal", "similarity"}:
        filtered = []
    else:
        filtered = rows

    items = [
        PendingSubmissionResponse(
            id=submission.submission_id,
            course_id=course.course_id,
            lesson_id=lesson.lesson_id,
            problem_id=problem.problem_id,
            student_name=student.full_name,
            student_code=student.student_code,
            course_code=course.course_id,
            session_label=f"Buổi {lesson.lesson_number}: {lesson.lesson_name}",
            topic=problem.title,
            judge_kind=_judge_kind(submission.status),
            judge_label=_judge_label(submission.status),
            issue=_issue(submission, problem),
            status=submission.status,
            manual_score=submission.manual_score,
            passed_count=submission.passed_count,
            total_testcases=problem.total_number_testcase,
        )
        for submission, problem, lesson, course, student in filtered[:max(limit, 1)]
    ]
    return PendingSubmissionListResponse(items=items, total=len(filtered), counts=counts)


def get_submission_detail(
    session: Session, submission_id: int, current_user: User
) -> SubmissionDetailResponse:
    submission, problem, lesson, course, student = get_visible_submission(
        session, submission_id, current_user
    )
    testcases = session.exec(
        select(Testcase)
        .where(Testcase.problem_id == problem.problem_id)
        .order_by(Testcase.testcase_id)
    ).all()
    results = result_by_testcase(submission)
    return SubmissionDetailResponse(
        id=submission.submission_id,
        problem_id=problem.problem_id,
        student_name=student.full_name,
        student_code=student.student_code,
        class_id=student.class_id,
        course_code=course.course_id,
        course_name=course.course_name,
        session_label=f"Buổi {lesson.lesson_number}: {lesson.lesson_name}",
        problem_code=problem.report,
        problem_title=problem.title,
        problem_description=problem.description,
        problem_constraints=problem.constraints,
        problem_level=problem.level,
        problem_function_name=problem.function_name,
        language=submission.language,
        submitted_code=submission.submitted_code,
        status=submission.status,
        compile_output=submission.compile_output,
        feedback=submission.feedback,
        manual_score=submission.manual_score,
        passed_count=submission.passed_count,
        total_testcases=problem.total_number_testcase,
        submitted_datetime=submission.submitted_datetime,
        testcases=[
            SubmissionTestcaseResponse(
                id=testcase.testcase_id,
                **testcase_to_api_values(testcase),
                is_sample=testcase.is_sample,
                status=results.get(testcase.testcase_id, {}).get("status"),
                time=results.get(testcase.testcase_id, {}).get("time"),
            )
            for testcase in testcases
        ],
        testcase_results=build_testcase_results(submission, list(testcases)),
    )


def update_submission(
    session: Session,
    submission_id: int,
    data: SubmissionUpdateRequest,
    current_user: User,
) -> SubmissionDetailResponse:
    submission = get_visible_submission(session, submission_id, current_user)[0]
    # Không cho sửa `status` (schema chặn từ trước): chỉ cập nhật nhận xét và điểm tay,
    # nên không đụng tới lease của worker đang chấm bài này.
    if data.feedback is not None:
        submission.feedback = data.feedback.strip() or None
    # An explicit null clears the override; an omitted field leaves it unchanged.
    if "manual_score" in data.model_fields_set:
        submission.manual_score = data.manual_score
    session.add(submission)
    session.commit()
    return get_submission_detail(session, submission_id, current_user)
