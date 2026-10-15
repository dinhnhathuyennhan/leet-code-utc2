import io
import json
import re
import zipfile

from app.services.course_view import build_course_response
from sqlmodel import Session, func, select
from fastapi import UploadFile
from app.schemas.classroom import ClassResponse, ClassStudentResponse
from app.schemas.lesson import LessonCreateRequest, LessonDetailResponse, LessonUpdateRequest
from app.schemas.problem import ProblemDetailResponse, ProblemUpdateRequest
from app.core.datetime_utils import as_utc, now_utc
from app.services.course_access import (
    get_lesson_in_course,
    get_manageable_course,
    get_problem_in_lesson,
    get_viewable_course,
)

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidFormatError,
    NotFoundError,
)
from app.dependencies import Role
from app.schemas.course import (
    CourseResponse,
    CourseTermsResponse,
    CreateCourseRequest,
    UpdateCourseRequest,
)
from models import Class, Course, Enrollment, Lesson, Problem, Submission, Testcase, User

def _assert_can_copy_problems(
    session: Session,
    problem_ids: list[int],
    current_user: User,
    target_lesson_id: int | None = None,
) -> None:
    """Giáo viên chỉ được dùng/sao chép bài thuộc lớp do chính mình tạo.

    - Admin: được dùng mọi bài.
    - Bài đã nằm sẵn trong buổi đích (source_lesson_id == target_lesson_id): luôn được.
    - Bài ở buổi khác: chủ lớp chứa bài đó phải là current_user.
    (Sau này có kho UTC2: thêm điều kiện cho phép course_id == "BANK-UTC2" ở đây.)
    """
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

    for _problem_id, source_lesson_id, owner_id in rows:
        if source_lesson_id == target_lesson_id:
            continue
        if owner_id != current_user.user_id:
            raise ForbiddenError("Bạn không có quyền sao chép bài tập này")


def _refresh_assignment_count(session: Session, lesson: Lesson) -> None:
    """Đếm số bài thật đang có trong buổi rồi ghi vào total_number_assignment."""
    session.flush()  # đảm bảo các bài vừa clone đã được đếm
    lesson.total_number_assignment = session.exec(
        select(func.count()).select_from(Problem).where(Problem.lesson_id == lesson.lesson_id)
    ).one()
    session.add(lesson)

# SỬA: Clone bài tập khi tái sử dụng ở Lesson khác để Submission cũ không bị tính sang buổi mới.
def _get_lesson_problems(session: Session, problem_ids: list[int], lesson_id: int | None = None) -> list[Problem]:
    if not problem_ids:
        return []
    problem_ids = list(dict.fromkeys(problem_ids))
    problems = session.exec(select(Problem).where(Problem.problem_id.in_(problem_ids))).all()
    found_ids = {problem.problem_id for problem in problems}
    if found_ids != set(problem_ids):
        raise NotFoundError("Một hoặc nhiều bài tập không tồn tại")
    if lesson_id is None:
        return problems

    selected: list[Problem] = []
    for problem in problems:
        if problem.lesson_id == lesson_id:
            selected.append(problem)
            continue

        # SỬA: Mỗi lần gắn bài từ Lesson khác phải tạo problem_id mới; Submission
        # của bài nguồn vẫn giữ nguyên Lesson cũ và không “đi theo” bài mới.
        cloned_problem = Problem(
            lesson_id=lesson_id,
            title=problem.title,
            description=problem.description,
            time_limit_seconds=problem.time_limit_seconds,
            start_format_code=problem.start_format_code,
            constraints=problem.constraints,
            level=problem.level,
            hint=problem.hint,
            complexity=problem.complexity,
            start_datetime=problem.start_datetime,
            end_datetime=problem.end_datetime,
            total_number_testcase=problem.total_number_testcase,
            report=problem.report,
        )
        session.add(cloned_problem)
        session.flush()
        source_testcases = session.exec(select(Testcase).where(Testcase.problem_id == problem.problem_id)).all()
        for testcase in source_testcases:
            session.add(Testcase(
                problem_id=cloned_problem.problem_id,
                input=testcase.input,
                expected_output=testcase.expected_output,
                is_sample=testcase.is_sample,
                input_type=testcase.input_type,
                expected_output_type=testcase.expected_output_type,
            ))
        selected.append(cloned_problem)
    return selected


