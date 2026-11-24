"""Integration tests for POST /problems/import and POST /problems/import/preview.

Tests the HTTP layer end-to-end using the real FastAPI app backed by an
in-memory SQLite database (via the `session` fixture from conftest.py).
Auth is bypassed by overriding `get_current_user` with a fixed User object.
"""
import json
import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_session
from app.core.dependencies import Role, get_current_user
from app.main import app
from app.models import User
from app.modules.problems.importer import MAX_PROBLEM_IMPORT_BYTES, MAX_PROBLEMS_PER_IMPORT

pytest_plugins = (
    "tests.support.fixtures.problem_fixtures",
    "tests.support.fixtures.api_fixtures",
)

JSON_MIME = "application/json"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(session) -> Iterator[TestClient]:
    """TestClient wired to the current test's in-memory session."""
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _login_as(role_id: int) -> None:
    """Override get_current_user so no JWT is needed."""
    user = User(
        user_id=uuid.uuid4(),
        full_name="Test User",
        email=f"user_{role_id}_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="placeholder",
        role_id=role_id,
    )
    app.dependency_overrides[get_current_user] = lambda: user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_problem_payload(**overrides) -> dict:
    """Return a minimal valid problem dict (10 testcases: 3 sample + 7 hidden)."""
    function_name = overrides.get("function_name", "sumTwoNumbers")
    base = {
        "title": "Sum Two Numbers",
        "report": None,
        "function_name": function_name,
        "description": "Return the sum of two numbers.",
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
            {"input": [i, i + 1], "expected_output": 2 * i + 1, "is_sample": i < 3}
            for i in range(10)
        ],
    }
    base.update(overrides)
    return base


def _upload(client: TestClient, endpoint: str, problems: list, filename: str = "problems.json"):
    """POST a JSON file containing the given problems list to `endpoint`."""
    raw = json.dumps({"problems": problems}).encode()
    return client.post(endpoint, files={"file": (filename, raw, JSON_MIME)})


# ---------------------------------------------------------------------------
# Auth tests — preview
# ---------------------------------------------------------------------------


def test_preview_requires_auth(client):
    raw = json.dumps({"problems": [_valid_problem_payload()]}).encode()
    response = client.post("/problems/import/preview", files={"file": ("p.json", raw, JSON_MIME)})
    assert response.status_code in (401, 403)


@pytest.mark.parametrize("role_id", [Role.ADMIN, Role.TEACHER])
def test_preview_allowed_for_admin_and_teacher(client, role_id):
    _login_as(role_id)
    response = _upload(client, "/problems/import/preview", [_valid_problem_payload()])
    assert response.status_code == 200


def test_preview_forbidden_for_student(client):
    _login_as(Role.STUDENT)
    response = _upload(client, "/problems/import/preview", [_valid_problem_payload()])
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Auth tests — import
# ---------------------------------------------------------------------------


def test_import_requires_auth(client):
    raw = json.dumps({"problems": [_valid_problem_payload()]}).encode()
    response = client.post("/problems/import", files={"file": ("p.json", raw, JSON_MIME)})
    assert response.status_code in (401, 403)


@pytest.mark.parametrize("role_id", [Role.ADMIN, Role.TEACHER])
def test_import_allowed_for_admin_and_teacher(client, role_id):
    _login_as(role_id)
    p = _valid_problem_payload(
        title=f"Unique Problem {role_id}",
        description=f"Unique description for role {role_id}.",
    )
    response = _upload(client, "/problems/import", [p])
    assert response.status_code == 201


def test_import_forbidden_for_student(client):
    _login_as(Role.STUDENT)
    response = _upload(client, "/problems/import", [_valid_problem_payload()])
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Preview — valid file
# ---------------------------------------------------------------------------


