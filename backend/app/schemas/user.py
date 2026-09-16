from pydantic import BaseModel


class UserResetPasswordResponse(BaseModel):
    user_id: str
    temporary_password: str
