from sqlmodel import Session, func, select, or_

from app.core.utils.datetime_utils import as_utc, now_utc, vn_day_end, vn_day_start
from app.core.exceptions import ConflictError, ForbiddenError, InvalidFormatError, NotFoundError
from app.core.dependencies import Role
from app.modules.testcases.testcase_format import testcase_to_storage, testcase_to_api_values
from app.modules.problems.schemas import AdminTestcaseMutation, ProblemDetailResponse, ProblemUpdateRequest, ProblemCreateRequest, \
    ProblemListResponse, validate_problem_schedule
from app.modules.courses.access import (
    get_lesson_in_course, get_manageable_course, get_problem_in_lesson, get_viewable_course,
)
from app.models import Course, Lesson, Problem, Submission, Testcase, User


def assert_can_copy_problems(
    session: Session, problem_ids: list[int], current_user: User, target_lesson_id: int | None = None
) -> None:
    """Bank problems are shared; attached problems stay scoped to their course owner."""
    if not problem_ids:
        return
    rows = session.exec(
        select(Problem.problem_id, Problem.lesson_id, Course.created_by)
        .outerjoin(Lesson, Lesson.lesson_id == Problem.lesson_id)
        .outerjoin(Course, Course.course_id == Lesson.course_id)
        .where(Problem.problem_id.in_(problem_ids))
    ).all()
    if {row[0] for row in rows} != set(problem_ids):
        raise NotFoundError("Một hoặc nhiều bài tập không tồn tại")
    if current_user.role_id == Role.ADMIN:
        return
    for _pid, source_lesson_id, source_course_owner in rows:
        if source_lesson_id is None:
            continue
        already_in_target = target_lesson_id is not None and source_lesson_id == target_lesson_id
        if not already_in_target and source_course_owner != current_user.user_id:
            raise ForbiddenError("Bạn không có quyền sao chép bài tập này")


def refresh_assignment_count(session: Session, lesson: Lesson) -> None:
    session.flush()
    lesson.total_number_assignment = session.exec(
        select(func.count()).select_from(Problem).where(Problem.lesson_id == lesson.lesson_id)
    ).one()
    session.add(lesson)


def create_bank_problem(
    session: Session, data: ProblemCreateRequest
) -> ProblemDetailResponse:
    problem = Problem(
        lesson_id=None,
        title=data.title,
        function_name=data.function_name,
        description=data.description,
        constraints=data.constraints,
        level=data.level,
        time_limit_seconds=data.time_limit_seconds,
        start_format_code=data.starter_codes["python"],
        starter_codes=data.starter_codes,
        start_datetime=data.start_datetime,
        end_datetime=data.end_datetime,
        hint=data.hint,
        complexity=data.complexity,
        total_number_testcase=len(data.testcases),
        report=None,
    )
    session.add(problem)
    session.flush()
    for testcase in data.testcases:
        session.add(Testcase(
            problem_id=problem.problem_id,
            **testcase_to_storage(testcase.model_dump()),
        ))
    session.commit()
    session.refresh(problem)
    return _build_problem_detail_response(session, problem, course_id=None)

def get_bank_problem(session: Session, problem_id: int, current_user: User) -> ProblemDetailResponse:
    problem = session.get(Problem, problem_id)
    if problem is None:
        raise NotFoundError("Không tìm thấy bài tập nguồn")
    if problem.lesson_id is not None:
        lesson = session.get(Lesson, problem.lesson_id)
        if lesson is None:
            raise NotFoundError("Không tìm thấy buổi học của bài tập")
        return get_problem_detail(session, lesson.course_id, lesson.lesson_id, problem_id, current_user)
    return _build_problem_detail_response(session, problem, course_id=None)

def update_bank_problem(session: Session, problem_id: int, data: ProblemUpdateRequest) -> ProblemDetailResponse:
    problem = session.get(Problem, problem_id)
    if problem is None or problem.lesson_id is not None:
        raise NotFoundError("Không tìm thấy bài tập nguồn")
    updates = data.model_dump(exclude_unset=True, exclude={"testcases", "starter_code", "starter_codes"})
    if updates.get("start_datetime") is not None or updates.get("end_datetime") is not None:
        validate_problem_schedule(updates.get("start_datetime") or problem.start_datetime, updates.get("end_datetime") or problem.end_datetime)
    for field, value in updates.items():
        if value is not None or field in {"hint", "complexity", "report"}:
            setattr(problem, field, value)
    if data.starter_codes is not None:
        problem.starter_codes = data.starter_codes
        problem.start_format_code = data.starter_codes["python"]
    elif data.starter_code is not None:
        problem.start_format_code = data.starter_code
        problem.starter_codes = {**(problem.starter_codes or {}), "python": data.starter_code}
    if data.testcases is not None:
        _replace_testcases(session, problem, [testcase_to_storage(t.model_dump()) for t in data.testcases])
    session.add(problem)
    session.commit()
    session.refresh(problem)
    return _build_problem_detail_response(session, problem, course_id=None)

