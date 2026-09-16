from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.schemas.user import CreateStudentRequest, CreateTeacherRequest
from app.services.user_service import (
    DateOfBirthRequiredError,
    EmailAlreadyExistsError,
    create_student,
    create_teacher,
)

router = APIRouter()


@router.post("/teachers")
def create_teacher_route(
    data: CreateTeacherRequest,
    session: Session = Depends(get_session),
):
    try:
        teacher = create_teacher(session, data)
        return {"message": "Teacher created successfully", "teacher": teacher}
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except DateOfBirthRequiredError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/students")
def create_student_route(
    data: CreateStudentRequest,
    session: Session = Depends(get_session),
):
    try:
        student = create_student(session, data)
        return {"message": "Student created successfully", "student": student}
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except DateOfBirthRequiredError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
