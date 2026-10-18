"""Serialize JSON function arguments in the existing text testcase columns."""
import json
from typing import Any

from app.core.exceptions import InvalidFormatError


JSON_ARGUMENTS = "json_args"
JSON_VALUE = "json"
LEGACY_INPUT = "stdin"
LEGACY_OUTPUT = "stdout"


def encode_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as error:
        raise InvalidFormatError("Testcase phải chứa giá trị JSON hợp lệ") from error


def decode_testcase_value(value: str, value_type: str) -> Any:
    if value_type not in (JSON_ARGUMENTS, JSON_VALUE):
        # Giữ nguyên testcase stdin/stdout đã có trước khi chuyển format.
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        # Dữ liệu JSON format hỏng vẫn có thể được xem và sửa qua API.
        return value


def testcase_to_storage(item: dict[str, Any]) -> dict[str, Any]:
    input_type = item.get("input_type", JSON_ARGUMENTS)
    output_type = item.get("expected_output_type", JSON_VALUE)
    if (input_type, output_type) == (LEGACY_INPUT, LEGACY_OUTPUT):
        if not isinstance(item["input"], str) or not isinstance(item["expected_output"], str):
            raise InvalidFormatError("Testcase stdin/stdout phải có input và expected_output dạng chuỗi")
        return {
            "input": item["input"],
            "expected_output": item["expected_output"],
            "is_sample": item.get("is_sample", False),
            "input_type": LEGACY_INPUT,
            "expected_output_type": LEGACY_OUTPUT,
        }
    if (input_type, output_type) != (JSON_ARGUMENTS, JSON_VALUE):
        raise InvalidFormatError("Định dạng testcase không được hỗ trợ")
    if not isinstance(item["input"], list):
        raise InvalidFormatError("Testcase JSON phải có input là mảng các tham số function")
    return {
        "input": encode_json(item["input"]),
        "expected_output": encode_json(item["expected_output"]),
        "is_sample": item.get("is_sample", False),
        "input_type": JSON_ARGUMENTS,
        "expected_output_type": JSON_VALUE,
    }


def testcase_to_api_values(testcase: Any) -> dict[str, Any]:
    return {
        "input": decode_testcase_value(testcase.input, testcase.input_type),
        "expected_output": decode_testcase_value(
            testcase.expected_output, testcase.expected_output_type
        ),
        "input_type": testcase.input_type,
        "expected_output_type": testcase.expected_output_type,
    }
