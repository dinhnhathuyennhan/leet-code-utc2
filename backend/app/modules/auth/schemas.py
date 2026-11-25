import string

from pydantic import BaseModel, field_validator

from app.core.exceptions import (
    EmptyFieldError,
    PasswordMismatchError,
    WeakPasswordError,
)
from app.core.utils.validation import AppEmailStr


class LoginRequest(BaseModel):
    email: AppEmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or not v.strip():
            raise EmptyFieldError("Mật khẩu không được trống")
        if len(v) < 8:
            raise WeakPasswordError("Mật khẩu ít nhất phải 8 ký tự")
        return v


class UserResponse(BaseModel):
    user_id: str
    full_name: str
    email: str
    role_id: int
    must_change_password: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_strength(cls, v: str) -> str:
        # Khớp với changePasswordSchema ở frontend (validate-field-form.ts): chữ hoa và
        # chữ số chỉ tính ASCII ([A-Z], [0-9]); str.isupper/isdigit nhận cả "Đ", "²"
        if len(v) < 8:
            raise WeakPasswordError("Mật khẩu mới phải có ít nhất 8 ký tự")
        if not any(c in string.ascii_uppercase for c in v):
            raise WeakPasswordError("Mật khẩu mới cần ít nhất 1 chữ cái viết hoa")
        if not any(c in string.digits for c in v):
            raise WeakPasswordError("Mật khẩu mới cần ít nhất 1 chữ số")
        if not any(not c.isalnum() and not c.isspace() for c in v):
            raise WeakPasswordError("Mật khẩu mới cần ít nhất 1 ký tự đặc biệt")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_match(cls, v: str, info) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise PasswordMismatchError("Mật khẩu xác nhận không khớp với mật khẩu mới")
        return v

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
