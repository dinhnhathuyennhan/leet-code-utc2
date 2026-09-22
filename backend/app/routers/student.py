import logging

from fastapi import APIRouter, Depends, File, UploadFile
from sqlmodel import Session

from app.db import get_session
from app.dependencies import Role, require_role
from app.schemas.student import StudentImportResponse
from app.services.student_service import import_students
from models import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/students/import",
    response_model=StudentImportResponse,
    status_code=201,
)
def import_students_route(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(
        require_role(Role.ADMIN, Role.TEACHER)
    ),
):
    contents = file.file.read()
    return import_students(session, contents, file.filename or "")
