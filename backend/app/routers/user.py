from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas.user import CreateStudentRequest, CreateTeacherRequest, UserResponse
from app.services.user_service import (
    create_student,
    create_teacher,
    user_response,
)

router = APIRouter()


@router.post("/teachers", response_model=UserResponse)
def create_teacher_route(
    data: CreateTeacherRequest,
    session: Session = Depends(get_session),
):
    teacher = create_teacher(session, data)
    return user_response(teacher)


@router.post("/students", response_model=UserResponse)
def create_student_route(
    data: CreateStudentRequest,
    session: Session = Depends(get_session),
):
    student = create_student(session, data)
    return user_response(student)
