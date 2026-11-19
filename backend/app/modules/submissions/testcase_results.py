"""Đọc kết quả chấm từng testcase đã lưu trong ``Submission.testcase_results``."""

from app.models import Submission, Testcase
from app.modules.submissions.schemas import TestcaseResultResponse


def result_by_testcase(submission: Submission) -> dict[int, dict]:
    """Map ``testcase_id`` -> ``{"status", "time"}``; rỗng với bài nộp cũ."""
    return {
        item["testcase_id"]: item
        for item in submission.testcase_results or []
        if isinstance(item, dict) and "testcase_id" in item
    }


def build_testcase_results(
    submission: Submission, testcases: list[Testcase]
) -> list[TestcaseResultResponse]:
    """Kết quả theo đúng thứ tự testcase, không kèm dữ liệu test.

    Trả về ``[]`` nếu bài nộp chưa có kết quả từng test (bài cũ, đang chấm) hoặc
    testcase của đề đã đổi sau khi chấm — giao diện khi đó chỉ hiện tổng passed/total.
    """
    results = result_by_testcase(submission)
    if not results or any(tc.testcase_id not in results for tc in testcases):
        return []
    return [
        TestcaseResultResponse(
            index=index,
            is_sample=testcase.is_sample,
            status=results[testcase.testcase_id]["status"],
            time=results[testcase.testcase_id].get("time"),
        )
        for index, testcase in enumerate(testcases, start=1)
    ]
