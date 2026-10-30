from sqlmodel import Session

from app.modules.submissions.service import list_pending_submissions
from app.models.entities import User

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