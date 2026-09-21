from sqlmodel import Session, select

from app.core.exceptions import ForbiddenError, NotFoundError
from app.dependencies import Role
from app.schemas.course import GetStudentListResponse
from models import Course, Enrollment, User


def get_course_enrollments(
    session: Session, course_id: str, current_user: User
) -> list[GetStudentListResponse]:
    course = session.get(Course, course_id)
    if course is None:
        raise NotFoundError("Không tìm thấy lớp học")

    can_view = current_user.role_id == Role.ADMIN or (
        current_user.role_id == Role.TEACHER
        and course.created_by == current_user.user_id
    )
    if current_user.role_id == Role.STUDENT:
        can_view = session.exec(
            select(Enrollment).where(
                Enrollment.course_id == course_id,
                Enrollment.student_id == current_user.user_id,
            )
        ).first() is not None

    if not can_view:
        raise ForbiddenError("Bạn không có quyền xem lớp học này")

    statement = (
        select(Enrollment, User)
        .join(User, Enrollment.student_id == User.user_id)
        .where(Enrollment.course_id == course_id)
    )
    return [
        GetStudentListResponse(
            enrollment_id=enrollment.enrollment_id,
            student_id=student.user_id,
            full_name=student.full_name,
            email=student.email,
        )
        for enrollment, student in session.exec(statement).all()
    ]

