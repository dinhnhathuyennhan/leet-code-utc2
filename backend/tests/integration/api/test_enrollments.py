"""HTTP integration tests cho endpoint enrollment.

Tập trung vào phân biệt `student_id` (UUID của user) và `student_code` (MSSV).
"""

import pytest

from app.core.dependencies import get_current_user
from app.main import app

pytest_plugins = (
    "tests.support.fixtures.api_fixtures",
    "tests.support.fixtures.user_fixtures",
    "tests.support.fixtures.course_fixtures",
)


@pytest.fixture
def as_user():
    def _login(user):
        app.dependency_overrides[get_current_user] = lambda: user

    yield _login
    app.dependency_overrides.pop(get_current_user, None)


class TestAddStudentRoute:
    # POST bằng MSSV → 201, response có cả UUID và MSSV
    def test_add_by_student_code_returns_201(
        self, client, as_user, course, owner_teacher, student
    ):
        as_user(owner_teacher)

        response = client.post(
            f"/courses/{course.course_id}/enrollments",
            json={"student_code": student.student_code},
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["student_id"] == str(student.user_id)
        assert body["student_code"] == student.student_code

    # MSSV gửi dạng số JSON vẫn được nhận
    def test_add_by_numeric_student_code_returns_201(
        self, client, as_user, course, owner_teacher, student
    ):
        as_user(owner_teacher)

        response = client.post(
            f"/courses/{course.course_id}/enrollments",
            json={"student_code": int(student.student_code)},
        )

        assert response.status_code == 201, response.text
        assert response.json()["student_code"] == student.student_code

    # form gửi kèm student_id rỗng → bỏ qua, dùng student_code
    def test_blank_student_id_with_student_code_returns_201(
        self, client, as_user, course, owner_teacher, student
    ):
        as_user(owner_teacher)

        response = client.post(
            f"/courses/{course.course_id}/enrollments",
            json={"student_id": "  ", "student_code": student.student_code},
        )

        assert response.status_code == 201, response.text

    # POST bằng UUID vẫn hoạt động như cũ
    def test_add_by_student_id_returns_201(
        self, client, as_user, course, owner_teacher, student
    ):
        as_user(owner_teacher)

        response = client.post(
            f"/courses/{course.course_id}/enrollments",
            json={"student_id": str(student.user_id)},
        )

        assert response.status_code == 201, response.text
        assert response.json()["student_code"] == student.student_code

    # Tương thích form FE hiện tại: MSSV gửi qua student_id vẫn thêm được
    def test_student_code_sent_as_student_id_returns_201(
        self, client, as_user, course, owner_teacher, student
    ):
        as_user(owner_teacher)

        response = client.post(
            f"/courses/{course.course_id}/enrollments",
            json={"student_id": student.student_code},
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["student_id"] == str(student.user_id)
        assert body["student_code"] == student.student_code

    # student_id không phải UUID và không khớp MSSV nào → 404
    def test_unknown_non_uuid_student_id_returns_404(
        self, client, as_user, course, owner_teacher
    ):
        as_user(owner_teacher)

        response = client.post(
            f"/courses/{course.course_id}/enrollments",
            json={"student_id": "0000000000"},
        )

        assert response.status_code == 404
        assert response.json()["error_code"] == "NOT_FOUND"

    # body rỗng → 422 EMPTY_FIELD đi qua AppError handler
    def test_empty_body_returns_empty_field(self, client, as_user, course, owner_teacher):
        as_user(owner_teacher)

        response = client.post(f"/courses/{course.course_id}/enrollments", json={})

        assert response.status_code == 422
        assert response.json()["error_code"] == "EMPTY_FIELD"

    # gửi cả 2 → 422 INVALID_FORMAT
    def test_both_identifiers_returns_invalid_format(
        self, client, as_user, course, owner_teacher, student
    ):
        as_user(owner_teacher)

        response = client.post(
            f"/courses/{course.course_id}/enrollments",
            json={"student_id": str(student.user_id), "student_code": student.student_code},
        )

        assert response.status_code == 422
        assert response.json()["error_code"] == "INVALID_FORMAT"

    # MSSV sai định dạng → 422 INVALID_FORMAT với message cụ thể
    def test_malformed_student_code_returns_invalid_format(
        self, client, as_user, course, owner_teacher
    ):
        as_user(owner_teacher)

        response = client.post(
            f"/courses/{course.course_id}/enrollments",
            json={"student_code": "12345"},
        )

        assert response.status_code == 422
        body = response.json()
        assert body["error_code"] == "INVALID_FORMAT"
        assert "10 chữ số" in body["message"]

    # teacher không sở hữu khoá → 403
    def test_other_teacher_returns_403(
        self, client, as_user, course, other_teacher, student
    ):
        as_user(other_teacher)

        response = client.post(
            f"/courses/{course.course_id}/enrollments",
            json={"student_code": student.student_code},
        )

        assert response.status_code == 403

    # sinh viên không được gọi endpoint thêm SV
    def test_student_role_returns_403(self, client, as_user, course, student):
        as_user(student)

        response = client.post(
            f"/courses/{course.course_id}/enrollments",
            json={"student_code": student.student_code},
        )

        assert response.status_code == 403


class TestListEnrollmentsRoute:
    # GET danh sách trả student_code (MSSV) bên cạnh student_id (UUID)
    def test_list_contains_student_code(
        self, client, as_user, course, owner_teacher, student
    ):
        as_user(owner_teacher)
        client.post(
            f"/courses/{course.course_id}/enrollments",
            json={"student_code": student.student_code},
        )

        response = client.get(f"/courses/{course.course_id}/enrollments")

        assert response.status_code == 200
        rows = response.json()
        assert rows == [
            {
                "enrollment_id": rows[0]["enrollment_id"],
                "student_id": str(student.user_id),
                "student_code": student.student_code,
                "full_name": student.full_name,
                "email": student.email,
            }
        ]
