"""Reset mat khau cho mot tai khoan (dung cho local dev / test E2E).

Usage: python tools/set_password.py <email> [password]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from sqlalchemy import update  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

from app.core.database import engine  # noqa: E402
from app.core.security.passwords import hash_password  # noqa: E402
from app.models import User  # noqa: E402


def set_password(email: str, password: str) -> bool:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if user is None:
            print(f"KHONG TIM THAY user: {email}")
            return False
        # Ghi lại trước khi session đóng — sau commit instance bị "expire",
        # đọc thuộc tính sẽ ném DetachedInstanceError.
        role_id = user.role_id
        session.exec(
            update(User)
            .where(User.email == email)
            .values(hashed_password=hash_password(password), token_version=0)
        )
        session.commit()
    print(f"Da reset mat khau cho {email} (role_id={role_id})")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    email_arg = sys.argv[1]
    pwd = sys.argv[2] if len(sys.argv) > 2 else os.getenv("SEED_DEFAULT_PASSWORD", "Password@123")
    raise SystemExit(0 if set_password(email_arg, pwd) else 1)
