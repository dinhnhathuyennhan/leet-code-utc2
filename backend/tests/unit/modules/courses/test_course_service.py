"""Unit tests for course service behavior."""

from datetime import datetime, timedelta

import pytest

from app.core.utils.datetime_utils import VN_TZ
from app.core.exceptions import (
    ConflictError,
    EmptyFieldError,
    ForbiddenError,
    InvalidFormatError,
    NotFoundError,
)
from app.modules.courses.schemas import CreateCourseRequest, UpdateCourseRequest
from app.modules.courses.service import (
    create_course,
    get_course,
    get_courses,
    get_course_terms,
    update_course,
)
from app.modules.courses.view import build_course_response
from app.models import Course

pytest_plugins = (
    "tests.support.fixtures.user_fixtures",
    "tests.support.fixtures.course_fixtures",
)
from tests.support.fixtures.course_fixtures import make_course
from tests.support.fixtures.enrollment_fixtures import enroll_directly
from tests.support.fixtures.user_fixtures import make_user, vn

from tests.support.fixtures.builders import make_enrollment, make_lesson, make_problem


# ============================== CREATE / UPDATE COURSE ==============================

VALID_START = vn(2026, 9, 7)
VALID_END = vn(2026, 12, 27)


def _make_create_request(
    course_id: str = "CS101",
    course_name: str = "Nhập môn lập trình",
    term: str = "HK1 2026-2027",
    start_date: datetime = VALID_START,
    end_date: datetime = VALID_END,
) -> CreateCourseRequest:
    return CreateCourseRequest(
        course_id=course_id,
        course_name=course_name,
        term=term,
        start_date=start_date,
        end_date=end_date,
    )


class TestCreateCourse:
    # Teacher tạo lớp — created_by và total_number_student do server set
    def test_teacher_creates_course_with_server_side_fields(
        self, session, owner_teacher
    ):
        result = create_course(_make_create_request(), session, owner_teacher)

        assert result.course_id == "CS101"
        assert result.course_name == "Nhập môn lập trình"
        assert result.created_by == owner_teacher.user_id
        assert result.total_number_student == 0
        assert result.avt_link is None

        saved = session.get(Course, "CS101")
        assert saved is not None
        assert saved.created_by == owner_teacher.user_id

    # Admin tạo lớp — cũng được, không phụ thuộc created_by
    def test_admin_creates_course(self, session, admin):
        result = create_course(_make_create_request(course_id="CS202"), session, admin)

        assert result.created_by == admin.user_id
        assert result.total_number_student == 0

    # Trùng course_id → 409
    def test_raises_conflict_when_course_id_already_exists(
        self, session, owner_teacher, course
    ):
        with pytest.raises(ConflictError, match="Mã lớp học đã tồn tại"):
            create_course(_make_create_request(), session, owner_teacher)

    # start_date phải trước end_date — validation tại schema layer
    def test_raises_invalid_format_when_start_after_end(self, session, owner_teacher):
        with pytest.raises(InvalidFormatError, match="start_date phải trước end_date"):
            CreateCourseRequest(
                course_id="CS303",
                course_name="Sai ngày",
                term="HK1 2026-2027",
                start_date=vn(2026, 12, 27),
                end_date=vn(2026, 9, 7),
            )

    # start_date bằng end_date cũng reject — validation tại schema layer
    def test_raises_invalid_format_when_start_equals_end(self, session, owner_teacher):
        same_day = vn(2026, 9, 7)
        with pytest.raises(InvalidFormatError, match="start_date phải trước end_date"):
            CreateCourseRequest(
                course_id="CS304",
                course_name="Bằng ngày",
                term="HK1 2026-2027",
                start_date=same_day,
                end_date=same_day,
            )

    # field bắt buộc bị rỗng → validation tại schema layer
    def test_raises_empty_field_when_course_name_blank(self, session, owner_teacher):
        with pytest.raises(EmptyFieldError, match="course_name"):
            CreateCourseRequest(
                course_id="CS305",
                course_name="   ",
                term="HK1 2026-2027",
                start_date=VALID_START,
                end_date=VALID_END,
            )

    # course_id dài quá 50 ký tự → 422 (giới hạn cột DB)
    def test_raises_error_when_course_id_too_long(self, session, owner_teacher):
        from pydantic import ValidationError

        too_long = "C" * 51
        # max_length=50 là constraint của pydantic → raise ValidationError.
        # Trên FastAPI layer sẽ được convert thành 422 response.
        with pytest.raises(ValidationError):
            CreateCourseRequest(
                course_id=too_long,
                course_name="OK",
                term="HK1",
                start_date=VALID_START,
                end_date=VALID_END,
            )

    # avt_link dài quá 2048 ký tự → 422 (giới hạn cột DB)
    def test_raises_error_when_avt_link_too_long(self, session, owner_teacher):
        from pydantic import ValidationError

        too_long = "https://x.com/" + ("a" * 2048)
        with pytest.raises(ValidationError):
            CreateCourseRequest(
                course_id="CS_OK",
                course_name="OK",
                term="HK1",
                start_date=VALID_START,
                end_date=VALID_END,
                avt_link=too_long,
            )

    # Gửi null cho field bắt buộc → 422 EMPTY_FIELD (trước kia raise message
    # chung tiếng Anh của pydantic)
    def test_raises_empty_field_when_required_field_missing(
        self, session, owner_teacher
    ):
        # Pydantic v2 với Field(...) coi None là input không hợp lệ và raise
        # ValidationError. Trên FastAPI layer sẽ được convert thành 422.
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CreateCourseRequest(
                course_id="CS_OK",
                course_name=None,  # type: ignore[arg-type]
                term="HK1",
                start_date=VALID_START,
                end_date=VALID_END,
            )


