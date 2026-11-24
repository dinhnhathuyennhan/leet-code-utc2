from fastapi import APIRouter, Depends
from sqlmodel import Session
from starlette import status

from app.core.database import get_session
from app.core.dependencies import Role, require_role
from app.modules.classrooms.schemas import (
    ClassResponse,
    ClassStudentResponse,
    CreateClassRequest,
    UpdateClassRequest,
)
from app.modules.classrooms.service import (
    create_class,
    delete_class,
    get_class,
    get_class_students,
    list_classes,
    update_class,
)
from app.models import User

router = APIRouter(tags=["class"])


@router.post(
    "/classes",
    response_model=ClassResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_class_route(
    data: CreateClassRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> ClassResponse:
    return create_class(session, data)


@router.get("/classes", response_model=list[ClassResponse])
def list_classes_route(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> list[ClassResponse]:
    return list_classes(session)


@router.get("/classes/{class_id}", response_model=ClassResponse)
def get_class_route(
    class_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> ClassResponse:
    return get_class(session, class_id)


@router.get("/classes/{class_id}/students", response_model=list[ClassStudentResponse])
def get_class_students_route(
    class_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> list[ClassStudentResponse]:
    return get_class_students(session, class_id)


@router.patch("/classes/{class_id}", response_model=ClassResponse)
def update_class_route(
    class_id: str,
    data: UpdateClassRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> ClassResponse:
    return update_class(session, class_id, data)


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class_route(
    class_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> None:
    delete_class(session, class_id)
