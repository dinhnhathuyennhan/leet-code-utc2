from sqlmodel import Session, func, select

from app.core.utils.datetime_utils import as_utc, now_utc, vn_day_end, vn_day_start
from app.core.exceptions import ConflictError, ForbiddenError, InvalidFormatError, NotFoundError
from app.core.dependencies import Role
from app.modules.problems.schemas import ProblemDetailResponse, ProblemUpdateRequest
from app.modules.courses.access import (
    get_lesson_in_course, get_manageable_course, get_problem_in_lesson, get_viewable_course,
)
from app.models import Course, Lesson, Problem, Submission, Testcase, User


def assert_can_copy_problems(
    session: Session, problem_ids: list[int], current_user: User, target_lesson_id: int | None = None
) -> None:
    """Admin: mọi bài. Giáo viên: bài ở buổi đích, hoặc bài thuộc lớp do chính mình tạo.
    (Sau này có kho UTC2: cho phép thêm course_id == "BANK-UTC2" ở đây.)"""
    if not problem_ids or current_user.role_id == Role.ADMIN:
        return
    rows = session.exec(
        select(Problem.problem_id, Problem.lesson_id, Course.created_by)
        .select_from(Problem)
        .join(Lesson, Lesson.lesson_id == Problem.lesson_id)
        .join(Course, Course.course_id == Lesson.course_id)
        .where(Problem.problem_id.in_(problem_ids))
    ).all()
    if {row[0] for row in rows} != set(problem_ids):
        raise NotFoundError("Một hoặc nhiều bài tập không tồn tại")
    for _pid, source_lesson_id, owner_id in rows:
        if source_lesson_id != target_lesson_id and owner_id != current_user.user_id:
            raise ForbiddenError("Bạn không có quyền sao chép bài tập này")


def refresh_assignment_count(session: Session, lesson: Lesson) -> None:
    session.flush()
    lesson.total_number_assignment = session.exec(
        select(func.count()).select_from(Problem).where(Problem.lesson_id == lesson.lesson_id)
    ).one()
    session.add(lesson)


def copy_problems_to_lesson(
    session: Session, problem_ids: list[int], lesson: Lesson, current_user: User
) -> list[Problem]:
    """Gắn bài vào buổi: bài đã ở buổi này giữ nguyên, bài ở buổi khác được SAO CHÉP
    (problem_id mới, Submission cũ không đi theo). Giữ nguyên mã bài `report`."""
    problem_ids = list(dict.fromkeys(problem_ids))   # bỏ id trùng, giữ thứ tự
    if not problem_ids:
        return []
    assert_can_copy_problems(session, problem_ids, current_user, lesson.lesson_id)

    sources = {p.problem_id: p for p in session.exec(
        select(Problem).where(Problem.problem_id.in_(problem_ids))).all()}
    testcases_by_source: dict[int, list[Testcase]] = {pid: [] for pid in problem_ids}
    for tc in session.exec(select(Testcase).where(Testcase.problem_id.in_(problem_ids))).all():
        testcases_by_source[tc.problem_id].append(tc)

    start_dt = vn_day_start(lesson.start_date)
    end_dt = vn_day_end(lesson.end_date)
    result: list[Problem] = []
    for pid in problem_ids:
        src = sources[pid]
        if src.lesson_id == lesson.lesson_id:
            result.append(src)
            continue
        clone = Problem(
            lesson_id=lesson.lesson_id, title=src.title, description=src.description,
            time_limit_seconds=src.time_limit_seconds, start_format_code=src.start_format_code,
            constraints=src.constraints, level=src.level, hint=src.hint,
            complexity=src.complexity, start_datetime=start_dt, end_datetime=end_dt,
            total_number_testcase=len(testcases_by_source[pid]), report=src.report,
        )
        session.add(clone)
        session.flush()
        for tc in testcases_by_source[pid]:
            session.add(Testcase(
                problem_id=clone.problem_id, input=tc.input, expected_output=tc.expected_output,
                is_sample=tc.is_sample, input_type=tc.input_type,
                expected_output_type=tc.expected_output_type,
            ))
        result.append(clone)
    return result


