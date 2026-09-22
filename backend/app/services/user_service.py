from sqlmodel import Session, select

from app.core.date import age_calculation
from app.core.exceptions import AppError, ConflictError
from app.core.password import hash_password
from app.dependencies import Role
from app.schemas.user import (
    CreateStudentRequest,
    CreateTeacherRequest,
    UserResponse,
    password_from_date,
)
from models import Course, Enrollment, User


class DateOfBirthRequiredError(AppError):
    status_code = 422
    error_code = "DATE_OF_BIRTH_INVALID"


class UserNotFoundError(AppError):
    status_code = 404
    error_code = "USER_NOT_FOUND"


class NotAllowedToResetError(AppError):
    status_code = 403
    error_code = "NOT_ALLOWED_TO_RESET"


def create_teacher(session: Session, data: CreateTeacherRequest) -> User:
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise ConflictError("Email đã được đăng ký")

    age = age_calculation(
        data.date_of_birth.day,
        data.date_of_birth.month,
        data.date_of_birth.year,
    )

    if age < 22:
        raise DateOfBirthRequiredError("Người dùng phải đủ 22 tuổi")

    teacher = User(
        user_id=data.user_id,
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(password_from_date(data.date_of_birth)),
        must_change_password=True,
        date_of_birth=data.date_of_birth,
        avt_link=data.avt_link,
        role_id=2,  # 1: admin, 2: teacher, 3: student
    )
    session.add(teacher)
    session.commit()
    session.refresh(teacher)
    return teacher


def create_student(session: Session, data: CreateStudentRequest) -> User:
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise ConflictError("Email đã được đăng ký")

    age = age_calculation(
        data.date_of_birth.day,
        data.date_of_birth.month,
        data.date_of_birth.year,
    )

    if age < 17:
        raise DateOfBirthRequiredError("Người dùng phải đủ 17 tuổi")

    student = User(
        user_id=data.user_id,
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(password_from_date(data.date_of_birth)),
        must_change_password=True,
        date_of_birth=data.date_of_birth,
        avt_link=data.avt_link,
        role_id=3,  # 1: admin, 2: teacher, 3: student
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


def user_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        full_name=user.full_name,
        email=user.email,
        role_id=user.role_id,
        date_of_birth=user.date_of_birth,
    )


def reset_password(
    session: Session, current_user: User, target_user_id: str
) -> tuple[str, str]:
    """Đặt lại mật khẩu cho tài khoản mục tiêu.

    Mật khẩu tạm thời được sinh từ ngày sinh của tài khoản mục tiêu
    theo định dạng ddmmyyyy (xem ``password_from_date``).

    Quyền:
        - ADMIN: đặt lại mật khẩu bất kỳ tài khoản nào.
        - TEACHER: chỉ được đặt lại mật khẩu sinh viên thuộc lớp mình quản lý.
        - STUDENT: không được phép đặt lại mật khẩu ai.

    Returns:
        tuple ``(user_id, temporary_password)`` để router trả về response.

    Raises:
        UserNotFoundError: không tìm thấy tài khoản mục tiêu.
        NotAllowedToResetError: người gọi không đủ quyền.
        DateOfBirthRequiredError: tài khoản mục tiêu chưa có ngày sinh hợp lệ.
    """
    target = session.get(User, target_user_id)
    if target is None:
        raise UserNotFoundError("Không tìm thấy tài khoản")

    # STUDENT bị chặn hoàn toàn (kể cả tự reset chính mình)
    if current_user.role_id == Role.STUDENT:
        raise NotAllowedToResetError(
            "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"
        )

    # TEACHER chỉ được reset sinh viên thuộc lớp do mình tạo
    if current_user.role_id == Role.TEACHER:
        if target.role_id != Role.STUDENT:
            raise NotAllowedToResetError(
                "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"
            )
        teacher_courses = session.exec(
            select(Course.course_id).where(Course.created_by == current_user.user_id)
        ).all()
        if not teacher_courses:
            raise NotAllowedToResetError(
                "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"
            )
        enrolled = session.exec(
            select(Enrollment).where(
                Enrollment.student_id == target_user_id,
                Enrollment.course_id.in_(teacher_courses),
            )
        ).first()
        if enrolled is None:
            raise NotAllowedToResetError(
                "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"
            )

    # Tài khoản mục tiêu phải có ngày sinh để sinh mật khẩu tạm thời
    if target.date_of_birth is None:
        raise DateOfBirthRequiredError(
            "Tài khoản chưa có ngày sinh để tạo mật khẩu tạm thời"
        )

    temporary_password = password_from_date(target.date_of_birth)
    target.hashed_password = hash_password(temporary_password)
    target.must_change_password = True
    target.token_version += 1

    session.add(target)
    session.commit()
    session.refresh(target)
    return target.user_id, temporary_password

