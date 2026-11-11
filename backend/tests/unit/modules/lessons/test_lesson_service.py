from datetime import UTC, date, datetime, timedelta

import pytest
from sqlmodel import Session, select

from app.core.exceptions import ConflictError, ForbiddenError, InvalidFormatError
from app.core.utils.datetime_utils import VN_TZ, vn_day_end, vn_day_start
from app.modules.submissions.judge0 import service as judge_service
from app.modules.submissions.judge0.schemas import CodeRequest
from app.modules.lessons.schemas import (
    LessonCreateRequest,
    LessonDuplicateRequest,
    LessonReorderRequest,
    LessonUpdateRequest,
)
import app.modules.lessons.service as lesson_service
from app.models.entities import Lesson, Problem, Testcase as CaseModel

pytest_plugins = ("tests.support.fixtures.lesson_fixtures",)


class TestCreateLesson:
    def test_create_lesson_assigns_next_order_and_copies_selected_bank_problem(
        self,
        session: Session,
        lesson_teacher,
        lesson_course,
        lesson_record,
        lesson_bank_problem,
        lesson_testcase_factory,
    ):
        lesson_testcase_factory(lesson_bank_problem, is_sample=True)
        request = LessonCreateRequest(
            lesson_name="  Week 2  ",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            problem_ids=[lesson_bank_problem.problem_id],
        )

        result = lesson_service.create_lesson(
            session, lesson_course.course_id, request, lesson_teacher
        )

        created = session.exec(
            select(Lesson).where(
                Lesson.course_id == lesson_course.course_id, Lesson.lesson_number == 2
            )
        ).one()
        copied_problem = session.exec(
            select(Problem).where(Problem.lesson_id == created.lesson_id)
        ).one()
        assert result.sessions[-1].title == "Week 2"
        assert created.total_number_assignment == 1
        assert copied_problem.problem_id != lesson_bank_problem.problem_id
        assert copied_problem.start_datetime.date() == date(2026, 2, 1)
        assert session.exec(
            select(CaseModel).where(CaseModel.problem_id == copied_problem.problem_id)
        ).all()

    def test_create_lesson_rejects_course_owned_by_another_teacher(
        self, session, lesson_other_teacher, lesson_course
    ):
        request = LessonCreateRequest(
            lesson_name="New lesson",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
        )

        with pytest.raises(ForbiddenError, match="không có quyền tạo buổi học"):
            lesson_service.create_lesson(
                session, lesson_course.course_id, request, lesson_other_teacher
            )


class TestUpdateLesson:
    def test_update_lesson_applies_partial_fields_and_rejects_reversed_resulting_dates(
        self, session, lesson_teacher, lesson_course, lesson_record
    ):
        result = lesson_service.update_lesson(
            session,
            lesson_course.course_id,
            lesson_record.lesson_id,
            LessonUpdateRequest(lesson_name="  Updated  "),
            lesson_teacher,
        )
        assert result.sessions[0].title == "Updated"

        with pytest.raises(InvalidFormatError, match="start_date"):
            lesson_service.update_lesson(
                session,
                lesson_course.course_id,
                lesson_record.lesson_id,
                LessonUpdateRequest(start_date=date(2026, 2, 1)),
                lesson_teacher,
            )
        session.refresh(lesson_record)
        assert lesson_record.start_date == date(2026, 1, 1)


