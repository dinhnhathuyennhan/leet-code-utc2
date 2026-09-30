import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.schemas.error import ErrorResponse
from app.services.auth_service import SessionExpiredError, SessionRevokedError

logger = logging.getLogger(__name__)

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    body = ErrorResponse(error_code=exc.error_code, message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())

async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled error at {request.url.path}")
    body = ErrorResponse(
        error_code="INTERNAL_ERROR",
        message="Đã có lỗi xảy ra, vui lòng thử lại sau.",
    )
    return JSONResponse(status_code=500, content=body.model_dump())

_HTTP_ERROR_CODES = {
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    429: "TOO_MANY_REQUESTS",
}


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    error_code = _HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
    body = ErrorResponse(error_code=error_code, message=str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=body.model_dump(),
        headers=exc.headers,  # giữ WWW-Authenticate, Retry-After...
    )

async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    message = errors[0].get("msg") if errors else None
    if message and message.startswith("Value error, "):
        message = message.removeprefix("Value error, ")
    body = ErrorResponse(error_code="VALIDATION_ERROR", message=message or "Dữ liệu đầu vào không hợp lệ.")
    return JSONResponse(status_code=422, content=body.model_dump())

async def session_ended_handler(request: Request, exc: AppError) -> JSONResponse:
    body = ErrorResponse(error_code=exc.error_code, message=exc.message)
    response = JSONResponse(status_code=exc.status_code, content=body.model_dump())
    response.delete_cookie(key="refresh_token", path="/auth")
    return response

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(SessionRevokedError, session_ended_handler)
    app.add_exception_handler(SessionExpiredError, session_ended_handler)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)