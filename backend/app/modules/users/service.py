import uuid

from sqlalchemy import update
from sqlmodel import Session, select, func

from app.core.exceptions import AppError, ConflictError, NotFoundError, InvalidFormatError, ForbiddenError
from app.core.security.passwords import hash_password
from app.core.dependencies import Role
from sqlalchemy.exc import IntegrityError

from app.modules.users.schemas import (
    CreateStudentRequest,
    CreateTeacherRequest,
    UpdateUserRequest,
    UserResponse,
    UserListResponse,
    student_email,
)
from app.models import Class, Course, Enrollment, User


class UserNotFoundError(AppError):
    status_code = 404
    error_code = "USER_NOT_FOUND"


class NotAllowedToResetError(AppError):
    status_code = 403
    error_code = "NOT_ALLOWED_TO_RESET"


class NotAllowedToManageAccountError(AppError):
    status_code = 403
    error_code = "NOT_ALLOWED_TO_MANAGE_ACCOUNT"


class FieldNotEditableError(AppError):
    status_code = 422
    error_code = "FIELD_NOT_EDITABLE"


MANAGE_ACCOUNT_FORBIDDEN = "Bạn không có quyền quản lý tài khoản này"
RESET_FORBIDDEN = "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"
UNLOCK_FORBIDDEN = "Tài khoản này chỉ Quản trị viên mới được mở khoá"
_LOCK_ATTEMPTS = 3  # số lần thử khi khoá/mở khoá đồng thời liên tục chen giữa


def create_teacher(session: Session, data: CreateTeacherRequest) -> User:
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise ConflictError("Email đã được đăng ký")

    teacher = User(
        full_name=data.full_name,
        email=data.email,
        # Default password = email; teacher bắt buộc đổi mật khẩu lần đầu đăng nhập
        hashed_password=hash_password(data.email),
        must_change_password=True,
        avt_link=data.avt_link,
        role_id=Role.TEACHER,  # 1: admin, 2: teacher, 3: student
    )
    session.add(teacher)
    session.commit()
    session.refresh(teacher)
    return teacher