class TestUpdateLessonSyncsProblemSchedule:
    """Ngày của buổi học là nguồn chuẩn: đổi ngày buổi thì ghi đè lịch mọi bài trong buổi
    thành 00:00 ngày bắt đầu -> 23:59:59 ngày kết thúc (giờ VN). Đồng bộ một chiều Lesson -> Problem."""

    @staticmethod
    def _update(session, course, lesson, teacher, **fields):
        return lesson_service.update_lesson(
            session, course.course_id, lesson.lesson_id, LessonUpdateRequest(**fields), teacher
        )

    def test_changing_end_date_overwrites_schedule_of_every_problem_in_lesson(
        self, session, lesson_teacher, lesson_course, lesson_record, lesson_problem_factory
    ):
        # lesson_record: 2026-01-01 -> 2026-01-31
        default_problem = lesson_problem_factory(
            lesson_record,
            start_datetime=vn_day_start(date(2026, 1, 1)),
            end_datetime=vn_day_end(date(2026, 1, 31)),
        )
        custom_time_problem = lesson_problem_factory(
            lesson_record,
            title="Custom time",
            start_datetime=datetime(2026, 1, 5, 9, 0, tzinfo=VN_TZ),
            end_datetime=datetime(2026, 1, 6, 11, 30, tzinfo=VN_TZ),
        )

        self._update(session, lesson_course, lesson_record, lesson_teacher, end_date=date(2026, 2, 15))

        for problem in (default_problem, custom_time_problem):
            session.refresh(problem)
            assert problem.start_datetime == vn_day_start(date(2026, 1, 1))
            assert problem.end_datetime == vn_day_end(date(2026, 2, 15))

    def test_changing_start_date_overwrites_opening_time_of_problems(
        self, session, lesson_teacher, lesson_course, lesson_record, lesson_problem_factory
    ):
        problem = lesson_problem_factory(
            lesson_record,
            start_datetime=vn_day_start(date(2026, 1, 1)),
            end_datetime=vn_day_end(date(2026, 1, 31)),
        )

        self._update(session, lesson_course, lesson_record, lesson_teacher, start_date=date(2026, 1, 10))

        session.refresh(problem)
        assert problem.start_datetime == vn_day_start(date(2026, 1, 10))
        assert problem.end_datetime == vn_day_end(date(2026, 1, 31))

    def test_renaming_lesson_only_keeps_problem_schedule(
        self, session, lesson_teacher, lesson_course, lesson_record, lesson_problem_factory
    ):
        start = datetime(2026, 1, 5, 9, 0, tzinfo=VN_TZ)
        end = datetime(2026, 1, 6, 11, 30, tzinfo=VN_TZ)
        problem = lesson_problem_factory(lesson_record, start_datetime=start, end_datetime=end)

        self._update(session, lesson_course, lesson_record, lesson_teacher, lesson_name="Renamed")

        session.refresh(problem)
        assert (problem.start_datetime, problem.end_datetime) == (start, end)

    def test_resending_same_dates_keeps_problem_schedule(
        self, session, lesson_teacher, lesson_course, lesson_record, lesson_problem_factory
    ):
        """FE thường gửi lại nguyên trạng cả form: ngày không đổi thì không được ghi đè lịch bài."""
        start = datetime(2026, 1, 5, 9, 0, tzinfo=VN_TZ)
        end = datetime(2026, 1, 6, 11, 30, tzinfo=VN_TZ)
        problem = lesson_problem_factory(lesson_record, start_datetime=start, end_datetime=end)

        self._update(
            session, lesson_course, lesson_record, lesson_teacher,
            lesson_name="Same dates", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31),
        )

        session.refresh(problem)
        assert (problem.start_datetime, problem.end_datetime) == (start, end)

    def test_problems_outside_the_lesson_are_not_touched(
        self,
        session,
        lesson_teacher,
        lesson_course,
        lesson_record,
        lesson_factory,
        lesson_problem_factory,
        lesson_bank_problem,
    ):
        sibling_lesson = lesson_factory(lesson_course, lesson_name="Lesson 2", lesson_number=2)
        start = datetime(2026, 1, 5, 9, 0, tzinfo=VN_TZ)
        end = datetime(2026, 1, 6, 11, 30, tzinfo=VN_TZ)
        sibling_problem = lesson_problem_factory(sibling_lesson, start_datetime=start, end_datetime=end)
        bank_start, bank_end = lesson_bank_problem.start_datetime, lesson_bank_problem.end_datetime
        lesson_problem_factory(lesson_record)

        self._update(session, lesson_course, lesson_record, lesson_teacher, end_date=date(2026, 2, 15))

        session.refresh(sibling_problem)
        session.refresh(lesson_bank_problem)
        assert (sibling_problem.start_datetime, sibling_problem.end_datetime) == (start, end)
        assert (lesson_bank_problem.start_datetime, lesson_bank_problem.end_datetime) == (
            bank_start,
            bank_end,
        )

    def test_reversed_dates_are_rejected_without_touching_problem_schedule(
        self, session, lesson_teacher, lesson_course, lesson_record, lesson_problem_factory
    ):
        start = datetime(2026, 1, 5, 9, 0, tzinfo=VN_TZ)
        end = datetime(2026, 1, 6, 11, 30, tzinfo=VN_TZ)
        problem = lesson_problem_factory(lesson_record, start_datetime=start, end_datetime=end)

        with pytest.raises(InvalidFormatError, match="start_date"):
            self._update(session, lesson_course, lesson_record, lesson_teacher, start_date=date(2026, 2, 1))

        # Kiểm tra trên object trong session (không refresh): bắt cả trường hợp đã gán lịch
        # cho bài rồi mới validate ngày của buổi.
        assert (problem.start_datetime, problem.end_datetime) == (start, end)

    def test_lesson_without_problems_updates_dates_without_error(
        self, session, lesson_teacher, lesson_course, lesson_record
    ):
        result = self._update(
            session, lesson_course, lesson_record, lesson_teacher, end_date=date(2026, 2, 15)
        )

        session.refresh(lesson_record)
        assert lesson_record.end_date == date(2026, 2, 15)
        assert result.sessions[0].problems == []

    def test_changing_dates_and_attaching_problems_in_one_request_aligns_all_problems(
        self,
        session,
        lesson_teacher,
        lesson_course,
        lesson_record,
        lesson_problem_factory,
        lesson_bank_problem,
        lesson_testcase_factory,
    ):
        """FE lưu form buổi học gửi ngày kèm problem_ids trong cùng một request."""
        existing = lesson_problem_factory(
            lesson_record,
            start_datetime=datetime(2026, 1, 5, 9, 0, tzinfo=VN_TZ),
            end_datetime=datetime(2026, 1, 6, 11, 30, tzinfo=VN_TZ),
        )
        lesson_testcase_factory(lesson_bank_problem)

        self._update(
            session, lesson_course, lesson_record, lesson_teacher,
            start_date=date(2026, 2, 1), end_date=date(2026, 2, 15),
            problem_ids=[lesson_bank_problem.problem_id],
        )

        problems = session.exec(
            select(Problem).where(Problem.lesson_id == lesson_record.lesson_id)
        ).all()
        assert existing in problems and len(problems) == 2
        for problem in problems:
            session.refresh(problem)
            assert problem.start_datetime == vn_day_start(date(2026, 2, 1))
            assert problem.end_datetime == vn_day_end(date(2026, 2, 15))

    def test_problem_with_submissions_still_gets_new_deadline(
        self,
        session,
        lesson_teacher,
        lesson_student,
        lesson_course,
        lesson_record,
        lesson_problem_factory,
        lesson_submission_factory,
    ):
        problem = lesson_problem_factory(lesson_record)
        lesson_submission_factory(problem, lesson_student)

        self._update(session, lesson_course, lesson_record, lesson_teacher, end_date=date(2026, 2, 15))

        session.refresh(problem)
        assert problem.end_datetime == vn_day_end(date(2026, 2, 15))


