from sqlmodel import Session, select

from app.core.exceptions import ConflictError, NotFoundError
from app.dependencies import Role
from app.schemas.enrollment import (
    AddClassToCourseResponse,
    AddStudentToCourseResponse,
    GetStudentListResponse,
)
from app.services.course_access import find_enrollment, get_manageable_course, get_viewable_course
from models import Class, Enrollment, Lesson, Problem, Submission, User

def get_course_enrollments(
    session: Session, course_id: str, current_user: User
) -> list[GetStudentListResponse]:
    course = get_viewable_course(session, course_id, current_user)

    statement = (
        select(Enrollment, User)
        .join(User, Enrollment.student_id == User.user_id)
        .where(Enrollment.course_id == course_id)
    )
    # SỬA: Trả thêm class_id để bảng sinh viên/bảng điểm hiển thị đúng lớp hành chính.
    enrollments = session.exec(statement).all()
    student_ids = [student.user_id for _, student in enrollments]
    lessons = session.exec(select(Lesson).where(Lesson.course_id == course.course_id)).all()
    problems = session.exec(
        select(Problem).where(Problem.lesson_id.in_([lesson.lesson_id for lesson in lessons]))
    ).all() if lessons else []
    problem_ids = [problem.problem_id for problem in problems]

    # SỬA: Tính AC theo từng problem bằng một lần đọc Submission, thay vì để frontend
    # khởi tạo toàn bộ tiến độ bằng 0 hoặc gọi lặp từng sinh viên/bài tập.
    submissions = session.exec(
        select(Submission).where(
            Submission.student_id.in_(student_ids),
            Submission.problem_id.in_(problem_ids),
        )
    ).all() if student_ids and problem_ids else []
    accepted_pairs = {
        (submission.student_id, submission.problem_id)
        for submission in submissions
        if submission.status.lower() == "accepted"
    }
    total_problems = len(problem_ids)
    results = []
    for enrollment, student in enrollments:
        accepted = sum((student.user_id, pid) in accepted_pairs for pid in problem_ids)
        results.append(GetStudentListResponse(
            enrollment_id=enrollment.enrollment_id, student_id=student.user_id,
            full_name=student.full_name, email=student.email, class_id=student.class_id,
            submitted_lessons=accepted, total_lessons=total_problems,
            progress_percent=round(accepted / total_problems * 100, 1) if total_problems else 0,
        ))
    return results

def add_student_to_course(student_id, course_id, session, current_user):
    course = get_manageable_course(
        course_id,
        session,
        current_user,
        "Bạn không có quyền thêm sinh viên vào lớp này",
    )

    student = session.get(User, student_id)
    if not student or student.role_id != Role.STUDENT:
        raise NotFoundError("Không tìm thấy sinh viên")

    if find_enrollment(session, course_id, student_id):
        raise ConflictError("Sinh viên đã có trong lớp học")

    enrollment = Enrollment(course_id=course_id, student_id=student_id)
    course.total_number_student += 1
    session.add(enrollment)
    session.commit()
    session.refresh(enrollment)

    return AddStudentToCourseResponse(
        student_id=student_id,
        course_id=course_id,
        enrollment_id=enrollment.enrollment_id,
    )

def delete_student_from_course(student_id, course_id, session, current_user):
    course = get_manageable_course(
        course_id,
        session,
        current_user,
        "Bạn không có quyền thực hiện hành động này",
    )

    enrollment = find_enrollment(session, course_id, student_id)
    if not enrollment:
        raise NotFoundError("Sinh viên không thuộc lớp học này")

    session.delete(enrollment)
    course.total_number_student -= 1
    session.commit()

def add_class_to_course(session: Session, course_id: str, class_id: str, current_user: User) -> AddClassToCourseResponse:
    course = get_manageable_course(course_id, session, current_user, "Bạn không có quyền thêm sinh viên vào lớp này")
    if session.get(Class, class_id) is None:
        raise NotFoundError("Không tìm thấy lớp hành chính")
    students = session.exec(select(User).where(User.class_id == class_id, User.role_id == Role.STUDENT)).all()
    student_ids = [student.user_id for student in students]
    existing_ids = set()
    if student_ids:
        existing_ids = set(session.exec(select(Enrollment.student_id).where(Enrollment.course_id == course_id, Enrollment.student_id.in_(student_ids))).all())
    new_ids = [student_id for student_id in student_ids if student_id not in existing_ids]
    session.add_all([Enrollment(course_id=course_id, student_id=student_id) for student_id in new_ids])
    course.total_number_student += len(new_ids)
    session.add(course)
    session.commit()
    return AddClassToCourseResponse(course_id=course_id, class_id=class_id, added_count=len(new_ids), skipped_count=len(existing_ids), added_student_ids=new_ids)
