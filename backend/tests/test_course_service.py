from datetime import datetime

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.services.course_service import (
    add_student_to_course,
    delete_student_from_course,
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