class TestLessonDeadlineAppliesToSubmission:
    """Hồi quy end-to-end ở tầng service: hạn mới của buổi phải có hiệu lực khi sinh viên nộp bài."""

    @pytest.fixture(autouse=True)
    def frozen_today(self, monkeypatch):
        """Cố định "bây giờ" lúc 12:00 giờ VN để test không flaky khi chạy vắt qua nửa đêm."""
        today = date(2026, 5, 15)
        noon_utc = datetime(2026, 5, 15, 12, 0, tzinfo=VN_TZ).astimezone(UTC)
        monkeypatch.setattr(judge_service, "now_utc", lambda: noon_utc)
        return today

    @staticmethod
    def _open_lesson_with_problem(lesson_factory, lesson_problem_factory, course, start_day, end_day):
        lesson = lesson_factory(course, start_date=start_day, end_date=end_day)
        problem = lesson_problem_factory(
            lesson,
            start_datetime=vn_day_start(start_day),
            end_datetime=vn_day_end(end_day),
            total_number_testcase=0,  # dừng submit ở bước "chưa có testcase", không gọi Judge0
        )
        return lesson, problem

    @staticmethod
    def _submit(session, course, lesson, problem, student):
        return judge_service.submit(
            session,
            course.course_id,
            lesson.lesson_id,
            problem.problem_id,
            CodeRequest(language="python", code="class Solution: pass"),
            student,
        )

    def test_moving_end_date_to_the_past_closes_submission(
        self,
        session,
        lesson_teacher,
        lesson_student,
        lesson_course,
        lesson_factory,
        lesson_problem_factory,
        lesson_enrollment_factory,
        frozen_today,
    ):
        today = frozen_today
        lesson_enrollment_factory(lesson_course, lesson_student)
        lesson, problem = self._open_lesson_with_problem(
            lesson_factory, lesson_problem_factory, lesson_course,
            today - timedelta(days=10), today + timedelta(days=10),
        )

        lesson_service.update_lesson(
            session, lesson_course.course_id, lesson.lesson_id,
            LessonUpdateRequest(end_date=today - timedelta(days=1)), lesson_teacher,
        )

        with pytest.raises(judge_service.SubmissionClosedError, match="hết hạn"):
            self._submit(session, lesson_course, lesson, problem, lesson_student)

    @pytest.mark.parametrize("new_end_offset_days", [0, 5], ids=["until-end-of-today", "future"])
    def test_extending_end_date_reopens_submission(
        self,
        session,
        lesson_teacher,
        lesson_student,
        lesson_course,
        lesson_factory,
        lesson_problem_factory,
        lesson_enrollment_factory,
        frozen_today,
        new_end_offset_days,
    ):
        today = frozen_today
        lesson_enrollment_factory(lesson_course, lesson_student)
        lesson, problem = self._open_lesson_with_problem(
            lesson_factory, lesson_problem_factory, lesson_course,
            today - timedelta(days=10), today - timedelta(days=2),
        )

        lesson_service.update_lesson(
            session, lesson_course.course_id, lesson.lesson_id,
            LessonUpdateRequest(end_date=today + timedelta(days=new_end_offset_days)), lesson_teacher,
        )

        # Qua được bước kiểm tra hạn -> dừng ở bước kế tiếp (bài chưa có testcase).
        with pytest.raises(ConflictError, match="chưa có testcase"):
            self._submit(session, lesson_course, lesson, problem, lesson_student)


