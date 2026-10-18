from sqlmodel import Session, func, select

from app.core.dependencies import Role
from app.core.exceptions import ConflictError, InvalidFormatError, NotFoundError, ForbiddenError
from app.core.utils.datetime_utils import as_utc
from app.modules.courses.schemas import CourseResponse
from app.modules.lessons.schemas import LessonCreateRequest, LessonDetailResponse, LessonUpdateRequest, \
    LessonDuplicateRequest, LessonReorderRequest
from app.modules.courses import grade_service
from app.modules.courses.access import get_lesson_in_course, get_manageable_course, get_viewable_course
from app.modules.courses.view import build_course_response
from app.modules.problems.service import copy_problems_to_lesson, refresh_assignment_count
from app.models import Enrollment, Lesson, Problem, Submission, Testcase, User, Course


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


def add_problems_to_lesson(
    session: Session,
    course_id: str,
    lesson_id: int,
    problem_ids: list[int],
    current_user: User,
) -> CourseResponse:
    course = get_manageable_course(
        course_id, session, current_user, "Bạn không có quyền sửa buổi học"
    )
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    copy_problems_to_lesson(session, problem_ids, lesson, current_user)
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


def reorder_lessons(
    session: Session,
    course_id: str,
    data: LessonReorderRequest,
    current_user: User,
) -> CourseResponse:
    course = get_manageable_course(
        course_id, session, current_user, "Bạn không có quyền thực hiện hành động này"
    )
    lessons = session.exec(
        select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.lesson_number)
    ).all()
    current_ids = {lesson.lesson_id for lesson in lessons}
    if len(data.order) != len(set(data.order)) or set(data.order) != current_ids:
        raise InvalidFormatError("Danh sách buổi học không hợp lệ")

    lessons_by_id = {lesson.lesson_id: lesson for lesson in lessons}
    for position, lesson_id in enumerate(data.order, start=1):
        lessons_by_id[lesson_id].lesson_number = position
        session.add(lessons_by_id[lesson_id])
    session.commit()
    session.refresh(course)
    return build_course_response(course, session)


def duplicate_lesson(
    session: Session,
    course_id: str,
    lesson_id: int,
    data: LessonDuplicateRequest,
    current_user: User,
) -> CourseResponse:
    get_viewable_course(session, course_id, current_user)
    source = get_lesson_in_course(session, course_id, lesson_id)
    target_course_id = data.target_course_id or course_id
    target_course = session.get(Course, target_course_id)
    if target_course is None:
        raise NotFoundError("Không tìm thấy lớp học đích")
    if current_user.role_id != Role.ADMIN and target_course.created_by != current_user.user_id:
        raise ForbiddenError("Bạn không có quyền tạo buổi học trong lớp đích")
    last_order = session.exec(
        select(Lesson.lesson_number)
        .where(Lesson.course_id == target_course_id)
        .order_by(Lesson.lesson_number.desc())
    ).first()
    duplicate = Lesson(
        lesson_number=(last_order or 0) + 1,
        lesson_name=source.lesson_name,
        course_id=target_course_id,
        start_date=data.new_start_date,
        end_date=data.new_end_date,
    )
    session.add(duplicate)
    session.flush()

    problem_ids = session.exec(
        select(Problem.problem_id)
        .where(Problem.lesson_id == source.lesson_id)
        .order_by(Problem.problem_id)
    ).all()
    copy_problems_to_lesson(session, problem_ids, duplicate, current_user)
    refresh_assignment_count(session, duplicate)
    session.commit()
    session.refresh(target_course)
    return build_course_response(target_course, session)


