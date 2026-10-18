import re

from sqlmodel import Session, select

from app.core.datetime_utils import as_utc
from app.core.exceptions import ConflictError, ForbiddenError, InvalidFormatError
from app.dependencies import Role
from app.schemas.course import (
    CourseResponse,
    CourseTermsResponse,
    CreateCourseRequest,
    UpdateCourseRequest,
)
from app.services.course_access import get_manageable_course, get_viewable_course
from app.services.course_view import build_course_response
from models import Course, Enrollment, User


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
    # Request/ORM dùng giờ Việt Nam dạng naive; chuẩn hoá cả hai về UTC để so sánh.
    new_start = update_fields.get("start_date", course.start_date)
    new_end = update_fields.get("end_date", course.end_date)
    if as_utc(new_start) >= as_utc(new_end):
        raise InvalidFormatError("start_date phải trước end_date")

    for field, value in update_fields.items():
        setattr(course, field, value)

    session.add(course)
    session.commit()
    session.refresh(course)
    return build_course_response(course)


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