# SỬA: Chuẩn hoá response detail cho trang quản trị buổi học từ Lesson/Problem/Submission.
def get_lesson_detail(
    session: Session, course_id: str, lesson_id: int, current_user: User
) -> LessonDetailResponse:
    course = get_viewable_course(session, course_id, current_user)
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    problems = session.exec(select(Problem).where(Problem.lesson_id == lesson_id).order_by(Problem.problem_id)).all()
    total_students = session.exec(select(Enrollment).where(Enrollment.course_id == course_id)).all()
    submitted_students = session.exec(
        select(Submission.student_id).join(Problem, Submission.problem_id == Problem.problem_id)
        .where(Problem.lesson_id == lesson_id).distinct()
    ).all()
    scored_submissions = [
        (submission.passed_count / problem.total_number_testcase * 10)
        for problem in problems
        for submission in session.exec(select(Submission).where(Submission.problem_id == problem.problem_id)).all()
        if problem.total_number_testcase
    ]
    avg_score = round(sum(scored_submissions) / len(scored_submissions), 1) if scored_submissions else 0
    missing_students = max(len(total_students) - len(submitted_students), 0)
    first_problem = problems[0] if problems else None
    return LessonDetailResponse(
        id=lesson.lesson_id,
        order=lesson.lesson_number,
        title=lesson.lesson_name,
        course_code=course.course_id,
        course_name=course.course_name,
        start_date=lesson.start_date,
        end_date=lesson.end_date,
        deadline_notice=f"Hạn nộp: {lesson.end_date.strftime('%d/%m/%Y')} - 23:59",
        submitted_students=len(submitted_students),
        total_students=len(total_students),
        stats={
            "submission_rate": round(len(submitted_students) / len(total_students) * 100, 1) if total_students else 0,
            "completed_students": len(submitted_students),
            "avg_score": avg_score,
            "score_diff": "Chưa có dữ liệu đối chiếu",
            "ast_cases": 0,
            "ast_similarity": "Chưa chạy phân tích",
        },
        alert={
            "problem_code": first_problem.report if first_problem and first_problem.report else "—",
            "missing_students": missing_students,
            "problem_name": first_problem.title if first_problem else "chưa có bài tập",
            "deadline_text": lesson.end_date.strftime("%d/%m/%Y 23:59"),
        },
        exercises=[
            {
                "id": problem.problem_id,
                "order": index + 1,
                "title": problem.title,
                "report": problem.report,
                "level": problem.level,
                "description": problem.description,
                "constraints": problem.constraints,
                "hint": problem.hint,
                "complexity": problem.complexity,
                "time_limit_seconds": problem.time_limit_seconds,
                "total_number_testcase": problem.total_number_testcase,
                "starter_code": problem.start_format_code,
                "testcases": [
                    {"id": testcase.testcase_id, "input": testcase.input, "expected_output": testcase.expected_output, "is_sample": testcase.is_sample}
                    for testcase in session.exec(select(Testcase).where(Testcase.problem_id == problem.problem_id).order_by(Testcase.testcase_id)).all()
                ],
                "submitted_count": len(session.exec(select(Submission).where(Submission.problem_id == problem.problem_id)).all()),
            }
            for index, problem in enumerate(problems)
        ],
    )

# SỬA: Lấy danh sách lớp theo mã để dropdown ổn định và dễ cache ở frontend.
def get_classes(session: Session, current_user: User) -> list[ClassResponse]:
    del current_user
    return [
        ClassResponse(class_id=item.class_id, type=item.type, course_number=item.course_number, department=item.department)
        for item in session.exec(select(Class).order_by(Class.class_id)).all()
    ]


# SỬA: Lấy sinh viên của một lớp trong một query, không tải toàn bộ User về frontend.
def get_class_students(session: Session, class_id: str, current_user: User) -> list[ClassStudentResponse]:
    del current_user
    if session.get(Class, class_id) is None:
        raise NotFoundError("Không tìm thấy lớp hành chính")
    return [
        ClassStudentResponse(user_id=student.user_id, full_name=student.full_name, email=student.email, class_id=student.class_id)
        for student in session.exec(select(User).where(User.class_id == class_id, User.role_id == Role.STUDENT).order_by(User.user_id)).all()
    ]


