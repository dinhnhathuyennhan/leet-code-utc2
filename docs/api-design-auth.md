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
| is_active | bool | trạng thái khoá tài khoản, luôn `true` khi tạo mới |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | `email` sai định dạng hoặc không phải chuỗi (số, mảng, object...) | `{"error_code": "INVALID_FORMAT", "message": "Email không đúng định dạng"}` |
| 422 | `email` rỗng hoặc chỉ có khoảng trắng | `{"error_code": "EMPTY_FIELD", "message": "Email không được để trống"}` |
| 422 | Thiếu field bắt buộc | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
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
| is_active | bool | trạng thái khoá tài khoản, luôn `true` khi tạo mới |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | `email` sai định dạng hoặc không phải chuỗi (số, mảng, object...) | `{"error_code": "INVALID_FORMAT", "message": "Email không đúng định dạng"}` |
| 422 | `email` rỗng hoặc chỉ có khoảng trắng | `{"error_code": "EMPTY_FIELD", "message": "Email không được để trống"}` |
| 422 | Thiếu field bắt buộc | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
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

## GET /users/me — Thông tin tài khoản đang đăng nhập

**Response 200 OK**: `UserResponse` của người gọi (`user_id`, `full_name`, `email`, `role_id`, `student_code`, `class_id`, `is_active`). Không bao giờ trả `hashed_password`.

**Response lỗi**: 401 token không hợp lệ/hết hạn; 403 `ACCOUNT_LOCKED` nếu tài khoản đang bị khoá (xem `POST /users/{user_id}/lock`).

- **Yêu cầu quyền**: Bearer token hợp lệ, mọi vai trò.

## GET /users — Danh sách tài khoản

**Query parameters**

| Field | Kiểu | Bắt buộc | Mặc định | Ghi chú |
|---|---|---|---|---|
| role_id | int \| null | không | null | `1` Admin, `2` Giáo viên, `3` Sinh viên. Chỉ có tác dụng với Admin |
| class_id | string \| null | không | null | 1–50 ký tự; chỉ lấy Sinh viên thuộc lớp hành chính này |
| page | int | không | 1 | ≥ 1 |
| page_size | int | không | 20 | Từ 1 đến 100 |

**Response 200 OK**