def test_preview_valid_file_returns_200_and_valid_true(client):
    _login_as(Role.ADMIN)
    response = _upload(client, "/problems/import/preview", [_valid_problem_payload()])
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["problem_count"] == 1
    assert data["ready_problem_count"] == 1
    assert data["testcase_count"] == 10
    assert data["sample_testcase_count"] == 3
    assert data["hidden_testcase_count"] == 7
    assert data["issues"] == []


def test_preview_two_unique_problems_returns_correct_counts(client):
    _login_as(Role.ADMIN)
    problems = [
        _valid_problem_payload(title="Alpha Problem", description="Alpha unique description."),
        _valid_problem_payload(title="Beta Problem", description="Beta unique description entirely different."),
    ]
    response = _upload(client, "/problems/import/preview", problems)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["problem_count"] == 2
    assert data["ready_problem_count"] == 2
    assert data["testcase_count"] == 20
    assert data["sample_testcase_count"] == 6
    assert data["hidden_testcase_count"] == 14
    assert data["issues"] == []


# ---------------------------------------------------------------------------
# Preview — validation failures
# ---------------------------------------------------------------------------


def test_preview_non_json_extension_returns_valid_false(client):
    _login_as(Role.ADMIN)
    raw = b'{"problems": []}'
    response = client.post("/problems/import/preview", files={"file": ("p.csv", raw, JSON_MIME)})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["issues"]) >= 1


def test_preview_oversized_file_returns_valid_false(client):
    _login_as(Role.ADMIN)
    raw = b"x" * (MAX_PROBLEM_IMPORT_BYTES + 1)
    response = client.post("/problems/import/preview", files={"file": ("big.json", raw, JSON_MIME)})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["issues"]) >= 1
    assert "25" in data["issues"][0]["message"]


def test_preview_too_many_problems_returns_valid_false(client):
    _login_as(Role.ADMIN)
    # Build minimal stubs exceeding the limit — no need for valid payloads
    items = [{"title": f"P{i}"} for i in range(MAX_PROBLEMS_PER_IMPORT + 1)]
    raw = json.dumps({"problems": items}).encode()
    response = client.post("/problems/import/preview", files={"file": ("too_many.json", raw, JSON_MIME)})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False


def test_preview_problem_with_too_few_testcases_returns_valid_false(client):
    _login_as(Role.ADMIN)
    p = _valid_problem_payload()
    p["testcases"] = p["testcases"][:5]  # only 5 — below minimum 10
    response = _upload(client, "/problems/import/preview", [p])
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False


def test_preview_problem_with_no_sample_testcases_returns_valid_false(client):
    _login_as(Role.ADMIN)
    p = _valid_problem_payload()
    for tc in p["testcases"]:
        tc["is_sample"] = False  # all hidden, 0 sample
    response = _upload(client, "/problems/import/preview", [p])
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False


# ---------------------------------------------------------------------------
# Preview — duplicate detection
# ---------------------------------------------------------------------------


def test_preview_duplicate_in_file_returns_valid_false(client):
    _login_as(Role.ADMIN)
    p1 = _valid_problem_payload(title="Dup Problem", description="Duplicate statement.")
    p2 = _valid_problem_payload(title="DUP PROBLEM", description="Duplicate statement.")
    response = _upload(client, "/problems/import/preview", [p1, p2])
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("trùng" in issue["message"] for issue in data["issues"])


def test_preview_duplicate_with_db_problem_returns_valid_false(client, problem_factory):
    _login_as(Role.ADMIN)
    # problem_factory() creates a "Two Sum" problem with function_name=two_sum,
    # description="Return matching indexes.", constraints="1 <= n <= 100" (from builders.py)
    existing = problem_factory()
    p = _valid_problem_payload(
        title="Two Sum",
        description="Return matching indexes.",
        function_name="two_sum",
        constraints="1 <= n <= 100",
    )
    response = _upload(client, "/problems/import/preview", [p])
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("trùng" in issue["message"] for issue in data["issues"])
    # The existing problem's ID must appear in the issue message
    assert any(str(existing.problem_id) in issue["message"] for issue in data["issues"])


