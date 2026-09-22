# Thiết kế API — Auth & Quản lý tài khoản

## POST /teachers — Cấp phát tài khoản Giáo viên

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| user_id | string | có | |
| full_name | string | có | |
| date_of_birth | date | có | định dạng `dd/mm/yyyy` hoặc `yyyy-mm-dd` |
| email | string (email) | có | phải đúng định dạng email |
| avt_link | string | không | |

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| user_id | string | |
| full_name | string | |
| email | string | |
| role_id | int | luôn = 2 |
| date_of_birth | date | |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Sai định dạng email / thiếu field | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 422 | Chưa đủ tuổi theo `date_of_birth` | `{"error_code": "DATE_OF_BIRTH_INVALID", "message": "Người dùng phải đủ 22 tuổi"}` |
| 400 | Email đã tồn tại | `{"error_code": "CONFLICT", "message": "Email đã được đăng ký"}` |

**Quy tắc nghiệp vụ** (từ Basic flow use-case)

- `role_id` luôn cố định = 2, không nhận từ client.
- `must_change_password` luôn = true khi tạo.
- Người được cấp tài khoản phải đủ **22 tuổi** trở lên, tính từ `date_of_birth`.
- Mật khẩu tạm sinh hoàn toàn phía server theo ngày sinh, định dạng `ddmmyyyy` (ví dụ `date_of_birth = 15/05/1990` → mật khẩu tạm `15051990`). Client không truyền và không thể ghi đè mật khẩu.
- Không trả `hashed_password` trong response.
- **Yêu cầu quyền**: chỉ Admin (`require_role(Role.ADMIN)`).

## POST /students — Cấp phát tài khoản Sinh viên

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| user_id | string | có | |
| full_name | string | có | |
| date_of_birth | date | có | định dạng `dd/mm/yyyy` hoặc `yyyy-mm-dd` |
| email | string (email) | có | phải đúng định dạng email |
| avt_link | string | không | |

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| user_id | string | |
| full_name | string | |
| email | string | |
| role_id | int | luôn = 3 |
| date_of_birth | date | |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Sai định dạng email / thiếu field | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 422 | Chưa đủ tuổi theo `date_of_birth` | `{"error_code": "DATE_OF_BIRTH_INVALID", "message": "Người dùng phải đủ 17 tuổi"}` |
| 400 | Email đã tồn tại | `{"error_code": "CONFLICT", "message": "Email đã được đăng ký"}` |

**Quy tắc nghiệp vụ**

- `role_id` luôn cố định = 3, không nhận từ client.
- `must_change_password` luôn = true khi tạo.
- Người được cấp tài khoản phải đủ 17 tuổi trở lên, tính từ `date_of_birth`.
- Mật khẩu tạm sinh hoàn toàn phía server theo ngày sinh, định dạng `ddmmyyyy` (ví dụ `date_of_birth = 15/05/1990` → mật khẩu tạm `15051990`). Client không truyền và không thể ghi đè mật khẩu.
- Không trả `hashed_password` trong response.
- **Yêu cầu quyền**: Admin hoặc Teacher (`require_role(Role.ADMIN, Role.TEACHER)`).

## POST /students/import — Cấp phát tài khoản Sinh viên hàng loạt bằng Excel

**Request**: `multipart/form-data`

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| file | file (.xlsx) | có | đúng cấu trúc mẫu: cột `user_id`, `full_name`, `date_of_birth`, `email` |

**Response 201 Created** — tổng hợp kết quả xử lý từng dòng

| Field | Kiểu | Ghi chú |
|---|---|---|
| created | array of object | mỗi phần tử: `user_id`, `full_name`, `email`, `date_of_birth`, `temporary_password` |
| errors | array of object | mỗi phần tử: `row` (số dòng trong file), `email`, `date_of_birth`, `reason` (lý do lỗi) |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | File không có phần mở rộng `.xlsx`, không đọc được, hoặc thiếu cột bắt buộc | `{"error_code": "INVALID_EXCEL_FORMAT", "message": "..."}` |
| 400 | File không có dữ liệu | `{"error_code": "EMPTY_EXCEL_FILE", "message": "File không có dữ liệu"}` |
| 400 | Vượt quá 500 dòng cho phép | `{"error_code": "EXCEL_FILE_TOO_LARGE", "message": "..."}` |

