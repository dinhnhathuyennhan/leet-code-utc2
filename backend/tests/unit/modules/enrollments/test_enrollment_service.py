"""Unit tests for enrollment service behavior."""

import uuid

import pytest

from app.core.exceptions import (
    ConflictError,
    EmptyFieldError,
    ForbiddenError,
    InvalidFormatError,
    NotFoundError,
)
from app.core.dependencies import Role
from app.models import Class, Enrollment
from app.modules.enrollments import service as enrollment_service
from app.modules.enrollments.service import (
    CONCURRENT_CLASS_ENROLLMENT,
    add_class_to_course,
    add_student_to_course,
    delete_student_from_course,
    get_course_enrollments,
)
from tests.support.fixtures.enrollment_fixtures import (
    counter_of,
    enroll_directly,
    enrollments_of,
)
from tests.support.fixtures.user_fixtures import make_user

pytest_plugins = (
    "tests.support.fixtures.user_fixtures",
    "tests.support.fixtures.course_fixtures",
)
# ============================== ADD / REMOVE STUDENT ==============================


class TestAddStudentToCourse:
    # giảng viên chủ khóa học thêm sinh viên và tăng total_number_student
    def test_owner_teacher_adds_student_and_increments_counter(
        self, session, course, owner_teacher, student
    ):
        result = add_student_to_course(
            student.user_id, course.course_id, session, owner_teacher
        )

        assert result.course_id == course.course_id
        assert result.student_id == str(student.user_id)
        assert result.enrollment_id is not None
        assert len(enrollments_of(session, course.course_id)) == 1
        assert counter_of(session, course) == 1

    # role admin không phải chủ khóa học
    # vẫn có thể thêm sinh viên và tăng total_number_student
    def test_admin_who_does_not_own_course_can_add_student(
        self, session, course, admin, student
    ):
        add_student_to_course(student.user_id, course.course_id, session, admin)

        assert counter_of(session, course) == 1

    # admin nhập MSSV (student_code) thay cho UUID vẫn thêm được sinh viên
    def test_admin_can_add_student_by_student_code(
        self, session, course, admin, student
    ):
        result = add_student_to_course(
            student.student_code, course.course_id, session, admin
        )

        assert result.student_id == str(student.user_id)
        assert result.student_code == student.student_code
        assert counter_of(session, course) == 1

    # raise forbidden nếu giảng viên không phải chủ khóa học
    def test_raises_forbidden_when_teacher_does_not_own_course(
        self, session, course, other_teacher, student
    ):
        with pytest.raises(
            ForbiddenError, match="Bạn không có quyền thêm sinh viên vào lớp này"
        ):
            add_student_to_course(
                student.user_id, course.course_id, session, other_teacher
            )

        assert enrollments_of(session, course.course_id) == []
        assert counter_of(session, course) == 0

    # raise not found khi không tìm thấy sinh viên
    def test_raises_not_found_when_student_id_does_not_exist(
        self, session, course, owner_teacher
    ):
        with pytest.raises(NotFoundError, match="Không tìm thấy sinh viên"):
            add_student_to_course(
                uuid.uuid4(), course.course_id, session, owner_teacher
            )

        assert counter_of(session, course) == 0

    # raise not found khi student_id truyền vào không phải là sinh viên
    def test_raises_not_found_when_target_user_is_not_a_student(
        self, session, course, owner_teacher, other_teacher
    ):
        with pytest.raises(NotFoundError, match="Không tìm thấy sinh viên"):
            add_student_to_course(
                other_teacher.user_id, course.course_id, session, owner_teacher
            )

        assert enrollments_of(session, course.course_id) == []

    # raise conflict khi sinh viên đã tồn tại trong khóa học
    def test_raises_conflict_when_student_already_enrolled(
        self, session, course, owner_teacher, student
    ):
        add_student_to_course(student.user_id, course.course_id, session, owner_teacher)

        with pytest.raises(ConflictError, match="Sinh viên đã có trong lớp học"):
            add_student_to_course(
                student.user_id, course.course_id, session, owner_teacher
            )

        # lần thêm trùng không được để lại dòng thừa hay tăng counter
        assert len(enrollments_of(session, course.course_id)) == 1
        assert counter_of(session, course) == 1

    # response trả cả UUID lẫn MSSV, không nhập nhằng 2 khái niệm
    def test_response_contains_student_code_alongside_uuid(
        self, session, course, owner_teacher, student
    ):
        result = add_student_to_course(
            student.user_id, course.course_id, session, owner_teacher
        )

        assert result.student_id == str(student.user_id)
        assert result.student_code == student.student_code


