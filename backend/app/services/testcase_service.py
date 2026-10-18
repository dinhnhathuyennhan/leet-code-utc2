import io
import json
import zipfile
from collections import Counter
from typing import Any

from sqlmodel import Session, func, select

from app.core.datetime_utils import as_utc, now_utc
from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.dependencies import Role
from app.schemas.problem import ProblemDetailResponse, ProblemTestcaseUpdate
from app.schemas.testcase import (
    PreviewErrorResponse,
    PreviewWarningResponse,
    TestcaseBatchRequest,
    TestcaseListResponse,
    TestcasePreviewRequest,
    TestcasePreviewResponse,
    TestcaseResponse,
    TestcaseUpdateRequest,
)
from app.services.course_access import (
    get_lesson_in_course,
    get_manageable_course,
    get_problem_in_lesson,
    get_viewable_course,
)
from app.services.problem_service import get_problem_detail
from app.services.testcase_format import (
    JSON_ARGUMENTS,
    JSON_VALUE,
    decode_testcase_value,
    encode_json,
    testcase_to_storage,
)
from models import Problem, Submission, Testcase, User

EXPORT_FORMATS = ("json", "zip")
PROBLEM_NOT_FOUND_MESSAGE = "Không tìm thấy bài tập trong buổi học"
HAS_SUBMISSION_MESSAGE = "Bài đã có bài nộp, không thể thay đổi testcase"


class InvalidExportFormatError(AppError):
    status_code = 422
    error_code = "VALIDATION_ERROR"


def _to_response(testcase: Testcase) -> TestcaseResponse:
    return TestcaseResponse(
        id=testcase.testcase_id,
        input=decode_testcase_value(testcase.input, testcase.input_type),
        expected_output=decode_testcase_value(testcase.expected_output, testcase.expected_output_type),
        is_sample=testcase.is_sample,
        input_type=testcase.input_type,
        expected_output_type=testcase.expected_output_type,
    )


def _get_viewable_problem(
    session: Session, course_id: str, lesson_id: int, problem_id: int, current_user: User
) -> Problem:
    get_viewable_course(session, course_id, current_user)
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    problem = get_problem_in_lesson(session, lesson, problem_id)
    # Giống get_problem_detail: bài chưa đến giờ mở thì Student coi như không tồn tại
    if current_user.role_id == Role.STUDENT and as_utc(problem.start_datetime) > now_utc():
        raise NotFoundError(PROBLEM_NOT_FOUND_MESSAGE)
    return problem


def _get_manageable_problem(
    session: Session, course_id: str, lesson_id: int, problem_id: int, current_user: User
) -> Problem:
    get_manageable_course(
        course_id, session, current_user, "Bạn không có quyền thực hiện hành động này"
    )
    lesson = get_lesson_in_course(session, course_id, lesson_id)
    return get_problem_in_lesson(session, lesson, problem_id)


def _get_testcase(session: Session, problem_id: int, testcase_id: int) -> Testcase:
    testcase = session.get(Testcase, testcase_id)
    if testcase is None or testcase.problem_id != problem_id:
        raise NotFoundError("Không tìm thấy testcase")
    return testcase


def _assert_no_submissions(session: Session, problem_id: int) -> None:
    has_submission = session.exec(
        select(Submission.submission_id).where(Submission.problem_id == problem_id)
    ).first()
    if has_submission is not None:
        raise ConflictError(HAS_SUBMISSION_MESSAGE)


def _refresh_testcase_count(session: Session, problem: Problem) -> None:
    session.flush()
    problem.total_number_testcase = session.exec(
        select(func.count()).select_from(Testcase).where(Testcase.problem_id == problem.problem_id)
    ).one()
    session.add(problem)


def list_testcases(
    session: Session,
    course_id: str,
    lesson_id: int,
    problem_id: int,
    is_sample: bool | None,
    current_user: User,
) -> TestcaseListResponse:
    problem = _get_viewable_problem(session, course_id, lesson_id, problem_id, current_user)
    testcases = session.exec(
        select(Testcase).where(Testcase.problem_id == problem.problem_id).order_by(Testcase.testcase_id)
    ).all()
    total_sample = sum(1 for testcase in testcases if testcase.is_sample)

    if current_user.role_id == Role.STUDENT:
        is_sample = True  # Student luôn chỉ thấy testcase mẫu, bỏ qua filter is_sample=false
    visible = [t for t in testcases if is_sample is None or t.is_sample == is_sample]
    return TestcaseListResponse(
        testcases=[_to_response(testcase) for testcase in visible],
        total_sample=total_sample,
        total_hidden=len(testcases) - total_sample,
    )


def add_testcase(
    session: Session,
    course_id: str,
    lesson_id: int,
    problem_id: int,
    data: ProblemTestcaseUpdate,
    current_user: User,
) -> ProblemDetailResponse:
    problem = _get_manageable_problem(session, course_id, lesson_id, problem_id, current_user)
    _assert_no_submissions(session, problem.problem_id)
    session.add(Testcase(problem_id=problem.problem_id, **testcase_to_storage(data.model_dump())))
    _refresh_testcase_count(session, problem)
    session.commit()
    return get_problem_detail(session, course_id, lesson_id, problem_id, current_user)


