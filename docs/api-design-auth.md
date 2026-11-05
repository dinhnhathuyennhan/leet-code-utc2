# Thiết kế API — Auth & Quản lý tài khoản

## POST /teachers — Cấp phát tài khoản Giáo viên

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| full_name | string | có | |
| email | string (email) | có | phải đúng định dạng email và có đuôi `@st.utc2.edu.vn` |
| avt_link | string | không | |

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| user_id | string | UUID do server sinh |
| full_name | string | |
| email | string | |
| role_id | int | luôn = 2 |
| student_code | null | luôn `null` với Giáo viên |
| class_id | null | luôn `null` với Giáo viên |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Sai định dạng email / thiếu field | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 422 | Email không có đuôi `@st.utc2.edu.vn` | `{"error_code": "INVALID_FORMAT", "message": "Email phải có đuôi @st.utc2.edu.vn."}` |
| 409 | Email đã tồn tại | `{"error_code": "CONFLICT", "message": "Email đã được đăng ký"}` |

**Quy tắc nghiệp vụ** (từ Basic flow use-case)

- `role_id` luôn cố định = 2, không nhận từ client.
- `must_change_password` luôn = true khi tạo.
- `user_id` là UUID do server sinh, client không truyền.
- Không có ràng buộc về tuổi và hệ thống không lưu ngày sinh.
- Mật khẩu tạm của Giáo viên **là email**, sinh hoàn toàn phía server (ví dụ `email = an.nv@st.utc2.edu.vn` → mật khẩu tạm `an.nv@st.utc2.edu.vn`). Client không truyền và không thể ghi đè mật khẩu.
- Không trả `hashed_password` trong response.
- **Yêu cầu quyền**: chỉ Admin (`require_role(Role.ADMIN)`).

## POST /students — Cấp phát tài khoản Sinh viên

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| student_code | string | có | MSSV, đúng 10 chữ số (0-9) |
| full_name | string | có | |
| email | string (email) | có | phải đúng định dạng email và có đuôi `@st.utc2.edu.vn` |
| class_id | string | có | mã lớp hành chính, phải tồn tại trong bảng `class` (lớp chưa có thì tạo trước bằng [`POST /classes`](api-design-class.md)) |
| avt_link | string | không | |

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| user_id | string | UUID do server sinh |
| full_name | string | |
| email | string | |
| role_id | int | luôn = 3 |
| student_code | string | MSSV |
| class_id | string | |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Sai định dạng email / thiếu field | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 422 | `student_code` trống, không đủ 10 ký tự hoặc chứa ký tự không phải chữ số | `{"error_code": "INVALID_FORMAT", "message": "Mã sinh viên phải gồm đúng 10 chữ số"}` (hoặc `"Mã sinh viên chỉ được gồm chữ số (0-9)"`) |
| 422 | Email không có đuôi `@st.utc2.edu.vn` | `{"error_code": "INVALID_FORMAT", "message": "Email phải có đuôi @st.utc2.edu.vn."}` |
| 404 | `class_id` không tồn tại (tạo lớp trước bằng [`POST /classes`](api-design-class.md)) | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp học có ID: ..."}` |
| 409 | Email đã tồn tại | `{"error_code": "CONFLICT", "message": "Email đã được đăng ký"}` |
| 409 | `student_code` đã được dùng | `{"error_code": "CONFLICT", "message": "Mã sinh viên đã được sử dụng"}` |

**Quy tắc nghiệp vụ**

- `role_id` luôn cố định = 3, không nhận từ client.
- `must_change_password` luôn = true khi tạo.
- `user_id` là UUID do server sinh. MSSV được lưu riêng ở `student_code` (duy nhất toàn hệ thống).
- Không có ràng buộc về tuổi và hệ thống không lưu ngày sinh.
- Mật khẩu tạm của Sinh viên **là MSSV (`student_code`)**, sinh hoàn toàn phía server (ví dụ `student_code = 6751071001` → mật khẩu tạm `6751071001`). Quy tắc này giống với import Excel và đặt lại mật khẩu, để mọi Sinh viên có cùng một kiểu mật khẩu tạm. Client không truyền và không thể ghi đè mật khẩu.
- Không trả `hashed_password` trong response.
- **Yêu cầu quyền**: Admin hoặc Teacher (`require_role(Role.ADMIN, Role.TEACHER)`).