# 10 chữ số fullwidth (U+FF10..U+FF19): isdigit() = True nhưng không phải ASCII
FULLWIDTH_CODE = "".join(chr(0xFF10 + int(c)) for c in "1234567890")


class TestAddStudentToCourseByStudentCode:
    # thêm sinh viên bằng MSSV: enrollment lưu đúng UUID, counter tăng
    def test_adds_student_by_student_code(
        self, session, course, owner_teacher, student
    ):
        result = add_student_to_course(
            None,
            course.course_id,
            session,
            owner_teacher,
            student_code=student.student_code,
        )

        enrollments = enrollments_of(session, course.course_id)
        assert len(enrollments) == 1
        assert enrollments[0].student_id == student.user_id
        assert result.student_id == str(student.user_id)
        assert result.student_code == student.student_code
        assert counter_of(session, course) == 1

    # MSSV có khoảng trắng đầu/cuối vẫn được chấp nhận
    def test_strips_whitespace_around_student_code(
        self, session, course, owner_teacher, student
    ):
        add_student_to_course(
            None,
            course.course_id,
            session,
            owner_teacher,
            student_code=f"  {student.student_code} ",
        )

        assert counter_of(session, course) == 1

    # MSSV đúng định dạng nhưng không có ai → 404
    def test_raises_not_found_when_student_code_does_not_exist(
        self, session, course, owner_teacher, student
    ):
        missing_code = "0000000000"
        assert student.student_code != missing_code

        with pytest.raises(NotFoundError, match="Không tìm thấy sinh viên"):
            add_student_to_course(
                None,
                course.course_id,
                session,
                owner_teacher,
                student_code=missing_code,
            )

        assert counter_of(session, course) == 0

    # MSSV sai định dạng → 422, không chạm DB
    @pytest.mark.parametrize("bad_code", ["123456789", "12345678901", "12345abcde", FULLWIDTH_CODE])
    def test_raises_invalid_format_for_malformed_student_code(
        self, session, course, owner_teacher, bad_code
    ):
        with pytest.raises(InvalidFormatError):
            add_student_to_course(
                None, course.course_id, session, owner_teacher, student_code=bad_code
            )

        assert counter_of(session, course) == 0

    # MSSV rỗng / toàn khoảng trắng → EmptyFieldError
    @pytest.mark.parametrize("blank", ["", "   "])
    def test_raises_empty_field_for_blank_student_code(
        self, session, course, owner_teacher, blank
    ):
        with pytest.raises(EmptyFieldError):
            add_student_to_course(
                None, course.course_id, session, owner_teacher, student_code=blank
            )

    # không truyền student_id lẫn student_code → EmptyFieldError
    def test_raises_empty_field_when_no_identifier_given(
        self, session, course, owner_teacher
    ):
        with pytest.raises(EmptyFieldError):
            add_student_to_course(None, course.course_id, session, owner_teacher)

        assert counter_of(session, course) == 0

    # truyền cả 2 → InvalidFormatError (không đoán cái nào đúng)
    def test_raises_invalid_format_when_both_identifiers_given(
        self, session, course, owner_teacher, student
    ):
        with pytest.raises(InvalidFormatError):
            add_student_to_course(
                student.user_id,
                course.course_id,
                session,
                owner_teacher,
                student_code=student.student_code,
            )

        assert counter_of(session, course) == 0

    # teacher không sở hữu khoá → 403 dù MSSV hợp lệ
    def test_raises_forbidden_when_teacher_does_not_own_course(
        self, session, course, other_teacher, student
    ):
        with pytest.raises(ForbiddenError):
            add_student_to_course(
                None,
                course.course_id,
                session,
                other_teacher,
                student_code=student.student_code,
            )

        assert enrollments_of(session, course.course_id) == []

    # đã thêm qua UUID rồi thêm lại qua MSSV → 409
    def test_raises_conflict_when_already_enrolled_via_uuid(
        self, session, course, owner_teacher, student
    ):
        add_student_to_course(student.user_id, course.course_id, session, owner_teacher)

        with pytest.raises(ConflictError, match="Sinh viên đã có trong lớp học"):
            add_student_to_course(
                None,
                course.course_id,
                session,
                owner_teacher,
                student_code=student.student_code,
            )

        assert counter_of(session, course) == 1

    # MSSV thuộc user không phải sinh viên (dữ liệu bất thường) → 404, chỉ whitelist STUDENT
    def test_raises_not_found_when_code_belongs_to_non_student(
        self, session, course, owner_teacher, other_teacher
    ):
        other_teacher.student_code = "9999999999"
        session.add(other_teacher)
        session.commit()

        with pytest.raises(NotFoundError, match="Không tìm thấy sinh viên"):
            add_student_to_course(
                None,
                course.course_id,
                session,
                owner_teacher,
                student_code="9999999999",
            )

        assert enrollments_of(session, course.course_id) == []