def test_preview_duplicate_message_includes_existing_problem_title(client, problem_factory):
    _login_as(Role.ADMIN)
    existing = problem_factory(title="Two Sum")
    p = _valid_problem_payload(
        title="Two Sum",
        description="Return matching indexes.",
        function_name="two_sum",
        constraints="1 <= n <= 100",
    )
    response = _upload(client, "/problems/import/preview", [p])
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("Two Sum" in issue["message"] for issue in data["issues"])
    assert any(f"ID {existing.problem_id}" in issue["message"] for issue in data["issues"])


# ---------------------------------------------------------------------------
# Import — valid file
# ---------------------------------------------------------------------------


def test_import_valid_file_returns_201(client):
    _login_as(Role.ADMIN)
    p = _valid_problem_payload(title="Unique Import Problem", description="Unique statement for import.")
    response = _upload(client, "/problems/import", [p])
    assert response.status_code == 201
    data = response.json()
    assert data["created_count"] == 1
    assert len(data["problems"]) == 1
    assert data["problems"][0]["title"] == "Unique Import Problem"
    assert data["problems"][0]["total_number_testcase"] == 10


def test_import_two_unique_problems_at_once(client):
    _login_as(Role.ADMIN)
    problems = [
        _valid_problem_payload(title="Alpha Import", description="Alpha unique import statement."),
        _valid_problem_payload(title="Beta Import", description="Beta unique import statement entirely different."),
    ]
    response = _upload(client, "/problems/import", problems)
    assert response.status_code == 201
    data = response.json()
    assert data["created_count"] == 2
    titles = [p["title"] for p in data["problems"]]
    assert "Alpha Import" in titles
    assert "Beta Import" in titles


# ---------------------------------------------------------------------------
# Import — validation / duplicate failures
# ---------------------------------------------------------------------------


def test_import_non_json_file_extension_returns_error(client):
    _login_as(Role.ADMIN)
    raw = b'{"problems": []}'
    response = client.post("/problems/import", files={"file": ("p.csv", raw, JSON_MIME)})
    assert response.status_code in (400, 422)


def test_import_duplicate_in_db_returns_error(client, problem_factory):
    _login_as(Role.ADMIN)
    # Existing bank problem: title="Two Sum", fn=two_sum, desc="Return matching indexes.", constraints="1 <= n <= 100"
    problem_factory()
    p = _valid_problem_payload(
        title="Two Sum",
        description="Return matching indexes.",
        function_name="two_sum",
        constraints="1 <= n <= 100",
    )
    response = _upload(client, "/problems/import", [p])
    assert response.status_code in (400, 422)
    body = response.json()
    assert "trùng" in str(body).lower()


def test_import_duplicate_message_includes_existing_problem_title(client, problem_factory):
    _login_as(Role.ADMIN)
    problem_factory(title="Two Sum")
    p = _valid_problem_payload(
        title="Two Sum",
        description="Return matching indexes.",
        function_name="two_sum",
        constraints="1 <= n <= 100",
    )
    response = _upload(client, "/problems/import", [p])
    assert response.status_code in (400, 422)
    body_text = str(response.json())
    assert "Two Sum" in body_text


def test_import_duplicate_within_file_returns_error(client):
    _login_as(Role.ADMIN)
    p1 = _valid_problem_payload(title="Dup Problem", description="Duplicate statement.")
    p2 = _valid_problem_payload(title="DUP PROBLEM", description="Duplicate statement.")
    response = _upload(client, "/problems/import", [p1, p2])
    assert response.status_code in (400, 422)
    body_text = str(response.json())
    assert "trùng" in body_text.lower()


def test_import_missing_file_field_returns_422(client):
    _login_as(Role.ADMIN)
    response = client.post("/problems/import")
    assert response.status_code == 422