class TestAddProblemsToLesson:
    def test_add_problems_to_lesson_clones_bank_problem_once_and_updates_count(
        self,
        session,
        lesson_teacher,
        lesson_course,
        lesson_record,
        lesson_bank_problem,
        lesson_testcase_factory,
    ):
        lesson_testcase_factory(lesson_bank_problem)

        lesson_service.add_problems_to_lesson(
            session,
            lesson_course.course_id,
            lesson_record.lesson_id,
            [lesson_bank_problem.problem_id, lesson_bank_problem.problem_id],
            lesson_teacher,
        )

        copied = session.exec(
            select(Problem).where(Problem.lesson_id == lesson_record.lesson_id)
        ).all()
        assert len(copied) == 1
        assert lesson_record.total_number_assignment == 1


class TestDeleteLesson:
    def test_delete_lesson_rejects_lesson_that_still_contains_problems(
        self, session, lesson_teacher, lesson_course, lesson_record, lesson_problem
    ):
        with pytest.raises(ConflictError, match="đã có bài tập"):
            lesson_service.delete_lesson(
                session,
                lesson_course.course_id,
                lesson_record.lesson_id,
                lesson_teacher,
            )
        assert session.get(Lesson, lesson_record.lesson_id) is not None

    def test_delete_lesson_removes_empty_lesson(
        self, session, lesson_teacher, lesson_course, lesson_record
    ):
        lesson_service.delete_lesson(
            session, lesson_course.course_id, lesson_record.lesson_id, lesson_teacher
        )
        assert session.get(Lesson, lesson_record.lesson_id) is None


