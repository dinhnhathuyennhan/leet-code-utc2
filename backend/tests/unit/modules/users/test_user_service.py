from datetime import date, timedelta

import pytest

from app.core.utils.datetime_utils import now_utc
from app.core.exceptions import ConflictError, NotFoundError, InvalidFormatError
from app.core.security.passwords import hash_password, verify_password
from app.core.dependencies import Role
from app.modules.users.schemas import CreateStudentRequest, CreateTeacherRequest
from app.modules.users.service import (
    DateOfBirthRequiredError,
    NotAllowedToResetError,
    UserNotFoundError,
    create_student,
    create_teacher,
    reset_password, list_users,
)
from app.models import Class, Course, Enrollment, User


def _make_class(session, class_id: str = "CQ.64.CNTT"):
    c = Class(class_id=class_id, type="CQ", course_number=64, department="CNTT")
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


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


def _make_listed_user(
    session,
    user_id: str,
    role_id: int,
    class_id=None,
    date_of_birth=date(2005, 8, 31),
):
    """User có sẵn ngày sinh để không dính lỗi UserResponse khi list."""
    user = _make_user(
        session,
        user_id,
        f"{user_id}@example.com",
        role_id,
        date_of_birth=date_of_birth,
    )
    if class_id is not None:
        user.class_id = class_id
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

def _make_course(session, course_id: str, teacher):
    course = Course(
        course_id=course_id,
        course_name=course_id,
        created_by=teacher.user_id,
        term="2026",
        start_date=now_utc(),
        end_date=now_utc() + timedelta(days=30),
        total_number_student=0,
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def _enroll(session, course, student):
    session.add(Enrollment(course_id=course.course_id, student_id=student.user_id))
    session.commit()


def _call(session, current_user, role_id=None, class_id=None, page=1, page_size=10):
    return list_users(session, current_user, role_id, class_id, page, page_size)


def _ids(result) -> list:
    return [item.user_id for item in result.items]

# region Test create_student

def test_create_student_success(session):
    _make_class(session, "CQ.64.CNTT")
    data = CreateStudentRequest(
        user_id="6451071055",
        full_name="Đinh Nhật Huyền Nhân",
        date_of_birth="31/08/2005",
        email="6451071055@st.utc2.edu.vn",
        class_id="CQ.64.CNTT",
    )
    student = create_student(session, data)

    assert student.user_id == "6451071055"
    assert student.full_name == "Đinh Nhật Huyền Nhân"
    assert student.email == "6451071055@st.utc2.edu.vn"
    assert student.role_id == 3
    assert student.class_id == "CQ.64.CNTT"
    assert student.must_change_password is True
    assert student.date_of_birth == date(2005, 8, 31)
    assert verify_password("6451071055", student.hashed_password)


def test_create_student_accepts_dd_mm_yyyy_and_normalizes_to_date_object(session):
    _make_class(session, "CQ.64.CNTT")
    data = CreateStudentRequest(
        user_id="6451071056",
        full_name="Nguyễn Văn A",
        date_of_birth="05-06-2000",
        email="6451071056@st.utc2.edu.vn",
        class_id="CQ.64.CNTT",
    )
    student = create_student(session, data)

    assert student.date_of_birth == date(2000, 6, 5)


def test_create_student_accepts_iso_date_format(session):
    _make_class(session, "CQ.64.CNTT")
    student_req = CreateStudentRequest(
        user_id="6451071057",
        full_name="Nguyễn Văn B",
        date_of_birth="2000-06-05",
        email="6451071057@st.utc2.edu.vn",
        class_id="CQ.64.CNTT",
    )
    assert student_req.date_of_birth == date(2000, 6, 5)


def test_create_student_duplicate_email_raises(session):
    _make_class(session, "CQ.64.CNTT")
    data = CreateStudentRequest(
        user_id="6451071055",
        full_name="Đinh Nhật Huyền Nhân",
        date_of_birth="31/08/2005",
        email="6451071055@st.utc2.edu.vn",
        class_id="CQ.64.CNTT",
    )

    create_student(session, data)

    with pytest.raises(ConflictError):
        create_student(session, data)


def test_create_student_invalid_age_raises(session):
    _make_class(session, "CQ.64.CNTT")
    data = CreateStudentRequest(
        user_id="6451071055",
        full_name="Đinh Nhật Huyền Nhân",
        date_of_birth="31/08/2020",
        email="6451071055@st.utc2.edu.vn",
        class_id="CQ.64.CNTT",
    )

    with pytest.raises(DateOfBirthRequiredError):
        create_student(session, data)


def test_create_student_class_not_found_raises(session):
    data = CreateStudentRequest(
        user_id="6451071058",
        full_name="Nguyễn Văn C",
        date_of_birth="31/08/2005",
        email="6451071058@st.utc2.edu.vn",
        class_id="CLASS_NON_EXISTENT",
    )

    with pytest.raises(NotFoundError):
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
    assert temporary_password == "student1"  # SV: mật khẩu tạm = MSSV
    assert temporary_password != "abc12345"

    session.refresh(target)
    assert verify_password(temporary_password, target.hashed_password)
    assert target.must_change_password is True
    assert target.token_version == 1


def test_reset_password_teacher_can_reset_student_in_their_class(session):
    from datetime import date, timedelta

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
        start_date=now_utc(),
        end_date=now_utc() + timedelta(days=30),
        total_number_student=1,
    )
    session.add(course)
    session.commit()
    session.refresh(course)

    enrollment = Enrollment(course_id=course.course_id, student_id=student.user_id)
    session.add(enrollment)
    session.commit()

    _, temporary_password = reset_password(session, teacher, student.user_id)
    assert temporary_password == "student2"

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
    from datetime import date, timedelta

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
        start_date=now_utc(),
        end_date=now_utc() + timedelta(days=30),
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
    """Giáo viên chưa có ngày sinh thì không thể sinh mật khẩu tạm."""
    admin = _make_user(session, "admin6", "admin6@example.com", Role.ADMIN)
    target = _make_user(
        session,
        "teacher_no_dob",
        "teacher_no_dob@example.com",
        Role.TEACHER,
        date_of_birth=None,
    )

    with pytest.raises(DateOfBirthRequiredError):
        reset_password(session, admin, target.user_id)

    session.refresh(target)
    assert target.token_version == 0


