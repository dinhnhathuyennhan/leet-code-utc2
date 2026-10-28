from datetime import date

import pytest
from sqlmodel import Session, select

from app.core.exceptions import ConflictError, ForbiddenError, InvalidFormatError
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