def delete_bank_problem(session: Session, problem_id: int) -> None:
    problem = session.get(Problem, problem_id)
    if problem is None or problem.lesson_id is not None:
        raise NotFoundError("Không tìm thấy bài tập nguồn")
    if _has_submissions(session, problem_id):
        raise ConflictError("Bài đã có bài nộp, không thể xoá")
    for testcase in session.exec(select(Testcase).where(Testcase.problem_id == problem_id)).all():
        session.delete(testcase)
    session.delete(problem)
    session.commit()


def list_problems(
    session: Session,
    current_user: User,
    *,
    q: str | None,
    level: str | None,
    course_id: str | None,
    page: int,
    page_size: int,
) -> ProblemListResponse:
    filters = []
    if current_user.role_id == Role.TEACHER:
        own_course_lesson_ids = select(Lesson.lesson_id).join(
            Course, Course.course_id == Lesson.course_id
        ).where(Course.created_by == current_user.user_id)
        filters.append(
            or_(Problem.lesson_id.is_(None), Problem.lesson_id.in_(own_course_lesson_ids))
        )
    if q and q.strip():
        filters.append(Problem.title.ilike(f"%{q.strip()}%"))
    if level is not None:
        filters.append(Problem.level == level)
    if course_id is not None:
        filters.append(
            Problem.lesson_id.in_(
                select(Lesson.lesson_id).where(Lesson.course_id == course_id)
            )
        )

    total = session.exec(
        select(func.count())
        .select_from(Problem)
        .where(*filters)
    ).one()
    rows = session.exec(
        select(Problem)
        .where(*filters)
        .order_by(Problem.problem_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return ProblemListResponse(
        items=[
            {
                "id": problem.problem_id,
                "code": problem.report,
                "title": problem.title,
                "level": problem.level,
                "lesson_id": problem.lesson_id,
                "total_number_testcase": problem.total_number_testcase,
            }
            for problem in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


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

    empty_problems = [pid for pid in problem_ids if not testcases_by_source[pid]]
    if empty_problems:
        raise InvalidFormatError("Problem phải có ít nhất một testcase trước khi gắn vào Lesson")

    start_dt = vn_day_start(lesson.start_date)
    end_dt = vn_day_end(lesson.end_date)
    result: list[Problem] = []
    for pid in problem_ids:
        src = sources[pid]
        if src.lesson_id == lesson.lesson_id:
            result.append(src)
            continue
        clone = Problem(
            lesson_id=lesson.lesson_id, title=src.title, function_name=src.function_name,
            description=src.description,
            time_limit_seconds=src.time_limit_seconds, start_format_code=src.start_format_code,
            starter_codes=src.starter_codes or {"python": src.start_format_code},
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


def _build_problem_detail_response(
    session: Session,
    problem: Problem,
    course_id: str | None,
    is_student: bool = False,
) -> ProblemDetailResponse:
    testcases = session.exec(
        select(Testcase)
        .where(Testcase.problem_id == problem.problem_id)
        .order_by(Testcase.testcase_id)
    ).all()
    if is_student:
        testcases = [t for t in testcases if t.is_sample]

    return ProblemDetailResponse(
        id=problem.problem_id, lesson_id=problem.lesson_id, course_id=course_id,
        code=problem.report, title=problem.title, function_name=problem.function_name,
        description=problem.description,
        constraints=problem.constraints, level=problem.level, hint=problem.hint,
        complexity=problem.complexity, time_limit_seconds=problem.time_limit_seconds,
        total_number_testcase=problem.total_number_testcase,
        start_datetime=problem.start_datetime, end_datetime=problem.end_datetime,
        starter_code=problem.starter_codes.get("python") or problem.start_format_code,
        starter_codes=problem.starter_codes or {"python": problem.start_format_code},
        testcases=[
            {"id": t.testcase_id, **testcase_to_api_values(t), "is_sample": t.is_sample}
            for t in testcases
        ],
    )


def get_problem_detail(
    session: Session, course_id: str, lesson_id: int, problem_id: int, current_user: User
) -> ProblemDetailResponse:
    get_viewable_course(session, course_id, current_user)
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    problem = get_problem_in_lesson(session, lesson, problem_id)

    is_student = current_user.role_id == Role.STUDENT
    if is_student and as_utc(problem.start_datetime) > now_utc():
        raise NotFoundError("Không tìm thấy bài tập trong buổi học")
    return _build_problem_detail_response(session, problem, course_id, is_student)


def _has_submissions(session: Session, problem_id: int) -> bool:
    return session.exec(select(Submission.submission_id).where(Submission.problem_id == problem_id)).first() is not None


def _get_admin_testcase_problem(session: Session, problem_id: int) -> Problem:
    problem = session.get(Problem, problem_id)
    if problem is None:
        raise NotFoundError("Không tìm thấy bài tập")
    if _has_submissions(session, problem_id):
        raise ConflictError("Bài đã có bài nộp, không thể thay đổi testcase")
    return problem


def _refresh_problem_testcase_count(session: Session, problem: Problem) -> None:
    session.flush()
    problem.total_number_testcase = session.exec(
        select(func.count()).select_from(Testcase).where(Testcase.problem_id == problem.problem_id)
    ).one()
    session.add(problem)


def _validate_admin_testcase_mode(problem: Problem, data: AdminTestcaseMutation) -> None:
    expected = ("json_args", "json") if problem.function_name else ("stdin", "stdout")
    if (data.input_type, data.expected_output_type) != expected:
        raise InvalidFormatError(
            "Đề chấm theo hàm cần testcase JSON; đề stdin/stdout cần testcase văn bản"
        )


def add_admin_testcase(
    session: Session, problem_id: int, data: AdminTestcaseMutation, current_user: User,
) -> ProblemDetailResponse:
    problem = _get_admin_testcase_problem(session, problem_id)
    _validate_admin_testcase_mode(problem, data)
    session.add(Testcase(problem_id=problem_id, **testcase_to_storage(data.model_dump())))
    _refresh_problem_testcase_count(session, problem)
    session.commit()
    return get_bank_problem(session, problem_id, current_user)


def update_admin_testcase(
    session: Session, problem_id: int, testcase_id: int,
    data: AdminTestcaseMutation, current_user: User,
) -> ProblemDetailResponse:
    problem = _get_admin_testcase_problem(session, problem_id)
    _validate_admin_testcase_mode(problem, data)
    testcase = session.get(Testcase, testcase_id)
    if testcase is None or testcase.problem_id != problem_id:
        raise NotFoundError("Không tìm thấy testcase trong bài tập")
    for field, value in testcase_to_storage(data.model_dump()).items():
        setattr(testcase, field, value)
    session.add(testcase)
    session.commit()
    return get_bank_problem(session, problem_id, current_user)


def delete_admin_testcase(session: Session, problem_id: int, testcase_id: int) -> None:
    problem = _get_admin_testcase_problem(session, problem_id)
    testcase = session.get(Testcase, testcase_id)
    if testcase is None or testcase.problem_id != problem_id:
        raise NotFoundError("Không tìm thấy testcase trong bài tập")
    count = session.exec(
        select(func.count()).select_from(Testcase).where(Testcase.problem_id == problem_id)
    ).one()
    if count <= 1:
        raise ConflictError("Bài tập phải có ít nhất một testcase")
    session.delete(testcase)
    _refresh_problem_testcase_count(session, problem)
    session.commit()


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

    updates = data.model_dump(exclude_unset=True, exclude={"testcases", "starter_code", "starter_codes"})
    has_grading_changes = (
        any(updates.get(field) is not None for field in ("function_name", "time_limit_seconds"))
        or data.starter_code is not None
        or data.starter_codes is not None
        or data.testcases is not None
    )
    if has_grading_changes and _has_submissions(session, problem.problem_id):
        raise ConflictError("Bài đã có bài nộp, không thể sửa thông tin ảnh hưởng đến chấm")

    new_start = updates.get("start_datetime") or problem.start_datetime
    new_end = updates.get("end_datetime") or problem.end_datetime
    if updates.get("start_datetime") is not None or updates.get("end_datetime") is not None:
        validate_problem_schedule(new_start, new_end)  # kiểm tra TRƯỚC khi gán

    nullable_fields = {"hint", "complexity", "report"}
    for field, value in updates.items():
        if value is not None or field in nullable_fields:
            setattr(problem, field, value)
    if data.starter_codes is not None:
        problem.starter_codes = data.starter_codes
        problem.start_format_code = data.starter_codes["python"]
    elif data.starter_code is not None:
        problem.start_format_code = data.starter_code
        problem.starter_codes = {**(problem.starter_codes or {}), "python": data.starter_code}
    if data.testcases is not None:
        _replace_testcases(
            session,
            problem,
            [testcase_to_storage(t.model_dump()) for t in data.testcases],
        )

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
    _replace_testcases(session, problem, [testcase_to_storage(item) for item in items])
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
    # Attached problems are lesson-specific clones. Remove the clone and its
    # testcases; the source bank/course problem remains untouched.
    for testcase in session.exec(
        select(Testcase).where(Testcase.problem_id == problem.problem_id)
    ).all():
        session.delete(testcase)
    session.flush()
    session.delete(problem)
    refresh_assignment_count(session, lesson)
    session.commit()
