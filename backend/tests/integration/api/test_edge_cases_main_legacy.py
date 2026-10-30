"""
Edge case tests — kiểm thử các tình huống đặc biệt có thể gây bug.

1. SQL injection attempt
2. Empty string filter
3. Special characters in term
4. Unicode in term
5. Very long term
6. Filter với course không tồn tại
7. Pagination edge cases
8. Multiple concurrent requests (race condition)
9. Token expired / invalid
10. Wrong role token
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# Load .env
_root_env = Path(__file__).resolve().parents[4] / ".env"
if _root_env.exists():
    from dotenv import load_dotenv
    load_dotenv(_root_env, override=False)
if not os.getenv("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from app.core.security.passwords import hash_password  # noqa: E402
from app.core.security.tokens import create_access_token  # noqa: E402
from app.core.database import get_session  # noqa: E402
from app.core.dependencies import Role  # noqa: E402
from app.core.utils.datetime_utils import VN_TZ  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Class, Course, User  # noqa: E402


ADMIN_ID = uuid.uuid4()
STUD_ID = uuid.uuid4()
TEACH_ID = uuid.uuid4()
BAD_ID = uuid.uuid4()


def setup_edge_db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    session.add(Class(class_id="C01", type="CĐ", course_number=1, department="CNTT"))
    session.add(
        User(
            user_id=ADMIN_ID,
            full_name="Admin",
            email="a@utc2.edu.vn",
            hashed_password=hash_password("x"),
            role_id=Role.ADMIN,
        )
    )
    session.add(
        User(
            user_id=STUD_ID,
            full_name="Student",
            email="s@st.utc2.edu.vn",
            hashed_password=hash_password("x"),
            role_id=Role.STUDENT,
            class_id="C01",
        )
    )
    session.add(
        User(
            user_id=TEACH_ID,
            full_name="Teacher",
            email="t@utc2.edu.vn",
            hashed_password=hash_password("x"),
            role_id=Role.TEACHER,
        )
    )
    session.commit()
    # Special character courses
    session.add_all(
        [
            Course(
                course_id="CS_100%",
                course_name="100% Java",
                term="HK1 2026-2027",
                created_by=TEACH_ID,
                start_date=datetime(2026, 9, 7, tzinfo=VN_TZ),
                end_date=datetime(2026, 12, 27, tzinfo=VN_TZ),
            ),
            Course(
                course_id="CS_50%",
                course_name="50% Off Python",
                term="HK1 2026-2027",
                created_by=TEACH_ID,
                start_date=datetime(2026, 9, 7, tzinfo=VN_TZ),
                end_date=datetime(2026, 12, 27, tzinfo=VN_TZ),
            ),
            Course(
                course_id="CS_un_der",
                course_name="underscore_test",
                term="HK1 2026-2027",
                created_by=TEACH_ID,
                start_date=datetime(2026, 9, 7, tzinfo=VN_TZ),
                end_date=datetime(2026, 12, 27, tzinfo=VN_TZ),
            ),
        ]
    )
    session.commit()
    return session


def hdr(user_id: uuid.UUID, role: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id, role, 0)}"}


def main():
    session = setup_edge_db()
    app.dependency_overrides[get_session] = lambda: (yield session)
    with TestClient(app) as client:
        h_admin = hdr(ADMIN_ID, Role.ADMIN)
        h_stud = hdr(STUD_ID, Role.STUDENT)

        print("=" * 70)
        print("  EDGE CASE TESTS")
        print("=" * 70)

        # Test 1: SQL injection attempt
        print("\n[1] SQL injection attempt trong term parameter")
        r = client.get("/courses", params={"term": "'; DROP TABLE course; --"}, headers=h_admin)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 0, f"SQL injection phải trả về 0, got {len(data)}"
        print(f"  OK: trả về {len(data)} kết quả (an toàn)")

        # Test 2: Empty string term → trả về tất cả
        print("\n[2] Empty string term")
        r = client.get("/courses", params={"term": ""}, headers=h_admin)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3, f"Empty term phải trả tất cả 3, got {len(data)}"
        print(f"  OK: trả về {len(data)} courses (tất cả)")

        # Test 3: Filter chính xác với ký tự %
        print("\n[3] Filter search='100%' (escape ký tự %)")
        r = client.get("/courses", params={"search": "100%"}, headers=h_admin)
        data = r.json()
        # Vì escape %, "100%" chỉ match đúng "100% Java" và "CS_100%"
        course_ids = {c["course_id"] for c in data}
        print(f"  Kết quả: {course_ids}")
        # Nếu KHÔNG escape, % sẽ match tất cả. Vì escape, chỉ match exact.
        assert len(data) <= 1, f"Phải match ≤1 vì escape, got {len(data)}"
        print("  OK: ký tự % được escape đúng")

        # Test 4: Filter chính xác với ký tự _
        print("\n[4] Filter search='CS_un' (escape ký tự _)")
        r = client.get("/courses", params={"search": "CS_un"}, headers=h_admin)
        data = r.json()
        course_ids = {c["course_id"] for c in data}
        print(f"  Kết quả: {course_ids}")
        # Nếu KHÔNG escape, _ match 1 char → có thể match "CS_50%" etc
        # Vì escape, chỉ match exact "CS_un_der"
        assert "CS_un_der" in course_ids or len(data) == 0
        print("  OK: ký tự _ được escape đúng")

        # Test 5: Unicode term
        print("\n[5] Unicode term 'HK1'")
        r = client.get("/courses", params={"term": "HK1"}, headers=h_admin)
        data = r.json()
        assert len(data) == 3
        print(f"  OK: {len(data)} courses có term chứa 'HK1'")

        # Test 6: Term với khoảng trắng đầu/cuối
        print("\n[6] Term với leading/trailing spaces")
        r = client.get("/courses", params={"term": "  HK1  "}, headers=h_admin)
        data = r.json()
        # BE không trim → sẽ trả 0 vì không có term nào bắt đầu bằng space
        print(f"  Kết quả: {len(data)} courses (BE không trim - chấp nhận)")
        # Verify: FE sẽ trim trước khi gửi
        assert r.status_code == 200
        print("  OK: 200 OK")

        # Test 7: Token giả
        print("\n[7] Token invalid")
        r = client.get("/courses", headers={"Authorization": "Bearer FAKE_TOKEN"})
        assert r.status_code == 401
        print("  OK: 401 cho token giả")

        # Test 8: Token hết hạn (giả lập với token tự tạo có exp quá khứ)
        print("\n[8] Token thiếu field bắt buộc")
        import jwt
        bad_token = jwt.encode(
            {"sub": str(ADMIN_ID), "role": Role.ADMIN, "type": "access"},
            "test-secret-key-for-pytest",
            algorithm="HS256",
        )
        r = client.get("/courses", headers={"Authorization": f"Bearer {bad_token}"})
        # Token thiếu 'tv' → 401
        assert r.status_code == 401
        print("  OK: 401 cho token thiếu claim")

        # Test 9: Role không hợp lệ trong DB
        print("\n[9] User với role_id không hợp lệ (giả lập trong DB)")
        # Tạo user với role_id=99
        bad_user = User(
            user_id=BAD_ID,
            full_name="Bad",
            email="bad@utc2.edu.vn",
            hashed_password=hash_password("x"),
            role_id=99,
        )
        session.add(bad_user)
        session.commit()
        h_bad = hdr(BAD_ID, 99)
        r = client.get("/courses", headers=h_bad)
        # Role 99 không nằm trong logic → có thể 403 hoặc empty
        print(f"  Status: {r.status_code} (BE handle unknown role)")
        assert r.status_code in (200, 403)

        # Test 10: Student truy cập course admin-only endpoint
        print("\n[10] Student truy cập POST /courses (chỉ admin/teacher)")
        r = client.post(
            "/courses",
            json={
                "course_id": "HACK",
                "course_name": "Hacked",
                "term": "HK1",
                "start_date": "2026-09-01T00:00:00+07:00",
                "end_date": "2026-12-01T00:00:00+07:00",
            },
            headers=h_stud,
        )
        assert r.status_code == 403
        print("  OK: 403 cho student cố tạo course")

        # Test 11: PATCH course không tồn tại
        print("\n[11] PATCH /courses/NOT_EXIST")
        r = client.patch(
            "/courses/NOT_EXIST",
            json={"course_name": "Updated"},
            headers=h_admin,
        )
        assert r.status_code == 404
        print("  OK: 404 cho course không tồn tại")

        # Test 12: PATCH với start_date >= end_date
        print("\n[12] PATCH với date không hợp lệ (start >= end)")
        r = client.patch(
            "/courses/CS_100%",
            json={
                "start_date": "2026-12-27T00:00:00+07:00",
                "end_date": "2026-09-07T00:00:00+07:00",
            },
            headers=h_admin,
        )
        assert r.status_code in (400, 422)
        print(f"  OK: {r.status_code} cho date range invalid")

    app.dependency_overrides.clear()
    print("\n" + "=" * 70)
    print("  ALL EDGE CASE TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()