class TestReorderLessons:
    def test_reorder_lessons_assigns_contiguous_positions_and_rejects_invalid_order(
        self,
        session,
        lesson_teacher,
        lesson_course,
        lesson_factory,
        lesson_record,
    ):
        second = lesson_factory(lesson_course, lesson_name="Lesson 2", lesson_number=2)
        lesson_service.reorder_lessons(
            session,
            lesson_course.course_id,
            LessonReorderRequest(order=[second.lesson_id, lesson_record.lesson_id]),
            lesson_teacher,
        )
        session.refresh(lesson_record)
        session.refresh(second)
        assert (second.lesson_number, lesson_record.lesson_number) == (1, 2)

        with pytest.raises(InvalidFormatError, match="không hợp lệ"):
            lesson_service.reorder_lessons(
                session,
                lesson_course.course_id,
                LessonReorderRequest(
                    order=[lesson_record.lesson_id, lesson_record.lesson_id]
                ),
                lesson_teacher,
            )


class TestDuplicateLesson:
    def test_duplicate_lesson_copies_problem_and_testcases_to_owned_target_course(
        self,
        session,
        lesson_teacher,
        lesson_course,
        lesson_course_factory,
        lesson_record,
        lesson_problem,
        lesson_testcase_factory,
    ):
        target_course = lesson_course_factory(lesson_teacher, "CS303")
        lesson_testcase_factory(lesson_problem, is_sample=True)

        lesson_service.duplicate_lesson(
            session,
            lesson_course.course_id,
            lesson_record.lesson_id,
            LessonDuplicateRequest(
                new_start_date=date(2026, 3, 1),
                new_end_date=date(2026, 3, 31),
                target_course_id=target_course.course_id,
            ),
            lesson_teacher,
        )

        duplicate = session.exec(
            select(Lesson).where(Lesson.course_id == target_course.course_id)
        ).one()
        copied = session.exec(
            select(Problem).where(Problem.lesson_id == duplicate.lesson_id)
        ).one()
        assert duplicate.lesson_number == 1
        assert copied.problem_id != lesson_problem.problem_id
        assert copied.start_datetime.date() == date(2026, 3, 1)
        assert (
            session.exec(
                select(CaseModel).where(CaseModel.problem_id == copied.problem_id)
            )
            .one()
            .is_sample
        )

    def test_duplicate_lesson_rejects_target_course_not_owned_by_teacher(
        self, session, lesson_teacher, lesson_course, lesson_other_course, lesson_record
    ):
        request = LessonDuplicateRequest(
            new_start_date=date(2026, 3, 1),
            new_end_date=date(2026, 3, 31),
            target_course_id=lesson_other_course.course_id,
        )
        with pytest.raises(ForbiddenError, match="lớp đích"):
            lesson_service.duplicate_lesson(
                session,
                lesson_course.course_id,
                lesson_record.lesson_id,
                request,
                lesson_teacher,
            )