```json
{
  "items": [
    {
      "user_id": "6f1c...-uuid",
      "full_name": "Nguyễn Văn A",
      "email": "6451071001@st.utc2.edu.vn",
      "role_id": 3,
      "student_code": "6451071001",
      "class_id": "CQ.64.CNTT",
      "is_active": true
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | `role_id` khác 1/2/3 | `{"error_code": "INVALID_FORMAT", "message": "role_id không hợp lệ"}` |
| 422 | Query sai kiểu, `page`/`page_size`/`class_id` ngoài giới hạn | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 403 | Người gọi không phải Admin/Giáo viên | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- Scope theo vai trò người gọi: Admin thấy mọi tài khoản (lọc được theo `role_id`); Giáo viên chỉ thấy Sinh viên đang ghi danh ít nhất một lớp học phần do mình tạo; `role_id` hợp lệ (1/2/3) truyền vào bị bỏ qua, còn giá trị khác vẫn bị 422 như mọi vai trò.
- Có `class_id` thì luôn chỉ trả Sinh viên của lớp đó (kết hợp với scope ở trên).
- Sắp xếp theo `user_id`; `total` là tổng số bản ghi khớp điều kiện (trước phân trang).
- **Yêu cầu quyền**: Bearer token hợp lệ, role Admin hoặc Giáo viên.

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
| 403 | Người gọi là Student hoặc có vai trò lạ (bị chặn hoàn toàn, kể cả tự reset chính mình) | `{"error_code": "NOT_ALLOWED_TO_RESET", "message": "Bạn không có quyền đặt lại mật khẩu cho tài khoản này"}` |
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
- **Yêu cầu quyền**: Admin (mọi tài khoản Admin/Teacher/Student) hoặc Teacher — nhưng Teacher chỉ được reset cho Student đang học **ít nhất một khoá học do chính Teacher đó tạo** (`Course.created_by = current_user.user_id`, kiểu UUID), không phải cứ `role_id = 3` là được; Student và mọi vai trò khác không được reset cho bất kỳ ai. Quyền là whitelist theo vai trò người gọi, vai trò lạ không bị xử lý nhầm như Admin. Endpoint không dùng `require_role` ở router — toàn bộ logic phân quyền nằm trong service (`backend/app/modules/users/service.py::reset_password`).

## PATCH /users/{user_id} — Sửa thông tin tài khoản

**Request body**: mọi field đều không bắt buộc. Field không gửi hoặc gửi `null` thì giữ nguyên. Field không có trong bảng (ví dụ `role_id`, `is_active`) bị bỏ qua.

| Field | Kiểu | Sửa được với tài khoản | Ghi chú |
|---|---|---|---|
| full_name | string | Admin (tự sửa mình), Giáo viên, Sinh viên | không được rỗng; khoảng trắng thừa được gộp thành một dấu cách |
| email | string (email) | Admin (tự sửa mình), Giáo viên | đúng định dạng email và có đuôi `@st.utc2.edu.vn`. Email Sinh viên không sửa trực tiếp được |
| student_code | string | Sinh viên | MSSV, đúng 10 chữ số (0-9). Đổi MSSV thì email tự đổi thành `<MSSV>@st.utc2.edu.vn` |
| class_id | string | Sinh viên | mã lớp hành chính, phải tồn tại trong bảng `class` |

Ví dụ đổi MSSV và lớp của Sinh viên:

```json
{"student_code": "6851071002", "class_id": "CQ.68.CNTT"}
```

**Response 200 OK**: thông tin tài khoản sau khi sửa, cùng các field như response của `POST /students`

```json
{
  "user_id": "3f6c2a8e-6d1b-4c3e-9a51-2b7f0d4e8c19",
  "full_name": "Nguyễn Văn An",
  "email": "6851071002@st.utc2.edu.vn",
  "role_id": 3,
  "student_code": "6851071002",
  "class_id": "CQ.68.CNTT",
  "is_active": true
}
```

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 403 | Người gọi là Student hoặc có vai trò lạ (chặn ở `require_role`) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |
| 422 | `full_name` rỗng hoặc chỉ có khoảng trắng / không phải chuỗi | `{"error_code": "EMPTY_FIELD", "message": "Họ và tên không được để trống"}` / `{"error_code": "INVALID_FORMAT", "message": "Họ và tên phải là chuỗi"}` |
| 422 | `email` sai định dạng, không phải chuỗi, hoặc không có đuôi `@st.utc2.edu.vn` | `{"error_code": "INVALID_FORMAT", "message": "Email không đúng định dạng"}` (hoặc `"Email phải có đuôi @st.utc2.edu.vn."`) |
| 422 | `email` rỗng hoặc chỉ có khoảng trắng | `{"error_code": "EMPTY_FIELD", "message": "Email không được để trống"}` |
| 422 | `student_code` trống, không đủ 10 ký tự hoặc chứa ký tự không phải chữ số | `{"error_code": "INVALID_FORMAT", "message": "Mã sinh viên phải gồm đúng 10 chữ số"}` (hoặc `"Mã sinh viên chỉ được gồm chữ số (0-9)"`; trống thì `EMPTY_FIELD` `"Mã sinh viên không được trống"`) |
| 422 | `class_id` rỗng / không phải chuỗi | `{"error_code": "EMPTY_FIELD", "message": "Mã lớp không được trống"}` / `{"error_code": "INVALID_FORMAT", "message": "Mã lớp phải là chuỗi"}` |
| 404 | `user_id` không tồn tại hoặc không phải UUID hợp lệ | `{"error_code": "USER_NOT_FOUND", "message": "Không tìm thấy tài khoản"}` |
| 403 | Không có quyền sửa tài khoản đích (xem ma trận quyền bên dưới) | `{"error_code": "NOT_ALLOWED_TO_MANAGE_ACCOUNT", "message": "Bạn không có quyền quản lý tài khoản này"}` |
| 422 | Gửi `email` cho tài khoản Sinh viên | `{"error_code": "FIELD_NOT_EDITABLE", "message": "Email sinh viên được tạo tự động theo MSSV, không thể sửa trực tiếp"}` |
| 422 | Gửi `student_code` hoặc `class_id` cho tài khoản Admin/Giáo viên | `{"error_code": "FIELD_NOT_EDITABLE", "message": "Chỉ tài khoản sinh viên mới có mã sinh viên và lớp hành chính"}` |
| 409 | `student_code` mới đã thuộc tài khoản khác | `{"error_code": "CONFLICT", "message": "Mã sinh viên đã được sử dụng"}` |
| 409 | Email tự sinh từ MSSV mới đã thuộc tài khoản khác | `{"error_code": "CONFLICT", "message": "Email 6851071002@st.utc2.edu.vn đã được đăng ký"}` |
| 409 | `email` mới (Admin/Giáo viên) đã thuộc tài khoản khác | `{"error_code": "CONFLICT", "message": "Email đã được đăng ký"}` |
| 409 | Trùng dữ liệu lúc lưu (request khác vừa ghi cùng email/MSSV) | `{"error_code": "CONFLICT", "message": "Email hoặc mã sinh viên đã được sử dụng"}` |
| 404 | `class_id` không tồn tại (hoặc vừa bị xoá/đổi mã lúc lưu) | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp học có ID: ..."}` |

