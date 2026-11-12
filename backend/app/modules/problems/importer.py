import json
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.core.exceptions import AppError, InvalidFormatError
from app.modules.problems.deduplication import duplicate_problem_pairs
from app.modules.problems.schemas import ProblemCreateRequest

MAX_PROBLEM_IMPORT_BYTES = 25 * 1024 * 1024
MAX_PROBLEMS_PER_IMPORT = 5000


@dataclass(frozen=True)
class ProblemImportIssue:
    message: str
    index: int | None = None
    code: str | None = None


@dataclass(frozen=True)
class ProblemImportInspection:
    problem_count: int
    problems: list[ProblemCreateRequest]
    issues: list[ProblemImportIssue]
    problem_indices: list[int]


def _reject_non_json_constant(value: str) -> None:
    raise ValueError(f"Hằng số {value} không phải JSON hợp lệ")


def _problem_items(payload: Any) -> list[Any]:
    if isinstance(payload, dict) and "problems" in payload:
        items = payload["problems"]
    elif isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = [payload]
    else:
        raise InvalidFormatError("File JSON phải là một problem, một mảng problem hoặc object có field problems")

    if not isinstance(items, list) or not items:
        raise InvalidFormatError("Danh sách problem trong file JSON không hợp lệ hoặc đang rỗng")
    if len(items) > MAX_PROBLEMS_PER_IMPORT:
        raise InvalidFormatError(f"Mỗi lần import tối đa {MAX_PROBLEMS_PER_IMPORT} problem")
    return items


def inspect_problem_import(filename: str, raw: bytes) -> ProblemImportInspection:
    if not filename.lower().endswith(".json"):
        return ProblemImportInspection(0, [], [ProblemImportIssue("File import problem phải có định dạng .json")], [])
    if len(raw) > MAX_PROBLEM_IMPORT_BYTES:
        return ProblemImportInspection(0, [], [ProblemImportIssue("File import problem quá lớn (tối đa 25MB)")], [])

    try:
        payload = json.loads(raw.decode("utf-8-sig"), parse_constant=_reject_non_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return ProblemImportInspection(
            0, [], [ProblemImportIssue("File import problem phải là JSON UTF-8 hợp lệ")], []
        )

    try:
        items = _problem_items(payload)
    except InvalidFormatError as error:
        return ProblemImportInspection(0, [], [ProblemImportIssue(error.message)], [])

    validated: list[ProblemCreateRequest] = []
    validated_indices: list[int] = []
    issues: list[ProblemImportIssue] = []
    for index, item in enumerate(items, start=1):
        code = item.get("report") if isinstance(item, dict) and isinstance(item.get("report"), str) else None
        try:
            validated.append(ProblemCreateRequest.model_validate(item))
            validated_indices.append(index)
        except AppError as error:
            issues.append(ProblemImportIssue(f"Problem #{index}: {error.message}", index, code))
        except ValidationError as error:
            first_error = error.errors()[0]
            location = ".".join(str(part) for part in first_error["loc"])
            field = f" ({location})" if location else ""
            message = first_error["msg"].removeprefix("Value error, ")
            issues.append(ProblemImportIssue(f"Problem #{index}{field}: {message}", index, code))
        except (TypeError, ValueError):
            issues.append(ProblemImportIssue(f"Problem #{index}: dữ liệu không đúng định dạng", index, code))

    for duplicate_index, first_index in duplicate_problem_pairs(validated):
        file_index = validated_indices[duplicate_index - 1]
        first_file_index = validated_indices[first_index - 1]
        issues.append(ProblemImportIssue(
            f"Nội dung problem #{file_index} trùng với problem #{first_file_index} trong file",
            file_index,
            validated[duplicate_index - 1].report,
        ))
    return ProblemImportInspection(len(items), validated, issues, validated_indices)


def parse_problem_import(filename: str, raw: bytes) -> list[ProblemCreateRequest]:
    inspection = inspect_problem_import(filename, raw)
    if inspection.issues:
        raise InvalidFormatError(inspection.issues[0].message)
    return inspection.problems
