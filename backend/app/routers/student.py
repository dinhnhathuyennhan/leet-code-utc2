from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.schemas.student import StudentCreate
from app.services.student_service import EmailAlreadyExistsError, create_student

router = APIRouter()


@router.post("/students")
def create_student_route(data: StudentCreate, session: Session = Depends(get_session)):
    try:
        return create_student(session, data)
    except EmailAlreadyExistsError as err:
        raise HTTPException(status_code=400, detail="Email đã tồn tại") from err