## POST /students/import — Cấp phát tài khoản Sinh viên hàng loạt bằng Excel

**Request**: `multipart/form-data`

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| file | file (.xls hoặc .xlsx) | có | file "Danh sách lớp học phần" xuất từ phòng đào tạo, tối đa 5 MB |

**Mẫu file** (đúng định dạng phòng đào tạo xuất ra, không cần sửa tay):

- Mỗi sheet là danh sách một lớp học phần. Hệ thống đọc **mọi sheet**. Sheet không có hàng tiêu đề theo mẫu (ví dụ sheet ghi chú) thì bỏ qua.
- Trong 20 hàng đầu của sheet phải có một hàng tiêu đề chứa đủ 4 cột: `STT`, `Mã sinh viên`, `Họ và tên`, `Lớp`. Không phân biệt hoa/thường, chấp nhận cả viết không dấu, `MSSV`, `Họ tên`. Các hàng phía trên (tên trường, học kỳ, thời khoá biểu...) và các cột khác (điểm danh, ghi chú) bị bỏ qua.
- `Họ và tên` thường gộp 2 ô (họ đệm và tên). Hệ thống ghép 2 ô lại bằng một dấu cách.
- Dữ liệu bắt đầu ngay dưới hàng tiêu đề. Dòng sinh viên là dòng có ô `STT` là số **hoặc** có `Mã sinh viên` (nên dòng bị xoá STT hoặc STT gõ sai vẫn được đọc). Dòng trống hoàn toàn thì bỏ qua và đọc tiếp. Gặp dòng có chữ nhưng không có STT lẫn MSSV (phần chân trang "TP Hồ Chí Minh, ngày...", "Người lập biểu") thì **dừng**. Dòng có STT nhưng các ô khác đều trống thì bỏ qua.
- File không có email. Email được sinh tự động, xem phần quy tắc.

Ví dụ một sheet:

```
Hàng 1-9 : TRƯỜNG ĐH GIAO THÔNG VẬN TẢI / Lớp học phần: ... / Mã học phần: ... / Học kỳ: ...
Hàng 11  : STT | Mã sinh viên | Họ và tên (2 ô)  |      | Lớp        | ... | Ghi chú
Hàng 12  : 1   | 6751071001   | Nguyễn Văn       | An   | CQ.67.CNTT |
Hàng 13  : 2   | 675107A002   | Trần Thị         | Bình | CQ.67.CNTT |
...      : (dòng trống) / TP Hồ Chí Minh, ngày ... / Người lập biểu
```

**Response 201 Created**: kết quả xử lý từng sinh viên

| Field | Kiểu | Ghi chú |
|---|---|---|
| created | array of object | sinh viên được tạo tài khoản. Mỗi phần tử: `user_id` (UUID), `student_code`, `full_name`, `email`, `class_id`, `temporary_password` |
| skipped | array of object | sinh viên **đã có tài khoản** nên bỏ qua (không phải lỗi). Mỗi phần tử: `user_id` (UUID của tài khoản đã có), `sheet`, `row`, `student_code`, `reason` |
| errors | array of object | dòng bị lỗi. Mỗi phần tử: `sheet`, `row` (số dòng trong Excel), `student_code` (`null` nếu ô MSSV trống), `reason`. Sắp xếp theo thứ tự sheet rồi theo dòng |

**Response lỗi** (cả file bị từ chối, chưa tạo tài khoản nào)