def get_problem_detail(
    session: Session, course_id: str, lesson_id: int, problem_id: int, current_user: User
) -> ProblemDetailResponse:
    get_viewable_course(session, course_id, current_user)
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    problem = get_problem_in_lesson(session, lesson, problem_id)

    is_student = current_user.role_id == Role.STUDENT
    if is_student and as_utc(problem.start_datetime) > now_utc():
        raise NotFoundError("Không tìm thấy bài tập trong buổi học")

    testcases = session.exec(
        select(Testcase).where(Testcase.problem_id == problem_id).order_by(Testcase.testcase_id)
    ).all()
    if is_student:
        testcases = [t for t in testcases if t.is_sample]

    return ProblemDetailResponse(
        id=problem.problem_id, lesson_id=lesson.lesson_id, course_id=course_id,
        code=problem.report, title=problem.title, description=problem.description,
        constraints=problem.constraints, level=problem.level, hint=problem.hint,
        complexity=problem.complexity, time_limit_seconds=problem.time_limit_seconds,
        total_number_testcase=problem.total_number_testcase,
        start_datetime=problem.start_datetime, end_datetime=problem.end_datetime,
        starter_code=problem.start_format_code,
        testcases=[
            {"id": t.testcase_id, "input": t.input,
             "expected_output": t.expected_output, "is_sample": t.is_sample}
            for t in testcases
        ],
    )


def _has_submissions(session: Session, problem_id: int) -> bool:
    return session.exec(select(Submission.submission_id).where(Submission.problem_id == problem_id)).first() is not None


def _replace_testcases(session: Session, problem: Problem, items: list[dict]) -> None:
    if _has_submissions(session, problem.problem_id):
        # Đổi testcase sau khi đã có bài nộp làm lệch điểm cũ -> chặn (bỏ dòng này nếu nhóm muốn cho phép)
        raise ConflictError("Bài đã có bài nộp, không thể thay đổi testcase")
    for tc in session.exec(select(Testcase).where(Testcase.problem_id == problem.problem_id)).all():
        session.delete(tc)
    session.flush()
    for item in items:
        session.add(Testcase(problem_id=problem.problem_id, **item))
    problem.total_number_testcase = len(items)
    session.add(problem)


def update_problem(
    session: Session, course_id: str, lesson_id: int, problem_id: int,
    data: ProblemUpdateRequest, current_user: User,
) -> ProblemDetailResponse:
    get_manageable_course(course_id, session, current_user, "Bạn không có quyền sửa bài tập")
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    problem = get_problem_in_lesson(session, lesson, problem_id)

    updates = data.model_dump(exclude_unset=True, exclude={"testcases", "starter_code"})
    new_start = updates.get("start_datetime") or problem.start_datetime
    new_end = updates.get("end_datetime") or problem.end_datetime
    if as_utc(new_start) > as_utc(new_end):          # kiểm tra TRƯỚC khi gán
        raise InvalidFormatError("start_datetime phải trước hoặc bằng end_datetime")

    for field, value in updates.items():
        if value is not None:
            setattr(problem, field, value)
    if data.starter_code is not None:
        problem.start_format_code = data.starter_code
    if data.testcases is not None:
        _replace_testcases(session, problem, [t.model_dump() for t in data.testcases])

    session.add(problem)
    session.commit()
    session.refresh(problem)
    return get_problem_detail(session, course_id, lesson_id, problem_id, current_user)


def replace_testcases(
    session: Session, course_id: str, lesson_id: int, problem_id: int,
    items: list[dict], current_user: User,
) -> ProblemDetailResponse:
    get_manageable_course(course_id, session, current_user, "Bạn không có quyền sửa testcase")
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    problem = get_problem_in_lesson(session, lesson, problem_id)
    _replace_testcases(session, problem, items)
    session.commit()
    session.refresh(problem)
    return get_problem_detail(session, course_id, lesson_id, problem_id, current_user)


def delete_problem(
    session: Session, course_id: str, lesson_id: int, problem_id: int, current_user: User
) -> None:
    get_manageable_course(course_id, session, current_user, "Bạn không có quyền xoá bài tập")
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    problem = get_problem_in_lesson(session, lesson, problem_id)
    if _has_submissions(session, problem_id):
        raise ConflictError("Bài đã có bài nộp, không thể xoá")
    for tc in session.exec(select(Testcase).where(Testcase.problem_id == problem_id)).all():
        session.delete(tc)
    session.delete(problem)
    refresh_assignment_count(session, lesson)
    session.commit()
