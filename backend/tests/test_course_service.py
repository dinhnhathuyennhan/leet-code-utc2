from datetime import datetime

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.exceptions import (
    ConflictError,
    EmptyFieldError,
    ForbiddenError,
    InvalidFormatError,
    NotFoundError,
)
from app.schemas.course import CreateCourseRequest, UpdateCourseRequest
from app.services.course_service import (
    add_student_to_course,
    create_course,
    delete_student_from_course,
    update_course,
)
from models import Course, Enrollment, User

"""
Test các luồng nghiệp vụ chính của add_student_to_course / delete_student_from_course.
    Sử sụng Sql-lite in memory thao tác nhanh không cần postgres
"""
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # giữ một connection duy nhất cho DB in-memory
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


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
def admin(session):
    return make_user(session, "AD001", 1)


@pytest.fixture
def owner_teacher(session):
    return make_user(session, "GV001", 2)


@pytest.fixture
def other_teacher(session):
    return make_user(session, "GV002", 2)


@pytest.fixture
def student(session):
    return make_user(session, "SV001", 3)


@pytest.fixture
def course(session, owner_teacher):
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


# ====== Dữ liệu mẫu dùng chung cho create_course / update_course ======

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
