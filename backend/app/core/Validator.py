from typing import Annotated

from email_validator import EmailNotValidError, validate_email
from pydantic import BeforeValidator

from app.core.exceptions import EmptyFieldError, InvalidFormatError

# các func validator khác chỉ dành riêng cho 1 field bất kỳ nên đặt trong schemas/ten_file.py
# định nghĩa function tại validator để tái sử dụng nhiều nơi
def _validate_email(v: str) -> str:
    if not v or not str(v).strip():
        raise EmptyFieldError("Email không được để trống")
    try:
        validate_email(v, check_deliverability=False)
    except EmailNotValidError as e:
        raise InvalidFormatError("Email không đúng định dạng") from e
    return v


AppEmailStr = Annotated[str, BeforeValidator(_validate_email)]