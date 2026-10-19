from sqlmodel import Session, select

from app.core.utils.datetime_utils import now_utc, vn_day_end, vn_day_start, as_utc
from app.modules.courses.schemas import CourseResponse, CourseLessonResponse, CourseGradeRowResponse
from app.modules.courses import grade_service
from app.models import Course, Enrollment, Lesson, Problem, User


def lesson_status(lesson: Lesson) -> str:
    now = now_utc()
    start = as_utc(vn_day_start(lesson.start_date))
    end = as_utc(vn_day_end(lesson.end_date))
    if now < start:
        return "upcoming"
    if now > end:
        return "closed"
    return "open"


def build_course_response(
    course: Course,
    session: Session | None = None,
    only_student_id: str | None = None,   # truyền user_id khi người xem là sinh viên
) -> CourseResponse:
    response = CourseResponse(
        course_id=course.course_id, course_name=course.course_name, term=course.term,
        start_date=course.start_date, end_date=course.end_date, avt_link=course.avt_link,
        created_by=course.created_by, total_number_student=course.total_number_student,
    )
    if session is None:
        return response

    is_student_view = only_student_id is not None

    lessons = session.exec(
        select(Lesson).where(Lesson.course_id == course.course_id).order_by(Lesson.lesson_number)
    ).all()
    lesson_ids = [lesson.lesson_id for lesson in lessons]
    problems = session.exec(
        select(Problem).where(Problem.lesson_id.in_(lesson_ids)).order_by(Problem.problem_id)
    ).all() if lesson_ids else []
    problems_by_lesson: dict[int, list[Problem]] = {lid: [] for lid in lesson_ids}
    for problem in problems:
        problems_by_lesson[problem.lesson_id].append(problem)

    if is_student_view:
        now = now_utc()
        problems_by_lesson = {
            lesson_id: [problem for problem in lesson_problems if as_utc(problem.start_datetime) <= now]
            for lesson_id, lesson_problems in problems_by_lesson.items()
        }

    participants = grade_service.participants_by_lesson(session, lesson_ids)

    lesson_responses = []
    for lesson in lessons:
        status = lesson_status(lesson)
        visible_problems = problems_by_lesson[lesson.lesson_id]
        lesson_responses.append({
            "id": lesson.lesson_id,
            "order": lesson.lesson_number,
            "title": lesson.lesson_name,
            "status": status,
            "opens_at": vn_day_start(lesson.start_date),
            "deadline": vn_day_end(lesson.end_date),
            "problems": [
                {"id": p.problem_id, "title": p.title, "report": p.report, "level": p.level,
                 "start_datetime": p.start_datetime, "end_datetime": p.end_datetime,
                 "total_number_testcase": p.total_number_testcase}
                for p in visible_problems
            ],
            "participant_count": None if is_student_view else participants.get(lesson.lesson_id, 0),
        })

    enrollment_stmt = (
        select(Enrollment, User).join(User, Enrollment.student_id == User.user_id)
        .where(Enrollment.course_id == course.course_id)
    )
    if only_student_id is not None:
        enrollment_stmt = enrollment_stmt.where(Enrollment.student_id == only_student_id)
    enrollments = session.exec(enrollment_stmt).all()

    grade_problem_ids = [
        problem.problem_id
        for lesson_problems in problems_by_lesson.values()
        for problem in lesson_problems
    ]
    best = grade_service.best_passed_counts(
        session, grade_problem_ids, [student.user_id for _, student in enrollments]
    )
    response.sessions = [CourseLessonResponse.model_validate(item) for item in lesson_responses]
    response.grades = [
        CourseGradeRowResponse.model_validate(item)
        for item in grade_service.build_grade_rows(lessons, problems_by_lesson, enrollments, best)
    ]
    return response
