from pydantic import BaseModel, EmailStr, Field, model_validator
from datetime import date

class CreateTeacherRequest(BaseModel):
    user_id: str
    full_name: str
    date_of_birth: date
    email: EmailStr
    avt_link: str | None = None
    password: str = Field(min_length=8)

class CreateStudentRequest(BaseModel):
    user_id: str
    full_name: str
    date_of_birth: date
    email: EmailStr
    avt_link: str | None = None
    password: str | None = None

    @model_validator(mode="after")
    def create_password(self):
        if self.password is None:
            self.password = (
                f"{self.date_of_birth.day:02d}"
                f"{self.date_of_birth.month:02d}"
                f"{self.date_of_birth.year}"
            )
        return self