from sqlmodel import Session, select

from app.models import Course, Enrollment, User


def enrollments_of(session: Session, course_id: str) -> list[Enrollment]:
    return list(
        session.exec(select(Enrollment).where(Enrollment.course_id == course_id)).all()
    )


def counter_of(session: Session, course: Course) -> int:
    session.refresh(course)
    return course.total_number_student


def enroll_directly(session: Session, course: Course, student: User) -> None:
    """Create enrollment data without calling the service under test."""
    session.add(Enrollment(course_id=course.course_id, student_id=student.user_id))
    course.total_number_student += 1
    session.commit()
