"""
Test các endpoint mới được thêm/sửa để fix 3 lỗi:
- Lỗi 4: GET /courses?term=...&search=...  (filter server-side theo term/search)
- Lỗi 7: GET /students/{student_id}/courses
- Lỗi 8: GET /students/{student_id}/enrollments

Test cả 2 layer:
1. Service layer (unit) — gọi trực tiếp hàm trong app.modules.courses.service
2. HTTP layer (integration) — gọi qua TestClient với token giả lập
"""

import os
import uuid
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

# Load .env ở root project TRƯỚC khi import app modules
# (cần cho JWT_SECRET_KEY trong create_access_token)
_root_env = Path(__file__).resolve().parents[4] / ".env"
if _root_env.exists():
    from dotenv import load_dotenv
    load_dotenv(_root_env, override=False)

# Fallback nếu JWT_SECRET_KEY vẫn None (an toàn cho test)
if not os.getenv("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from app.core.exceptions import ForbiddenError, NotFoundError  # noqa: E402
from app.core.security.passwords import hash_password  # noqa: E402
from app.core.security.tokens import create_access_token  # noqa: E402
from app.core.dependencies import Role  # noqa: E402
from app.core.utils.datetime_utils import VN_TZ  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.courses.service import (  # noqa: E402
    get_courses,
    get_student_courses,
    get_student_enrollments,
)
from app.models import Course, Enrollment, User  # noqa: E402


# ============================== FIXTURES CHUNG ==============================


@pytest.fixture(name="session")
def session_fixture() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Iterator[TestClient]:
    from app.core.database import get_session

    def _override_get_session():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_session] = _override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_user(
    session: Session,
    user_id: str,
    role_id: int,
    *,
    email: str | None = None,
) -> User:
    user = User(
        user_id=uuid.uuid4(),
        student_code=(
            f"{uuid.uuid5(uuid.NAMESPACE_DNS, user_id).int % 10**10:010d}"
            if role_id == Role.STUDENT
            else None
        ),
        full_name=f"User {user_id}",
        email=email or f"{user_id.lower()}@utc2.edu.vn",
        hashed_password=hash_password("dummy"),
        role_id=role_id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def make_course(
    session: Session,
    course_id: str,
    owner: User,
    *,
    course_name: str | None = None,
    term: str = "HK1 2026-2027",
) -> Course:
    course = Course(
        course_id=course_id,
        course_name=course_name or f"Lớp {course_id}",
        created_by=owner.user_id,
        term=term,
        start_date=datetime(2026, 9, 7, tzinfo=VN_TZ),
        end_date=datetime(2026, 12, 27, tzinfo=VN_TZ),
        total_number_student=0,
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def enroll(session: Session, course_id: str, student_id: uuid.UUID) -> None:
    """Insert enrollment trực tiếp (bypass service đang test)."""
    session.add(Enrollment(course_id=course_id, student_id=student_id))
    course = session.get(Course, course_id)
    assert course is not None
    course.total_number_student += 1
    session.commit()


def auth_header(user: User) -> dict[str, str]:
    """Tạo Bearer token cho user (giả lập đăng nhập)."""
    token = create_access_token(
        user_id=user.user_id,
        role_id=user.role_id,
        token_version=user.token_version,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin(session: Session) -> User:
    return make_user(session, "AD001", Role.ADMIN)


@pytest.fixture
def teacher_a(session: Session) -> User:
    return make_user(session, "GV001", Role.TEACHER)


@pytest.fixture
def teacher_b(session: Session) -> User:
    return make_user(session, "GV002", Role.TEACHER)


@pytest.fixture
def student_a(session: Session) -> User:
    return make_user(session, "SV001", Role.STUDENT)


@pytest.fixture
def student_b(session: Session) -> User:
    return make_user(session, "SV002", Role.STUDENT)


# =========================================================================
# LỖI 4: GET /courses?term=...&search=...
# =========================================================================


class TestGetCoursesFilter:
    """Lỗi 4 — kiểm tra filter server-side theo term & search."""

    def test_admin_sees_all_courses_without_filter(
        self, session, admin, teacher_a, teacher_b
    ):
        make_course(session, "CS101", teacher_a, term="HK1 2026-2027")
        make_course(session, "CS102", teacher_b, term="HK2 2026-2027")
        make_course(session, "CS103", teacher_a, term="HK1 2025-2026")

        result = get_courses(session, admin)

        ids = {c.course_id for c in result}
        assert ids == {"CS101", "CS102", "CS103"}

    def test_filter_by_term_substring(self, session, admin, teacher_a, teacher_b):
        """term='HK1' phải match cả 2 course có 'HK1 2026-2027' và 'HK1 2025-2026'."""
        make_course(session, "CS101", teacher_a, term="HK1 2026-2027")
        make_course(session, "CS102", teacher_b, term="HK2 2026-2027")
        make_course(session, "CS103", teacher_a, term="HK1 2025-2026")

        result = get_courses(session, admin, term="HK1")

        ids = {c.course_id for c in result}
        assert ids == {"CS101", "CS103"}

    def test_filter_by_term_year_only(self, session, admin, teacher_a, teacher_b):
        """term='2026-2027' match cả HK1/HK2 của năm học 2026-2027.

        Lưu ý: nếu chỉ search "2026" thì cũng match cả "2025-2026"
        (vì "2026" xuất hiện ở cuối chuỗi) → test này dùng pattern
        đặc trưng hơn để tránh false positive.
        """
        make_course(session, "CS101", teacher_a, term="HK1 2026-2027")
        make_course(session, "CS102", teacher_b, term="HK2 2026-2027")
        make_course(session, "CS103", teacher_a, term="HK1 2025-2026")

        result = get_courses(session, admin, term="2026-2027")

        ids = {c.course_id for c in result}
        assert ids == {"CS101", "CS102"}

    def test_filter_by_search_matches_course_id(self, session, admin, teacher_a):
        make_course(session, "CS101", teacher_a, course_name="Nhập môn lập trình")
        make_course(session, "MATH202", teacher_a, course_name="Toán rời rạc")

        result = get_courses(session, admin, search="CS101")

        ids = {c.course_id for c in result}
        assert ids == {"CS101"}

    def test_filter_by_search_matches_course_name(self, session, admin, teacher_a):
        make_course(session, "CS101", teacher_a, course_name="Nhập môn lập trình")
        make_course(session, "CS102", teacher_a, course_name="Lập trình nâng cao")

        result = get_courses(session, admin, search="lập trình")

        ids = {c.course_id for c in result}
        assert ids == {"CS101", "CS102"}

    def test_combined_term_and_search(self, session, admin, teacher_a):
        make_course(session, "CS101", teacher_a, course_name="Lập trình C", term="HK1 2026-2027")
        make_course(session, "CS102", teacher_a, course_name="Lập trình Java", term="HK2 2026-2027")
        make_course(session, "MATH202", teacher_a, course_name="Toán rời rạc", term="HK1 2026-2027")

        result = get_courses(session, admin, term="HK1", search="CS")

        ids = {c.course_id for c in result}
        assert ids == {"CS101"}

    def test_escape_like_wildcards_in_term(self, session, admin, teacher_a):
        """Ký tự %, _ phải được escape — không match tất cả record."""
        make_course(session, "CS101", teacher_a, course_name="Lập trình")
        make_course(session, "CS102", teacher_a, course_name="Cơ sở dữ liệu")

        # Nếu không escape, % sẽ match tất cả
        result = get_courses(session, admin, term="100%")
        assert {c.course_id for c in result} == set()

    def test_teacher_only_sees_own_courses_even_with_filter(
        self, session, teacher_a, teacher_b
    ):
        make_course(session, "CS101", teacher_a, term="HK1 2026-2027")
        make_course(session, "CS102", teacher_b, term="HK1 2026-2027")

        result = get_courses(session, teacher_a, term="HK1")

        ids = {c.course_id for c in result}
        assert ids == {"CS101"}  # teacher_a không thấy lớp của teacher_b

    def test_student_only_sees_enrolled_courses_with_filter(
        self, session, teacher_a, student_a, student_b
    ):
        c1 = make_course(session, "CS101", teacher_a, term="HK1 2026-2027")
        make_course(session, "CS102", teacher_a, term="HK1 2026-2027")
        c3 = make_course(session, "CS103", teacher_a, term="HK2 2026-2027")

        enroll(session, c1.course_id, student_a.user_id)
        enroll(session, c3.course_id, student_a.user_id)
        enroll(session, "CS102", student_b.user_id)  # student_b vào CS102

        result = get_courses(session, student_a, term="HK1")

        ids = {c.course_id for c in result}
        # student_a chỉ thấy CS101 (đã enroll HK1), không thấy CS102 (student_b enroll)
        # cũng không thấy CS103 (HK2, đã filter)
        assert ids == {"CS101"}

    def test_student_course_filter_returns_course_once_when_duplicate_enrollment_is_rejected(
        self, session, teacher_a, student_a
    ):
        """Unique constraint rejects a duplicate enrollment; the student still sees the course."""
        c1 = make_course(session, "CS101", teacher_a)
        assert c1.course_id == "CS101"

        enroll(session, c1.course_id, student_a.user_id)
        session.add(Enrollment(course_id="CS101", student_id=student_a.user_id))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        result = get_courses(session, student_a)
        assert len(result) == 1
        assert result[0].course_id == "CS101"


# =========================================================================
# LỖI 7: GET /students/{student_id}/courses
# =========================================================================


class TestGetStudentCourses:
    """Lỗi 7 — lấy danh sách lớp của 1 sinh viên."""

    def test_student_sees_own_courses(
        self, session, student_a, teacher_a
    ):
        c1 = make_course(session, "CS101", teacher_a)
        c2 = make_course(session, "CS102", teacher_a)
        enroll(session, c1.course_id, student_a.user_id)
        enroll(session, c2.course_id, student_a.user_id)
        # student_a không enroll c3

        result = get_student_courses(session, student_a.user_id, student_a)

        ids = {c.course_id for c in result}
        assert ids == {"CS101", "CS102"}

    def test_admin_can_view_any_student_courses(
        self, session, admin, student_a, teacher_a
    ):
        c1 = make_course(session, "CS101", teacher_a)
        enroll(session, c1.course_id, student_a.user_id)

        result = get_student_courses(session, student_a.user_id, admin)
        assert len(result) == 1
        assert result[0].course_id == "CS101"

    def test_teacher_can_only_view_students_in_their_courses(
        self, session, teacher_a, teacher_b, student_a
    ):
        """Teacher chỉ xem được SV enroll lớp do mình tạo."""
        c_teacher_a = make_course(session, "CS101", teacher_a)
        c_teacher_b = make_course(session, "CS102", teacher_b)

        enroll(session, c_teacher_a.course_id, student_a.user_id)
        enroll(session, c_teacher_b.course_id, student_a.user_id)

        # teacher_a xem: chỉ thấy CS101 (lớp mình tạo)
        result = get_student_courses(session, student_a.user_id, teacher_a)
        ids = {c.course_id for c in result}
        assert ids == {"CS101"}

    def test_teacher_cannot_view_student_not_in_their_courses(
        self, session, teacher_a, teacher_b, student_a
    ):
        """teacher_a KHÔNG được xem SV chỉ enroll lớp của teacher_b."""
        c_teacher_b = make_course(session, "CS101", teacher_b)
        enroll(session, c_teacher_b.course_id, student_a.user_id)

        with pytest.raises(ForbiddenError, match="Bạn không có quyền xem thông tin sinh viên này"):
            get_student_courses(session, student_a.user_id, teacher_a)

    def test_student_cannot_view_other_student_courses(
        self, session, student_a, student_b, teacher_a
    ):
        c1 = make_course(session, "CS101", teacher_a)
        enroll(session, c1.course_id, student_b.user_id)

        with pytest.raises(ForbiddenError, match="Bạn không có quyền xem thông tin sinh viên này"):
            get_student_courses(session, student_b.user_id, student_a)

    def test_raises_not_found_for_nonexistent_student(self, session, admin):
        with pytest.raises(NotFoundError, match="Không tìm thấy sinh viên"):
            get_student_courses(session, uuid.uuid4(), admin)

    def test_raises_not_found_when_target_is_not_student(
        self, session, admin, teacher_a
    ):
        """Target là teacher thì raise NotFoundError (vì role_id != STUDENT)."""
        with pytest.raises(NotFoundError, match="Không tìm thấy sinh viên"):
            get_student_courses(session, teacher_a.user_id, admin)

    def test_student_courses_returns_course_once_when_duplicate_enrollment_is_rejected(
        self, session, admin, student_a, teacher_a
    ):
        """Unique constraint rejects a duplicate enrollment; the result remains unique."""
        course = make_course(session, "CS101", teacher_a)
        enroll(session, course.course_id, student_a.user_id)
        session.add(Enrollment(course_id="CS101", student_id=student_a.user_id))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        result = get_student_courses(session, student_a.user_id, admin)
        assert len(result) == 1

    def test_returns_empty_list_when_student_has_no_enrollments(
        self, session, student_a, admin
    ):
        result = get_student_courses(session, student_a.user_id, admin)
        assert result == []


# =========================================================================
# LỖI 8: GET /students/{student_id}/enrollments
# =========================================================================


class TestGetStudentEnrollments:
    """Lỗi 8 — lấy danh sách enrollment (kèm thông tin lớp)."""

    def test_returns_enrollment_with_course_info(
        self, session, admin, student_a, teacher_a
    ):
        c1 = make_course(
            session,
            "CS101",
            teacher_a,
            course_name="Nhập môn lập trình",
            term="HK1 2026-2027",
        )
        enroll(session, c1.course_id, student_a.user_id)

        result = get_student_enrollments(session, student_a.user_id, admin)

        assert len(result) == 1
        item = result[0]
        assert item.enrollment_id is not None
        assert item.course_id == "CS101"
        assert item.course_name == "Nhập môn lập trình"
        assert item.term == "HK1 2026-2027"

    def test_orders_by_enrollment_id_desc(self, session, admin, student_a, teacher_a):
        """Enrollment mới nhất lên đầu."""
        c1 = make_course(session, "CS101", teacher_a)
        c2 = make_course(session, "CS102", teacher_a)
        c3 = make_course(session, "CS103", teacher_a)
        enroll(session, c1.course_id, student_a.user_id)
        enroll(session, c2.course_id, student_a.user_id)
        enroll(session, c3.course_id, student_a.user_id)

        result = get_student_enrollments(session, student_a.user_id, admin)

        # Course id giảm dần (theo enrollment_id DESC, course_id tăng dần nên ngược lại thứ tự enroll)
        course_ids = [item.course_id for item in result]
        assert course_ids == ["CS103", "CS102", "CS101"]

    def test_student_sees_own_enrollments(self, session, student_a, teacher_a):
        c1 = make_course(session, "CS101", teacher_a)
        enroll(session, c1.course_id, student_a.user_id)

        result = get_student_enrollments(session, student_a.user_id, student_a)
        assert len(result) == 1

    def test_teacher_view_permission_same_as_courses(
        self, session, teacher_a, teacher_b, student_a
    ):
        c_teacher_b = make_course(session, "CS101", teacher_b)
        enroll(session, c_teacher_b.course_id, student_a.user_id)

        with pytest.raises(ForbiddenError):
            get_student_enrollments(session, student_a.user_id, teacher_a)

    def test_returns_empty_for_student_without_enrollments(
        self, session, admin, student_a
    ):
        result = get_student_enrollments(session, student_a.user_id, admin)
        assert result == []


# =========================================================================
# HTTP LAYER: TestClient với JWT token
# =========================================================================


class TestCoursesHttpEndpoint:
    """Test HTTP layer cho GET /courses với query param."""

    def test_get_courses_requires_authentication(self, client: TestClient):
        response = client.get("/courses")
        assert response.status_code == 401  # Bearer token thiếu

    def test_get_courses_with_term_filter_via_http(
        self, client: TestClient, session, admin, teacher_a
    ):
        make_course(session, "CS101", teacher_a, term="HK1 2026-2027")
        make_course(session, "CS102", teacher_a, term="HK2 2026-2027")

        response = client.get(
            "/courses",
            params={"term": "HK1"},
            headers=auth_header(admin),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["course_id"] == "CS101"
        assert data[0]["term"] == "HK1 2026-2027"

    def test_get_courses_with_search_via_http(
        self, client: TestClient, session, admin, teacher_a
    ):
        make_course(session, "CS101", teacher_a, course_name="Lập trình C")
        make_course(session, "MATH202", teacher_a, course_name="Toán rời rạc")

        response = client.get(
            "/courses",
            params={"search": "lập trình"},
            headers=auth_header(admin),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["course_id"] == "CS101"


class TestStudentCoursesHttpEndpoint:
    """Test HTTP layer cho GET /students/{id}/courses (Lỗi 7)."""

    def test_endpoint_requires_authentication(
        self, client: TestClient, student_a
    ):
        response = client.get(f"/students/{student_a.user_id}/courses")
        assert response.status_code == 401

    def test_student_can_get_own_courses_via_http(
        self, client: TestClient, session, student_a, teacher_a
    ):
        c1 = make_course(session, "CS101", teacher_a)
        enroll(session, c1.course_id, student_a.user_id)

        response = client.get(
            f"/students/{student_a.user_id}/courses",
            headers=auth_header(student_a),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["course_id"] == "CS101"

    def test_student_cannot_get_other_student_courses_via_http(
        self, client: TestClient, session, student_a, student_b, teacher_a
    ):
        c1 = make_course(session, "CS101", teacher_a)
        enroll(session, c1.course_id, student_b.user_id)

        response = client.get(
            f"/students/{student_b.user_id}/courses",
            headers=auth_header(student_a),
        )

        assert response.status_code == 403

    def test_admin_can_get_any_student_courses_via_http(
        self, client: TestClient, session, admin, student_a, teacher_a
    ):
        c1 = make_course(session, "CS101", teacher_a)
        enroll(session, c1.course_id, student_a.user_id)

        response = client.get(
            f"/students/{student_a.user_id}/courses",
            headers=auth_header(admin),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_404_for_nonexistent_student(
        self, client: TestClient, admin
    ):
        response = client.get(
            f"/students/{uuid.uuid4()}/courses",
            headers=auth_header(admin),
        )
        assert response.status_code == 404


class TestStudentEnrollmentsHttpEndpoint:
    """Test HTTP layer cho GET /students/{id}/enrollments (Lỗi 8)."""

    def test_endpoint_returns_enrollment_with_course_info_via_http(
        self, client: TestClient, session, student_a, teacher_a
    ):
        c1 = make_course(
            session,
            "CS101",
            teacher_a,
            course_name="Lập trình C",
            term="HK1 2026-2027",
        )
        enroll(session, c1.course_id, student_a.user_id)

        response = client.get(
            f"/students/{student_a.user_id}/enrollments",
            headers=auth_header(student_a),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        item = data[0]
        assert item["enrollment_id"] is not None
        assert item["course_id"] == "CS101"
        assert item["course_name"] == "Lập trình C"
        assert item["term"] == "HK1 2026-2027"
        # datetime phải là ISO string
        assert "2026-09-07" in item["start_date"]

    def test_student_cannot_get_other_student_enrollments_via_http(
        self, client: TestClient, session, student_a, student_b, teacher_a
    ):
        c1 = make_course(session, "CS101", teacher_a)
        enroll(session, c1.course_id, student_b.user_id)

        response = client.get(
            f"/students/{student_b.user_id}/enrollments",
            headers=auth_header(student_a),
        )
        assert response.status_code == 403

    def test_empty_list_when_student_has_no_enrollments(
        self, client: TestClient, student_a
    ):
        response = client.get(
            f"/students/{student_a.user_id}/enrollments",
            headers=auth_header(student_a),
        )
        assert response.status_code == 200
        assert response.json() == []


# =========================================================================
# Import ForbiddenError ở cuối để tránh phụ thuộc vòng
# =========================================================================