Các lỗi 422 về định dạng (`EMPTY_FIELD`, `INVALID_FORMAT`) được kiểm tra ở schema `UpdateUserRequest`: sau `require_role`, nhưng trước khi service kiểm tra tài khoản đích (404) và quyền quản lý (`NOT_ALLOWED_TO_MANAGE_ACCOUNT`).

**Ma trận quyền** (whitelist theo vai trò người gọi, `backend/app/modules/users/service.py::_ensure_can_edit_account`)

| Người gọi | Được sửa | Không được sửa |
|---|---|---|
| Admin | chính mình (chỉ `full_name`, `email`), mọi Giáo viên, mọi Sinh viên | Admin khác, tài khoản có vai trò lạ |
| Giáo viên | Sinh viên đang học ít nhất một khoá do chính Giáo viên đó tạo (`Course.created_by`) | chính mình, Giáo viên khác, Admin, Sinh viên ngoài lớp mình quản lý |
| Sinh viên, vai trò lạ | không tài khoản nào, kể cả của mình | |

**Quy tắc nghiệp vụ**

- Field được sửa phụ thuộc vai trò của **tài khoản đích**: Giáo viên/Admin sửa `full_name`, `email`; Sinh viên sửa `full_name`, `student_code`, `class_id`.
- Đổi `student_code` thì server tự đặt `email = <MSSV>@st.utc2.edu.vn`. Gửi lại đúng MSSV hiện tại thì không đổi gì.
- Không đổi mật khẩu, `must_change_password` và `token_version`, nên người dùng không bị đăng xuất. Từ lần đăng nhập sau phải dùng email mới.
- Mọi kiểm tra chạy xong mới ghi database, lỗi không để lại thay đổi dở dang. Body không có thay đổi nào thì trả 200 với dữ liệu hiện tại.
- `role_id` và trạng thái khoá không sửa qua endpoint này.
- Không trả `hashed_password` trong response.
- **Yêu cầu quyền**: Admin hoặc Teacher (`require_role(Role.ADMIN, Role.TEACHER)`), phân quyền chi tiết theo tài khoản đích nằm trong service (`update_user`).

## POST /users/{user_id}/lock — Khoá tài khoản

**Request body**: không có (chỉ cần `user_id` trên path, là UUID)

