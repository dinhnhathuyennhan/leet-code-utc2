import pytest
from sqlmodel import Session

from app.core.dependencies import Role
from app.modules.submissions.service import list_pending_submissions
from app.models.entities import Submission, User
from tests.support.fixtures.builders import make_submission, make_user

pytest_plugins = ("tests.support.fixtures.submission_fixtures",)


class TestListPendingSubmissions:
    def test_search_keeps_compile_error_count_scoped_to_matching_rows(
        self,
        session: Session,
        submission_teacher: User,
        submission_student: User,
        pending_error_submission,
    ):
        result = list_pending_submissions(
            session, submission_teacher, search=submission_student.student_code
        )

        assert result.total == 1
        assert result.counts["all"] == 1
        assert result.counts["error"] == 1
        assert result.items[0].student_code == submission_student.student_code


class TestPendingFilters:
    """Chip lọc trên UI gửi thẳng judge_kind làm `filter`, backend phải hiểu đúng."""

    @pytest.fixture
    def mixed_submissions(
        self,
        session: Session,
        submission_problem,
        submission_student: User,
    ) -> dict[str, Submission]:
        others = [make_user(session, f"SV10{index}", Role.STUDENT) for index in range(3)]
        return {
            "pending": make_submission(
                session, submission_problem, submission_student, status="pending"
            ),
            "wrong_answer": make_submission(
                session, submission_problem, others[0], status="wrong_answer", passed_count=1
            ),
            "compile_error": make_submission(
                session, submission_problem, others[1], status="compile_error"
            ),
            "accepted": make_submission(
                session, submission_problem, others[2], status="accepted", passed_count=3
            ),
        }

    @pytest.mark.parametrize("judge_kind", ["pending", "wrong_answer", "compile_error"])
    def test_filter_by_judge_kind_returns_only_that_kind(
        self, session: Session, submission_teacher: User, mixed_submissions, judge_kind: str
    ):
        result = list_pending_submissions(session, submission_teacher, filter_name=judge_kind)

        assert result.total == 1
        assert [item.status for item in result.items] == [judge_kind]

    def test_counts_cover_every_chip_without_applying_the_filter(
        self, session: Session, submission_teacher: User, mixed_submissions
    ):
        result = list_pending_submissions(session, submission_teacher, filter_name="pending")

        # Số đếm phải tính trên toàn bộ danh sách, không phải trên phần đã lọc.
        assert result.counts["all"] == 3  # accepted bị ẩn khi include_graded=False
        assert result.counts["pending"] == 1
        assert result.counts["wrong_answer"] == 1
        assert result.counts["compile_error"] == 1

    def test_unknown_filter_falls_back_to_all_rows(
        self, session: Session, submission_teacher: User, mixed_submissions
    ):
        result = list_pending_submissions(session, submission_teacher, filter_name="khong-ton-tai")

        assert result.total == 3

    def test_needs_grading_skips_accepted_and_already_scored_rows(
        self, session: Session, submission_teacher: User, mixed_submissions
    ):
        mixed_submissions["wrong_answer"].manual_score = 7.5
        session.add(mixed_submissions["wrong_answer"])
        session.flush()

        result = list_pending_submissions(
            session, submission_teacher, filter_name="needs_grading", include_graded=True
        )

        assert result.counts["needs_grading"] == 2
        assert {item.status for item in result.items} == {"pending", "compile_error"}

    def test_items_carry_grading_fields_so_client_skips_detail_calls(
        self, session: Session, submission_teacher: User, submission_problem, mixed_submissions
    ):
        mixed_submissions["wrong_answer"].manual_score = 6.0
        session.add(mixed_submissions["wrong_answer"])
        session.flush()

        result = list_pending_submissions(
            session, submission_teacher, filter_name="wrong_answer"
        )

        item = result.items[0]
        assert item.status == "wrong_answer"
        assert item.manual_score == 6.0
        assert item.passed_count == 1
        assert item.total_testcases == submission_problem.total_number_testcase
        expected_student = session.get(
            User, mixed_submissions["wrong_answer"].student_id
        )
        assert expected_student is not None
        assert item.student_code == expected_student.student_code
