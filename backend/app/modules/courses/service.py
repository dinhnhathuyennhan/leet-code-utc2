import re

from sqlmodel import Session, func, or_, select

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidFormatError,
    NotFoundError,
)
from app.core.dependencies import Role
from app.modules.courses.schemas import (
    CourseResponse,
    CourseTermsResponse,
    CreateCourseRequest,
    StudentDashboardResponse,
    StudentEnrollmentResponse,
    UpdateCourseRequest,
)
from app.modules.courses.access import (
    get_manageable_course,
    get_viewable_course,
)
from app.modules.courses.view import build_course_response
from app.models import (
    Course,
    Enrollment,
    Lesson,
    Problem,
    Submission,
    User,
)


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


def _parse_term(term: str) -> tuple[int, str]:
    """Tách học kỳ + năm học từ chuỗi term như 'HK1 - 2024'."""
    match = re.match(r"^HK(\d)\s*[- ]\s*(.+)$", term, re.IGNORECASE)
    if match is None:
        return 1, term
    return int(match.group(1)), match.group(2).strip()


def _visible_courses(session: Session, current_user: User) -> list[Course]:
    """Lấy danh sách course mà user được phép xem, theo role."""
    if current_user.role_id == Role.ADMIN:
        statement = select(Course)
    elif current_user.role_id == Role.TEACHER:
        statement = select(Course).where(Course.created_by == current_user.user_id)
    elif current_user.role_id == Role.STUDENT:
        statement = (
            select(Course)
            .join(Enrollment, Enrollment.course_id == Course.course_id)
            .where(Enrollment.student_id == current_user.user_id)
            .distinct()
        )
    else:
        raise ForbiddenError("Bạn không có quyền thực hiện hành động này")
    return list(session.exec(statement.order_by(Course.course_id)).all())


# def get_course(session: Session, course_id: str, current_user: User) -> CourseResponse:
#     course = get_viewable_course(session, course_id, current_user)
#     only_student_id = current_user.user_id if current_user.role_id == Role.STUDENT else None  # MỚI
#     return build_course_response(course, session, only_student_id=only_student_id)


def get_courses(
    session: Session,
    current_user: User,
    *,
    term: str | None = None,
    search: str | None = None,
) -> list[CourseResponse]:
    """Lấy danh sách lớp theo role, kèm filter server-side.

    Filter:
        - ``term``: LIKE %%term%% trên cột ``Course.term``.
        - ``search``: LIKE %%search%% trên ``course_id`` HOẶC ``course_name``.
    """
    statement = select(Course)

    if current_user.role_id == Role.ADMIN:
        pass
    elif current_user.role_id == Role.TEACHER:
        statement = statement.where(Course.created_by == current_user.user_id)
    elif current_user.role_id == Role.STUDENT:
        statement = (
            statement
            .join(Enrollment, Enrollment.course_id == Course.course_id)
            .where(Enrollment.student_id == current_user.user_id)
            .distinct()
        )
    else:
        raise ForbiddenError("Bạn không có quyền thực hiện hành động này")

    if term:
        statement = statement.where(Course.term.contains(term, autoescape=True))

    if search:
        statement = statement.where(
            or_(
                Course.course_id.contains(search, autoescape=True),
                Course.course_name.contains(search, autoescape=True),
            )
        )

    only_student_id = current_user.user_id if current_user.role_id == Role.STUDENT else None
    courses = session.exec(statement.order_by(Course.course_id)).all()
    return [
        build_course_response(course, session, only_student_id=only_student_id)
        for course in courses
    ]


def get_course_terms(session: Session, current_user: User) -> CourseTermsResponse:
    """Trả các học kỳ/năm học có trong các lớp người dùng được phép xem."""
    courses = _visible_courses(session, current_user)
    terms = [_parse_term(course.term) for course in courses if course.term]
    academic_years = sorted({year for _, year in terms}, reverse=True)
    semesters = sorted({semester for semester, _ in terms})
    return CourseTermsResponse(academic_years=academic_years, semesters=semesters)


# ─── Helpers dùng chung cho 2 endpoint mới (Lỗi 7 + Lỗi 8) ──────────────


def _check_can_view_student_courses(
    session: Session, current_user: User, target_student_id: str
) -> None:
    """Check quyền xem lớp/enrollments của 1 sinh viên.

    Quy tắc (theo role của current_user):
        - ADMIN: xem được mọi SV.
        - TEACHER: chỉ xem SV đang enroll ít nhất 1 lớp do mình tạo.
        - STUDENT: chỉ xem của chính mình.
    """
    if current_user.role_id == Role.STUDENT:
        if current_user.user_id != target_student_id:
            raise ForbiddenError("Bạn không có quyền xem thông tin sinh viên này")
        target = session.get(User, target_student_id)
        if target is None or target.role_id != Role.STUDENT:
            raise NotFoundError("Không tìm thấy sinh viên")
        return

    if current_user.role_id == Role.TEACHER:
        overlap = session.exec(
            select(Enrollment)
            .join(Course, Course.course_id == Enrollment.course_id)
            .where(
                Enrollment.student_id == target_student_id,
                Course.created_by == current_user.user_id,
            )
        ).first()
        if overlap is None:
            raise ForbiddenError("Bạn không có quyền xem thông tin sinh viên này")
        return

    if current_user.role_id == Role.ADMIN:
        target = session.get(User, target_student_id)
        if target is None or target.role_id != Role.STUDENT:
            raise NotFoundError("Không tìm thấy sinh viên")
        return

    raise ForbiddenError("Bạn không có quyền thực hiện hành động này")