class TestGetLessonDetail:
    def test_student_lesson_detail_hides_future_problems_and_hidden_testcases(
        self,
        session,
        lesson_student,
        lesson_course,
        lesson_record,
        lesson_enrollment_factory,
        lesson_problem_factory,
        lesson_testcase_factory,
    ):
        from datetime import datetime, timedelta
        from app.core.utils.datetime_utils import VN_TZ

        lesson_enrollment_factory(lesson_course, lesson_student)
        open_problem = lesson_problem_factory(lesson_record)
        future_problem = lesson_problem_factory(
            lesson_record,
            title="Future",
            start_datetime=datetime.now(VN_TZ) + timedelta(days=30),
        )
        lesson_testcase_factory(open_problem, is_sample=True)
        lesson_testcase_factory(open_problem, input_value="[1]", is_sample=False)
        lesson_testcase_factory(future_problem, is_sample=True)

        detail = lesson_service.get_lesson_detail(
            session, lesson_course.course_id, lesson_record.lesson_id, lesson_student
        )

        assert [exercise.title for exercise in detail.exercises] == ["Two Sum"]
        assert len(detail.exercises[0].testcases) == 1
        assert detail.total_students is None
        assert detail.stats is None

    def test_teacher_lesson_detail_reports_enrollment_and_submission_statistics(
        self,
        session,
        lesson_teacher,
        lesson_student,
        lesson_course,
        lesson_record,
        lesson_enrollment_factory,
        lesson_problem_factory,
        lesson_testcase_factory,
        lesson_submission_factory,
    ):
        lesson_enrollment_factory(lesson_course, lesson_student)
        problem = lesson_problem_factory(lesson_record, total_number_testcase=2)
        lesson_testcase_factory(problem, is_sample=True)
        lesson_testcase_factory(problem, input_value="[2]", is_sample=False)
        lesson_submission_factory(
            problem, lesson_student, status="accepted", passed_count=1
        )

        detail = lesson_service.get_lesson_detail(
            session, lesson_course.course_id, lesson_record.lesson_id, lesson_teacher
        )

        assert detail.total_students == 1
        assert detail.submitted_students == 1
        assert detail.stats.submission_rate == 100
        assert detail.exercises[0].submitted_count == 1
        assert detail.stats.avg_score == 5

    def test_lesson_stats_ignore_submissions_from_unenrolled_students(
        self,
        session,
        lesson_user_factory,
        lesson_student,
        lesson_teacher,
        lesson_course,
        lesson_record,
        lesson_problem,
        lesson_enrollment_factory,
        lesson_submission_factory,
    ):
        former_student = lesson_user_factory("SV002", lesson_student.role_id)
        lesson_enrollment_factory(lesson_course, lesson_student)
        lesson_submission_factory(
            lesson_problem, former_student, status="accepted", passed_count=2
        )

        detail = lesson_service.get_lesson_detail(
            session, lesson_course.course_id, lesson_record.lesson_id, lesson_teacher
        )

        assert detail.total_students == 1
        assert detail.submitted_students == 0
        assert detail.stats.completed_students == 0
        assert detail.stats.avg_score == 0
        assert detail.exercises[0].submitted_count == 0


class TestLessonDetailProblemSchedule:
    def test_exercises_expose_their_own_schedule(
        self,
        session,
        lesson_teacher,
        lesson_course,
        lesson_record,
        lesson_problem_factory,
    ):
        """Thiếu 2 mốc này thì form soạn bài rơi về mốc của buổi học và ghi đè lịch thật."""
        from datetime import datetime

        from app.core.utils.datetime_utils import VN_TZ

        lesson_problem_factory(
            lesson_record,
            start_datetime=datetime(2026, 10, 5, 9, 0, tzinfo=VN_TZ),
            end_datetime=datetime(2026, 10, 6, 11, 30, tzinfo=VN_TZ),
        )

        detail = lesson_service.get_lesson_detail(
            session, lesson_course.course_id, lesson_record.lesson_id, lesson_teacher
        )

        exercise = detail.exercises[0]
        assert exercise.start_datetime == datetime(2026, 10, 5, 9, 0, tzinfo=VN_TZ)
        assert exercise.end_datetime == datetime(2026, 10, 6, 11, 30, tzinfo=VN_TZ)
