from sqlmodel import Session, select

from app.core.password import generate_temporary_password, hash_password
from app.dependencies import Role
from models import Course, Enrollment, User


class UserNotFoundError(Exception):
    """Không tìm thấy tài khoản."""


class NotAllowedToResetError(Exception):
    """Người gọi không có quyền đặt lại mật khẩu cho tài khoản này."""


def reset_password(
    session: Session, current_user: User, target_user_id: str
) -> tuple[str, str]:
    """Đặt lại mật khẩu cho tài khoản mục tiêu.

    Quyền:
        - ADMIN: đặt lại mật khẩu bất kỳ tài khoản nào.
        - TEACHER: chỉ được đặt lại mật khẩu sinh viên thuộc lớp mình quản lý.
        - STUDENT: không được phép đặt lại mật khẩu ai.

    Returns:
        tuple (user_id, temporary_password) để router trả về response.
    """
    target = session.get(User, target_user_id)
    if target is None:
        raise UserNotFoundError("Không tìm thấy tài khoản")

    # Bước 1: STUDENT bị chặn hoàn toàn
    if current_user.role_id == Role.STUDENT:
        raise NotAllowedToResetError(
            "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"
        )

    # Bước 2: TEACHER chỉ được đặt lại mật khẩu sinh viên trong lớp mình quản lý
    if current_user.role_id == Role.TEACHER:
        if target.role_id != Role.STUDENT:
            raise NotAllowedToResetError(
                "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"
            )
        # Kiểm tra sinh viên có thuộc lớp do giáo viên này tạo không
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

    # Bước 3: ADMIN được đặt lại mọi tài khoản (không cần check thêm)

    temporary_password = generate_temporary_password()
    target.hashed_password = hash_password(temporary_password)
    target.must_change_password = True
    target.token_version += 1

    session.add(target)
    session.commit()
    session.refresh(target)
    return target.user_id, temporary_password
