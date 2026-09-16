from sqlmodel import Session

from app.core.password import generate_temporary_password, hash_password
from app.dependencies import Role
from models import User


class UserNotFoundError(Exception):
    """Không tìm thấy tài khoản."""


class NotAllowedToResetError(Exception):
    """Người gọi không có quyền đặt lại mật khẩu cho tài khoản này."""


def reset_password(
    session: Session, current_user: User, target_user_id: str
) -> tuple[str, str]:
    """Đặt lại mật khẩu cho tài khoản mục tiêu.

    Returns:
        tuple (user_id, temporary_password) để router trả về response.
    """
    target = session.get(User, target_user_id)
    if target is None:
        raise UserNotFoundError("Không tìm thấy tài khoản")

    if current_user.role_id == Role.TEACHER and target.role_id != Role.STUDENT:
        raise NotAllowedToResetError(
            "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"
        )

    temporary_password = generate_temporary_password()
    target.hashed_password = hash_password(temporary_password)
    target.must_change_password = True
    target.token_version += 1

    session.add(target)
    session.commit()
    session.refresh(target)
    return target.user_id, temporary_password
