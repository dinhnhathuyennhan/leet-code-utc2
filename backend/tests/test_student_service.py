import pytest

from app.schemas.user import CreateStudentRequest
from app.services.user_service import EmailAlreadyExistsError, create_student


def test_create_student_success(session):
    data = CreateStudentRequest(
        user_id="student-001",
        full_name="Nguyễn Văn A",
        email="a@example.com",
        date_of_birth="01/01/2000",
    )

    student = create_student(session, data)

    assert student.full_name == "Nguyễn Văn A"
    assert student.email == "a@example.com"
    assert student.role_id == 3
    assert student.must_change_password is True


def test_create_student_dupicate_email_raises(session):
    data = CreateStudentRequest(
        user_id="student-001",
        full_name="Nguyễn Văn A",
        email="a@example.com",
        date_of_birth="01/01/2000",
    )
    create_student(session, data)

    with pytest.raises(EmailAlreadyExistsError):
        create_student(session, data)