def test_reset_password_student_without_date_of_birth_uses_user_id(session):
    """SV import từ file danh sách lớp không có ngày sinh vẫn reset được."""
    admin = _make_user(session, "admin7", "admin7@example.com", Role.ADMIN)
    target = _make_user(
        session,
        "675107A095",
        "675107A095@st.utc2.edu.vn",
        Role.STUDENT,
        date_of_birth=None,
    )

    _, temporary_password = reset_password(session, admin, target.user_id)

    assert temporary_password == "675107A095"
    session.refresh(target)
    assert verify_password("675107A095", target.hashed_password)
    assert target.must_change_password is True
    assert target.token_version == 1


def test_reset_password_teacher_target_uses_date_of_birth(session):
    admin = _make_user(session, "admin8", "admin8@example.com", Role.ADMIN)
    target = _make_user(
        session,
        "teacher8",
        "teacher8@example.com",
        Role.TEACHER,
        date_of_birth=date(1990, 1, 15),
    )

    _, temporary_password = reset_password(session, admin, target.user_id)

    assert temporary_password == "15011990"
    session.refresh(target)
    assert verify_password("15011990", target.hashed_password)


def test_reset_password_rejects_unknown_target_role(session):
    """Role lạ không được rơi vào nhánh nào (whitelist), dữ liệu giữ nguyên."""
    admin = _make_user(session, "admin9", "admin9@example.com", Role.ADMIN)
    target = _make_user(
        session,
        "ghost",
        "ghost@example.com",
        99,
        date_of_birth=date(2000, 1, 1),
        password="keep-me-123",
    )

    with pytest.raises(NotAllowedToResetError):
        reset_password(session, admin, target.user_id)

    session.refresh(target)
    assert verify_password("keep-me-123", target.hashed_password)
    assert target.token_version == 0

# endregion

#region test list_users

# --- validate role_id --------------------------------------------------------
@pytest.mark.parametrize("bad_role", [0, 4, 99])
def test_list_users_invalid_role_id_raises(session, bad_role):
    admin = _make_listed_user(session, "admin1", Role.ADMIN)

    with pytest.raises(InvalidFormatError):
        _call(session, admin, role_id=bad_role)


