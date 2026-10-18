import os
import sys
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Load .env ở root project TRƯỚC khi import app modules
# (cần cho JWT_SECRET_KEY — create_access_token require string, không được None).
_root_env = Path(__file__).resolve().parents[2] / ".env"
if _root_env.exists():
    from dotenv import load_dotenv

    load_dotenv(_root_env, override=False)

# Fallback nếu vẫn None (an toàn cho test).
if not os.getenv("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest"

import models  # noqa: E401,F401


# Tách engine và session ra riêng để dùng linh động hơn trong việc test
@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture()
def session(engine):
    with Session(engine) as s:
        yield s
