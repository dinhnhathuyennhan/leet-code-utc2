
import httpx

from app.core import config


class Judge0Error(Exception):
    """Lỗi khi giao tiếp với Judge0."""


class Judge0Client:
    def __init__(self):
        self.base_url = config.JUDGE0_URL
        self.api_token = config.JUDGE0_AUTH_TOKEN

    async def submit(
        self,
        source_code: str,
        language_id: int,
        stdin: str = "",
        expected_output: str | None = None,
    ) -> dict:
        payload = {
            "source_code": source_code,
            "language_id": language_id,
            "stdin": stdin,
        }

        if expected_output is not None:
            payload["expected_output"] = expected_output

        headers = {
            "X-Auth-Token": self.api_token,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/submissions",
                    params={"base64_encoded": "false", "wait": "true"},
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException as exc:
            raise Judge0Error("Judge0 không phản hồi kịp thời.") from exc

        except httpx.HTTPStatusError as exc:
            raise Judge0Error(
                f"Judge0 trả về HTTP {exc.response.status_code}."
            ) from exc

        except (httpx.RequestError, ValueError) as exc:
            raise Judge0Error(
                "Không thể nhận kết quả hợp lệ từ Judge0."
            ) from exc
