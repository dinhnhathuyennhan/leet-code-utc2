import pytest
from app.schemas.user import CreateStudentRequest, CreateTeacherRequest
from app.services.user_service import create_student, EmailAlreadyExistsError, DateOfBirthRequiredError, create_teacher

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

def test_create_student_duplicate_email_raises(session):
    data = CreateStudentRequest(
            user_id="6451071055",
            full_name="Đinh Nhật Huyền Nhân",
            date_of_birth="31/08/2005",
            email="6451071055@st.utc2.edu.vn",
        )
    
    student = create_student(session, data)

    with pytest.raises(EmailAlreadyExistsError):
        create_student(session, data)

def test_create_student_invalid_date_of_birth_raises(session):
    data = CreateStudentRequest(
            user_id="6451071055",
            full_name="Đinh Nhật Huyền Nhân",
            date_of_birth="31/08/2020",  # Invalid date of birth (too young)
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
        email="huyennhan@st.utc2.edu.vn"
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
            email="huyennhan@st.utc2.edu.vn"
        )
    
    teacher = create_teacher(session, data)

    with pytest.raises(EmailAlreadyExistsError):
        create_teacher(session, data)

def test_create_teacher_invalid_date_of_birth_raises(session):
    data = CreateTeacherRequest(
            user_id="teacher_IT_001",
            full_name="Đinh Nhật Huyền Nhân",
            date_of_birth="15/05/2020",  # Invalid date of birth (too young)
            email="huyennhan@st.utc2.edu.vn"
        )
    
    with pytest.raises(DateOfBirthRequiredError):
        create_teacher(session, data)

# endregion