**Response 200 OK**: thông tin tài khoản, cùng các field như response của `PATCH /users/{user_id}`, với `is_active = false`

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 403 | Người gọi là Student hoặc có vai trò lạ (chặn ở `require_role`) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |
| 404 | `user_id` không tồn tại hoặc không phải UUID hợp lệ | `{"error_code": "USER_NOT_FOUND", "message": "Không tìm thấy tài khoản"}` |
| 403 | Tự khoá chính mình; Admin khoá Admin khác; Giáo viên khoá Giáo viên/Admin hoặc Sinh viên không học khoá nào do mình tạo; tài khoản đích có vai trò lạ | `{"error_code": "NOT_ALLOWED_TO_MANAGE_ACCOUNT", "message": "Bạn không có quyền quản lý tài khoản này"}` |
| 409 | Request khoá/mở khoá khác chạy đồng thời liên tục làm đổi trạng thái (thử tối đa 3 lần vẫn không được) | `{"error_code": "CONFLICT", "message": "Trạng thái tài khoản vừa thay đổi, vui lòng thử lại"}` |

**Quy tắc nghiệp vụ**

- Khoá: đặt `is_active = false`, ghi `locked_by = user_id` của người khoá và tăng `token_version` (UPDATE nguyên tử), nên mọi access/refresh token cũ bị vô hiệu hoá, tài khoản bị đăng xuất khỏi mọi thiết bị.
- Idempotent: tài khoản đã khoá thì trả 200 và **không** tăng `token_version` lần nữa.
  - Giáo viên khoá lại: giữ nguyên `locked_by` (người khoá trước vẫn là người khoá, kể cả khi đó là Admin).
  - Admin khoá lại: `locked_by` chuyển sang Admin này, từ đó Giáo viên không mở khoá được nữa.
- Sau khi bị khoá:
  - Đăng nhập đúng mật khẩu → 403 `ACCOUNT_LOCKED`; sai mật khẩu → vẫn 401 lỗi chung `"Email hoặc mật khẩu không đúng"`.
  - Refresh token và mọi API dùng Bearer token (kể cả token đang dùng lúc bị khoá) → 403 `{"error_code": "ACCOUNT_LOCKED", "message": "Tài khoản đã bị khoá"}`, response kèm `Set-Cookie` xoá cookie `refresh_token`.
- `locked_by` không có trong response.
- **Yêu cầu quyền**: Admin hoặc Teacher (`require_role(Role.ADMIN, Role.TEACHER)`), whitelist theo vai trò người gọi (`_ensure_can_manage_account`):
  - Admin: khoá Giáo viên và Sinh viên; không tự khoá mình, không khoá Admin khác.
  - Giáo viên: chỉ khoá Sinh viên đang học ít nhất một khoá do chính mình tạo.

## POST /users/{user_id}/unlock — Mở khoá tài khoản

**Request body**: không có (chỉ cần `user_id` trên path, là UUID)

**Response 200 OK**: thông tin tài khoản, cùng các field như response của `PATCH /users/{user_id}`, với `is_active = true`

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 403 | Người gọi là Student hoặc có vai trò lạ (chặn ở `require_role`) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |
| 404 | `user_id` không tồn tại hoặc không phải UUID hợp lệ | `{"error_code": "USER_NOT_FOUND", "message": "Không tìm thấy tài khoản"}` |
| 403 | Không có quyền quản lý tài khoản đích (giống `POST /users/{user_id}/lock`) | `{"error_code": "NOT_ALLOWED_TO_MANAGE_ACCOUNT", "message": "Bạn không có quyền quản lý tài khoản này"}` |
| 403 | Giáo viên mở khoá tài khoản không do Giáo viên khoá (Admin khoá, `locked_by` NULL, người khoá đã bị xoá hoặc có vai trò lạ), hoặc Admin vừa khoá lại cùng lúc | `{"error_code": "NOT_ALLOWED_TO_MANAGE_ACCOUNT", "message": "Tài khoản này chỉ Quản trị viên mới được mở khoá"}` |

**Quy tắc nghiệp vụ**