# --- admin -------------------------------------------------------------------
def test_list_users_admin_without_filter_returns_all_ordered_by_user_id(session):
    admin = _make_listed_user(session, "admin1", Role.ADMIN)
    teacher = _make_listed_user(session, "teacher1", Role.TEACHER)
    student = _make_listed_user(session, "student1", Role.STUDENT)

    result = _call(session, admin)

    assert result.total == 3
    assert _ids(result) == sorted(
        [admin.user_id, teacher.user_id, student.user_id]
    )


def test_list_users_admin_filter_by_role_id(session):
    admin = _make_listed_user(session, "admin1", Role.ADMIN)
    _make_listed_user(session, "teacher1", Role.TEACHER)
    student = _make_listed_user(session, "student1", Role.STUDENT)

    result = _call(session, admin, role_id=Role.STUDENT)

    assert _ids(result) == [student.user_id]
    assert result.total == 1


def test_list_users_admin_filter_by_class_id(session):
    _make_class(session, "CQ.64.CNTT")
    _make_class(session, "CQ.64.KT")
    admin = _make_listed_user(session, "admin1", Role.ADMIN)
    cntt = _make_listed_user(session, "student1", Role.STUDENT, "CQ.64.CNTT")
    _make_listed_user(session, "student2", Role.STUDENT, "CQ.64.KT")

    result = _call(session, admin, class_id="CQ.64.CNTT")

    assert _ids(result) == [cntt.user_id]
    assert result.total == 1


def test_list_users_admin_filter_by_class_id_no_match_returns_empty(session):
    _make_class(session, "CQ.64.CNTT")
    admin = _make_listed_user(session, "admin1", Role.ADMIN)
    _make_listed_user(session, "student1", Role.STUDENT, "CQ.64.CNTT")

    result = _call(session, admin, class_id="CLASS_NON_EXISTENT")

    assert result.items == []
    assert result.total == 0


def test_list_users_admin_combined_role_and_class_filter(session):
    _make_class(session, "CQ.64.CNTT")
    admin = _make_listed_user(session, "admin1", Role.ADMIN)
    student = _make_listed_user(session, "student1", Role.STUDENT, "CQ.64.CNTT")
    # cùng class_id trong DB nhưng khác role -> không được lọt vào kết quả
    _make_listed_user(session, "teacher1", Role.TEACHER, "CQ.64.CNTT")

    result = _call(session, admin, role_id=Role.STUDENT, class_id="CQ.64.CNTT")

    assert _ids(result) == [student.user_id]


# --- teacher -----------------------------------------------------------------


def test_list_users_teacher_sees_only_students_in_own_courses(session):
    teacher = _make_listed_user(session, "teacher1", Role.TEACHER)
    other_teacher = _make_listed_user(session, "teacher2", Role.TEACHER)
    mine = _make_listed_user(session, "student1", Role.STUDENT)
    theirs = _make_listed_user(session, "student2", Role.STUDENT)
    _make_listed_user(session, "student3", Role.STUDENT)  # chưa enroll khoá nào
    _make_listed_user(session, "admin1", Role.ADMIN)

    _enroll(session, _make_course(session, "course1", teacher), mine)
    _enroll(session, _make_course(session, "course2", other_teacher), theirs)

    result = _call(session, teacher)

    assert _ids(result) == [mine.user_id]
    assert result.total == 1


def test_list_users_teacher_without_courses_sees_nothing(session):
    teacher = _make_listed_user(session, "teacher1", Role.TEACHER)
    other_teacher = _make_listed_user(session, "teacher2", Role.TEACHER)
    student = _make_listed_user(session, "student1", Role.STUDENT)
    _enroll(session, _make_course(session, "course1", other_teacher), student)

    result = _call(session, teacher)

    assert result.items == []
    assert result.total == 0


def test_list_users_teacher_student_in_multiple_own_courses_appears_once(session):
    teacher = _make_listed_user(session, "teacher1", Role.TEACHER)
    student = _make_listed_user(session, "student1", Role.STUDENT)
    _enroll(session, _make_course(session, "course1", teacher), student)
    _enroll(session, _make_course(session, "course2", teacher), student)

    result = _call(session, teacher)

    assert _ids(result) == [student.user_id]
    assert result.total == 1


