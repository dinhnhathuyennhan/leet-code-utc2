import os

import httpx

from app.modules.ai_review.prompts import SYSTEM_PROMPT
from app.modules.ai_review.schemas import (
    AIReviewRequest,
    AIReviewResponse,
)


class AIReviewService:
    @staticmethod
    async def review(data: AIReviewRequest) -> AIReviewResponse:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
        proxy = os.getenv("TS_PROXY_URL")

        payload = {
            "model": model,
            "system": SYSTEM_PROMPT,
            "prompt": (
                f"Language: {data.language}\n"
                f"Analyze the following code:\n"
                f"<code>\n{data.code}\n</code>"
            ),
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
