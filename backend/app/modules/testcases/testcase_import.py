import io
import json
import zipfile

from app.core.exceptions import InvalidFormatError
from app.modules.testcases.testcase_format import (
    JSON_ARGUMENTS,
    JSON_VALUE,
    LEGACY_INPUT,
    LEGACY_OUTPUT,
    encode_json,
)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_UNZIPPED_BYTES = 20 * 1024 * 1024


def parse_testcases(filename: str, raw: bytes) -> list[dict]:
    if len(raw) > MAX_UPLOAD_BYTES:
        raise InvalidFormatError("File testcase quá lớn (tối đa 5MB)")
    try:
        if filename.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                infos = [i for i in archive.infolist()
                         if i.filename.lower().endswith(".json") and not i.is_dir()]
                if not infos:
                    raise InvalidFormatError("File ZIP không chứa file JSON testcase")
                if sum(i.file_size for i in infos) > MAX_UNZIPPED_BYTES:
                    raise InvalidFormatError("Nội dung giải nén quá lớn")
                payloads = [json.loads(archive.read(i).decode("utf-8")) for i in infos]
            payload = next(
                (p for p in payloads if isinstance(p, dict) and "testcases" in p), payloads[0]
            )
        else:
            payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        raise InvalidFormatError("File testcase phải là JSON hợp lệ hoặc ZIP chứa JSON") from error

    items = payload.get("testcases", payload) if isinstance(payload, dict) else payload
    if not isinstance(items, list) or not items:
        raise InvalidFormatError("Danh sách testcase không hợp lệ hoặc đang rỗng")

    normalized = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or "input" not in item or "expected_output" not in item:
            raise InvalidFormatError(f"Testcase #{index} thiếu input hoặc expected_output")
        is_sample = item.get("is_sample", False)
        if not isinstance(is_sample, bool):
            raise InvalidFormatError(f"Testcase #{index}: is_sample phải là true hoặc false")
        input_type = item.get("input_type", JSON_ARGUMENTS)
        expected_output_type = item.get("expected_output_type", JSON_VALUE)
        if (input_type, expected_output_type) == (LEGACY_INPUT, LEGACY_OUTPUT):
            if not isinstance(item["input"], str) or not isinstance(item["expected_output"], str):
                raise InvalidFormatError(f"Testcase #{index}: stdin/stdout phải có input và output dạng chuỗi")
        elif (input_type, expected_output_type) == (JSON_ARGUMENTS, JSON_VALUE):
            if not isinstance(item["input"], list):
                raise InvalidFormatError(f"Testcase #{index}: input phải là mảng các tham số function")
            try:
                encode_json(item["input"])
                encode_json(item["expected_output"])
            except InvalidFormatError as error:
                raise InvalidFormatError(f"Testcase #{index}: giá trị JSON không hợp lệ") from error
        else:
            raise InvalidFormatError(f"Testcase #{index}: cặp input_type/expected_output_type không được hỗ trợ")
        normalized.append({
            "input": item["input"],
            "expected_output": item["expected_output"],
            "is_sample": is_sample,
            "input_type": input_type,
            "expected_output_type": expected_output_type,
        })
    return normalized
