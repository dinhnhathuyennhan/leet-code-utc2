import pytest
from sqlmodel import Session

from app.core.dependencies import Role
from app.modules.submissions.schemas import SubmissionUpdateRequest
from app.modules.submissions.service import list_pending_submissions, update_submission
from app.models.entities import User
from tests.support.fixtures.builders import make_user

pytest_plugins = ("tests.support.fixtures.submission_fixtures",)


class TestListPendingSubmissions:
    def test_search_keeps_compile_error_count_scoped_to_matching_rows(
        self,
        session: Session,
        submission_teacher: User,
        pending_error_submission,
    ):
        result = list_pending_submissions(
            session, submission_teacher, search="SV001"
        )

        assert result.total == 1
        assert result.counts["all"] == 1
        assert result.counts["error"] == 1
        assert result.items[0].student_code == "SV001"


class TestUpdateSubmission:
    @pytest.mark.parametrize("role", [Role.ADMIN, Role.TEACHER])
    @pytest.mark.parametrize(
        ("score_fields", "expected"),
        [({}, 7.5), ({"manual_score": None}, None),
         ({"manual_score": 0}, 0), ({"manual_score": 8.5}, 8.5),
         ({"manual_score": 10}, 10)],
        ids=["omitted-preserves-score", "null-clears-score", "zero", "decimal", "maximum"],
    )
    def test_manual_score_patch_persists_explicit_values_only(
        self, session: Session, submission_teacher: User,
        pending_error_submission, role, score_fields, expected,
    ):
        submission = pending_error_submission
        submission.manual_score = 7.5
        session.add(submission)
        session.commit()
        actor = (make_user(session, "ADMIN_TEST", Role.ADMIN)
                 if role == Role.ADMIN else submission_teacher)

        result = update_submission(
            session, submission.submission_id,
            SubmissionUpdateRequest(feedback="Updated feedback", **score_fields), actor,
        )

        assert result.manual_score == expected
        session.expire_all()
        session.refresh(submission)
        assert submission.manual_score == expected
        assert submission.feedback == "Updated feedback"
        assert submission.status == "compile_error"