# SỬA: Lấy đầy đủ nội dung một bài tập thuộc đúng course/lesson, sinh viên chỉ thấy testcase mẫu, và chỉ khi bài đã mở
def get_problem_detail(
    session: Session, course_id: str, lesson_id: int, problem_id: int, current_user: User
) -> ProblemDetailResponse:
    get_viewable_course(session, course_id, current_user)
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    problem = get_problem_in_lesson(session, lesson, problem_id)

    is_student = current_user.role_id == Role.STUDENT
    if is_student and as_utc(problem.start_datetime) > now_utc():
        raise NotFoundError("Không tìm thấy bài tập trong buổi học")  # chưa mở thì coi như chưa tồn tại

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


# SỬA: Cập nhật bài tập và testcase bằng các cột/model hiện có; không sửa models.py.
def update_problem(
    session: Session,
    course_id: str,
    lesson_id: int,
    problem_id: int,
    data: ProblemUpdateRequest,
    current_user: User,
) -> ProblemDetailResponse:
    get_manageable_course(course_id, session, current_user, "Bạn không có quyền sửa bài tập")
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    problem = get_problem_in_lesson(session, lesson, problem_id)

    updates = data.model_dump(exclude_unset=True, exclude={"testcases", "starter_code"})
    for field, value in updates.items():
        setattr(problem, field, value)
    if data.starter_code is not None:
        problem.start_format_code = data.starter_code
    if as_utc(problem.start_datetime) > as_utc(problem.end_datetime):
        raise InvalidFormatError("start_datetime phải trước hoặc bằng end_datetime")

    if data.testcases is not None:
        # SỬA: Thay toàn bộ testcase trong một transaction để tránh dữ liệu cũ còn sót.
        old_testcases = session.exec(select(Testcase).where(Testcase.problem_id == problem_id)).all()
        for testcase in old_testcases:
            session.delete(testcase)
        session.flush()
        for testcase in data.testcases:
            session.add(Testcase(problem_id=problem_id, **testcase.model_dump()))
        problem.total_number_testcase = len(data.testcases)

    session.add(problem)
    session.commit()
    session.refresh(problem)
    return get_problem_detail(session, course_id, lesson_id, problem_id, current_user)


# SỬA: Đọc testcase từ JSON hoặc ZIP JSON và thay dữ liệu testcase của Problem trong một transaction.
def upload_problem_testcases(
    session: Session,
    course_id: str,
    lesson_id: int,
    problem_id: int,
    file: UploadFile,
    current_user: User,
) -> ProblemDetailResponse:
    get_manageable_course(course_id, session, current_user, "Bạn không có quyền sửa testcase")
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    problem = get_problem_in_lesson(session, lesson, problem_id)

    raw = file.file.read()
    try:
        if (file.filename or "").lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                json_names = [name for name in archive.namelist() if name.lower().endswith(".json") and not name.endswith("/")]
                if not json_names:
                    raise InvalidFormatError("File ZIP không chứa file JSON testcase")
                payloads = [json.loads(archive.read(name).decode("utf-8")) for name in json_names]
                payload = next((item for item in payloads if isinstance(item, dict) and "testcases" in item), payloads[0])
        else:
            payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        raise InvalidFormatError("File testcase phải là JSON hợp lệ hoặc ZIP chứa JSON") from error

    items = payload.get("testcases", payload) if isinstance(payload, dict) else payload
    if not isinstance(items, list) or not items:
        raise InvalidFormatError("Danh sách testcase không hợp lệ hoặc đang rỗng")
    normalized = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or "input" not in item or "expected_output" not in item:
            raise InvalidFormatError(f"Testcase #{index} thiếu input hoặc expected_output")
        normalized.append({
            "input": str(item["input"]),
            "expected_output": str(item["expected_output"]),
            "is_sample": bool(item.get("is_sample", False)),
            "input_type": str(item.get("input_type", "stdin")),
            "expected_output_type": str(item.get("expected_output_type", "stdout")),
        })

    old_testcases = session.exec(select(Testcase).where(Testcase.problem_id == problem_id)).all()
    for testcase in old_testcases:
        session.delete(testcase)
    session.flush()
    for testcase in normalized:
        session.add(Testcase(problem_id=problem_id, **testcase))
    problem.total_number_testcase = len(normalized)
    session.add(problem)
    session.commit()
    session.refresh(problem)
    return get_problem_detail(session, course_id, lesson_id, problem_id, current_user)


