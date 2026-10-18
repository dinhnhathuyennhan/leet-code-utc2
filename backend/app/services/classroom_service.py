"""Service quản lý lớp hành chính (Class).

Lớp hành chính còn được tự tạo khi import sinh viên
(``student_service._create_missing_classes``). Các hàm ở đây phục vụ
tạo/xem/xoá lớp bằng tay qua ``/classes``.
"""

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, delete, func, select

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.classroom import ClassResponse, CreateClassRequest
from models import Class, User


def create_class(session: Session, data: CreateClassRequest) -> ClassResponse:
    class_id = data.class_id
    if session.get(Class, class_id) is not None:
        raise ConflictError(f"Lớp {class_id} đã tồn tại")

    db_class = Class(
        class_id=class_id,
        type=data.type,
        course_number=data.course_number,
        department=data.department,
    )
    session.add(db_class)
    try:
        session.commit()
    except IntegrityError as err:
        # 2 request tạo cùng một lớp cùng lúc: request đến sau vấp khoá chính
        session.rollback()
        raise ConflictError(f"Lớp {class_id} đã tồn tại") from err
    session.refresh(db_class)
    return _class_response(db_class, student_count=0)


def list_classes(session: Session) -> list[ClassResponse]:
    rows = session.exec(_class_with_student_count().order_by(Class.class_id)).all()
    return [_class_response(db_class, student_count) for db_class, student_count in rows]


def get_class(session: Session, class_id: str) -> ClassResponse:
    row = session.exec(
        _class_with_student_count().where(Class.class_id == class_id)
    ).first()
    if row is None:
        raise NotFoundError(f"Không tìm thấy lớp {class_id}")
    db_class, student_count = row
    return _class_response(db_class, student_count)


def delete_class(session: Session, class_id: str) -> None:
    if session.get(Class, class_id) is None:
        raise NotFoundError(f"Không tìm thấy lớp {class_id}")

    student_count = session.exec(
        select(func.count()).select_from(User).where(User.class_id == class_id)
    ).one()
    if student_count > 0:
        raise ConflictError(
            f"Lớp {class_id} đang có {student_count} sinh viên, không thể xóa"
        )
    # Không dùng session.delete(): ORM sẽ tự gán class_id = NULL cho sinh viên
    # của lớp rồi xoá lớp. Câu DELETE trực tiếp để khoá ngoại của DB chặn lại.
    try:
        session.exec(delete(Class).where(Class.class_id == class_id))
        session.commit()
    except IntegrityError as err:
        session.rollback()
        raise ConflictError(
            f"Lớp {class_id} đang có sinh viên, không thể xóa"
        ) from err


def _class_with_student_count():
    """Lớp kèm số sinh viên; LEFT JOIN nên lớp chưa có sinh viên vẫn có, đếm = 0."""
    return (
        select(Class, func.count(User.user_id))
        .outerjoin(User, User.class_id == Class.class_id)
        .group_by(Class.class_id)
    )

def _class_response(db_class: Class, student_count: int) -> ClassResponse:
    return ClassResponse(
        class_id=db_class.class_id,
        type=db_class.type,
        course_number=db_class.course_number,
        department=db_class.department,
        student_count=student_count,
    )
