from sqlmodel import Session, select, func

from app.core.date import age_calculation
from app.core.exceptions import AppError, ConflictError, NotFoundError, InvalidFormatError, ForbiddenError
from app.core.password import hash_password
from app.dependencies import Role
from app.schemas.user import (
    CreateStudentRequest,
    CreateTeacherRequest,
    UserResponse,
    UserListResponse,
    password_from_date,
    student_temp_password,
)
from models import Class, Course, Enrollment, User


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

    db_class = session.get(Class, data.class_id)
    if not db_class:
        raise NotFoundError(f"Không tìm thấy lớp học có ID: {data.class_id}")

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
        hashed_password=hash_password(student_temp_password(data.user_id)),
        must_change_password=True,
        date_of_birth=data.date_of_birth,
        avt_link=data.avt_link,
        role_id=3,  # 1: admin, 2: teacher, 3: student
        class_id=data.class_id,
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
        class_id=user.class_id if user.role_id == Role.STUDENT else None,
    )

def list_users(
    session: Session,
    current_user: User,
    role_id: int | None,
    class_id: str | None,
    page: int,
    page_size: int,
) -> UserListResponse:
    if role_id is not None and role_id not in (
        Role.ADMIN,
        Role.TEACHER,
        Role.STUDENT,
    ):
        raise InvalidFormatError("role_id không hợp lệ")

    conditions = []

    if current_user.role_id == Role.TEACHER:
        # Teacher chỉ thấy Student đang học khoá do mình tạo, bất kể role_id truyền vào
        managed_course_ids = select(Course.course_id).where(
            Course.created_by == current_user.user_id
        )
        managed_student_ids = select(Enrollment.student_id).where(
            Enrollment.course_id.in_(managed_course_ids)
        )
        conditions.append(User.role_id == Role.STUDENT)
        conditions.append(User.user_id.in_(managed_student_ids))
    elif current_user.role_id != Role.ADMIN:
        # Whitelist: chỉ Admin và Teacher được xem, mọi role khác (kể cả role phát sinh sau này) bị từ chối
        raise ForbiddenError("Bạn không có quyền xem danh sách người dùng")
    elif role_id is not None:
        conditions.append(User.role_id == role_id)

    if class_id is not None:
        conditions.append(User.role_id == Role.STUDENT)
        conditions.append(User.class_id == class_id)

    total = session.exec(select(func.count()).select_from(User).where(*conditions)).one()
    users = session.exec(
        select(User)
        .where(*conditions)
        .order_by(User.user_id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return UserListResponse(
        items=[user_response(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
    )


def _temporary_password_for(user: User) -> str:
    """Sinh mật khẩu tạm theo vai trò của tài khoản.

    - STUDENT: MSSV (``user_id``), không cần ngày sinh.
    - TEACHER, ADMIN: ngày sinh dạng ddmmyyyy.
    - Vai trò khác: không cho reset (whitelist, tránh role lạ rơi vào nhánh sai).
    """
    if user.role_id == Role.STUDENT:
        return student_temp_password(user.user_id)
    if user.role_id in (Role.TEACHER, Role.ADMIN):
        if user.date_of_birth is None:
            raise DateOfBirthRequiredError(
                "Tài khoản chưa có ngày sinh để tạo mật khẩu tạm thời"
            )
        return password_from_date(user.date_of_birth)
    raise NotAllowedToResetError(
        "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"
    )


def reset_password(
    session: Session, current_user: User, target_user_id: str
) -> tuple[str, str]:
    """Đặt lại mật khẩu cho tài khoản mục tiêu.

    Mật khẩu tạm thời: sinh viên = MSSV; giáo viên/admin = ngày sinh
    dạng ddmmyyyy (xem ``_temporary_password_for``).

    Quyền:
        - ADMIN: đặt lại mật khẩu bất kỳ tài khoản nào.
        - TEACHER: chỉ được đặt lại mật khẩu sinh viên thuộc lớp mình quản lý.
        - STUDENT: không được phép đặt lại mật khẩu ai.

    Returns:
        tuple ``(user_id, temporary_password)`` để router trả về response.

    Raises:
        UserNotFoundError: không tìm thấy tài khoản mục tiêu.
        NotAllowedToResetError: người gọi không đủ quyền, hoặc tài khoản mục tiêu có vai trò lạ.
        DateOfBirthRequiredError: giáo viên/admin mục tiêu chưa có ngày sinh.
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

    temporary_password = _temporary_password_for(target)
    target.hashed_password = hash_password(temporary_password)
    target.must_change_password = True
    target.token_version += 1

    session.add(target)
    session.commit()
    session.refresh(target)
    return target.user_id, temporary_password
