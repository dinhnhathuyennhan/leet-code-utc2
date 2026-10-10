from datetime import UTC, datetime

from sqlmodel import Session, or_, select

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidFormatError,
    NotFoundError,
)
from app.dependencies import Role
from app.schemas.course import (
    AddStudentToCourseResponse,
    CourseResponse,
    CreateCourseRequest,
    GetStudentListResponse,
    StudentEnrollmentResponse,
    UpdateCourseRequest,
)
from models import Course, Enrollment, User


def get_course_enrollments(
    session: Session, course_id: str, current_user: User
) -> list[GetStudentListResponse]:
    _get_viewable_course(session, course_id, current_user)

    statement = (
        select(Enrollment, User)
        .join(User, Enrollment.student_id == User.user_id)
        .where(Enrollment.course_id == course_id)
    )
    return [
        GetStudentListResponse(
            enrollment_id=enrollment.enrollment_id,
            student_id=student.user_id,
            full_name=student.full_name,
            email=student.email,
        )
        for enrollment, student in session.exec(statement).all()
    ]


def _get_viewable_course(
    session: Session, course_id: str, current_user: User
) -> Course:
    course = session.get(Course, course_id)
    if course is None:
        raise NotFoundError("Không tìm thấy lớp học")

    if current_user.role_id == Role.ADMIN:
        can_view = True
    elif current_user.role_id == Role.TEACHER:
        can_view = course.created_by == current_user.user_id
    elif current_user.role_id == Role.STUDENT:
        can_view = (
            _find_enrollment(session, course_id, current_user.user_id) is not None
        )
    else:
        can_view = False

    if not can_view:
        raise ForbiddenError("Bạn không có quyền xem lớp học này")
    return course


def _get_manageable_course(
    course_id: str, session: Session, current_user: User, forbidden_message: str
) -> Course:
    course = session.get(Course, course_id)
    if not course:
        raise NotFoundError("Không tìm thấy lớp học")
    if current_user.role_id != Role.ADMIN and course.created_by != current_user.user_id:
        raise ForbiddenError(forbidden_message)
    return course


def _find_enrollment(
    session: Session, course_id: str, student_id: str
) -> Enrollment | None:
    return session.exec(
        select(Enrollment).where(
            Enrollment.course_id == course_id,
            Enrollment.student_id == student_id,
        )
    ).first()


def add_student_to_course(student_id, course_id, session, current_user):
    course = _get_manageable_course(
        course_id,
        session,
        current_user,
        "Bạn không có quyền thêm sinh viên vào lớp này",
    )

    student = session.get(User, student_id)
    if not student or student.role_id != 3:
        raise NotFoundError("Không tìm thấy sinh viên")

    if _find_enrollment(session, course_id, student_id):
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
    course = _get_manageable_course(
        course_id,
        session,
        current_user,
        "Bạn không có quyền thực hiện hành động này",
    )

    enrollment = _find_enrollment(session, course_id, student_id)
    if not enrollment:
        raise NotFoundError("Sinh viên không thuộc lớp học này")

    session.delete(enrollment)
    course.total_number_student -= 1
    session.commit()


def _to_response(course: Course) -> CourseResponse:
    """Map Course ORM → CourseResponse schema để trả về client."""
    return CourseResponse(
        course_id=course.course_id,
        course_name=course.course_name,
        term=course.term,
        start_date=course.start_date,
        end_date=course.end_date,
        avt_link=course.avt_link,
        created_by=course.created_by,
        total_number_student=course.total_number_student,
    )


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
    return _to_response(course)


