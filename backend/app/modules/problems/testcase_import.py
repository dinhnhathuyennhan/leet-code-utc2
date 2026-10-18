import io
import json
import zipfile

from app.core.exceptions import InvalidFormatError

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
        normalized.append({
            "input": str(item["input"]),
            "expected_output": str(item["expected_output"]),
            "is_sample": bool(item.get("is_sample", False)),
            "input_type": str(item.get("input_type", "stdin")),
            "expected_output_type": str(item.get("expected_output_type", "stdout")),
        })
    return normalized
