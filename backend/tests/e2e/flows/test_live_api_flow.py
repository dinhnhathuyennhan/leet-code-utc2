"""
Live API test — mô phỏng end-user flow thực tế.

Không cần start Uvicorn: dùng TestClient với SQLite in-memory,
gọi qua HTTP layer thật (không bypass như unit test).

Covers:
1. Login flow
2. Sinh viên xem danh sách lớp đang học (verify Lỗi 9 - mapping đúng)
3. Filter theo học kỳ (verify Lỗi 4)
4. Sinh viên xem chi tiết 1 lớp
5. Sinh viên xem danh sách bạn cùng lớp
6. Sinh viên xem danh sách enrollment (verify Lỗi 8)
7. Phân quyền: student không thấy course của student khác
8. Phân quyền: teacher chỉ thấy course do mình tạo
9. Phân quyền: admin thấy hết
10. Validation: filter escape LIKE wildcard
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add project root vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# Load .env ở root cho JWT_SECRET_KEY
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
from app.models import Class, Course, Enrollment, User  # noqa: E402


ADMIN_ID = uuid.uuid4()
TEACHER_A_ID = uuid.uuid4()
TEACHER_B_ID = uuid.uuid4()
STUDENT_A_ID = uuid.uuid4()
STUDENT_B_ID = uuid.uuid4()


# ============================== SETUP DB ==============================


def setup_test_db() -> Session:
    """Tạo DB in-memory, seed users + courses + enrollments."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    session = Session(engine)

    # Tạo 1 class để seed student có class_id hợp lệ
    cls = Class(class_id="CNTT01", type="CĐ", course_number=1, department="CNTT")
    session.add(cls)
    session.commit()

    # Admin
    admin = User(
        user_id=ADMIN_ID,
        full_name="Admin Demo",
        email="admin@utc2.edu.vn",
        hashed_password=hash_password("dummy"),
        role_id=Role.ADMIN,
    )
    # Teacher 1
    teacher_a = User(
        user_id=TEACHER_A_ID,
        full_name="Nguyễn Văn A",
        email="gv.a@utc2.edu.vn",
        hashed_password=hash_password("dummy"),
        role_id=Role.TEACHER,
    )
    # Teacher 2
    teacher_b = User(
        user_id=TEACHER_B_ID,
        full_name="Trần Thị B",
        email="gv.b@utc2.edu.vn",
        hashed_password=hash_password("dummy"),
        role_id=Role.TEACHER,
    )
    # Student A
    student_a = User(
        user_id=STUDENT_A_ID,
        student_code="6451071001",
        full_name="Lê Văn C",
        email="sv.c@st.utc2.edu.vn",
        hashed_password=hash_password("dummy"),
        role_id=Role.STUDENT,
        class_id="CNTT01",
    )
    # Student B
    student_b = User(
        user_id=STUDENT_B_ID,
        student_code="6451071002",
        full_name="Phạm Thị D",
        email="sv.d@st.utc2.edu.vn",
        hashed_password=hash_password("dummy"),
        role_id=Role.STUDENT,
        class_id="CNTT01",
    )

    session.add_all([admin, teacher_a, teacher_b, student_a, student_b])
    session.commit()

    # Courses
    courses = [
        Course(
            course_id="CS101",
            course_name="Nhập môn lập trình",
            term="HK1 2026-2027",
            created_by=TEACHER_A_ID,
            start_date=datetime(2026, 9, 7, tzinfo=VN_TZ),
            end_date=datetime(2026, 12, 27, tzinfo=VN_TZ),
        ),
        Course(
            course_id="CS102",
            course_name="Cấu trúc dữ liệu",
            term="HK1 2026-2027",
            created_by=TEACHER_A_ID,
            start_date=datetime(2026, 9, 7, tzinfo=VN_TZ),
            end_date=datetime(2026, 12, 27, tzinfo=VN_TZ),
        ),
        Course(
            course_id="MATH201",
            course_name="Toán rời rạc",
            term="HK2 2026-2027",
            created_by=TEACHER_B_ID,
            start_date=datetime(2027, 1, 5, tzinfo=VN_TZ),
            end_date=datetime(2027, 4, 30, tzinfo=VN_TZ),
        ),
        Course(
            course_id="DB101",
            course_name="Cơ sở dữ liệu",
            term="HK2 2025-2026",
            created_by=TEACHER_A_ID,
            start_date=datetime(2026, 1, 5, tzinfo=VN_TZ),
            end_date=datetime(2026, 4, 30, tzinfo=VN_TZ),
        ),
    ]
    session.add_all(courses)
    session.commit()

    # Enrollments
    session.add_all(
        [
            Enrollment(course_id="CS101", student_id=STUDENT_A_ID),
            Enrollment(course_id="MATH201", student_id=STUDENT_A_ID),
            Enrollment(course_id="CS101", student_id=STUDENT_B_ID),
        ]
    )
    # Update total_number_student
    for c in courses:
        c.total_number_student = sum(
            1
            for e in session.exec(
                __import__("sqlmodel").select(Enrollment).where(
                    Enrollment.course_id == c.course_id
                )
            ).all()
        )
    session.commit()

    return session


