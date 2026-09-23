from sqlmodel import Session, select

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.schemas.course import (
    AddStudentToCourseResponse,
    CourseResponse,
    CreateCourseRequest,
    UpdateCourseRequest,
)
from models import Course, Enrollment, User


def _get_manageable_course(
    course_id: str, session: Session, current_user: User, forbidden_message: str
) -> Course:
    course = session.get(Course, course_id)
    if not course:
        raise NotFoundError("Không tìm thấy lớp học")
    if current_user.role_id != 1 and course.created_by != current_user.user_id:
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
        course_id, session, current_user,
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
        enrollment_id=enrollment.enrollment_id
    )


def delete_student_from_course(student_id, course_id, session, current_user):
    course = _get_manageable_course(
        course_id, session, current_user,
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


def update_course(
    course_id: str,
    data: UpdateCourseRequest,
    session: Session,
    current_user: User,
) -> CourseResponse:
    """Cập nhật 1 phần thông tin lớp học.

    Quy tắc nghiệp vụ (theo api-design-course.md):
    - Không cho sửa `course_id`, `created_by`, `total_number_student`.
    - Chỉ field nào client gửi mới được cập nhật (partial update).
    - Nếu thay đổi `start_date` hoặc `end_date` thì phải bảo đảm
      `start_date < end_date` (đã validate ở schema).
    - Quyền: Admin mọi lớp, hoặc Teacher là chủ lớp (`created_by`).
    """
    course = session.get(Course, course_id)
    if not course:
        raise NotFoundError("Không tìm thấy lớp học")

    if current_user.role_id != 1 and course.created_by != current_user.user_id:
        raise ForbiddenError("Bạn không có quyền thực hiện hành động này")

    # Chỉ set các field client thực sự gửi — tránh ghi đè None lên giá trị cũ.
    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(course, field, value)

    session.add(course)
    session.commit()
    session.refresh(course)
    return _to_response(course)