def create_student(session: Session, data: CreateStudentRequest) -> User:
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise ConflictError("Email đã được đăng ký")

    existing_code = session.exec(
        select(User).where(User.student_code == data.student_code)
    ).first()
    if existing_code:
        raise ConflictError("Mã sinh viên đã được sử dụng")

    db_class = session.get(Class, data.class_id)
    if not db_class:
        raise NotFoundError(f"Không tìm thấy lớp học có ID: {data.class_id}")

    student = User(
        student_code=data.student_code,
        full_name=data.full_name,
        email=data.email,
        # Default password = student_code (MSSV)
        hashed_password=hash_password(data.student_code),
        must_change_password=True,
        avt_link=data.avt_link,
        role_id=Role.STUDENT,  # 1: admin, 2: teacher, 3: student
        class_id=data.class_id,
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


def user_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=str(user.user_id),
        full_name=user.full_name,
        email=user.email,
        role_id=user.role_id,
        student_code=user.student_code if user.role_id == Role.STUDENT else None,
        class_id=user.class_id if user.role_id == Role.STUDENT else None,
        is_active=user.is_active,
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
        # Whitelist: chỉ Admin và Teacher được xem, mọi role khác bị từ chối
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

    - STUDENT: student_code (MSSV).
    - TEACHER, ADMIN: email.
    - Vai trò khác: không cho reset (whitelist, tránh role lạ rơi vào nhánh sai).
    """
    if user.role_id == Role.STUDENT:
        if user.student_code is None:
            raise NotAllowedToResetError(
                "Tài khoản sinh viên chưa có mã sinh viên để tạo mật khẩu tạm thời"
            )
        return user.student_code
    if user.role_id in (Role.TEACHER, Role.ADMIN):
        return user.email
    raise NotAllowedToResetError(RESET_FORBIDDEN)


def _get_user_or_404(session: Session, user_id: str | uuid.UUID) -> User:
    try:
        user_uuid = uuid.UUID(str(user_id))
    except ValueError:
        raise UserNotFoundError("Không tìm thấy tài khoản") from None

    user = session.get(User, user_uuid)
    if user is None:
        raise UserNotFoundError("Không tìm thấy tài khoản")
    return user


def _is_student_of_teacher(session: Session, teacher: User, student: User) -> bool:
    """Student có đang học một khoá do teacher tạo (Course.created_by) hay không."""
    return (
        session.exec(
            select(Enrollment.enrollment_id)
            .join(Course, Course.course_id == Enrollment.course_id)
            .where(
                Enrollment.student_id == student.user_id,
                Course.created_by == teacher.user_id,
            )
        ).first()
        is not None
    )


def _can_manage_account(
    session: Session,
    actor: User,
    target: User,
    *,
    admin_target_roles: tuple[int, ...] = (Role.TEACHER, Role.STUDENT),
) -> bool:
    """Whitelist quyền quản lý tài khoản theo vai trò người gọi."""
    if actor.role_id == Role.ADMIN:
        return target.role_id in admin_target_roles
    if actor.role_id == Role.TEACHER:
        return target.role_id == Role.STUDENT and _is_student_of_teacher(
            session, actor, target
        )
    return False  # whitelist: Student, role lạ, role phát sinh sau này


def _ensure_can_manage_account(session: Session, current_user: User, target: User) -> None:
    if target.user_id == current_user.user_id or not _can_manage_account(
        session, current_user, target
    ):
        raise NotAllowedToManageAccountError(MANAGE_ACCOUNT_FORBIDDEN)


def reset_password(
    session: Session, current_user: User, target_user_id: str | uuid.UUID
) -> tuple[str, str]:
    """Đặt lại mật khẩu cho tài khoản mục tiêu.

    Mật khẩu tạm thời: sinh viên = student_code (MSSV); giáo viên/admin = email.

    Quyền (whitelist theo vai trò người gọi):
        - ADMIN: đặt lại mật khẩu bất kỳ tài khoản nào (Admin, Teacher, Student).
        - TEACHER: chỉ được đặt lại mật khẩu sinh viên đang học khoá do mình tạo.
        - STUDENT và mọi vai trò khác: không được phép đặt lại mật khẩu ai.

    Returns:
        tuple ``(user_id_str, temporary_password)`` để router trả về response.

    Raises:
        UserNotFoundError: không tìm thấy tài khoản mục tiêu.
        NotAllowedToResetError: người gọi không đủ quyền, hoặc tài khoản mục tiêu có vai trò lạ.
    """
    target = _get_user_or_404(session, target_user_id)

    if not _can_manage_account(
        session,
        current_user,
        target,
        admin_target_roles=(Role.ADMIN, Role.TEACHER, Role.STUDENT),
    ):
        raise NotAllowedToResetError(RESET_FORBIDDEN)

    temporary_password = _temporary_password_for(target)
    target.hashed_password = hash_password(temporary_password)
    target.must_change_password = True
    target.token_version += 1

    session.add(target)
    session.commit()
    session.refresh(target)
    return str(target.user_id), temporary_password


def _locked_by_teacher(session: Session, target: User) -> bool:
    """Tài khoản đang bị một Giáo viên khoá (Giáo viên được phép mở khoá).

    Whitelist: chỉ khi người khoá còn tồn tại và đúng role TEACHER. Khoá bởi Admin,
    role lạ, người khoá đã bị xoá hay khoá từ trước khi có ``locked_by`` (NULL)
    đều coi như chỉ Admin được mở khoá.
    """
    if target.locked_by is None:
        return False
    locker = session.get(User, target.locked_by)
    return locker is not None and locker.role_id == Role.TEACHER


def _apply_status_update(session: Session, target: User, *conditions, **values) -> int:
    result = session.exec(
        update(User).where(User.user_id == target.user_id, *conditions).values(**values)
    )
    session.commit()
    session.refresh(target)
    return result.rowcount


def lock_user(
    session: Session, current_user: User, target_user_id: str | uuid.UUID
) -> User:
    """Khoá tài khoản, ghi ``locked_by`` và tăng token_version.

    Idempotent: đã khoá thì không tăng token_version lần nữa. Giáo viên khoá lại thì
    giữ nguyên người khoá; Admin khoá lại thì ``locked_by`` chuyển sang Admin, để
    Giáo viên không mở khoá được nữa.

    Mỗi bước là UPDATE có điều kiện và quyết định theo ``rowcount`` chứ không theo
    trạng thái đọc trước đó, nên request khoá/mở khoá chạy đồng thời (vd: GV khoá
    ngay trước Admin, hay GV mở khoá chen giữa) không làm lệnh khoá của Admin bị bỏ
    qua im lặng.
    """
    target = _get_user_or_404(session, target_user_id)
    _ensure_can_manage_account(session, current_user, target)

    for _ in range(_LOCK_ATTEMPTS):
        # UPDATE nguyên tử để không mất lượt tăng token_version của thao tác đồng
        # thời khác (vd: đổi mật khẩu).
        if _apply_status_update(
            session,
            target,
            User.is_active.is_(True),
            is_active=False,
            locked_by=current_user.user_id,
            token_version=User.token_version + 1,
        ):
            return target
        # Đang bị khoá sẵn.
        if current_user.role_id == Role.ADMIN:
            if _apply_status_update(
                session, target, User.is_active.is_(False), locked_by=current_user.user_id
            ):
                return target
        elif not target.is_active:
            return target
        # Vừa bị mở khoá đồng thời giữa hai bước: thử khoá lại.
    raise ConflictError("Trạng thái tài khoản vừa thay đổi, vui lòng thử lại")


def unlock_user(
    session: Session, current_user: User, target_user_id: str | uuid.UUID
) -> User:
    """Mở khoá tài khoản (không đổi token_version). Idempotent.

    Giáo viên chỉ mở khoá được tài khoản do Giáo viên khoá; tài khoản do Admin
    khoá chỉ Admin mở được.
    """
    target = _get_user_or_404(session, target_user_id)
    _ensure_can_manage_account(session, current_user, target)

    if target.is_active:
        return target

    conditions = [User.is_active.is_(False)]
    if current_user.role_id != Role.ADMIN:
        if not _locked_by_teacher(session, target):
            raise NotAllowedToManageAccountError(UNLOCK_FORBIDDEN)
        # Chỉ mở khoá nếu người khoá không đổi kể từ lúc kiểm tra (vd: Admin vừa
        # khoá lại).
        conditions.append(User.locked_by == target.locked_by)

    updated = _apply_status_update(
        session, target, *conditions, is_active=True, locked_by=None
    )
    if updated == 0 and not target.is_active:
        raise NotAllowedToManageAccountError(UNLOCK_FORBIDDEN)
    return target


_EDITABLE_FIELDS = {
    Role.ADMIN: {"full_name", "email"},  # chỉ áp dụng khi Admin tự sửa chính mình
    Role.TEACHER: {"full_name", "email"},
    Role.STUDENT: {"full_name", "student_code", "class_id"},
}


def _ensure_can_edit_account(session: Session, current_user: User, target: User) -> None:
    """Quyền sửa thông tin tài khoản.

    - ADMIN: sửa chính mình, và mọi Teacher/Student (không sửa Admin khác).
    - TEACHER: chỉ sửa Student đang học khoá do mình tạo (không tự sửa mình).
    - STUDENT và mọi vai trò khác: không sửa tài khoản nào, kể cả của mình.

    Khác quyền khoá/mở khoá: Admin được tự sửa thông tin nhưng không được tự khoá mình.
    """
    if current_user.role_id == Role.ADMIN and target.user_id == current_user.user_id:
        return
    _ensure_can_manage_account(session, current_user, target)


def _other_user_with(session: Session, target: User, *conditions) -> User | None:
    return session.exec(
        select(User).where(User.user_id != target.user_id, *conditions)
    ).first()


def update_user(
    session: Session,
    current_user: User,
    target_user_id: str | uuid.UUID,
    data: UpdateUserRequest,
) -> User:
    """Sửa thông tin tài khoản. Quyền xem ``_ensure_can_edit_account``; field cho phép theo vai trò đích.

    Toàn bộ thay đổi được kiểm tra trước khi gán, nên lỗi không để lại thay đổi dở dang.
    """
    target = _get_user_or_404(session, target_user_id)
    _ensure_can_edit_account(session, current_user, target)

    changes = {
        key: value
        for key, value in data.model_dump(exclude_unset=True).items()
        if value is not None
    }

    if target.role_id == Role.STUDENT and "email" in changes:
        raise FieldNotEditableError(
            "Email sinh viên được tạo tự động theo MSSV, không thể sửa trực tiếp"
        )
    if target.role_id in (Role.ADMIN, Role.TEACHER) and (
        {"student_code", "class_id"} & changes.keys()
    ):
        raise FieldNotEditableError(
            "Chỉ tài khoản sinh viên mới có mã sinh viên và lớp hành chính"
        )
    if not changes.keys() <= _EDITABLE_FIELDS.get(target.role_id, set()):
        raise NotAllowedToManageAccountError(MANAGE_ACCOUNT_FORBIDDEN)

    new_code = changes.get("student_code")
    if new_code is not None and new_code != target.student_code:
        if _other_user_with(session, target, User.student_code == new_code):
            raise ConflictError("Mã sinh viên đã được sử dụng")
        derived_email = student_email(new_code)
        if _other_user_with(session, target, User.email == derived_email):
            raise ConflictError(f"Email {derived_email} đã được đăng ký")
        changes["email"] = derived_email
    else:
        changes.pop("student_code", None)

    if (
        target.role_id in (Role.ADMIN, Role.TEACHER)
        and "email" in changes
        and _other_user_with(session, target, User.email == changes["email"])
    ):
        raise ConflictError("Email đã được đăng ký")

    if "class_id" in changes and session.get(Class, changes["class_id"]) is None:
        raise NotFoundError(f"Không tìm thấy lớp học có ID: {changes['class_id']}")

    changes = {k: v for k, v in changes.items() if getattr(target, k) != v}
    if not changes:
        return target

    for key, value in changes.items():
        setattr(target, key, value)
    session.add(target)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        class_id = changes.get("class_id")
        if class_id is not None and session.get(Class, class_id) is None:
            # Lớp bị xoá/đổi tên giữa bước kiểm tra tồn tại và commit (vi phạm FK)
            raise NotFoundError(f"Không tìm thấy lớp học có ID: {class_id}") from None
        raise ConflictError("Email hoặc mã sinh viên đã được sử dụng") from None
    session.refresh(target)
    return target
