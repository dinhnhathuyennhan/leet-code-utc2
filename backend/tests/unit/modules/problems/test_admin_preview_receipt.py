import pytest

from app.core.exceptions import ConflictError
from app.modules.ai_review.preview_receipt import create_preview_receipt, verify_preview_receipt
from app.modules.ai_review.schemas import AdminPreviewReviewRequest


def test_preview_receipt_only_accepts_matching_user_problem_and_code():
    receipt = create_preview_receipt(
        user_id="admin-1", problem_id=10, language="python", code="print(1)",
        status="wrong_answer", passed_count=1, total_count=3,
    )
    result = verify_preview_receipt(
        receipt, user_id="admin-1", problem_id=10, language="python", code="print(1)",
    )
    assert result["passed_count"] == 1
    for changes in ({"code": "print(2)"}, {"user_id": "admin-2"}, {"problem_id": 11}):
        with pytest.raises(ConflictError):
            verify_preview_receipt(receipt, **{
                "user_id": "admin-1", "problem_id": 10,
                "language": "python", "code": "print(1)", **changes,
            })
    with pytest.raises(ConflictError):
        verify_preview_receipt("invalid", user_id="admin-1", problem_id=10,
                               language="python", code="print(1)")


def test_ai_request_preserves_code_whitespace_from_judge0():
    code = "  def solve():\n    return 1\n\n"
    receipt = create_preview_receipt(
        user_id="admin-1", problem_id=10, language="python", code=code,
        status="accepted", passed_count=1, total_count=1,
    )
    request = AdminPreviewReviewRequest.model_validate({
        "code": code, "language": "python", "preview_token": receipt,
    })
    assert request.code == code
    assert verify_preview_receipt(
        request.preview_token, user_id="admin-1", problem_id=10,
        language=request.language, code=request.code,
    )["status"] == "accepted"
