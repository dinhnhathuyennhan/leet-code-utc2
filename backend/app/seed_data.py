# app/seed.py
import logging
import os

from sqlmodel import Session, or_, select

from app.core.password import hash_password
from app.db import engine
from models import User

logger = logging.getLogger("uvicorn.error")

SEED_USERS = [
    {
        "user_id": "6451071003",
        "full_name": "TEACHER NEW",
        "email": "teacher.new@st.utc2.edu.vn",
        "role_id": 2,
        "must_change_password": True
    },
    {
        "user_id": "6451071004",
        "full_name": "STUDENT NEW",
        "email": "student.new@st.utc2.edu.vn",
        "role_id": 3,
        "must_change_password": True
    },
    {
        "user_id": "6451071005",
        "full_name": "STUDENT TOKEN",
        "email": "student.token@st.utc2.edu.vn",
        "role_id": 3
    },
]


def seed_users() -> None:
    logger.info("Seed users: bắt đầu (SEED_DATA=%s)", os.getenv("SEED_DATA"))

    if os.getenv("SEED_DATA", "false").lower() != "true":
        logger.info("Seed users: bỏ qua vì SEED_DATA không phải 'true'")
        return

    password = os.getenv("SEED_DEFAULT_PASSWORD", "LeetCodeForUtc2")
    # default password nếu không set .env

    with Session(engine) as session:
        created = 0
        for data in SEED_USERS:
            exists = session.exec(
                select(User).where(
                    or_(User.user_id == data["user_id"], User.email == data["email"])
                )
            ).first()
            if exists:
                logger.info("Seed users: %s đã tồn tại, bỏ qua", data["email"])
                continue

            session.add(
                User(
                    **data,
                    hashed_password=hash_password(password),
                )
            )
            created += 1

        session.commit()
        logger.info("Seed users: đã thêm %d user", created)
