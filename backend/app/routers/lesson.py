from fastapi import APIRouter, Depends
from sqlmodel import Session
from starlette import status

from app.db import get_session
from app.dependencies import Role, require_role
from app.schemas.course import CourseResponse
from app.schemas.lesson import LessonCreateRequest, LessonDetailResponse, LessonUpdateRequest
from app.services import lesson_service
from models import User

router = APIRouter(tags=["lesson"])


@router.post("/courses/{course_id}/lessons", response_model=CourseResponse,
             status_code=status.HTTP_201_CREATED)
def create_lesson_route(
    course_id: str, data: LessonCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> CourseResponse:
    return lesson_service.create_lesson(session, course_id, data, current_user)


@router.get("/courses/{course_id}/lessons/{lesson_id}", response_model=LessonDetailResponse)
def get_lesson_detail_route(
    course_id: str, lesson_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> LessonDetailResponse:
    return lesson_service.get_lesson_detail(session, course_id, lesson_id, current_user)


@router.patch("/courses/{course_id}/lessons/{lesson_id}", response_model=CourseResponse)
def update_lesson_route(
    course_id: str, lesson_id: int, data: LessonUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> CourseResponse:
    return lesson_service.update_lesson(session, course_id, lesson_id, data, current_user)


@router.delete("/courses/{course_id}/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson_route(
    course_id: str, lesson_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    lesson_service.delete_lesson(session, course_id, lesson_id, current_user)
