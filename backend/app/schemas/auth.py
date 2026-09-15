from pydantic import BaseModel, EmailStr, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Mật khẩu không được trống")
        if len(v) < 8:
            raise ValueError("Mật khẩu ít nhất phải 8 ký tự")
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
        # Hiện tại config độ mạnh password > 8 ký tự (Sau có điều chỉnh sẽ sửa thêm)
        if len(v) < 8:
            raise ValueError("Mật khẩu mới phải có ít nhất 8 ký tự")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_match(cls, v: str, info) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Mật khẩu xác nhận không khớp với mật khẩu mới")
        return v
