# Global Exception Handler — Tài liệu luồng xử lý

## 1. Mục đích

Trước đây mỗi router tự viết `try/except` để bắt lỗi và tự quyết định format JSON trả về khi lỗi xảy ra. Điều này dẫn đến:

- Response lỗi không đồng nhất giữa các endpoint (mỗi người tự đặt field khác nhau)
- Code lặp lại (`try/except` giống hệt nhau ở nhiều router)
- Lỗi không lường trước (bug, mất kết nối DB...) có thể vô tình lộ traceback ra ngoài cho client

Global Exception Handler giải quyết việc này bằng cách xử lý **tập trung tại 1 nơi duy nhất**, áp dụng cho toàn bộ ứng dụng — router không cần viết `try/except` nữa.

---

## 2. Cấu trúc file liên quan

```
backend/app/
├── core/
│   └── exceptions.py          # Base exception AppError
├── handlers/
│   └── exception_handlers.py  # Đăng ký & xử lý exception tập trung
├── schemas/
│   └── error.py               # Format response lỗi chuẩn (ErrorResponse)
├── services/
│   └── auth_service.py        # Exception riêng của từng domain, kế thừa AppError
├── routers/
│   └── auth.py                 # Không còn try/except, để lỗi tự bay lên
└── main.py                     # Gọi register_exception_handlers(app)
```

---

## 3. Luồng xử lý

### Trường hợp thành công

```
Client → Router → Service (return data) → FastAPI serialize theo response_model → Client nhận JSON 200
```

### Trường hợp lỗi

```
Client → Router → Service (raise AppError con) 
       → FastAPI bắt exception theo type
       → Gọi đúng handler đã đăng ký
       → Handler build ErrorResponse
       → Client nhận JSON lỗi (status code tương ứng)
```

**Điểm quan trọng**: Khi service `raise` exception, code trong router **dừng thực thi ngay tại đó** — các dòng phía sau (VD: `_set_refresh_token_cookie`) sẽ **không chạy**. FastAPI tự động bắt exception này ở tầng ngoài cùng và chuyển cho handler tương ứng.

---

## 4. Cách hoạt động — từng bước cụ thể

### Bước 1 — `AppError` (base exception)

```python
# app/core/exceptions.py
class AppError(Exception):
    status_code: int = 400
    error_code: str = "APP_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
```

Mọi exception nghiệp vụ trong hệ thống nên kế thừa từ class này. Nhờ đó, chỉ cần **1 handler duy nhất** bắt được toàn bộ các loại lỗi nghiệp vụ, không cần viết handler riêng cho từng exception.

### Bước 2 — Mỗi service tự định nghĩa exception riêng, kế thừa `AppError`

```python
# app/services/auth_service.py
from app.core.exceptions import AppError

class InvalidCredentialsError(AppError):
    status_code = 401
    error_code = "INVALID_CREDENTIALS"

class WrongCurrentPasswordError(AppError):
    status_code = 401
    error_code = "WRONG_PASSWORD"

class SamePasswordError(AppError):
    status_code = 400
    error_code = "SAME_PASSWORD"
```

**Quy ước cho member khi thêm domain mới** (VD: `student_service.py`):
- Nếu lỗi chỉ đặc thù cho 1 domain → định nghĩa ngay trong file service đó, kế thừa `AppError`
- Nếu lỗi dùng chung cho nhiều domain (VD: `NotFoundError`, `UnauthorizedError`) → cân nhắc đưa vào `core/exceptions.py`

### Bước 3 — Format response lỗi chuẩn

```python
# app/schemas/error.py
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error_code: str
    message: str
```

Mọi lỗi trong toàn hệ thống, bất kể route nào, đều trả về đúng shape này.

### Bước 4 — Handler tập trung

```python
# app/handlers/exception_handlers.py
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppError
from app.schemas.error import ErrorResponse

logger = logging.getLogger(__name__)

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    body = ErrorResponse(error_code=exc.error_code, message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())

async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error at %s", request.url.path)
    body = ErrorResponse(error_code="INTERNAL_ERROR", message="Đã có lỗi xảy ra, vui lòng thử lại sau.")
    return JSONResponse(status_code=500, content=body.model_dump())

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
```

- `AppError` → mọi lỗi nghiệp vụ đã được định nghĩa (401, 400...) đi qua `app_error_handler`
- `Exception` (catch-all) → mọi lỗi **không lường trước** (bug, DB down...) đi qua `unhandled_exception_handler`, luôn trả `500` và **không lộ traceback thật** cho client — traceback chỉ được ghi vào log server qua `logger.exception(...)`

### Bước 5 — Đăng ký vào app

```python
# app/main.py
from app.handlers.exception_handlers import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
```

### Bước 6 — Router không cần try/except nữa

```python
@router.post("/auth/login", response_model=LoginResponse)
def login(data: LoginRequest, response: Response, session: Session = Depends(get_session)):
    result, refresh_token = login_service(session, data)
    _set_refresh_token_cookie(response, refresh_token)
    return result
```

Nếu `login_service` raise `InvalidCredentialsError`, dòng `_set_refresh_token_cookie` sẽ không chạy — exception được FastAPI bắt và xử lý ở handler, hoàn toàn tách biệt khỏi code router.

---

## 5. Ví dụ response thực tế

**Thành công — `POST /auth/login` (200 OK)**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user_id": 42,
  "email": "trung@example.com"
}
```

**Lỗi nghiệp vụ — sai mật khẩu (401 Unauthorized)**
```json
{
  "error_code": "INVALID_CREDENTIALS",
  "message": "Email hoặc mật khẩu không đúng"
}
```

**Lỗi không lường trước — VD DB mất kết nối (500 Internal Server Error)**
```json
{
  "error_code": "INTERNAL_ERROR",
  "message": "Đã có lỗi xảy ra, vui lòng thử lại sau."
}
```
→ Server log sẽ có đầy đủ traceback thật để debug, nhưng client không bao giờ thấy.

---

## 6. Hướng dẫn cho member khi thêm endpoint/domain mới

1. **Không viết `try/except` trong router** — cứ để service raise exception tự nhiên.
2. **Định nghĩa exception mới** (nếu cần) trong file service tương ứng, kế thừa `AppError`, khai rõ `status_code` và `error_code`.
3. **Không cần đăng ký handler mới** — vì đã kế thừa `AppError`, exception mới tự động được `app_error_handler` xử lý.
4. Nếu lỗi dùng chung nhiều domain, thảo luận với team trước khi đưa lên `core/exceptions.py` để tránh trùng lặp `error_code`.

---

## 7. Lưu ý bảo mật

- **Không bao giờ** để lộ message lỗi kỹ thuật thật (VD: nội dung exception từ DB driver, đường dẫn file nội bộ) ra `ErrorResponse.message` cho client — chỉ dùng message thân thiện, dễ hiểu.
- Toàn bộ traceback chi tiết chỉ nằm trong log server (`logger.exception`), phục vụ debug nội bộ.