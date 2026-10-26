from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.dependencies import Role, require_role
from app.modules.judge0.client import Judge0Client, Judge0Error

router = APIRouter(prefix="/judge0", tags=["judge0"])

class Judge0RunRequest(BaseModel):
    source_code: str = Field(min_length=1, max_length=20000)
    language_id: int
    stdin: str = Field(default="", max_length=10000)
    expected_output: str | None = Field(default=None, max_length=10000)


@router.post("/test")
async def test_judge0(
    _current_user=Depends(require_role(Role.ADMIN)),
):
    try:
        client = Judge0Client()

        result = await client.submit(
            source_code='print("Hello Judge0")',
            language_id=71,
        )

        return {
            "message": "Judge0 connection test",
            "stdout": result.get("stdout"),
            "stderr": result.get("stderr"),
            "status": result.get("status"),
            "compile_output": result.get("compile_output"),
        }

    except Judge0Error as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

@router.post("/run")
async def run_code(
    data: Judge0RunRequest,
    _current_user=Depends(require_role(Role.ADMIN)),
):
    try:
        client = Judge0Client()

        result = await client.submit(
            source_code=data.source_code,
            language_id=data.language_id,
            stdin=data.stdin,
            expected_output=data.expected_output,
        )

        return {
            "stdout": result.get("stdout"),
            "stderr": result.get("stderr"),
            "compile_output": result.get("compile_output"),
            "status": result.get("status"),
            "time": result.get("time"),
            "memory": result.get("memory"),
        }

    except Judge0Error as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
