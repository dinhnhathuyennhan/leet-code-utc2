from sqlmodel import Session, select

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.schemas.course import AddStudentToCourseResponse
from models import Course, Enrollment, User


def _get_manageable_course(
    course_id: str, session: Session, current_user: User, forbidden_message: str
) -> Course:
    course = session.get(Course, course_id)
    if not course:
        raise NotFoundError("Không tìm thấy lớp học")
    if current_user.role_id != 1 and course.created_by != current_user.user_id:
        raise ForbiddenError(forbidden_message)
    return course


def _find_enrollment(
        session: Session, course_id: str, student_id: str
) -> Enrollment | None:
    return session.exec(
        select(Enrollment).where(
            Enrollment.course_id == course_id,
            Enrollment.student_id == student_id,
        )
    ).first()


def add_student_to_course(student_id, course_id, session, current_user):
    course = _get_manageable_course(
        course_id, session, current_user,
        "Bạn không có quyền thêm sinh viên vào lớp này",
    )

    student = session.get(User, student_id)
    if not student or student.role_id != 3:
        raise NotFoundError("Không tìm thấy sinh viên")

    if _find_enrollment(session, course_id, student_id):
        raise ConflictError("Sinh viên đã có trong lớp học")

    enrollment = Enrollment(course_id=course_id, student_id=student_id)
    course.total_number_student += 1
    session.add(enrollment)
    session.commit()
    session.refresh(enrollment)

    return AddStudentToCourseResponse(
        student_id=student_id,
        course_id=course_id,
        enrollment_id=enrollment.enrollment_id
    )


def delete_student_from_course(student_id, course_id, session, current_user):
    course = _get_manageable_course(
        course_id, session, current_user,
        "Bạn không có quyền thực hiện hành động này",
    )

    enrollment = _find_enrollment(session, course_id, student_id)
    if not enrollment:
        raise NotFoundError("Sinh viên không thuộc lớp học này")

    session.delete(enrollment)
    course.total_number_student -= 1
    session.commit()