class TestUpdateCourse:
    # Teacher chủ lớp cập nhật 1 vài field — các field không gửi phải giữ nguyên
    def test_owner_teacher_updates_only_sent_fields(
        self, session, course, owner_teacher
    ):
        update = UpdateCourseRequest(course_name="Tên mới", term="HK2 2026-2027")

        result = update_course(course.course_id, update, session, owner_teacher)

        assert result.course_name == "Tên mới"
        assert result.term == "HK2 2026-2027"
        # course_id, created_by, total_number_student, start/end_date phải KHÔNG đổi
        assert result.course_id == course.course_id
        assert result.created_by == owner_teacher.user_id
        assert result.total_number_student == course.total_number_student
        assert result.start_date == course.start_date
        assert result.end_date == course.end_date

    # Admin cập nhật lớp của teacher khác — được phép
    def test_admin_can_update_any_course(self, session, course, admin):
        update = UpdateCourseRequest(avt_link="https://cdn/avt.png")

        result = update_course(course.course_id, update, session, admin)

        assert result.avt_link == "https://cdn/avt.png"

    # Teacher không phải chủ lớp → 403
    def test_raises_forbidden_when_teacher_does_not_own_course(
        self, session, course, other_teacher
    ):
        update = UpdateCourseRequest(course_name="Hack")

        with pytest.raises(
            ForbiddenError, match="Bạn không có quyền thực hiện hành động này"
        ):
            update_course(course.course_id, update, session, other_teacher)

        # dữ liệu không được đổi
        assert course.course_name != "Hack"

    # course_id không tồn tại → 404
    def test_raises_not_found_when_course_id_missing(self, session, owner_teacher):
        update = UpdateCourseRequest(course_name="X")

        with pytest.raises(NotFoundError, match="Không tìm thấy lớp học"):
            update_course("KHONG_CO", update, session, owner_teacher)

    # Nếu đổi cả start_date và end_date mà sai thứ tự → 422
    def test_raises_invalid_format_when_new_date_range_invalid(
        self, session, course, owner_teacher
    ):
        with pytest.raises(InvalidFormatError, match="start_date phải trước end_date"):
            UpdateCourseRequest(
                start_date=vn(2026, 12, 27),
                end_date=vn(2026, 9, 7),
            )

    # Có thể đổi end_date một mình nếu vẫn sau start_date hiện tại
    def test_can_update_only_end_date(self, session, course, owner_teacher):
        update = UpdateCourseRequest(end_date=vn(2027, 1, 15))

        result = update_course(course.course_id, update, session, owner_teacher)

        assert result.end_date == vn(2027, 1, 15)
        assert result.start_date == course.start_date

    # Truyền chuỗi rỗng cho field optional → 422 EmptyFieldError
    def test_raises_empty_field_when_optional_str_blank(
        self, session, course, owner_teacher
    ):
        with pytest.raises(EmptyFieldError, match="course_name"):
            UpdateCourseRequest(course_name="   ")

    # PATCH body rỗng → no-op, trả về 200 với dữ liệu hiện tại
    def test_empty_body_is_noop(self, session, course, owner_teacher):
        result = update_course(
            course.course_id, UpdateCourseRequest(), session, owner_teacher
        )

        assert result.course_id == course.course_id
        assert result.course_name == course.course_name

    # PATCH: chỉ gửi start_date mà end_date hiện tại lại trước/sau → 422
    def test_raises_invalid_format_when_only_start_date_collides_with_db_end(
        self, session, course, owner_teacher
    ):
        # course hiện tại có end_date = 2026-12-27.
        # Gửi start_date mới = 2027-01-01 (sau end_date DB) → 422.
        with pytest.raises(InvalidFormatError, match="start_date phải trước end_date"):
            update_course(
                course.course_id,
                UpdateCourseRequest(start_date=vn(2027, 1, 1)),
                session,
                owner_teacher,
            )

    # PATCH: chỉ gửi end_date mà start_date hiện tại lại sau → 422
    def test_raises_invalid_format_when_only_end_date_collides_with_db_start(
        self, session, course, owner_teacher
    ):
        # course hiện tại có start_date = 2026-09-07.
        # Gửi end_date mới = 2026-08-01 (trước start_date DB) → 422.
        with pytest.raises(InvalidFormatError, match="start_date phải trước end_date"):
            update_course(
                course.course_id,
                UpdateCourseRequest(end_date=vn(2026, 8, 1)),
                session,
                owner_teacher,
            )

    # PATCH: gửi field=null phải được bỏ qua, không ghi đè cột NOT NULL → 200
    def test_null_field_is_ignored_not_overwritten(
        self, session, course, owner_teacher
    ):
        original_name = course.course_name

        result = update_course(
            course.course_id,
            UpdateCourseRequest(course_name=None, term="HK Mới"),
            session,
            owner_teacher,
        )

        assert result.course_name == original_name  # không bị ghi đè thành None
        assert result.term == "HK Mới"


