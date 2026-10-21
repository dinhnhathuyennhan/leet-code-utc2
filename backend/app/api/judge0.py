
from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import Role, require_role
from app.modules.judge0.client import Judge0Client, Judge0Error

router = APIRouter(prefix="/judge0", tags=["judge0"])


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
