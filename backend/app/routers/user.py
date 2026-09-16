import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.dependencies import get_current_user
from app.schemas.user import UserResetPasswordResponse
from app.services.user_service import NotAllowedToResetError, UserNotFoundError
from app.services.user_service import reset_password as reset_password_service
from models import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/users/{user_id}/reset-password", response_model=UserResetPasswordResponse
)
def reset_password_route(
    user_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        target_user_id, temporary_password = reset_password_service(
            session, current_user, user_id
        )
    except UserNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except NotAllowedToResetError as err:
        raise HTTPException(status_code=403, detail=str(err)) from err

    return UserResetPasswordResponse(
        user_id=target_user_id, temporary_password=temporary_password
    )
