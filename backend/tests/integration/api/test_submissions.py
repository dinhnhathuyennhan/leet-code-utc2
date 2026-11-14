from app.core.dependencies import get_current_user
from app.main import app

pytest_plugins = (
    "tests.support.fixtures.api_fixtures",
    "tests.support.fixtures.submission_fixtures",
)


class TestRegradeSubmissionRoute:
    def test_regrade_internal_error_submission_returns_pending(
        self,
        client,
        session,
        submission_teacher,
        submission_student,
        pending_error_submission,
        monkeypatch,
    ):
        pending_error_submission.status = "internal_error"
        session.add(pending_error_submission)
        session.commit()
        app.dependency_overrides[get_current_user] = lambda: submission_teacher
        queued: list[int] = []
        monkeypatch.setattr(
            "app.modules.submissions.judge0.grading_queue.enqueue",
            lambda submission_id, *args: queued.append(submission_id),
        )

        response = client.post(
            f"/submissions/{pending_error_submission.submission_id}/regrade"
        )

        assert response.status_code == 202
        assert response.json() == {
            "submission_id": pending_error_submission.submission_id,
            "status": "pending",
        }
        assert queued == [pending_error_submission.submission_id]

    def test_regrade_rejects_student(self, client, submission_student, pending_error_submission):
        app.dependency_overrides[get_current_user] = lambda: submission_student

        response = client.post(
            f"/submissions/{pending_error_submission.submission_id}/regrade"
        )

        assert response.status_code == 403
