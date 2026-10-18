from fastapi import APIRouter, Depends, Query, Response
from sqlmodel import Session
from starlette import status

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_role, Role
from app.models import User
from app.modules.problems.schemas import ProblemDetailResponse, ProblemTestcaseUpdate
from app.modules.testcases.schemas import TestcaseListResponse, TestcasePreviewRequest, TestcasePreviewResponse, \
    TestcaseUpdateRequest, TestcaseBatchRequest
from app.modules.testcases import service as testcase_service
router = APIRouter(tags=["testcases"])
BASE = "/courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/testcases"
EXPORT_MEDIA_TYPES = {"json": "application/json", "zip": "application/zip"}


@router.get(BASE, response_model=TestcaseListResponse)
def list_testcases_route(
    course_id: str, lesson_id: int, problem_id: int,
    is_sample: bool | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TestcaseListResponse:
    return testcase_service.list_testcases(
        session, course_id, lesson_id, problem_id, is_sample, current_user
    )


@router.post(BASE, response_model=ProblemDetailResponse)
def add_testcase_route(
    course_id: str, lesson_id: int, problem_id: int, data: ProblemTestcaseUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> ProblemDetailResponse:
    return testcase_service.add_testcase(
        session, course_id, lesson_id, problem_id, data, current_user
    )


# Các route tĩnh (/download, /preview, /batch) phải khai báo TRƯỚC /{testcase_id}
@router.get(BASE + "/download")
def download_testcases_route(
    course_id: str, lesson_id: int, problem_id: int,
    format: str = Query(default="json"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> Response:
    content = testcase_service.export_testcases(
        session, course_id, lesson_id, problem_id, format, current_user
    )
    return Response(
        content=content,
        media_type=EXPORT_MEDIA_TYPES[format],
        headers={
            "Content-Disposition": f'attachment; filename="testcases_{problem_id}.{format}"'
        },
    )


@router.post(BASE + "/preview", response_model=TestcasePreviewResponse)
def preview_testcases_route(
    data: TestcasePreviewRequest,
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> TestcasePreviewResponse:
    return testcase_service.preview_testcases(data)


@router.patch(BASE + "/batch", response_model=ProblemDetailResponse)
def batch_update_sample_route(
    course_id: str, lesson_id: int, problem_id: int, data: TestcaseBatchRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> ProblemDetailResponse:
    return testcase_service.batch_update_sample(
        session, course_id, lesson_id, problem_id, data, current_user
    )


@router.patch(BASE + "/{testcase_id}", response_model=ProblemDetailResponse)
def update_testcase_route(
    course_id: str, lesson_id: int, problem_id: int, testcase_id: int,
    data: TestcaseUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> ProblemDetailResponse:
    return testcase_service.update_testcase(
        session, course_id, lesson_id, problem_id, testcase_id, data, current_user
    )


@router.delete(BASE + "/{testcase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_testcase_route(
    course_id: str, lesson_id: int, problem_id: int, testcase_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    testcase_service.delete_testcase(
        session, course_id, lesson_id, problem_id, testcase_id, current_user
    )
