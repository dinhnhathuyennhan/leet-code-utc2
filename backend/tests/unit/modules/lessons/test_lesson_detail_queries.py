"""get_lesson_detail: thống kê nộp bài gộp trong một truy vấn trên bảng submission."""

import pytest
from sqlmodel import Session

import app.modules.lessons.service as lesson_service
from app.modules.courses.view import build_course_response
from tests.support.query_counter import count_queries

pytest_plugins = ("tests.support.fixtures.lesson_fixtures",)


def _submission_reads(queries) -> list[str]:
    return [s for s in queries.statements if "FROM submission" in s]


@pytest.fixture
def stats_setup(
    session: Session,
    lesson_user_factory,
    lesson_course,
    lesson_record,
    lesson_problem_factory,
    lesson_submission_factory,
    lesson_enrollment_factory,
):
    """Hai bài (4 và 2 testcase), hai sinh viên trong lớp, một sinh viên ngoài lớp."""
    p1 = lesson_problem_factory(lesson_record, title="P1", total_number_testcase=4)
    p2 = lesson_problem_factory(lesson_record, title="P2", total_number_testcase=2)
    s1 = lesson_user_factory("6451000001", 3)
    s2 = lesson_user_factory("6451000002", 3)
    outsider = lesson_user_factory("6451000003", 3)
    lesson_enrollment_factory(lesson_course, s1)
    lesson_enrollment_factory(lesson_course, s2)
    # s1 nộp 3 lần P1 (tốt nhất 2) và 2 lần P2 (tốt nhất 1); s2 nộp 1 lần P1 (tốt nhất 4)
    for passed in (0, 2, 1):
        lesson_submission_factory(p1, s1, passed_count=passed)
    for passed in (1, 0):
        lesson_submission_factory(p2, s1, passed_count=passed)
    lesson_submission_factory(p1, s2, passed_count=4)
    # sinh viên ngoài lớp không được tính
    lesson_submission_factory(p1, outsider, passed_count=4)
    lesson_submission_factory(p2, outsider, passed_count=2)
    session.commit()
    return p1, p2, s1, s2


class TestLessonDetailStats:
    def test_teacher_stats_count_attempts_of_enrolled_students_only(
        self, engine, session, lesson_teacher, lesson_course, lesson_record, stats_setup
    ):
        p1, p2, *_ = stats_setup
        p1_id, p2_id = p1.problem_id, p2.problem_id
        course_id, lesson_id = lesson_course.course_id, lesson_record.lesson_id
        session.refresh(lesson_teacher)

        with count_queries(engine) as queries:
            detail = lesson_service.get_lesson_detail(session, course_id, lesson_id, lesson_teacher)

        by_id = {e.id: e for e in detail.exercises}
        assert by_id[p1_id].submitted_count == 4  # 3 của s1 + 1 của s2
        assert by_id[p2_id].submitted_count == 2
        assert detail.submitted_students == 2
        assert detail.total_students == 2
        # điểm tốt nhất: s1/P1 2/4 -> 5.0, s1/P2 1/2 -> 5.0, s2/P1 4/4 -> 10.0 => trung bình 6.7
        assert detail.stats.avg_score == 6.7
        assert detail.stats.submission_rate == 100.0
        assert detail.alert.missing_students == 0
        assert len(_submission_reads(queries)) == 1

    def test_student_viewer_gets_no_stats_and_no_submission_query(
        self, engine, session, lesson_course, lesson_record, stats_setup
    ):
        _, _, s1, _ = stats_setup
        session.refresh(s1)
        course_id, lesson_id = lesson_course.course_id, lesson_record.lesson_id

        with count_queries(engine) as queries:
            detail = lesson_service.get_lesson_detail(session, course_id, lesson_id, s1)

        assert detail.stats is None
        assert detail.submitted_students is None
        assert detail.total_students is None
        assert all(e.submitted_count is None for e in detail.exercises)
        assert _submission_reads(queries) == []

    def test_lesson_without_problems(
        self, engine, session, lesson_teacher, lesson_course, lesson_record,
        lesson_user_factory, lesson_enrollment_factory,
    ):
        lesson_enrollment_factory(lesson_course, lesson_user_factory("6451000001", 3))
        session.commit()
        course_id, lesson_id = lesson_course.course_id, lesson_record.lesson_id

        with count_queries(engine) as queries:
            detail = lesson_service.get_lesson_detail(session, course_id, lesson_id, lesson_teacher)

        assert detail.exercises == []
        assert detail.total_students == 1
        assert detail.submitted_students == 0
        assert detail.stats.avg_score == 0
        assert _submission_reads(queries) == []

    def test_lesson_without_enrolled_students(
        self, engine, session, lesson_teacher, lesson_course, lesson_record,
        lesson_problem_factory, lesson_user_factory, lesson_submission_factory,
    ):
        problem = lesson_problem_factory(lesson_record, total_number_testcase=2)
        lesson_submission_factory(problem, lesson_user_factory("6451000009", 3), passed_count=2)
        session.commit()
        course_id, lesson_id = lesson_course.course_id, lesson_record.lesson_id

        with count_queries(engine) as queries:
            detail = lesson_service.get_lesson_detail(session, course_id, lesson_id, lesson_teacher)

        assert detail.total_students == 0
        assert detail.submitted_students == 0
        assert detail.exercises[0].submitted_count == 0
        assert detail.stats.submission_rate == 0
        assert detail.stats.avg_score == 0
        assert _submission_reads(queries) == []

    def test_enrolled_students_without_submissions(
        self, session, lesson_teacher, lesson_course, lesson_record,
        lesson_problem_factory, lesson_user_factory, lesson_enrollment_factory,
    ):
        lesson_problem_factory(lesson_record, total_number_testcase=2)
        lesson_enrollment_factory(lesson_course, lesson_user_factory("6451000001", 3))
        session.commit()

        detail = lesson_service.get_lesson_detail(
            session, lesson_course.course_id, lesson_record.lesson_id, lesson_teacher
        )

        assert detail.submitted_students == 0
        assert detail.exercises[0].submitted_count == 0
        assert detail.stats.avg_score == 0
        assert detail.alert.missing_students == 1


