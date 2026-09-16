import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.db import get_session
from app.dependencies import Role, require_role
from app.schemas.student import (
    StudentCreate,
    StudentCreatedResponse,
    StudentImportResponse,
)
from app.services.student_service import (
    EmailAlreadyExistsError,
    EmptyExcelFileError,
    ExcelFileTooLargeError,
    InvalidExcelFormatError,
)
from app.services.student_service import create_student as create_student_service
from app.services.student_service import (
    import_students as import_students_service,
)
from models import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/students", response_model=StudentCreatedResponse, status_code=201)
def create_student_route(
    data: StudentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(
        require_role(Role.ADMIN, Role.TEACHER)
    ),
):
    try:
        student, temporary_password = create_student_service(session, data)
    except EmailAlreadyExistsError as err:
        raise HTTPException(status_code=400, detail="Email đã tồn tại") from err

    return StudentCreatedResponse(
        user_id=student.user_id,
        full_name=student.full_name,
        email=student.email,
        role_id=student.role_id,
        temporary_password=temporary_password,
    )


@router.post("/students/import", response_model=StudentImportResponse, status_code=201)
def import_students_route(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(
        require_role(Role.ADMIN, Role.TEACHER)
    ),
):
    contents = file.file.read()
    try:
        return import_students_service(session, contents, file.filename or "")
    except InvalidExcelFormatError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    except (EmptyExcelFileError, ExcelFileTooLargeError) as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
