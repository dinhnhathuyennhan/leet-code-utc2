from app.core.dependencies import Role, get_current_user
from app.main import app
from tests.support.fixtures.builders import make_user

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

    def test_regrade_other_teachers_submission_returns_404(
        self,
        client,
        session,
        pending_error_submission,
        monkeypatch,
    ):
        other_teacher = make_user(session, "GV002", Role.TEACHER)
        pending_error_submission.status = "internal_error"
        session.add(pending_error_submission)
        session.commit()
        app.dependency_overrides[get_current_user] = lambda: other_teacher
        queued: list[int] = []
        monkeypatch.setattr(
            "app.modules.submissions.judge0.grading_queue.enqueue",
            lambda submission_id, *args: queued.append(submission_id),
        )

        response = client.post(
            f"/submissions/{pending_error_submission.submission_id}/regrade"
        )

        assert response.status_code == 404
        assert queued == []
        session.refresh(pending_error_submission)
        assert pending_error_submission.status == "internal_error"
