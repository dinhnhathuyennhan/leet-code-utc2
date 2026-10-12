from sqlmodel import Session, select

from app.core.exceptions import NotFoundError
from app.dependencies import Role
from app.schemas.class_ import ClassResponse, ClassStudentResponse
from models import Class, User


def get_classes(session: Session) -> list[ClassResponse]:
    return [
        ClassResponse(
            class_id=item.class_id, type=item.type,
            course_number=item.course_number, department=item.department,
        )
        for item in session.exec(select(Class).order_by(Class.class_id)).all()
    ]


def get_class_students(session: Session, class_id: str) -> list[ClassStudentResponse]:
    if session.get(Class, class_id) is None:
        raise NotFoundError("Không tìm thấy lớp hành chính")
    students = session.exec(
        select(User).where(User.class_id == class_id, User.role_id == Role.STUDENT).order_by(User.user_id)
    ).all()
    return [
        ClassStudentResponse(
            user_id=s.user_id, full_name=s.full_name, email=s.email, class_id=s.class_id
        )
        for s in students
    ]
