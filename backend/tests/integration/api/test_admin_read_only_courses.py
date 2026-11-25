"""Admin chỉ xem lớp học phần, không vận hành lớp học.

Admin không tạo/sửa lớp, không can thiệp buổi học, bài tập trong buổi, testcase,
ghi danh, bài nộp (các việc đó do giảng viên chủ lớp làm), nhưng vẫn xem được lớp,
buổi học, danh sách sinh viên, bảng điểm, testcase và vẫn xoá được lớp.
"""

import pytest

from app.core.dependencies import Role, get_current_user
from app.main import app
from tests.support.fixtures.builders import (
    make_course,
    make_enrollment,
    make_lesson,
    make_problem,
    make_submission,
    make_testcase,
    make_user,
)

pytest_plugins = ("tests.support.fixtures.api_fixtures",)

COURSE = "/courses/CS101"
LESSON = COURSE + "/lessons/{lesson_id}"
PROBLEM = LESSON + "/problems/{problem_id}"
TESTCASES = PROBLEM + "/testcases"


@pytest.fixture
def setup(session):
    admin = make_user(session, "AD001", Role.ADMIN)
    teacher = make_user(session, "GV001", Role.TEACHER)
    student = make_user(session, "SV001", Role.STUDENT)
    course = make_course(session, teacher, "CS101")
    lesson = make_lesson(session, course)
    problem = make_problem(session, lesson)
    testcase = make_testcase(session, problem)
    make_enrollment(session, course, student)
    submission = make_submission(session, problem, student)
    ids = {
        "lesson_id": lesson.lesson_id,
        "problem_id": problem.problem_id,
        "testcase_id": testcase.testcase_id,
        "submission_id": submission.submission_id,
        "student_id": student.user_id,
    }
    return admin, teacher, ids


@pytest.fixture
def as_user():
    def login(user):
        app.dependency_overrides[get_current_user] = lambda: user

    yield login
    app.dependency_overrides.pop(get_current_user, None)


# (method, path) của mọi API ghi vào lớp học mà Admin không được gọi.
ADMIN_FORBIDDEN_WRITES = [
    ("POST", "/courses"),
    ("PATCH", COURSE),
    ("POST", COURSE + "/lessons"),
    ("PATCH", COURSE + "/lessons/reorder"),
    ("PATCH", LESSON),
    ("DELETE", LESSON),
    ("POST", LESSON + "/duplicate"),
    ("POST", LESSON + "/problems"),
    ("POST", LESSON + "/problems/new"),
    ("PATCH", PROBLEM),
    ("DELETE", PROBLEM),
    ("POST", PROBLEM + "/testcases/upload"),
    ("POST", TESTCASES),
    ("PATCH", TESTCASES + "/batch"),
    ("PATCH", TESTCASES + "/{testcase_id}"),
    ("DELETE", TESTCASES + "/{testcase_id}"),
    ("POST", COURSE + "/enrollments"),
    ("POST", COURSE + "/enrollments/class"),
    ("DELETE", COURSE + "/enrollments/{student_id}"),
    ("GET", "/submissions/pending"),
    ("GET", "/submissions/{submission_id}"),
    ("PATCH", "/submissions/{submission_id}"),
    ("POST", "/submissions/{submission_id}/regrade"),
]


@pytest.mark.parametrize(("method", "path"), ADMIN_FORBIDDEN_WRITES)
def test_admin_cannot_operate_course(client, session, setup, as_user, method, path):
    admin, _teacher, ids = setup
    as_user(admin)

    response = client.request(method, path.format(**ids), json={})

    assert response.status_code == 403, response.text


# (path) các API chỉ đọc mà Admin vẫn dùng để xem lớp học phần.
ADMIN_ALLOWED_READS = [
    COURSE,
    COURSE + "/enrollments",
    LESSON,
    PROBLEM,
    TESTCASES,
    TESTCASES + "/download?format=json",
    COURSE + "/grades/export",
]


@pytest.mark.parametrize("path", ADMIN_ALLOWED_READS)
def test_admin_can_view_course(client, session, setup, as_user, path):
    admin, _teacher, ids = setup
    as_user(admin)

    response = client.get(path.format(**ids))

    assert response.status_code == 200, response.text


def test_owner_teacher_still_updates_course(client, session, setup, as_user):
    _admin, teacher, _ids = setup
    as_user(teacher)

    response = client.patch(COURSE, json={"course_name": "Đổi tên"})

    assert response.status_code == 200, response.text
    assert response.json()["course_name"] == "Đổi tên"


def test_owner_teacher_still_reads_submission(client, session, setup, as_user):
    _admin, teacher, ids = setup
    as_user(teacher)

    response = client.get(f"/submissions/{ids['submission_id']}")

    assert response.status_code == 200, response.text
