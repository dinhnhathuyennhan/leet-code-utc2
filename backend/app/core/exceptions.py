class AppError(Exception):
    # Base exception cho mọi lỗi nghiệp vụ có kiểm soát trong hệ thống.
    status_code: int = 400
    error_code: str = "APP_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

# --- Lỗi input / validate — dùng chung cho nhiều schema (422) ---
class EmptyFieldError(AppError):
    """Trường bắt buộc bị để trống hoặc chỉ chứa khoảng trắng."""
    status_code = 422
    error_code = "EMPTY_FIELD"


class InvalidFormatError(AppError):
    """Giá trị sai định dạng mong đợi (email, số điện thoại, ngày tháng...)."""
    status_code = 422
    error_code = "INVALID_FORMAT"


class WeakPasswordError(AppError):
    """Mật khẩu không đạt độ mạnh yêu cầu (độ dài, ký tự đặc biệt...)."""
    status_code = 422
    error_code = "WEAK_PASSWORD"


class PasswordMismatchError(AppError):
    """Mật khẩu xác nhận không khớp với mật khẩu vừa nhập."""
    status_code = 422
    error_code = "PASSWORD_MISMATCH"


# --- Lỗi truy cập tài nguyên — dùng chung cho mọi domain (404/409) ---

class NotFoundError(AppError):
    """Không tìm thấy tài nguyên được yêu cầu (user, student, order...)."""
    # lưu ý khi dùng exception này: truyền error message cụ thể đúng ngữ cảnh
    # tránh "không tìm thấy" quá chung chung không debug được
    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(AppError):
    """Tài nguyên đã tồn tại hoặc xung đột trạng thái (email đã đăng ký, trùng dữ liệu...)."""
    status_code = 409
    error_code = "CONFLICT"


# --- Lỗi xác thực / phân quyền — dùng chung cho mọi endpoint cần auth (401/403) ---

class UnauthorizedError(AppError):
    """Chưa xác thực hoặc token không hợp lệ/hết hạn."""
    status_code = 401
    error_code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    """Đã xác thực nhưng không đủ quyền thực hiện hành động."""
    status_code = 403
    error_code = "FORBIDDEN"

# trong file này định nghĩa các error dùng chung
# đối với các error đặc trưng riêng biệt có thể khai báo thẳng trong file đó