class TestDeleteStudentFromCourse:
    # giảng viên chủ khóa học xóa sinh viên khỏi khóa và giảm total_number_student
    def test_owner_teacher_removes_student_and_decrements_counter(
        self, session, course, owner_teacher, student
    ):
        enroll_directly(session, course, student)

        delete_student_from_course(
            student.user_id, course.course_id, session, owner_teacher
        )

        assert enrollments_of(session, course.course_id) == []
        assert counter_of(session, course) == 0

    # raise forbidden khi giảng không phải chủ khóa học
    def test_raises_forbidden_when_teacher_does_not_own_course(
        self, session, course, other_teacher, student
    ):
        enroll_directly(session, course, student)

        with pytest.raises(
            ForbiddenError, match="Bạn không có quyền thực hiện hành động này"
        ):
            delete_student_from_course(
                student.user_id, course.course_id, session, other_teacher
            )

        # bị chặn thì dữ liệu phải giữ nguyên
        assert len(enrollments_of(session, course.course_id)) == 1
        assert counter_of(session, course) == 1

    # raise not found khi xóa sinh viên không thuộc về khóa học
    def test_raises_not_found_when_student_is_not_in_course(
        self, session, course, owner_teacher, student
    ):
        with pytest.raises(NotFoundError, match="Sinh viên không thuộc lớp học này"):
            delete_student_from_course(
                student.user_id, course.course_id, session, owner_teacher
            )

        # counter không được âm khi xoá người không có trong lớp
        assert counter_of(session, course) == 0


class TestGetCourseEnrollments:
    # admin xem được danh sách
    def test_admin_can_get_student_list(self, session, course, admin, student):
        enroll_directly(session, course, student)

        result = get_course_enrollments(session, course.course_id, admin)

        assert len(result) == 1
        assert result[0].student_id == str(student.user_id)
        assert result[0].student_code == student.student_code
        assert result[0].full_name == student.full_name
        assert result[0].email == student.email

    # teacher chủ lớp xem được
    def test_owner_teacher_can_get_student_list(
        self, session, course, owner_teacher, student
    ):
        enroll_directly(session, course, student)

        result = get_course_enrollments(session, course.course_id, owner_teacher)

        assert len(result) == 1
        assert result[0].student_id == str(student.user_id)

    # teacher không phải chủ lớp nhận 403
    def test_raises_forbidden_when_teacher_does_not_own_course(
        self, session, course, other_teacher
    ):
        with pytest.raises(ForbiddenError, match="Bạn không có quyền xem lớp học này"):
            get_course_enrollments(session, course.course_id, other_teacher)

    # student có trong lớp xem được
    def test_student_in_course_can_get_student_list(self, session, course, student):
        enroll_directly(session, course, student)

        result = get_course_enrollments(session, course.course_id, student)

        assert len(result) == 1
        assert result[0].student_id == str(student.user_id)

    # student không có trong lớp nhận 403
    def test_raises_forbidden_when_student_not_in_course(self, session, course):
        other_student = make_user(session, "SV002", 3)

        with pytest.raises(ForbiddenError, match="Bạn không có quyền xem lớp học này"):
            get_course_enrollments(session, course.course_id, other_student)

    # course_id không tồn tại nhận 404
    def test_raises_not_found_when_course_id_does_not_exist(self, session, admin):
        with pytest.raises(NotFoundError, match="Không tìm thấy lớp học"):
            get_course_enrollments(session, "KHONG_EXIST", admin)

    # lớp chưa có sinh viên trả []
    def test_returns_empty_list_when_course_has_no_students(
        self, session, course, owner_teacher
    ):
        result = get_course_enrollments(session, course.course_id, owner_teacher)

        assert result == []


