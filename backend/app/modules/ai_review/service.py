import os

import httpx

from app.modules.ai_review.prompts import SYSTEM_PROMPT
from app.modules.ai_review.schemas import (
    AIConnectionResponse,
    AIReviewRequest,
    AIReviewResponse,
)


class AIReviewService:
    @staticmethod
    async def test_connection() -> AIConnectionResponse:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
        async with httpx.AsyncClient(proxy=os.getenv("TS_PROXY_URL") or None,
                                     timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            response = await client.get(f"{base_url}/api/tags")
            response.raise_for_status()
            models = response.json()["models"]
        return AIConnectionResponse(connected=True, model=model,
                                    model_available=any(item.get("name") == model for item in models))

    @staticmethod
    async def review(data: AIReviewRequest, judge_summary: str | None = None) -> AIReviewResponse:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
        proxy = os.getenv("TS_PROXY_URL")

        payload = {
            "model": model,
            "system": SYSTEM_PROMPT,
            "prompt": (f"Language: {data.language}\n"
                       + (f"Judge0 result: {judge_summary}\n" if judge_summary else "")
                       + f"Analyze the following code:\n<code>\n{data.code}\n</code>"),
            "stream": False,
            "format": AIReviewResponse.model_json_schema(),
            "options": {
                "temperature": 0.1,
                "num_ctx": 4096,
            },
        }

        async with httpx.AsyncClient(
            proxy=proxy or None,
            timeout=httpx.Timeout(180.0, connect=20.0),
        ) as client:
            response = await client.post(f"{base_url}/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()

        return AIReviewResponse.model_validate_json(result["response"])
