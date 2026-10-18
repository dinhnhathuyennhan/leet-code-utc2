from fastapi import APIRouter, Depends
from sqlmodel import Session
from starlette import status
from starlette.responses import JSONResponse

from app.core.database import get_session
from app.core.dependencies import Role, require_role, get_current_user
from app.modules.courses.schemas import CourseResponse
from app.modules.lessons.schemas import LessonCreateRequest, LessonDetailResponse, LessonUpdateRequest, \
    LessonProblemAttachRequest, LessonDuplicateRequest, LessonReorderRequest
from app.modules.lessons import service as lesson_service
from app.models import User

router = APIRouter(tags=["lesson"])


@router.post("/courses/{course_id}/lessons", response_model=CourseResponse,
             status_code=status.HTTP_201_CREATED)
def create_lesson_route(
    course_id: str, data: LessonCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> CourseResponse:
    return lesson_service.create_lesson(session, course_id, data, current_user)


@router.patch("/courses/{course_id}/lessons/reorder", response_model=CourseResponse)
def reorder_lessons_route(
    course_id: str,
    data: LessonReorderRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> CourseResponse:
    return lesson_service.reorder_lessons(session, course_id, data, current_user)


@router.post(
    "/courses/{course_id}/lessons/{lesson_id}/duplicate",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def duplicate_lesson_route(
    course_id: str,
    lesson_id: int,
    data: LessonDuplicateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> CourseResponse:
    return lesson_service.duplicate_lesson(
        session, course_id, lesson_id, data, current_user
    )


@router.get(
    "/courses/{course_id}/lessons/{lesson_id}",
    response_model=LessonDetailResponse,
)
def get_lesson_detail_route(
    course_id: str, lesson_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LessonDetailResponse | JSONResponse:
    detail = lesson_service.get_lesson_detail(session, course_id, lesson_id, current_user)
    if current_user.role_id == Role.STUDENT:
        return JSONResponse(
            content=detail.model_dump(
                mode="json",
                exclude={
                    "submitted_students": True,
                    "total_students": True,
                    "stats": True,
                    "alert": True,
                    "exercises": {"__all__": {"submitted_count": True}},
                },
            )
        )
    return detail


@router.patch("/courses/{course_id}/lessons/{lesson_id}", response_model=CourseResponse)
def update_lesson_route(
    course_id: str, lesson_id: int, data: LessonUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> CourseResponse:
    return lesson_service.update_lesson(session, course_id, lesson_id, data, current_user)


@router.post(
    "/courses/{course_id}/lessons/{lesson_id}/problems",
    response_model=CourseResponse,
)
def add_problems_to_lesson_route(
    course_id: str,
    lesson_id: int,
    data: LessonProblemAttachRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> CourseResponse:
    return lesson_service.add_problems_to_lesson(
        session, course_id, lesson_id, data.problem_ids, current_user
    )


@router.delete("/courses/{course_id}/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson_route(
    course_id: str, lesson_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    lesson_service.delete_lesson(session, course_id, lesson_id, current_user)