class TestEnrollmentListStatusFields:
    # admin/teacher thấy class_id và is_active của sinh viên
    @pytest.mark.parametrize("caller_fixture", ["admin", "owner_teacher"])
    def test_admin_and_teacher_see_class_id_and_is_active(
        self, request, session, course, student, caller_fixture
    ):
        caller = request.getfixturevalue(caller_fixture)
        student.class_id = "CQ.64.CNTT"
        student.is_active = False
        session.add(student)
        session.commit()
        enroll_directly(session, course, student)

        result = get_course_enrollments(session, course.course_id, caller)

        assert result[0].class_id == "CQ.64.CNTT"
        assert result[0].is_active is False

    # sinh viên xem bạn cùng lớp không thấy class_id/is_active
    def test_student_does_not_see_class_id_or_is_active(
        self, session, course, student
    ):
        student.class_id = "CQ.64.CNTT"
        session.add(student)
        session.commit()
        enroll_directly(session, course, student)

        result = get_course_enrollments(session, course.course_id, student)

        assert result[0].class_id is None
        assert result[0].is_active is None


# ============================== CONCURRENT ENROLLMENT ==============================


class TestStudentCountSync:
    """Sĩ số được đếm lại từ bảng enrollment, nên giá trị cache đã lệch tự đúng lại."""

    def test_add_student_recounts_drifted_counter(self, session, course, owner_teacher, student):
        course.total_number_student = 134
        session.add(course)
        session.commit()

        add_student_to_course(student.user_id, course.course_id, session, owner_teacher)

        assert counter_of(session, course) == 1

    def test_delete_student_recounts_drifted_counter(self, session, course, owner_teacher, student):
        enroll_directly(session, course, student)
        course.total_number_student = 134
        session.add(course)
        session.commit()

        delete_student_from_course(student.user_id, course.course_id, session, owner_teacher)

        assert counter_of(session, course) == 0


class TestConcurrentEnrollment:
    """Hai request ghi danh cùng lúc: cả hai qua bước kiểm tra trùng, ràng buộc
    unique (course_id, student_id) chặn request sau. Phải trả 409, không phải 500."""

    def test_add_student_race_returns_conflict_instead_of_500(
        self, session, course, owner_teacher, student, monkeypatch
    ):
        enroll_directly(session, course, student)
        # Giả lập request thứ hai đã đọc trước khi request đầu commit.
        monkeypatch.setattr(enrollment_service, "find_enrollment", lambda *_: None)

        with pytest.raises(ConflictError, match="Sinh viên đã có trong lớp học"):
            add_student_to_course(student.user_id, course.course_id, session, owner_teacher)

        assert len(enrollments_of(session, course.course_id)) == 1
        assert counter_of(session, course) == 1

    def test_add_class_race_returns_conflict_and_keeps_counter(
        self, session, course, owner_teacher, monkeypatch
    ):
        session.add(Class(class_id="CQ.64.CNTT", type="CQ", course_number=64, department="CNTT"))
        students = [make_user(session, f"SV10{i}", Role.STUDENT) for i in range(2)]
        for s in students:
            s.class_id = "CQ.64.CNTT"
            session.add(s)
        session.commit()

        original_add_all = session.add_all

        def add_all_with_concurrent_insert(rows):
            original_add_all(rows)
            # Request khác vừa ghi danh students[0] sau bước đọc existing_ids.
            session.add(Enrollment(course_id=course.course_id, student_id=students[0].user_id))

        monkeypatch.setattr(session, "add_all", add_all_with_concurrent_insert)

        with pytest.raises(ConflictError) as exc:
            add_class_to_course(session, course.course_id, "CQ.64.CNTT", owner_teacher)

        assert exc.value.message == CONCURRENT_CLASS_ENROLLMENT
        assert enrollments_of(session, course.course_id) == []
        assert counter_of(session, course) == 0

    def test_add_class_skips_already_enrolled_students(self, session, course, owner_teacher):
        session.add(Class(class_id="CQ.64.CNTT", type="CQ", course_number=64, department="CNTT"))
        students = [make_user(session, f"SV20{i}", Role.STUDENT) for i in range(2)]
        for s in students:
            s.class_id = "CQ.64.CNTT"
            session.add(s)
        session.commit()
        enroll_directly(session, course, students[0])

        result = add_class_to_course(session, course.course_id, "CQ.64.CNTT", owner_teacher)

        assert (result.added_count, result.skipped_count) == (1, 1)
        assert len(enrollments_of(session, course.course_id)) == 2
        assert counter_of(session, course) == 2