class TestLessonAvgScoreMatchesGradebook:
    """avg_score dùng cùng quy tắc chọn bài nộp với bảng điểm: điểm tay ưu tiên hơn passed_count."""

    def _detail(self, session, teacher, course, lesson):
        session.refresh(teacher)
        return lesson_service.get_lesson_detail(session, course.course_id, lesson.lesson_id, teacher)

    def test_manual_score_overrides_higher_passed_count(
        self, session, lesson_teacher, lesson_course, lesson_record,
        lesson_user_factory, lesson_problem_factory, lesson_submission_factory, lesson_enrollment_factory,
    ):
        problem = lesson_problem_factory(lesson_record, title="P", total_number_testcase=4)
        student = lesson_user_factory("6451000011", 3)
        lesson_enrollment_factory(lesson_course, student)
        lesson_submission_factory(problem, student, passed_count=4)  # 10 điểm tự động
        graded = lesson_submission_factory(problem, student, passed_count=1)
        graded.manual_score = 3.5  # giáo viên chấm tay bài này
        session.add(graded)
        session.commit()

        detail = self._detail(session, lesson_teacher, lesson_course, lesson_record)

        assert detail.stats.avg_score == 3.5
        assert detail.exercises[0].submitted_count == 2

    def test_manual_score_counts_when_problem_has_no_testcases(
        self, session, lesson_teacher, lesson_course, lesson_record,
        lesson_user_factory, lesson_problem_factory, lesson_submission_factory, lesson_enrollment_factory,
    ):
        problem = lesson_problem_factory(lesson_record, title="P", total_number_testcase=0)
        student = lesson_user_factory("6451000012", 3)
        lesson_enrollment_factory(lesson_course, student)
        submission = lesson_submission_factory(problem, student, passed_count=0)
        submission.manual_score = 8.0
        session.add(submission)
        session.commit()

        assert self._detail(session, lesson_teacher, lesson_course, lesson_record).stats.avg_score == 8.0

    def test_problem_without_testcases_or_manual_score_is_not_averaged(
        self, session, lesson_teacher, lesson_course, lesson_record,
        lesson_user_factory, lesson_problem_factory, lesson_submission_factory, lesson_enrollment_factory,
    ):
        empty = lesson_problem_factory(lesson_record, title="Rỗng", total_number_testcase=0)
        normal = lesson_problem_factory(lesson_record, title="P", total_number_testcase=2)
        student = lesson_user_factory("6451000013", 3)
        lesson_enrollment_factory(lesson_course, student)
        lesson_submission_factory(empty, student, passed_count=0)
        lesson_submission_factory(normal, student, passed_count=1)
        session.commit()

        detail = self._detail(session, lesson_teacher, lesson_course, lesson_record)

        assert detail.stats.avg_score == 5.0
        assert detail.submitted_students == 1

    def test_avg_score_equals_mean_of_gradebook_cells(
        self, session, lesson_teacher, lesson_course, lesson_record, stats_setup, lesson_submission_factory,
    ):
        p1, _p2, s1, _s2 = stats_setup
        override = lesson_submission_factory(p1, s1, passed_count=0)
        override.manual_score = 9.0
        session.add(override)
        session.commit()

        detail = self._detail(session, lesson_teacher, lesson_course, lesson_record)

        course = build_course_response(lesson_course, session)
        cells = [
            cell.value
            for row in course.grades
            for cell in row.session_scores[str(lesson_record.lesson_id)]
            if cell.value is not None
        ]
        # s1/P1 điểm tay 9.0, s1/P2 5.0, s2/P1 10.0
        assert sorted(cells) == [5.0, 9.0, 10.0]
        assert detail.stats.avg_score == round(sum(cells) / len(cells), 1) == 8.0