def _normalize_to_utc(dt: datetime) -> datetime:
    """Đưa datetime về timezone-aware UTC để so sánh an toàn.

    SQLite lưu naive datetime; Postgres trả về tz-aware.
    Chuẩn hoá cả hai về UTC trước mọi phép so sánh.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


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
    course = _get_manageable_course(
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
        return _to_response(course)

    # Validate khoảng ngày khi có thay đổi, đối chiếu với giá trị đang lưu
    # trong DB để bắt cả trường hợp client chỉ gửi một trong hai ngày.
    # Chuẩn hoá giá trị DB về UTC trước khi so sánh (SQLite: naive, Postgres: aware).
    db_start = _normalize_to_utc(course.start_date)
    db_end = _normalize_to_utc(course.end_date)
    new_start = update_fields.get("start_date", db_start)
    new_end = update_fields.get("end_date", db_end)
    if new_start >= new_end:
        raise InvalidFormatError("start_date phải trước end_date")

    for field, value in update_fields.items():
        setattr(course, field, value)

    session.add(course)
    session.commit()
    session.refresh(course)
    return _to_response(course)


def get_course(session: Session, course_id: str, current_user: User) -> CourseResponse:
    course = _get_viewable_course(session, course_id, current_user)
    return _to_response(course)


def get_courses(
    session: Session,
    current_user: User,
    *,
    term: str | None = None,
    search: str | None = None,
) -> list[CourseResponse]:
    """Lấy danh sách lớp theo role, kèm filter server-side.

    Quy tắc:
        - ADMIN: thấy tất cả.
        - TEACHER: chỉ thấy lớp do mình tạo.
        - STUDENT: chỉ thấy lớp đã enroll.

    Filter:
        - ``term``: LIKE %%term%% trên cột ``Course.term`` (vd: "HK1", "2024").
        - ``search``: LIKE %%search%% trên ``course_id`` HOẶC ``course_name``.
    """
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

    if term:
        # contains() → SQL LIKE %term%; escape ký tự đặc biệt để tránh SQL injection.
        # (sqlmodel/SQLAlchemy đã tự parameter hóa; chỉ cần thoát \, %, _.)
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        statement = statement.where(Course.term.contains(escaped))

    if search:
        needle = search.strip()
        if needle:
            escaped = needle.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            statement = statement.where(
                or_(
                    Course.course_id.contains(escaped),
                    Course.course_name.contains(escaped),
                )
            )

    courses = session.exec(statement.order_by(Course.course_id)).all()
    return [_to_response(course) for course in courses]


# ─── Helpers dùng chung cho 2 endpoint mới (Lỗi 7 + Lỗi 8) ──────────────


def _check_can_view_student_courses(
    session: Session, current_user: User, target_student_id: str
) -> None:
    """Check quyền xem lớp/enrollments của 1 sinh viên.

    Quy tắc (theo role của current_user):
        - ADMIN: xem được mọi SV.
        - TEACHER: chỉ xem SV đang enroll ít nhất 1 lớp do mình tạo.
        - STUDENT: chỉ xem của chính mình.

    Raises:
        NotFoundError: SV không tồn tại hoặc không phải role student.
        ForbiddenError: current_user không đủ quyền.
    """
    target = session.get(User, target_student_id)
    if target is None or target.role_id != Role.STUDENT:
        raise NotFoundError("Không tìm thấy sinh viên")

    if current_user.role_id == Role.ADMIN:
        return

    if current_user.role_id == Role.STUDENT:
        if current_user.user_id != target_student_id:
            raise ForbiddenError("Bạn chỉ có thể xem thông tin của chính mình")
        return

    if current_user.role_id == Role.TEACHER:
        # Teacher chỉ xem được SV enroll lớp do mình tạo.
        overlap = session.exec(
            select(Enrollment)
            .join(Course, Course.course_id == Enrollment.course_id)
            .where(
                Enrollment.student_id == target_student_id,
                Course.created_by == current_user.user_id,
            )
        ).first()
        if overlap is None:
            raise ForbiddenError(
                "Bạn không có quyền xem thông tin sinh viên này"
            )
        return

    raise ForbiddenError("Bạn không có quyền thực hiện hành động này")


def get_student_courses(
    session: Session, student_id: str, current_user: User
) -> list[CourseResponse]:
    """Lấy danh sách lớp mà 1 sinh viên đang học (Lỗi 7).

    Phục vụ:
        - Student xem "Lớp đang học" của chính mình.
        - Teacher xem SV thuộc lớp mình dạy.
        - Admin xem tất cả.

    Lưu ý: Với role TEACHER, **chỉ trả về các lớp do teacher này tạo**
    mà student đã enroll — không trộn lẫn lớp của teacher khác
    (xem test ``test_teacher_can_only_view_students_in_their_courses``).
    """
    _check_can_view_student_courses(session, current_user, student_id)

    statement = (
        select(Course)
        .join(Enrollment, Enrollment.course_id == Course.course_id)
        .where(Enrollment.student_id == student_id)
        .distinct()
    )
    if current_user.role_id == Role.TEACHER:
        statement = statement.where(Course.created_by == current_user.user_id)

    courses = session.exec(statement.order_by(Course.course_id)).all()
    return [_to_response(course) for course in courses]


def get_student_enrollments(
    session: Session, student_id: str, current_user: User
) -> list[StudentEnrollmentResponse]:
    """Lấy danh sách enrollment (kèm thông tin lớp) của 1 sinh viên (Lỗi 8).

    Trả về các cặp ``(enrollment, course)`` thay vì chỉ CourseResponse,
    để client có thể hiển thị "Bạn đã đăng ký lớp X lúc Y" (nếu sau này
    schema có cột ``enrolled_at`` thì chỉ cần mở rộng StudentEnrollmentResponse).
    """
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
