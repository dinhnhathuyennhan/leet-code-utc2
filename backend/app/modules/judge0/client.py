import asyncio
import time

import httpx

from app.core import config


class Judge0Error(Exception):
    """Lỗi khi giao tiếp với Judge0."""


class Judge0Client:
    """Client gọi Judge0 để chạy thử code từ trang Cấu hình của admin.

    Judge0 Community Edition **không hỗ trợ** tham số `wait=true`
    (trả `400 {"error":"wait not allowed"}`). Vì vậy phải theo mô hình
    submit -> nhận token -> poll `GET /submissions/{token}` cho tới khi
    bài chạy xong, giống `app/modules/submissions/judge0/judge0_client.py`.
    """

    def __init__(self):
        self.base_url = config.JUDGE0_URL
        self.api_token = config.JUDGE0_AUTH_TOKEN

    def _headers(self) -> dict[str, str]:
        return {"X-Auth-Token": self.api_token} if self.api_token else {}

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

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/submissions",
                    params={"base64_encoded": "false"},
                    json=payload,
                    headers=self._headers(),
                )
                response.raise_for_status()
                token = response.json()["token"]

                return await self._wait_for_result(client, token)
        except httpx.TimeoutException as exc:
            raise Judge0Error("Judge0 không phản hồi kịp thời.") from exc

        except httpx.HTTPStatusError as exc:
            raise Judge0Error(
                f"Judge0 trả về HTTP {exc.response.status_code}."
            ) from exc

        except (httpx.RequestError, ValueError, KeyError) as exc:
            raise Judge0Error(
                "Không thể nhận kết quả hợp lệ từ Judge0."
            ) from exc

    async def _wait_for_result(
        self, client: httpx.AsyncClient, token: str
    ) -> dict:
        """Poll kết quả tới khi Judge0 chạy xong (status.id khác 1 và 2)."""
        deadline = time.monotonic() + config.JUDGE0_HTTP_TIMEOUT_SECONDS * 3
        while True:
            response = await client.get(
                f"{self.base_url}/submissions/{token}",
                params={"base64_encoded": "false"},
                headers=self._headers(),
            )
            response.raise_for_status()
            result = response.json()
            status = result.get("status") or {}
            # 1 = In Queue, 2 = Processing — vẫn đang chạy.
            if status.get("id") not in (1, 2):
                return result
            if time.monotonic() >= deadline:
                raise Judge0Error("Judge0 chạy quá thời gian cho phép.")
            await asyncio.sleep(config.JUDGE0_POLL_INTERVAL_SECONDS)
