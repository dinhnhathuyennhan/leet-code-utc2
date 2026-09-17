import pytest

from app.core.password import verify_password
from app.dependencies import Role
from app.services.user_service import (
    NotAllowedToResetError,
    UserNotFoundError,
    reset_password,
)
from models import Course, Enrollment, User


def make_user(
    session,
    user_id: str,
    email: str,
    role_id: int,
    password: str = "old-password-123",
    token_version: int = 0,
):
    user = User(
        user_id=user_id,
        full_name=user_id,
        email=email,
        hashed_password=verify_password.__self__ if False else "placeholder",
        role_id=role_id,
        token_version=token_version,
    )
    # hash thật để có thể test verify
    from app.core.password import hash_password

    user.hashed_password = hash_password(password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_reset_password_admin_can_reset_any_user(session):
    admin = make_user(session, "admin1", "admin@example.com", Role.ADMIN)
    target = make_user(
        session, "student1", "student@example.com", Role.STUDENT, password="abc12345"
    )

    returned_id, temporary_password = reset_password(session, admin, target.user_id)

    assert returned_id == target.user_id
    assert temporary_password
    assert temporary_password != "abc12345"

    session.refresh(target)
    assert verify_password(temporary_password, target.hashed_password)
    assert target.must_change_password is True
    assert target.token_version == 1


def test_reset_password_teacher_can_reset_student(session):
    teacher = make_user(session, "teacher1", "teacher@example.com", Role.TEACHER)
    student = make_user(
        session, "student2", "student2@example.com", Role.STUDENT, password="abc12345"
    )

    # Setup: tạo lớp do giáo viên quản lý và cho sinh viên vào lớp đó
    from datetime import datetime, timedelta

    course = Course(
        course_id="course1",
        course_name="Course 1",
        created_by=teacher.user_id,
        term="2026",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        total_number_student=1,
    )
    session.add(course)
    session.commit()
    session.refresh(course)

    enrollment = Enrollment(course_id=course.course_id, student_id=student.user_id)
    session.add(enrollment)
    session.commit()

    _, temporary_password = reset_password(session, teacher, student.user_id)

    session.refresh(student)
    assert verify_password(temporary_password, student.hashed_password)
    assert student.must_change_password is True
    assert student.token_version == 1


def test_reset_password_teacher_cannot_reset_teacher(session):
    teacher = make_user(session, "teacher2", "teacher2@example.com", Role.TEACHER)
    other_teacher = make_user(
        session, "teacher3", "teacher3@example.com", Role.TEACHER
    )

    with pytest.raises(NotAllowedToResetError):
        reset_password(session, teacher, other_teacher.user_id)


def test_reset_password_teacher_cannot_reset_admin(session):
    teacher = make_user(session, "teacher4", "teacher4@example.com", Role.TEACHER)
    admin = make_user(session, "admin2", "admin2@example.com", Role.ADMIN)

    with pytest.raises(NotAllowedToResetError):
        reset_password(session, teacher, admin.user_id)


def test_reset_password_user_not_found(session):
    admin = make_user(session, "admin3", "admin3@example.com", Role.ADMIN)

    with pytest.raises(UserNotFoundError):
        reset_password(session, admin, "missing-user-id")


def test_reset_password_increments_token_version_each_time(session):
    admin = make_user(session, "admin4", "admin4@example.com", Role.ADMIN)
    target = make_user(
        session, "student3", "student3@example.com", Role.STUDENT, password="abc12345"
    )

    reset_password(session, admin, target.user_id)
    session.refresh(target)
    assert target.token_version == 1

    reset_password(session, admin, target.user_id)
    session.refresh(target)
    assert target.token_version == 2


def test_reset_password_teacher_cannot_reset_student_outside_their_class(session):
    """Giáo viên CHỈ được reset sinh viên trong lớp mình quản lý,
    sinh viên ngoài lớp thì bị chặn."""
    from datetime import datetime, timedelta

    teacher = make_user(session, "teacher5", "teacher5@example.com", Role.TEACHER)
    other_teacher = make_user(
        session, "teacher6", "teacher6@example.com", Role.TEACHER
    )
    student = make_user(
        session, "student4", "student4@example.com", Role.STUDENT, password="abc12345"
    )

    # Tạo lớp do giáo viên KHÁC quản lý, gán sinh viên vào đó
    course = Course(
        course_id="course-other",
        course_name="Other Course",
        created_by=other_teacher.user_id,
        term="2026",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        total_number_student=1,
    )
    session.add(course)
    session.commit()
    session.refresh(course)

    enrollment = Enrollment(course_id=course.course_id, student_id=student.user_id)
    session.add(enrollment)
    session.commit()

    # teacher5 không quản lý lớp này → bị chặn
    with pytest.raises(NotAllowedToResetError):
        reset_password(session, teacher, student.user_id)


def test_reset_password_student_is_blocked_completely(session):
    """Sinh viên bị chặn hoàn toàn — không reset được bất kỳ ai."""
    student_a = make_user(
        session, "student_a", "student_a@example.com", Role.STUDENT
    )
    student_b = make_user(
        session, "student_b", "student_b@example.com", Role.STUDENT
    )
    teacher = make_user(session, "teacher7", "teacher7@example.com", Role.TEACHER)
    admin = make_user(session, "admin5", "admin5@example.com", Role.ADMIN)

    # Sinh viên không reset được sinh viên khác
    with pytest.raises(NotAllowedToResetError):
        reset_password(session, student_a, student_b.user_id)
    # Sinh viên không reset được giáo viên
    with pytest.raises(NotAllowedToResetError):
        reset_password(session, student_a, teacher.user_id)
    # Sinh viên không reset được admin
    with pytest.raises(NotAllowedToResetError):
        reset_password(session, student_a, admin.user_id)


def test_reset_password_teacher_cannot_reset_self(session):
    """Giáo viên không được tự reset mật khẩu của mình."""
    teacher = make_user(session, "teacher8", "teacher8@example.com", Role.TEACHER)

    with pytest.raises(NotAllowedToResetError):
        reset_password(session, teacher, teacher.user_id)
