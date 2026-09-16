import pytest

from app.core.password import verify_password
from app.schemas.student import StudentCreate
from app.services.student_service import EmailAlreadyExistsError, create_student


def test_create_student_success(session):
    data = StudentCreate(full_name="Nguyễn Văn A", email="a@example.com")

    student, temporary_password = create_student(session, data)

    assert student.full_name == "Nguyễn Văn A"
    assert student.email == "a@example.com"
    assert student.user_id == "a@example.com"
    assert student.role_id == 3
    assert student.must_change_password is True
    assert temporary_password
    assert verify_password(temporary_password, student.hashed_password)


def test_create_student_duplicate_email_raises(session):
    data = StudentCreate(full_name="Nguyễn Văn A", email="a@example.com")
    create_student(session, data)

    with pytest.raises(EmailAlreadyExistsError):
        create_student(session, data)
