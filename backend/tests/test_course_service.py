from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.exceptions import (
    ConflictError,
    EmptyFieldError,
    ForbiddenError,
    InvalidFormatError,
    NotFoundError,
)
from app.dependencies import Role
from app.main import app
from app.schemas.course import CreateCourseRequest, UpdateCourseRequest
from app.services.course_service import (
    add_student_to_course,
    create_course,
    delete_student_from_course,
    update_course,
)
from models import Course, Enrollment, User

"""
Test các luồng nghiệp vụ chính của course_service.
Sử dụng SQLite in-memory thao tác nhanh, không cần Postgres.
"""


# ============================== FIXTURES ==============================

@pytest.fixture(name="session")
def session_fixture() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # giữ một connection duy nhất cho DB in-memory
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Iterator[TestClient]:
    """TestClient với session SQLite in-memory thông qua dependency override."""
    from app.db import get_session

    def _override_get_session():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_session] = _override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_user(session: Session, user_id: str, role_id: int) -> User:
    user = User(
        user_id=user_id,
        full_name=f"User {user_id}",
        email=f"{user_id.lower()}@example.com",
        hashed_password="not-a-real-hash",
        role_id=role_id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def admin(session: Session) -> User:
    return make_user(session, "AD001", Role.ADMIN)


@pytest.fixture
def owner_teacher(session: Session) -> User:
    return make_user(session, "GV001", Role.TEACHER)


@pytest.fixture
def other_teacher(session: Session) -> User:
    return make_user(session, "GV002", Role.TEACHER)


@pytest.fixture
def student(session: Session) -> User:
    return make_user(session, "SV001", Role.STUDENT)


@pytest.fixture
def course(session: Session, owner_teacher: User) -> Course:
    course = Course(
        course_id="CS101",
        course_name="Nhập môn lập trình",
        created_by=owner_teacher.user_id,
        term="HK1 2026-2027",
        start_date=datetime(2026, 9, 7),
        end_date=datetime(2026, 12, 27),
        total_number_student=0,
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def enrollments_of(session: Session, course_id: str) -> list[Enrollment]:
    return list(
        session.exec(select(Enrollment).where(Enrollment.course_id == course_id)).all()
    )


def counter_of(session: Session, course: Course) -> int:
    session.refresh(course)  # đọc lại từ DB, không tin object trong memory
    return course.total_number_student


def enroll_directly(session: Session, course: Course, student: User) -> None:
    """Dựng dữ liệu có sẵn cho test xoá, không đi qua service đang được test."""
    session.add(Enrollment(course_id=course.course_id, student_id=student.user_id))
    course.total_number_student += 1
    session.commit()


# ============================== ADD / REMOVE STUDENT ==============================

class TestAddStudentToCourse:

    # giảng viên chủ khóa học thêm sinh viên và tăng total_number_student
    def test_owner_teacher_adds_student_and_increments_counter(
        self, session, course, owner_teacher, student
    ):
        result = add_student_to_course(
            student.user_id, course.course_id, session, owner_teacher
        )

        assert result.course_id == course.course_id
        assert result.student_id == student.user_id
        assert result.enrollment_id is not None
        assert len(enrollments_of(session, course.course_id)) == 1
        assert counter_of(session, course) == 1

    # role admin không phải chủ khóa học
    # vẫn có thể thêm sinh viên và tăng total_number_student
    def test_admin_who_does_not_own_course_can_add_student(
        self, session, course, admin, student
    ):
        add_student_to_course(student.user_id, course.course_id, session, admin)

        assert counter_of(session, course) == 1

    # raise forbidden nếu giảng viên không phải chủ khóa học
    def test_raises_forbidden_when_teacher_does_not_own_course(
        self, session, course, other_teacher, student
    ):
        with pytest.raises(
            ForbiddenError,
            match="Bạn không có quyền thêm sinh viên vào lớp này"
        ):
            add_student_to_course(
                student.user_id, course.course_id, session, other_teacher
            )

        assert enrollments_of(session, course.course_id) == []
        assert counter_of(session, course) == 0

    # raise not found khi không tìm thấy sinh viên
    def test_raises_not_found_when_student_id_does_not_exist(
        self, session, course, owner_teacher
    ):
        with pytest.raises(
            NotFoundError, match="Không tìm thấy sinh viên"
        ):
            add_student_to_course(
                "KHONG_CO", course.course_id, session, owner_teacher
            )

        assert counter_of(session, course) == 0

    # raise not found khi student_id truyền vào không phải là sinh viên
    def test_raises_not_found_when_target_user_is_not_a_student(
        self, session, course, owner_teacher, other_teacher
    ):
        with pytest.raises(
            NotFoundError, match="Không tìm thấy sinh viên"
        ):
            add_student_to_course(
                other_teacher.user_id, course.course_id, session, owner_teacher
            )

        assert enrollments_of(session, course.course_id) == []

    # raise conflict khi sinh viên đã tồn tại trong khóa học
    def test_raises_conflict_when_student_already_enrolled(
        self, session, course, owner_teacher, student
    ):
        add_student_to_course(student.user_id, course.course_id, session, owner_teacher)

        with pytest.raises(
            ConflictError, match="Sinh viên đã có trong lớp học"
        ):
            add_student_to_course(
                student.user_id, course.course_id, session, owner_teacher
            )

        # lần thêm trùng không được để lại dòng thừa hay tăng counter
        assert len(enrollments_of(session, course.course_id)) == 1
        assert counter_of(session, course) == 1


class TestDeleteStudentFromCourse:

    # giảng viên chủ khóa học xóa sinh viên khỏi khóa và giảm total_number_student
    def test_owner_teacher_removes_student_and_decrements_counter(
        self, session, course, owner_teacher, student
    ):
        enroll_directly(session, course, student)

        delete_student_from_course(
            student.user_id, course.course_id, session, owner_teacher
        )

        assert enrollments_of(session, course.course_id) == []
        assert counter_of(session, course) == 0

    #raise forbidden khi giảng không phải chủ khóa học
    def test_raises_forbidden_when_teacher_does_not_own_course(
        self, session, course, other_teacher, student
    ):
        enroll_directly(session, course, student)

        with pytest.raises(
            ForbiddenError, match="Bạn không có quyền thực hiện hành động này"
        ):
            delete_student_from_course(
                student.user_id, course.course_id, session, other_teacher
            )

        # bị chặn thì dữ liệu phải giữ nguyên
        assert len(enrollments_of(session, course.course_id)) == 1
        assert counter_of(session, course) == 1

    # raise not found khi xóa sinh viên không thuộc về khóa học
    def test_raises_not_found_when_student_is_not_in_course(
        self, session, course, owner_teacher, student
    ):
        with pytest.raises(
            NotFoundError, match="Sinh viên không thuộc lớp học này"
        ):
            delete_student_from_course(
                student.user_id, course.course_id, session, owner_teacher
            )

        # counter không được âm khi xoá người không có trong lớp
        assert counter_of(session, course) == 0


# ============================== CREATE / UPDATE COURSE ==============================

VALID_START = datetime(2026, 9, 7)
VALID_END = datetime(2026, 12, 27)


def _make_create_request(
    course_id: str = "CS101",
    course_name: str = "Nhập môn lập trình",
    term: str = "HK1 2026-2027",
    start_date: datetime = VALID_START,
    end_date: datetime = VALID_END,
) -> CreateCourseRequest:
    return CreateCourseRequest(
        course_id=course_id,
        course_name=course_name,
        term=term,
        start_date=start_date,
        end_date=end_date,
    )


class TestCreateCourse:

    # Teacher tạo lớp — created_by và total_number_student do server set
    def test_teacher_creates_course_with_server_side_fields(
        self, session, owner_teacher
    ):
        result = create_course(_make_create_request(), session, owner_teacher)

        assert result.course_id == "CS101"
        assert result.course_name == "Nhập môn lập trình"
        assert result.created_by == owner_teacher.user_id
        assert result.total_number_student == 0
        assert result.avt_link is None

        saved = session.get(Course, "CS101")
        assert saved is not None
        assert saved.created_by == owner_teacher.user_id

    # Admin tạo lớp — cũng được, không phụ thuộc created_by
    def test_admin_creates_course(self, session, admin):
        result = create_course(_make_create_request(course_id="CS202"), session, admin)

        assert result.created_by == admin.user_id
        assert result.total_number_student == 0

    # Trùng course_id → 409
    def test_raises_conflict_when_course_id_already_exists(
        self, session, owner_teacher, course
    ):
        with pytest.raises(ConflictError, match="Mã lớp học đã tồn tại"):
            create_course(_make_create_request(), session, owner_teacher)

    # start_date phải trước end_date — validation tại schema layer
    def test_raises_invalid_format_when_start_after_end(
        self, session, owner_teacher
    ):
        with pytest.raises(InvalidFormatError, match="start_date phải trước end_date"):
            CreateCourseRequest(
                course_id="CS303",
                course_name="Sai ngày",
                term="HK1 2026-2027",
                start_date=datetime(2026, 12, 27),
                end_date=datetime(2026, 9, 7),
            )

    # start_date bằng end_date cũng reject — validation tại schema layer
    def test_raises_invalid_format_when_start_equals_end(
        self, session, owner_teacher
    ):
        same_day = datetime(2026, 9, 7)
        with pytest.raises(InvalidFormatError, match="start_date phải trước end_date"):
            CreateCourseRequest(
                course_id="CS304",
                course_name="Bằng ngày",
                term="HK1 2026-2027",
                start_date=same_day,
                end_date=same_day,
            )

    # field bắt buộc bị rỗng → validation tại schema layer
    def test_raises_empty_field_when_course_name_blank(
        self, session, owner_teacher
    ):
        with pytest.raises(EmptyFieldError, match="course_name"):
            CreateCourseRequest(
                course_id="CS305",
                course_name="   ",
                term="HK1 2026-2027",
                start_date=VALID_START,
                end_date=VALID_END,
            )

    # course_id dài quá 50 ký tự → 422 (giới hạn cột DB)
    def test_raises_error_when_course_id_too_long(
        self, session, owner_teacher
    ):
        from pydantic import ValidationError

        too_long = "C" * 51
        # max_length=50 là constraint của pydantic → raise ValidationError.
        # Trên FastAPI layer sẽ được convert thành 422 response.
        with pytest.raises(ValidationError):
            CreateCourseRequest(
                course_id=too_long,
                course_name="OK",
                term="HK1",
                start_date=VALID_START,
                end_date=VALID_END,
            )

    # avt_link dài quá 2048 ký tự → 422 (giới hạn cột DB)
    def test_raises_error_when_avt_link_too_long(
        self, session, owner_teacher
    ):
        from pydantic import ValidationError

        too_long = "https://x.com/" + ("a" * 2048)
        with pytest.raises(ValidationError):
            CreateCourseRequest(
                course_id="CS_OK",
                course_name="OK",
                term="HK1",
                start_date=VALID_START,
                end_date=VALID_END,
                avt_link=too_long,
            )

    # Gửi null cho field bắt buộc → 422 EMPTY_FIELD (trước kia raise message
    # chung tiếng Anh của pydantic)
    def test_raises_empty_field_when_required_field_missing(
        self, session, owner_teacher
    ):
        # Pydantic v2 với Field(...) coi None là input không hợp lệ và raise
        # ValidationError. Trên FastAPI layer sẽ được convert thành 422.
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CreateCourseRequest(
                course_id="CS_OK",
                course_name=None,  # type: ignore[arg-type]
                term="HK1",
                start_date=VALID_START,
                end_date=VALID_END,
            )


class TestUpdateCourse:

    # Teacher chủ lớp cập nhật 1 vài field — các field không gửi phải giữ nguyên
    def test_owner_teacher_updates_only_sent_fields(
        self, session, course, owner_teacher
    ):
        update = UpdateCourseRequest(course_name="Tên mới", term="HK2 2026-2027")

        result = update_course(course.course_id, update, session, owner_teacher)

        assert result.course_name == "Tên mới"
        assert result.term == "HK2 2026-2027"
        # course_id, created_by, total_number_student, start/end_date phải KHÔNG đổi
        assert result.course_id == course.course_id
        assert result.created_by == owner_teacher.user_id
        assert result.total_number_student == course.total_number_student
        assert result.start_date == course.start_date
        assert result.end_date == course.end_date

    # Admin cập nhật lớp của teacher khác — được phép
    def test_admin_can_update_any_course(self, session, course, admin):
        update = UpdateCourseRequest(avt_link="https://cdn/avt.png")

        result = update_course(course.course_id, update, session, admin)

        assert result.avt_link == "https://cdn/avt.png"

    # Teacher không phải chủ lớp → 403
    def test_raises_forbidden_when_teacher_does_not_own_course(
        self, session, course, other_teacher
    ):
        update = UpdateCourseRequest(course_name="Hack")

        with pytest.raises(
            ForbiddenError, match="Bạn không có quyền thực hiện hành động này"
        ):
            update_course(course.course_id, update, session, other_teacher)

        # dữ liệu không được đổi
        assert course.course_name != "Hack"

    # course_id không tồn tại → 404
    def test_raises_not_found_when_course_id_missing(self, session, owner_teacher):
        update = UpdateCourseRequest(course_name="X")

        with pytest.raises(NotFoundError, match="Không tìm thấy lớp học"):
            update_course("KHONG_CO", update, session, owner_teacher)

    # Nếu đổi cả start_date và end_date mà sai thứ tự → 422
    def test_raises_invalid_format_when_new_date_range_invalid(
        self, session, course, owner_teacher
    ):
        with pytest.raises(InvalidFormatError, match="start_date phải trước end_date"):
            UpdateCourseRequest(
                start_date=datetime(2026, 12, 27),
                end_date=datetime(2026, 9, 7),
            )

    # Có thể đổi end_date một mình nếu vẫn sau start_date hiện tại
    def test_can_update_only_end_date(self, session, course, owner_teacher):
        update = UpdateCourseRequest(end_date=datetime(2027, 1, 15))

        result = update_course(course.course_id, update, session, owner_teacher)

        assert result.end_date == datetime(2027, 1, 15)
        assert result.start_date == course.start_date

    # Truyền chuỗi rỗng cho field optional → 422 EmptyFieldError
    def test_raises_empty_field_when_optional_str_blank(
        self, session, course, owner_teacher
    ):
        with pytest.raises(EmptyFieldError, match="course_name"):
            UpdateCourseRequest(course_name="   ")

    # PATCH body rỗng → no-op, trả về 200 với dữ liệu hiện tại
    def test_empty_body_is_noop(self, session, course, owner_teacher):
        result = update_course(course.course_id, UpdateCourseRequest(), session, owner_teacher)

        assert result.course_id == course.course_id
        assert result.course_name == course.course_name

    # PATCH: chỉ gửi start_date mà end_date hiện tại lại trước/sau → 422
    def test_raises_invalid_format_when_only_start_date_collides_with_db_end(
        self, session, course, owner_teacher
    ):
        # course hiện tại có end_date = 2026-12-27.
        # Gửi start_date mới = 2027-01-01 (sau end_date DB) → 422.
        with pytest.raises(InvalidFormatError, match="start_date phải trước end_date"):
            update_course(
                course.course_id,
                UpdateCourseRequest(start_date=datetime(2027, 1, 1)),
                session,
                owner_teacher,
            )

    # PATCH: chỉ gửi end_date mà start_date hiện tại lại sau → 422
    def test_raises_invalid_format_when_only_end_date_collides_with_db_start(
        self, session, course, owner_teacher
    ):
        # course hiện tại có start_date = 2026-09-07.
        # Gửi end_date mới = 2026-08-01 (trước start_date DB) → 422.
        with pytest.raises(InvalidFormatError, match="start_date phải trước end_date"):
            update_course(
                course.course_id,
                UpdateCourseRequest(end_date=datetime(2026, 8, 1)),
                session,
                owner_teacher,
            )

    # PATCH: gửi field=null phải được bỏ qua, không ghi đè cột NOT NULL → 200
    def test_null_field_is_ignored_not_overwritten(
        self, session, course, owner_teacher
    ):
        original_name = course.course_name

        result = update_course(
            course.course_id,
            UpdateCourseRequest(course_name=None, term="HK Mới"),
            session,
            owner_teacher,
        )

        assert result.course_name == original_name  # không bị ghi đè thành None
        assert result.term == "HK Mới"

    # PATCH: start_date tz-aware + end_date tz-naive (khi chỉ gửi 1 trong 2)
    # phải không gây TypeError → so sánh với giá trị DB ổn định
    def test_update_with_tz_aware_datetime_does_not_raise_type_error(
        self, session, course, owner_teacher
    ):
        # end_date trong DB là naive; gửi start_date tz-aware.
        # Service phải chuẩn hoá rồi so sánh, không raise TypeError.
        tz_aware = datetime(2026, 10, 1, tzinfo=UTC)
        result = update_course(
            course.course_id,
            UpdateCourseRequest(start_date=tz_aware),
            session,
            owner_teacher,
        )

        # So sánh theo giá trị naive (SQLite strip timezone khi ghi).
        assert result.start_date.replace(tzinfo=None) == datetime(2026, 10, 1)
        assert result.end_date == course.end_date


# ============================== ROUTE LAYER ==============================
# Test các endpoint POST /courses và PATCH /courses/{id} qua TestClient
# để đảm bảo status code + JSON response mapping đúng.


class TestCourseRoutes:
    """Test endpoint HTTP layer qua TestClient, bypass JWT bằng dependency override."""

    def _make_stub_require_role(self, user: User):
        """Tạo dependency function trả về user cố định, bỏ qua kiểm tra role."""
        def stub():
            return user
        return stub

    # POST /courses — happy path trả về 201 với body đúng shape
    def test_post_courses_returns_201(
        self, client, session, owner_teacher
    ):
        from app.dependencies import get_current_user

        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        payload = {
            "course_id": "CS_HTTP_1",
            "course_name": "Qua HTTP",
            "term": "HK1 2026-2027",
            "start_date": "2026-09-07T00:00:00",
            "end_date": "2026-12-27T00:00:00",
        }
        response = client.post("/courses", json=payload)
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["course_id"] == "CS_HTTP_1"
        assert body["created_by"] == owner_teacher.user_id
        assert body["total_number_student"] == 0
        app.dependency_overrides.clear()

    # POST /courses — thiếu field bắt buộc → 422
    def test_post_courses_missing_required_field_returns_422(
        self, client, owner_teacher
    ):
        from app.dependencies import get_current_user

        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        payload = {
            # thiếu course_name cố ý
            "course_id": "CS_HTTP_BAD",
            "term": "HK1",
            "start_date": "2026-09-07T00:00:00",
            "end_date": "2026-12-27T00:00:00",
        }
        response = client.post("/courses", json=payload)
        assert response.status_code == 422
        app.dependency_overrides.clear()

    # POST /courses — trùng course_id → 409
    def test_post_courses_duplicate_returns_409(
        self, client, session, owner_teacher, course
    ):
        from app.dependencies import get_current_user

        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        payload = {
            "course_id": course.course_id,  # CS101 — đã tồn tại từ fixture
            "course_name": "Trùng",
            "term": "HK1",
            "start_date": "2026-09-07T00:00:00",
            "end_date": "2026-12-27T00:00:00",
        }
        response = client.post("/courses", json=payload)
        assert response.status_code == 409
        app.dependency_overrides.clear()

    # PATCH /courses/{id} — owner teacher update course_name → 200
    def test_patch_courses_owner_returns_200(
        self, client, session, course, owner_teacher
    ):
        from app.dependencies import get_current_user

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
        from app.dependencies import get_current_user

        app.dependency_overrides[get_current_user] = lambda: other_teacher

        response = client.patch(
            f"/courses/{course.course_id}",
            json={"course_name": "Hack"},
        )
        assert response.status_code == 403
        app.dependency_overrides.clear()

    # PATCH /courses/{id} — course không tồn tại → 404
    def test_patch_courses_missing_returns_404(self, client, owner_teacher):
        from app.dependencies import get_current_user

        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        response = client.patch(
            "/courses/KHONG_CO",
            json={"course_name": "X"},
        )
        assert response.status_code == 404
        app.dependency_overrides.clear()

    # PATCH /courses/{id} — body rỗng → 200 no-op
    def test_patch_courses_empty_body_is_noop(
        self, client, course, owner_teacher
    ):
        from app.dependencies import get_current_user

        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        response = client.patch(f"/courses/{course.course_id}", json={})
        assert response.status_code == 200
        assert response.json()["course_name"] == course.course_name
        app.dependency_overrides.clear()

    # PATCH /courses/{id} — gửi field=null phải bị bỏ qua → 200
    def test_patch_courses_null_field_is_ignored(
        self, client, course, owner_teacher
    ):
        from app.dependencies import get_current_user

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
        from app.dependencies import get_current_user

        app.dependency_overrides[get_current_user] = lambda: owner_teacher

        response = client.patch(
            f"/courses/{course.course_id}",
            json={"start_date": "2027-01-01T00:00:00"},  # sau end_date DB
        )
        assert response.status_code == 422
        app.dependency_overrides.clear()
