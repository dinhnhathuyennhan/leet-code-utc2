from sqlmodel import Session, select

from app.core.date import is_at_least_17, is_at_least_22
from app.core.exceptions import AppError
from app.core.password import hash_password
from app.schemas.user import (
    CreateStudentRequest,
    CreateTeacherRequest,
    UserResponse,
    password_from_date,
)
from models import User


class EmailAlreadyExistsError(AppError):
    status_code = 409
    error_code = "EMAIL_ALREADY_EXISTS"


class DateOfBirthRequiredError(AppError):
    status_code = 422
    error_code = "DATE_OF_BIRTH_INVALID"


def create_teacher(session: Session, data: CreateTeacherRequest) -> User:
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise EmailAlreadyExistsError("Email đã được đăng ký")

    if not is_at_least_22(
        data.date_of_birth.day,
        data.date_of_birth.month,
        data.date_of_birth.year,
    ):
        raise DateOfBirthRequiredError("Người dùng phải đủ 22 tuổi")

    if data.password is None:
        password = password_from_date(data.date_of_birth)
    else:
        password = data.password

    teacher = User(
        user_id=data.user_id,
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(password),
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
        raise EmailAlreadyExistsError("Email đã được đăng ký")

    if not is_at_least_17(
        data.date_of_birth.day,
        data.date_of_birth.month,
        data.date_of_birth.year,
    ):
        raise DateOfBirthRequiredError("Người dùng phải đủ 17 tuổi")

    if data.password is None:

        password = password_from_date(data.date_of_birth)
    else:
        password = data.password

    student = User(
        user_id=data.user_id,
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(password),
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

