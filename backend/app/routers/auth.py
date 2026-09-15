import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session

from app.db import get_session
from app.dependencies import get_current_user
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse
from app.services.auth_service import (
    InvalidCredentialsError,
    SamePasswordError,
    WrongCurrentPasswordError,
)
from app.services.auth_service import (
    change_password as change_password_service,
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
        httponly=True,
        path="/auth",
        max_age=REFRESH_TOKEN_MAX_AGE_SECONDS,
    )


@router.post("/auth/login", response_model=LoginResponse)
def login(
    data: LoginRequest, response: Response, session: Session = Depends(get_session)
):
    try:
        result, refresh_token = login_service(session, data)
    except InvalidCredentialsError as err:
        raise HTTPException(status_code=401, detail=str(err)) from err

    _set_refresh_token_cookie(response, refresh_token)
    return result


@router.post("/auth/change-password", response_model=LoginResponse)
def change_password(
    data: ChangePasswordRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        result, refresh_token = change_password_service(session, current_user, data)
    except WrongCurrentPasswordError as err:
        raise HTTPException(status_code=401, detail=str(err)) from err
    except SamePasswordError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    _set_refresh_token_cookie(response, refresh_token)
    return result