def get_lesson_detail(session: Session, course_id: str, lesson_id: int, current_user: User) -> LessonDetailResponse:
    course = get_viewable_course(session, course_id, current_user)
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    all_problems = session.exec(
        select(Problem).where(Problem.lesson_id == lesson_id).order_by(Problem.problem_id)
    ).all()
    is_student = current_user.role_id == Role.STUDENT
    problems = [
        problem for problem in all_problems
        if not is_student or as_utc(problem.start_datetime) <= now_utc()
    ]
    problem_ids = [p.problem_id for p in problems]
    problem_by_id = {p.problem_id: p for p in problems}

    total_students = submitted_students = 0
    enrolled_student_ids: list[str] = []
    if not is_student:
        enrolled_student_ids = session.exec(
            select(Enrollment.student_id).where(Enrollment.course_id == course_id)
        ).all()
        total_students = len(enrolled_student_ids)

    testcases_by_problem: dict[int, list[Testcase]] = {pid: [] for pid in problem_ids}
    submitted_by_problem: dict[int, int] = {}
    if problem_ids:
        testcase_query = select(Testcase).where(Testcase.problem_id.in_(problem_ids))
        if is_student:
            testcase_query = testcase_query.where(Testcase.is_sample.is_(True))
        for tc in session.exec(
            testcase_query.order_by(Testcase.testcase_id)
        ).all():
            testcases_by_problem[tc.problem_id].append(tc)
        if not is_student and enrolled_student_ids:
            submitted_by_problem = dict(
                session.exec(
                    select(Submission.problem_id, func.count())
                    .where(
                        Submission.problem_id.in_(problem_ids),
                        Submission.student_id.in_(enrolled_student_ids),
                    )
                    .group_by(Submission.problem_id)
                ).all()
            )
            submitted_students = session.exec(
                select(func.count(func.distinct(Submission.student_id)))
                .where(
                    Submission.problem_id.in_(problem_ids),
                    Submission.student_id.in_(enrolled_student_ids),
                )
            ).one()

    best = (
        grade_service.best_passed_counts(session, problem_ids, enrolled_student_ids)
        if not is_student
        else {}
    )
    scores = [s for (_sid, pid), cnt in best.items()
              if (s := grade_service.problem_score(problem_by_id[pid], cnt)) is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    first = problems[0] if problems else None

    return LessonDetailResponse(
        id=lesson.lesson_id, order=lesson.lesson_number, title=lesson.lesson_name,
        course_code=course.course_id, course_name=course.course_name,
        start_date=lesson.start_date, end_date=lesson.end_date,
        deadline_notice=f"Hạn nộp: {lesson.end_date.strftime('%d/%m/%Y')} - 23:59",
        submitted_students=None if is_student else submitted_students,
        total_students=None if is_student else total_students,
        stats=None if is_student else {
            "submission_rate": round(submitted_students / total_students * 100, 1) if total_students else 0,
            "completed_students": submitted_students, "avg_score": avg_score,
            "score_diff": "Chưa có dữ liệu đối chiếu", "ast_cases": 0, "ast_similarity": "Chưa chạy phân tích",
        },
        alert=None if is_student else {
            "problem_code": first.report if first and first.report else "—",
            "missing_students": max(total_students - submitted_students, 0),
            "problem_name": first.title if first else "chưa có bài tập",
            "deadline_text": lesson.end_date.strftime("%d/%m/%Y 23:59"),
        },
        exercises=[
            {
                "id": p.problem_id, "order": index + 1, "title": p.title, "report": p.report,
                "function_name": p.function_name,
                "level": p.level, "description": p.description, "constraints": p.constraints,
                "hint": p.hint, "complexity": p.complexity, "time_limit_seconds": p.time_limit_seconds,
                "total_number_testcase": p.total_number_testcase,
                "starter_code": p.starter_codes.get("python") or p.start_format_code,
                "starter_codes": p.starter_codes or {"python": p.start_format_code},
                "testcases": [
                    {"id": t.testcase_id, **testcase_to_api_values(t), "is_sample": t.is_sample}
                    for t in testcases_by_problem[p.problem_id]
                    if not is_student or t.is_sample
                ],
                "submitted_count": None if is_student else submitted_by_problem.get(p.problem_id, 0),
            }
            for index, p in enumerate(problems)
        ],
    )
