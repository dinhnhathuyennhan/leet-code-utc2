from sqlmodel import Session, select

from app.core.date import is_at_least_17
from app.core.password import hash_password
from app.schemas.user import CreateStudentRequest, CreateTeacherRequest
from models import User


class EmailAlreadyExistsError(Exception):
    pass


class DateOfBirthRequiredError(Exception):
    pass


def create_teacher(session: Session, data: CreateTeacherRequest) -> User:
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise EmailAlreadyExistsError(data.email)

    if not is_at_least_17(
        data.date_of_birth.day,
        data.date_of_birth.month,
        data.date_of_birth.year,
    ):
        raise DateOfBirthRequiredError("Users must be at least 17 years old.")

    # Tạo password từ ngày sinh: DDMMYYYY
    # Ví dụ: 11/11/2000 -> "11112000"
    if data.password is None:
        password = (
            f"{data.date_of_birth.day:02d}"
            f"{data.date_of_birth.month:02d}"
            f"{data.date_of_birth.year}"
        )
    else:
        password = data.password

    teacher = User(
        user_id=data.email,
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
        raise EmailAlreadyExistsError(data.email)

    if not is_at_least_17(
        data.date_of_birth.day,
        data.date_of_birth.month,
        data.date_of_birth.year,
    ):
        raise DateOfBirthRequiredError("Users must be at least 17 years old.")

    # Tạo password từ ngày sinh: DDMMYYYY
    # Ví dụ: 11/11/2000 -> "11112000"
    if data.password is None:
        password = (
            f"{data.date_of_birth.day:02d}"
            f"{data.date_of_birth.month:02d}"
            f"{data.date_of_birth.year}"
        )
    else:
        password = data.password

    student = User(
        user_id=data.email,
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

