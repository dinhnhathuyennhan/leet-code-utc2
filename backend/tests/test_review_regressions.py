from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError
from sqlmodel import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.dependencies import Role
from app.schemas.problem import ProblemUpdateRequest
from app.schemas.testcase import TestcaseUpdateRequest as PatchTestcaseRequest
from app.services.course_view import build_course_response
from app.services.lesson_service import get_lesson_detail
from app.services.problem_service import copy_problems_to_lesson, update_problem
from app.services.submission_service import list_pending_submissions
from app.services.testcase_format import testcase_to_storage as to_storage
from app.services.testcase_import import parse_testcases
from app.services.testcase_service import export_testcases
from models import Course, Enrollment, Lesson, Problem, Submission, Testcase as CaseModel, User


def _user(session: Session, user_id: str, role_id: int) -> User:
    user = User(
        user_id=user_id,
        full_name=f"User {user_id}",
        email=f"{user_id.lower()}@example.com",
        hashed_password="not-a-real-hash",
        role_id=role_id,
    )
    session.add(user)
    session.flush()
    return user


def _course(session: Session, owner: User) -> Course:
    course = Course(
        course_id=f"C-{owner.user_id}",
        course_name="Review course",
        created_by=owner.user_id,
        term="HK1 2026-2027",
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2027, 1, 1),
        total_number_student=0,
    )
    session.add(course)
    session.flush()
    return course


def _lesson(session: Session, course: Course) -> Lesson:
    lesson = Lesson(
        lesson_number=1,
        lesson_name="Lesson 1",
        course_id=course.course_id,
        start_date=date(2026, 1, 1),
        end_date=date(2027, 1, 1),
    )
    session.add(lesson)
    session.flush()
    return lesson


def _problem(session: Session, lesson: Lesson, *, start_datetime: datetime | None = None) -> Problem:
    problem = Problem(
        lesson_id=lesson.lesson_id,
        title="Two Sum",
        function_name="twoSum",
        description="Return indices.",
        time_limit_seconds=2,
        start_format_code="class Solution:\n    pass\n",
        starter_codes={"python": "class Solution:\n    pass\n"},
        constraints="1 <= n <= 10",
        level="easy",
        start_datetime=start_datetime or datetime(2026, 1, 1),
        end_datetime=datetime(2027, 1, 1),
        total_number_testcase=2,
    )
    session.add(problem)
    session.flush()
    return problem


def _submission(session: Session, problem: Problem, student: User, status: str, passed: int = 0) -> Submission:
    submission = Submission(
        problem_id=problem.problem_id,
        student_id=student.user_id,
        language="python",
        submitted_code="class Solution: pass",
        status=status,
        passed_count=passed,
        submitted_datetime=datetime(2026, 10, 1),
    )
    session.add(submission)
    session.flush()
    return submission


def test_testcase_patch_rejects_explicit_null_input_but_allows_omitted_input():
    with pytest.raises(ValidationError, match="input không được là null"):
        PatchTestcaseRequest.model_validate({"input": None})

    assert PatchTestcaseRequest.model_validate({}).model_dump(exclude_unset=True) == {}
    assert PatchTestcaseRequest.model_validate({"expected_output": None}).model_dump(
        exclude_unset=True
    ) == {"expected_output": None}


def test_admin_copy_of_missing_problem_returns_404(session: Session):
    admin = _user(session, "AD001", Role.ADMIN)
    course = _course(session, admin)
    lesson = _lesson(session, course)

    with pytest.raises(NotFoundError, match="Một hoặc nhiều bài tập không tồn tại"):
        copy_problems_to_lesson(session, [99999], lesson, admin)