**Quy tắc nghiệp vụ**

- Xử lý "best-effort": dòng hợp lệ vẫn tạo tài khoản, dòng lỗi bị bỏ qua và liệt kê lại trong `errors` — không trả lỗi HTTP cho toàn bộ request chỉ vì có dòng lỗi (kể cả khi `created` rỗng toàn bộ, vẫn trả 201 kèm `errors` đầy đủ, đúng use-case E1 "không có tài khoản nào được tạo" — không coi là lỗi request).
- Mỗi dòng hợp lệ: `role_id = 3`, `must_change_password = true`, mật khẩu tạm sinh theo ngày sinh (`date_of_birth`) của chính dòng đó, định dạng `ddmmyyyy`.
- **Yêu cầu quyền**: Admin hoặc Teacher.

## POST /users/{user_id}/reset-password — Đặt lại mật khẩu

**Request body**: không có (chỉ cần `user_id` trên path)

**Response 200 OK**

| Field | Kiểu | Ghi chú |
|---|---|---|
| user_id | string | |
| temporary_password | string | mật khẩu tạm mới, chỉ trả về đúng 1 lần |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `user_id` không tồn tại | `{"error_code": "USER_NOT_FOUND", "message": "Không tìm thấy tài khoản"}` |
| 403 | Người gọi là Student (bị chặn hoàn toàn, kể cả tự reset chính mình) | `{"error_code": "NOT_ALLOWED_TO_RESET", "message": "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"}` |
| 403 | Người gọi là Teacher nhưng tài khoản mục tiêu không phải Student | `{"error_code": "NOT_ALLOWED_TO_RESET", "message": "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"}` |
| 403 | Người gọi là Teacher, mục tiêu là Student nhưng không học khoá nào do Teacher này tạo | `{"error_code": "NOT_ALLOWED_TO_RESET", "message": "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"}` |
| 422 | Tài khoản mục tiêu chưa có `date_of_birth` (không thể sinh mật khẩu tạm) | `{"error_code": "DATE_OF_BIRTH_INVALID", "message": "Tài khoản chưa có ngày sinh để tạo mật khẩu tạm thời"}` |

**Quy tắc nghiệp vụ**

- Mật khẩu tạm mới sinh lại theo `date_of_birth` hiện có của tài khoản mục tiêu (định dạng `ddmmyyyy`), không sinh ngẫu nhiên.
- Đặt `must_change_password = true`, tăng `token_version` (vô hiệu hoá toàn bộ token cũ của tài khoản mục tiêu).
- **Yêu cầu quyền**: Admin (mọi tài khoản) hoặc Teacher — nhưng Teacher chỉ được reset cho Student đang học **ít nhất một khoá học do chính Teacher đó tạo** (`Course.created_by = current_user.user_id`), không phải cứ `role_id = 3` là được; Student không được reset cho bất kỳ ai. Endpoint không dùng `require_role` ở router — toàn bộ logic phân quyền nằm trong service (`backend/app/services/user_service.py::reset_password`).

## POST /auth/login — Đăng nhập

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| email | string (email) | có | |
| password | string | có | |

**Response 200 OK**

| Field | Kiểu | Ghi chú |
|---|---|---|
| access_token | string | JWT ngắn hạn |
| token_type | string | luôn `"bearer"` |
| user | object | `user_id`, `full_name`, `email`, `role_id`, `must_change_password` |

