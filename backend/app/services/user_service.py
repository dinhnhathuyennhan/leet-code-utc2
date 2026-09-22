from sqlmodel import Session, select

from app.core.date import age_calculation
from app.core.exceptions import AppError, ConflictError
from app.core.password import hash_password
from app.schemas.user import (
    CreateStudentRequest,
    CreateTeacherRequest,
    UserResponse,
    password_from_date,
)
from models import User


class DateOfBirthRequiredError(AppError):
    status_code = 422
    error_code = "DATE_OF_BIRTH_INVALID"


def create_teacher(session: Session, data: CreateTeacherRequest) -> User:
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise ConflictError("Email đã được đăng ký")

    age = age_calculation(
        data.date_of_birth.day,
        data.date_of_birth.month,
        data.date_of_birth.year,
    )

    if age < 22:
        raise DateOfBirthRequiredError("Người dùng phải đủ 22 tuổi")

    teacher = User(
        user_id=data.user_id,
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(password_from_date(data.date_of_birth)),
        must_change_password=True,
        date_of_birth=data.date_of_birth,
        avt_link=data.avt_link,
        role_id=2,  # 1: admin, 2: teacher, 3: student
    )
    session.add(teacher)
    session.commit()
    session.refresh(teacher)
    return teacher


def create_student(session: Session, data: CreateStudentRequest) -> User:
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise ConflictError("Email đã được đăng ký")

    age = age_calculation(
        data.date_of_birth.day,
        data.date_of_birth.month,
        data.date_of_birth.year,
    )

    if age < 17:
        raise DateOfBirthRequiredError("Người dùng phải đủ 17 tuổi")

    student = User(
        user_id=data.user_id,
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(password_from_date(data.date_of_birth)),
        must_change_password=True,
        date_of_birth=data.date_of_birth,
        avt_link=data.avt_link,
        role_id=3,  # 1: admin, 2: teacher, 3: student
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


def user_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        full_name=user.full_name,
        email=user.email,
        role_id=user.role_id,
        date_of_birth=user.date_of_birth,
    )

