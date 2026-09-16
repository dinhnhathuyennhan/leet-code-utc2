from pydantic import BaseModel, EmailStr


class StudentCreate(BaseModel):
    full_name: str
    email: EmailStr


class StudentCreatedResponse(BaseModel):
    user_id: str
    full_name: str
    email: str
    role_id: int
    temporary_password: str


class StudentImportCreatedRow(BaseModel):
    user_id: str
    full_name: str
    email: str
    temporary_password: str


class StudentImportErrorRow(BaseModel):
    row: int
    email: str | None
    reason: str


class StudentImportResponse(BaseModel):
    created: list[StudentImportCreatedRow]
    errors: list[StudentImportErrorRow]