Đồng thời set cookie `refresh_token` (HttpOnly, `Path=/auth`).

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Sai định dạng email/thiếu field | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 401 | Email hoặc mật khẩu sai | `{"error_code": "INVALID_CREDENTIALS", "message": "Email hoặc mật khẩu không đúng"}` (thông báo chung, không tiết lộ sai cái nào) |

**Quy tắc nghiệp vụ**

- `access_token`/`refresh_token` đều nhúng claim `tv` (token_version hiện tại của tài khoản) và claim `type` (`"access"` hoặc `"refresh"`) để phân biệt 2 loại token — server phải kiểm tra đúng `type` tương ứng ở từng endpoint, không chấp nhận lẫn loại token.
- Client dựa vào `user.must_change_password` để tự điều hướng sang trang đổi mật khẩu.
- **Yêu cầu quyền**: không (public, ai cũng gọi được).

## POST /auth/change-password — Đổi mật khẩu

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| current_password | string | có | |
| new_password | string | có | |
| confirm_password | string | có | phải trùng `new_password` |

**Response 200 OK** — giống hệt response của `/auth/login` (`access_token`, `token_type`, `user`) + set lại cookie `refresh_token` mới.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | `new_password` không khớp `confirm_password` hoặc không đủ độ mạnh | `{"error_code": "PASSWORD_MISMATCH" \| "WEAK_PASSWORD", "message": "..."}` |
| 401 | `current_password` sai | `{"error_code": "WRONG_PASSWORD", "message": "Mật khẩu hiện tại không đúng"}` |
| 400 | `new_password` trùng `current_password` | `{"error_code": "SAME_PASSWORD", "message": "Mật khẩu mới phải khác mật khẩu hiện tại"}` |

**Quy tắc nghiệp vụ**

- Tăng `token_version` (vô hiệu hoá mọi token cũ trên mọi thiết bị), rồi cấp ngay token mới cho chính request này (tránh tự đăng xuất chính mình).
- Đặt `must_change_password = false`.
- **Yêu cầu quyền**: Bearer token hợp lệ (bất kỳ role nào, chỉ tác động lên chính tài khoản đang đăng nhập).

## POST /auth/logout — Đăng xuất

**Request body**: không có

**Response**: `204 No Content` — xoá cookie `refresh_token`.

**Response lỗi**: không có mã lỗi nghiệp vụ nào (endpoint luôn thành công/idempotent); lỗi mất kết nối là do phía client tự xử lý, không phải response code từ server.

**Quy tắc nghiệp vụ**

- Không thay đổi `token_version` (không ảnh hưởng tới các thiết bị khác đang đăng nhập).
- **Yêu cầu quyền**: không bắt buộc (hoạt động kể cả khi access token đã hết hạn, vì mục đích chỉ là xoá cookie).

## POST /auth/refresh-access-token — Làm mới phiên đăng nhập

**Request body**: không có (đọc cookie `refresh_token`)

**Response 200 OK**

| Field | Kiểu | Ghi chú |
|---|---|---|
| access_token | string | JWT ngắn hạn mới |
| token_type | string | luôn `"bearer"` |

Cookie `refresh_token` giữ nguyên (không rotate).

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 401 | Cookie `refresh_token` thiếu | `{"error_code": "SESSION_EXPIRED", "message": "Phiên đăng nhập đã hết hạn"}` |
| 401 | `token_version` trong token không khớp database (đã bị thu hồi do đổi mật khẩu/reset ở nơi khác) | `{"error_code": "SESSION_REVOKED", "message": "Phiên đăng nhập không còn hợp lệ"}` |

**Quy tắc nghiệp vụ**

- Không rotate refresh token — chỉ cấp access token mới.
- Server không kiểm tra claim `type` của token trong cookie `refresh_token` trước khi cấp access token mới — chỉ kiểm tra `token_version` khớp với database (`backend/app/services/auth_service.py::refresh_access_token`, `backend/app/core/token.py::decode_token`).
- **Yêu cầu quyền**: cookie `refresh_token` hợp lệ (không cần access token).
