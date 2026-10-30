"""HTTP integration tests for course endpoints."""

from app.core.dependencies import get_current_user
from app.main import app

from tests.support.fixtures.course_fixtures import make_course
from tests.support.fixtures.user_fixtures import make_user

pytest_plugins = (
    "tests.support.fixtures.api_fixtures",
    "tests.support.fixtures.user_fixtures",
    "tests.support.fixtures.course_fixtures",
)


# ============================== ROUTE LAYER ==============================
# Test các endpoint POST /courses và PATCH /courses/{id} qua TestClient
# để đảm bảo status code + JSON response mapping đúng.


class TestCourseRoutes:
    """Test endpoint HTTP layer qua TestClient, bypass JWT bằng dependency override."""

    # POST /courses — happy path trả về 201 với body đúng shape
    def test_post_courses_returns_201(self, client, session, owner_teacher):
        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        payload = {
            "course_id": "CS_HTTP_1",
            "course_name": "Qua HTTP",
            "term": "HK1 2026-2027",
            "start_date": "2026-09-07T00:00:00+07:00",
            "end_date": "2026-12-27T00:00:00+07:00",
        }
        response = client.post("/courses", json=payload)
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["course_id"] == "CS_HTTP_1"
        assert body["created_by"] == str(owner_teacher.user_id)
        assert body["total_number_student"] == 0
        app.dependency_overrides.clear()

    # POST /courses — thiếu field bắt buộc → 422
    def test_post_courses_missing_required_field_returns_422(
        self, client, owner_teacher
    ):
        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        payload = {
            # thiếu course_name cố ý
            "course_id": "CS_HTTP_BAD",
            "term": "HK1",
            "start_date": "2026-09-07T00:00:00+07:00",
            "end_date": "2026-12-27T00:00:00+07:00",
        }
        response = client.post("/courses", json=payload)
        assert response.status_code == 422
        app.dependency_overrides.clear()

    # POST /courses — trùng course_id → 409
    def test_post_courses_duplicate_returns_409(
        self, client, session, owner_teacher, course
    ):
        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        payload = {
            "course_id": course.course_id,  # CS101 — đã tồn tại từ fixture
            "course_name": "Trùng",
            "term": "HK1",
            "start_date": "2026-09-07T00:00:00+07:00",
            "end_date": "2026-12-27T00:00:00+07:00",
        }
        response = client.post("/courses", json=payload)
        assert response.status_code == 409
        app.dependency_overrides.clear()

    # PATCH /courses/{id} — owner teacher update course_name → 200
    def test_patch_courses_owner_returns_200(
        self, client, session, course, owner_teacher
    ):
        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        response = client.patch(
            f"/courses/{course.course_id}",
            json={"course_name": "Tên mới qua HTTP"},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["course_name"] == "Tên mới qua HTTP"
        assert body["course_id"] == course.course_id
        app.dependency_overrides.clear()

    # PATCH /courses/{id} — teacher không phải chủ lớp → 403
    def test_patch_courses_other_teacher_returns_403(
        self, client, course, other_teacher
    ):
        app.dependency_overrides[get_current_user] = lambda: other_teacher

        response = client.patch(
            f"/courses/{course.course_id}",
            json={"course_name": "Hack"},
        )
        assert response.status_code == 403
        app.dependency_overrides.clear()

    # PATCH /courses/{id} — course không tồn tại → 404
    def test_patch_courses_missing_returns_404(self, client, owner_teacher):
        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        response = client.patch(
            "/courses/KHONG_CO",
            json={"course_name": "X"},
        )
        assert response.status_code == 404
        app.dependency_overrides.clear()

    # PATCH /courses/{id} — body rỗng → 200 no-op
    def test_patch_courses_empty_body_is_noop(self, client, course, owner_teacher):
        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        response = client.patch(f"/courses/{course.course_id}", json={})
        assert response.status_code == 200
        assert response.json()["course_name"] == course.course_name
        app.dependency_overrides.clear()

    # PATCH /courses/{id} — gửi field=null phải bị bỏ qua → 200
    def test_patch_courses_null_field_is_ignored(self, client, course, owner_teacher):
        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        original_name = course.course_name
        response = client.patch(
            f"/courses/{course.course_id}",
            json={"course_name": None, "term": "HK Mới"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["course_name"] == original_name  # KHÔNG bị ghi đè None
        assert body["term"] == "HK Mới"
        app.dependency_overrides.clear()

    # PATCH /courses/{id} — chỉ gửi start_date trùng/sau end_date DB → 422
    def test_patch_courses_only_start_after_db_end_returns_422(
        self, client, course, owner_teacher
    ):
        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        response = client.patch(
            f"/courses/{course.course_id}",
            json={"start_date": "2027-01-01T00:00:00+07:00"},  # sau end_date DB
        )
        assert response.status_code == 422
        app.dependency_overrides.clear()

    # POST /courses — datetime không kèm múi giờ → 422 INVALID_FORMAT qua Global Exception Handler
    def test_post_courses_naive_datetime_returns_invalid_format(self, client, owner_teacher):
        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        response = client.post(
            "/courses",
            json={
                "course_id": "CS_HTTP_NAIVE",
                "course_name": "Thiếu offset",
                "term": "HK1 2026-2027",
                "start_date": "2026-09-07T00:00:00",
                "end_date": "2026-12-27T00:00:00+07:00",
            },
        )

        assert response.status_code == 422
        body = response.json()
        assert body["error_code"] == "INVALID_FORMAT"
        assert "start_date" in body["message"]
        assert "phải kèm múi giờ" in body["message"]
        app.dependency_overrides.clear()

    # POST /courses — datetime có offset được nhận và response chuẩn hóa về giờ Việt Nam.
    def test_post_courses_offset_datetime_is_returned_in_vietnam_timezone(self, client, owner_teacher):
        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        payload = {
            "course_id": "CS_HTTP_OFFSET",
            "course_name": "Có offset",
            "term": "HK1 2026-2027",
            "start_date": "2026-09-07T00:00:00+07:00",
            "end_date": "2026-12-27T00:00:00+07:00",
        }
        response = client.post("/courses", json=payload)

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["start_date"] == "2026-09-07T00:00:00+07:00"
        assert body["end_date"] == "2026-12-27T00:00:00+07:00"
        app.dependency_overrides.clear()

    # PATCH /courses/{id} — datetime trả về theo giờ Việt Nam có offset.
    def test_patch_courses_returns_vietnam_local_datetime_with_offset(self, client, course, owner_teacher):
        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        response = client.patch(
            f"/courses/{course.course_id}",
            json={"end_date": "2027-01-15T00:00:00+07:00"},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["end_date"] == "2027-01-15T00:00:00+07:00"
        assert body["start_date"] == "2026-09-07T00:00:00+07:00"
        app.dependency_overrides.clear()




class TestGetCourseRoutes:
    """Test HTTP cho GET /courses và GET /courses/{course_id}."""

    # GET /courses — teacher nhận 200, chỉ có lớp của mình
    def test_get_courses_returns_200(
        self, client, session, course, owner_teacher, other_teacher
    ):
        make_course(session, "CS102", other_teacher)
        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        response = client.get("/courses")

        assert response.status_code == 200, response.text
        body = response.json()
        assert len(body) == 1
        assert body[0]["course_id"] == "CS101"
        assert body[0]["created_by"] == str(owner_teacher.user_id)
        app.dependency_overrides.clear()

    # GET /courses — role lạ nhận 403 qua Global Exception Handler
    def test_get_courses_unknown_role_returns_403(self, client, session, course):
        stranger = make_user(session, "XX001", 99)
        app.dependency_overrides[get_current_user] = lambda: stranger

        response = client.get("/courses")

        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"
        app.dependency_overrides.clear()

    # GET /courses/{id} — chủ lớp nhận 200 với body đúng shape
    def test_get_course_owner_returns_200(self, client, course, owner_teacher):
        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        response = client.get(f"/courses/{course.course_id}")

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["course_id"] == course.course_id
        assert body["course_name"] == course.course_name
        assert body["total_number_student"] == 0
        app.dependency_overrides.clear()

    # GET /courses/{id} — student ngoài lớp nhận 403
    def test_get_course_student_not_enrolled_returns_403(
        self, client, course, student
    ):
        app.dependency_overrides[get_current_user] = lambda: student

        response = client.get(f"/courses/{course.course_id}")

        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"
        app.dependency_overrides.clear()

    # GET /courses/{id} — course_id không tồn tại nhận 404
    def test_get_course_missing_returns_404(self, client, admin):
        app.dependency_overrides[get_current_user] = lambda: admin

        response = client.get("/courses/KHONG_CO")

        assert response.status_code == 404
        assert response.json()["error_code"] == "NOT_FOUND"
        app.dependency_overrides.clear()