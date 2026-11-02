from uuid import UUID
from sqlmodel import Session, select

from app.core.dependencies import Role
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Class, Enrollment, User
from app.modules.courses.access import (
    find_enrollment,
    get_manageable_course,
    get_viewable_course,
)
from app.modules.enrollments.schemas import (
    AddClassToCourseResponse,
    AddStudentToCourseResponse,
    GetStudentListResponse,
)


def get_course_enrollments(
    session: Session, course_id: str, current_user: User
) -> list[GetStudentListResponse]:
    get_viewable_course(session, course_id, current_user)

    statement = (
        select(Enrollment, User)
        .join(User, Enrollment.student_id == User.user_id)
        .where(Enrollment.course_id == course_id)
    )
    enrollments = session.exec(statement).all()
    return [
        GetStudentListResponse(
            enrollment_id=enrollment.enrollment_id,
            student_id=str(student.user_id),
            full_name=student.full_name,
            email=student.email,
        )
        for enrollment, student in enrollments
    ]


def add_student_to_course(
    student_id: str,
    course_id: str,
    session: Session,
    current_user: User,
) -> AddStudentToCourseResponse:
    course = get_manageable_course(
        course_id,
        session,
        current_user,
        "Bạn không có quyền thêm sinh viên vào lớp này",
    )

    try:
        student_uuid = UUID(str(student_id))
    except (TypeError, ValueError, AttributeError):
        raise NotFoundError("Không tìm thấy sinh viên") from None
    student = session.get(User, student_uuid)
    if not student or student.role_id != Role.STUDENT:
        raise NotFoundError("Không tìm thấy sinh viên")

    if find_enrollment(session, course_id, student_uuid):
        raise ConflictError("Sinh viên đã có trong lớp học")

    enrollment = Enrollment(course_id=course_id, student_id=student_uuid)
    course.total_number_student += 1
    session.add(enrollment)
    session.commit()
    session.refresh(enrollment)

    return AddStudentToCourseResponse(
        student_id=str(student_uuid),
        course_id=course_id,
        enrollment_id=enrollment.enrollment_id,
    )


def delete_student_from_course(
    student_id: str,
    course_id: str,
    session: Session,
    current_user: User,
) -> None:
    course = get_manageable_course(
        course_id,
        session,
        current_user,
        "Bạn không có quyền thực hiện hành động này",
    )

    try:
        student_uuid = UUID(str(student_id))
    except (TypeError, ValueError, AttributeError):
        raise NotFoundError("Sinh viên không thuộc lớp học này") from None
    enrollment = find_enrollment(session, course_id, student_uuid)
    if not enrollment:
        raise NotFoundError("Sinh viên không thuộc lớp học này")

    session.delete(enrollment)
    course.total_number_student -= 1
    session.commit()


def add_class_to_course(
    session: Session,
    course_id: str,
    class_id: str,
    current_user: User,
) -> AddClassToCourseResponse:
    course = get_manageable_course(
        course_id,
        session,
        current_user,
        "Bạn không có quyền thêm sinh viên vào lớp này",
    )
    if session.get(Class, class_id) is None:
        raise NotFoundError("Không tìm thấy lớp hành chính")
    students = session.exec(
        select(User).where(User.class_id == class_id, User.role_id == Role.STUDENT)
    ).all()
    student_ids = [student.user_id for student in students]
    existing_ids = set()
    if student_ids:
        existing_ids = set(
            session.exec(
                select(Enrollment.student_id).where(
                    Enrollment.course_id == course_id,
                    Enrollment.student_id.in_(student_ids),
                )
            ).all()
        )
    new_ids = [student_id for student_id in student_ids if student_id not in existing_ids]
    session.add_all(
        [Enrollment(course_id=course_id, student_id=student_id) for student_id in new_ids]
    )
    course.total_number_student += len(new_ids)
    session.add(course)
    session.commit()
    return AddClassToCourseResponse(
        course_id=course_id,
        class_id=class_id,
        added_count=len(new_ids),
        skipped_count=len(existing_ids),
        added_student_ids=[str(student_id) for student_id in new_ids],
    )