# ============================== TIMEZONE ==============================
# Quy ước: input datetime bắt buộc kèm offset, DB lưu UTC, response trả giờ VN (+07:00).


class TestCourseTimezone:
    def test_create_accepts_vietnam_local_datetime_with_offset(self):
        request = CreateCourseRequest(
            course_id="CS401",
            course_name="Giờ Việt Nam",
            term="HK1 2026-2027",
            start_date=datetime(2026, 9, 7, tzinfo=VN_TZ),
            end_date=datetime(2026, 12, 27, tzinfo=VN_TZ),
        )
        assert request.start_date == datetime(2026, 9, 7, tzinfo=VN_TZ)

    def test_create_rejects_datetime_without_offset(self):
        with pytest.raises(InvalidFormatError, match=r"start_date.*phải kèm múi giờ"):
            CreateCourseRequest(
                course_id="CS402",
                course_name="Thiếu offset",
                term="HK1 2026-2027",
                start_date=datetime(2026, 9, 7),
                end_date=datetime(2026, 12, 27),
            )

    def test_update_returns_vietnam_local_time_after_utc_storage(self, session, course, owner_teacher):
        result = update_course(
            course.course_id,
            UpdateCourseRequest(start_date=datetime(2026, 10, 1, 7, 0, tzinfo=VN_TZ)),
            session,
            owner_teacher,
        )
        assert result.start_date == datetime(2026, 10, 1, 7, 0, tzinfo=VN_TZ)
        assert result.start_date.tzinfo is not None
        assert result.end_date == course.end_date

    def test_update_only_end_date_accepts_offset(self):
        request = UpdateCourseRequest(
            end_date=datetime.fromisoformat("2027-01-15T00:00:00+07:00")
        )
        assert request.end_date == datetime(2027, 1, 15, tzinfo=VN_TZ)


# ============================== GET COURSES ==============================