- Mở khoá: đặt `is_active = true`, `locked_by = NULL`. **Không** đổi `token_version`, nên token phát hành trước khi khoá vẫn không dùng được (access token cũ → 401 `UNAUTHORIZED` `"Phiên đăng nhập đã hết hạn"`, refresh token cũ → 401 `SESSION_REVOKED`). Người dùng phải đăng nhập lại.
- Idempotent: tài khoản đang hoạt động thì trả 200, không đổi gì.
- Ai được mở khoá phụ thuộc người khoá (`locked_by`):
  - Admin: mở khoá được mọi Giáo viên/Sinh viên đang bị khoá.
  - Giáo viên: chỉ mở khoá được khi người khoá còn tồn tại và có vai trò Giáo viên (không bắt buộc là chính mình, Giáo viên khác cùng dạy Sinh viên đó cũng được). Tài khoản do Admin khoá, bị khoá từ trước khi có cột `locked_by` (NULL), hay người khoá đã bị xoá thì chỉ Admin mở khoá được.
- **Yêu cầu quyền**: giống `POST /users/{user_id}/lock`.

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
| 422 | `email` sai định dạng hoặc không phải chuỗi (số, mảng, object...) | `{"error_code": "INVALID_FORMAT", "message": "Email không đúng định dạng"}` |
| 422 | `email` rỗng hoặc chỉ có khoảng trắng | `{"error_code": "EMPTY_FIELD", "message": "Email không được để trống"}` |
| 422 | Thiếu field bắt buộc | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 401 | Email hoặc mật khẩu sai | `{"error_code": "INVALID_CREDENTIALS", "message": "Email hoặc mật khẩu không đúng"}` (thông báo chung, không tiết lộ sai cái nào) |
| 403 | Mật khẩu đúng nhưng tài khoản đang bị khoá (`is_active = false`) | `{"error_code": "ACCOUNT_LOCKED", "message": "Tài khoản đã bị khoá"}` |
| 429 | Email đã đăng nhập sai quá nhiều lần và đang bị tạm chặn (trả cả khi lần này nhập đúng mật khẩu) | `{"error_code": "LOGIN_RATE_LIMITED", "message": "Bạn đã đăng nhập sai quá nhiều lần. Vui lòng thử lại sau {n} phút"}` |

**Quy tắc nghiệp vụ**

- `access_token`/`refresh_token` đều nhúng claim `tv` (token_version hiện tại của tài khoản) và claim `type` (`"access"` hoặc `"refresh"`) để phân biệt 2 loại token — server phải kiểm tra đúng `type` tương ứng ở từng endpoint, không chấp nhận lẫn loại token.
- Client dựa vào `user.must_change_password` để tự điều hướng sang trang đổi mật khẩu.
- Trạng thái khoá chỉ được báo **sau khi** mật khẩu đúng. Tài khoản bị khoá mà nhập sai mật khẩu vẫn nhận 401 lỗi chung, để người lạ không dò được tài khoản nào đang bị khoá.
  - Đánh đổi có chủ ý: 403 cho biết mật khẩu vừa nhập là đúng. Nhóm chấp nhận điều này để chủ tài khoản hiểu vì sao không vào được, thay vì tưởng mình quên mật khẩu. Rủi ro thấp vì tài khoản bị khoá không đăng nhập được, việc dò vẫn bị giới hạn số lượt ở dưới, và lượt đoán trúng không xoá bộ đếm.
