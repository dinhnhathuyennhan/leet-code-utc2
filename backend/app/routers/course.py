import logging

from fastapi import APIRouter, Depends, File, UploadFile
from sqlmodel import Session
from starlette import status

from app.db import get_session
from app.dependencies import Role, get_current_user, require_role
from app.schemas.course import (
    AddStudentToCourseRequest,
    AddStudentToCourseResponse,
    AddClassToCourseRequest,
    AddClassToCourseResponse,
    ClassResponse,
    ClassStudentResponse,
    CourseResponse,
    CreateCourseRequest,
    GetStudentListResponse,
    LessonCreateRequest,
    LessonDetailResponse,
    LessonUpdateRequest,
    ProblemDetailResponse,
    ProblemUpdateRequest,
    UpdateCourseRequest,
)
from app.services.course_service import (
    add_student_to_course as _add_student_to_course,
    create_course as _create_course,
    delete_student_from_course as _delete_student_from_course,
    get_course as _get_course,
    get_course_enrollments,
    get_courses as _get_courses,
    create_lesson as _create_lesson,
    delete_lesson as _delete_lesson,
    get_lesson_detail as _get_lesson_detail,
    get_problem_detail as _get_problem_detail,
    update_problem as _update_problem,
    upload_problem_testcases as _upload_problem_testcases,
    update_lesson as _update_lesson,
    update_course as _update_course,
    add_class_to_course as _add_class_to_course,
    get_classes as _get_classes,
    get_class_students as _get_class_students,
)
from models import User

router = APIRouter(tags=["course"])
logger = logging.getLogger(__name__)


@router.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course_route(
    data: CreateCourseRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> CourseResponse:
    return _create_course(
        data=data,
        session=session,
        current_user=current_user,
    )


@router.get(
    "/courses",
    response_model=list[CourseResponse],
)
def get_courses_route(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[CourseResponse]:
    return _get_courses(session=session, current_user=current_user)


@router.get(
    "/courses/{course_id}",
    response_model=CourseResponse,
)
def get_course_route(
    course_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CourseResponse:
    return _get_course(session=session, course_id=course_id, current_user=current_user)


@router.patch(
    "/courses/{course_id}",
    response_model=CourseResponse,
)
def update_course_route(
    course_id: str,
    data: UpdateCourseRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> CourseResponse:
    return _update_course(
        course_id=course_id,
        data=data,
        session=session,
        current_user=current_user,
    )


@router.post(
    "/courses/{course_id}/enrollments",
    response_model=AddStudentToCourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_student_to_course(
    data: AddStudentToCourseRequest,
    course_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> AddStudentToCourseResponse:
    return _add_student_to_course(
        student_id=data.student_id,
        course_id=course_id,
        session=session,
        current_user=current_user,
    )


# SỬA: Một request thêm toàn bộ sinh viên của lớp, thay cho N request từng sinh viên.
@router.post(
    "/courses/{course_id}/enrollments/class",
    response_model=AddClassToCourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_class_to_course(
    course_id: str,
    data: AddClassToCourseRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> AddClassToCourseResponse:
    return _add_class_to_course(session, course_id, data.class_id, current_user)


@router.delete(
    "/courses/{course_id}/enrollments/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_student_from_course(
    student_id: str,
    course_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    _delete_student_from_course(
        student_id=student_id,
        course_id=course_id,
        session=session,
        current_user=current_user,
    )


@router.get(
    "/courses/{course_id}/enrollments",
    response_model=list[GetStudentListResponse],
)
def get_course_enrollments_route(
    course_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return get_course_enrollments(session, course_id, current_user)


# SỬA: API danh sách lớp hành chính phục vụ dropdown thêm sinh viên.
@router.get("/classes", response_model=list[ClassResponse])
def get_classes_route(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> list[ClassResponse]:
    return _get_classes(session, current_user)


# SỬA: API sinh viên theo lớp, dùng một query để hiển thị danh sách chọn.
@router.get("/classes/{class_id}/students", response_model=list[ClassStudentResponse])
def get_class_students_route(
    class_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> list[ClassStudentResponse]:
    return _get_class_students(session, class_id, current_user)


# SỬA: API tạo buổi học; chỉ giáo viên chủ lớp hoặc admin được phép thao tác.
@router.post(
    "/courses/{course_id}/lessons",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson_route(
    course_id: str,
    data: LessonCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> CourseResponse:
    return _create_lesson(session, course_id, data, current_user)


# SỬA: API chi tiết buổi học để nút "Vào xem chi tiết" không còn gọi endpoint giả.
@router.get(
    "/courses/{course_id}/lessons/{lesson_id}",
    response_model=LessonDetailResponse,
)
def get_lesson_detail_route(
    course_id: str,
    lesson_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> LessonDetailResponse:
    return _get_lesson_detail(session, course_id, lesson_id, current_user)


# SỬA: API chi tiết bài tập để trang buổi học có thể mở nội dung đề, testcase và code mẫu.
@router.get(
    "/courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}",
    response_model=ProblemDetailResponse,
)
def get_problem_detail_route(
    course_id: str,
    lesson_id: int,
    problem_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ProblemDetailResponse:
    return _get_problem_detail(session, course_id, lesson_id, problem_id, current_user)


# SỬA: API lưu nội dung bài tập đang được chọn trong màn hình Soạn bài tập.
@router.patch(
    "/courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}",
    response_model=ProblemDetailResponse,
)
def update_problem_route(
    course_id: str,
    lesson_id: int,
    problem_id: int,
    data: ProblemUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> ProblemDetailResponse:
    return _update_problem(session, course_id, lesson_id, problem_id, data, current_user)


# SỬA: API nhận ZIP/JSON testcase để màn hình Soạn bài tập hiển thị và lưu dữ liệu thật.
@router.post(
    "/courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/testcases/upload",
    response_model=ProblemDetailResponse,
)
def upload_problem_testcases_route(
    course_id: str,
    lesson_id: int,
    problem_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> ProblemDetailResponse:
    return _upload_problem_testcases(session, course_id, lesson_id, problem_id, file, current_user)


# SỬA: API sửa buổi học, đồng bộ tiêu đề/thời gian/danh sách bài tập với giao diện.
@router.patch(
    "/courses/{course_id}/lessons/{lesson_id}",
    response_model=CourseResponse,
)
def update_lesson_route(
    course_id: str,
    lesson_id: int,
    data: LessonUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
) -> CourseResponse:
    return _update_lesson(session, course_id, lesson_id, data, current_user)


# SỬA: API xoá buổi học để menu thao tác không chỉ là giao diện giả.
@router.delete(
    "/courses/{course_id}/lessons/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_lesson_route(
    course_id: str,
    lesson_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role(Role.ADMIN, Role.TEACHER)),
):
    _delete_lesson(session, course_id, lesson_id, current_user)
