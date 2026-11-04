from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlmodel import Session
from starlette import status

from app.core.database import get_session
from app.core.dependencies import Role, get_current_user, require_role
from app.core.exceptions import InvalidFormatError
from app.modules.problems.schemas import AdminTestcaseMutation, ProblemDetailResponse, ProblemUpdateRequest, ProblemCreateRequest, \
    ProblemListResponse
from app.modules.problems import service as problem_service
from app.modules.testcases.testcase_import import MAX_UPLOAD_BYTES, parse_testcases
from app.models import User
from app.modules.submissions.judge0.schemas import CodeRequest, RunResponse, SubmitAcceptedResponse
from app.modules.submissions.judge0 import grading_queue, service as judge_service
router = APIRouter(tags=["problem"])
BASE = "/courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}"


@router.post("/problems", response_model=ProblemDetailResponse, status_code=status.HTTP_201_CREATED)
def create_bank_problem_route(
    data: ProblemCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> ProblemDetailResponse:
    return problem_service.create_bank_problem(session, data)


@router.get("/problems", response_model=ProblemListResponse)
def list_problems_route(
    q: str | None = None,
    level: str | None = None,
    course_id: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> ProblemListResponse:
    if level is not None and level not in ("easy", "medium", "hard"):
        raise InvalidFormatError("level chỉ được nhận một trong các giá trị: easy, medium, hard")
    return problem_service.list_problems(
        session, current_user, q=q, level=level, course_id=course_id,
        page=page, page_size=page_size,
    )

@router.get("/problems/{problem_id}", response_model=ProblemDetailResponse)
def get_bank_problem_route(
    problem_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> ProblemDetailResponse:
    return problem_service.get_bank_problem(session, problem_id, current_user)

@router.patch("/problems/{problem_id}", response_model=ProblemDetailResponse)
def update_bank_problem_route(
    problem_id: int, data: ProblemUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> ProblemDetailResponse:
    return problem_service.update_bank_problem(session, problem_id, data)

@router.delete("/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bank_problem_route(
    problem_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    problem_service.delete_bank_problem(session, problem_id)


@router.post("/problems/{problem_id}/testcases", response_model=ProblemDetailResponse)
def add_admin_testcase_route(
    problem_id: int, data: AdminTestcaseMutation,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> ProblemDetailResponse:
    return problem_service.add_admin_testcase(session, problem_id, data, current_user)


@router.put("/problems/{problem_id}/testcases/{testcase_id}", response_model=ProblemDetailResponse)
def update_admin_testcase_route(
    problem_id: int, testcase_id: int, data: AdminTestcaseMutation,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> ProblemDetailResponse:
    return problem_service.update_admin_testcase(session, problem_id, testcase_id, data, current_user)


@router.delete("/problems/{problem_id}/testcases/{testcase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_testcase_route(
    problem_id: int, testcase_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    problem_service.delete_admin_testcase(session, problem_id, testcase_id)


@router.post("/problems/{problem_id}/run-preview", response_model=RunResponse)
def run_admin_problem_preview_route(
    problem_id: int, data: CodeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> RunResponse:
    return judge_service.run_admin_preview(session, problem_id, data, current_user)


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

@router.post(BASE + "/run", response_model=RunResponse)
def run_code_route(
    course_id: str, lesson_id: int, problem_id: int, data: CodeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.STUDENT)),
) -> RunResponse:
    return judge_service.run(session, course_id, lesson_id, problem_id, data, current_user)


@router.post(BASE + "/submissions", response_model=SubmitAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_code_route(
        course_id: str, lesson_id: int, problem_id: int, data: CodeRequest,
        session: Session = Depends(get_session),
        current_user: User = Depends(require_role(Role.STUDENT)),
) -> SubmitAcceptedResponse:
    submission = judge_service.submit(session, course_id, lesson_id, problem_id, data, current_user)
    grading_queue.enqueue(submission.submission_id)
    return SubmitAcceptedResponse(submission_id=submission.submission_id, status=submission.status)

@router.post(
    "/{submission_id}/regrade",
    response_model=SubmitAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def regrade_submission_route(
    submission_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> SubmitAcceptedResponse:
    submission = judge_service.regrade(session, submission_id, current_user)
    return SubmitAcceptedResponse(submission_id=submission.submission_id, status=submission.status)
