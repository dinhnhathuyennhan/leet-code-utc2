from sqlmodel import Session, select

from app.schemas.student import StudentCreate
from models import User


class EmailAlreadyExistsError(Exception):
    pass


def create_student(session: Session, data: StudentCreate) -> User:
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise EmailAlreadyExistsError(data.email)

    student = User(
        user_id=data.email,
        full_name=data.full_name,
        email=data.email,
        hashed_password="temp",
        must_change_password=True,
        role_id=3,
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    return student
