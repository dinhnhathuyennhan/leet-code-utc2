from datetime import date

import pytest

from app.core.exceptions import ConflictError
from app.core.password import hash_password, verify_password
from app.dependencies import Role
from app.schemas.user import CreateStudentRequest, CreateTeacherRequest
from app.services.user_service import (
    DateOfBirthRequiredError,
    NotAllowedToResetError,
    UserNotFoundError,
    create_student,
    create_teacher,
    reset_password,
)
from models import Course, Enrollment, User


def _make_user(
    session,
    user_id: str,
    email: str,
    role_id: int,
    date_of_birth=None,
    password: str = "old-password-123",
    token_version: int = 0,
):
    user = User(
        user_id=user_id,
        full_name=user_id,
        email=email,
        hashed_password=hash_password(password),
        date_of_birth=date_of_birth,
        role_id=role_id,
        token_version=token_version,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# region Test create_student

def test_create_student_success(session):
    data = CreateStudentRequest(
        user_id="6451071055",
        full_name="Đinh Nhật Huyền Nhân",
        date_of_birth="31/08/2005",
        email="6451071055@st.utc2.edu.vn",
    )
    student = create_student(session, data)

    assert student.user_id == "6451071055"
    assert student.full_name == "Đinh Nhật Huyền Nhân"
    assert student.email == "6451071055@st.utc2.edu.vn"
    assert student.role_id == 3
    assert student.must_change_password is True
    assert student.date_of_birth == date(2005, 8, 31)


def test_create_student_accepts_dd_mm_yyyy_and_normalizes_to_date_object(session):
    data = CreateStudentRequest(
        user_id="6451071056",
        full_name="Nguyễn Văn A",
        date_of_birth="05-06-2000",
        email="6451071056@st.utc2.edu.vn",
    )
    student = create_student(session, data)

    assert student.date_of_birth == date(2000, 6, 5)


def test_create_student_accepts_iso_date_format(session):
    student = CreateStudentRequest(
        user_id="6451071057",
        full_name="Nguyễn Văn B",
        date_of_birth="2000-06-05",
        email="6451071057@st.utc2.edu.vn",
    )
    assert student.date_of_birth == date(2000, 6, 5)


def test_create_student_duplicate_email_raises(session):
    data = CreateStudentRequest(
        user_id="6451071055",
        full_name="Đinh Nhật Huyền Nhân",
        date_of_birth="31/08/2005",
        email="6451071055@st.utc2.edu.vn",
    )

    create_student(session, data)

    with pytest.raises(ConflictError):
        create_student(session, data)


def test_create_student_invalid_age_raises(session):
    data = CreateStudentRequest(
        user_id="6451071055",
        full_name="Đinh Nhật Huyền Nhân",
        date_of_birth="31/08/2020",
        email="6451071055@st.utc2.edu.vn",
    )

    with pytest.raises(DateOfBirthRequiredError):
        create_student(session, data)


# endregion

# region Test create_teacher


def test_create_teacher_success(session):
    data = CreateTeacherRequest(
        user_id="teacher_IT_001",
        full_name="Đinh Nhật Huyền Nhân",
        date_of_birth="15/05/1980",
        email="huyennhan@st.utc2.edu.vn",
    )
    teacher = create_teacher(session, data)

    assert teacher.user_id == "teacher_IT_001"
    assert teacher.full_name == "Đinh Nhật Huyền Nhân"
    assert teacher.email == "huyennhan@st.utc2.edu.vn"
    assert teacher.role_id == 2
    assert teacher.must_change_password is True


def test_create_teacher_duplicate_email_raises(session):
    data = CreateTeacherRequest(
        user_id="teacher_IT_001",
        full_name="Đinh Nhật Huyền Nhân",
        date_of_birth="15/05/1980",
        email="huyennhan@st.utc2.edu.vn",
    )

    create_teacher(session, data)

    with pytest.raises(ConflictError):
        create_teacher(session, data)


def test_create_teacher_invalid_date_of_birth_raises(session):
    data = CreateTeacherRequest(
        user_id="teacher_IT_001",
        full_name="Đinh Nhật Huyền Nhân",
        date_of_birth="15/05/2020",
        email="huyennhan@st.utc2.edu.vn",
    )

    with pytest.raises(DateOfBirthRequiredError):
        create_teacher(session, data)


# endregion

# region Test reset_password

def test_reset_password_admin_can_reset_any_user(session):
    from datetime import date

    admin = _make_user(session, "admin1", "admin@example.com", Role.ADMIN)
    target = _make_user(
        session,
        "student1",
        "student@example.com",
        Role.STUDENT,
        date_of_birth=date(2005, 8, 31),
        password="abc12345",
    )

    returned_id, temporary_password = reset_password(session, admin, target.user_id)

    assert returned_id == target.user_id
    assert temporary_password == "31082005"
    assert temporary_password != "abc12345"

    session.refresh(target)
    assert verify_password(temporary_password, target.hashed_password)
    assert target.must_change_password is True
    assert target.token_version == 1


def test_reset_password_teacher_can_reset_student_in_their_class(session):
    from datetime import date, datetime, timedelta

    teacher = _make_user(session, "teacher1", "teacher@example.com", Role.TEACHER)
    student = _make_user(
        session,
        "student2",
        "student2@example.com",
        Role.STUDENT,
        date_of_birth=date(2005, 8, 31),
        password="abc12345",
    )

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
    assert temporary_password == "31082005"

    session.refresh(student)
    assert verify_password(temporary_password, student.hashed_password)
    assert student.must_change_password is True
    assert student.token_version == 1


def test_reset_password_teacher_cannot_reset_teacher(session):
    teacher = _make_user(session, "teacher2", "teacher2@example.com", Role.TEACHER)
    other_teacher = _make_user(
        session, "teacher3", "teacher3@example.com", Role.TEACHER
    )

    with pytest.raises(NotAllowedToResetError):
        reset_password(session, teacher, other_teacher.user_id)


def test_reset_password_teacher_cannot_reset_admin(session):
    teacher = _make_user(session, "teacher4", "teacher4@example.com", Role.TEACHER)
    admin = _make_user(session, "admin2", "admin2@example.com", Role.ADMIN)

    with pytest.raises(NotAllowedToResetError):
        reset_password(session, teacher, admin.user_id)


def test_reset_password_user_not_found(session):
    admin = _make_user(session, "admin3", "admin3@example.com", Role.ADMIN)

    with pytest.raises(UserNotFoundError):
        reset_password(session, admin, "missing-user-id")


def test_reset_password_increments_token_version_each_time(session):
    from datetime import date

    admin = _make_user(session, "admin4", "admin4@example.com", Role.ADMIN)
    target = _make_user(
        session,
        "student3",
        "student3@example.com",
        Role.STUDENT,
        date_of_birth=date(2005, 8, 31),
        password="abc12345",
    )

    reset_password(session, admin, target.user_id)
    session.refresh(target)
    assert target.token_version == 1

    reset_password(session, admin, target.user_id)
    session.refresh(target)
    assert target.token_version == 2


def test_reset_password_teacher_cannot_reset_student_outside_their_class(session):
    from datetime import date, datetime, timedelta

    teacher = _make_user(session, "teacher5", "teacher5@example.com", Role.TEACHER)
    other_teacher = _make_user(
        session, "teacher6", "teacher6@example.com", Role.TEACHER
    )
    student = _make_user(
        session,
        "student4",
        "student4@example.com",
        Role.STUDENT,
        date_of_birth=date(2005, 8, 31),
        password="abc12345",
    )

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

    with pytest.raises(NotAllowedToResetError):
        reset_password(session, teacher, student.user_id)


def test_reset_password_student_is_blocked_completely(session):
    from datetime import date

    student_a = _make_user(
        session,
        "student_a",
        "student_a@example.com",
        Role.STUDENT,
        date_of_birth=date(2005, 1, 1),
    )
    student_b = _make_user(
        session,
        "student_b",
        "student_b@example.com",
        Role.STUDENT,
        date_of_birth=date(2005, 1, 2),
    )
    teacher = _make_user(session, "teacher7", "teacher7@example.com", Role.TEACHER)
    admin = _make_user(session, "admin5", "admin5@example.com", Role.ADMIN)

    with pytest.raises(NotAllowedToResetError):
        reset_password(session, student_a, student_b.user_id)
    with pytest.raises(NotAllowedToResetError):
        reset_password(session, student_a, teacher.user_id)
    with pytest.raises(NotAllowedToResetError):
        reset_password(session, student_a, admin.user_id)


def test_reset_password_teacher_cannot_reset_self(session):
    teacher = _make_user(session, "teacher8", "teacher8@example.com", Role.TEACHER)

    with pytest.raises(NotAllowedToResetError):
        reset_password(session, teacher, teacher.user_id)


def test_reset_password_requires_date_of_birth(session):
    """Nếu tài khoản mục tiêu chưa có ngày sinh thì không thể reset mật khẩu."""
    admin = _make_user(session, "admin6", "admin6@example.com", Role.ADMIN)
    target = _make_user(
        session,
        "student_no_dob",
        "student_no_dob@example.com",
        Role.STUDENT,
        date_of_birth=None,
        password="abc12345",
    )

    with pytest.raises(DateOfBirthRequiredError):
        reset_password(session, admin, target.user_id)

# endregion
