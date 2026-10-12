from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.dependencies import Role, require_role
from app.schemas.class_ import ClassResponse, ClassStudentResponse
from app.services import class_service
from models import User

router = APIRouter(tags=["class"])


@router.get("/classes", response_model=list[ClassResponse])
def get_classes_route(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> list[ClassResponse]:
    return class_service.get_classes(session)


@router.get("/classes/{class_id}/students", response_model=list[ClassStudentResponse])
def get_class_students_route(
    class_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> list[ClassStudentResponse]:
    return class_service.get_class_students(session, class_id)