| Status | Khi nào | Body |
|---|---|---|
| 422 | Đuôi file không phải `.xls`/`.xlsx`, file hỏng hoặc đổi đuôi giả, hoặc không sheet nào có hàng tiêu đề theo mẫu | `{"error_code": "INVALID_EXCEL_FORMAT", "message": "..."}` |
| 400 | File không có dữ liệu | `{"error_code": "EMPTY_EXCEL_FILE", "message": "File không có dữ liệu"}` |
| 400 | File lớn hơn 5 MB, hoặc có quá 500 sinh viên (đếm sau khi gộp MSSV trùng) | `{"error_code": "EXCEL_FILE_TOO_LARGE", "message": "..."}` |

**Lý do lỗi của từng dòng** (`errors[].reason`)

| Lý do | Khi nào |
|---|---|
| `Mã sinh viên không được trống` / `Họ tên không được trống` / `Mã lớp không được trống` | ô tương ứng trống |
| `Mã sinh viên phải gồm đúng 10 chữ số` | MSSV không đủ hoặc quá 10 ký tự |
| `Mã sinh viên chỉ được gồm chữ số (0-9)` | MSSV có chữ cái, dấu, khoảng trắng, ký tự đặc biệt |
| `Mã lớp ... không đúng dạng <hệ>.<khoá>.<ngành> (vd CQ.67.CNTT)` | thiếu phần, có phần rỗng, hoặc khoá không phải số. Mã lớp dài quá 50 ký tự cũng bị lỗi |
| `Mã sinh viên trùng với dòng N (sheet X) nhưng khác họ tên hoặc lớp` | cùng MSSV xuất hiện nhiều lần với thông tin khác nhau. Lần xuất hiện đầu tiên vẫn được xử lý |
| `Email {MSSV}@st.utc2.edu.vn đã được dùng cho tài khoản khác` | email tự sinh đã thuộc một tài khoản khác (có `student_code` khác) |
| `Mã sinh viên hoặc email đã tồn tại` | lỗi trùng khi lưu (ví dụ có người khác vừa tạo cùng lúc) |
| `Không lưu được dòng này, vui lòng thử lại` | lỗi cơ sở dữ liệu khác. Chi tiết chỉ ghi vào log server, không trả câu SQL cho client |

**Quy tắc nghiệp vụ**

- Xử lý "best-effort": sinh viên hợp lệ vẫn được tạo, dòng lỗi được bỏ qua và liệt kê trong `errors`. Request không trả lỗi HTTP chỉ vì có dòng lỗi: kể cả khi `created` rỗng thì vẫn trả 201 kèm `errors` đầy đủ (use-case E1).
- Mỗi sinh viên được tạo với:
  - `role_id = 3`, `must_change_password = true`, `student_code = MSSV`, `user_id` là UUID do server sinh;
  - email tự sinh `{MSSV}@st.utc2.edu.vn`;
  - mật khẩu tạm = **MSSV**, chỉ trả về đúng 1 lần trong `created[].temporary_password`.
