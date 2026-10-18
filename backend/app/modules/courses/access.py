from sqlmodel import Session, select

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.dependencies import Role
from app.models import Course, Enrollment, Lesson, Problem, User


def find_enrollment(session: Session, course_id: str, student_id: str) -> Enrollment | None:
    return session.exec(
        select(Enrollment).where(
            Enrollment.course_id == course_id, Enrollment.student_id == student_id
        )
    ).first()


def get_viewable_course(session: Session, course_id: str, current_user: User) -> Course:
    course = session.get(Course, course_id)
    if course is None:
        raise NotFoundError("Không tìm thấy lớp học")
    if current_user.role_id == Role.ADMIN:
        can_view = True
    elif current_user.role_id == Role.TEACHER:
        can_view = course.created_by == current_user.user_id
    elif current_user.role_id == Role.STUDENT:
        can_view = find_enrollment(session, course_id, current_user.user_id) is not None
    else:
        can_view = False
    if not can_view:
        raise ForbiddenError("Bạn không có quyền xem lớp học này")
    return course


def get_manageable_course(
    course_id: str, session: Session, current_user: User, forbidden_message: str
) -> Course:
    course = session.get(Course, course_id)
    if not course:
        raise NotFoundError("Không tìm thấy lớp học")
    if current_user.role_id != Role.ADMIN and course.created_by != current_user.user_id:
        raise ForbiddenError(forbidden_message)
    return course


def get_lesson_in_course(session: Session, course_id: str, lesson_id: int) -> Lesson:
    lesson = session.get(Lesson, lesson_id)
    if lesson is None or lesson.course_id != course_id:
        raise NotFoundError("Không tìm thấy buổi học")
    return lesson


def get_problem_in_lesson(session: Session, lesson: Lesson, problem_id: int) -> Problem:
    problem = session.get(Problem, problem_id)
    if problem is None or problem.lesson_id != lesson.lesson_id:
        raise NotFoundError("Không tìm thấy bài tập trong buổi học")
    return problem
