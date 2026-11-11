import io
import json
import zipfile
from collections import Counter
from typing import Any

from sqlmodel import Session, func, select

from app.core.utils.datetime_utils import as_utc, now_utc
from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.core.dependencies import Role
from app.modules.problems.schemas import (
    MAX_PROBLEM_TESTCASES,
    MIN_HIDDEN_TESTCASES,
    MIN_PROBLEM_TESTCASES,
    MIN_SAMPLE_TESTCASES,
    ProblemDetailResponse,
    ProblemTestcaseUpdate,
    validate_testcase_coverage,
    validate_problem_testcase_mode,
)
from app.modules.testcases.schemas import (
    PreviewErrorResponse,
    PreviewWarningResponse,
    TestcaseBatchRequest,
    TestcaseListResponse,
    TestcasePreviewRequest,
    TestcasePreviewResponse,
    TestcaseResponse,
    TestcaseUpdateRequest,
)
from app.modules.courses.access import (
    get_lesson_in_course,
    get_manageable_course,
    get_problem_in_lesson,
    get_viewable_course,
)
from app.modules.problems.service import get_problem_detail
from app.modules.testcases.testcase_format import (
    JSON_ARGUMENTS,
    JSON_VALUE,
    decode_testcase_value,
    encode_json,
    problem_testcase_to_storage,
    testcase_to_api_values,
)
from app.models.entities import Problem, Submission, Testcase, User

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
    testcase_count = session.exec(
        select(func.count()).select_from(Testcase).where(Testcase.problem_id == problem.problem_id)
    ).one()
    if testcase_count >= MAX_PROBLEM_TESTCASES:
        raise ConflictError(f"Problem chỉ được có tối đa {MAX_PROBLEM_TESTCASES} testcase")
    validate_problem_testcase_mode([data], problem.function_name)
    session.add(Testcase(
        problem_id=problem.problem_id,
        **problem_testcase_to_storage(data.model_dump(), problem.function_name),
    ))
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
    current_values = testcase_to_api_values(testcase)
    new_values = {
        "input": update_fields.get("input", current_values["input"]),
        "expected_output": update_fields.get("expected_output", current_values["expected_output"]),
        "is_sample": update_fields.get("is_sample", testcase.is_sample),
    }
    validate_problem_testcase_mode([ProblemTestcaseUpdate(**new_values)], problem.function_name)
    if (
        update_fields.get("is_sample") is not None
        and update_fields["is_sample"] != testcase.is_sample
    ):
        current_testcases = session.exec(
            select(Testcase).where(Testcase.problem_id == problem.problem_id)
        ).all()
        if len(current_testcases) >= MIN_PROBLEM_TESTCASES:
            validate_testcase_coverage([
                {
                    "is_sample": update_fields["is_sample"]
                    if item.testcase_id == testcase_id else item.is_sample
                }
                for item in current_testcases
            ])
    if "input" in update_fields or "expected_output" in update_fields:
        update_fields.update(problem_testcase_to_storage(new_values, problem.function_name))
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
    current_testcases = session.exec(
        select(Testcase).where(Testcase.problem_id == problem.problem_id)
    ).all()
    if len(current_testcases) >= MIN_PROBLEM_TESTCASES:
        validate_testcase_coverage(
            [item for item in current_testcases if item.testcase_id != testcase.testcase_id]
        )
    elif len(current_testcases) <= 1:
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

    current_testcases = session.exec(
        select(Testcase).where(Testcase.problem_id == problem.problem_id)
    ).all()
    if (
        any(item.is_sample != data.is_sample for item in testcases)
        and len(current_testcases) >= MIN_PROBLEM_TESTCASES
    ):
        validate_testcase_coverage([
            {"is_sample": data.is_sample if item.testcase_id in testcase_ids else item.is_sample}
            for item in current_testcases
        ])

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
    if "is_sample" in item and not isinstance(item["is_sample"], bool):
        return "is_sample phải là true hoặc false"
    input_type = item.get("input_type", JSON_ARGUMENTS)
    output_type = item.get("expected_output_type", JSON_VALUE)
    if (input_type, output_type) == ("stdin", "stdout"):
        if not isinstance(item["input"], str) or not isinstance(item["expected_output"], str):
            return "stdin/stdout testcase cần input và expected_output dạng chuỗi"
    elif (input_type, output_type) == (JSON_ARGUMENTS, JSON_VALUE):
        if not isinstance(item["input"], list):
            return "input phải là mảng các tham số truyền vào function"
        try:
            encode_json(item["input"])
            encode_json(item["expected_output"])
        except AppError as error:
            return str(error)
    else:
        return "cặp input_type/expected_output_type không được hỗ trợ"
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
    hidden_count = len(valid_items) - sample_count
    coverage_issues = []
    if len(data.testcases) < MIN_PROBLEM_TESTCASES or len(data.testcases) > MAX_PROBLEM_TESTCASES:
        coverage_issues.append(f"tổng testcase phải từ {MIN_PROBLEM_TESTCASES} đến {MAX_PROBLEM_TESTCASES}")
    if sample_count < MIN_SAMPLE_TESTCASES:
        coverage_issues.append(f"cần ít nhất {MIN_SAMPLE_TESTCASES} testcase mẫu")
    if hidden_count < MIN_HIDDEN_TESTCASES:
        coverage_issues.append(f"cần ít nhất {MIN_HIDDEN_TESTCASES} testcase ẩn")
    if coverage_issues:
        errors.append(PreviewErrorResponse(
            index=len(data.testcases) + 1,
            message=(
                f"Payload chưa đạt yêu cầu ({'; '.join(coverage_issues)}; hiện có "
                f"{len(data.testcases)} tổng, {sample_count} mẫu, {hidden_count} ẩn)"
            ),
        ))
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