- Cùng một MSSV xuất hiện ở nhiều sheet (sinh viên học nhiều lớp học phần) với cùng họ tên và lớp thì chỉ tạo **1 lần**, không báo lỗi.
- MSSV **đã có tài khoản** (trùng `student_code`) thì đưa vào `skipped`, không ghi đè tài khoản cũ.
- Lớp hành chính (cột `Lớp`) chưa có trong bảng `class` thì **tự tạo** bằng cách tách mã lớp tại 2 dấu chấm đầu tiên: `CQ.67.CNTT` → `type = "CQ"`, `course_number = 67`, `department = "CNTT"`, còn `CQ.67.KTXDCTGT.2` → `department = "KTXDCTGT.2"`. Mã lớp có ngành chứa ký tự không hợp lệ (vd `CQ.67.CNTT/1`, `CQ.67.CN TT`) bị báo lỗi ở dòng đó. Lớp đã có thì giữ nguyên. Chỉ tạo lớp cho các sinh viên thực sự được tạo tài khoản. Quy ước mã lớp dùng chung với `POST /classes`, xem [api-design-class.md](api-design-class.md#quy-ước-mã-lớp-class_id).
- Mỗi sinh viên được lưu (commit) riêng. Nếu lỗi xảy ra giữa chừng, các sinh viên đã lưu trước đó vẫn được giữ (use-case E3).
- Mật khẩu tạm được băm (bcrypt) song song trên nhiều luồng để rút ngắn thời gian xử lý. Một lớp khoảng 100 sinh viên mất vài giây; FE nên đặt timeout riêng cho request này, dài hơn timeout mặc định.
- **Yêu cầu quyền**: Admin hoặc Teacher (`require_role(Role.ADMIN, Role.TEACHER)`). Teacher import cũng có thể tạo lớp hành chính mới.

## POST /users/{user_id}/reset-password — Đặt lại mật khẩu

**Request body**: không có (chỉ cần `user_id` trên path, là UUID)

**Response 200 OK**

| Field | Kiểu | Ghi chú |
|---|---|---|
| user_id | string | |
| temporary_password | string | mật khẩu tạm mới, chỉ trả về đúng 1 lần |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `user_id` không tồn tại hoặc không phải UUID hợp lệ | `{"error_code": "USER_NOT_FOUND", "message": "Không tìm thấy tài khoản"}` |
| 403 | Người gọi là Student (bị chặn hoàn toàn, kể cả tự reset chính mình) | `{"error_code": "NOT_ALLOWED_TO_RESET", "message": "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"}` |
| 403 | Người gọi là Teacher nhưng tài khoản mục tiêu không phải Student | `{"error_code": "NOT_ALLOWED_TO_RESET", "message": "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"}` |
| 403 | Người gọi là Teacher, mục tiêu là Student nhưng không học khoá nào do Teacher này tạo | `{"error_code": "NOT_ALLOWED_TO_RESET", "message": "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"}` |
| 403 | Tài khoản mục tiêu có vai trò không thuộc Admin/Teacher/Student (vai trò lạ) | `{"error_code": "NOT_ALLOWED_TO_RESET", "message": "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"}` |
| 403 | Tài khoản mục tiêu là Student nhưng chưa có `student_code` (không thể sinh mật khẩu tạm) | `{"error_code": "NOT_ALLOWED_TO_RESET", "message": "Tài khoản sinh viên chưa có mã sinh viên để tạo mật khẩu tạm thời"}` |

**Quy tắc nghiệp vụ**

- Mật khẩu tạm mới sinh theo vai trò của tài khoản mục tiêu, không sinh ngẫu nhiên:
  - **Student**: MSSV (`student_code`).
  - **Teacher/Admin**: email của tài khoản.
  - Vai trò khác: bị chặn (403), không thay đổi gì. Danh sách vai trò được phép là whitelist.
- Đặt `must_change_password = true`, tăng `token_version` (vô hiệu hoá toàn bộ token cũ của tài khoản mục tiêu).
- **Yêu cầu quyền**: Admin (mọi tài khoản) hoặc Teacher — nhưng Teacher chỉ được reset cho Student đang học **ít nhất một khoá học do chính Teacher đó tạo** (`Course.created_by = current_user.user_id`, kiểu UUID), không phải cứ `role_id = 3` là được; Student không được reset cho bất kỳ ai. Endpoint không dùng `require_role` ở router — toàn bộ logic phân quyền nằm trong service (`backend/app/modules/users/service.py::reset_password`).

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
- Server không kiểm tra claim `type` của token trong cookie `refresh_token` trước khi cấp access token mới — chỉ kiểm tra `token_version` khớp với database (`backend/app/modules/auth/service.py::refresh_access_token`, `backend/app/core/security/tokens.py::decode_token`).
- **Yêu cầu quyền**: cookie `refresh_token` hợp lệ (không cần access token).
