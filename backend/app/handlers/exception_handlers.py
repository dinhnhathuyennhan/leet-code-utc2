import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError
from app.schemas.error import ErrorResponse
from app.services.auth_service import SessionRevokedError

logger = logging.getLogger(__name__)


# tự định nghĩa errorResponse của system
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    body = ErrorResponse(error_code=exc.error_code, message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


# error ngoài phạm vi các exception đã định nghĩa trước đó
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log đầy đủ để debug nội bộ, không lộ chi tiết ra client
    logger.exception(f"Unhandled error at {request.url.path}")
    body = ErrorResponse(
        error_code="INTERNAL_ERROR",
        message="Đã có lỗi xảy ra, vui lòng thử lại sau.",
    )
    return JSONResponse(status_code=500, content=body.model_dump())

#xử lý riêng cho session revoked(refresh token hết hạn hoặc đã revoked)
async def session_revoked_handler(request: Request, exc: SessionRevokedError) -> JSONResponse:
    body = ErrorResponse(error_code=exc.error_code, message=exc.message)
    response = JSONResponse(status_code=exc.status_code, content=body.model_dump())
    response.delete_cookie(key="refresh_token", path="/auth")
    return response

# đăng ký globalExceptionHandler tự định nghĩa bởi system với FastAPI (đăng ký tại main)
def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(SessionRevokedError, session_revoked_handler)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