class TestGetCourses:

    # admin thấy tất cả lớp, kể cả lớp của teacher khác
    def test_admin_sees_all_courses(
        self, session, course, admin, other_teacher
    ):
        make_course(session, "CS102", other_teacher)

        result = get_courses(session, admin)

        assert [c.course_id for c in result] == ["CS101", "CS102"]

    # role lạ (không phải 1/2/3) → 403, không được lọt vào nhánh nào
    def test_raises_forbidden_for_unknown_role(self, session, course):
        stranger = make_user(session, "XX001", 99)

        with pytest.raises(ForbiddenError):
            get_courses(session, stranger)

    # teacher chỉ thấy lớp mình tạo, không thấy lớp của teacher khác
    def test_teacher_only_sees_own_courses(
        self, session, course, owner_teacher, other_teacher
    ):
        make_course(session, "CS102", other_teacher)

        result = get_courses(session, owner_teacher)

        assert [c.course_id for c in result] == ["CS101"]

    # teacher chưa tạo lớp nào trả []
    def test_teacher_without_courses_gets_empty_list(
        self, session, course, other_teacher
    ):
        result = get_courses(session, other_teacher)

        assert result == []

    # student chỉ thấy lớp mình có Enrollment
    def test_student_only_sees_enrolled_courses(
        self, session, course, student, other_teacher
    ):
        enroll_directly(session, course, student)
        make_course(session, "CS102", other_teacher)

        result = get_courses(session, student)

        assert [c.course_id for c in result] == ["CS101"]

    # student chưa được thêm vào lớp nào trả []
    def test_student_without_enrollment_gets_empty_list(
        self, session, course, student
    ):
        result = get_courses(session, student)

        assert result == []

    # admin khi hệ thống chưa có lớp nào trả []
    def test_admin_gets_empty_list_when_no_courses(self, session, admin):
        result = get_courses(session, admin)

        assert result == []

    def test_course_terms_are_scoped_and_sorted(
        self, session, course, owner_teacher, other_teacher
    ):
        make_course(session, "CS102", owner_teacher)
        make_course(session, "CS201", other_teacher)
        session.get(Course, "CS102").term = "HK2 2025-2026"
        session.commit()

        result = get_course_terms(session, owner_teacher)

        assert result.academic_years == ["2026-2027", "2025-2026"]
        assert result.semesters == [1, 2]


class TestGetCourse:

    # teacher chủ lớp xem được chi tiết
    def test_owner_teacher_can_get_course(
        self, session, course, owner_teacher
    ):
        result = get_course(session, course.course_id, owner_teacher)

        assert result.course_id == "CS101"
        assert result.created_by == owner_teacher.user_id

    # admin xem được lớp bất kỳ
    def test_admin_can_get_any_course(self, session, course, admin):
        result = get_course(session, course.course_id, admin)

        assert result.course_id == course.course_id

    # student đã được thêm vào lớp xem được chi tiết
    def test_enrolled_student_can_get_course(self, session, course, student):
        enroll_directly(session, course, student)

        result = get_course(session, course.course_id, student)

        assert result.course_id == course.course_id
        assert result.total_number_student == 1

    # teacher không phải chủ lớp nhận 403
    def test_raises_forbidden_when_teacher_does_not_own_course(
        self, session, course, other_teacher
    ):
        with pytest.raises(ForbiddenError, match="Bạn không có quyền xem lớp học này"):
            get_course(session, course.course_id, other_teacher)

    # student chưa được thêm vào lớp nhận 403
    def test_raises_forbidden_when_student_not_in_course(
        self, session, course, student
    ):
        with pytest.raises(ForbiddenError, match="Bạn không có quyền xem lớp học này"):
            get_course(session, course.course_id, student)

    # role lạ (không phải 1/2/3) nhận 403
    def test_raises_forbidden_for_unknown_role(self, session, course):
        stranger = make_user(session, "XX001", 99)

        with pytest.raises(ForbiddenError, match="Bạn không có quyền xem lớp học này"):
            get_course(session, course.course_id, stranger)

    # course_id không tồn tại nhận 404
    def test_raises_not_found_when_course_id_does_not_exist(self, session, admin):
        with pytest.raises(NotFoundError, match="Không tìm thấy lớp học"):
            get_course(session, "KHONG_CO", admin)


class TestStudentCourseGrades:
    def test_student_course_grades_omit_problems_that_have_not_opened(
        self, session, course, student
    ):
        lesson = make_lesson(session, course)
        future_problem = make_problem(
            session,
            lesson,
            start_datetime=datetime.now(VN_TZ)
            + timedelta(days=2),
        )
        make_enrollment(session, course, student)

        response = build_course_response(
            course, session, only_student_id=student.user_id
        )

        assert response.sessions[0].problems == []
        assert response.grades[0].session_scores[str(lesson.lesson_id)] == []
        assert future_problem.problem_id is not None
