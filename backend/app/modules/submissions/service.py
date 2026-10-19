from sqlmodel import Session, select

from app.core.exceptions import InvalidFormatError, NotFoundError
from app.core.dependencies import Role
from app.modules.testcases.testcase_format import testcase_to_api_values
from app.modules.submissions.schemas import (
    PendingSubmissionListResponse,
    PendingSubmissionResponse,
    SubmissionDetailResponse,
    SubmissionTestcaseResponse,
    SubmissionUpdateRequest,
)
from app.models import Course, Lesson, Problem, Submission, Testcase, User


_VISIBLE_STATUSES = {"pending", "wrong_answer", "compile_error"}
_ALLOWED_UPDATE_STATUSES = {"pending", "accepted", "wrong_answer", "compile_error"}


def _teacher_course_ids(session: Session, current_user: User) -> set[str] | None:
    if current_user.role_id == Role.ADMIN:
        return None
    return set(
        session.exec(
            select(Course.course_id).where(Course.created_by == current_user.user_id)
        ).all()
    )


def _submission_rows(session: Session, current_user: User) -> list[tuple[Submission, Problem, Lesson, Course, User]]:
    statement = (
        select(Submission, Problem, Lesson, Course, User)
        .join(Problem, Submission.problem_id == Problem.problem_id)
        .join(Lesson, Problem.lesson_id == Lesson.lesson_id)
        .join(Course, Lesson.course_id == Course.course_id)
        .join(User, Submission.student_id == User.user_id)
        .order_by(Submission.submitted_datetime.desc(), Submission.submission_id.desc())
    )
    course_ids = _teacher_course_ids(session, current_user)
    if course_ids is not None:
        if not course_ids:
            return []
        statement = statement.where(Course.course_id.in_(course_ids))
    return list(session.exec(statement).all())


def _judge_kind(status: str) -> str:
    normalized = status.lower()
    if normalized == "compile_error":
        return "compile_error"
    return "wrong_answer"


def _judge_label(status: str) -> str:
    return {
        "pending": "Đang chờ chấm",
        "wrong_answer": "Sai kết quả",
        "compile_error": "Lỗi biên dịch",
    }.get(status.lower(), status)


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
) -> PendingSubmissionListResponse:
    rows = _submission_rows(session, current_user)
    rows = [row for row in rows if row[0].status.lower() in _VISIBLE_STATUSES]

    counts = {"all": len(rows), "late_appeal": 0, "similarity": 0, "error": 0}
    if search:
        query = search.strip().lower()
        rows = [
            row for row in rows
            if query in row[4].user_id.lower()
            or query in row[4].full_name.lower()
            or query in row[2].course_id.lower()
            or query in row[3].course_name.lower()
            or query in (row[1].report or "").lower()
            or query in row[1].title.lower()
        ]

    counts = {
        "all": len(rows),
        "late_appeal": 0,
        "similarity": 0,
        "error": sum(1 for row in rows if row[0].status.lower() == "compile_error"),
    }

    if filter_name == "error":
        filtered = [row for row in rows if row[0].status.lower() == "compile_error"]
    elif filter_name in {"late_appeal", "similarity"}:
        filtered = []
    else:
        filtered = rows

    items = [
        PendingSubmissionResponse(
            id=submission.submission_id,
            student_name=student.full_name,
            student_code=student.user_id,
            course_code=course.course_id,
            session_label=f"Buổi {lesson.lesson_number}: {lesson.lesson_name}",
            topic=problem.title,
            judge_kind=_judge_kind(submission.status),
            judge_label=_judge_label(submission.status),
            issue=_issue(submission, problem),
        )
        for submission, problem, lesson, course, student in filtered[:max(limit, 1)]
    ]
    return PendingSubmissionListResponse(items=items, total=len(filtered), counts=counts)


def get_submission_detail(
    session: Session, submission_id: int, current_user: User
) -> SubmissionDetailResponse:
    rows = [row for row in _submission_rows(session, current_user) if row[0].submission_id == submission_id]
    if not rows:
        raise NotFoundError("Không tìm thấy bài nộp")

    submission, problem, lesson, course, student = rows[0]
    testcases = session.exec(
        select(Testcase)
        .where(Testcase.problem_id == problem.problem_id)
        .order_by(Testcase.testcase_id)
    ).all()
    return SubmissionDetailResponse(
        id=submission.submission_id,
        student_name=student.full_name,
        student_code=student.user_id,
        class_id=student.class_id,
        course_code=course.course_id,
        course_name=course.course_name,
        session_label=f"Buổi {lesson.lesson_number}: {lesson.lesson_name}",
        problem_code=problem.report,
        problem_title=problem.title,
        language=submission.language,
        submitted_code=submission.submitted_code,
        status=submission.status,
        compile_output=submission.compile_output,
        feedback=submission.feedback,
        passed_count=submission.passed_count,
        total_testcases=problem.total_number_testcase,
        submitted_datetime=submission.submitted_datetime,
        testcases=[
            SubmissionTestcaseResponse(
                id=testcase.testcase_id,
                **testcase_to_api_values(testcase),
                is_sample=testcase.is_sample,
            )
            for testcase in testcases
        ],
    )


def update_submission(
    session: Session,
    submission_id: int,
    data: SubmissionUpdateRequest,
    current_user: User,
) -> SubmissionDetailResponse:
    rows = [row for row in _submission_rows(session, current_user) if row[0].submission_id == submission_id]
    if not rows:
        raise NotFoundError("Không tìm thấy bài nộp")
    if data.status is not None and data.status not in _ALLOWED_UPDATE_STATUSES:
        raise InvalidFormatError("Trạng thái bài nộp không hợp lệ")

    submission = rows[0][0]
    if data.feedback is not None:
        submission.feedback = data.feedback.strip() or None
    if data.status is not None:
        submission.status = data.status
    session.add(submission)
    session.commit()
    return get_submission_detail(session, submission_id, current_user)
