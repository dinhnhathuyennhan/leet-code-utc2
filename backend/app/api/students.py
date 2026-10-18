from fastapi import APIRouter, Depends, File, UploadFile
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import Role, require_role
from app.modules.students.schemas import StudentImportResponse
from app.modules.students.service import MAX_IMPORT_FILE_BYTES, import_students
from app.models import User

router = APIRouter()


@router.post(
    "/students/import",
    response_model=StudentImportResponse,
    status_code=201,
)
def import_students_route(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    # Đọc tối đa giới hạn + 1 byte: đủ để service biết file vượt giới hạn
    # mà không phải nạp cả file quá lớn vào bộ nhớ
    contents = file.file.read(MAX_IMPORT_FILE_BYTES + 1)
    return import_students(session, contents, file.filename or "")