- **Chống dò mật khẩu** (bảng `login_attempt`): sai `LOGIN_MAX_FAILED_ATTEMPTS` lần (mặc định 5) trong `LOGIN_FAILURE_WINDOW_MINUTES` phút (mặc định 15) thì email bị tạm chặn `LOGIN_LOCKOUT_MINUTES` phút (mặc định 15).
  - Lần sai chạm ngưỡng trả luôn 429. Trong lúc bị chặn, server không kiểm tra mật khẩu và trả 429 kể cả khi mật khẩu đúng.
  - Đếm theo email sau khi `strip` (giữ nguyên hoa/thường, khớp cách login tìm tài khoản), không theo IP, vì cả phòng máy thường dùng chung một IP. Email khác hoa/thường không đăng nhập được vào tài khoản thật, nên đếm riêng không giúp lách ngưỡng.
  - Email chưa có tài khoản cũng bị đếm và chặn giống hệt, để không dò được email nào tồn tại.
  - Đăng nhập thành công thì xoá bộ đếm. Tài khoản đang bị khoá (`is_active = false`) mà nhập đúng mật khẩu thì vẫn tính là một lượt sai và **không** xoá bộ đếm (vẫn trả 403, riêng lượt chạm ngưỡng trả 429), để đoán trúng không mở ra cửa sổ thử mới. Hết thời gian chặn hoặc hết cửa sổ đếm thì đếm lại từ đầu.
  - Mỗi lượt đăng nhập được tính vào bộ đếm **trước** khi kiểm tra mật khẩu (dưới khoá dòng), nên một đợt request song song không thử được quá ngưỡng: lượt thứ `LOGIN_MAX_FAILED_ATTEMPTS` đặt luôn mốc chặn, các request đến trong lúc nó đang kiểm tra mật khẩu nhận 429. Nếu chính lượt đó đúng mật khẩu thì vẫn đăng nhập được và bộ đếm bị xoá.
  - Dòng đã hết cửa sổ đếm và không còn bị chặn được tự dọn định kỳ (mỗi process tối đa 5 phút một lần, chạy kèm lượt đăng nhập), để email sai rồi bỏ đi không nằm lại mãi trong bảng.
  - Đánh đổi: người khác biết email có thể cố tình nhập sai để chặn tạm tài khoản đó tối đa 15 phút.
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
| 422 | `new_password` chứa MSSV (`student_code`) hoặc phần trước `@` của email (so không phân biệt hoa thường, chỉ xét chuỗi >= 4 ký tự) | `{"error_code": "WEAK_PASSWORD", "message": "Mật khẩu mới không được chứa mã sinh viên hoặc email"}` |

**Độ mạnh của `new_password`** (khớp `changePasswordSchema` ở frontend):

- Ít nhất 8 ký tự, có ít nhất 1 chữ hoa, 1 chữ số và 1 ký tự đặc biệt (ký tự không phải chữ, số hay khoảng trắng).
- Không chứa MSSV hoặc phần trước `@` của email (mật khẩu tạm của Sinh viên chính là MSSV).
- Chỉ áp cho mật khẩu mới. Đăng nhập vẫn chấp nhận mật khẩu cũ yếu hơn để không khoá tài khoản sẵn có.

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
| 401 | Cookie `refresh_token` sai chữ ký, hết hạn, sai loại token (không phải `"refresh"`) hoặc thiếu claim | `{"error_code": "SESSION_EXPIRED", "message": "Phiên đăng nhập đã hết hạn"}` |
| 401 | Tài khoản không còn tồn tại, hoặc `token_version` trong token không khớp database (đã bị thu hồi do đổi mật khẩu/reset/khoá ở nơi khác) | `{"error_code": "SESSION_REVOKED", "message": "Phiên đăng nhập không còn hợp lệ"}` |
| 403 | Tài khoản đang bị khoá | `{"error_code": "ACCOUNT_LOCKED", "message": "Tài khoản đã bị khoá"}` |

**Quy tắc nghiệp vụ**

- Không rotate refresh token — chỉ cấp access token mới.
- Server kiểm tra token trong cookie phải có claim `type = "refresh"` (access token đặt vào cookie bị từ chối), rồi kiểm tra tài khoản còn tồn tại, chưa bị khoá và `token_version` khớp với database (`backend/app/modules/auth/service.py::refresh_access_token`, `backend/app/core/security/tokens.py::decode_token`).
- Trạng thái khoá được kiểm tra **trước** `token_version`. Khoá luôn tăng `token_version`, nên nhờ thứ tự này người đang đăng nhập bị khoá nhận `ACCOUNT_LOCKED` thay vì `SESSION_REVOKED`.
- Mọi lỗi `SESSION_EXPIRED`, `SESSION_REVOKED`, `ACCOUNT_LOCKED` đều kèm `Set-Cookie` xoá cookie `refresh_token` (`Path=/auth`, `Secure`, `SameSite=None`, khớp thuộc tính lúc set để trình duyệt chấp nhận xoá ở ngữ cảnh cross-site).
- **Yêu cầu quyền**: cookie `refresh_token` hợp lệ (không cần access token).
