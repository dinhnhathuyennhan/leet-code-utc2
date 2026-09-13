# Thiết kế API

## POST /teachers — Cấp phát tài khoản Giáo viên

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| full_name | string | có | |
| email | string (email) | có | phải đúng định dạng email |

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| user_id | string | |
| full_name | string | |
| email | string | |
| role_id | int | luôn = 2 |
| temporary_password | string | mật khẩu tạm, chỉ trả về đúng 1 lần lúc tạo |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Sai định dạng email / thiếu field | (FastAPI tự sinh) |
| 400 | Email đã tồn tại (use-case bước 6a) | `{"detail": "Email đã tồn tại"}` |

**Quy tắc nghiệp vụ** (từ Basic flow use-case)

- `role_id` luôn cố định = 2, không nhận từ client.
- `must_change_password` luôn = true khi tạo.
- Mật khẩu tạm sinh ngẫu nhiên phía server, không cho client truyền vào.
- Không trả `hashed_password` trong response.
- **Yêu cầu quyền**: chỉ Admin (khi Auth hoàn thiện, endpoint này cần `require_role(Role.ADMIN)`).

## POST /students — Cấp phát tài khoản Sinh viên

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| full_name | string | có | |
| email | string (email) | có | phải đúng định dạng email |

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| user_id | string | |
| full_name | string | |
| email | string | |
| role_id | int | luôn = 3 |
| temporary_password | string | mật khẩu tạm, chỉ trả về đúng 1 lần lúc tạo |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Sai định dạng email / thiếu field | (FastAPI tự sinh) |
| 400 | Email đã tồn tại (use-case bước 6a) | `{"detail": "Email đã tồn tại"}` |

**Quy tắc nghiệp vụ**

- `role_id` luôn cố định = 3, không nhận từ client.
- `must_change_password` luôn = true khi tạo.
- Mật khẩu tạm sinh ngẫu nhiên phía server.
- Không trả `hashed_password` trong response.
- **Yêu cầu quyền**: Admin hoặc Teacher (`require_role(Role.ADMIN, Role.TEACHER)`).

## POST /students/import — Cấp phát tài khoản Sinh viên hàng loạt bằng Excel

**Request**: `multipart/form-data`

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| file | file (.xlsx) | có | đúng cấu trúc mẫu: cột `full_name`, `email` |

**Response 201 Created** — tổng hợp kết quả xử lý từng dòng

| Field | Kiểu | Ghi chú |
|---|---|---|
| created | array of object | mỗi phần tử: `user_id`, `full_name`, `email`, `temporary_password` |
| errors | array of object | mỗi phần tử: `row` (số dòng trong file), `email`, `reason` (lý do lỗi) |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Sai định dạng file (không phải .xlsx, sai cấu trúc cột) | (use-case 5a) |
| 400 | File rỗng hoặc vượt quá số dòng cho phép | (use-case E2) |

**Quy tắc nghiệp vụ**

- Xử lý "best-effort": dòng hợp lệ vẫn tạo tài khoản, dòng lỗi bị bỏ qua và liệt kê lại trong `errors` — không trả lỗi HTTP cho toàn bộ request chỉ vì có dòng lỗi (kể cả khi `created` rỗng toàn bộ, vẫn trả 201 kèm `errors` đầy đủ, đúng use-case E1 "không có tài khoản nào được tạo" — không coi là lỗi request).
- Mỗi dòng hợp lệ: `role_id = 3`, `must_change_password = true`, sinh mật khẩu tạm riêng.
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
| 404 | `user_id` không tồn tại | `{"detail": "Không tìm thấy tài khoản"}` |
| 403 | Người gọi là Teacher nhưng tài khoản mục tiêu không phải Student (use-case 7a) | `{"detail": "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"}` |

**Quy tắc nghiệp vụ**

- Đặt `must_change_password = true`, tăng `token_version` (vô hiệu hoá toàn bộ token cũ của tài khoản mục tiêu).
- **Yêu cầu quyền**: Admin (mọi tài khoản) hoặc Teacher (chỉ tài khoản `role_id = 3`).

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
| 422 | Sai định dạng email/thiếu field | (FastAPI tự sinh) |
| 401 | Email hoặc mật khẩu sai (use-case 5a) | `{"detail": "Email hoặc mật khẩu không đúng"}` (thông báo chung, không tiết lộ sai cái nào) |

**Quy tắc nghiệp vụ**

- `access_token`/`refresh_token` đều nhúng claim `tv` (token_version hiện tại của tài khoản).
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
| 422 | `new_password` không khớp `confirm_password` hoặc không đủ độ mạnh (use-case 4a) | (chi tiết lỗi field) |
| 401 | `current_password` sai (use-case 5a) | `{"detail": "Mật khẩu hiện tại không đúng"}` |
| 400 | `new_password` trùng `current_password` (use-case 6a) | `{"detail": "Mật khẩu mới phải khác mật khẩu hiện tại"}` |

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

## POST /auth/refresh — Làm mới phiên đăng nhập

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
| 401 | Cookie thiếu, sai chữ ký hoặc hết hạn (use-case 2a) | `{"detail": "Phiên đăng nhập đã hết hạn"}` |
| 401 | `token_version` trong token không khớp database — đã bị thu hồi (use-case 3a) | `{"detail": "Phiên đăng nhập không còn hợp lệ"}`, đồng thời xoá cookie hiện tại |

**Quy tắc nghiệp vụ**

- Không rotate refresh token — chỉ cấp access token mới.
- **Yêu cầu quyền**: cookie `refresh_token` hợp lệ (không cần access token).