def update_testcase(
    session: Session,
    course_id: str,
    lesson_id: int,
    problem_id: int,
    testcase_id: int,
    data: TestcaseUpdateRequest,
    current_user: User,
) -> ProblemDetailResponse:
    problem = _get_manageable_problem(session, course_id, lesson_id, problem_id, current_user)
    testcase = _get_testcase(session, problem.problem_id, testcase_id)
    _assert_no_submissions(session, problem.problem_id)

    update_fields = data.model_dump(exclude_unset=True)
    if "input" in update_fields:
        update_fields["input"] = encode_json(update_fields["input"])
        update_fields["input_type"] = JSON_ARGUMENTS
    if "expected_output" in update_fields:
        update_fields["expected_output"] = encode_json(update_fields["expected_output"])
        update_fields["expected_output_type"] = JSON_VALUE
    update_fields = {
        key: value for key, value in update_fields.items()
        if value is not None or key == "expected_output"
    }
    for field, value in update_fields.items():
        setattr(testcase, field, value)
    session.add(testcase)
    session.commit()
    return get_problem_detail(session, course_id, lesson_id, problem_id, current_user)


def delete_testcase(
    session: Session,
    course_id: str,
    lesson_id: int,
    problem_id: int,
    testcase_id: int,
    current_user: User,
) -> None:
    problem = _get_manageable_problem(session, course_id, lesson_id, problem_id, current_user)
    testcase = _get_testcase(session, problem.problem_id, testcase_id)
    _assert_no_submissions(session, problem.problem_id)
    testcase_count = session.exec(
        select(func.count()).select_from(Testcase).where(Testcase.problem_id == problem.problem_id)
    ).one()
    if testcase_count <= 1:
        raise ConflictError("Problem phải có ít nhất một testcase")
    session.delete(testcase)
    _refresh_testcase_count(session, problem)
    session.commit()


def batch_update_sample(
    session: Session,
    course_id: str,
    lesson_id: int,
    problem_id: int,
    data: TestcaseBatchRequest,
    current_user: User,
) -> ProblemDetailResponse:
    problem = _get_manageable_problem(session, course_id, lesson_id, problem_id, current_user)
    testcase_ids = set(data.testcase_ids)
    testcases = session.exec(
        select(Testcase).where(
            Testcase.problem_id == problem.problem_id,
            Testcase.testcase_id.in_(testcase_ids),
        )
    ).all()
    if len(testcases) != len(testcase_ids):
        raise NotFoundError("Một hoặc nhiều testcase không tồn tại trong bài tập này")
    _assert_no_submissions(session, problem.problem_id)

    for testcase in testcases:
        testcase.is_sample = data.is_sample
        session.add(testcase)
    session.commit()
    return get_problem_detail(session, course_id, lesson_id, problem_id, current_user)


def export_testcases(
    session: Session,
    course_id: str,
    lesson_id: int,
    problem_id: int,
    export_format: str,
    current_user: User,
) -> bytes:
    problem = _get_manageable_problem(session, course_id, lesson_id, problem_id, current_user)
    if export_format not in EXPORT_FORMATS:
        raise InvalidExportFormatError("format phải là 'json' hoặc 'zip'")

    testcases = session.exec(
        select(Testcase).where(Testcase.problem_id == problem.problem_id).order_by(Testcase.testcase_id)
    ).all()
    # Cùng cấu trúc với endpoint upload nên file tải về có thể upload lại nguyên vẹn
    payload = {
        "problem_title": problem.title,
        "exported_at": now_utc().isoformat(timespec="seconds"),
        "testcases": [
            {
                "input": decode_testcase_value(testcase.input, testcase.input_type),
                "expected_output": decode_testcase_value(
                    testcase.expected_output, testcase.expected_output_type
                ),
                "is_sample": testcase.is_sample,
                "input_type": testcase.input_type,
                "expected_output_type": testcase.expected_output_type,
            }
            for testcase in testcases
        ],
    }
    content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    if export_format == "json":
        return content

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"testcases_{problem.problem_id}.json", content)
    return buffer.getvalue()


def _preview_item_error(item: Any) -> str | None:
    if not isinstance(item, dict):
        return "Testcase phải là một object"
    for field in ("input", "expected_output"):
        if field not in item:
            return f"Thiếu {field}"
    if not isinstance(item["input"], list):
        return "input phải là mảng các tham số truyền vào function"
    try:
        encode_json(item["input"])
        encode_json(item["expected_output"])
    except AppError as error:
        return str(error)
    if "is_sample" in item and not isinstance(item["is_sample"], bool):
        return "is_sample phải là true hoặc false"
    if item.get("input_type", JSON_ARGUMENTS) != JSON_ARGUMENTS:
        return f"input_type phải là '{JSON_ARGUMENTS}'"
    if item.get("expected_output_type", JSON_VALUE) != JSON_VALUE:
        return f"expected_output_type phải là '{JSON_VALUE}'"
    return None


def preview_testcases(data: TestcasePreviewRequest) -> TestcasePreviewResponse:
    """Stateless: chỉ validate, không đụng DB."""
    errors: list[PreviewErrorResponse] = []
    valid_items: list[dict] = []
    for index, item in enumerate(data.testcases, start=1):
        message = _preview_item_error(item)
        if message is None:
            valid_items.append(item)
        else:
            errors.append(PreviewErrorResponse(index=index, message=message))

    sample_count = sum(1 for item in valid_items if item.get("is_sample", False))
    warnings: list[PreviewWarningResponse] = []
    if valid_items and sample_count == 0:
        warnings.append(
            PreviewWarningResponse(
                message="Không có testcase mẫu nào, sinh viên sẽ không thấy ví dụ"
            )
        )
    output_counts = Counter(encode_json(item["expected_output"]) for item in valid_items)
    warnings.extend(
        PreviewWarningResponse(message=f"{count} testcase có cùng expected_output, hãy kiểm tra lại")
        for count in output_counts.values()
        if count >= 2
    )

    return TestcasePreviewResponse(
        valid=not errors,
        count=len(data.testcases),
        sample_count=sample_count,
        hidden_count=len(valid_items) - sample_count,
        errors=errors,
        warnings=warnings,
    )
