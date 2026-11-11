import json

import pytest
from sqlmodel import select

from app.core.exceptions import InvalidFormatError
from app.modules.problems import service as problem_service
from app.modules.problems.importer import (
    MAX_PROBLEM_IMPORT_BYTES,
    MAX_PROBLEMS_PER_IMPORT,
    inspect_problem_import,
    parse_problem_import,
)
from app.modules.problems.schemas import (
    MIN_PROBLEM_TESTCASES,
    MIN_SAMPLE_TESTCASES,
    MAX_PROBLEM_TESTCASES,
)
from app.models.entities import Problem

pytest_plugins = ("tests.support.fixtures.problem_fixtures",)


def _problem_payload(
    *,
    title: str = "Sum Two Numbers",
    description: str = "Return the sum of two numbers.",
    function_name: str = "sumTwoNumbers",
    report: str | None = None,
) -> dict:
    return {
        "title": title,
        "report": report,
        "function_name": function_name,
        "description": description,
        "constraints": "-1000 <= a, b <= 1000",
        "level": "easy",
        "time_limit_seconds": 2,
        "starter_codes": {
            "python": f"class Solution:\n    def {function_name}(self, a, b): pass",
            "javascript": f"function {function_name}(a, b) {{ return a + b; }}",
        },
        "start_datetime": "2026-01-01T00:00:00+07:00",
        "end_datetime": "2099-12-31T23:59:00+07:00",
        "testcases": [
            {"input": [index, index + 1], "expected_output": 2 * index + 1, "is_sample": index < 3}
            for index in range(10)
        ],
    }


def _request(factory, *, title: str, description: str, **overrides):
    function_name = overrides.get("function_name", "solve")
    starter_codes = overrides.pop("starter_codes", {
        "python": f"def {function_name}(*args): pass",
        "javascript": f"function {function_name}(...args) {{ return 0; }}",
    })
    return factory(
        title=title,
        description=description,
        starter_codes=starter_codes,
        testcases=[
            {"input": [index, index + 1], "expected_output": 2 * index + 1, "is_sample": index < 3}
            for index in range(10)
        ],
        **overrides,
    )


def test_import_accepts_supported_json_shapes_and_preserves_report():
    problem = _problem_payload(report="  IMPORT-CODE  ")
    for payload in (problem, [problem], {"problems": [problem]}):
        parsed = parse_problem_import("problems.json", json.dumps(payload).encode())
        assert len(parsed) == 1
        assert parsed[0].report == "IMPORT-CODE"


def test_preview_rejects_duplicate_normalized_problem_content(session):
    payload = {
        "problems": [
            _problem_payload(report="FIRST-CODE"),
            _problem_payload(title="  SUM\t TWO NUMBERS  ", report="SECOND-CODE"),
        ]
    }

    inspection = inspect_problem_import("problems.json", json.dumps(payload).encode())
    preview = problem_service.preview_bank_problem_import(session, inspection)

    assert preview.valid is False
    assert preview.problem_count == 2
    assert preview.ready_problem_count == 2
    assert [issue.index for issue in preview.issues] == [2]
    assert "trùng với problem #1" in preview.issues[0].message


def test_duplicate_issue_uses_original_file_index_after_an_invalid_item():
    payload = {
        "problems": [
            {"title": "Invalid problem"},
            _problem_payload(),
            _problem_payload(title=" SUM   TWO NUMBERS "),
        ]
    }

    inspection = inspect_problem_import("problems.json", json.dumps(payload).encode())

    assert [issue.index for issue in inspection.issues] == [1, 3]
    assert "problem #3 trùng với problem #2" in inspection.issues[1].message


def test_preview_reports_content_already_in_problem_bank(session, problem_factory):
    existing = problem_factory()
    payload = _problem_payload(
        title="Two Sum",
        description="Return matching indexes.",
        function_name="two_sum",
    )
    payload["constraints"] = "1 <= n <= 100"
    inspection = inspect_problem_import("problems.json", json.dumps(payload).encode())

    preview = problem_service.preview_bank_problem_import(session, inspection)

    assert preview.valid is False
    assert len(preview.issues) == 1
    assert preview.issues[0].index == 1
    assert f"ID {existing.problem_id}" in preview.issues[0].message


def test_parse_rejects_duplicate_content_even_when_codes_differ():
    payload = {
        "problems": [
            _problem_payload(report="FIRST-CODE"),
            _problem_payload(report="SECOND-CODE"),
        ]
    }

    with pytest.raises(InvalidFormatError, match="trùng với problem #1"):
        parse_problem_import("problems.json", json.dumps(payload).encode())