@pytest.mark.parametrize("role_param", [Role.ADMIN, Role.TEACHER])
def test_list_users_teacher_ignores_role_id_param(session, role_param):
    teacher = _make_listed_user(session, "teacher1", Role.TEACHER)
    student = _make_listed_user(session, "student1", Role.STUDENT)
    _make_listed_user(session, "admin1", Role.ADMIN)
    _enroll(session, _make_course(session, "course1", teacher), student)

    result = _call(session, teacher, role_id=role_param)

    assert _ids(result) == [student.user_id]


def test_list_users_teacher_class_id_filter_stays_within_own_scope(session):
    _make_class(session, "CQ.64.CNTT")
    _make_class(session, "CQ.64.KT")
    teacher = _make_listed_user(session, "teacher1", Role.TEACHER)
    in_class = _make_listed_user(session, "student1", Role.STUDENT, "CQ.64.CNTT")
    other_class = _make_listed_user(session, "student2", Role.STUDENT, "CQ.64.KT")
    # cùng lớp với student1 nhưng không học khoá của teacher này
    outsider = _make_listed_user(session, "student3", Role.STUDENT, "CQ.64.CNTT")

    course = _make_course(session, "course1", teacher)
    _enroll(session, course, in_class)
    _enroll(session, course, other_class)

    result = _call(session, teacher, class_id="CQ.64.CNTT")

    assert _ids(result) == [in_class.user_id]
    assert outsider.user_id not in _ids(result)


# --- pagination --------------------------------------------------------------


def test_list_users_pagination_pages_and_total(session):
    admin = _make_listed_user(session, "admin1", Role.ADMIN)
    students = [
        _make_listed_user(session, f"student{i}", Role.STUDENT) for i in range(1, 6)
    ]

    page1 = _call(session, admin, role_id=Role.STUDENT, page=1, page_size=2)
    page2 = _call(session, admin, role_id=Role.STUDENT, page=2, page_size=2)
    page3 = _call(session, admin, role_id=Role.STUDENT, page=3, page_size=2)

    assert _ids(page1) == [s.user_id for s in students[:2]]
    assert _ids(page2) == [s.user_id for s in students[2:4]]
    assert _ids(page3) == [students[4].user_id]  # trang cuối thiếu item
    assert page1.total == page2.total == page3.total == 5
    assert (page1.page, page1.page_size) == (1, 2)


def test_list_users_pagination_page_beyond_range_returns_empty_with_total(session):
    admin = _make_listed_user(session, "admin1", Role.ADMIN)
    for i in range(1, 4):
        _make_listed_user(session, f"student{i}", Role.STUDENT)

    result = _call(session, admin, role_id=Role.STUDENT, page=10, page_size=2)

    assert result.items == []
    assert result.total == 3


def test_list_users_pagination_applies_to_teacher_scope(session):
    teacher = _make_listed_user(session, "teacher1", Role.TEACHER)
    course = _make_course(session, "course1", teacher)
    students = [
        _make_listed_user(session, f"student{i}", Role.STUDENT) for i in range(1, 4)
    ]
    for student in students:
        _enroll(session, course, student)

    page1 = _call(session, teacher, page=1, page_size=2)
    page2 = _call(session, teacher, page=2, page_size=2)

    assert _ids(page1) == [s.user_id for s in students[:2]]
    assert _ids(page2) == [students[2].user_id]
    assert page1.total == page2.total == 3


# --- mapping sang UserResponse ----------------------------------------------


def test_list_users_class_id_only_exposed_for_students(session):
    _make_class(session, "CQ.64.CNTT")
    admin = _make_listed_user(session, "admin1", Role.ADMIN)
    _make_listed_user(session, "student1", Role.STUDENT, "CQ.64.CNTT")
    # class_id có trong DB nhưng response phải ẩn với Teacher
    _make_listed_user(session, "teacher1", Role.TEACHER, "CQ.64.CNTT")

    students = _call(session, admin, role_id=Role.STUDENT).items
    teachers = _call(session, admin, role_id=Role.TEACHER).items

    assert students[0].class_id == "CQ.64.CNTT"
    assert teachers[0].class_id is None

# endregion

