"""Ngân hàng bài chung chỉ Admin được ghi; Teacher tạo bài mới thẳng trong buổi học.

Cover: Teacher bị 403 khi tạo/import/sửa/xoá bài bank, và
``POST /courses/{course_id}/lessons/{lesson_id}/problems/new`` tạo bài gắn buổi
học (không để lại bản trong bank), đúng lịch buổi học, đúng quyền chủ lớp.
"""

from collections.abc import Iterator
import json

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.main import app
from app.models import Problem
from app.modules.problems.service import lesson_problem_window

pytest_plugins = ("tests.support.fixtures.problem_fixtures",)


@pytest.fixture()
def client(session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _login(user) -> None:
    app.dependency_overrides[get_current_user] = lambda: user


def _payload(**overrides) -> dict:
    base = {
        "title": "Sum Two Numbers",
        "function_name": "sumTwoNumbers",
        "description": "Return the sum of two numbers.",
        "constraints": "-1000 <= a, b <= 1000",
        "level": "easy",
        "time_limit_seconds": 2,
        "starter_codes": {
            "python": "class Solution:\n    def sumTwoNumbers(self, a, b): pass",
            "javascript": "function sumTwoNumbers(a, b) { return a + b; }",
        },
        "start_datetime": "2026-01-01T00:00:00+07:00",
        "end_datetime": "2099-12-31T23:59:00+07:00",
        "testcases": [
            {"input": [i, i + 1], "expected_output": 2 * i + 1, "is_sample": i < 3}
            for i in range(10)
        ],
    }
    base.update(overrides)
    return base


# ---------- Ghi vào ngân hàng: chỉ Admin ----------


def test_teacher_cannot_create_bank_problem(client, session, problem_teacher):
    _login(problem_teacher)

    response = client.post("/problems", json=_payload())

    assert response.status_code == 403
    assert session.exec(select(Problem)).all() == []


def test_admin_can_create_bank_problem(client, problem_admin):
    _login(problem_admin)

    response = client.post("/problems", json=_payload())

    assert response.status_code == 201, response.text
    assert response.json()["lesson_id"] is None


@pytest.mark.parametrize("endpoint", ["/problems/import", "/problems/import/preview"])
def test_teacher_cannot_import_bank_problems(client, problem_teacher, endpoint):
    _login(problem_teacher)
    raw = json.dumps({"problems": [_payload()]}).encode()

    response = client.post(endpoint, files={"file": ("p.json", raw, "application/json")})

    assert response.status_code == 403


def test_teacher_cannot_update_or_delete_bank_problem(
    client, problem_teacher, problem_bank_problem
):
    _login(problem_teacher)
    problem_id = problem_bank_problem.problem_id

    assert client.patch(f"/problems/{problem_id}", json={"title": "Đổi tên"}).status_code == 403
    assert client.delete(f"/problems/{problem_id}").status_code == 403


def test_teacher_can_still_list_and_view_bank_problems(client, problem_teacher, problem_bank_problem):
    _login(problem_teacher)

    assert client.get("/problems").status_code == 200
    assert client.get(f"/problems/{problem_bank_problem.problem_id}").status_code == 200


# ---------- Tạo bài thẳng trong buổi học ----------


def test_owner_teacher_creates_problem_directly_in_lesson(
    client, session, problem_teacher, problem_course, problem_lesson
):
    _login(problem_teacher)

    response = client.post(
        f"/courses/{problem_course.course_id}/lessons/{problem_lesson.lesson_id}/problems/new",
        json=_payload(),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["lesson_id"] == problem_lesson.lesson_id
    assert body["course_id"] == problem_course.course_id
    problems = session.exec(select(Problem)).all()
    # Không có bản nào nằm lại trong ngân hàng
    assert [p.lesson_id for p in problems] == [problem_lesson.lesson_id]
    assert problems[0].total_number_testcase == 10
    session.refresh(problem_lesson)
    assert problem_lesson.total_number_assignment == 1


def test_lesson_problem_schedule_follows_lesson_dates(
    client, session, problem_teacher, problem_course, problem_lesson
):
    _login(problem_teacher)

    response = client.post(
        f"/courses/{problem_course.course_id}/lessons/{problem_lesson.lesson_id}/problems/new",
        json=_payload(start_datetime="2030-05-01T00:00:00+07:00", end_datetime="2030-05-02T00:00:00+07:00"),
    )

    assert response.status_code == 201, response.text
    problem = session.get(Problem, response.json()["id"])
    start, end = lesson_problem_window(problem_lesson)
    assert (problem.start_datetime, problem.end_datetime) == (start, end)


def test_other_teacher_cannot_create_problem_in_lesson(
    client, session, problem_other_teacher, problem_course, problem_lesson
):
    _login(problem_other_teacher)

    response = client.post(
        f"/courses/{problem_course.course_id}/lessons/{problem_lesson.lesson_id}/problems/new",
        json=_payload(),
    )

    assert response.status_code == 403
    assert session.exec(select(Problem)).all() == []


def test_create_problem_in_lesson_of_other_course_returns_404(
    client, problem_teacher, problem_course, problem_other_lesson
):
    _login(problem_teacher)

    response = client.post(
        f"/courses/{problem_course.course_id}/lessons/{problem_other_lesson.lesson_id}/problems/new",
        json=_payload(),
    )

    assert response.status_code == 404


def test_student_cannot_create_problem_in_lesson(
    client, problem_student, problem_course, problem_lesson
):
    _login(problem_student)

    response = client.post(
        f"/courses/{problem_course.course_id}/lessons/{problem_lesson.lesson_id}/problems/new",
        json=_payload(),
    )

    assert response.status_code == 403