def test_new_bank_problems_store_optional_report(session, problem_create_request_factory):
    result = problem_service.create_bank_problem(
        session,
        _request(
            problem_create_request_factory,
            title="New problem",
            description="A newly created problem.",
            report="TEAM-PROBLEM-001",
        ),
    )

    saved = session.get(Problem, result.id)
    assert saved is not None
    assert saved.report == "TEAM-PROBLEM-001"


def test_import_rejects_duplicate_content_before_writing(session, problem_create_request_factory):
    first = _request(
        problem_create_request_factory,
        title="Same problem",
        description="Same normalized statement.",
    )
    second = _request(
        problem_create_request_factory,
        title="  SAME   PROBLEM ",
        description="Same normalized statement.",
    )

    with pytest.raises(InvalidFormatError, match="trùng với problem #1"):
        problem_service.import_bank_problems(session, [first, second])

    assert session.exec(select(Problem)).all() == []


def test_import_rejects_content_already_in_problem_bank(
    session, problem_factory, problem_create_request_factory
):
    existing = problem_factory()
    duplicate = _request(
        problem_create_request_factory,
        title="Two Sum",
        description="Return matching indexes.",
        function_name="two_sum",
        constraints="1 <= n <= 100",
    )

    with pytest.raises(InvalidFormatError, match="trùng với bài nguồn hiện có"):
        problem_service.import_bank_problems(session, [duplicate])

    assert session.get(Problem, existing.problem_id) is not None
    assert len(session.exec(select(Problem)).all()) == 1


def test_import_success_creates_problems_with_reports(session, problem_create_request_factory):
    items = [
        _request(
            problem_create_request_factory,
            title="First imported problem",
            description="First imported statement.",
            report="IMPORT-001",
        ),
        _request(
            problem_create_request_factory,
            title="Second imported problem",
            description="Second imported statement.",
            report="IMPORT-002",
        ),
    ]

    result = problem_service.import_bank_problems(session, items)
    saved = session.exec(select(Problem).order_by(Problem.problem_id)).all()

    assert result.created_count == 2
    assert len(result.problems) == 2
    assert [item.code for item in result.problems] == ["IMPORT-001", "IMPORT-002"]
    assert [problem.report for problem in saved] == ["IMPORT-001", "IMPORT-002"]


def test_import_rolls_back_all_problems_when_a_write_fails(
    session, problem_create_request_factory, monkeypatch
):
    first = _request(
        problem_create_request_factory,
        title="First problem",
        description="First statement.",
    )
    second = _request(
        problem_create_request_factory,
        title="Second problem",
        description="Second statement.",
    )
    original_insert = problem_service._insert_bank_problem
    calls = 0

    def fail_on_second_insert(db_session, data):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("simulated database write failure")
        return original_insert(db_session, data)

    monkeypatch.setattr(problem_service, "_insert_bank_problem", fail_on_second_insert)
    with pytest.raises(RuntimeError, match="simulated database write failure"):
        problem_service.import_bank_problems(session, [first, second])

    assert session.exec(select(Problem)).all() == []


# ---------------------------------------------------------------------------
# New edge-case tests
# ---------------------------------------------------------------------------

def test_import_rejects_non_json_file_extension():
    """Files without .json extension must be rejected immediately."""
    raw = json.dumps(_problem_payload()).encode()
    inspection = inspect_problem_import("problems.csv", raw)
    assert len(inspection.issues) == 1
    assert "định dạng .json" in inspection.issues[0].message.lower() or "json" in inspection.issues[0].message.lower()


def test_import_rejects_oversized_file():
    """Files exceeding MAX_PROBLEM_IMPORT_BYTES must be rejected."""
    oversized = b"x" * (MAX_PROBLEM_IMPORT_BYTES + 1)
    inspection = inspect_problem_import("big.json", oversized)
    assert len(inspection.issues) == 1
    assert "25" in inspection.issues[0].message  # references the 25 MB limit


def test_import_rejects_too_many_problems():
    """A file with more than MAX_PROBLEMS_PER_IMPORT problems must be rejected."""
    # Build a minimal list exceeding the limit without fully parsing each problem
    items = [{"title": f"P{i}"} for i in range(MAX_PROBLEMS_PER_IMPORT + 1)]
    raw = json.dumps({"problems": items}).encode()
    inspection = inspect_problem_import("too_many.json", raw)
    assert len(inspection.issues) == 1
    assert str(MAX_PROBLEMS_PER_IMPORT) in inspection.issues[0].message