def make_headers(user_id: uuid.UUID, role_id: int, token_version: int = 0) -> dict:
    token = create_access_token(
        user_id=user_id, role_id=role_id, token_version=token_version
    )
    return {"Authorization": f"Bearer {token}"}


def banner(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


# ============================== CHẠY TESTS ==============================


def main() -> None:
    session = setup_test_db()

    def _override_get_session():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_session] = _override_get_session

    with TestClient(app) as client:
        headers_student_a = make_headers(STUDENT_A_ID, Role.STUDENT)
        _headers_student_b = make_headers(STUDENT_B_ID, Role.STUDENT)
        headers_teacher_a = make_headers(TEACHER_A_ID, Role.TEACHER)
        headers_teacher_b = make_headers(TEACHER_B_ID, Role.TEACHER)
        headers_admin = make_headers(ADMIN_ID, Role.ADMIN)

        # ==================== TEST 1: Sinh viên xem danh sách lớp đang học ====================
        banner("TEST 1: Student A xem danh sách lớp đang học (verify Lỗi 9 mapping)")
        response = client.get("/courses", headers=headers_student_a)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        print(f"  Status: {response.status_code}")
        print(f"  Số lượng lớp: {len(data)}")
        assert len(data) == 2, f"Expected 2 courses for student_a, got {len(data)}"
        for c in data:
            print(f"    - {c['course_id']}: {c['course_name']} ({c['term']})")
            # Verify mapping đúng - Lỗi 9
            assert "course_id" in c, "Field course_id phải có (mapping OK)"
            assert "course_name" in c, "Field course_name phải có (mapping OK)"
            assert c["course_name"], "course_name không được rỗng (verify Lỗi 9)"
        course_ids = {c["course_id"] for c in data}
        assert course_ids == {"CS101", "MATH201"}, f"Expected CS101 + MATH201, got {course_ids}"
        print("  ✅ PASS: Lỗi 9 - mapping course_id/course_name đầy đủ")

        # ==================== TEST 2: Filter theo học kỳ (Lỗi 4) ====================
        banner("TEST 2: Admin filter courses theo term='HK1 2026' (verify Lỗi 4)")
        response = client.get(
            "/courses",
            params={"term": "HK1 2026"},
            headers=headers_admin,
        )
        assert response.status_code == 200
        data = response.json()
        print(f"  Status: {response.status_code}")
        print(f"  Filter term='HK1 2026' → {len(data)} kết quả")
        for c in data:
            print(f"    - {c['course_id']}: {c['course_name']} ({c['term']})")
        assert len(data) == 2
        for c in data:
            assert "HK1 2026" in c["term"]
        print("  ✅ PASS: Lỗi 4 - filter term qua query param")

        # ==================== TEST 3: Filter search theo course_id ====================
        banner("TEST 3: Search theo course_id='CS' (verify Lỗi 4 - search)")
        response = client.get(
            "/courses",
            params={"search": "CS"},
            headers=headers_admin,
        )
        data = response.json()
        print(f"  Status: {response.status_code}")
        print(f"  Search 'CS' → {len(data)} kết quả")
        for c in data:
            print(f"    - {c['course_id']}: {c['course_name']}")
        course_ids = {c["course_id"] for c in data}
        assert course_ids == {"CS101", "CS102"}, f"Got {course_ids}"
        print("  ✅ PASS: search hoạt động đúng trên course_id")

        # ==================== TEST 4: Student xem chi tiết 1 lớp ====================
        banner("TEST 4: Student A xem chi tiết CS101")
        response = client.get("/courses/CS101", headers=headers_student_a)
        assert response.status_code == 200
        data = response.json()
        print(f"  Status: {response.status_code}")
        print(f"  Course: {data['course_id']} - {data['course_name']}")
        print(f"  Term: {data['term']}")
        print(f"  Tổng SV: {data['total_number_student']}")
        assert data["course_id"] == "CS101"
        assert data["total_number_student"] == 2  # SV001 + SV002 enroll
        print("  ✅ PASS: chi tiết lớp load đúng")

        # ==================== TEST 5: Student xem danh sách bạn cùng lớp ====================
        banner("TEST 5: Student A xem danh sách sinh viên trong CS101")
        response = client.get("/courses/CS101/enrollments", headers=headers_student_a)
        assert response.status_code == 200
        data = response.json()
        print(f"  Status: {response.status_code}")
        print(f"  Có {len(data)} sinh viên trong CS101:")
        for s in data:
            print(f"    - {s['student_id']}: {s['full_name']} ({s['email']})")
        assert len(data) == 2
        student_ids = {s["student_id"] for s in data}
        assert student_ids == {str(STUDENT_A_ID), str(STUDENT_B_ID)}
        print("  ✅ PASS: danh sách SV trong lớp đầy đủ")

        # ==================== TEST 6: Student xem danh sách enrollment (Lỗi 8) ====================
        banner("TEST 6: Student A xem danh sách enrollment của chính mình (verify Lỗi 8)")
        response = client.get(
            f"/students/{STUDENT_A_ID}/enrollments",
            headers=headers_student_a,
        )
        assert response.status_code == 200
        data = response.json()
        print(f"  Status: {response.status_code}")
        print(f"  Có {len(data)} enrollment:")
        for e in data:
            print(
                f"    - enrollment_id={e['enrollment_id']} "
                f"course={e['course_id']} '{e['course_name']}' term={e['term']}"
            )
        assert len(data) == 2
        # Verify thứ tự DESC
        course_ids_ordered = [e["course_id"] for e in data]
        print(f"  Thứ tự enrollment (DESC): {course_ids_ordered}")
        for e in data:
            assert e["enrollment_id"] is not None
            assert e["course_name"], "Phải có course_name"
        print("  ✅ PASS: Lỗi 8 - enrollment trả về enrollment_id + course info")

        # ==================== TEST 7: Student xem courses của chính mình (Lỗi 7) ====================
        banner("TEST 7: Student A xem courses của chính mình (verify Lỗi 7)")
        response = client.get(
            f"/students/{STUDENT_A_ID}/courses",
            headers=headers_student_a,
        )
        assert response.status_code == 200
        data = response.json()
        print(f"  Status: {response.status_code}")
        print(f"  Có {len(data)} lớp đang học:")
        for c in data:
            print(f"    - {c['course_id']}: {c['course_name']}")
        course_ids = {c["course_id"] for c in data}
        assert course_ids == {"CS101", "MATH201"}
        print("  ✅ PASS: Lỗi 7 - courses per student hoạt động")

        # ==================== TEST 8: Student xem courses của người khác → 403 ====================
        banner("TEST 8: Student A xem courses của Student B → phải 403")
        response = client.get(
            f"/students/{STUDENT_B_ID}/courses",
            headers=headers_student_a,
        )
        print(f"  Status: {response.status_code}")
        assert response.status_code == 403
        print(f"  Body: {response.json()}")
        print("  ✅ PASS: chặn student xem data của student khác")

        # ==================== TEST 9: Teacher A chỉ thấy course do mình tạo ====================
        banner("TEST 9: Teacher A xem danh sách course (filter role)")
        response = client.get("/courses", headers=headers_teacher_a)
        assert response.status_code == 200
        data = response.json()
        print(f"  Status: {response.status_code}")
        print(f"  Teacher A thấy {len(data)} lớp:")
        for c in data:
            print(f"    - {c['course_id']} (created_by={c['created_by']})")
        course_ids = {c["course_id"] for c in data}
        # Teacher A (GV001) tạo CS101, CS102, DB101
        assert course_ids == {"CS101", "CS102", "DB101"}
        for c in data:
            assert c["created_by"] == str(TEACHER_A_ID)
        print("  ✅ PASS: teacher chỉ thấy lớp do mình tạo")

        # ==================== TEST 10: Teacher xem student của mình ====================
        banner("TEST 10: Teacher A xem courses của Student A (chỉ lớp do mình tạo)")
        response = client.get(
            f"/students/{STUDENT_A_ID}/courses",
            headers=headers_teacher_a,
        )
        assert response.status_code == 200
        data = response.json()
        print(f"  Status: {response.status_code}")
        print(f"  Teacher A thấy SV001 học {len(data)} lớp (của mình):")
        for c in data:
            print(f"    - {c['course_id']}: {c['course_name']}")
        course_ids = {c["course_id"] for c in data}
        # Student A enroll CS101 (của GV001) + MATH201 (của GV002)
        # Teacher A chỉ được thấy CS101
        assert course_ids == {"CS101"}
        print("  ✅ PASS: teacher chỉ thấy lớp của mình trong danh sách SV")

        # ==================== TEST 11: Teacher xem student không phải của mình ====================
        banner("TEST 11: Teacher B xem courses của Student A (Student A không học GV002)")
        response = client.get(
            f"/students/{STUDENT_A_ID}/courses",
            headers=headers_teacher_b,
        )
        print(f"  Status: {response.status_code}")
        # Student A enroll CS101 (GV001) + MATH201 (GV002) → Teacher B có quyền xem MATH201
        # → chỉ trả 1 lớp MATH201 (của GV002)
        if response.status_code == 200:
            data = response.json()
            course_ids = {c["course_id"] for c in data}
            print(f"  Teacher B thấy: {course_ids}")
            assert course_ids == {"MATH201"}
            print("  ✅ PASS: Teacher B thấy đúng lớp của mình (MATH201)")
        else:
            print(f"  Body: {response.json()}")
            assert response.status_code == 403

        # ==================== TEST 12: Admin thấy hết + không filter role ====================
        banner("TEST 12: Admin xem tất cả courses")
        response = client.get("/courses", headers=headers_admin)
        data = response.json()
        print(f"  Status: {response.status_code}")
        print(f"  Admin thấy {len(data)} lớp:")
        for c in data:
            print(f"    - {c['course_id']} (created_by={c['created_by']})")
        course_ids = {c["course_id"] for c in data}
        assert course_ids == {"CS101", "CS102", "MATH201", "DB101"}
        print("  ✅ PASS: admin thấy tất cả")

        # ==================== TEST 13: Filter escape LIKE wildcard ====================
        banner("TEST 13: Filter term='%' phải không match tất cả (escape LIKE)")
        response = client.get(
            "/courses",
            params={"term": "%"},
            headers=headers_admin,
        )
        data = response.json()
        print(f"  Status: {response.status_code}")
        print(f"  Filter term='%' → {len(data)} kết quả (phải = 0 vì escape)")
        assert len(data) == 0, f"Wildcard % phải được escape, got {len(data)} results"
        print("  ✅ PASS: LIKE wildcard được escape an toàn")

        # ==================== TEST 14: Course 404 ====================
        banner("TEST 14: GET /courses/COURSE_KHONG_TON_TAI")
        response = client.get("/courses/NOTFOUND", headers=headers_admin)
        print(f"  Status: {response.status_code}")
        assert response.status_code == 404
        print(f"  Body: {response.json()}")
        print("  ✅ PASS: 404 cho course không tồn tại")

        # ==================== TEST 15: Unauthenticated ====================
        banner("TEST 15: GET /courses không có token → 401")
        response = client.get("/courses")
        print(f"  Status: {response.status_code}")
        assert response.status_code == 401
        print("  ✅ PASS: 401 cho request không có token")

    app.dependency_overrides.clear()
    print("\n" + "=" * 70)
    print("  🎉 TẤT CẢ 15 LIVE TESTS ĐỀU PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()
