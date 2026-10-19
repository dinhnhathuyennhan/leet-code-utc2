from fastapi import APIRouter, Depends, File, UploadFile
from sqlmodel import Session
from starlette import status

from app.core.database import get_session
from app.core.dependencies import Role, get_current_user, require_role
from app.modules.problems.schemas import ProblemDetailResponse, ProblemUpdateRequest
from app.modules.problems import service as problem_service
from app.modules.problems.testcase_import import MAX_UPLOAD_BYTES, parse_testcases
from app.models import User

router = APIRouter(tags=["problem"])
BASE = "/courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}"


@router.get(BASE, response_model=ProblemDetailResponse)
def get_problem_detail_route(
    course_id: str, lesson_id: int, problem_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ProblemDetailResponse:
    return problem_service.get_problem_detail(session, course_id, lesson_id, problem_id, current_user)


@router.patch(BASE, response_model=ProblemDetailResponse)
def update_problem_route(
    course_id: str, lesson_id: int, problem_id: int, data: ProblemUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> ProblemDetailResponse:
    return problem_service.update_problem(session, course_id, lesson_id, problem_id, data, current_user)


@router.delete(BASE, status_code=status.HTTP_204_NO_CONTENT)
def delete_problem_route(
    course_id: str, lesson_id: int, problem_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    problem_service.delete_problem(session, course_id, lesson_id, problem_id, current_user)


@router.post(BASE + "/testcases/upload", response_model=ProblemDetailResponse)
def upload_problem_testcases_route(
    course_id: str, lesson_id: int, problem_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> ProblemDetailResponse:
    raw = file.file.read(MAX_UPLOAD_BYTES + 1)           # đọc có giới hạn
    items = parse_testcases(file.filename or "", raw)
    return problem_service.replace_testcases(session, course_id, lesson_id, problem_id, items, current_user)
