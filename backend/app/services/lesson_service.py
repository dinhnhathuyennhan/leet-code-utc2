from sqlmodel import Session, func, select

from app.core.exceptions import ConflictError, InvalidFormatError
from app.schemas.course import CourseResponse
from app.schemas.lesson import LessonCreateRequest, LessonDetailResponse, LessonUpdateRequest
from app.services import grade_service
from app.services.course_access import get_lesson_in_course, get_manageable_course, get_viewable_course
from app.services.course_view import build_course_response
from app.services.problem_service import copy_problems_to_lesson, refresh_assignment_count
from models import Enrollment, Lesson, Problem, Submission, Testcase, User


def create_lesson(session: Session, course_id: str, data: LessonCreateRequest, current_user: User) -> CourseResponse:
    course = get_manageable_course(course_id, session, current_user, "Bạn không có quyền tạo buổi học")
    last_order = session.exec(
        select(Lesson.lesson_number).where(Lesson.course_id == course_id).order_by(Lesson.lesson_number.desc())
    ).first()
    lesson = Lesson(
        lesson_number=(last_order or 0) + 1, lesson_name=data.lesson_name, course_id=course_id,
        start_date=data.start_date, end_date=data.end_date,
    )
    session.add(lesson)
    session.flush()
    copy_problems_to_lesson(session, data.problem_ids, lesson, current_user)  # kiểm tra quyền nằm trong hàm này; lỗi thì rollback
    refresh_assignment_count(session, lesson)
    session.commit()
    session.refresh(course)
    return build_course_response(course, session)


def update_lesson(session: Session, course_id: str, lesson_id: int, data: LessonUpdateRequest, current_user: User) -> CourseResponse:
    course = get_manageable_course(course_id, session, current_user, "Bạn không có quyền sửa buổi học")
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    updates = data.model_dump(exclude_unset=True)
    for field in ("lesson_name", "start_date", "end_date"):
        if updates.get(field) is not None:
            setattr(lesson, field, updates[field])
    if lesson.start_date > lesson.end_date:
        raise InvalidFormatError("start_date phải trước hoặc bằng end_date")
    if data.problem_ids is not None:       # chỉ THÊM bài; muốn gỡ bài dùng DELETE problem
        copy_problems_to_lesson(session, data.problem_ids, lesson, current_user)
        refresh_assignment_count(session, lesson)
    session.add(lesson)
    session.commit()
    session.refresh(course)
    return build_course_response(course, session)


def delete_lesson(session: Session, course_id: str, lesson_id: int, current_user: User) -> None:
    get_manageable_course(course_id, session, current_user, "Bạn không có quyền xoá buổi học")
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    if session.exec(select(Problem.problem_id).where(Problem.lesson_id == lesson_id)).first():
        raise ConflictError("Không thể xoá buổi học đã có bài tập")
    session.delete(lesson)
    session.commit()


def get_lesson_detail(session: Session, course_id: str, lesson_id: int, current_user: User) -> LessonDetailResponse:
    course = get_viewable_course(session, course_id, current_user)
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    problems = session.exec(
        select(Problem).where(Problem.lesson_id == lesson_id).order_by(Problem.problem_id)
    ).all()
    problem_ids = [p.problem_id for p in problems]
    problem_by_id = {p.problem_id: p for p in problems}

    total_students = session.exec(
        select(func.count()).select_from(Enrollment).where(Enrollment.course_id == course_id)
    ).one()

    testcases_by_problem: dict[int, list[Testcase]] = {pid: [] for pid in problem_ids}
    submitted_by_problem: dict[int, int] = {}
    submitted_students = 0
    if problem_ids:
        for tc in session.exec(
            select(Testcase).where(Testcase.problem_id.in_(problem_ids)).order_by(Testcase.testcase_id)
        ).all():
            testcases_by_problem[tc.problem_id].append(tc)
        submitted_by_problem = dict(
            session.exec(
                select(Submission.problem_id, func.count())
                .where(Submission.problem_id.in_(problem_ids))
                .group_by(Submission.problem_id)
            ).all()
        )
        submitted_students = session.exec(
            select(func.count(func.distinct(Submission.student_id)))
            .where(Submission.problem_id.in_(problem_ids))
        ).one()

    best = grade_service.best_passed_counts(session, problem_ids)
    scores = [s for (_sid, pid), cnt in best.items()
              if (s := grade_service.problem_score(problem_by_id[pid], cnt)) is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    first = problems[0] if problems else None

    return LessonDetailResponse(
        id=lesson.lesson_id, order=lesson.lesson_number, title=lesson.lesson_name,
        course_code=course.course_id, course_name=course.course_name,
        start_date=lesson.start_date, end_date=lesson.end_date,
        deadline_notice=f"Hạn nộp: {lesson.end_date.strftime('%d/%m/%Y')} - 23:59",
        submitted_students=submitted_students, total_students=total_students,
        stats={
            "submission_rate": round(submitted_students / total_students * 100, 1) if total_students else 0,
            "completed_students": submitted_students, "avg_score": avg_score,
            "score_diff": "Chưa có dữ liệu đối chiếu", "ast_cases": 0, "ast_similarity": "Chưa chạy phân tích",
        },
        alert={
            "problem_code": first.report if first and first.report else "—",
            "missing_students": max(total_students - submitted_students, 0),
            "problem_name": first.title if first else "chưa có bài tập",
            "deadline_text": lesson.end_date.strftime("%d/%m/%Y 23:59"),
        },
        exercises=[
            {
                "id": p.problem_id, "order": index + 1, "title": p.title, "report": p.report,
                "level": p.level, "description": p.description, "constraints": p.constraints,
                "hint": p.hint, "complexity": p.complexity, "time_limit_seconds": p.time_limit_seconds,
                "total_number_testcase": p.total_number_testcase, "starter_code": p.start_format_code,
                "testcases": [
                    {"id": t.testcase_id, "input": t.input,
                     "expected_output": t.expected_output, "is_sample": t.is_sample}
                    for t in testcases_by_problem[p.problem_id]
                ],
                "submitted_count": submitted_by_problem.get(p.problem_id, 0),
            }
            for index, p in enumerate(problems)
        ],
    )
