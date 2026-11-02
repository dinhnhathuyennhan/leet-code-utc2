"""Plain model builders shared by the Lesson, Problem, and Testcase fixtures."""

from datetime import date, datetime
from typing import Any
import uuid

from sqlmodel import Session

from app.core.utils.datetime_utils import VN_TZ
from app.core.dependencies import Role
from app.models.entities import Course, Enrollment, Lesson, Problem, Submission, Testcase, User
from app.modules.problems.schemas import ProblemCreateRequest


def make_user(session: Session, user_id: str, role_id: int) -> User:
    student_code = None
    if role_id == Role.STUDENT:
        student_code = (
            user_id
            if user_id.isascii() and user_id.isdigit() and len(user_id) == 10
            else f"{uuid.uuid5(uuid.NAMESPACE_DNS, user_id).int % 10**10:010d}"
        )
    user = User(
        user_id=uuid.UUID(user_id) if _is_uuid(user_id) else uuid.uuid4(),
        student_code=student_code,
        full_name=f"User {user_id}",
        email=f"{user_id.lower()}@example.com",
        hashed_password="test-hash",
        role_id=role_id,
    )
    session.add(user)
    session.flush()
    return user


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except (TypeError, ValueError, AttributeError):
        return False
    return True


def make_course(session: Session, owner: User, course_id: str) -> Course:
    course = Course(
        course_id=course_id,
        course_name=f"Course {course_id}",
        created_by=owner.user_id,
        term="HK1 2026-2027",
        start_date=datetime(2026, 1, 1, tzinfo=VN_TZ),
        end_date=datetime(2027, 1, 1, tzinfo=VN_TZ),
        total_number_student=0,
    )
    session.add(course)
    session.flush()
    return course


def make_lesson(
    session: Session,
    course: Course,
    lesson_name: str = "Lesson 1",
    start_date: date = date(2026, 1, 1),
    end_date: date = date(2026, 1, 31),
    lesson_number: int = 1,
) -> Lesson:
    lesson = Lesson(
        lesson_number=lesson_number,
        lesson_name=lesson_name,
        course_id=course.course_id,
        start_date=start_date,
        end_date=end_date,
    )
    session.add(lesson)
    session.flush()
    return lesson


def make_problem(
    session: Session,
    lesson: Lesson | None = None,
    *,
    title: str = "Two Sum",
    start_datetime: datetime = datetime(2026, 1, 1, tzinfo=VN_TZ),
    end_datetime: datetime = datetime(2027, 1, 1, tzinfo=VN_TZ),
    starter_codes: dict[str, str] | None = None,
    **overrides: Any,
) -> Problem:
    codes = starter_codes or {
        "python": "class Solution:\n    def two_sum(self, nums, target): pass",
        "c": "int two_sum(void) { return 0; }",
        "cpp": "int two_sum() { return 0; }",
        "java": "class Solution { int two_sum() { return 0; } }",
    }
    fields: dict[str, Any] = {
        "lesson_id": lesson.lesson_id if lesson else None,
        "title": title,
        "function_name": "two_sum",
        "description": "Return matching indexes.",
        "time_limit_seconds": 2,
        "start_format_code": codes.get("python", "legacy python template"),
        "starter_codes": codes,
        "constraints": "1 <= n <= 100",
        "level": "easy",
        "hint": "Use a map.",
        "complexity": "O(n)",
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "total_number_testcase": 0,
        "report": "TWO_SUM",
    }
    fields.update(overrides)
    problem = Problem(**fields)
    session.add(problem)
    session.flush()
    return problem


def make_testcase(
    session: Session,
    problem: Problem,
    *,
    input_value: str = "[[2,7,11,15],9]",
    expected_output: str = "[0,1]",
    is_sample: bool = False,
    input_type: str = "json_args",
    expected_output_type: str = "json",
) -> Testcase:
    testcase = Testcase(
        problem_id=problem.problem_id,
        input=input_value,
        expected_output=expected_output,
        is_sample=is_sample,
        input_type=input_type,
        expected_output_type=expected_output_type,
    )
    session.add(testcase)
    session.flush()
    return testcase


def make_submission(
    session: Session,
    problem: Problem,
    student: User,
    *,
    status: str = "wrong_answer",
    passed_count: int = 0,
) -> Submission:
    submission = Submission(
        problem_id=problem.problem_id,
        student_id=student.user_id,
        language="python",
        submitted_code="class Solution: pass",
        status=status,
        passed_count=passed_count,
        submitted_datetime=datetime(2026, 1, 10, tzinfo=VN_TZ),
    )
    session.add(submission)
    session.flush()
    return submission


def make_enrollment(session: Session, course: Course, student: User) -> Enrollment:
    enrollment = Enrollment(course_id=course.course_id, student_id=student.user_id)
    session.add(enrollment)
    session.flush()
    return enrollment


def make_problem_create_request(**overrides: Any) -> ProblemCreateRequest:
    payload: dict[str, Any] = {
        "title": "  Bank Problem  ",
        "function_name": "solve",
        "description": "Solve the task.",
        "constraints": "1 <= n <= 100",
        "level": "easy",
        "time_limit_seconds": 2,
        "starter_codes": {
            "python": "class Solution:\n    def solve(self): pass",
            "c": "int solve(void) { return 0; }",
            "cpp": "int solve() { return 0; }",
            "java": "class Solution { int solve() { return 0; } }",
        },
        "start_datetime": datetime(2026, 1, 1, tzinfo=VN_TZ),
        "end_datetime": datetime(2026, 2, 1, tzinfo=VN_TZ),
        "testcases": [
            {"input": [1, 2], "expected_output": 3, "is_sample": True},
        ],
    }
    payload.update(overrides)
    return ProblemCreateRequest(**payload)
