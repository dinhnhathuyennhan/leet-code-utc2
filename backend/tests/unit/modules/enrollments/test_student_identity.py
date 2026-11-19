"""Test phân biệt MSSV (`student_code`) với UUID (`user_id`).

Bối cảnh: trong bảng `user`, `user_id` là UUID (khoá chính) còn `student_code`
là MSSV 10 chữ số. FE đã từng hiển thị UUID dưới nhãn "MSSV" khiến giáo viên
không tìm được sinh viên. Các test dưới đây chốt API phải trả CẢ HAI, tách
bạch rõ, để FE có đủ dữ liệu hiển thị đúng MSSV.
"""

import uuid

from app.core.dependencies import Role
from app.modules.classrooms.service import get_class_students
from app.modules.enrollments.service import get_course_enrollments
from app.models import Class, Enrollment, User

pytest_plugins = (
    "tests.support.fixtures.user_fixtures",
    "tests.support.fixtures.course_fixtures",
)


def _add_class(session, class_id: str = "CQ.67.CNTT") -> Class:
    db_class = Class(
        class_id=class_id,
        type=class_id.split(".")[0],
        course_number=int(class_id.split(".")[1]),
        department=class_id.split(".")[2],
    )
    session.add(db_class)
    session.commit()
    return db_class


def _add_student(session, student_code: str, class_id: str | None = "CQ.67.CNTT") -> User:
    user = User(
        user_id=uuid.uuid4(),
        student_code=student_code,
        full_name=f"Sinh viên {student_code}",
        email=f"{student_code}@st.utc2.edu.vn",
        hashed_password="placeholder",
        role_id=Role.STUDENT,
        class_id=class_id,
    )
    session.add(user)
    session.commit()
    return user


class TestClassStudentsExposeStudentCode:
    """`GET /classes/{class_id}/students` phải trả MSSV bên cạnh UUID."""

    def test_returns_student_code_alongside_user_id(self, session):
        _add_class(session)
        student = _add_student(session, "6251071001")

        rows = get_class_students(session, "CQ.67.CNTT")

        assert len(rows) == 1
        assert rows[0].user_id == str(student.user_id)
        assert rows[0].student_code == "6251071001"
        assert rows[0].full_name == student.full_name

    def test_user_id_is_uuid_and_student_code_is_mssv(self, session):
        """Hai định danh phải khác nhau — MSSV KHÔNG phải UUID."""
        _add_class(session)
        _add_student(session, "6251071002")

        row = get_class_students(session, "CQ.67.CNTT")[0]

        assert uuid.UUID(row.user_id)
        assert row.user_id != row.student_code
        assert row.student_code == "6251071002"

    def test_teacher_has_no_student_code(self, session):
        """Giáo viên không có MSSV → `student_code` là None chứ không phải UUID."""
        _add_class(session)
        teacher = User(
            user_id=uuid.uuid4(),
            student_code=None,
            full_name="Giáo viên",
            email="gv@example.com",
            hashed_password="placeholder",
            role_id=Role.TEACHER,
            class_id="CQ.67.CNTT",
        )
        session.add(teacher)
        session.commit()

        rows = get_class_students(session, "CQ.67.CNTT")

        assert rows == []  # lọc theo role STUDENT nên giáo viên không xuất hiện


class TestCourseEnrollmentsExposeStudentCode:
    """`GET /courses/{id}/enrollments` phải trả MSSV bên cạnh UUID."""

    def test_returns_student_code_alongside_student_id(
        self, session, course, admin, student
    ):
        session.add(
            Enrollment(course_id=course.course_id, student_id=student.user_id)
        )
        session.commit()

        rows = get_course_enrollments(session, course.course_id, admin)

        assert len(rows) == 1
        assert rows[0].student_id == str(student.user_id)
        assert rows[0].student_code == student.student_code

    def test_student_code_is_not_the_uuid(self, session, course, admin, student):
        session.add(
            Enrollment(course_id=course.course_id, student_id=student.user_id)
        )
        session.commit()

        row = get_course_enrollments(session, course.course_id, admin)[0]

        assert row.student_id != row.student_code
        assert uuid.UUID(row.student_id)

    def test_every_enrolled_student_has_its_own_mssv(
        self, session, course, admin, student
    ):
        second = _add_student(session, "6351071002")
        session.add(
            Enrollment(course_id=course.course_id, student_id=student.user_id)
        )
        session.add(
            Enrollment(course_id=course.course_id, student_id=second.user_id)
        )
        session.commit()

        rows = get_course_enrollments(session, course.course_id, admin)

        codes = sorted(row.student_code for row in rows)
        assert codes == sorted([student.student_code, "6351071002"])
        assert all(row.student_code != row.student_id for row in rows)

    def test_enrollment_response_exposes_uuid_and_mssv(
        self, session, course, owner_teacher, student
    ):
        """API enrollment trả về cả hai định danh, không nhập nhằng."""
        from app.modules.enrollments.service import add_student_to_course

        result = add_student_to_course(
            student.user_id, course.course_id, session, owner_teacher
        )

        assert result.student_id == str(student.user_id)
        assert result.student_code == student.student_code
        assert result.student_id != result.student_code

    def test_students_without_mssv_still_enumerable(self, session, course, admin):
        """Sinh viên thiếu MSSV vẫn xuất hiện với `student_code = None`."""
        user = _add_student(session, "6251071003")
        user.student_code = None
        session.add(user)
        session.commit()
        session.add(
            Enrollment(course_id=course.course_id, student_id=user.user_id)
        )
        session.commit()

        rows = get_course_enrollments(session, course.course_id, admin)

        assert len(rows) == 1
        assert rows[0].student_id == str(user.user_id)
        assert rows[0].student_code is None