def test_import_rejects_problem_with_too_few_total_testcases():
    """A problem with fewer than MIN_PROBLEM_TESTCASES testcases must produce an issue."""
    payload = _problem_payload()
    # Keep only MIN_PROBLEM_TESTCASES - 1 testcases
    payload["testcases"] = payload["testcases"][: MIN_PROBLEM_TESTCASES - 1]
    inspection = inspect_problem_import("bad.json", json.dumps(payload).encode())
    assert len(inspection.issues) == 1
    assert "#1" in inspection.issues[0].message


def test_import_rejects_problem_with_too_few_sample_testcases():
    """A problem with fewer than MIN_SAMPLE_TESTCASES sample testcases must produce an issue."""
    payload = _problem_payload()
    # Mark all testcases as hidden (is_sample=False)
    for tc in payload["testcases"]:
        tc["is_sample"] = False
    inspection = inspect_problem_import("bad.json", json.dumps(payload).encode())
    assert len(inspection.issues) == 1


def test_import_rejects_problem_with_too_few_hidden_testcases():
    """A problem with fewer than MIN_HIDDEN_TESTCASES hidden testcases must produce an issue."""
    payload = _problem_payload()
    # Mark all testcases as sample (is_sample=True) — no hidden testcases
    for tc in payload["testcases"]:
        tc["is_sample"] = True
    inspection = inspect_problem_import("bad.json", json.dumps(payload).encode())
    assert len(inspection.issues) == 1


def test_import_rejects_problem_with_too_many_testcases():
    """A problem with more than MAX_PROBLEM_TESTCASES testcases must produce an issue."""
    payload = _problem_payload()
    # Build MAX_PROBLEM_TESTCASES+1 testcases (3 sample + rest hidden)
    payload["testcases"] = [
        {"input": [i, i + 1], "expected_output": 2 * i + 1, "is_sample": i < MIN_SAMPLE_TESTCASES}
        for i in range(MAX_PROBLEM_TESTCASES + 1)
    ]
    inspection = inspect_problem_import("bad.json", json.dumps(payload).encode())
    assert len(inspection.issues) == 1


def test_preview_duplicate_message_includes_existing_problem_title(
    session, problem_factory
):
    """Preview issue for a DB duplicate must include the existing problem's title."""
    existing = problem_factory(title="Two Sum")
    payload = _problem_payload(
        title="Two Sum",
        description="Return matching indexes.",
        function_name="two_sum",
    )
    payload["constraints"] = "1 <= n <= 100"
    inspection = inspect_problem_import("problems.json", json.dumps(payload).encode())

    preview = problem_service.preview_bank_problem_import(session, inspection)

    assert preview.valid is False
    assert len(preview.issues) == 1
    issue_msg = preview.issues[0].message
    assert f"ID {existing.problem_id}" in issue_msg
    assert "Two Sum" in issue_msg


def test_import_duplicate_message_includes_existing_problem_title(
    session, problem_factory, problem_create_request_factory
):
    """import_bank_problems error message must include the existing problem's title."""
    problem_factory(title="Two Sum")
    duplicate = _request(
        problem_create_request_factory,
        title="Two Sum",
        description="Return matching indexes.",
        function_name="two_sum",
        constraints="1 <= n <= 100",
    )

    with pytest.raises(InvalidFormatError) as exc_info:
        problem_service.import_bank_problems(session, [duplicate])

    assert "Two Sum" in str(exc_info.value.message)


def test_preview_valid_file_returns_correct_counts(session):
    """A valid file with 2 unique problems should produce valid=True and correct counts."""
    payload = {
        "problems": [
            _problem_payload(title="Problem Alpha", description="Alpha description."),
            _problem_payload(title="Problem Beta", description="Beta description entirely different."),
        ]
    }
    inspection = inspect_problem_import("valid.json", json.dumps(payload).encode())
    preview = problem_service.preview_bank_problem_import(session, inspection)

    assert preview.valid is True
    assert preview.problem_count == 2
    assert preview.ready_problem_count == 2
    assert preview.testcase_count == 20   # 10 testcases per problem, 2 problems
    assert preview.sample_testcase_count == 6  # 3 sample per problem, 2 problems
    assert preview.hidden_testcase_count == 14  # 7 hidden per problem, 2 problems
    assert preview.issues == []


def test_import_non_utf8_file_returns_issue():
    """A file with invalid encoding must produce a parse error issue."""
    raw = b"\xff\xfe" + b"not valid utf-8 json"
    inspection = inspect_problem_import("bad.json", raw)
    # Either a JSON decode error or a file format error — either way there's an issue
    assert len(inspection.issues) >= 1


