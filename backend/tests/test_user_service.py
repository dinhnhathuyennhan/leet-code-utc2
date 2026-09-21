from datetime import date

import pytest

from app.core.exceptions import ConflictError, InvalidFormatError
from app.schemas.user import CreateStudentRequest, CreateTeacherRequest
from app.services.user_service import (
    DateOfBirthRequiredError,
    create_student,
    create_teacher,
)

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


def test_create_student_rejects_iso_date_format(session):
    with pytest.raises(InvalidFormatError):
        CreateStudentRequest(
            user_id="6451071057",
            full_name="Nguyễn Văn B",
            date_of_birth="2000-06-05",
            email="6451071057@st.utc2.edu.vn",
        )


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
