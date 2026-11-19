"""Nghiệp vụ nộp bài và xem kết quả chấm dành cho SINH VIÊN.

Tách riêng khỏi ``submissions/service.py`` vốn phục vụ giáo viên
(xem/chấm bài của lớp mình), còn module này phục vụ sinh viên:
- xem lịch sử bài nộp của chính mình,
- xem kết quả chấm chi tiết của chính mình.

Việc chấm thật do ``modules/submissions/judge0`` đảm nhiệm (chạy nền qua
``grading_queue``), module này chỉ lo phần truy vấn và hiển thị.
"""
from sqlmodel import Session, select

from app.core.dependencies import Role
from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.testcases.testcase_format import testcase_to_api_values
from app.modules.submissions.schemas import (
    StudentSubmissionDetailResponse,
    StudentSubmissionListResponse,
    StudentSubmissionResponse,
    StudentSubmissionTestcaseResponse,
)
from app.models import Course, Lesson, Problem, Submission, Testcase, User


def _assert_student(current_user: User) -> None:
    if current_user.role_id != Role.STUDENT:
        raise ForbiddenError("Chỉ sinh viên mới được xem bài nộp của mình")


def _student_rows(
    session: Session, student_id: str
) -> list[tuple[Submission, Problem, Lesson, Course]]:
    statement = (
        select(Submission, Problem, Lesson, Course)
        .join(Problem, Submission.problem_id == Problem.problem_id)
        .join(Lesson, Problem.lesson_id == Lesson.lesson_id)
        .join(Course, Lesson.course_id == Course.course_id)
        .where(Submission.student_id == student_id)
        .order_by(Submission.submitted_datetime.desc(), Submission.submission_id.desc())
    )
    return list(session.exec(statement).all())


def list_student_submissions(
    session: Session,
    current_user: User,
    course_id: str | None = None,
    problem_id: int | None = None,
) -> StudentSubmissionListResponse:
    """Lịch sử bài nộp của chính sinh viên đang đăng nhập."""
    _assert_student(current_user)
    rows = _student_rows(session, current_user.user_id)
    if course_id:
        rows = [row for row in rows if row[3].course_id == course_id]
    if problem_id is not None:
        rows = [row for row in rows if row[1].problem_id == problem_id]

    items = [
        StudentSubmissionResponse(
            id=submission.submission_id,
            problem_id=problem.problem_id,
            problem_code=problem.report,
            problem_title=problem.title,
            course_id=course.course_id,
            course_name=course.course_name,
            lesson_id=lesson.lesson_id,
            session_label=f"Buổi {lesson.lesson_number}: {lesson.lesson_name}",
            language=submission.language,
            status=submission.status,
            passed_count=submission.passed_count,
            total_testcases=problem.total_number_testcase,
            submitted_datetime=submission.submitted_datetime,
        )
        for submission, problem, lesson, course in rows
    ]
    counts = {
        "all": len(items),
        "accepted": sum(item.status == "accepted" for item in items),
        "wrong_answer": sum(item.status == "wrong_answer" for item in items),
        "compile_error": sum(item.status == "compile_error" for item in items),
        "pending": sum(item.status in ("pending", "processing") for item in items),
    }
    return StudentSubmissionListResponse(items=items, total=len(items), counts=counts)


def _build_student_detail(
    submission: Submission,
    problem: Problem,
    lesson: Lesson,
    course: Course | None,
    testcases: list[Testcase],
) -> StudentSubmissionDetailResponse:
    return StudentSubmissionDetailResponse(
        id=submission.submission_id,
        problem_id=problem.problem_id,
        problem_code=problem.report,
        problem_title=problem.title,
        course_id=course.course_id if course else "",
        course_name=course.course_name if course else "",
        lesson_id=lesson.lesson_id,
        session_label=f"Buổi {lesson.lesson_number}: {lesson.lesson_name}",
        language=submission.language,
        submitted_code=submission.submitted_code,
        status=submission.status,
        compile_output=submission.compile_output,
        feedback=submission.feedback,
        passed_count=submission.passed_count,
        total_testcases=problem.total_number_testcase,
        submitted_datetime=submission.submitted_datetime,
        testcases=[
            StudentSubmissionTestcaseResponse(
                id=testcase.testcase_id,
                **testcase_to_api_values(testcase),
                is_sample=True,
            )
            for testcase in testcases
            if testcase.is_sample
        ],
    )


def get_student_submission_detail(
    session: Session,
    current_user: User,
    submission_id: int,
) -> StudentSubmissionDetailResponse:
    """Xem chi tiết kết quả chấm của một bài nộp - chỉ chính chủ bài nộp được xem."""
    _assert_student(current_user)
    rows = [
        row
        for row in _student_rows(session, current_user.user_id)
        if row[0].submission_id == submission_id
    ]
    if not rows:
        # Trả 404 chứ không phải 403 để không lộ sự tồn tại của bài nộp người khác.
        raise NotFoundError("Không tìm thấy bài nộp")
    submission, problem, lesson, course = rows[0]
    testcases = session.exec(
        select(Testcase)
        .where(Testcase.problem_id == problem.problem_id)
        .order_by(Testcase.testcase_id)
    ).all()
    return _build_student_detail(submission, problem, lesson, course, list(testcases))
