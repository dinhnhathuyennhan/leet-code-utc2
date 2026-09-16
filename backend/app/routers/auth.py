import logging

from fastapi import APIRouter, Depends, Response, Request
from sqlmodel import Session

from app.db import get_session
from app.dependencies import get_current_user
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, AccessTokenResponse
from app.services.auth_service import (
    change_password as change_password_service,
    refresh_access_token as refresh_access_token_service
)
from app.services.auth_service import (
    login as login_service,
)
from models import User

router = APIRouter()
logger = logging.getLogger(__name__)

REFRESH_TOKEN_MAX_AGE_SECONDS = 7 * 24 * 60 * 60  # khớp REFRESH_TOKEN_EXPIRE_DAYS


def _set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True, # không cho phép frontend đọc được refresh_token bằng JS
        path="/auth",
        max_age=REFRESH_TOKEN_MAX_AGE_SECONDS,
    )

def _clear_refresh_token_cookie(response: Response) -> None:
    response.delete_cookie(key="refresh_token", path="/auth")

@router.post("/auth/login", response_model=LoginResponse)
def login(
    data: LoginRequest, response: Response, session: Session = Depends(get_session)
):
    result, refresh_token = login_service(session, data)
    _set_refresh_token_cookie(response, refresh_token)
    return result


@router.post("/auth/change-password", response_model=LoginResponse)
def change_password(
    data: ChangePasswordRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    result, refresh_token = change_password_service(session, current_user, data)
    _set_refresh_token_cookie(response, refresh_token)
    return result

@router.post("/auth/logout", status_code=204)
def logout(
    response: Response
):
    _clear_refresh_token_cookie(response)

@router.post("/auth/refresh-access-token", response_model=AccessTokenResponse)
def refresh_access_token(
        request: Request,
        session: Session = Depends(get_session),
):
    refresh_token = request.cookies.get("refresh_token")
    access_token = refresh_access_token_service(session, refresh_token)
    return AccessTokenResponse(access_token=access_token)