"""Content-based duplicate detection for Problem JSON imports."""

import json
import re
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any


def _normalized_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def problem_content_identity(problem: Any) -> str:
    """Return a stable identity from the normalized problem content.

    Case, Unicode composition, and whitespace differences do not make a new
    problem. Test cases are intentionally excluded: two copies of the same
    statement remain duplicates even if one file has extra test cases.
    """
    if hasattr(problem, "model_dump"):
        problem = problem.model_dump(mode="python")
    if not isinstance(problem, Mapping):
        problem = {
            field: getattr(problem, field, None)
            for field in ("title", "description", "constraints", "function_name")
        }

    identity = {
        "title": _normalized_text(problem.get("title")),
        "description": _normalized_text(problem.get("description")),
        "constraints": _normalized_text(problem.get("constraints")),
        "function_name": _normalized_text(problem.get("function_name")),
    }
    return json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def duplicate_problem_pairs(problems: Sequence[Any]) -> list[tuple[int, int]]:
    """Return (duplicate_index, first_index) pairs using 1-based positions."""
    first_by_identity: dict[str, int] = {}
    duplicates: list[tuple[int, int]] = []
    for index, problem in enumerate(problems, start=1):
        identity = problem_content_identity(problem)
        first_index = first_by_identity.get(identity)
        if first_index is None:
            first_by_identity[identity] = index
        else:
            duplicates.append((index, first_index))
    return duplicates


def normalized_task_id(value: Any) -> str:
    """Normalize an upstream dataset task identifier for duplicate checks."""
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value)))
