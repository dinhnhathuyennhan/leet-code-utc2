import string
import unicodedata

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
    # MSSV, chỉ Sinh viên có; FE dùng để báo trước luật "không chứa MSSV" khi đổi mật khẩu
    student_code: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Đúng tập ký tự mà `\s` của JavaScript khớp (WhiteSpace + LineTerminator, ECMAScript).
# Không dùng str.isspace(): nó coi \x1c-\x1f, \x85 là khoảng trắng nhưng không nhận \ufeff.
_JS_WHITESPACE = frozenset(
    "\t\n\v\f\r \u00a0\u1680\u2028\u2029\u202f\u205f\u3000\ufeff"
) | frozenset(chr(c) for c in range(0x2000, 0x200B))


def _is_special_char(c: str) -> bool:
    r"""Khớp `/[^\p{L}\p{N}\s]/u` ở frontend: không phải chữ, số hay khoảng trắng."""
    return unicodedata.category(c)[0] not in "LN" and c not in _JS_WHITESPACE


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
        if not any(_is_special_char(c) for c in v):
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