def test_lesson_stats_ignore_submissions_from_unenrolled_students(session: Session):
    teacher = _user(session, "GV001", Role.TEACHER)
    enrolled = _user(session, "SV001", Role.STUDENT)
    former_student = _user(session, "SV002", Role.STUDENT)
    course = _course(session, teacher)
    lesson = _lesson(session, course)
    problem = _problem(session, lesson)
    session.add(Enrollment(course_id=course.course_id, student_id=enrolled.user_id))
    session.add(_submission(session, problem, former_student, "accepted", passed=2))
    session.commit()

    detail = get_lesson_detail(session, course.course_id, lesson.lesson_id, teacher)

    assert detail.total_students == 1
    assert detail.submitted_students == 0
    assert detail.stats.completed_students == 0
    assert detail.stats.avg_score == 0
    assert detail.exercises[0].submitted_count == 0


def test_problem_grading_metadata_is_locked_after_first_submission(session: Session):
    teacher = _user(session, "GV001", Role.TEACHER)
    student = _user(session, "SV001", Role.STUDENT)
    course = _course(session, teacher)
    lesson = _lesson(session, course)
    problem = _problem(session, lesson)
    _submission(session, problem, student, "wrong_answer", passed=1)
    session.commit()
    update = ProblemUpdateRequest(
        function_name="twoSumV2",
        starter_codes={
            "python": "class Solution: pass",
            "c": "int twoSum(void) { return 0; }",
            "cpp": "int twoSum() { return 0; }",
            "java": "class Solution { int twoSum() { return 0; } }",
        },
    )

    with pytest.raises(ConflictError, match="không thể sửa thông tin ảnh hưởng đến chấm"):
        update_problem(session, course.course_id, lesson.lesson_id, problem.problem_id, update, teacher)

    session.refresh(problem)
    assert problem.function_name == "twoSum"


@pytest.mark.parametrize("export_format", ["json", "zip"])
def test_legacy_testcase_export_can_be_imported_without_changing_markers(
    session: Session, export_format: str
):
    teacher = _user(session, "GV001", Role.TEACHER)
    course = _course(session, teacher)
    lesson = _lesson(session, course)
    problem = _problem(session, lesson)
    session.add(
        CaseModel(
            problem_id=problem.problem_id,
            input="2 7 9",
            expected_output="0 1",
            is_sample=True,
            input_type="stdin",
            expected_output_type="stdout",
        )
    )
    session.add(
        CaseModel(
            problem_id=problem.problem_id,
            input='[[2,7],9]',
            expected_output="[0,1]",
            is_sample=False,
            input_type="json_args",
            expected_output_type="json",
        )
    )
    session.commit()

    content = export_testcases(session, course.course_id, lesson.lesson_id, problem.problem_id, export_format, teacher)
    parsed = parse_testcases(f"testcases.{export_format}", content)
    stored = [to_storage(item) for item in parsed]

    assert stored[0] == {
        "input": "2 7 9",
        "expected_output": "0 1",
        "is_sample": True,
        "input_type": "stdin",
        "expected_output_type": "stdout",
    }
    assert stored[1]["input_type"] == "json_args"
    assert stored[1]["expected_output_type"] == "json"
    assert stored[1]["input"] == "[[2,7],9]"


def test_pending_submission_counts_error_after_search(session: Session):
    teacher = _user(session, "GV001", Role.TEACHER)
    student = _user(session, "SV001", Role.STUDENT)
    course = _course(session, teacher)
    lesson = _lesson(session, course)
    problem = _problem(session, lesson)
    _submission(session, problem, student, "compile_error")
    session.commit()

    result = list_pending_submissions(session, teacher, search="SV001")

    assert result.counts["all"] == 1
    assert result.counts["error"] == 1


def test_student_course_grades_omit_problems_that_have_not_opened(session: Session):
    teacher = _user(session, "GV001", Role.TEACHER)
    student = _user(session, "SV001", Role.STUDENT)
    course = _course(session, teacher)
    lesson = _lesson(session, course)
    future_problem = _problem(
        session,
        lesson,
        start_datetime=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=2),
    )
    session.add(Enrollment(course_id=course.course_id, student_id=student.user_id))
    session.commit()

    response = build_course_response(course, session, only_student_id=student.user_id)

    assert response.sessions[0].problems == []
    assert response.grades[0].session_scores[str(lesson.lesson_id)] == []
    assert future_problem.problem_id is not None
