from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.services.user_service import EmailAlreadyExistsError, create_teacher, create_student, DateOfBirthRequiredError
from app.schemas.user import CreateStudentRequest, CreateTeacherRequest

router = APIRouter()

@router.post("/teachers")
def create_teacher_route(data: CreateTeacherRequest, session: Session = Depends(get_session)):
    try:
        teacher = create_teacher(session, data)
        return {"message": "Teacher created successfully", "teacher": teacher}
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DateOfBirthRequiredError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/students")
def create_student_route(data: CreateStudentRequest, session: Session = Depends(get_session)):
    try:
        student = create_student(session, data)
        return {"message": "Student created successfully", "student": student}
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DateOfBirthRequiredError as e:
        raise HTTPException(status_code=400, detail=str(e))