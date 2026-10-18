import io
import json
import re
import zipfile

from fastapi import UploadFile
from sqlmodel import Session, func, or_, select
from sqlmodel import Session, select

from app.core.utils.datetime_utils import as_utc, now_utc
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidFormatError,
    NotFoundError,
)
from app.core.dependencies import Role
from app.modules.classrooms.schemas import ClassResponse, ClassStudentResponse
from app.modules.courses.schemas import (
    AddStudentToCourseResponse,
from app.core.utils.datetime_utils import as_utc
from app.core.exceptions import ConflictError, ForbiddenError, InvalidFormatError
from app.core.dependencies import Role
from app.modules.courses.schemas import (
    CourseResponse,
    CourseTermsResponse,
    CreateCourseRequest,
    UpdateCourseRequest,
)
from app.modules.lessons.schemas import (
    LessonCreateRequest,
    LessonDetailResponse,
    LessonUpdateRequest,
)
from app.modules.problems.schemas import ProblemDetailResponse, ProblemUpdateRequest
from app.modules.courses.access import (
    get_lesson_in_course,
    get_manageable_course,
    get_problem_in_lesson,
    get_viewable_course,
)
from app.modules.courses.view import build_course_response
from app.models import (
    Class,
    Course,
    Enrollment,
    Lesson,
    Problem,
    Submission,
    Testcase,
    User,
)


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
    session.flush()
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