# SỬA: Tạo Lesson bằng dữ liệu hiện có trong models.py, không thay đổi cấu trúc database.
def create_lesson(session: Session, course_id: str, data: LessonCreateRequest, current_user: User) -> CourseResponse:
    course = get_manageable_course(course_id, session, current_user, "Bạn không có quyền tạo buổi học")
    _assert_can_copy_problems(session, data.problem_ids, current_user)

    last_order = session.exec(
        select(Lesson.lesson_number).where(Lesson.course_id == course_id).order_by(Lesson.lesson_number.desc())
    ).first()
    lesson = Lesson(
        lesson_number=(last_order or 0) + 1,
        lesson_name=data.lesson_name,
        course_id=course_id,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    session.add(lesson)
    session.flush()
    _get_lesson_problems(session, data.problem_ids, lesson.lesson_id)
    _refresh_assignment_count(session, lesson)
    session.commit()
    session.refresh(course)
    return build_course_response(course, session)


# SỬA: Cập nhật Lesson và các bài tập được chọn trong form sửa buổi học.
def update_lesson(session: Session, course_id: str, lesson_id: int, data: LessonUpdateRequest, current_user: User) -> CourseResponse:
    course = get_manageable_course(course_id, session, current_user, "Bạn không có quyền sửa buổi học")
    lesson = get_lesson_in_course(session, course_id, lesson_id)

    updates = data.model_dump(exclude_unset=True)
    for field in ("lesson_name", "start_date", "end_date"):
        if field in updates and updates[field] is not None:
            setattr(lesson, field, updates[field])
    if lesson.start_date > lesson.end_date:
        raise InvalidFormatError("start_date phải trước hoặc bằng end_date")

    if data.problem_ids is not None:
        _assert_can_copy_problems(session, data.problem_ids, current_user, lesson.lesson_id)
        _get_lesson_problems(session, data.problem_ids, lesson.lesson_id)
        _refresh_assignment_count(session, lesson)  # MỚI: thay cho len(data.problem_ids)

    session.add(lesson)
    session.commit()
    session.refresh(course)
    return build_course_response(course, session)


# SỬA: Xoá Lesson nếu không còn ràng buộc Problem; tránh xoá mất submission lịch sử.
def delete_lesson(session: Session, course_id: str, lesson_id: int, current_user: User) -> None:
    get_manageable_course(course_id, session, current_user, "Bạn không có quyền xoá buổi học")
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    if session.exec(select(Problem).where(Problem.lesson_id == lesson_id)).first():
        raise ConflictError("Không thể xoá buổi học đã có bài tập")
    session.delete(lesson)
    session.commit()

def get_course(session: Session, course_id: str, current_user: User) -> CourseResponse:
    course = get_viewable_course(session, course_id, current_user)
    only_student_id = current_user.user_id if current_user.role_id == Role.STUDENT else None
    return build_course_response(course, session, only_student_id=only_student_id)

def create_course(
    data: CreateCourseRequest,
    session: Session,
    current_user: User,
) -> CourseResponse:
    """Tạo lớp học mới.

    Quy tắc nghiệp vụ (theo api-design-course.md):
    - `created_by` luôn lấy từ `current_user.user_id`, KHÔNG nhận từ client.
    - `total_number_student` luôn khởi tạo = 0.
    - `course_id` phải duy nhất — nếu trùng raise `ConflictError`.
    - Quyền: Admin hoặc Teacher (đã được `require_role` chặn ở router).
    """
    if session.get(Course, data.course_id):
        raise ConflictError("Mã lớp học đã tồn tại")

    course = Course(
        course_id=data.course_id,
        course_name=data.course_name,
        term=data.term,
        start_date=data.start_date,
        end_date=data.end_date,
        avt_link=data.avt_link,
        created_by=current_user.user_id,
        total_number_student=0,
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    return build_course_response(course)

def update_course(
    course_id: str,
    data: UpdateCourseRequest,
    session: Session,
    current_user: User,
) -> CourseResponse:
    """Cập nhật 1 phần thông tin lớp học.

    Quy tắc nghiệp vụ (theo api-design-course.md):
    - Không cho sửa `course_id`, `created_by`, `total_number_student`.
    - Chỉ field nào client gửi (và không null) mới được cập nhật.
    - Nếu thay đổi ngày, phải bảo đảm `start_date < end_date` khi đối chiếu
      với giá trị đang lưu trong DB (kể cả khi client chỉ gửi một trong hai).
    - Quyền: Admin mọi lớp, hoặc Teacher là chủ lớp (`created_by`).
    """
    course = get_manageable_course(
        course_id,
        session,
        current_user,
        "Bạn không có quyền thực hiện hành động này",
    )

    # `exclude_unset=True` chỉ chứa các field client thực sự gửi trong body.
    # Tuy nhiên nếu client gửi field=null thì key vẫn xuất hiện trong dict
    # với giá trị None — ta phải loại None để tránh ghi đè cột NOT NULL.
    update_fields = {
        key: value
        for key, value in data.model_dump(exclude_unset=True).items()
        if value is not None
    }

    if not update_fields:
        # Body trống hoặc toàn null → no-op, trả về trạng thái hiện tại.
        return build_course_response(course)

    # Validate khoảng ngày khi có thay đổi, đối chiếu với giá trị đang lưu
    # trong DB để bắt cả trường hợp client chỉ gửi một trong hai ngày.
    # Cả hai phía đều có múi giờ (DB qua UTCDateTime, input qua require_offset) nên so sánh trực tiếp.
    new_start = update_fields.get("start_date", course.start_date)
    new_end = update_fields.get("end_date", course.end_date)
    if new_start >= new_end:
        raise InvalidFormatError("start_date phải trước end_date")

    for field, value in update_fields.items():
        setattr(course, field, value)

    session.add(course)
    session.commit()
    session.refresh(course)
    return build_course_response(course)


# def get_course(session: Session, course_id: str, current_user: User) -> CourseResponse:
#     course = get_viewable_course(session, course_id, current_user)
#     only_student_id = current_user.user_id if current_user.role_id == Role.STUDENT else None  # MỚI
#     return build_course_response(course, session, only_student_id=only_student_id)


def get_courses(session: Session, current_user: User) -> list[CourseResponse]:
    courses = _visible_courses(session, current_user)
    only_student_id = current_user.user_id if current_user.role_id == Role.STUDENT else None
    return [
        build_course_response(course, session, only_student_id=only_student_id)
        for course in courses
    ]


def get_course_terms(session: Session, current_user: User) -> CourseTermsResponse:
    """Trả các học kỳ/năm học có trong các lớp người dùng được phép xem."""
    courses = _visible_courses(session, current_user)
    terms = [_parse_term(course.term) for course in courses]
    academic_years = sorted({year for _, year in terms}, reverse=True)
    semesters = sorted({semester for semester, _ in terms})
    return CourseTermsResponse(academic_years=academic_years, semesters=semesters)


def _visible_courses(session: Session, current_user: User) -> list[Course]:
    if current_user.role_id == Role.ADMIN:
        statement = select(Course)
    elif current_user.role_id == Role.TEACHER:
        statement = select(Course).where(Course.created_by == current_user.user_id)
    elif current_user.role_id == Role.STUDENT:
        statement = (
            select(Course)
            .join(Enrollment, Enrollment.course_id == Course.course_id)
            .where(Enrollment.student_id == current_user.user_id)
        )
    else:
        raise ForbiddenError("Bạn không có quyền thực hiện hành động này")
    return list(session.exec(statement.order_by(Course.course_id)).all())


def _parse_term(term: str) -> tuple[int, str]:
    match = re.match(r"^HK(\d)\s*[- ]\s*(.+)$", term, re.IGNORECASE)
    if match is None:
        return 1, term
    return int(match.group(1)), match.group(2).strip()
