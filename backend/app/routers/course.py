import logging

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from starlette import status

from app.db import get_session
from app.dependencies import Role, get_current_user, require_role
from app.schemas.course import (
    AddStudentToCourseRequest,
    AddStudentToCourseResponse,
    CourseResponse,
    CreateCourseRequest,
    GetStudentListResponse,
    StudentEnrollmentResponse,
    UpdateCourseRequest,
)
from app.services.course_service import (
    add_student_to_course as _add_student_to_course,
    create_course as _create_course,
    delete_student_from_course as _delete_student_from_course,
    get_course as _get_course,
    get_course_enrollments,
    get_courses as _get_courses,
    get_student_courses as _get_student_courses,
    get_student_enrollments as _get_student_enrollments,
    update_course as _update_course,
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
    term: str | None = Query(
        default=None,
        description=(
            "Lọc theo cột `term` (LIKE %term%). "
            "Ví dụ: 'HK1' hoặc '2024' đều match chuỗi con."
        ),
    ),
    search: str | None = Query(
        default=None,
        description="Tìm trong `course_id` hoặc `course_name` (LIKE %search%).",
    ),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[CourseResponse]:
    return _get_courses(
        session=session,
        current_user=current_user,
        term=term,
        search=search,
    )


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


# ─── Lỗi 7: Lấy danh sách lớp của 1 sinh viên ──────────────────────────────


@router.get(
    "/students/{student_id}/courses",
    response_model=list[CourseResponse],
)
def get_student_courses_route(
    student_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[CourseResponse]:
    """Trả về các lớp mà sinh viên đang học.

    Quyền:
        - ADMIN: xem tất cả.
        - TEACHER: chỉ xem SV enroll lớp do mình tạo.
        - STUDENT: chỉ xem của chính mình.
    """
    return _get_student_courses(
        session=session,
        student_id=student_id,
        current_user=current_user,
    )


# ─── Lỗi 8: Lấy danh sách enrollment của 1 sinh viên ───────────────────────


@router.get(
    "/students/{student_id}/enrollments",
    response_model=list[StudentEnrollmentResponse],
)
def get_student_enrollments_route(
    student_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[StudentEnrollmentResponse]:
    """Trả về các enrollment (kèm thông tin lớp) của sinh viên.

    Khác với `GET /students/{id}/courses` ở chỗ endpoint này trả cả
    ``enrollment_id`` (khóa chính của bảng enrollment) → client có thể
    dùng cho "Lịch sử đăng ký" hoặc để gọi API xoá enrollment sau này.
    """
    return _get_student_enrollments(
        session=session,
        student_id=student_id,
        current_user=current_user,
    )