def get_student_courses(
    session: Session, student_id: str, current_user: User
) -> list[CourseResponse]:
    """Lấy danh sách lớp mà 1 sinh viên đang học (Lỗi 7)."""
    _check_can_view_student_courses(session, current_user, student_id)

    statement = (
        select(Course)
        .join(Enrollment, Enrollment.course_id == Course.course_id)
        .where(Enrollment.student_id == student_id)
        .distinct()
    )
    if current_user.role_id == Role.TEACHER:
        statement = statement.where(Course.created_by == current_user.user_id)

    only_student_id = student_id if current_user.role_id == Role.STUDENT else None
    courses = session.exec(statement.order_by(Course.course_id)).all()
    return [
        build_course_response(course, session, only_student_id=only_student_id)
        for course in courses
    ]


def get_student_enrollments(
    session: Session, student_id: str, current_user: User
) -> list[StudentEnrollmentResponse]:
    """Lấy danh sách enrollment (kèm thông tin lớp) của 1 sinh viên (Lỗi 8)."""
    _check_can_view_student_courses(session, current_user, student_id)

    statement = (
        select(Enrollment, Course)
        .join(Course, Course.course_id == Enrollment.course_id)
        .where(Enrollment.student_id == student_id)
    )
    if current_user.role_id == Role.TEACHER:
        statement = statement.where(Course.created_by == current_user.user_id)
    statement = statement.order_by(Enrollment.enrollment_id.desc())

    rows = session.exec(statement).all()

    return [
        StudentEnrollmentResponse(
            enrollment_id=enrollment.enrollment_id,
            course_id=course.course_id,
            course_name=course.course_name,
            term=course.term,
            start_date=course.start_date,
            end_date=course.end_date,
            total_number_student=course.total_number_student,
        )
        for enrollment, course in rows
    ]


def get_student_dashboard(
    session: Session, student_id: str, current_user: User
) -> StudentDashboardResponse:
    """Lấy thống kê tổng quan cho trang Student Dashboard."""
    _check_can_view_student_courses(session, current_user, student_id)

    course_statement = (
        select(Course)
        .join(Enrollment, Enrollment.course_id == Course.course_id)
        .where(Enrollment.student_id == student_id)
        .distinct()
    )
    if current_user.role_id == Role.TEACHER:
        course_statement = course_statement.where(
            Course.created_by == current_user.user_id
        )
    courses = session.exec(course_statement.order_by(Course.course_id)).all()

    only_student_id = student_id if current_user.role_id == Role.STUDENT else None
    course_responses = [
        build_course_response(course, session, only_student_id=only_student_id)
        for course in courses
    ]

    total_classes = len(course_responses)
    if total_classes == 0:
        return StudentDashboardResponse(
            total_classes=0,
            completed_problems=0,
            total_problems=0,
            average_score=None,
            courses=[],
        )

    problem_count_statement = (
        select(func.count(Problem.problem_id))
        .join(Lesson, Lesson.lesson_id == Problem.lesson_id)
        .join(Course, Course.course_id == Lesson.course_id)
        .join(Enrollment, Enrollment.course_id == Course.course_id)
        .where(Enrollment.student_id == student_id)
    )
    if current_user.role_id == Role.TEACHER:
        problem_count_statement = problem_count_statement.where(
            Course.created_by == current_user.user_id
        )
    total_problems = session.exec(problem_count_statement).one() or 0

    completed_statement = (
        select(func.count(Submission.submission_id))
        .where(
            Submission.student_id == student_id,
            Submission.status == "accepted",
        )
    )
    completed_problems = session.exec(completed_statement).one() or 0

    average_statement = (
        select(
            func.sum(Submission.passed_count),
            func.count(Submission.submission_id),
        )
        .join(Problem, Problem.problem_id == Submission.problem_id)
        .where(
            Submission.student_id == student_id,
            Problem.total_number_testcase > 0,
        )
    )
    passed_sum, total_subs = session.exec(average_statement).one()
    if not total_subs:
        average_score: float | None = None
    else:
        ratio = (passed_sum or 0) / float(total_subs)
        average_score = round(ratio, 2)

    return StudentDashboardResponse(
        total_classes=total_classes,
        completed_problems=int(completed_problems),
        total_problems=int(total_problems),
        average_score=average_score,
        courses=course_responses,
    )
